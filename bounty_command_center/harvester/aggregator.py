import asyncio
from typing import List
import aiohttp
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
    def __init__(self):
        self._harvesters: List[BaseHarvester] = []
        self._register_harvesters()

    def _register_harvesters(self):
        """Initializes and registers all the available harvesters."""
        try:
            self.add_harvester(HackeroneHarvester())
            log.info("Registered HackerOne harvester.")
        except ValueError as e:
            log.error("Failed to register HackeroneHarvester", error=str(e),
                      instructions="Ensure H1 credentials are set in the environment.")
        # Future harvesters would be registered here.

    def add_harvester(self, harvester: BaseHarvester):
        """Adds a harvester to the aggregator."""
        self._harvesters.append(harvester)

    async def run_all(self, db_session: Session):
        """
        Runs all registered harvesters concurrently and saves the results
        to the database.
        """
        if not self._harvesters:
            log.warning("No harvesters are registered. Skipping run.")
            return

        persistence = DataPersistence(db_session)

        async with aiohttp.ClientSession() as session:
            tasks = [harvester.fetch_programs(session) for harvester in self._harvesters]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for harvester, result in zip(self._harvesters, results):
                platform_name = harvester.platform_name
                if isinstance(result, Exception):
                    log.error("Failed to fetch programs", platform=platform_name, error=result)
                elif result:
                    log.info(f"Successfully fetched {len(result)} programs from {platform_name}. Saving to DB...")
                    try:
                        persistence.save_programs(result)
                        log.info("Successfully saved programs", platform=platform_name)
                    except Exception as e:
                        log.error("Failed to save programs to database", platform=platform_name, error=str(e))
                else:
                    log.info("No programs fetched for platform", platform=platform_name)

if __name__ == '__main__':
    # This is for standalone testing and requires a DB session.
    # You would need to set up a session similar to how the main app does it.
    print("This script is not meant to be run standalone without a database session.")
