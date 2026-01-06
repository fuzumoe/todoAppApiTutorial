from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.mongo import beanie_lifespan
from app.models.enums import Role
from app.models.user import User
from app.repositories.user import UserRepository

pytestmark = [pytest.mark.asyncio, pytest.mark.no_docker_cleanup]


@pytest.fixture(scope="session", autouse=True)
def disable_pymongo_logging() -> None:
    """Reduce PyMongo logging to avoid noisy teardown errors during tests."""
    import logging

    logging.getLogger("pymongo").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.connection").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.topology").setLevel(logging.CRITICAL)
    logging.getLogger("pymongo.command").setLevel(logging.CRITICAL)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_after_each_test() -> AsyncGenerator[None, None]:
    """Ensure collections are cleaned between tests.

    We create a fresh Beanie/Mongo context to perform cleanup so this runs
    even after tests that closed their own lifespan.
    """
    yield
    try:
        async with beanie_lifespan():
            await User.find_all().delete()
    except Exception:
        # Cleanup is best-effort for local/dev; don't fail tests on teardown
        pass


async def _make_user(idx: int = 1, roles: list[Role] | None = None) -> User:
    user = User(
        full_name=f"User {idx}",
        email=f"user{idx}@example.com",
        password_hash="hashed-password",
        roles=roles if roles is not None else [Role.USER],
    )
    await user.insert()
    return user


async def test_user_create_and_get() -> None:
    async with beanie_lifespan():
        repo = UserRepository()
        created = await repo.create(
            User(
                full_name="Alice",
                email="alice@example.com",
                password_hash="hashed",
                roles=[Role.USER],
            )
        )

        assert created.id is not None

        fetched = await repo.get(str(created.id))
        assert fetched is not None
        assert fetched.full_name == "Alice"
        assert fetched.email == "alice@example.com"
        assert Role.USER in fetched.roles


async def test_user_get_by_email() -> None:
    async with beanie_lifespan():
        repo = UserRepository()
        await _make_user(2)

        fetched = await repo.get_by_email("user2@example.com")
        assert fetched is not None
        assert fetched.email == "user2@example.com"


async def test_user_list_pagination() -> None:
    async with beanie_lifespan():
        repo = UserRepository()
        for i in range(5):
            await _make_user(10 + i)

        first_page = await repo.list(skip=0, limit=3)
        second_page = await repo.list(skip=3, limit=3)

        assert len(first_page) == 3
        assert len(second_page) >= 2


async def test_user_update() -> None:
    async with beanie_lifespan():
        repo = UserRepository()
        user = await _make_user(20)

        updated = await repo.update(str(user.id), {"full_name": "Bob"})
        assert updated is not None
        assert updated.full_name == "Bob"


async def test_user_delete() -> None:
    async with beanie_lifespan():
        repo = UserRepository()
        user = await _make_user(30)

        ok = await repo.delete(str(user.id))
        assert ok is True

        missing = await repo.get(str(user.id))
        assert missing is None
