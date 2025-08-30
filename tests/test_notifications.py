import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, create_engine
from bounty_command_center.models import Target, Evidence
from bounty_command_center.evidence_manager import EvidenceManager

# Create a new engine for the test database
engine = create_engine("sqlite:///:memory:")

@pytest.fixture(name="db_session")
def db_session_fixture():
    """Create a new database session for each test."""
    from bounty_command_center.models import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@patch("bounty_command_center.evidence_manager.NotificationManager")
def test_create_evidence_sends_high_severity_notification(
    mock_notification_manager, db_session: Session
):
    """
    Test that a high-severity notification is sent when evidence with
    severity "High" is created.
    """
    # Arrange
    mock_manager_instance = mock_notification_manager.return_value
    evidence_manager = EvidenceManager()
    target = Target(name="Test Target", url="http://test.com", scope=["http://test.com"])
    db_session.add(target)
    db_session.commit()

    # Act
    evidence_manager.create_evidence(
        db=db_session,
        finding_summary="Test high-severity finding",
        reproduction_steps="1. Do this\n2. Do that",
        severity="High",
        status="new",
        target_id=target.id,
    )

    # Assert
    mock_manager_instance.send_high_severity_notification.assert_called_once_with(
        target_name="Test Target",
        finding_summary="Test high-severity finding",
    )

@patch("bounty_command_center.evidence_manager.NotificationManager")
def test_create_evidence_sends_critical_severity_notification(
    mock_notification_manager, db_session: Session
):
    """
    Test that a high-severity notification is sent when evidence with
    severity "Critical" is created.
    """
    # Arrange
    mock_manager_instance = mock_notification_manager.return_value
    evidence_manager = EvidenceManager()
    target = Target(name="Test Target", url="http://test.com", scope=["http://test.com"])
    db_session.add(target)
    db_session.commit()

    # Act
    evidence_manager.create_evidence(
        db=db_session,
        finding_summary="Test critical-severity finding",
        reproduction_steps="1. Do this\n2. Do that",
        severity="Critical",
        status="new",
        target_id=target.id,
    )

    # Assert
    mock_manager_instance.send_high_severity_notification.assert_called_once_with(
        target_name="Test Target",
        finding_summary="Test critical-severity finding",
    )

@patch("bounty_command_center.evidence_manager.NotificationManager")
def test_create_evidence_does_not_send_low_severity_notification(
    mock_notification_manager, db_session: Session
):
    """
    Test that a notification is not sent when evidence with a
    low severity (e.g., "Informational") is created.
    """
    # Arrange
    mock_manager_instance = mock_notification_manager.return_value
    evidence_manager = EvidenceManager()
    target = Target(name="Test Target", url="http://test.com", scope=["http://test.com"])
    db_session.add(target)
    db_session.commit()

    # Act
    evidence_manager.create_evidence(
        db=db_session,
        finding_summary="Test informational finding",
        reproduction_steps="1. Do this\n2. Do that",
        severity="Informational",
        status="new",
        target_id=target.id,
    )

    # Assert
    mock_manager_instance.send_high_severity_notification.assert_not_called()
