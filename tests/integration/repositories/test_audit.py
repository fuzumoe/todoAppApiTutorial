from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.mongo import beanie_lifespan
from app.models.audit import Audit
from app.models.enums import Role
from app.models.user import User
from app.repositories.audit import AuditRepository

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
            await Audit.find_all().delete()
            await User.find_all().delete()
    except Exception:
        # Cleanup is best-effort for local/dev; don't fail tests on teardown
        pass


async def _make_user(idx: int = 1) -> User:
    user = User(
        full_name=f"Tester {idx}",
        email=f"tester{idx}@example.com",
        password_hash="hashed-password",
        roles=[Role.USER],
    )
    await user.insert()
    return user


async def test_audit_create_and_get() -> None:
    async with beanie_lifespan():
        repo = AuditRepository()
        actor = await _make_user(1)

        audit = Audit(actor=actor, action="LOGIN", detail="User logged in")
        created = await repo.create(audit)

        assert created.id is not None

        fetched = await repo.get(str(created.id))
        assert fetched is not None
        assert fetched.action == "LOGIN"
        assert fetched.detail == "User logged in"
        # Link[User] may not expose .id statically; ensure link present
        assert fetched.actor is not None


async def test_audit_list_pagination() -> None:
    async with beanie_lifespan():
        repo = AuditRepository()
        actor = await _make_user(2)

        # create multiple audit entries
        for i in range(5):
            a = Audit(actor=actor, action="ACTION", detail=f"d{i}")
            await repo.create(a)

        first_page = await repo.list(skip=0, limit=3)
        second_page = await repo.list(skip=3, limit=3)

        assert len(first_page) == 3
        assert len(second_page) >= 2


async def test_audit_update() -> None:
    async with beanie_lifespan():
        repo = AuditRepository()
        actor = await _make_user(3)

        audit = await repo.create(
            Audit(actor=actor, action="UPDATE_PROFILE", detail="before")
        )

        updated = await repo.update(str(audit.id), {"detail": "after"})
        assert updated is not None
        assert updated.detail == "after"


async def test_audit_delete() -> None:
    async with beanie_lifespan():
        repo = AuditRepository()
        actor = await _make_user(4)

        audit = await repo.create(
            Audit(actor=actor, action="DELETE_ACCOUNT", detail="to be removed")
        )

        ok = await repo.delete(str(audit.id))
        assert ok is True

        missing = await repo.get(str(audit.id))
        assert missing is None
