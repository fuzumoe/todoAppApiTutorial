from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.mongo import beanie_lifespan
from app.models.enums import Role, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.task import TaskRepository

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
            await Task.find_all().delete()
            await Project.find_all().delete()
            await User.find_all().delete()
    except Exception:
        # Cleanup is best-effort for local/dev; don't fail tests on teardown
        pass


async def _make_user(idx: int = 1) -> User:
    user = User(
        full_name=f"Assignee {idx}",
        email=f"assignee{idx}@example.com",
        password_hash="hashed-password",
        roles=[Role.USER],
    )
    await user.insert()
    return user


async def _make_project(idx: int = 1, owner: User | None = None) -> Project:
    if owner is None:
        owner = await _make_user(idx)
    project = Project(name=f"Project {idx}", description=f"p{idx}", owner=owner)
    await project.insert()
    return project


async def test_task_create_and_get() -> None:
    async with beanie_lifespan():
        repo = TaskRepository()
        owner = await _make_user(1)
        project = await _make_project(1, owner)
        assignee = await _make_user(2)

        task = Task(description="Do something", project=project, assigned_to=assignee)
        created = await repo.create(task)

        assert created.id is not None

        fetched = await repo.get(str(created.id))
        assert fetched is not None
        assert fetched.description == "Do something"
        assert fetched.project is not None
        assert fetched.assigned_to is not None
        assert fetched.status == TaskStatus.PENDING


async def test_task_list_pagination() -> None:
    async with beanie_lifespan():
        repo = TaskRepository()
        owner = await _make_user(3)
        project = await _make_project(2, owner)

        # create multiple tasks
        for i in range(5):
            t = Task(description=f"t{i}", project=project)
            await repo.create(t)

        first_page = await repo.list(skip=0, limit=3)
        second_page = await repo.list(skip=3, limit=3)

        assert len(first_page) == 3
        assert len(second_page) >= 2


async def test_task_update_status_and_assignment() -> None:
    async with beanie_lifespan():
        repo = TaskRepository()
        owner = await _make_user(4)
        project = await _make_project(3, owner)
        task = await repo.create(Task(description="initial", project=project))

        new_assignee = await _make_user(5)
        updated = await repo.update(
            str(task.id),
            {"status": TaskStatus.COMPLETED, "assigned_to": new_assignee},
        )

        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED
        assert updated.assigned_to is not None


async def test_task_delete() -> None:
    async with beanie_lifespan():
        repo = TaskRepository()
        owner = await _make_user(6)
        project = await _make_project(4, owner)

        task = await repo.create(Task(description="remove me", project=project))

        ok = await repo.delete(str(task.id))
        assert ok is True

        missing = await repo.get(str(task.id))
        assert missing is None
