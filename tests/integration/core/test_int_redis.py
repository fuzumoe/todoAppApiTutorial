import logging
import time
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import (
    _wait_for_redis,
    get_redis,
    is_user_session_active,
    redis_lifespan,
    revoke_user_session,
    store_session_for_user,
)

logger = logging.getLogger(__name__)

# Skip docker cleanup for these tests - they use standalone services
pytestmark = [pytest.mark.asyncio, pytest.mark.no_docker_cleanup]


@pytest.fixture(scope="session", autouse=True)
def disable_redis_logging() -> None:
    """Disable Redis logging to prevent errors during test teardown."""
    logging.getLogger("redis").setLevel(logging.CRITICAL)
    logging.getLogger("redis.asyncio").setLevel(logging.CRITICAL)
    logging.getLogger("redis.connection").setLevel(logging.CRITICAL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_redis() -> AsyncGenerator[None, None]:
    """Clean up Redis data after all tests complete."""
    # Yield to run all tests first
    yield

    # Cleanup after all tests
    if await _is_redis_available():
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            # Flush all test data
            await client.flushdb()
            logger.info("Flushed Redis test database")
        except Exception as e:
            logger.warning(f"Failed to flush Redis database: {e}")
        finally:
            await client.close()


async def _is_redis_available() -> bool:
    """Check if Redis is available with a fast timeout."""
    try:
        client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
        )
        result = await client.ping()
        await client.close()
        return bool(result)
    except Exception:
        return False


@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Fixture to provide a Redis client for testing (function-scoped for proper event loop management)."""
    if not await _is_redis_available():
        pytest.skip("Redis is not available")

    client = Redis.from_url(settings.redis_url, decode_responses=True)
    yield client
    # Close after test
    await client.close()


# Tests for get_redis function (no network I/O)
async def test_get_redis_not_initialized() -> None:
    """Test that get_redis raises error when not initialized."""
    import app.core.redis as redis_module

    original_redis = redis_module._redis
    redis_module._redis = None

    try:
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            get_redis()
    finally:
        redis_module._redis = original_redis


# Integration tests - require Redis
async def test_wait_for_redis_success(redis_client: Redis) -> None:
    """Test that _wait_for_redis succeeds when Redis is running."""
    await _wait_for_redis(redis_client, attempts=5, delay=0.1)


async def test_wait_for_redis_with_retries(redis_client: Redis) -> None:
    """Test that _wait_for_redis retries multiple times."""
    await _wait_for_redis(redis_client, attempts=10, delay=0.05)


async def test_redis_lifespan_initialization() -> None:
    """Test that redis_lifespan properly initializes Redis."""
    async with redis_lifespan():
        client = get_redis()
        assert client is not None
        result = await client.ping()
        assert result is True or result == "PONG"


async def test_redis_lifespan_cleanup() -> None:
    """Test that redis_lifespan properly cleans up on exit."""
    import app.core.redis as redis_module

    async with redis_lifespan():
        assert redis_module._redis is not None

    assert redis_module._redis is None


async def test_redis_lifespan_operations() -> None:
    """Test that Redis is properly initialized for operations."""
    async with redis_lifespan():
        client = get_redis()

        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        assert value == "test_value"

        # Cleanup
        await client.delete("test_key")


async def test_redis_ping(redis_client: Redis) -> None:
    """Test that we can ping Redis."""
    result = await redis_client.ping()
    assert result is True or result == "PONG"


async def test_redis_basic_operations(redis_client: Redis) -> None:
    """Test basic Redis operations."""
    # Set a value
    await redis_client.set("test_key", "test_value")

    # Get the value
    value = await redis_client.get("test_key")
    assert value == "test_value"

    # Delete the value
    deleted = await redis_client.delete("test_key")
    assert deleted == 1

    # Verify deletion
    value = await redis_client.get("test_key")
    assert value is None


async def test_redis_hash_operations(redis_client: Redis) -> None:
    """Test Redis hash operations."""
    key = "test_hash"

    # Set hash fields
    result = await redis_client.hset(
        key, mapping={"field1": "value1", "field2": "value2"}
    )
    assert result >= 0  # hset returns number of fields added

    # Get a field
    value = await redis_client.hget(key, "field1")
    assert value == "value1"

    # Get all fields
    all_fields = await redis_client.hgetall(key)
    assert all_fields == {"field1": "value1", "field2": "value2"}

    # Cleanup
    await redis_client.delete(key)


async def test_redis_ttl_operations(redis_client: Redis) -> None:
    """Test Redis TTL (expiration) operations."""
    key = "test_ttl_key"

    # Set a key with TTL
    await redis_client.set(key, "value", ex=2)  # 2 seconds TTL

    # Check TTL
    ttl = await redis_client.ttl(key)
    assert 0 < ttl <= 2

    # Value should exist
    value = await redis_client.get(key)
    assert value == "value"

    # Cleanup
    await redis_client.delete(key)


async def test_store_session_for_user() -> None:
    """Test storing session data for a user."""
    async with redis_lifespan():
        username = "test_user"
        jti = "test_jti_123"
        exp_unix_ts = int(time.time()) + 3600  # 1 hour from now

        await store_session_for_user(
            username=username,
            jti=jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
            meta={"ip": "127.0.0.1"},
        )

        # Verify the session was stored
        client = get_redis()
        stored_jti = await client.hget(f"session:access:{username}", "jti")
        assert stored_jti == jti

        # Cleanup
        await client.delete(f"session:access:{username}")


async def test_is_user_session_active() -> None:
    """Test checking if a user session is active."""
    async with redis_lifespan():
        username = "test_user_active"
        jti = "test_jti_456"
        exp_unix_ts = int(time.time()) + 3600

        # Store session
        await store_session_for_user(
            username=username,
            jti=jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
        )

        # Check active session
        is_active = await is_user_session_active(username, jti, kind="access")
        assert is_active is True

        # Check with wrong JTI
        is_active = await is_user_session_active(username, "wrong_jti", kind="access")
        assert is_active is False

        # Cleanup
        client = get_redis()
        await client.delete(f"session:access:{username}")


async def test_revoke_user_session() -> None:
    """Test revoking a user session."""
    async with redis_lifespan():
        username = "test_user_revoke"
        jti = "test_jti_789"
        exp_unix_ts = int(time.time()) + 3600

        # Store session
        await store_session_for_user(
            username=username,
            jti=jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
        )

        # Verify session exists
        is_active = await is_user_session_active(username, jti, kind="access")
        assert is_active is True

        # Revoke session
        await revoke_user_session(username, kind="access")

        # Verify session is gone
        is_active = await is_user_session_active(username, jti, kind="access")
        assert is_active is False


async def test_session_ttl_enforcement() -> None:
    """Test that session TTL is properly set and enforced."""
    async with redis_lifespan():
        username = "test_user_ttl"
        jti = "test_jti_ttl"
        exp_unix_ts = int(time.time()) + 5  # 5 seconds from now

        await store_session_for_user(
            username=username,
            jti=jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
        )

        # Check TTL is set
        client = get_redis()
        ttl = await client.ttl(f"session:access:{username}")
        assert 0 < ttl <= 5

        # Cleanup
        await client.delete(f"session:access:{username}")


async def test_multiple_session_kinds() -> None:
    """Test storing different session kinds (access vs refresh)."""
    async with redis_lifespan():
        username = "test_user_kinds"
        access_jti = "access_jti"
        refresh_jti = "refresh_jti"
        exp_unix_ts = int(time.time()) + 3600

        # Store access session
        await store_session_for_user(
            username=username,
            jti=access_jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
        )

        # Store refresh session
        await store_session_for_user(
            username=username,
            jti=refresh_jti,
            exp_unix_ts=exp_unix_ts,
            kind="refresh",
        )

        # Verify both exist
        access_active = await is_user_session_active(
            username, access_jti, kind="access"
        )
        refresh_active = await is_user_session_active(
            username, refresh_jti, kind="refresh"
        )

        assert access_active is True
        assert refresh_active is True

        # Verify they're separate
        access_wrong = await is_user_session_active(
            username, refresh_jti, kind="access"
        )
        assert access_wrong is False

        # Cleanup
        client = get_redis()
        await client.delete(f"session:access:{username}")
        await client.delete(f"session:refresh:{username}")


async def test_session_metadata() -> None:
    """Test storing and retrieving session metadata."""
    async with redis_lifespan():
        username = "test_user_meta"
        jti = "test_jti_meta"
        exp_unix_ts = int(time.time()) + 3600
        meta = {"ip": "192.168.1.1", "user_agent": "TestAgent/1.0"}

        await store_session_for_user(
            username=username,
            jti=jti,
            exp_unix_ts=exp_unix_ts,
            kind="access",
            meta=meta,
        )

        # Retrieve metadata
        client = get_redis()
        stored_ip = await client.hget(f"session:access:{username}", "ip")
        stored_ua = await client.hget(f"session:access:{username}", "user_agent")

        assert stored_ip == "192.168.1.1"
        assert stored_ua == "TestAgent/1.0"

        # Cleanup
        await client.delete(f"session:access:{username}")


async def test_redis_lifespan_error_handling() -> None:
    """Test that Redis lifespan properly handles cleanup on error."""
    import app.core.redis as redis_module

    try:
        async with redis_lifespan():
            assert redis_module._redis is not None
            raise ValueError("Simulated error during app execution")
    except ValueError:
        pass

    assert redis_module._redis is None
