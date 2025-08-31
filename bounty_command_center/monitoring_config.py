import os
from dataclasses import dataclass

def get_env_bool(key: str, default: bool) -> bool:
    """
    Retrieves a boolean value from an environment variable.
    The function is case-insensitive and interprets 'true', '1', 't', 'yes', 'y' as True.
    """
    val = os.getenv(key, str(default)).lower()
    return val in ('true', '1', 't', 'yes', 'y')

@dataclass
class MonitoringConfig:
    """
    Holds all configuration settings for the resource monitoring feature.
    Values are loaded from environment variables with sensible defaults.
    """
    cpu_limit: float = float(os.getenv("RUNNER_CPU_LIMIT", "0.80"))
    mem_limit: float = float(os.getenv("RUNNER_MEM_LIMIT", "0.75"))
    breach_window_seconds: int = int(os.getenv("RUNNER_BREACH_WINDOW", "30"))
    poll_interval_seconds: int = int(os.getenv("RUNNER_POLL_INTERVAL", "1"))
    smoothing_method: str = os.getenv("RUNNER_SMOOTHING", "ema")
    smoothing_alpha: float = float(os.getenv("RUNNER_SMOOTHING_ALPHA", "0.3"))
    kill_grace_seconds: int = int(os.getenv("RUNNER_KILL_GRACE", "5"))
    abort_enable: bool = get_env_bool("RUNNER_ABORT_ENABLE", True)
    abort_dry_run: bool = get_env_bool("RUNNER_ABORT_DRY_RUN", False)

# A single, global instance of the monitoring configuration.
# This can be imported and used throughout the application.
monitoring_config = MonitoringConfig()
