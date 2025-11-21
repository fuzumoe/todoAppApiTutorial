import asyncio
import ssl as _ssl
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import cast

from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


def _build_redis() -> Redis:
    kwargs: dict = {  
        "decode_responses": settings.redis_decode_responses,
        "socket_connect_timeout": settings.redis_socket_connect_timeout,
        "socket_timeout": settings.redis_socket_timeout,
        "max_connections": settings.redis_connection_pool_max_connections,
    }

    # SSL cert requirements mapping if SSL is enabled
    if settings.redis_ssl:
        mapping = {
            "none": _ssl.CERT_NONE,
            "optional": _ssl.CERT_OPTIONAL,
            "required": _ssl.CERT_REQUIRED,
        }
        kwargs["ssl_cert_reqs"] = mapping.get(
            (settings.redis_ssl_cert_reqs or "none").lower(), _ssl.CERT_NONE
        )

    redis_url = str(settings.redis_url)
    client =  Redis.from_url(redis_url, **kwargs)
    return client   # connection object  = client

# READINESS PROBE
async def _wait_for_redis(
    client: Redis, *, attempts: int = 20, delay: float = 0.25
) -> bool | None:
    last_exc: Exception | None = None
    
    """
    attempt 1:
            pong = True
            redis = ready
            return True  
    """
    for _ in range(attempts):
        try:
            # ping = you pushing the ball redis
            pong = await client.ping() # object tha represent redis db | connection object
            # pong = redis pushing the bal back to you
            # if pong is false = redis did no receive the ball or did nt push back the ball indicating redis is not ready
            # if true = redis is alive and ready
            if pong:  # True / "PONG"
                return
        except Exception as exc:  # pragma: no cover (startup path)
            last_exc = exc
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 3.0)
    raise RuntimeError("Redis not ready after retries") from last_exc


# SINGLETON CONNECTION
def get_redis() -> Redis:
    """
    Access the initialized Redis client. Call within app lifespan.
    """
    if _client is None:
        raise RuntimeError("Redis client not initialized. Use within app lifespan.")
    return _client

# lifespan 
# redis should be ready =_wait_for_redis 
# get redis need to get a built connection ? = _build_redis()
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
    global _client 
    _client = _build_redis() # redis client or connection object 
    await _wait_for_redis(_client)
    try:
        yield
    finally:
        if _client is not None:
            await _client.close()
            _client = None


# Session utilities (username key)


def _session_key(kind: str, username: str) -> str:
    """
    Session key format: session:<kind>:<username>
    Example: session:access:alice
    """
    return f"session:{kind}:{username}"


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
    r = get_redis()
    ttl = max(
        1, exp_unix_ts - int(asyncio.get_running_loop().time() // 1 + 0)
    )  # safe min TTL
    # Better TTL calc (UTC now):
    import time

    ttl = max(1, exp_unix_ts - int(time.time()))

    key = _session_key(kind, username)
    payload: dict[str, str] = {"jti": jti, "exp": str(exp_unix_ts)}
    if meta:
        # Convert all meta values to strings for Redis
        payload.update({k: str(v) for k, v in meta.items()})

    async with r.pipeline(transaction=True) as pipe:
        # Cast to satisfy mypy's strict type checking for Redis hset
        await pipe.hset(
            key, mapping=cast(Mapping[str | bytes, bytes | float | int | str], payload)
        )
        await pipe.expire(key, ttl)
        await pipe.execute()


async def is_user_session_active(
    username: str, jti: str, *, kind: str = "access"
) -> bool:
    """
    Check if the stored JTI for this user/kind matches the presented token JTI.
    """
    r = get_redis()
    key = _session_key(kind, username)
    stored_jti = await r.hget(key, "jti")
    return cast(bool, stored_jti == jti)


async def revoke_user_session(username: str, *, kind: str = "access") -> None:
    """
    Delete the user's session record for the given kind (access/refresh).
    """
    r = get_redis()
    await r.delete(_session_key(kind, username))
