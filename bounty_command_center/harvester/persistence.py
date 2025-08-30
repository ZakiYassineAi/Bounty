from typing import List, Dict, Any
from sqlmodel import Session, select
from .. import models
import structlog

log = structlog.get_logger()

class DataPersistence:
    """
    Handles saving and updating harvested data to the database.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_or_create_platform(self, platform_name: str, platform_url: str) -> models.Platform:
        """
        Retrieves a platform from the database by name, creating it if it doesn't exist.
        """
        statement = select(models.Platform).where(models.Platform.name == platform_name)
        platform = self.db.exec(statement).first()
        if not platform:
            log.info("Platform not found, creating a new one.", platform_name=platform_name)
            platform = models.Platform(name=platform_name, url=platform_url)
            self.db.add(platform)
            # Commit here to ensure the platform has an ID for the subsequent program insertions.
            # This is a trade-off for simplicity in this context.
            self.db.commit()
            self.db.refresh(platform)
        return platform

    def upsert_program(self, program_data: Dict[str, Any], platform_id: int):
        """
        Updates an existing program or inserts a new one if it doesn't exist.
        The program is identified by its unique `program_url`.
        """
        program_url = program_data.get("program_url")
        if not program_url:
            log.warning("Skipping program data due to missing 'program_url'.", data=program_data)
            return

        statement = select(models.Program).where(models.Program.program_url == program_url)
        existing_program = self.db.exec(statement).first()

        # Simple logic to determine if program is active based on submission state
        is_active = program_data.get("submission_state", "").lower() in ["open", "new"]

        if existing_program:
            log.debug("Updating existing program.", url=program_url)
            # Update fields
            existing_program.name = program_data.get("name", existing_program.name)
            existing_program.is_active = is_active
            existing_program.scope = program_data.get("scope", existing_program.scope)
            existing_program.last_harvested_at = models.datetime.now(models.timezone.utc)
            # In a more complex scenario, you'd also update rewards here.
        else:
            log.debug("Creating new program.", url=program_url)
            new_program = models.Program(
                name=program_data.get("name"),
                program_url=program_url,
                is_active=is_active,
                scope=program_data.get("scope", {}),
                platform_id=platform_id,
            )
            self.db.add(new_program)

    def save_programs(self, programs_list: List[Dict[str, Any]]):
        """
        Saves a list of harvested program data to the database.
        It assumes all programs in the list belong to the same platform.
        """
        if not programs_list:
            log.info("No programs provided to save.")
            return

        # All harvesters should provide a platform_name.
        platform_name = programs_list[0].get("platform_name")
        if not platform_name:
            log.error("Cannot process programs without a 'platform_name'.", first_program=programs_list[0])
            return

        # A simple way to get a default URL. This could be improved.
        platform_url = f"https://{platform_name.lower()}.com"

        platform = self.get_or_create_platform(platform_name, platform_url)

        for program_data in programs_list:
            self.upsert_program(program_data, platform.id)

        try:
            # Commit all the changes (updates and inserts) for this batch.
            self.db.commit()
            log.info("Successfully saved/updated program data.", count=len(programs_list), platform=platform_name)
        except Exception as e:
            log.error("Database commit failed. Rolling back.", error=str(e))
            self.db.rollback()
            raise # Re-raise the exception to be handled by the caller (e.g., the Celery task)
