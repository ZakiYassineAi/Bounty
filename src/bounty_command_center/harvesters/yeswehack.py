import requests
from bs4 import BeautifulSoup
import json

class YesWeHackHarvester:
    """
    A harvester for scraping bug bounty programs from YesWeHack.
    """

    def __init__(self):
        """
        Initializes the YesWeHackHarvester.
        """
        self.url = "https://yeswehack.com/programs"

    def fetch_raw_data(self):
        """
        Fetches the raw HTML from the YesWeHack programs page.

        Returns:
            str: The raw HTML content as a string, or None on failure.
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs from YesWeHack: {e}")
            return None
