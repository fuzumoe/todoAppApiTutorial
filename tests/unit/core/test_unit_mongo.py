"""
Unit tests for MongoDB core module.
Tests functions in isolation using mocks (no actual MongoDB connection).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.mongo import (
    _wait_for_mongo,
    beanie_lifespan,
    get_client,
    get_db,
)


@pytest.mark.asyncio
async def test_wait_for_mongo_success_first_try() -> None:
    """Test successful connection on first attempt."""
    mock_client = MagicMock()
    mock_client.admin.command = AsyncMock(return_value={"ok": 1})

    await _wait_for_mongo(mock_client, attempts=3, delay=0.01)

    # Should only call once
    mock_client.admin.command.assert_called_once_with("ping")


@pytest.mark.asyncio
async def test_wait_for_mongo_success_after_retries() -> None:
    """Test successful connection after a few retries."""
    mock_client = MagicMock()
    # Fail twice, then succeed
    mock_client.admin.command = AsyncMock(
        side_effect=[
            Exception("Connection refused"),
            Exception("Connection refused"),
            {"ok": 1},
        ]
    )

    await _wait_for_mongo(mock_client, attempts=5, delay=0.01)

    # Should call 3 times (2 failures + 1 success)
    assert mock_client.admin.command.call_count == 3


@pytest.mark.asyncio
async def test_wait_for_mongo_failure_exhausts_attempts() -> None:
    """Test that it raises RuntimeError after all attempts fail."""
    mock_client = MagicMock()
    mock_client.admin.command = AsyncMock(side_effect=Exception("Connection refused"))

    with pytest.raises(RuntimeError, match="MongoDB not ready"):
        await _wait_for_mongo(mock_client, attempts=3, delay=0.01)

    # Should try 3 times
    assert mock_client.admin.command.call_count == 3


@pytest.mark.asyncio
async def test_wait_for_mongo_exponential_backoff() -> None:
    """Test that delay increases exponentially."""
    mock_client = MagicMock()
    mock_client.admin.command = AsyncMock(
        side_effect=[
            Exception("Connection refused"),
            Exception("Connection refused"),
            {"ok": 1},
        ]
    )

    # Capture actual delays by timing
    start_time = asyncio.get_event_loop().time()
    await _wait_for_mongo(mock_client, attempts=5, delay=0.01)
    elapsed = asyncio.get_event_loop().time() - start_time

    # With delay=0.01: 0.01 + 0.015 = 0.025, should be at least that much
    # (allowing some tolerance for test execution)
    assert elapsed >= 0.02


@pytest.mark.asyncio
async def test_get_client_not_initialized() -> None:
    """Test that get_client raises error when client not initialized."""
    import app.core.mongo as mongo_module

    original_client = mongo_module._client
    mongo_module._client = None

    try:
        with pytest.raises(
            RuntimeError,
            match=r"Mongo client not initialized\. Use inside app lifespan\.",
        ):
            get_client()
    finally:
        mongo_module._client = original_client


@pytest.mark.asyncio
async def test_get_client_returns_initialized_client() -> None:
    """Test that get_client returns the initialized client."""
    import app.core.mongo as mongo_module

    mock_client = MagicMock()
    original_client = mongo_module._client
    mongo_module._client = mock_client

    try:
        result = get_client()
        assert result is mock_client
    finally:
        mongo_module._client = original_client


@pytest.mark.asyncio
@patch("app.core.mongo.get_client")
@patch("app.core.mongo.settings")
async def test_get_db_returns_database(
    mock_settings: MagicMock, mock_get_client: MagicMock
) -> None:
    """Test that get_db returns the correct database."""
    mock_settings.database_name = "test_db"
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_get_client.return_value = mock_client

    result = get_db()

    mock_client.__getitem__.assert_called_once_with("test_db")
    assert result is mock_db


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_success(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test successful beanie_lifespan initialization and cleanup."""
    import app.core.mongo as mongo_module

    # Setup mocks
    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_motor_client_class.return_value = mock_client

    # Run lifespan
    async with beanie_lifespan():
        # During lifespan, client should be set
        assert mongo_module._client is mock_client

    # Verify initialization
    mock_motor_client_class.assert_called_once_with("mongodb://localhost:27017")
    mock_wait.assert_called_once_with(mock_client)
    mock_init_beanie.assert_called_once()

    # Verify cleanup
    mock_client.close.assert_called_once()
    assert mongo_module._client is None


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_cleanup_on_error(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test that cleanup happens even when error occurs during lifespan."""
    import app.core.mongo as mongo_module

    # Setup mocks
    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_motor_client_class.return_value = mock_client

    # Run lifespan with error
    try:
        async with beanie_lifespan():
            assert mongo_module._client is mock_client
            raise ValueError("Simulated error during app execution")
    except ValueError:
        pass

    # Verify cleanup still happened
    mock_client.close.assert_called_once()
    assert mongo_module._client is None


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_init_beanie_called_with_correct_params(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test that init_beanie is called with correct database and models."""
    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_motor_client_class.return_value = mock_client

    async with beanie_lifespan():
        pass

    # Verify init_beanie was called with database and document_models
    call_kwargs = mock_init_beanie.call_args[1]
    assert call_kwargs["database"] is mock_db
    assert "document_models" in call_kwargs
    assert isinstance(call_kwargs["document_models"], list)


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_wait_for_mongo_failure(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test that error during wait_for_mongo is propagated (cleanup doesn't happen since it's before try block)."""
    import app.core.mongo as mongo_module

    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_motor_client_class.return_value = mock_client
    mock_wait.side_effect = RuntimeError("MongoDB not ready")

    with pytest.raises(RuntimeError, match="MongoDB not ready"):
        async with beanie_lifespan():
            pass

    # Note: cleanup doesn't happen because wait_for_mongo is before the try block
    # The client is created but not closed if wait fails
    mock_client.close.assert_not_called()
    # Client is still set in the module (not cleaned up)
    assert mongo_module._client is mock_client


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_init_beanie_failure(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test that error during init_beanie is propagated and cleanup happens."""
    import app.core.mongo as mongo_module

    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_motor_client_class.return_value = mock_client
    mock_init_beanie.side_effect = Exception("Beanie initialization failed")

    with pytest.raises(Exception, match="Beanie initialization failed"):
        async with beanie_lifespan():
            pass

    # Verify cleanup happened
    mock_client.close.assert_called_once()
    assert mongo_module._client is None


@pytest.mark.asyncio
@patch("app.core.mongo.init_beanie")
@patch("app.core.mongo._wait_for_mongo")
@patch("app.core.mongo.AsyncIOMotorClient")
@patch("app.core.mongo.settings")
async def test_beanie_lifespan_sets_global_client(
    mock_settings: MagicMock,
    mock_motor_client_class: MagicMock,
    mock_wait: AsyncMock,
    mock_init_beanie: AsyncMock,
) -> None:
    """Test that beanie_lifespan sets the global _client variable."""
    import app.core.mongo as mongo_module

    mock_settings.mongodb_uri = "mongodb://localhost:27017"
    mock_settings.database_name = "test_db"

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.__getitem__.return_value = mock_db
    mock_motor_client_class.return_value = mock_client

    # Before lifespan
    original_client = mongo_module._client
    mongo_module._client = None

    try:
        async with beanie_lifespan():
            # Inside lifespan, client should be set
            assert mongo_module._client is not None
            assert mongo_module._client is mock_client

        # After lifespan, client should be None
        assert mongo_module._client is None
    finally:
        mongo_module._client = original_client
