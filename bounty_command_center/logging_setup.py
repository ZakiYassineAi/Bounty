import logging
import sys
import structlog


def setup_logging(log_to_file: bool = False):
    """
    Configures structlog for structured logging.
    Logs to console by default, or to 'app.log' if log_to_file is True.
    """
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
        level=logging.INFO,
        handlers=[
            logging.NullHandler()
        ],  # Don't want basicConfig to set up any handlers
    )

    if log_to_file:
        # Log to a file in JSON format
        handler = logging.FileHandler("app.log", mode="w")
        renderer = structlog.processors.JSONRenderer()
    else:
        # Log to the console with colors
        handler = logging.StreamHandler(sys.stdout)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
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
    root_logger.setLevel(logging.INFO)


def get_logger(name: str):
    """
    Returns a configured structlog logger instance.
    """
    return structlog.get_logger(name)
