import pytest
from unittest.mock import MagicMock, patch, ANY
from bounty_command_center.tasks import harvest_platform, schedule_all_platform_harvests
from sqlmodel import Session

@patch("bounty_command_center.tasks.generate_run_report")
@patch("bounty_command_center.tasks.NormalizationService")
@patch("bounty_command_center.tasks.HarvesterAggregator")
@patch("bounty_command_center.tasks.get_session")
def test_harvest_platform_task(mock_get_session, mock_aggregator_class, mock_normalizer_class, mock_report_gen):
    """
    Tests the harvest_platform Celery task orchestrates correctly.
    """
    # Arrange
    mock_aggregator_instance = MagicMock()
    mock_aggregator_class.return_value = mock_aggregator_instance

    mock_normalizer_instance = MagicMock()
    mock_normalizer_class.return_value = mock_normalizer_instance
    mock_stats = {'new': 5, 'invalid': 1}
    mock_normalizer_instance.run.return_value = mock_stats

    mock_db_session = MagicMock(spec=Session)
    mock_get_session.return_value.__enter__.return_value = mock_db_session

    platform_to_test = "intigriti"

    # Act
    harvest_platform(platform_to_test)

    # Assert
    mock_aggregator_instance.run.assert_called_once()
    assert mock_aggregator_instance.run.call_args.args[0] == mock_db_session
    assert mock_aggregator_instance.run.call_args.args[1] == platform_to_test
    assert isinstance(mock_aggregator_instance.run.call_args.kwargs['run_id'], str)

    mock_normalizer_instance.run.assert_called_once_with(mock_db_session, platform_to_test)

    # Check that the report generator was called with the stats and a run_id
    mock_report_gen.assert_called_once()
    call_args, _ = mock_report_gen.call_args
    assert call_args[0] == platform_to_test
    assert call_args[1]['new'] == 5
    assert 'duration' in call_args[1]
    assert 'error' in call_args[1]
    assert isinstance(call_args[2], str) # run_id


@patch("bounty_command_center.tasks.harvest_platform.apply_async")
def test_schedule_all_platform_harvests_task(mock_apply_async):
    """
    Tests the schedule_all_platform_harvests Celery task.
    """
    # Arrange
    platforms = ["intigriti", "yeswehack", "openbugbounty", "synack"]

    # Act
    schedule_all_platform_harvests()

    # Assert
    assert mock_apply_async.call_count == len(platforms)

    for platform in platforms:
        found_call = False
        for call in mock_apply_async.call_args_list:
            if call.kwargs.get('args') == [platform] and 'countdown' in call.kwargs:
                found_call = True
                break
        assert found_call, f"apply_async not called for platform {platform} with a countdown"
