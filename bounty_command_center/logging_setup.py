import logging
import sys
import os
import structlog

def setup_logging(log_level: str = "INFO"):
    """
    Configures structlog for structured logging.
    The output format is controlled by the LOG_FORMAT environment variable.
    - 'console': (Default) Human-readable, colored output for development.
    - 'json':    Machine-readable JSON output for production.
    """
    log_format = os.getenv("LOG_FORMAT", "console").lower()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure the standard logging library to be a sink for structlog
    logging.basicConfig(
        format="%(message)s",
        level=log_level.upper(),
        handlers=[logging.NullHandler()],
    )

    if log_format == "json":
        # Production-ready JSON logs to stdout
        handler = logging.StreamHandler(sys.stdout)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development-friendly console logs
        handler = logging.StreamHandler(sys.stdout)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processor=renderer,
    )

    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

def get_logger(name: str):
    """
    Returns a configured structlog logger instance.
    """
    return structlog.get_logger(name)
