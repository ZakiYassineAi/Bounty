import pytest
import json
from sqlmodel import Session, select
from bounty_command_center.models import ProgramRaw, ProgramClean, ProgramInvalid
from bounty_command_center.normalization_service import NormalizationService

# region Intigriti Tests
def test_normalize_intigriti_success(db_session: Session):
    """Tests the successful normalization of valid raw Intigriti data."""
    raw_data = json.dumps([
        {
            "name": "Intigriti Program",
            "url": "https://intigriti.com/programs/intigriti/intigriti",
            "status": "open",
            "max_bounty": 5000.0,
            "min_bounty": 100.0,
            "company_handle": "intigriti"
        }
    ])
    raw_program = ProgramRaw(platform="intigriti", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    programs = db_session.exec(select(ProgramClean)).all()
    assert len(programs) == 1
    assert programs[0].name == "Intigriti Program"

def test_normalize_intigriti_invalid_json(db_session: Session):
    """Tests that invalid Intigriti JSON is handled correctly."""
    raw_program = ProgramRaw(platform="intigriti", data="not valid json")
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "Invalid JSON" in invalid_programs[0].error_message

def test_normalize_intigriti_schema_validation_failure(db_session: Session):
    """Tests that Intigriti data failing schema validation is handled."""
    raw_data = json.dumps([{"name": "Only Name Program"}]) # Missing required fields
    raw_program = ProgramRaw(platform="intigriti", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "url" in invalid_programs[0].error_message # Pydantic error will mention missing fields
# endregion

# region YesWeHack Tests
def test_normalize_yeswehack_success(db_session: Session):
    """Tests the successful normalization of valid raw YesWeHack data."""
    ywh_program_data = {
        "title": "YesWeHack Program", "slug": "ywh-program",
        "bounty_reward_min": 100.0, "bounty_reward_max": 5000.0, "disabled": False
    }
    raw_data = f"""
    <html><body><script id="ng-state" type="application/json">
    {{ "getPrograms-x": {{ "data": {{ "items": [ {json.dumps(ywh_program_data)} ] }} }} }}
    </script></body></html>
    """
    raw_program = ProgramRaw(platform="yeswehack", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    programs = db_session.exec(select(ProgramClean)).all()
    assert len(programs) == 1
    assert programs[0].name == "YesWeHack Program"

def test_normalize_yeswehack_missing_script_tag(db_session: Session):
    """Tests YesWeHack normalization when the ng-state script tag is missing."""
    raw_program = ProgramRaw(platform="yeswehack", data="<html><body></body></html>")
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "Could not find ng-state script tag" in invalid_programs[0].error_message

def test_normalize_yeswehack_schema_validation_failure(db_session: Session):
    """Tests YesWeHack data failing schema validation."""
    ywh_program_data = {"title": "Only Title Program"} # Missing slug
    raw_data = f"""
    <html><body><script id="ng-state" type="application/json">
    {{ "getPrograms-x": {{ "data": {{ "items": [ {json.dumps(ywh_program_data)} ] }} }} }}
    </script></body></html>
    """
    raw_program = ProgramRaw(platform="yeswehack", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "slug" in invalid_programs[0].error_message
# endregion

# region OpenBugBounty Tests
def test_normalize_openbugbounty_success(db_session: Session):
    """Tests the successful normalization of raw Open Bug Bounty data."""
    raw_data = """
    <html><body>
        <div class="bugbounty-list__item">
            <a href="/reports/12345/">Open Bug Bounty Program</a>
        </div>
    </body></html>
    """
    raw_program = ProgramRaw(platform="openbugbounty", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    programs = db_session.exec(select(ProgramClean)).all()
    assert len(programs) == 1
    assert programs[0].name == "Open Bug Bounty Program"

def test_normalize_openbugbounty_malformed_html(db_session: Session):
    """Tests Open Bug Bounty normalization with malformed HTML."""
    raw_data = """
    <html><body>
        <div class="bugbounty-list__item">
            <span>No link here</span>
        </div>
    </body></html>
    """
    raw_program = ProgramRaw(platform="openbugbounty", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "Could not find program name" in invalid_programs[0].error_message
# endregion

# region Synack Tests
def test_normalize_synack_success(db_session: Session):
    """Tests the successful normalization of valid raw Synack data."""
    raw_data = json.dumps([
        {"name": "Synack Program", "url": "https://platform.synack.com/targets/123"}
    ])
    raw_program = ProgramRaw(platform="Synack", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    programs = db_session.exec(select(ProgramClean)).all()
    assert len(programs) == 1
    assert programs[0].name == "Synack Program"
    assert programs[0].platform == "Synack"

def test_normalize_synack_invalid_data(db_session: Session):
    """Tests that invalid Synack data is handled correctly."""
    raw_data = json.dumps([
        {"name": "Invalid Synack"} # Missing URL
    ])
    raw_program = ProgramRaw(platform="Synack", data=raw_data)
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    assert db_session.exec(select(ProgramClean)).first() is None
    invalid_programs = db_session.exec(select(ProgramInvalid)).all()
    assert len(invalid_programs) == 1
    assert "url" in invalid_programs[0].error_message
# endregion

def test_unknown_platform_is_skipped(db_session: Session, capsys):
    """Tests that an unknown platform is skipped without error."""
    raw_program = ProgramRaw(platform="unknown-platform", data="some data")
    db_session.add(raw_program)
    db_session.commit()

    service = NormalizationService()
    service.run(db_session)

    captured = capsys.readouterr()
    assert "Normalization not implemented for platform: unknown-platform" in captured.out
    assert db_session.exec(select(ProgramClean)).first() is None
    assert db_session.exec(select(ProgramInvalid)).first() is None
