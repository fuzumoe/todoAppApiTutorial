from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.task import Task


class TaskRepository:
    """Repository for Task documents."""

    async def create(self, task: Task) -> Task:
        await task.insert()
        return task

    async def get(self, id: PydanticObjectId | str) -> Task | None:
        doc: Task | None = await Task.get(id)
        return doc

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Task]:
        items: list[Task] = await Task.find_all().skip(skip).limit(limit).to_list()
        return items

    async def update(
        self, id: PydanticObjectId | str, patch: Mapping[str, Any]
    ) -> Task | None:
        doc: Task | None = await Task.get(id)
        if doc is None:
            return None
        for k, v in patch.items():
            setattr(doc, k, v)
        await doc.save()
        return doc

    async def delete(self, id: PydanticObjectId | str) -> bool:
        doc = await Task.get(id)
        if doc is None:
            return False
        await doc.delete()
        return True
