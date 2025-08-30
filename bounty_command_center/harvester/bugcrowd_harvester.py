import httpx
import structlog
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from .base_harvester import BaseHarvester

log = structlog.get_logger()

class BugcrowdHarvester(BaseHarvester):
    """
    Harvester for the Bugcrowd platform.
    This harvester scrapes the public program directory.
    """
    def __init__(self):
        super().__init__(platform_name="Bugcrowd", platform_url="https://bugcrowd.com")
        self.start_url = "https://bugcrowd.com/programs"

    async def fetch_programs(
        self, client: httpx.AsyncClient, last_run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches all public programs from Bugcrowd by scraping the directory.
        """
        log.info("Starting program harvest", platform=self.platform_name)
        programs = []

        try:
            response = await client.get(self.start_url, timeout=30.0)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # This is a hypothetical structure. I'm assuming there's a list
            # of programs, and each program is in a container with a specific class.
            program_containers = soup.find_all('div', class_='bc-program-card')

            for container in program_containers:
                # Again, making assumptions about the internal structure.
                name_tag = container.find('h4', class_='bc-program-card__name')
                link_tag = container.find('a', class_='bc-program-card__link')
                payout_tag = container.find('span', class_='bc-program-card__payout')

                if name_tag and link_tag:
                    name = name_tag.get_text(strip=True)
                    program_url = self.platform_url + link_tag['href']

                    # Basic parsing for payout range
                    min_payout, max_payout = None, None
                    if payout_tag:
                        payout_text = payout_tag.get_text(strip=True).replace('$', '').replace(',', '')
                        parts = [p.strip() for p in payout_text.split('-')]
                        if len(parts) == 2:
                            min_payout = int(parts[0])
                            max_payout = int(parts[1])

                    programs.append({
                        "platform_name": self.platform_name,
                        "name": name,
                        "program_url": program_url,
                        "offers_bounties": bool(payout_tag),
                        "min_payout": min_payout,
                        "max_payout": max_payout,
                        "external_id": link_tag['href'].split('/')[-1] # Use the handle as external_id
                    })

            # NOTE: Pagination logic would be added here. It would involve finding
            # the 'next' link and recursively calling the fetch logic or looping.
            # For this initial implementation, I am only fetching the first page.

            log.info("Finished fetching programs", count=len(programs))

        except httpx.HTTPError as e:
            log.error("Failed to fetch Bugcrowd programs page", error=str(e))
        except Exception as e:
            log.error("An error occurred while parsing Bugcrowd programs", error=str(e), exc_info=True)

        # This harvester does not support ETags as it's scraping HTML.
        return {"programs": programs, "metadata": {}}
