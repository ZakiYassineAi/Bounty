from abc import ABC, abstractmethod
from typing import List, Dict, Any
import aiohttp

class BaseHarvester(ABC):
    """
    Abstract base class for all platform-specific bug bounty harvesters.
    """
    def __init__(self, platform_name: str, platform_url: str):
        self.platform_name = platform_name
        self.platform_url = platform_url

    @abstractmethod
    async def fetch_programs(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """
        Fetches all programs from the platform.

        Args:
            session: An aiohttp.ClientSession object for making HTTP requests.

        Returns:
            A list of dictionaries, where each dictionary represents a program.
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
