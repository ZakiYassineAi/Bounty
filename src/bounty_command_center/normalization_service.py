import json
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, ValidationError
from sqlmodel import Session, select
from .models import ProgramRaw, ProgramClean, ProgramInvalid

# Pydantic schemas for validation
class IntigritiProgramSchema(BaseModel):
    name: str
    url: HttpUrl
    status: str
    max_bounty: float
    min_bounty: float
    company_handle: str

class YesWeHackProgramSchema(BaseModel):
    title: str
    slug: str
    bounty_reward_min: Optional[float]
    bounty_reward_max: Optional[float]
    disabled: bool

class SynackProgramSchema(BaseModel):
    name: str
    url: HttpUrl

class NormalizationService:
    """
    A service for normalizing raw program data from various platforms.
    """

    def run(self, db: Session, platform: Optional[str] = None) -> dict:
        """
        Runs the normalization process.

        Args:
            db (Session): The database session.
            platform (str, optional): If provided, only normalizes data for this platform.

        Returns:
            A dictionary containing statistics about the run.
        """
        stats = {'new': 0, 'invalid': 0, 'updated': 0} # 'updated' is a placeholder for now

        query = select(ProgramRaw)
        if platform:
            query = query.where(ProgramRaw.platform == platform)

        raw_programs = db.exec(query).all()

        for raw_program in raw_programs:
            handler = getattr(self, f"_normalize_{raw_program.platform.lower()}", None)
            if handler:
                new, invalid = handler(db, raw_program)
                stats['new'] += new
                stats['invalid'] += invalid
            else:
                print(f"Normalization not implemented for platform: {raw_program.platform}")

        return stats

    def _normalize_synack(self, db: Session, raw_program: ProgramRaw) -> Tuple[int, int]:
        """
        Normalizes raw data from Synack using a Pydantic schema.
        Returns a tuple of (new_count, invalid_count).
        """
        new_count, invalid_count = 0, 0
        try:
            programs_data = json.loads(raw_program.data)
            for program_data in programs_data:
                try:
                    validated_program = SynackProgramSchema.model_validate(program_data)

                    existing_program = db.exec(select(ProgramClean).where(ProgramClean.url == str(validated_program.url))).first()
                    if existing_program:
                        continue

                    program = ProgramClean(
                        name=validated_program.name,
                        url=str(validated_program.url),
                        platform="Synack",
                        scope=[],
                        vulnerability_types=[],
                    )
                    db.add(program)
                    new_count += 1
                except ValidationError as e:
                    invalid_program = ProgramInvalid(
                        platform="Synack",
                        raw_data=json.dumps(program_data),
                        error_message=e.json(),
                    )
                    db.add(invalid_program)
                    invalid_count += 1
            db.commit()
        except json.JSONDecodeError:
            invalid_program = ProgramInvalid(
                platform="Synack",
                raw_data=raw_program.data,
                error_message="Invalid JSON format in raw data.",
            )
            db.add(invalid_program)
            invalid_count += 1
            db.commit()
        return new_count, invalid_count

    def _normalize_intigriti(self, db: Session, raw_program: ProgramRaw) -> Tuple[int, int]:
        """
        Normalizes raw data from Intigriti using a Pydantic schema for validation.
        Returns a tuple of (new_count, invalid_count).
        """
        new_count, invalid_count = 0, 0
        try:
            programs_data = json.loads(raw_program.data)
            for program_data in programs_data:
                try:
                    validated_program = IntigritiProgramSchema.model_validate(program_data)

                    url_str = str(validated_program.url)
                    existing_program = db.exec(select(ProgramClean).where(ProgramClean.url == url_str)).first()
                    if existing_program:
                        continue

                    program = ProgramClean(
                        name=validated_program.name,
                        url=url_str,
                        platform="intigriti",
                        status=validated_program.status,
                        min_bounty=validated_program.min_bounty,
                        max_bounty=validated_program.max_bounty,
                        scope=[],
                        vulnerability_types=[],
                    )
                    db.add(program)
                    new_count += 1
                except ValidationError as e:
                    invalid_program = ProgramInvalid(
                        platform="intigriti",
                        raw_data=json.dumps(program_data),
                        error_message=e.json(),
                    )
                    db.add(invalid_program)
                    invalid_count += 1
            db.commit()
        except json.JSONDecodeError:
            invalid_program = ProgramInvalid(
                platform="intigriti",
                raw_data=raw_program.data,
                error_message="Invalid JSON format in raw data.",
            )
            db.add(invalid_program)
            invalid_count += 1
            db.commit()
        return new_count, invalid_count

    def _normalize_yeswehack(self, db: Session, raw_program: ProgramRaw) -> Tuple[int, int]:
        """
        Normalizes raw data from YesWeHack using a Pydantic schema for validation.
        Returns a tuple of (new_count, invalid_count).
        """
        new_count, invalid_count = 0, 0
        soup = BeautifulSoup(raw_program.data, 'html.parser')
        script_tag = soup.find('script', {'id': 'ng-state'})
        if not script_tag or not hasattr(script_tag, 'string'):
            invalid_program = ProgramInvalid(
                platform="yeswehack", raw_data=raw_program.data,
                error_message="Could not find ng-state script tag in HTML."
            )
            db.add(invalid_program)
            db.commit()
            return 0, 1

        try:
            json_data = json.loads(script_tag.string)
            programs_data = []
            for key, value in json_data.items():
                if key.startswith('getPrograms-') and isinstance(value, dict):
                    programs_data = value.get('data', {}).get('items', [])
                    break

            if not programs_data:
                raise KeyError("Could not find programs data in the ng-state JSON.")

            for program_data in programs_data:
                try:
                    validated_program = YesWeHackProgramSchema.model_validate(program_data)
                    url = f"https://yeswehack.com/programs/{validated_program.slug}"
                    if db.exec(select(ProgramClean).where(ProgramClean.url == url)).first():
                        continue

                    program = ProgramClean(
                        name=validated_program.title, url=url, platform="yeswehack",
                        min_bounty=validated_program.bounty_reward_min,
                        max_bounty=validated_program.bounty_reward_max,
                        status="enabled" if not validated_program.disabled else "disabled",
                        scope=[], vulnerability_types=[]
                    )
                    db.add(program)
                    new_count += 1
                except ValidationError as e:
                    invalid_program = ProgramInvalid(
                        platform="yeswehack", raw_data=json.dumps(program_data), error_message=e.json()
                    )
                    db.add(invalid_program)
                    invalid_count += 1
            db.commit()
        except (json.JSONDecodeError, KeyError) as e:
            invalid_program = ProgramInvalid(
                platform="yeswehack", raw_data=raw_program.data,
                error_message=f"Error parsing ng-state JSON: {e}"
            )
            db.add(invalid_program)
            invalid_count += 1
            db.commit()
        return new_count, invalid_count

    def _normalize_openbugbounty(self, db: Session, raw_program: ProgramRaw) -> Tuple[int, int]:
        """
        Normalizes raw data from Open Bug Bounty.
        Returns a tuple of (new_count, invalid_count).
        """
        new_count, invalid_count = 0, 0
        soup = BeautifulSoup(raw_program.data, 'html.parser')

        program_rows = soup.select('div.bugbounty-list__item')

        for row in program_rows:
            try:
                name_element = row.select_one('a')
                if name_element and name_element.has_attr('href'):
                    name = name_element.text.strip()
                    url = f"https://www.openbugbounty.org{name_element['href']}"
                else:
                    raise ValueError("Could not find program name and url in row")

                if not name or not url:
                    raise ValueError("Missing name or url")

                if db.exec(select(ProgramClean).where(ProgramClean.url == url)).first():
                    continue

                program = ProgramClean(
                    name=name, url=url, platform="openbugbounty",
                    scope=[], vulnerability_types=[]
                )
                db.add(program)
                new_count += 1
            except Exception as e:
                invalid_program = ProgramInvalid(
                    platform="openbugbounty", raw_data=str(row),
                    error_message=f"Error parsing row: {e}"
                )
                db.add(invalid_program)
                invalid_count += 1
                continue
        db.commit()
        return new_count, invalid_count
