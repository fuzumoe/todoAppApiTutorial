from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.mongo import beanie_lifespan
from app.models.enums import Role
from app.models.project import Project
from app.models.user import User
from app.repositories.project import ProjectRepository

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
            await Project.find_all().delete()
            await User.find_all().delete()
    except Exception:
        # Cleanup is best-effort for local/dev; don't fail tests on teardown
        pass


async def _make_user(idx: int = 1) -> User:
    user = User(
        full_name=f"Owner {idx}",
        email=f"owner{idx}@example.com",
        password_hash="hashed-password",
        roles=[Role.USER],
    )
    await user.insert()
    return user


async def test_project_create_and_get() -> None:
    async with beanie_lifespan():
        repo = ProjectRepository()
        owner = await _make_user(1)

        project = Project(name="Proj A", description="First", owner=owner)
        created = await repo.create(project)

        assert created.id is not None

        fetched = await repo.get(str(created.id))
        assert fetched is not None
        assert fetched.name == "Proj A"
        assert fetched.description == "First"
        # Link[User] may not expose .id statically; ensure link present
        assert fetched.owner is not None


async def test_project_list_pagination() -> None:
    async with beanie_lifespan():
        repo = ProjectRepository()
        owner = await _make_user(2)

        # create multiple projects
        for i in range(5):
            p = Project(name=f"P{i}", description=f"d{i}", owner=owner)
            await repo.create(p)

        first_page = await repo.list(skip=0, limit=3)
        second_page = await repo.list(skip=3, limit=3)

        assert len(first_page) == 3
        assert len(second_page) >= 2


async def test_project_update() -> None:
    async with beanie_lifespan():
        repo = ProjectRepository()
        owner = await _make_user(3)

        project = await repo.create(
            Project(name="Old Name", description="before", owner=owner)
        )

        updated = await repo.update(
            str(project.id), {"name": "New Name", "description": "after"}
        )
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.description == "after"


async def test_project_delete() -> None:
    async with beanie_lifespan():
        repo = ProjectRepository()
        owner = await _make_user(4)

        project = await repo.create(
            Project(name="To Delete", description="remove me", owner=owner)
        )

        ok = await repo.delete(str(project.id))
        assert ok is True

        missing = await repo.get(str(project.id))
        assert missing is None
