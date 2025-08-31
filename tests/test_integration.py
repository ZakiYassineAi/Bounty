import sys
import os
import pytest
import importlib
from unittest.mock import patch

@pytest.mark.asyncio
async def test_resource_monitor_integration_aborts_process():
    """
    Integration test to verify that the resource monitor can successfully
    detect and abort a real, resource-intensive process.
    """
    # Set aggressive monitoring config via environment variables to ensure
    # the test runs quickly and reliably triggers the abort mechanism.
    mock_env = {
        "RUNNER_CPU_LIMIT": "0.10",          # 10% CPU limit
        "RUNNER_BREACH_WINDOW": "2",         # 2-second breach window
        "RUNNER_POLL_INTERVAL": "1",         # 1-second polling
        "RUNNER_ABORT_ENABLE": "true",
        "RUNNER_ABORT_DRY_RUN": "false",
    }

    original_env = os.environ.copy()
    os.environ.update(mock_env)

    # Reload modules to ensure they pick up the new environment variables.
    # This is critical for the test's correctness.
    from bounty_command_center import async_runner, monitoring_config
    importlib.reload(monitoring_config)
    importlib.reload(async_runner)

    try:
        runner = async_runner.AsyncToolRunner()
        command = [sys.executable, "tests/cpu_burner.py"]

        # We expect the command to be aborted, not to time out.
        # The timeout is a safeguard for the test itself.
        result = await runner._run_single_command(command, timeout=10)

        assert result.aborted is True
        assert result.abort_reason == "resource_limit"
        assert result.time_to_abort is not None
        assert result.samples_collected > 0
        assert result.peak_cpu > 0 # It should have registered some CPU usage

    finally:
        # Restore the environment and reload modules to prevent side effects
        # on other tests. This is crucial for test suite stability.
        os.environ.clear()
        os.environ.update(original_env)
        importlib.reload(monitoring_config)
        importlib.reload(async_runner)
