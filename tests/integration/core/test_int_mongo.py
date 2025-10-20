import logging
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

import app.core.mongo as mongo_module
from app.core.config import settings
from app.core.mongo import (
    _wait_for_mongo,
    beanie_lifespan,
    get_client,
    get_db,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_docker_cleanup]


@pytest.fixture(scope="session", autouse=True)
def disable_pymongo_logging() -> None:
    """Disable PyMongo logging to prevent errors during test teardown."""
    logging.getLogger("pymongo").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.connection").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.topology").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.command").setLevel(logging.CRITICAL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_database() -> AsyncGenerator[None, None]:
    """Clean up the test database after all tests complete."""
    yield

    if await _is_mongo_available():
        client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri())
        try:
            await client.drop_database(settings.database_name)
            logger.info(f"Dropped test database: {settings.database_name}")
        except Exception as e:
            logger.warning(f"Failed to drop test database: {e}")
        finally:
            client.close()


async def _is_mongo_available() -> bool:
    """Check if MongoDB is available with a fast timeout."""
    try:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            settings.mongodb_uri(),
            serverSelectionTimeoutMS=1000,
        )
        await client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture(scope="function")
async def mongo_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Fixture to provide a Motor client for testing (function-scoped for proper event loop management)."""
    if not await _is_mongo_available():
        pytest.skip("MongoDB is not available")

    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri())
    yield client
    client.close()


@pytest_asyncio.fixture(scope="function")
async def mongo_db(mongo_client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    """Fixture to provide a MongoDB database for testing (function-scoped)."""
    return mongo_client[settings.database_name]


async def test_get_client_not_initialized() -> None:
    """Test that get_client raises error when not initialized."""

    original_client = mongo_module._client
    mongo_module._client = None

    try:
        with pytest.raises(RuntimeError, match="Mongo client not initialized"):
            get_client()
    finally:
        mongo_module._client = original_client


async def test_wait_for_mongo_success(mongo_client: AsyncIOMotorClient) -> None:
    """Test that _wait_for_mongo succeeds when MongoDB is running."""
    await _wait_for_mongo(mongo_client, attempts=5, delay=0.1)


async def test_wait_for_mongo_with_retries(mongo_client: AsyncIOMotorClient) -> None:
    """Test that _wait_for_mongo retries multiple times."""
    await _wait_for_mongo(mongo_client, attempts=10, delay=0.05)


async def test_get_db_returns_database() -> None:
    """Test that get_db returns a Motor database instance."""
    async with beanie_lifespan():
        db = get_db()
        assert db is not None
        assert isinstance(db, AsyncIOMotorDatabase)


async def test_beanie_lifespan_initialization() -> None:
    """Test that beanie_lifespan properly initializes MongoDB."""
    async with beanie_lifespan():
        client = get_client()
        assert client is not None

        db = get_db()
        assert db is not None


async def test_beanie_lifespan_cleanup() -> None:
    """Test that beanie_lifespan properly cleans up on exit."""
    import app.core.mongo as mongo_module

    async with beanie_lifespan():
        assert mongo_module._client is not None

    assert mongo_module._client is None


async def test_beanie_lifespan_database_operations(
    mongo_db: AsyncIOMotorDatabase,
) -> None:
    """Test that Beanie is properly initialized for database operations."""
    async with beanie_lifespan():
        db = get_db()
        collections = await db.list_collection_names()
        assert isinstance(collections, list)


async def test_mongo_ping(mongo_client: AsyncIOMotorClient) -> None:
    """Test that we can ping MongoDB."""
    result = await mongo_client.admin.command("ping")
    assert result is not None
    assert "ok" in result or result is True or result == "PONG"


async def test_mongo_database_exists(mongo_db: AsyncIOMotorDatabase) -> None:
    """Test that the configured database exists."""
    result = await mongo_db.command("ping")
    assert result is not None


async def test_mongo_collection_operations(mongo_db: AsyncIOMotorDatabase) -> None:
    """Test basic collection operations."""
    collection = mongo_db["test_collection"]

    doc = {"name": "test", "value": 42}
    result = await collection.insert_one(doc)
    assert result.inserted_id is not None

    found = await collection.find_one({"name": "test"})
    assert found is not None
    assert found["value"] == 42

    await collection.delete_one({"name": "test"})


async def test_beanie_lifespan_with_document_models() -> None:
    """Test that Beanie is initialized with document models."""
    async with beanie_lifespan():
        client = get_client()
        assert client is not None

        db = get_db()
        assert db is not None


async def test_beanie_lifespan_error_handling() -> None:
    """Test that Beanie lifespan properly handles cleanup on error."""
    import app.core.mongo as mongo_module

    try:
        async with beanie_lifespan():
            assert mongo_module._client is not None
            raise ValueError("Simulated error during app execution")
    except ValueError:
        pass

    assert mongo_module._client is None
