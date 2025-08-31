import pytest
from pathlib import Path
from bounty_command_center.report_generator import generate_run_report

def test_generate_run_report_success(tmp_path, mocker):
    """
    Tests that a successful run report is generated correctly.
    """
    # Arrange
    platform = "test_platform"
    stats = {'new': 10, 'invalid': 2, 'updated': 5, 'duration': '123.45 seconds', 'error': None}
    run_id = "test-run-id-123"

    mocker.patch("bounty_command_center.report_generator.Path", return_value=tmp_path)

    # Act
    report_path = generate_run_report(platform, stats, run_id)

    # Assert
    created_files = list(tmp_path.glob(f"run_report_{platform}_*.md"))
    assert len(created_files) == 1

    content = created_files[0].read_text()
    assert f"Harvester Run Report: {platform.title()}" in content
    assert f"- **Run ID:** `{run_id}`" in content
    assert f"- **Run Duration:** {stats['duration']}" in content
    assert f"| New Programs    | {stats['new']}" in content
    assert "Error Summary" not in content # No error section on success

def test_generate_run_report_with_error(tmp_path, mocker):
    """
    Tests that a run report with an error is generated correctly.
    """
    # Arrange
    platform = "error_platform"
    stats = {'new': 0, 'invalid': 0, 'updated': 0, 'duration': '5.01 seconds', 'error': 'Something went wrong'}
    run_id = "test-run-id-456"

    mocker.patch("bounty_command_center.report_generator.Path", return_value=tmp_path)

    # Act
    report_path = generate_run_report(platform, stats, run_id)

    # Assert
    created_files = list(tmp_path.glob(f"run_report_{platform}_*.md"))
    assert len(created_files) == 1

    content = created_files[0].read_text()
    assert "## Error Summary" in content
    assert stats['error'] in content
