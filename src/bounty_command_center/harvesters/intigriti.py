import requests
import os

class IntigritiHarvester:
    """
    A harvester for fetching bug bounty programs from Intigriti.
    """

    def __init__(self, api_key=None):
        """
        Initializes the IntigritiHarvester.

        Args:
            api_key (str, optional): The Intigriti API key. If not provided,
                                     it will be read from the INTIGRITI_API_KEY
                                     environment variable.
        """
        self.api_key = api_key or os.environ.get("INTIGRITI_API_KEY")
        self.api_url = "https://api.intigriti.com/external/company/v2.0/programs"

    def fetch_raw_data(self):
        """
        Fetches the raw program data from the Intigriti API.

        Returns:
            str: The raw JSON response as a string, or None on failure.
        """
        if not self.api_key:
            raise ValueError("Intigriti API key not provided.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(self.api_url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs from Intigriti: {e}")
            return None
