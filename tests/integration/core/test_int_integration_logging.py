import json
import logging
import os
import sys
import tempfile
from collections.abc import Generator
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.core.logging import CSVFormatter, JSONFormatter, get_logger


@pytest.fixture
def temp_log_file() -> Generator[str, None, None]:
    """Create a temporary log file for testing."""
    fd, path = tempfile.mkstemp(suffix=".log")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_get_logger_returns_logger(temp_log_file: str) -> None:
    """Test that get_logger returns a logger instance."""
    with patch.object(settings, "log_file", temp_log_file):
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"


def test_json_formatter() -> None:
    """Test that JSONFormatter formats log records as JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert "time" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"


def test_csv_formatter() -> None:
    """Test that CSVFormatter formats log records as CSV."""
    formatter = CSVFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parts = formatted.split(",")

    assert len(parts) == 4
    assert any(part.strip() == "INFO" for part in parts)
    assert "Test message" in parts[-1].strip()


@pytest.mark.parametrize(
    ("log_format", "formatter_class"),
    [
        ("text", logging.Formatter),
        ("json", JSONFormatter),
        ("csv", CSVFormatter),
    ],
)
def test_log_format_selection(
    log_format: str, formatter_class: type, temp_log_file: str
) -> None:
    """Test that the correct formatter is selected based on log_format setting."""
    with (
        patch.object(settings, "log_format", log_format),
        patch.object(settings, "log_file", temp_log_file),
        patch.object(settings, "log_handlers_raw", "file"),
    ):
        logger = get_logger("test_format")

        logger.info("Test message for format selection")

        assert len(logging.root.handlers) > 0

        formatter_found = False
        for handler in logging.root.handlers:
            if isinstance(handler.formatter, formatter_class):
                formatter_found = True
                break

        assert formatter_found, f"No handler with {formatter_class.__name__} found"


def test_file_handler_with_rotation(temp_log_file: str) -> None:
    """Test that file handler uses rotation when configured."""
    from logging.handlers import TimedRotatingFileHandler

    with (
        patch.object(settings, "log_file", temp_log_file),
        patch.object(settings, "log_handlers_raw", "file"),
        patch.object(settings, "log_rotation", "1d"),
        patch.object(settings, "log_retention", "7d"),
    ):
        logger = get_logger("test_rotation")

        logger.info("Test message for rotation")

        rotating_handler_found = False
        for handler in logging.root.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                rotating_handler_found = True
                assert handler.when.lower() == "d"  # daily rotation
                assert handler.backupCount == 7  # 7 days retention
                break

        assert rotating_handler_found, "No TimedRotatingFileHandler found"


def test_console_handler() -> None:
    """Test that console handler outputs to stdout."""
    with patch.object(settings, "log_handlers_raw", "console"):
        logger = get_logger("test_console")

        logger.info("Test message for console output")

        stream_handler_found = False
        for handler in logging.root.handlers:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            ):
                stream_handler_found = True
                break

        assert stream_handler_found, "No StreamHandler for stdout found"


def test_log_level_setting(temp_log_file: str) -> None:
    """Test that log level is set correctly based on settings."""
    with (
        patch.object(settings, "log_level", "ERROR"),
        patch.object(settings, "log_file", temp_log_file),
    ):
        logger = get_logger("test_level")

        logger.debug("Debug message should not appear")
        logger.error("Error message should appear")

        assert logging.root.level == logging.ERROR


def test_integration_logging_flow(temp_log_file: str) -> None:
    """Integration test for the complete logging flow."""
    with (
        patch.object(settings, "log_format", "json"),
        patch.object(settings, "log_handlers_raw", "file"),
        patch.object(settings, "log_file", temp_log_file),
    ):
        logger = get_logger("integration_test")
        logger.info("Integration test message")

        with open(temp_log_file) as f:
            log_content = f.read()

        log_lines = [line for line in log_content.strip().split("\n") if line]
        assert len(log_lines) >= 2

        found_message = False
        for line in log_lines:
            try:
                log_entry = json.loads(line)
                if (
                    "message" in log_entry
                    and "Integration test message" in log_entry["message"]
                ):
                    assert log_entry["level"] == "INFO"
                    found_message = True
                    break
            except json.JSONDecodeError:
                continue

        assert found_message, "Expected log message not found in log file"
