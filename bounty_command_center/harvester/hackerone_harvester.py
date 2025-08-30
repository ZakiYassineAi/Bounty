import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

from .base_harvester import BaseHarvester

log = structlog.get_logger()

# --- Custom Exception for Retrying ---
class RetryableHTTPError(Exception):
    """Custom exception for HTTP status codes we want to retry on."""
    def __init__(self, status_code: int, message: str = "Retryable HTTP Error"):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{message}: Status {status_code}")

def is_retryable_error(exception: BaseException) -> bool:
    """Return True if the exception is a retryable HTTP error."""
    return isinstance(exception, (httpx.TimeoutException, httpx.ConnectError, RetryableHTTPError))

class HackeroneHarvester(BaseHarvester):
    """
    A robust, compliant harvester for the HackerOne bug bounty platform.
    Uses httpx, tenacity for retries, and respects ETag headers.
    """
    def __init__(self):
        super().__init__(platform_name="HackerOne", platform_url="https://hackerone.com")
        self.api_username = os.getenv("HACKERONE_USERNAME")
        self.api_token = os.getenv("HACKERONE_API_TOKEN")
        self.base_url = "https://api.hackerone.com/v1/hackers"

        if not self.api_username or not self.api_token:
            log.error("H1 credentials not found in env.", instructions="Set HACKERONE_USERNAME and HACKERONE_API_TOKEN.")
            raise ValueError("HackerOne API credentials are not configured.")

        self.auth = httpx.BasicAuth(self.api_username, self.api_token)

    @retry(
        wait=wait_random_exponential(multiplier=1, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RetryableHTTPError)
    )
    async def _make_request(
        self, client: httpx.AsyncClient, url: str, headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Makes a robust, retrying GET request."""
        log.debug("Requesting URL", url=url, headers=headers)
        response = await client.get(url, headers=headers, auth=self.auth, timeout=30.0)

        # Raise retryable error for server-side issues
        if response.status_code in [500, 502, 503, 504]:
            raise RetryableHTTPError(status_code=response.status_code)

        response.raise_for_status() # Raise for other 4xx client errors
        return response

    async def _fetch_paginated_data(
        self, client: httpx.AsyncClient, url: str, etag: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetches all pages from a paginated HackerOne endpoint, handling ETag.
        Returns the data and the new ETag.
        """
        all_data = []
        request_headers = {'Accept': 'application/json'}
        if etag:
            request_headers['If-None-Match'] = etag

        try:
            response = await self._make_request(client, url, headers=request_headers)

            if response.status_code == 304:
                log.info("Data not modified (304)", url=url)
                return [], etag

            new_etag = response.headers.get('etag')
            page_json = response.json()

            while True:
                data = page_json.get('data')
                if not data:
                    break
                all_data.extend(data)

                next_url = page_json.get('links', {}).get('next')
                if not next_url:
                    break

                log.debug("Fetching next page", url=next_url)
                response = await self._make_request(client, next_url)
                page_json = response.json()

            return all_data, new_etag

        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404: # Don't log 404 as an error, it's expected
                log.error("API request failed", url=url, status=e.response.status_code)
            return [], etag
        except Exception as e:
            log.error("An unexpected error occurred during pagination", url=url, error=str(e))
            return [], etag

    async def fetch_programs(
        self, client: httpx.AsyncClient, last_run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches all programs from HackerOne, normalizes them, and returns them
        along with the new run metadata (like ETag).
        """
        log.info("Starting program harvest", platform=self.platform_name)

        etag = last_run_metadata.get("etag") if last_run_metadata else None

        programs_url = f"{self.base_url}/programs"
        basic_programs, new_etag = await self._fetch_paginated_data(client, programs_url, etag=etag)

        if not basic_programs:
            log.info("No new or updated programs fetched from HackerOne.")
            return {"programs": [], "metadata": {"etag": new_etag or etag}}

        normalized_programs = []
        for program_data in basic_programs:
            attributes = program_data.get('attributes', {})
            handle = attributes.get('handle')
            if not handle:
                continue

            normalized_programs.append({
                "external_id": program_data.get("id"),
                "platform_name": self.platform_name,
                "name": attributes.get('name'),
                "program_url": f"https://hackerone.com/{handle}",
                "handle": handle,
                "offers_bounties": attributes.get('offers_bounties', False),
                "submission_state": attributes.get('submission_state'),
            })

        log.info("Finished fetching programs", count=len(normalized_programs))
        return {"programs": normalized_programs, "metadata": {"etag": new_etag}}
