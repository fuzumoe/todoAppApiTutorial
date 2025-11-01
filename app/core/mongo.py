from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None


async def _wait_for_mongo(
    client: AsyncIOMotorClient, *, attempts: int = 10, delay: float = 0.5
) -> None:
    """Wait until Mongo responds to ping (helpful with Docker)."""


def get_db() -> AsyncIOMotorDatabase | None:
    """
    Access the initialized Motor database. Call within app lifespan.
    """
    return None


@asynccontextmanager
async def beanie_lifespan() -> AsyncIterator[None]:
    """
    Creates Motor client from settings, waits for Mongo,
    initializes **Beanie** with your Document models, then closes on shutdown.
    """
    # set up client / beanie initialization here
    yield
    # cleanup / close client here
