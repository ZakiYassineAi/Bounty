import redis
from sqlmodel import Session
from .harvesters.intigriti import IntigritiHarvester
from .harvesters.yeswehack import YesWeHackHarvester
from .harvesters.openbugbounty import OpenBugBountyHarvester
from .database import engine
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

    def run(self, platform):
        """
        Runs the harvester for the specified platform and stores the raw data.

        Args:
            platform (str): The name of the platform to harvest.
        """
        lock = self.redis_client.lock(self.lock_key, timeout=self.lock_timeout)
        if not lock.acquire(blocking=False):
            print("Could not acquire lock. Another instance may be running.")
            return

        try:
            print(f"Acquired lock. Running {platform} harvester...")
            if platform == 'intigriti':
                harvester = IntigritiHarvester()
            elif platform == 'yeswehack':
                harvester = YesWeHackHarvester()
            elif platform == 'openbugbounty':
                harvester = OpenBugBountyHarvester()
            else:
                print(f"Unknown platform: {platform}")
                return

            raw_data = harvester.fetch_raw_data()
            if raw_data:
                print(f"Fetched raw data from {platform}.")
                with Session(engine) as db:
                    program_raw = ProgramRaw(platform=platform, data=raw_data)
                    db.add(program_raw)
                    db.commit()
                print("Successfully saved raw data to the database.")
            else:
                print(f"Failed to fetch raw data from {platform}.")
        finally:
            lock.release()
            print("Released lock.")
