import json
from bs4 import BeautifulSoup
from sqlmodel import Session, select
from .models import ProgramRaw, ProgramClean

class NormalizationService:
    """
    A service for normalizing raw program data from various platforms.
    """

    def run(self, db: Session):
        """
        Runs the normalization process for all platforms.
        """
        raw_programs = db.exec(select(ProgramRaw)).all()
        for raw_program in raw_programs:
            if raw_program.platform == "intigriti":
                self._normalize_intigriti(db, raw_program)
            elif raw_program.platform == "yeswehack":
                self._normalize_yeswehack(db, raw_program)
            elif raw_program.platform == "openbugbounty":
                self._normalize_openbugbounty(db, raw_program)
            else:
                print(f"Unknown platform: {raw_program.platform}")

    def _normalize_intigriti(self, db: Session, raw_program: ProgramRaw):
        """
        Normalizes raw data from Intigriti.
        """
        try:
            data = json.loads(raw_program.data)
            for program_data in data:
                url = program_data.get("url")
                if not url:
                    continue

                # Check for duplicates
                existing_program = db.exec(select(ProgramClean).where(ProgramClean.url == url)).first()
                if existing_program:
                    continue

                program = ProgramClean(
                    name=program_data.get("name"),
                    url=url,
                    platform="intigriti",
                    # The following fields are placeholders and need to be extracted from the actual data
                    scope=[],
                    vulnerability_types=[],
                    min_bounty=None,
                    max_bounty=None,
                    status="public",
                    last_updated=None,
                    acceptance_rate=None,
                )
                db.add(program)
            db.commit()
        except json.JSONDecodeError:
            print(f"Error decoding JSON for raw program {raw_program.id}")

    def _normalize_yeswehack(self, db: Session, raw_program: ProgramRaw):
        """
        Normalizes raw data from YesWeHack.
        """
        soup = BeautifulSoup(raw_program.data, 'html.parser')
        script_tag = soup.find('script', {'id': 'ng-state'})
        if not script_tag or not hasattr(script_tag, 'string'):
            print(f"Could not find ng-state script tag or its content for raw program {raw_program.id}")
            return

        try:
            json_data = json.loads(script_tag.string)
            programs_data = []
            for key, value in json_data.items():
                if key.startswith('getPrograms-'):
                    programs_data = value['data']['items']
                    break

            for program_data in programs_data:
                url = f"https://yeswehack.com/programs/{program_data.get('slug')}"
                if not url:
                    continue

                # Check for duplicates
                existing_program = db.exec(select(ProgramClean).where(ProgramClean.url == url)).first()
                if existing_program:
                    continue

                program = ProgramClean(
                    name=program_data.get("title"),
                    url=url,
                    platform="yeswehack",
                    scope=[],
                    vulnerability_types=[],
                    min_bounty=program_data.get("bounty_reward_min"),
                    max_bounty=program_data.get("bounty_reward_max"),
                    status="public",
                    last_updated=None, # This needs parsing from the 'last_update_at' field
                    acceptance_rate=None,
                )
                db.add(program)
            db.commit()
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing JSON for raw program {raw_program.id}: {e}")

    def _normalize_openbugbounty(self, db: Session, raw_program: ProgramRaw):
        """
        Normalizes raw data from Open Bug Bounty.
        """
        soup = BeautifulSoup(raw_program.data, 'html.parser')

        # This is a guess based on the HTML structure from view_text_website
        # It might need to be adjusted.
        program_rows = soup.select('div.bugbounty-list__item')

        for row in program_rows:
            try:
                name_element = row.select_one('a')
                if name_element:
                    name = name_element.text.strip()
                    url = f"https://www.openbugbounty.org{name_element['href']}"
                else:
                    continue

                # Check for duplicates
                existing_program = db.exec(select(ProgramClean).where(ProgramClean.url == url)).first()
                if existing_program:
                    continue

                program = ProgramClean(
                    name=name,
                    url=url,
                    platform="openbugbounty",
                    scope=[],
                    vulnerability_types=[],
                    min_bounty=None,
                    max_bounty=None,
                    status="public",
                    last_updated=None,
                    acceptance_rate=None,
                )
                db.add(program)
            except (AttributeError, KeyError) as e:
                print(f"Error parsing Open Bug Bounty row: {e}")
                continue
        db.commit()
