from typing import Optional
from .base import BaseHarvester
import requests

class YesWeHackHarvester(BaseHarvester):
    """
    A harvester for scraping bug bounty programs from YesWeHack.
    """

    def __init__(self):
        """
        Initializes the YesWeHackHarvester.
        """
        super().__init__()
        self.url = "https://yeswehack.com/programs"

    def fetch_raw_data(self, etag: Optional[str] = None, last_modified: Optional[str] = None):
        """
        Fetches the raw HTML from the YesWeHack programs page.

        Args:
            etag (str, optional): The ETag from the previous response.
            last_modified (str, optional): The Last-Modified date from the previous response.

        Returns:
            tuple: A tuple containing the raw data, the new ETag, and the new Last-Modified date,
                   or (None, None, None) if the data has not changed or on failure.
        """
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            response = self.session.get(self.url, headers=headers)
            if response.status_code == 304:
                return None, None, None
            response.raise_for_status()
            new_etag = response.headers.get("ETag")
            new_last_modified = response.headers.get("Last-Modified")
            return response.text, new_etag, new_last_modified
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs from YesWeHack: {e}")
            return None, None, None
