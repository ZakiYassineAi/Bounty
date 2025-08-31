import pytest
from sqlmodel import Session, create_engine, select
from bounty_command_center.models import ProgramRaw, ProgramClean, SQLModel
from bounty_command_center.normalization_service import NormalizationService
from bounty_command_center import models


def test_normalize_intigriti():
    """
    Tests the normalization of raw Intigriti data.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        raw_data = '[{"name": "Intigriti Program", "url": "https://intigriti.com/program"}]'
        raw_program = ProgramRaw(platform="intigriti", data=raw_data)
        session.add(raw_program)
        session.commit()

        service = NormalizationService()
        service.run(session)

        programs = session.exec(select(ProgramClean)).all()
        assert len(programs) == 1
        assert programs[0].name == "Intigriti Program"
        assert programs[0].platform == "intigriti"

def test_normalize_yeswehack():
    """
    Tests the normalization of raw YesWeHack data.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        raw_data = """
        <html>
            <body>
                <script id="ng-state" type="application/json">
                    {
                        "getPrograms-{\\"0\\":\\"\\",\\"1\\":\\"bug-bounty\\"}": {
                            "data": {
                                "items": [
                                    {
                                        "title": "YesWeHack Program",
                                        "slug": "yeswehack-program"
                                    }
                                ]
                            }
                        }
                    }
                </script>
            </body>
        </html>
        """
        raw_program = ProgramRaw(platform="yeswehack", data=raw_data)
        session.add(raw_program)
        session.commit()

        service = NormalizationService()
        service.run(session)

        programs = session.exec(select(ProgramClean)).all()
        assert len(programs) == 1
        assert programs[0].name == "YesWeHack Program"
        assert programs[0].platform == "yeswehack"

def test_normalize_openbugbounty():
    """
    Tests the normalization of raw Open Bug Bounty data.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # This HTML is a simplified representation of the actual page structure.
        raw_data = """
        <html>
            <body>
                <div class="bugbounty-list__item">
                    <a href="/reports/12345/">Open Bug Bounty Program</a>
                </div>
            </body>
        </html>
        """
        raw_program = ProgramRaw(platform="openbugbounty", data=raw_data)
        session.add(raw_program)
        session.commit()

        service = NormalizationService()
        service.run(session)

        programs = session.exec(select(ProgramClean)).all()
        assert len(programs) == 1
        assert programs[0].name == "Open Bug Bounty Program"
        assert programs[0].platform == "openbugbounty"
