from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select
from .. import models
import structlog
from datetime import datetime, timezone

log = structlog.get_logger()

class DataPersistence:
    """
    Handles saving and updating harvested data to the database using robust,
    atomic operations.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_or_create_platform(self, platform_name: str, platform_url: str) -> models.Platform:
        """Gets a platform from the DB or creates it if it doesn't exist."""
        statement = select(models.Platform).where(models.Platform.name == platform_name)
        platform = self.db.exec(statement).first()
        if not platform:
            log.info("Platform not found, creating new one.", platform_name=platform_name)
            platform = models.Platform(name=platform_name, url=platform_url)
            self.db.add(platform)
            self.db.commit() # Commit immediately to get an ID
            self.db.refresh(platform)
        return platform

    def get_last_run_metadata(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves the last run metadata for a given platform."""
        statement = select(models.PlatformMetadata).where(models.PlatformMetadata.platform_name == platform_name)
        metadata_obj = self.db.exec(statement).first()
        return metadata_obj.last_run_metadata if metadata_obj else None

    def save_run_metadata(self, platform_name: str, metadata: Dict[str, Any]):
        """Saves the run metadata for a platform."""
        statement = select(models.PlatformMetadata).where(models.PlatformMetadata.platform_name == platform_name)
        metadata_obj = self.db.exec(statement).first()
        if metadata_obj:
            metadata_obj.last_run_metadata = metadata
        else:
            metadata_obj = models.PlatformMetadata(
                platform_name=platform_name,
                last_run_metadata=metadata
            )
        self.db.add(metadata_obj)
        # This will be committed along with the program upserts.

    def upsert_programs_batch(self, programs_list: List[Dict[str, Any]], platform_id: int):
        """
        Upserts a batch of programs using a single, efficient SQL statement.
        """
        if not programs_list:
            return

        def get_status(state: Optional[str]) -> str:
            state = (state or "").lower()
            if state in ["open", "new"]: return "active"
            if state in ["paused", "disabled"]: return "paused"
            return "unknown"

        insert_values = [
            {
                "platform_id": platform_id,
                "external_id": p.get("external_id"),
                "name": p.get("name"),
                "program_url": p.get("program_url"),
                "status": get_status(p.get("submission_state")),
                "offers_bounties": p.get("offers_bounties", False),
                "last_seen_at": datetime.now(timezone.utc),
            }
            for p in programs_list if p.get("external_id") and p.get("program_url")
        ]

        if not insert_values:
            log.warning("No valid programs to upsert after filtering.")
            return

        stmt = sqlite_insert(models.Program).values(insert_values)

        stmt = stmt.on_conflict_do_update(
            index_elements=['platform_id', 'external_id'],
            set_={
                "name": stmt.excluded.name,
                "program_url": stmt.excluded.program_url,
                "status": stmt.excluded.status,
                "offers_bounties": stmt.excluded.offers_bounties,
                "last_seen_at": stmt.excluded.last_seen_at,
            }
        )

        self.db.exec(stmt)
        log.info("Executed batch upsert for programs.", count=len(insert_values))
