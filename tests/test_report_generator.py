import pytest
from pathlib import Path
from bounty_command_center.report_generator import generate_run_report

def test_generate_run_report(tmp_path, mocker):
    """
    Tests that the generate_run_report function creates a report
    with the correct content and filename in a temporary directory.
    """
    # Arrange
    platform = "test_platform"
    stats = {'new': 10, 'invalid': 2, 'updated': 5}

    # Mock the Path object to control where the report is written.
    # The Path("reports") call inside the function will now resolve to our tmp_path.
    mocker.patch("bounty_command_center.report_generator.Path", return_value=tmp_path)

    # Act
    report_path = generate_run_report(platform, stats)

    # Assert
    assert report_path is not None
    # The final path will be inside tmp_path, e.g., /tmp/pytest-of-user/pytest-0/test_generate_run_report0/run_report_...
    # So we check if any file with the expected pattern exists in the temp dir.
    created_files = list(tmp_path.glob(f"run_report_{platform}_*.md"))
    assert len(created_files) == 1

    content = created_files[0].read_text()
    assert f"Harvester Run Report: {platform.title()}" in content
    assert f"| New Programs    | {stats['new']}" in content
    assert f"| Invalid Records | {stats['invalid']}" in content
    assert f"| Updated Programs| {stats['updated']}" in content
