import os
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
import structlog
from .base_harvester import BaseHarvester

log = structlog.get_logger()

class HackeroneHarvester(BaseHarvester):
    """
    Harvester for the HackerOne bug bounty platform.

    This harvester requires a HackerOne username and API token to be set as
    environment variables:
    - HACKERONE_USERNAME
    - HACKERONE_API_TOKEN
    """
    def __init__(self):
        super().__init__(platform_name="HackerOne", platform_url="https://hackerone.com")
        self.api_username = os.getenv("HACKERONE_USERNAME")
        self.api_token = os.getenv("HACKERONE_API_TOKEN")
        self.base_url = "https://api.hackerone.com/v1/hackers"
        self.headers = {'Accept': 'application/json'}

        if not self.api_username or not self.api_token:
            log.error("HackerOne credentials not found in environment variables.",
                      instructions="Please set HACKERONE_USERNAME and HACKERONE_API_TOKEN.")
            raise ValueError("HackerOne API credentials are not configured.")

        self.auth = aiohttp.BasicAuth(self.api_username, self.api_token)

    async def _fetch_paginated_data(self, session: aiohttp.ClientSession, url: str) -> List[Dict[str, Any]]:
        """Generic helper to fetch all pages from a paginated HackerOne endpoint."""
        all_data = []
        page_number = 1
        while True:
            params = {'page[number]': str(page_number), 'page[size]': '100'}
            try:
                response = await session.get(url, headers=self.headers, auth=self.auth, params=params)
                response.raise_for_status()
                page_json = await response.json()

                data = page_json.get('data')
                if not data:
                    break

                all_data.extend(data)

                if 'next' in page_json.get('links', {}):
                    page_number += 1
                else:
                    break # No more pages
            except aiohttp.ClientError as e:
                log.error("API request failed", url=url, page=page_number, error=str(e))
                # Depending on the error, you might want to break or retry.
                # For a 404 on a sub-resource like scopes, it's fine to just stop.
                if e.status == 404:
                    log.warning("Resource not found, likely no items.", url=url)
                break
            except Exception as e:
                log.error("An unexpected error occurred during pagination", url=url, error=str(e))
                break
        return all_data

    async def _fetch_program_details(self, session: aiohttp.ClientSession, program_handle: str) -> Optional[Dict[str, Any]]:
        """Fetches detailed information for a single program."""
        url = f"{self.base_url}/programs/{program_handle}"
        try:
            response = await session.get(url, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            return await response.json()
        except aiohttp.ClientError as e:
            log.error("Failed to fetch program details", handle=program_handle, error=str(e))
            return None

    async def fetch_programs(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """
        Fetches all programs from HackerOne, enriches them with details and scope,
        and returns a normalized list.
        """
        log.info(f"Starting program harvest from {self.platform_name}...")

        programs_url = f"{self.base_url}/programs"
        basic_programs = await self._fetch_paginated_data(session, programs_url)

        if not basic_programs:
            log.warning("No programs were fetched from HackerOne.")
            return []

        enriched_programs = []
        for program_data in basic_programs:
            attributes = program_data.get('attributes', {})
            handle = attributes.get('handle')

            if not handle:
                log.warning("Found program data without a handle, skipping.", data=program_data)
                continue

            # Fetch details and scopes concurrently
            details_task = self._fetch_program_details(session, handle)
            scopes_url = f"{self.base_url}/programs/{handle}/structured_scopes"
            scopes_task = self._fetch_paginated_data(session, scopes_url)

            details_response, scopes_data = await asyncio.gather(details_task, scopes_task)

            # Normalize the program data
            normalized_program = {
                "platform_name": self.platform_name,
                "name": attributes.get('name'),
                "program_url": f"https://hackerone.com/{handle}",
                "offers_bounties": attributes.get('offers_bounties', False),
                "submission_state": attributes.get('submission_state'),
                "handle": handle,
                "policy": "",
                "scope": [],
            }

            if details_response and 'data' in details_response:
                details_attr = details_response['data'].get('attributes', {})
                normalized_program['policy'] = details_attr.get('policy', '')

            if scopes_data:
                normalized_program['scope'] = [
                    {
                        "asset_type": s.get('attributes', {}).get('asset_type'),
                        "asset_identifier": s.get('attributes', {}).get('asset_identifier'),
                        "eligible_for_bounty": s.get('attributes', {}).get('eligible_for_bounty'),
                        "instruction": s.get('attributes', {}).get('instruction'),
                    }
                    for s in scopes_data
                ]

            enriched_programs.append(normalized_program)
            log.info(f"Successfully enriched program", handle=handle)

            # A small, respectful delay to avoid overwhelming the API
            await asyncio.sleep(0.1)

        log.info(f"Finished fetching and enriching {len(enriched_programs)} programs from {self.platform_name}.")
        return enriched_programs
