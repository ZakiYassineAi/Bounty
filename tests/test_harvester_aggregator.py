import pytest
from unittest.mock import MagicMock
from sqlmodel import Session, select
from bounty_command_center.models import ProgramRaw
from bounty_command_center.harvester_aggregator import HarvesterAggregator

def test_aggregator_runs_harvester_and_saves_data(db_session: Session, mocker):
    """
    Tests that the HarvesterAggregator can run a mocked harvester
    and correctly save the returned raw data to the database.
    """
    # Arrange
    platform_to_test = "intigriti"
    mock_harvester_instance = MagicMock()
    mock_harvester_instance.fetch_raw_data.return_value = ("some raw data", "new-etag", "new-last-modified")

    mocker.patch(
        "bounty_command_center.harvester_aggregator.IntigritiHarvester",
        return_value=mock_harvester_instance,
    )

    aggregator = HarvesterAggregator()

    # Act
    aggregator.run(db_session, platform_to_test)

    # Assert
    mock_harvester_instance.fetch_raw_data.assert_called_once()
    saved_programs = db_session.exec(select(ProgramRaw)).all()
    assert len(saved_programs) == 1
    assert saved_programs[0].platform == platform_to_test

def test_aggregator_skips_if_lock_is_held(db_session: Session, mocker, capsys):
    """
    Tests that the aggregator does not run if the redis lock is already held.
    """
    # Arrange
    mock_redis_client = mocker.patch("redis.StrictRedis").return_value
    mock_lock = MagicMock()
    mock_lock.acquire.return_value = False # Simulate lock being held
    mock_redis_client.lock.return_value = mock_lock

    mock_harvester_class = mocker.patch("bounty_command_center.harvester_aggregator.IntigritiHarvester")

    aggregator = HarvesterAggregator()

    # Act
    aggregator.run(db_session, "intigriti")

    # Assert
    mock_harvester_class.assert_not_called()
    captured = capsys.readouterr()
    assert "Could not acquire lock for intigriti" in captured.out

def test_aggregator_handles_unknown_platform(db_session: Session, mocker, capsys):
    """
    Tests that the aggregator handles an unknown platform gracefully.
    """
    # Arrange
    aggregator = HarvesterAggregator()

    # Act
    aggregator.run(db_session, "unknown_platform")

    # Assert
    captured = capsys.readouterr()
    assert "Unknown platform: unknown_platform" in captured.out
    # Ensure no data was written to the db
    programs = db_session.exec(select(ProgramRaw)).all()
    assert len(programs) == 0

def test_aggregator_handles_no_new_data(db_session: Session, mocker):
    """
    Tests that the aggregator handles the case where a harvester returns no new data.
    """
    # Arrange
    mock_harvester_instance = MagicMock()
    # Simulate the harvester finding no new data
    mock_harvester_instance.fetch_raw_data.return_value = (None, None, None)
    mocker.patch(
        "bounty_command_center.harvester_aggregator.IntigritiHarvester",
        return_value=mock_harvester_instance,
    )
    aggregator = HarvesterAggregator()

    # Act
    aggregator.run(db_session, "intigriti")

    # Assert
    mock_harvester_instance.fetch_raw_data.assert_called_once()
    # Ensure no data was written to the db
    programs = db_session.exec(select(ProgramRaw)).all()
    assert len(programs) == 0
