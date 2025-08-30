import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from bounty_command_center.main import app
from bounty_command_center.database import get_session
from bounty_command_center.models import Evidence, Target, User
from bounty_command_center.auth import get_current_user

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# --- Test Fixtures ---

@pytest.fixture(name="session")
def session_fixture():
    # Importing the models here ensures they are registered with SQLModel
    # before the tables are created.
    from bounty_command_center import models
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session, monkeypatch):
    # Prevent the real db creation from running during tests
    monkeypatch.setattr("bounty_command_center.main.create_db_and_tables", lambda: None)

    def get_session_override():
        return session

    def get_current_user_override():
        # Return a mock user with a role that has access
        return User(id=1, username="testuser", role="admin", password="fakepassword")

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()

# --- Tests ---

def test_generate_pdf_report_for_evidence_unit(session: Session):
    """
    Unit test for the PDF generation function.
    """
    # 1. Create mock data
    target = Target(name="Test Target", url="http://test.com", scope=["http://test.com"])
    session.add(target)
    session.commit()
    session.refresh(target)

    evidence = Evidence(
        finding_summary="Test XSS",
        reproduction_steps="1. Go to page\n2. Inject payload",
        severity="High",
        target_id=target.id,
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)

    # 2. Call the function
    from bounty_command_center.report_generator import generate_pdf_report_for_evidence
    pdf_bytes = generate_pdf_report_for_evidence(db=session, evidence_id=evidence.id)

    # 3. Assert the result
    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF-") # Check for PDF magic number

def test_export_evidence_report_integration(client: TestClient, session: Session):
    """
    Integration test for the evidence export endpoint.
    """
    # 1. Create mock data in the test database
    target = Target(name="Test Target", url="http://test.com", scope=["http://test.com"])
    session.add(target)
    session.commit()
    session.refresh(target)

    evidence = Evidence(
        finding_summary="Test SQLi",
        reproduction_steps="1. Go to login\n2. Enter ' OR 1=1 --",
        severity="Critical",
        target_id=target.id
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)

    # 2. Make a request to the endpoint
    response = client.get(f"/api/reports/export/evidence/{evidence.id}")

    # 3. Assert the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == f"attachment; filename=evidence_report_{evidence.id}.pdf"
    assert response.content.startswith(b"%PDF-")

def test_export_evidence_report_not_found(client: TestClient, session: Session):
    """
    Test the endpoint with a non-existent evidence ID.
    """
    response = client.get("/api/reports/export/evidence/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report could not be generated. Evidence not found or error in generation."}
