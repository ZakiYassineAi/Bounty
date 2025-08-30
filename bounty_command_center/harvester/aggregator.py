import asyncio
import httpx
from sqlmodel import Session
import structlog

from .base_harvester import BaseHarvester
from .hackerone_harvester import HackeroneHarvester
from .persistence import DataPersistence

log = structlog.get_logger()

class HarvesterAggregator:
    """
    Manages and runs all registered bug bounty harvesters and saves the data.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.persistence = DataPersistence(db_session)
        self._harvesters: list[BaseHarvester] = []
        self._register_harvesters()

    def _register_harvesters(self):
        """Initializes and registers all available harvesters."""
        try:
            self.add_harvester(HackeroneHarvester())
            log.info("Registered HackerOne harvester.")
        except ValueError as e:
            log.error("Failed to register HackeroneHarvester", error=str(e))

    def add_harvester(self, harvester: BaseHarvester):
        """Adds a harvester to the aggregator."""
        self._harvesters.append(harvester)

    async def run_harvester(self, harvester: BaseHarvester, client: httpx.AsyncClient):
        """Runs a single harvester and persists its data."""
        platform_name = harvester.platform_name
        log.info("Running harvester", platform=platform_name)

        try:
            platform = self.persistence.get_or_create_platform(
                platform_name=platform_name,
                platform_url=harvester.platform_url
            )

            last_run_meta = self.persistence.get_last_run_metadata(platform_name)

            result = await harvester.fetch_programs(client, last_run_meta)

            programs = result.get("programs")
            new_meta = result.get("metadata")

            if programs:
                self.persistence.upsert_programs_batch(programs, platform.id)

            if new_meta:
                self.persistence.save_run_metadata(platform_name, new_meta)

            self.db_session.commit()
            log.info("Successfully completed harvester run.", platform=platform_name)

        except Exception as e:
            log.error("Harvester run failed", platform=platform_name, error=str(e), exc_info=True)
            self.db_session.rollback()

    async def run_all(self):
        """
        Runs all registered harvesters concurrently.
        """
        if not self._harvesters:
            log.warning("No harvesters registered. Skipping run.")
            return

        async with httpx.AsyncClient() as client:
            tasks = [self.run_harvester(h, client) for h in self._harvesters]
            await asyncio.gather(*tasks)
