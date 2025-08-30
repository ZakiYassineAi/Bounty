import logging
import sys
import structlog

def setup_logging():
    """
    Configures structlog for structured, context-aware, and readable logging.
    """
    # Define the chain of processors that will enrich the log records
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
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog itself
    structlog.configure(
        processors=shared_processors + [
            # This processor is the final step, rendering the log record
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Use a specific formatter for our handler to get colored, readable output
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run after the processors defined in `structlog.configure`
        foreign_pre_chain=shared_processors,
        processor=structlog.dev.ConsoleRenderer(colors=True),
    )

    # Get the root handler and set our new formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Replace the default handler with our custom one
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)

def get_logger(name: str):
    """
    Returns a configured structlog logger instance.
    """
    return structlog.get_logger(name)
