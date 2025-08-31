import pytest
from sqlmodel import text
from bounty_command_center.database import get_session

def test_get_session_context_manager(db_session):
    """
    Tests that get_session() works as a context manager and provides a valid session.
    This is a regression test for the missing @contextmanager decorator.
    """
    # The db_session fixture already sets up the database and tables.
    # We are testing the application's get_session function directly here.
    try:
        with get_session() as db:
            result = db.exec(text("SELECT 1")).first()
            assert result[0] == 1
    except Exception as e:
        pytest.fail(f"get_session context manager failed with an exception: {e}")
