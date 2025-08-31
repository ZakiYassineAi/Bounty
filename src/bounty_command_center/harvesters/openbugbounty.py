import requests

class OpenBugBountyHarvester:
    """
    A harvester for scraping bug bounty programs from Open Bug Bounty.
    """

    def __init__(self):
        """
        Initializes the OpenBugBountyHarvester.
        """
        self.url = "https://www.openbugbounty.org/bugbounty-list/"

    def fetch_raw_data(self):
        """
        Fetches the raw HTML from the Open Bug Bounty programs page.

        Returns:
            str: The raw HTML content as a string, or None on failure.
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs from Open Bug Bounty: {e}")
            return None
