import os
import httpx
from typing import Optional, List, Dict, Any, Callable
from .base import BaseHarvester

class IntigritiClient:
    """
    A client for interacting with the Intigriti API.
    Designed for testability by allowing injection of an httpx client and API key provider.
    """
    def __init__(
        self,
        http: Optional[httpx.Client] = None,
        base_url: str = "https://api.intigriti.com",
        api_key_provider: Optional[Callable[[], str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.http = http or httpx.Client(base_url=self.base_url, timeout=30)
        self.get_api_key = api_key_provider or (lambda: os.environ.get("INTIGRITI_API_KEY", "MISSING"))

    def _auth_headers(self) -> Dict[str, str]:
        """Returns the authorization headers for API requests."""
        api_key = self.get_api_key()
        if not api_key or api_key == "MISSING":
            raise ValueError("Intigriti API key not provided or found in environment.")
        return {"Authorization": f"Bearer {api_key}"}

    def list_programs(self, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Lists all programs from the Intigriti API."""
        request_headers = self._auth_headers()
        if headers:
            request_headers.update(headers)

        response = self.http.get("/external/company/v2.0/programs", headers=request_headers)
        response.raise_for_status()
        return response

class IntigritiHarvester(BaseHarvester):
    """
    A harvester for fetching bug bounty programs from Intigriti.
    """
    def __init__(self, client: Optional[IntigritiClient] = None):
        """
        Initializes the IntigritiHarvester.
        An IntigritiClient can be injected for testing purposes.
        """
        super().__init__()
        self.client = client or IntigritiClient()

    def fetch_raw_data(self, etag: Optional[str] = None, last_modified: Optional[str] = None):
        """
        Fetches the raw program data from the Intigriti API.
        """
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            response = self.client.list_programs(headers=headers)
            if response.status_code == 304:
                return None, None, None

            new_etag = response.headers.get("ETag")
            new_last_modified = response.headers.get("Last-Modified")
            return response.text, new_etag, new_last_modified
        except (httpx.RequestError, ValueError) as e:
            print(f"Error fetching programs from Intigriti: {e}")
            return None, None, None
