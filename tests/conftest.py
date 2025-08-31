import os
import pathlib
import pytest
from sqlmodel import SQLModel, Session, create_engine, text
from sqlalchemy import event

# 1) Per-worker DB path (parallel-safe)
def db_path(tmp_path_factory) -> pathlib.Path:
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    base = tmp_path_factory.mktemp("db")
    return base / f"test_{worker_id}.sqlite3"

# 2) Enable SQLite foreign keys
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture(scope="session")
def db_file(tmp_path_factory):
    """A temporary database file path that is unique per worker."""
    path = db_path(tmp_path_factory)
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

@pytest.fixture(scope="session")
def engine(db_file):
    """
    A single, session-scoped SQLAlchemy engine that creates the schema once.
    """
    url = f"sqlite:///{db_file}"
    engine = create_engine(
        url,
        echo=False, # Set to True to see SQL queries
        connect_args={"check_same_thread": False}, # Needed for SQLite
        future=True,
    )
    event.listen(engine, "connect", enable_sqlite_fk)

    # Import all models BEFORE create_all so metadata is complete
    from bounty_command_center import models  # noqa: F401

    # Create schema once per session
    SQLModel.metadata.create_all(engine)
    yield engine

    # Dispose engine and clean DB file after session
    engine.dispose()
    try:
        pathlib.Path(db_file).unlink(missing_ok=True)
    except Exception:
        pass

@pytest.fixture(scope="session")
def connection(engine):
    """A single, shared connection for the whole session, enabling fast transaction-based rollbacks."""
    conn = engine.connect()
    yield conn
    conn.close()

@pytest.fixture
def db_session(connection):
    """
    A per-test fixture that wraps the test in a transaction and rolls it back afterwards.
    This is much faster than creating and dropping the schema for every test.
    """
    trans = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        # Roll back test data (schema persists)
        trans.rollback()

@pytest.fixture
def with_clean_tables(db_session):
    """
    Optional utility to truncate tables between phases inside one test function.
    """
    table_names = ["programraw", "programclean", "programinvalid", "target", "evidence", "user"]
    for t in table_names:
        db_session.exec(text(f"DELETE FROM {t}"))
    db_session.commit()
    return True

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    """Auto-mock redis for all tests in this module."""
    mock_redis_client = mocker.MagicMock()
    mock_lock = mocker.MagicMock()
    mock_lock.acquire.return_value = True
    mock_redis_client.lock.return_value = mock_lock
    mocker.patch("redis.StrictRedis", return_value=mock_redis_client)
    return mock_redis_client
