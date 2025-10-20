import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.models import (
    models,  # Import your Beanie document models here
)

_client: AsyncIOMotorClient | None = None


async def _wait_for_mongo(
    client: AsyncIOMotorClient, *, attempts: int = 10, delay: float = 0.5
) -> None:
    """Wait until Mongo responds to ping (helpful with Docker)."""
    last_err: Exception | None = None
    for _ in range(attempts):
        try:
            await client.admin.command("ping")
            return
        except Exception as exc:  # pragma: no cover
            last_err = exc
            await asyncio.sleep(delay)
            delay *= 1.5
    raise RuntimeError("MongoDB not ready") from last_err


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("Mongo client not initialized. Use inside app lifespan.")
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[settings.database_name]


@asynccontextmanager
async def beanie_lifespan() -> AsyncIterator[None]:
    """
    Creates Motor client from settings, waits for Mongo,
    initializes **Beanie** with your Document models, then closes on shutdown.
    """
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri)

    # Wait for Mongo to be reachable
    await _wait_for_mongo(_client)

    try:
        await init_beanie(
            database=_client[settings.database_name],
            document_models=list(models),
        )
        yield
    finally:
        # Close Motor client (Beanie uses Motor's connection)
        if _client is not None:
            _client.close()
            _client = None
