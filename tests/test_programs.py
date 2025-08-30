import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from bounty_command_center.main import app
from bounty_command_center.database import get_session
from bounty_command_center.models import Program, Platform, User
from bounty_command_center.auth import get_current_user

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(name="session")
def session_fixture():
    from bounty_command_center import models
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    def get_current_user_override():
        # Return a mock user with a role that has access
        return User(id=1, username="testuser", role="viewer", hashed_password="fakepassword")

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def setup_test_data(session: Session):
    """Helper function to create mock data."""
    platform1 = Platform(name="HackerOne", url="https://hackerone.com")
    platform2 = Platform(name="Bugcrowd", url="https://bugcrowd.com")
    session.add(platform1)
    session.add(platform2)
    session.commit()

    program1 = Program(name="Test Program 1", program_url="https://hackerone.com/test1", platform_id=platform1.id, external_id="h1-1", status="active", offers_bounties=True, min_payout=100)
    program2 = Program(name="Test Program 2", program_url="https://bugcrowd.com/test2", platform_id=platform2.id, external_id="bc-1", status="active", offers_bounties=False)
    program3 = Program(name="Another H1 Program", program_url="https://hackerone.com/test3", platform_id=platform1.id, external_id="h1-2", status="paused", offers_bounties=True, min_payout=500)
    session.add_all([program1, program2, program3])
    session.commit()

def test_read_programs_paginated(client: TestClient, session: Session):
    setup_test_data(session)
    response = client.get("/programs/?limit=2&sort_by=-id")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Another H1 Program"
    assert data["next_cursor"] is not None

    # Fetch next page
    next_cursor = data["next_cursor"]
    response2 = client.get(f"/programs/?limit=2&sort_by=-id&cursor={next_cursor}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["name"] == "Test Program 1"
    assert data2["next_cursor"] is None

def test_read_programs_with_filters(client: TestClient, session: Session):
    setup_test_data(session)
    # Filter by platform
    response = client.get("/programs/?platform_name=HackerOne")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert all(p["platform"]["name"] == "HackerOne" for p in data["items"])

    # Filter by status
    response = client.get("/programs/?status=paused")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Another H1 Program"

    # Filter by min_payout
    response = client.get("/programs/?min_payout=200")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Another H1 Program"

def test_read_single_program(client: TestClient, session: Session):
    setup_test_data(session)
    program = session.exec(select(Program).where(Program.name == "Test Program 1")).one()

    response = client.get(f"/programs/{program.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Program 1"
    assert data["id"] == program.id
    assert data["status"] == "active"

def test_read_nonexistent_program(client: TestClient):
    response = client.get("/programs/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Program not found"}
