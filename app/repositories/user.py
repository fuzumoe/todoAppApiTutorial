from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.user import User


class UserRepository:
    """Repository for User documents.

    Minimal CRUD + a convenience finder.
    Intended to be consumed by services/routers.
    """

    async def create(self, user: User) -> User:
        await user.insert()
        return user

    async def get(self, id: PydanticObjectId | str) -> User | None:
        doc: User | None = await User.get(id)
        return doc

    async def get_by_email(self, email: str) -> User | None:
        doc: User | None = await User.find_one(User.email == email)
        return doc

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        items: list[User] = await User.find_all().skip(skip).limit(limit).to_list()
        return items

    async def update(
        self, id: PydanticObjectId | str, patch: Mapping[str, Any]
    ) -> User | None:
        doc: User | None = await User.get(id)
        if doc is None:
            return None
        for k, v in patch.items():
            setattr(doc, k, v)
        await doc.save()
        return doc

    async def delete(self, id: PydanticObjectId | str) -> bool:
        doc = await User.get(id)
        if doc is None:
            return False
        await doc.delete()
        return True
