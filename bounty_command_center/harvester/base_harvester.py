from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx

class BaseHarvester(ABC):
    """
    Abstract base class for all platform-specific bug bounty harvesters.
    """
    def __init__(self, platform_name: str, platform_url: str):
        self.platform_name = platform_name
        self.platform_url = platform_url

    @abstractmethod
    async def fetch_programs(
        self, client: httpx.AsyncClient, last_run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches all programs from the platform.

        Args:
            client: An httpx.AsyncClient for making HTTP requests.
            last_run_metadata: A dictionary containing metadata from the last
                               successful run, e.g., ETags.

        Returns:
            A dictionary containing the list of fetched programs and new
            metadata for the next run.
            Example: {"programs": [...], "metadata": {"etag": "..."}}
        """
        pass

    def get_platform_info(self) -> Dict[str, str]:
        """
        Returns basic information about the platform.
        """
        return {
            "name": self.platform_name,
            "url": self.platform_url,
        }
