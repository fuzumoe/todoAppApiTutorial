from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

_redis: Redis | None = None


def _build_redis() -> Redis | None:
    return None


async def _wait_for_redis(
    client: Redis, *, attempts: int = 20, delay: float = 0.25
) -> None:
    pass


def get_redis() -> Redis | None:
    """
    Access the initialized Redis client. Call within app lifespan.
    """
    return None


@asynccontextmanager
async def redis_lifespan() -> AsyncIterator[None]:
    """
    FastAPI lifespan context: initialize Redis on startup, close on shutdown.

    Usage (in app/main.py):
        from app.core.redis import redis_lifespan
        async def lifespan(app):
            async with redis_lifespan():
                yield
    """
    yield


# Session utilities (username key)


def _session_key(kind: str, username: str) -> str | None:
    """
    Session key format: session:<kind>:<username>
    Example: session:access:alice
    """
    return None


async def store_session_for_user(
    username: str,
    jti: str,
    exp_unix_ts: int,
    *,
    kind: str = "access",
    meta: dict | None = None,
) -> None:
    """
    Store the current active token info for a user under their username key.
    Enforces ONE active token per <kind> per user.
    """
    return


async def is_user_session_active(
    username: str, jti: str, *, kind: str = "access"
) -> bool:
    """
    Check if the stored JTI for this user/kind matches the presented token JTI.
    """
    return False


async def revoke_user_session(username: str, *, kind: str = "access") -> None:
    """
    Delete the user's session record for the given kind (access/refresh).
    """
    return
