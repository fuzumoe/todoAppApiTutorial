from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None

# READINESS PROBE
async def _wait_for_mongo(
    client: AsyncIOMotorClient, *, attempts: int = 10, delay: float = 0.5
) -> None:
    """Wait until Mongo responds to ping (helpful with Docker)."""

# SINGLETON CONNECTION
def get_db() -> AsyncIOMotorDatabase | None:
    """
    Access the initialized Motor database. Call within app lifespan.
    """
    return None

# lifespan 
# mongodb should be ready = _wait_for_mongo
# to check for readiness you nee mongo client = get_db
@asynccontextmanager
async def beanie_lifespan() -> AsyncIterator[None]:
    """
    Creates Motor client from settings, waits for Mongo,
    initializes **Beanie** with your Document models, then closes on shutdown.
    """
    # set up client / beanie initialization here
    # client = get_db()
    # _wait_for_mongo(client)
    # initialize models
    """ 
    models = [prjects, ...]
    await init_beanie(database=cast(Any, db), document_models=models)
    """
    yield
    # cleanup / close client here
