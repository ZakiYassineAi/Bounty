import os
import importlib
from unittest.mock import patch

def test_monitoring_config_defaults():
    """
    Tests that the monitoring config loads with default values.
    """
    # Ensure no environment variables are set for this test
    with patch.dict(os.environ, {}, clear=True):
        from bounty_command_center import monitoring_config
        importlib.reload(monitoring_config)
        config = monitoring_config.MonitoringConfig()

        assert config.cpu_limit == 0.80
        assert config.mem_limit == 0.75
        assert config.breach_window_seconds == 30
        assert config.poll_interval_seconds == 1
        assert config.smoothing_alpha == 0.3
        assert config.kill_grace_seconds == 5
        assert config.abort_enable is True
        assert config.abort_dry_run is False

def test_monitoring_config_overrides():
    """
    Tests that environment variables correctly override the default config values.
    """
    mock_env = {
        "RUNNER_CPU_LIMIT": "0.55",
        "RUNNER_MEM_LIMIT": "0.65",
        "RUNNER_BREACH_WINDOW": "15",
        "RUNNER_POLL_INTERVAL": "2",
        "RUNNER_SMOOTHING_ALPHA": "0.5",
        "RUNNER_KILL_GRACE": "10",
        "RUNNER_ABORT_ENABLE": "false",
        "RUNNER_ABORT_DRY_RUN": "true",
    }
    with patch.dict(os.environ, mock_env, clear=True):
        from bounty_command_center import monitoring_config
        importlib.reload(monitoring_config)
        config = monitoring_config.MonitoringConfig()

        assert config.cpu_limit == 0.55
        assert config.mem_limit == 0.65
        assert config.breach_window_seconds == 15
        assert config.poll_interval_seconds == 2
        assert config.smoothing_alpha == 0.5
        assert config.kill_grace_seconds == 10
        assert config.abort_enable is False
        assert config.abort_dry_run is True

    # It's good practice to restore the original state after the test
    from bounty_command_center import monitoring_config
    importlib.reload(monitoring_config)
