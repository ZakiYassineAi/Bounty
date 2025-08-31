import pytest
import asyncio
import os
import signal
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
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

@pytest.mark.asyncio
async def test_runner_aborted_scan(target):
    """
    Tests that a runner correctly handles an aborted scan.
    """
    runner = SubfinderRunner()  # We can use any runner for this test

    # Mock the command result for an aborted scan
    mock_result = CommandResult(
        command="",
        stdout="",
        stderr="Aborted",
        return_code=1,
            aborted=True,
            abort_reason="resource_limit",
            time_to_abort=3.14,
            peak_cpu=0.9,
            avg_cpu=0.85,
            peak_mem=0.8,
            avg_mem=0.78,
            samples_collected=5
    )

    # Patch the _run_single_command method
    runner._run_single_command = AsyncMock(return_value=mock_result)

    # Run the runner
    evidence_list = await runner.run(target)

    # Assertions
    assert len(evidence_list) == 1

    # The summary is now dynamically generated, so we build the expected string
    from bounty_command_center.monitoring_config import monitoring_config
    expected_summary = (
        f"Scan aborted due to sustained resource usage "
        f"(CPU > {monitoring_config.cpu_limit:.0%} or "
        f"Mem > {monitoring_config.mem_limit:.0%}) for "
        f"{monitoring_config.breach_window_seconds}s."
    )
    assert evidence_list[0].finding_summary == expected_summary
    assert evidence_list[0].severity == "Informational"
    assert "Peak CPU: 90.00%" in evidence_list[0].reproduction_steps


@pytest.mark.asyncio
@patch('bounty_command_center.async_runner.asyncio.sleep', new_callable=AsyncMock)
@patch('bounty_command_center.async_runner.psutil.Process')
async def test_monitor_ignores_short_spikes(mock_psutil_process, mock_sleep, target):
    """
    Tests that the resource monitor does not abort the process for short-lived resource spikes.
    """
    # Mock a process that spikes once, then returns to normal
    mock_proc_instance = MagicMock()
    mock_proc_instance.is_running.return_value = True
    mock_proc_instance.cpu_percent.side_effect = [0.0, 95.0, 10.0, 10.0, 10.0, 10.0] # Spike, then normal
    mock_proc_instance.memory_info.return_value.rss = 100 * 1024 * 1024 # 100MB
    type(mock_proc_instance).returncode = 0 # Simulate process finishing
    mock_psutil_process.return_value = mock_proc_instance

    # Mock the subprocess to control its lifecycle
    mock_subprocess = AsyncMock()
    mock_subprocess.communicate.return_value = (b"output", b"")
    type(mock_subprocess).pid = 1234
    type(mock_subprocess).returncode = 0

    with patch.dict(os.environ, {"RUNNER_BREACH_WINDOW": "3", "RUNNER_POLL_INTERVAL": "1"}), \
         patch('bounty_command_center.async_runner.asyncio.create_subprocess_exec', return_value=mock_subprocess):

        import importlib
        from bounty_command_center import async_runner, monitoring_config
        importlib.reload(monitoring_config)
        importlib.reload(async_runner)

        runner = async_runner.AsyncToolRunner()
        result = await runner._run_single_command(["echo", "test"], timeout=10)

        assert not result.aborted
        assert result.abort_reason is None

@pytest.mark.asyncio
@patch('bounty_command_center.async_runner.os.getpgid')
@patch('bounty_command_center.async_runner.time.time')
@patch('bounty_command_center.async_runner.os.killpg')
@patch('bounty_command_center.async_runner.asyncio.sleep', new_callable=AsyncMock)
@patch('bounty_command_center.async_runner.psutil.Process')
async def test_monitor_aborts_on_sustained_load(mock_psutil_process, mock_sleep, mock_killpg, mock_time, mock_getpgid, target):
    """
    Tests that the resource monitor aborts the process for sustained high resource usage.
    This test mocks the passage of time to ensure deterministic behavior.
    """
    # Mock time to control the breach window calculation
    mock_time.side_effect = [1000, 1001, 1002, 1003, 1004, 1005]
    mock_getpgid.return_value = 1234 # Mock the process group ID call

    mock_proc_instance = MagicMock()
    mock_proc_instance.is_running.return_value = True
    mock_proc_instance.cpu_percent.return_value = 95.0 # Sustained high usage
    mock_proc_instance.memory_info.return_value.rss = 100 * 1024 * 1024
    type(mock_proc_instance).returncode = None # psutil process is running
    mock_psutil_process.return_value = mock_proc_instance

    mock_subprocess = AsyncMock()
    type(mock_subprocess).pid = 1234
    # The subprocess's returncode should be None while it's "running"
    type(mock_subprocess).returncode = PropertyMock(return_value=None)

    process_killed_event = asyncio.Event()
    def set_event_on_kill(*args, **kwargs):
        # When kill is called, update the mock process's returncode and set the event
        type(mock_subprocess).returncode = PropertyMock(return_value=-signal.SIGKILL)
        process_killed_event.set()
    mock_killpg.side_effect = set_event_on_kill

    async def mock_communicate():
        await process_killed_event.wait()
        return (b'', b'process was killed')
    mock_subprocess.communicate.side_effect = mock_communicate

    with patch.dict(os.environ, {"RUNNER_BREACH_WINDOW": "2", "RUNNER_POLL_INTERVAL": "1"}), \
         patch('bounty_command_center.async_runner.asyncio.create_subprocess_exec', return_value=mock_subprocess):

        import importlib
        from bounty_command_center import async_runner, monitoring_config
        importlib.reload(monitoring_config)
        importlib.reload(async_runner)

        runner = async_runner.AsyncToolRunner()
        result = await runner._run_single_command(["echo", "test"], timeout=10)

        assert result.aborted
        assert result.abort_reason == "resource_limit"
        mock_killpg.assert_called()

@pytest.mark.asyncio
@patch('bounty_command_center.async_runner.os.killpg')
@patch('bounty_command_center.async_runner.asyncio.sleep', new_callable=AsyncMock)
@patch('bounty_command_center.async_runner.psutil.Process')
async def test_monitor_dry_run_does_not_kill(mock_psutil_process, mock_sleep, mock_killpg, target):
    """
    Tests that dry-run mode logs the intent to abort but does not actually kill the process.
    """
    mock_proc_instance = MagicMock()
    mock_proc_instance.is_running.return_value = True
    mock_proc_instance.cpu_percent.return_value = 95.0
    mock_proc_instance.memory_info.return_value.rss = 100 * 1024 * 1024
    type(mock_proc_instance).returncode = None
    mock_psutil_process.return_value = mock_proc_instance

    mock_subprocess = AsyncMock()
    # In dry run, process is not killed, so it should time out or finish
    mock_subprocess.communicate.side_effect = asyncio.TimeoutError
    type(mock_subprocess).pid = 1234
    type(mock_subprocess).returncode = None

    with patch.dict(os.environ, {
        "RUNNER_BREACH_WINDOW": "2",
        "RUNNER_POLL_INTERVAL": "1",
        "RUNNER_ABORT_DRY_RUN": "true"
    }), patch('bounty_command_center.async_runner.asyncio.create_subprocess_exec', return_value=mock_subprocess):

        import importlib
        from bounty_command_center import async_runner, monitoring_config
        importlib.reload(monitoring_config)
        importlib.reload(async_runner)

        runner = async_runner.AsyncToolRunner()
        # Expect a timeout because the process is never killed in dry run
        await runner._run_single_command(["echo", "test"], timeout=5)

        mock_killpg.assert_not_called()
