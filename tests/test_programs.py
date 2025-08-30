import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from bounty_command_center.main import app
from bounty_command_center.database import get_session
from bounty_command_center.models import Program, Platform, User, Reward
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
        return User(id=1, username="testuser", role="viewer", hashed_password="fakepassword")

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_read_programs(client: TestClient, session: Session):
    # 1. Arrange: Create mock data
    platform1 = Platform(name="HackerOne", url="https://hackerone.com")
    platform2 = Platform(name="Bugcrowd", url="https://bugcrowd.com")
    session.add(platform1)
    session.add(platform2)
    session.commit()

    program1 = Program(name="Test Program 1", program_url="https://hackerone.com/test1", platform_id=platform1.id, scope={})
    program2 = Program(name="Test Program 2", program_url="https://bugcrowd.com/test2", platform_id=platform2.id, scope={})
    program3 = Program(name="Another H1 Program", program_url="https://hackerone.com/test3", platform_id=platform1.id, scope={})
    session.add(program1)
    session.add(program2)
    session.add(program3)
    session.commit()

    # 2. Act: Make request to the endpoint
    response = client.get("/programs/")

    # 3. Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Test Program 1"
    assert data[1]["platform"]["name"] == "Bugcrowd"

def test_read_programs_with_platform_filter(client: TestClient, session: Session):
    # 1. Arrange: Create mock data
    platform1 = Platform(name="HackerOne", url="https://hackerone.com")
    platform2 = Platform(name="Bugcrowd", url="https://bugcrowd.com")
    session.add(platform1)
    session.add(platform2)
    session.commit()

    program1 = Program(name="Test Program 1", program_url="https://hackerone.com/test1", platform_id=platform1.id, scope={})
    program2 = Program(name="Test Program 2", program_url="https://bugcrowd.com/test2", platform_id=platform2.id, scope={})
    program3 = Program(name="Another H1 Program", program_url="https://hackerone.com/test3", platform_id=platform1.id, scope={})
    session.add(program1)
    session.add(program2)
    session.add(program3)
    session.commit()

    # 2. Act: Make request with filter
    response = client.get("/programs/?platform_name=HackerOne")

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Test Program 1"
    assert data[1]["name"] == "Another H1 Program"
    assert all(p["platform"]["name"] == "HackerOne" for p in data)

def test_read_single_program(client: TestClient, session: Session):
    # 1. Arrange
    platform = Platform(name="HackerOne", url="https://hackerone.com")
    session.add(platform)
    session.commit()
    program = Program(name="My Test Program", program_url="https://hackerone.com/mytest", platform_id=platform.id, scope={"in_scope": ["test.com"]})
    session.add(program)
    session.commit()
    session.refresh(program) # to get the ID

    reward = Reward(program_id=program.id, severity="Critical", min_payout=5000, max_payout=10000)
    session.add(reward)
    session.commit()

    # 2. Act
    response = client.get(f"/programs/{program.id}")

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Test Program"
    assert data["id"] == program.id
    assert data["scope"]["in_scope"][0] == "test.com"
    assert len(data["rewards"]) == 1
    assert data["rewards"][0]["severity"] == "Critical"


def test_read_nonexistent_program(client: TestClient):
    response = client.get("/programs/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Program not found"}
