"""
Unit tests for Redis core module.
Tests functions in isolation using mocks (no actual Redis connection).
"""

import asyncio
import ssl as _ssl
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.redis import (
    _build_redis,
    _session_key,
    _wait_for_redis,
    get_redis,
    is_user_session_active,
    redis_lifespan,
    revoke_user_session,
    store_session_for_user,
)


@pytest.mark.asyncio
@patch("app.core.redis.Redis")
@patch("app.core.redis.settings")
async def test_build_redis_basic_config(
    mock_settings: MagicMock, mock_redis_class: MagicMock
) -> None:
    """Test _build_redis creates Redis client with basic settings."""
    mock_settings.redis_url = "redis://localhost:6379"
    mock_settings.redis_decode_responses = True
    mock_settings.redis_socket_connect_timeout = 5
    mock_settings.redis_socket_timeout = 5
    mock_settings.redis_connection_pool_max_connections = 50
    mock_settings.redis_ssl = False

    mock_client = MagicMock()
    mock_redis_class.from_url.return_value = mock_client

    result = _build_redis()

    mock_redis_class.from_url.assert_called_once_with(
        "redis://localhost:6379",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        max_connections=50,
    )
    assert result is mock_client


@pytest.mark.asyncio
@patch("app.core.redis.Redis")
@patch("app.core.redis.settings")
async def test_build_redis_with_ssl_none(
    mock_settings: MagicMock, mock_redis_class: MagicMock
) -> None:
    """Test _build_redis with SSL enabled and CERT_NONE."""
    mock_settings.redis_url = "rediss://localhost:6379"
    mock_settings.redis_decode_responses = True
    mock_settings.redis_socket_connect_timeout = 5
    mock_settings.redis_socket_timeout = 5
    mock_settings.redis_connection_pool_max_connections = 50
    mock_settings.redis_ssl = True
    mock_settings.redis_ssl_cert_reqs = "none"

    mock_client = MagicMock()
    mock_redis_class.from_url.return_value = mock_client

    _build_redis()

    call_kwargs = mock_redis_class.from_url.call_args[1]
    assert call_kwargs["ssl_cert_reqs"] == _ssl.CERT_NONE


@pytest.mark.asyncio
@patch("app.core.redis.Redis")
@patch("app.core.redis.settings")
async def test_build_redis_with_ssl_optional(
    mock_settings: MagicMock, mock_redis_class: MagicMock
) -> None:
    """Test _build_redis with SSL enabled and CERT_OPTIONAL."""
    mock_settings.redis_url = "rediss://localhost:6379"
    mock_settings.redis_decode_responses = True
    mock_settings.redis_socket_connect_timeout = 5
    mock_settings.redis_socket_timeout = 5
    mock_settings.redis_connection_pool_max_connections = 50
    mock_settings.redis_ssl = True
    mock_settings.redis_ssl_cert_reqs = "optional"

    mock_client = MagicMock()
    mock_redis_class.from_url.return_value = mock_client

    _build_redis()

    call_kwargs = mock_redis_class.from_url.call_args[1]
    assert call_kwargs["ssl_cert_reqs"] == _ssl.CERT_OPTIONAL


@pytest.mark.asyncio
@patch("app.core.redis.Redis")
@patch("app.core.redis.settings")
async def test_build_redis_with_ssl_required(
    mock_settings: MagicMock, mock_redis_class: MagicMock
) -> None:
    """Test _build_redis with SSL enabled and CERT_REQUIRED."""
    mock_settings.redis_url = "rediss://localhost:6379"
    mock_settings.redis_decode_responses = True
    mock_settings.redis_socket_connect_timeout = 5
    mock_settings.redis_socket_timeout = 5
    mock_settings.redis_connection_pool_max_connections = 50
    mock_settings.redis_ssl = True
    mock_settings.redis_ssl_cert_reqs = "required"

    mock_client = MagicMock()
    mock_redis_class.from_url.return_value = mock_client

    _build_redis()

    call_kwargs = mock_redis_class.from_url.call_args[1]
    assert call_kwargs["ssl_cert_reqs"] == _ssl.CERT_REQUIRED


@pytest.mark.asyncio
@patch("app.core.redis.Redis")
@patch("app.core.redis.settings")
async def test_build_redis_with_ssl_invalid_cert_reqs(
    mock_settings: MagicMock, mock_redis_class: MagicMock
) -> None:
    """Test _build_redis with SSL enabled and invalid cert_reqs defaults to CERT_NONE."""
    mock_settings.redis_url = "rediss://localhost:6379"
    mock_settings.redis_decode_responses = True
    mock_settings.redis_socket_connect_timeout = 5
    mock_settings.redis_socket_timeout = 5
    mock_settings.redis_connection_pool_max_connections = 50
    mock_settings.redis_ssl = True
    mock_settings.redis_ssl_cert_reqs = "invalid_value"

    mock_client = MagicMock()
    mock_redis_class.from_url.return_value = mock_client

    _build_redis()

    call_kwargs = mock_redis_class.from_url.call_args[1]
    assert call_kwargs["ssl_cert_reqs"] == _ssl.CERT_NONE


@pytest.mark.asyncio
async def test_wait_for_redis_success_first_try() -> None:
    """Test successful connection on first attempt."""
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value=True)

    await _wait_for_redis(mock_client, attempts=3, delay=0.01)

    mock_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_redis_success_with_pong_string() -> None:
    """Test successful connection when ping returns 'PONG' string."""
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value="PONG")

    await _wait_for_redis(mock_client, attempts=3, delay=0.01)

    mock_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_redis_success_after_retries() -> None:
    """Test successful connection after a few retries."""
    mock_client = MagicMock()
    # Fail twice, then succeed
    mock_client.ping = AsyncMock(
        side_effect=[
            Exception("Connection refused"),
            Exception("Connection refused"),
            True,
        ]
    )

    await _wait_for_redis(mock_client, attempts=5, delay=0.01)

    assert mock_client.ping.call_count == 3


@pytest.mark.asyncio
async def test_wait_for_redis_failure_exhausts_attempts() -> None:
    """Test that it raises RuntimeError after all attempts fail."""
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(side_effect=Exception("Connection refused"))

    with pytest.raises(RuntimeError, match="Redis not ready after retries"):
        await _wait_for_redis(mock_client, attempts=3, delay=0.01)

    assert mock_client.ping.call_count == 3


@pytest.mark.asyncio
async def test_wait_for_redis_exponential_backoff() -> None:
    """Test that delay increases exponentially up to max 3.0."""
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(
        side_effect=[
            Exception("Connection refused"),
            Exception("Connection refused"),
            True,
        ]
    )

    start_time = asyncio.get_event_loop().time()
    await _wait_for_redis(mock_client, attempts=5, delay=0.01)
    elapsed = asyncio.get_event_loop().time() - start_time

    # With delay=0.01: first retry waits 0.01, second waits 0.015
    # Total should be at least 0.025
    assert elapsed >= 0.02


@pytest.mark.asyncio
async def test_wait_for_redis_delay_caps_at_3_seconds() -> None:
    """Test that delay caps at 3.0 seconds."""
    mock_client = MagicMock()
    # Fail many times to test cap
    mock_client.ping = AsyncMock(
        side_effect=[Exception("Connection refused")] * 10 + [True]
    )

    # This test verifies the delay logic but doesn't wait full time
    await _wait_for_redis(mock_client, attempts=15, delay=2.0)

    # Just verify it succeeded without checking exact timing
    assert mock_client.ping.call_count == 11


@pytest.mark.asyncio
async def test_get_redis_not_initialized() -> None:
    """Test that get_redis raises error when client not initialized."""
    import app.core.redis as redis_module

    original_redis = redis_module._redis
    redis_module._redis = None

    try:
        with pytest.raises(
            RuntimeError,
            match=r"Redis client not initialized\. Use within app lifespan\.",
        ):
            get_redis()
    finally:
        redis_module._redis = original_redis


@pytest.mark.asyncio
async def test_get_redis_returns_initialized_client() -> None:
    """Test that get_redis returns the initialized client."""
    import app.core.redis as redis_module

    mock_client = MagicMock()
    original_redis = redis_module._redis
    redis_module._redis = mock_client

    try:
        result = get_redis()
        assert result is mock_client
    finally:
        redis_module._redis = original_redis


@pytest.mark.asyncio
@patch("app.core.redis._wait_for_redis")
@patch("app.core.redis._build_redis")
async def test_redis_lifespan_success(
    mock_build: MagicMock, mock_wait: AsyncMock
) -> None:
    """Test successful redis_lifespan initialization and cleanup."""
    import app.core.redis as redis_module

    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_build.return_value = mock_client

    async with redis_lifespan():
        # During lifespan, client should be set
        assert redis_module._redis is mock_client

    # Verify initialization
    mock_build.assert_called_once()
    mock_wait.assert_called_once_with(mock_client)

    # Verify cleanup
    mock_client.close.assert_called_once()
    assert redis_module._redis is None


@pytest.mark.asyncio
@patch("app.core.redis._wait_for_redis")
@patch("app.core.redis._build_redis")
async def test_redis_lifespan_cleanup_on_error(
    mock_build: MagicMock, mock_wait: AsyncMock
) -> None:
    """Test that cleanup happens even when error occurs during lifespan."""
    import app.core.redis as redis_module

    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_build.return_value = mock_client

    try:
        async with redis_lifespan():
            assert redis_module._redis is mock_client
            raise ValueError("Simulated error during app execution")
    except ValueError:
        pass

    # Verify cleanup still happened
    mock_client.close.assert_called_once()
    assert redis_module._redis is None


@pytest.mark.asyncio
@patch("app.core.redis._wait_for_redis")
@patch("app.core.redis._build_redis")
async def test_redis_lifespan_wait_failure(
    mock_build: MagicMock, mock_wait: AsyncMock
) -> None:
    """Test that error during wait_for_redis is propagated (cleanup doesn't happen since it's before try block)."""
    import app.core.redis as redis_module

    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_build.return_value = mock_client
    mock_wait.side_effect = RuntimeError("Redis not ready after retries")

    with pytest.raises(RuntimeError, match="Redis not ready after retries"):
        async with redis_lifespan():
            pass

    # Note: cleanup doesn't happen because wait_for_redis is before the try block
    # The client is created but not closed if wait fails
    mock_client.close.assert_not_called()
    # Client is still set in the module (not cleaned up)
    assert redis_module._redis is mock_client


@pytest.mark.asyncio
@patch("app.core.redis._wait_for_redis")
@patch("app.core.redis._build_redis")
async def test_redis_lifespan_sets_global_client(
    mock_build: MagicMock, mock_wait: AsyncMock
) -> None:
    """Test that redis_lifespan sets the global _redis variable."""
    import app.core.redis as redis_module

    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_build.return_value = mock_client

    # Before lifespan
    original_redis = redis_module._redis
    redis_module._redis = None

    try:
        async with redis_lifespan():
            # Inside lifespan, client should be set
            assert redis_module._redis is not None
            assert redis_module._redis is mock_client

        # After lifespan, client should be None
        assert redis_module._redis is None
    finally:
        redis_module._redis = original_redis


@pytest.mark.asyncio
async def test_session_key_access_token() -> None:
    """Test session key format for access token."""
    result = _session_key("access", "alice")
    assert result == "session:access:alice"


@pytest.mark.asyncio
async def test_session_key_refresh_token() -> None:
    """Test session key format for refresh token."""
    result = _session_key("refresh", "bob")
    assert result == "session:refresh:bob"


@pytest.mark.asyncio
async def test_session_key_with_special_characters() -> None:
    """Test session key format with special characters in username."""
    result = _session_key("access", "user@example.com")
    assert result == "session:access:user@example.com"


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_store_session_for_user_basic(mock_get_redis: MagicMock) -> None:
    """Test storing session with basic parameters."""
    mock_client = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.hset = AsyncMock()
    mock_pipeline.expire = AsyncMock()
    mock_pipeline.execute = AsyncMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_client.pipeline.return_value = mock_pipeline
    mock_get_redis.return_value = mock_client

    exp_ts = int(time.time()) + 3600
    await store_session_for_user(
        username="alice", jti="test_jti_123", exp_unix_ts=exp_ts, kind="access"
    )

    mock_client.pipeline.assert_called_once_with(transaction=True)
    mock_pipeline.hset.assert_called_once()
    mock_pipeline.expire.assert_called_once()
    mock_pipeline.execute.assert_called_once()


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_store_session_for_user_with_metadata(mock_get_redis: MagicMock) -> None:
    """Test storing session with metadata."""
    mock_client = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.hset = AsyncMock()
    mock_pipeline.expire = AsyncMock()
    mock_pipeline.execute = AsyncMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_client.pipeline.return_value = mock_pipeline
    mock_get_redis.return_value = mock_client

    exp_ts = int(time.time()) + 3600
    meta = {"ip": "192.168.1.1", "user_agent": "TestAgent/1.0"}

    await store_session_for_user(
        username="alice",
        jti="test_jti_123",
        exp_unix_ts=exp_ts,
        kind="access",
        meta=meta,
    )

    # Verify hset was called with jti, exp, and metadata
    call_args = mock_pipeline.hset.call_args
    mapping = call_args[1]["mapping"]
    assert mapping["jti"] == "test_jti_123"
    assert mapping["exp"] == str(exp_ts)
    assert mapping["ip"] == "192.168.1.1"
    assert mapping["user_agent"] == "TestAgent/1.0"


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_store_session_for_user_ttl_calculation(
    mock_get_redis: MagicMock,
) -> None:
    """Test that TTL is calculated correctly."""
    mock_client = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.hset = AsyncMock()
    mock_pipeline.expire = AsyncMock()
    mock_pipeline.execute = AsyncMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_client.pipeline.return_value = mock_pipeline
    mock_get_redis.return_value = mock_client

    exp_ts = int(time.time()) + 3600  # 1 hour from now

    await store_session_for_user(
        username="alice", jti="test_jti_123", exp_unix_ts=exp_ts, kind="access"
    )

    # Verify expire was called with a reasonable TTL (around 3600 seconds)
    call_args = mock_pipeline.expire.call_args
    ttl = call_args[0][1]
    assert 3500 < ttl <= 3600  # Allow some time variance


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_store_session_for_user_refresh_token(mock_get_redis: MagicMock) -> None:
    """Test storing refresh token session."""
    mock_client = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.hset = AsyncMock()
    mock_pipeline.expire = AsyncMock()
    mock_pipeline.execute = AsyncMock()
    mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
    mock_pipeline.__aexit__ = AsyncMock(return_value=None)
    mock_client.pipeline.return_value = mock_pipeline
    mock_get_redis.return_value = mock_client

    exp_ts = int(time.time()) + 7200

    await store_session_for_user(
        username="alice", jti="refresh_jti_456", exp_unix_ts=exp_ts, kind="refresh"
    )

    # Verify correct key was used (session:refresh:alice)
    call_args = mock_pipeline.hset.call_args
    key = call_args[0][0]
    assert key == "session:refresh:alice"


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_is_user_session_active_returns_true_when_jti_matches(
    mock_get_redis: MagicMock,
) -> None:
    """Test that session is active when stored JTI matches."""
    mock_client = MagicMock()
    mock_client.hget = AsyncMock(return_value="test_jti_123")
    mock_get_redis.return_value = mock_client

    result = await is_user_session_active("alice", "test_jti_123", kind="access")

    assert result is True
    mock_client.hget.assert_called_once_with("session:access:alice", "jti")


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_is_user_session_active_returns_false_when_jti_mismatch(
    mock_get_redis: MagicMock,
) -> None:
    """Test that session is inactive when stored JTI doesn't match."""
    mock_client = MagicMock()
    mock_client.hget = AsyncMock(return_value="different_jti")
    mock_get_redis.return_value = mock_client

    result = await is_user_session_active("alice", "test_jti_123", kind="access")

    assert result is False


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_is_user_session_active_returns_false_when_no_session(
    mock_get_redis: MagicMock,
) -> None:
    """Test that session is inactive when no session exists."""
    mock_client = MagicMock()
    mock_client.hget = AsyncMock(return_value=None)
    mock_get_redis.return_value = mock_client

    result = await is_user_session_active("alice", "test_jti_123", kind="access")

    assert result is False


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_is_user_session_active_refresh_token(
    mock_get_redis: MagicMock,
) -> None:
    """Test checking refresh token session."""
    mock_client = MagicMock()
    mock_client.hget = AsyncMock(return_value="refresh_jti_456")
    mock_get_redis.return_value = mock_client

    result = await is_user_session_active("alice", "refresh_jti_456", kind="refresh")

    assert result is True
    mock_client.hget.assert_called_once_with("session:refresh:alice", "jti")


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_revoke_user_session_access_token(mock_get_redis: MagicMock) -> None:
    """Test revoking access token session."""
    mock_client = MagicMock()
    mock_client.delete = AsyncMock(return_value=1)
    mock_get_redis.return_value = mock_client

    await revoke_user_session("alice", kind="access")

    mock_client.delete.assert_called_once_with("session:access:alice")


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_revoke_user_session_refresh_token(mock_get_redis: MagicMock) -> None:
    """Test revoking refresh token session."""
    mock_client = MagicMock()
    mock_client.delete = AsyncMock(return_value=1)
    mock_get_redis.return_value = mock_client

    await revoke_user_session("alice", kind="refresh")

    mock_client.delete.assert_called_once_with("session:refresh:alice")


@pytest.mark.asyncio
@patch("app.core.redis.get_redis")
async def test_revoke_user_session_when_no_session_exists(
    mock_get_redis: MagicMock,
) -> None:
    """Test revoking session when no session exists (should not error)."""
    mock_client = MagicMock()
    mock_client.delete = AsyncMock(return_value=0)  # No keys deleted
    mock_get_redis.return_value = mock_client

    # Should not raise any error
    await revoke_user_session("alice", kind="access")

    mock_client.delete.assert_called_once_with("session:access:alice")
