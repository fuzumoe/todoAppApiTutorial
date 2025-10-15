"""
Unit tests for the logging module.

These tests focus on isolated functionality of the logging components
without requiring the full application context.
"""

import json
import logging
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.core.logging import CSVFormatter, JSONFormatter, get_logger


# Custom Formatter Tests
@pytest.fixture
def temp_log_file() -> str:
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as temp:
        temp_name = temp.name
    return temp_name


def test_json_formatter_format() -> None:
    """Test that JSONFormatter correctly formats log records as JSON."""
    formatter = JSONFormatter(datefmt="%Y-%m-%d")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert isinstance(parsed, dict)
    assert "time" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"


def test_json_formatter_with_args() -> None:
    """Test that JSONFormatter correctly handles messages with arguments."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test_path",
        lineno=42,
        msg="Warning: %s at %s",
        args=("disk full", "11:23 AM"),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "WARNING"
    assert parsed["message"] == "Warning: disk full at 11:23 AM"


def test_csv_formatter_format() -> None:
    """Test that CSVFormatter correctly formats log records as CSV."""
    formatter = CSVFormatter(datefmt="%Y-%m-%d")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test_path",
        lineno=42,
        msg="Error message",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)

    # Verify it's a valid CSV format (we'll just do basic checks)
    assert "," in formatted
    assert "ERROR" in formatted
    assert "Error message" in formatted


def test_csv_formatter_output_reset() -> None:
    """Test that CSVFormatter correctly resets its output between calls."""
    formatter = CSVFormatter()
    record1 = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path",
        lineno=42,
        msg="First message",
        args=(),
        exc_info=None,
    )
    record2 = logging.LogRecord(
        name="test_logger",
        level=logging.DEBUG,
        pathname="test_path",
        lineno=43,
        msg="Second message",
        args=(),
        exc_info=None,
    )

    # Format two records
    formatted1 = formatter.format(record1)
    formatted2 = formatter.format(record2)

    # Check that the first message isn't in the second output
    assert "First message" in formatted1
    assert "First message" not in formatted2
    assert "Second message" in formatted2
    assert "INFO" in formatted1
    assert "DEBUG" in formatted2


# Logger Creation Tests
@patch("app.core.logging.logging")
@patch("logging.handlers.TimedRotatingFileHandler")
def test_get_logger_returns_configured_logger(
    mock_file_handler: MagicMock, mock_logging: MagicMock, temp_log_file: str
) -> None:
    """Test that get_logger returns a properly configured logger."""
    # Set up mocks for different loggers
    test_logger = MagicMock(spec=logging.Logger)
    internal_logger = MagicMock(spec=logging.Logger)

    # Use side_effect to return different loggers based on the name
    def get_logger_side_effect(name: str) -> MagicMock:
        if name == "test_unit_logger":
            return test_logger
        else:
            return internal_logger

    mock_logging.getLogger.side_effect = (
        get_logger_side_effect  # Need to mock settings properties that get accessed
    )
    with patch.multiple(
        settings,
        log_level="INFO",
        log_format="text",
        log_handlers_raw="console",
        log_file=temp_log_file,
    ):
        # Call get_logger with a test name
        logger = get_logger("test_unit_logger")

        # Verify the right logger was returned
        assert logger == test_logger
        # Verify the logger was retrieved with the correct name
        mock_logging.getLogger.assert_any_call("test_unit_logger")


@patch("app.core.logging.logging")
def test_get_logger_sets_root_level(mock_logging: MagicMock) -> None:
    """Test that get_logger sets the root logger level correctly."""
    with patch.multiple(
        settings,
        log_level="ERROR",
        log_format="text",
        log_handlers_raw="console",
        log_file="/tmp/test.log",
    ):
        get_logger("test_level")

        # Verify root logger level was set to ERROR
        mock_logging.root.setLevel.assert_called_once_with(mock_logging.ERROR)


@patch("app.core.logging.logging")
def test_get_logger_clears_existing_handlers(mock_logging: MagicMock) -> None:
    """Test that get_logger clears existing handlers from the root logger."""
    # Setup mock handlers
    mock_handler1 = MagicMock()
    mock_handler2 = MagicMock()
    mock_logging.root.handlers = [mock_handler1, mock_handler2]

    with patch.multiple(
        settings,
        log_level="INFO",
        log_format="text",
        log_handlers_raw="console",
        log_file="/tmp/test.log",
    ):
        get_logger()

    # Verify handlers were removed
    assert mock_logging.root.removeHandler.call_count == 2
    mock_logging.root.removeHandler.assert_any_call(mock_handler1)
    mock_logging.root.removeHandler.assert_any_call(mock_handler2)


# Log Handler Configuration Tests
@patch("app.core.logging.logging")
def test_console_handler_creation(mock_logging: MagicMock) -> None:
    """Test that a console handler is created when configured."""
    mock_stream_handler = MagicMock()
    mock_logging.StreamHandler.return_value = mock_stream_handler

    with patch.multiple(
        settings,
        log_level="INFO",
        log_handlers_raw="console",
        log_format="text",
        log_file="/tmp/test.log",
    ):
        get_logger()

        # Verify StreamHandler was created with stdout
        mock_logging.StreamHandler.assert_called_once()
        assert mock_logging.StreamHandler.call_args[0][0] == sys.stdout

        # Verify handler was added to root logger
        mock_logging.root.addHandler.assert_called_with(mock_stream_handler)


@patch("app.core.logging.logging")
@patch("logging.handlers.TimedRotatingFileHandler")
def test_file_handler_creation(
    mock_rotating_handler: MagicMock, mock_logging: MagicMock
) -> None:
    """Test that a file handler is created when configured."""
    mock_file_handler = MagicMock()
    mock_rotating_handler.return_value = mock_file_handler

    with patch.multiple(
        settings,
        log_level="INFO",
        log_handlers_raw="file",
        log_format="text",
        log_file="/tmp/test.log",
        log_rotation="1d",
        log_retention="7d",
    ):
        get_logger()

        # Verify TimedRotatingFileHandler was created with correct parameters
        mock_rotating_handler.assert_called_once_with(
            "/tmp/test.log", when="d", interval=1, backupCount=7
        )

        # Verify handler was added to root logger
        mock_logging.root.addHandler.assert_called_with(mock_file_handler)


@patch("app.core.logging.logging")
def test_multiple_handlers(mock_logging: MagicMock) -> None:
    """Test that multiple handlers are created when configured."""
    # Create mock handlers
    mock_console_handler = MagicMock()
    mock_file_handler = MagicMock()

    # Setup mocks
    mock_logging.StreamHandler.return_value = mock_console_handler

    with (
        patch("logging.handlers.TimedRotatingFileHandler") as mock_rotating_handler,
        patch.multiple(
            settings,
            log_level="INFO",
            log_handlers_raw="console,file",
            log_format="text",
            log_file="/tmp/test.log",
        ),
    ):
        mock_rotating_handler.return_value = mock_file_handler
        get_logger()

        # Verify both handlers were added to root logger
        assert mock_logging.root.addHandler.call_count == 2
        mock_logging.root.addHandler.assert_any_call(mock_console_handler)
        mock_logging.root.addHandler.assert_any_call(mock_file_handler)


# Formatter Selection Tests
@patch("app.core.logging.logging")
def test_text_formatter_selected(mock_logging: MagicMock) -> None:
    """Test that the text formatter is selected when configured."""
    mock_formatter = MagicMock()
    mock_logging.Formatter.return_value = mock_formatter

    with patch.multiple(
        settings,
        log_level="INFO",
        log_format="text",
        log_handlers_raw="console",
        log_file="/tmp/test.log",
    ):
        get_logger()

        # Verify a text formatter was created
        mock_logging.Formatter.assert_called_once()


@patch("app.core.logging.JSONFormatter")
@patch("app.core.logging.logging")
def test_json_formatter_selected(
    mock_logging: MagicMock, mock_json_formatter: MagicMock
) -> None:
    """Test that the JSON formatter is selected when configured."""
    with patch.multiple(
        settings,
        log_level="INFO",
        log_format="json",
        log_handlers_raw="console",
        log_file="/tmp/test.log",
    ):
        get_logger()

        # Verify a JSONFormatter was created
        mock_json_formatter.assert_called_once()


@patch("app.core.logging.CSVFormatter")
@patch("app.core.logging.logging")
def test_csv_formatter_selected(
    mock_logging: MagicMock, mock_csv_formatter: MagicMock
) -> None:
    """Test that the CSV formatter is selected when configured."""
    with patch.multiple(
        settings,
        log_level="INFO",
        log_format="csv",
        log_handlers_raw="console",
        log_file="/tmp/test.log",
    ):
        get_logger()

        # Verify a CSVFormatter was created
        mock_csv_formatter.assert_called_once()


# Rotation Configuration Tests
@patch("logging.handlers.TimedRotatingFileHandler")
@patch("app.core.logging.logging")
def test_hourly_rotation(mock_logging: MagicMock, mock_handler: MagicMock) -> None:
    """Test that hourly rotation is configured correctly."""
    with patch.multiple(
        settings,
        log_level="INFO",
        log_handlers_raw="file",
        log_format="text",
        log_file="/tmp/test.log",
        log_rotation="1h",
    ):
        get_logger()

        # Verify rotation parameters
        assert mock_handler.call_args.kwargs["when"] == "h"


@patch("logging.handlers.TimedRotatingFileHandler")
@patch("app.core.logging.logging")
def test_retention_parsing(mock_logging: MagicMock, mock_handler: MagicMock) -> None:
    """Test that retention period is parsed correctly."""
    with patch.multiple(
        settings,
        log_level="INFO",
        log_handlers_raw="file",
        log_format="text",
        log_file="/tmp/test.log",
        log_retention="14d",
    ):
        get_logger()

        # Verify backup count
        assert mock_handler.call_args.kwargs["backupCount"] == 14


@patch("logging.handlers.TimedRotatingFileHandler")
@patch("app.core.logging.logging")
def test_retention_invalid_format(
    mock_logging: MagicMock, mock_handler: MagicMock
) -> None:
    """Test that invalid retention format falls back to default."""
    with patch.multiple(
        settings,
        log_level="INFO",
        log_handlers_raw="file",
        log_format="text",
        log_file="/tmp/test.log",
        log_retention="invalid",
    ):
        get_logger()

        # Verify default backup count used
        assert mock_handler.call_args.kwargs["backupCount"] == 7


# Log Handlers Access Tests
@patch("app.core.logging.logging")
def test_computed_log_handlers(mock_logging: MagicMock) -> None:
    """Test handling of computed log_handlers property."""
    # Simulate production environment where log_handlers is a computed property
    with patch("app.core.logging.settings") as mock_settings:
        mock_settings.log_handlers = lambda: ["console", "file"]
        mock_settings.log_format = "text"
        mock_settings.log_level = "INFO"
        mock_settings.log_file = "/tmp/test.log"
        mock_settings.log_date_format = "%Y-%m-%d %H:%M:%S"

        # Mock the TimedRotatingFileHandler
        with patch("logging.handlers.TimedRotatingFileHandler") as mock_handler:
            mock_handler.return_value = MagicMock()
            get_logger()

            # Verify two handlers were added (console and file)
            assert mock_logging.root.addHandler.call_count == 2


@patch("app.core.logging.logging")
def test_direct_log_handlers(mock_logging: MagicMock) -> None:
    """Test handling of log_handlers as a direct attribute."""
    # Simulate test environment where log_handlers might be a direct attribute
    with patch("app.core.logging.settings") as mock_settings:
        mock_settings.log_handlers = ["console"]
        mock_settings.log_format = "text"
        mock_settings.log_level = "INFO"
        mock_settings.log_date_format = "%Y-%m-%d %H:%M:%S"

        get_logger()

        # Verify one handler was added
        assert mock_logging.root.addHandler.call_count == 1


@patch("app.core.logging.logging")
def test_missing_log_handlers(mock_logging: MagicMock) -> None:
    """Test handling of missing log_handlers attribute."""
    # Simulate environment where log_handlers is not defined
    with patch("app.core.logging.settings") as mock_settings:
        # Deliberately not setting log_handlers
        mock_settings.log_format = "text"
        mock_settings.log_level = "INFO"
        mock_settings.log_date_format = "%Y-%m-%d %H:%M:%S"
        mock_settings.log_handlers_raw = "console"
        # Ensure log_handlers is not present
        if hasattr(mock_settings, "log_handlers"):
            delattr(mock_settings, "log_handlers")

        get_logger()

        # Verify default console handler was added
        assert mock_logging.root.addHandler.call_count == 1
        mock_logging.StreamHandler.assert_called_once()
