import csv
import json
import logging
import sys
from io import StringIO

from app.core.config import settings


# Custom logging formatters
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_record)


class CSVFormatter(logging.Formatter):
    def __init__(self, fmt: str | None = None, datefmt: str | None = None) -> None:
        super().__init__(fmt, datefmt)
        self.output = StringIO()
        self.writer = csv.writer(self.output)

    def format(self, record: logging.LogRecord) -> str:
        self.output.seek(0)
        self.output.truncate(0)
        self.writer.writerow(
            [
                self.formatTime(record, self.datefmt),
                record.levelname,
                record.getMessage(),
            ]
        )
        return self.output.getvalue().strip()


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Initialize logging based on configuration in settings and return a logger.
    Supports text, json, and csv formats and console and file handlers.

    Args:
        name: The name for the logger. If None, returns the root logger.

    Returns:
        logging.Logger: A configured logger instance
    """
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Determine log level (convert to uppercase for logging module)
    log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
    logging.root.setLevel(log_level)

    # Choose a formatter based on the log_format setting
    default_log_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter: logging.Formatter
    if settings.log_format == "csv":
        formatter = CSVFormatter(datefmt=settings.log_date_format)

    elif settings.log_format == "json":
        formatter = JSONFormatter(datefmt=settings.log_date_format)

    else:  # default to text formatting
        formatter = logging.Formatter(
            default_log_format, datefmt=settings.log_date_format
        )

    # Determine active handlers from settings.log_handlers (a list from computed field)
    handlers: list[logging.Handler] = []

    # Get the log handlers from settings
    # This handles both cases:
    # - In production log_handlers is a computed property (callable)
    # - In tests it might be mocked as a direct list
    handlers_attr = getattr(settings, "log_handlers", None)
    if callable(handlers_attr):
        log_handlers = handlers_attr()  # Call if it's a method/computed property
    else:
        # Use the attribute directly, defaulting to ["console"] if it doesn't exist
        log_handlers = handlers_attr if handlers_attr is not None else ["console"]

    if "console" in log_handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    if "file" in log_handlers:
        from logging.handlers import TimedRotatingFileHandler

        rotation_when = "d"  # daily rotation by default
        rotation_interval = 1
        backup_count = 7  # default retention

        if hasattr(settings, "log_rotation") and settings.log_rotation:
            if "h" in settings.log_rotation.lower():
                rotation_when = "h"
            elif "d" in settings.log_rotation.lower():
                rotation_when = "d"

        if hasattr(settings, "log_retention") and settings.log_retention:
            try:
                backup_count = int(settings.log_retention.rstrip("dDhH"))
            except Exception:
                backup_count = 7

        file_handler = TimedRotatingFileHandler(
            settings.log_file,
            when=rotation_when,
            interval=rotation_interval,
            backupCount=backup_count,
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Attach handlers to the root logger
    for handler in handlers:
        logging.root.addHandler(handler)

    # Get the requested logger
    logger = logging.getLogger(name)

    # Log an initialization message
    logging.getLogger(__name__).info(
        "Logging configured successfully using %s format at %s level.",
        settings.log_format,
        settings.log_level,
    )

    return logger
