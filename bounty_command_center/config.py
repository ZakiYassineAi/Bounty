import yaml
from pydantic import BaseModel, ValidationError
from pathlib import Path

from .logging_setup import get_logger

log = get_logger(__name__)

# --- Pydantic Models for Validation ---


class ToolSetting(BaseModel):
    """Defines the settings for a single tool."""

    path: str


class ToolsConfig(BaseModel):
    nmap: ToolSetting = ToolSetting(path="/usr/bin/nmap")
    sqlmap: ToolSetting = ToolSetting(path="/usr/bin/sqlmap")
    dirb: ToolSetting = ToolSetting(path="/usr/bin/dirb")


class ApiKeysConfig(BaseModel):
    virustotal: str = "YOUR_API_KEY_HERE"
    shodan: str = "YOUR_API_KEY_HERE"


class ReportingConfig(BaseModel):
    export_directory: str = "reports"
    filename_template: str = "{target_name}-{evidence_id}-{timestamp}.md"


class AsyncRunnerConfig(BaseModel):
    default_timeout: int = 60


class AuthConfig(BaseModel):
    jwt_secret_key: str = "a_very_secret_key_that_should_be_changed"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30


class Settings(BaseModel):
    tools: ToolsConfig = ToolsConfig()
    api_keys: ApiKeysConfig = ApiKeysConfig()
    reporting: ReportingConfig = ReportingConfig()
    async_runner: AsyncRunnerConfig = AsyncRunnerConfig()
    auth: AuthConfig = AuthConfig()


# --- Config Loading Logic ---


def load_config(config_path: Path = Path("config.yaml")) -> Settings:
    """
    Loads configuration from a YAML file and validates it using Pydantic.

    If the config file does not exist, default settings are used.
    If the file is invalid, an error is logged and default settings are used.
    """
    if config_path.exists():
        log.info("Loading configuration from file", path=str(config_path))
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                log.warning("Config file is empty, using default settings.")
                return Settings()

            return Settings.parse_obj(config_data)

        except yaml.YAMLError as e:
            log.error("Error parsing YAML config file, using defaults.", error=str(e))
            return Settings()
        except ValidationError as e:
            log.error(
                "Configuration validation failed, using defaults.", errors=e.errors()
            )
            return Settings()
        except Exception:
            log.exception(
                "An unexpected error occurred loading config, using defaults."
            )
            return Settings()
    else:
        log.warning(
            "Config file not found, using default settings.", path=str(config_path)
        )
        return Settings()


# Load the settings once on startup and make it available for import
settings = load_config()
