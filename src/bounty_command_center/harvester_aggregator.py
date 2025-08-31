import asyncio
import redis
from sqlmodel import Session, select
from .harvesters.intigriti import IntigritiHarvester
from .harvesters.yeswehack import YesWeHackHarvester
from .harvesters.openbugbounty import OpenBugBountyHarvester
from .harvesters.synack import SynackHarvester
from .models import ProgramRaw

class HarvesterAggregator:
    """
    Aggregates data from various bug bounty platform harvesters and stores the raw data.
    Uses a Redis lock to prevent concurrent runs.
    """

    def __init__(self, redis_host='localhost', redis_port=6379):
        """
        Initializes the HarvesterAggregator.

        Args:
            redis_host (str): The Redis host.
            redis_port (int): The Redis port.
        """
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
        self.lock_key = "harvester_aggregator_lock"
        self.lock_timeout = 60  # Lock timeout in seconds

    def run(self, db: Session, platform: str, run_id: str):
        """
        Runs the harvester for the specified platform and stores the raw data.

        Args:
            db (Session): The database session to use.
            platform (str): The name of the platform to harvest.
            run_id (str): A unique ID for this run, for tracing.
        """
        lock = self.redis_client.lock(f"harvester_lock_{platform}", timeout=self.lock_timeout)
        if not lock.acquire(blocking=False):
            print(f"Could not acquire lock for {platform}. Another instance may be running. run_id={run_id}")
            return

        try:
            print(f"Acquired lock. Running {platform} harvester... run_id={run_id}")
            latest_raw = db.exec(
                select(ProgramRaw)
                .where(ProgramRaw.platform == platform)
                .order_by(ProgramRaw.fetched_at.desc())
            ).first()

            etag = latest_raw.etag if latest_raw else None
            last_modified = latest_raw.last_modified if latest_raw else None

            if platform == 'intigriti':
                harvester = IntigritiHarvester()
                raw_data, new_etag, new_last_modified = harvester.fetch_raw_data(etag, last_modified)
            elif platform == 'yeswehack':
                harvester = YesWeHackHarvester()
                raw_data, new_etag, new_last_modified = harvester.fetch_raw_data(etag, last_modified)
            elif platform == 'openbugbounty':
                harvester = OpenBugBountyHarvester()
                raw_data, new_etag, new_last_modified = harvester.fetch_raw_data(etag, last_modified)
            elif platform == 'synack':
                harvester = SynackHarvester()
                raw_data, new_etag, new_last_modified = asyncio.run(harvester.fetch_raw_data(etag, last_modified))
            else:
                print(f"Unknown platform: {platform}")
                return

            if raw_data:
                print(f"Fetched new raw data from {platform}.")
                program_raw = ProgramRaw(
                    platform=platform,
                    data=raw_data,
                    etag=new_etag,
                    last_modified=new_last_modified,
                )
                db.add(program_raw)
                db.commit()
                print("Successfully saved new raw data to the database.")
            else:
                print(f"No new data from {platform}.")
        finally:
            lock.release()
            print("Released lock.")
