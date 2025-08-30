import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from bounty_command_center.models import Target, Evidence
from bounty_command_center.subfinder_runner import SubfinderRunner
from bounty_command_center.dalfox_runner import DalfoxRunner
from bounty_command_center.sqlmap_runner import SqlmapRunner
from bounty_command_center.async_runner import CommandResult

@pytest.fixture
def target():
    return Target(id=1, name="test.com", url="test.com", scope=["*.test.com"])

@pytest.mark.asyncio
async def test_subfinder_runner(target):
    """
    Tests the SubfinderRunner by mocking the command execution.
    """
    runner = SubfinderRunner()

    # Mock the command result
    mock_stdout = '{"host":"blog.test.com"}\n{"host":"shop.test.com"}'
    mock_result = CommandResult(command="", stdout=mock_stdout, stderr="", return_code=0)

    # Patch the _run_single_command method
    runner._run_single_command = AsyncMock(return_value=mock_result)

    # Run the runner
    evidence_list = await runner.run(target)

    # Assertions
    assert len(evidence_list) == 2
    assert evidence_list[0].finding_summary == "Subdomain discovered: blog.test.com"
    assert evidence_list[0].severity == "Informational"
    assert evidence_list[1].finding_summary == "Subdomain discovered: shop.test.com"

@pytest.mark.asyncio
async def test_dalfox_runner(target):
    """
    Tests the DalfoxRunner by mocking the command execution.
    """
    runner = DalfoxRunner()

    # Mock the command result
    mock_stdout = '{"pocs": [{"message_str": "Reflected XSS in `q` parameter", "severity": "High", "data": "http://test.com?q=<script>alert(1)</script>"}]}'
    mock_result = CommandResult(command="", stdout=mock_stdout, stderr="", return_code=0)

    # Patch the _run_single_command method
    runner._run_single_command = AsyncMock(return_value=mock_result)

    # Run the runner
    evidence_list = await runner.run(target)

    # Assertions
    assert len(evidence_list) == 1
    assert evidence_list[0].finding_summary == "Reflected XSS in `q` parameter"
    assert evidence_list[0].severity == "High"
    assert "http://test.com?q=<script>alert(1)</script>" in evidence_list[0].reproduction_steps

@pytest.mark.asyncio
async def test_sqlmap_runner(target):
    """
    Tests the SqlmapRunner by mocking the command execution.
    """
    runner = SqlmapRunner()

    # Mock the command result
    mock_stdout = '{"type": "vulnerability", "data": {"title": "Boolean-based blind", "type": "boolean-based blind"}}\n{"type": "vulnerability", "data": {"title": "Error-based", "type": "error-based"}}'
    mock_result = CommandResult(command="", stdout=mock_stdout, stderr="", return_code=0)

    # Patch the _run_single_command method
    runner._run_single_command = AsyncMock(return_value=mock_result)

    # Run the runner
    evidence_list = await runner.run(target)

    # Assertions
    assert len(evidence_list) == 2
    assert "Boolean-based blind" in evidence_list[0].finding_summary
    assert evidence_list[0].severity == "Critical"
    assert "Error-based" in evidence_list[1].finding_summary
    assert evidence_list[1].severity == "High"
