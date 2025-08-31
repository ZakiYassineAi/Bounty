import requests
from requests.adapters import HTTPAdapter, Retry

class BaseHarvester:
    """
    A base class for harvesters that provides a session with a retry mechanism.
    """

    def __init__(self):
        """
        Initializes the BaseHarvester.
        """
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
