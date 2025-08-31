import asyncio
import json
from pathlib import Path
from typing import Tuple, Optional

from playwright.async_api import async_playwright

from .base import BaseHarvester

LOGIN_URL = "https://platform.synack.com/login"
POST_LOGIN_URL_IDENTIFIER = "https://platform.synack.com/tasks"

class SynackHarvester(BaseHarvester):
    AUTH_FILE = Path("synack_auth_state.json")
    """
    A harvester for fetching bug bounty programs from Synack using Playwright.
    This harvester requires a one-time manual login to save the session state.
    """

    def __init__(self):
        """
        Initializes the SynackHarvester.
        """
        pass

    async def fetch_raw_data(
        self, etag: Optional[str] = None, last_modified: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetches the raw program data from the Synack platform using Playwright.
        """
        max_retries = 3
        retry_delay_seconds = 10

        for attempt in range(max_retries):
            try:
                print(f"Starting Synack harvester (Attempt {attempt + 1}/{max_retries})...")
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False)

                    context_options = {}
                    if self.AUTH_FILE.exists():
                        print(f"Authentication file found at {self.AUTH_FILE}. Loading state.")
                        context_options["storage_state"] = str(self.AUTH_FILE)

                    context = await browser.new_context(**context_options)
                    page = await context.new_page()

                    print(f"Navigating to {POST_LOGIN_URL_IDENTIFIER} to check auth status.")
                    await page.goto(POST_LOGIN_URL_IDENTIFIER, wait_until="networkidle")

                    if LOGIN_URL in page.url:
                        print("Authentication state is invalid or missing. Manual login required.")
                        print(f"Please complete the login process in the browser window.")

                        try:
                            await page.wait_for_url(f"{POST_LOGIN_URL_IDENTIFIER}/**", timeout=300000)
                            print("Login successful. Saving authentication state.")
                            await context.storage_state(path=self.AUTH_FILE)
                        except Exception as e:
                            print(f"Failed to detect successful login within the time limit: {e}")
                            await browser.close()
                            return None, None, None

                    print("Successfully authenticated. Navigating to programs page.")
                    targets_url = "https://platform.synack.com/targets/listings"
                    await page.goto(targets_url, wait_until="networkidle")

                    print("Taking screenshot of programs page.")
                    await page.screenshot(path="synack_programs_page.png")

                    print("Scraping program data (placeholder)...")
                    scraped_programs = [
                        {
                            "name": "Dummy Synack Program",
                            "url": "https://platform.synack.com/targets/listings/dummy-program",
                        }
                    ]

                    # The raw data is simply the JSON list of scraped programs.
                    raw_data_json = json.dumps(scraped_programs)

                    await browser.close()
                    print("Synack harvester finished successfully.")
                    return raw_data_json, None, None

            except Exception as e:
                print(f"An error occurred during Synack harvest (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay_seconds} seconds...")
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    print("Max retries reached. Synack harvest failed.")
                    return None, None, None

        return None, None, None
