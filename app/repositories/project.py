from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.project import Project


class ProjectRepository:
    """Repository for Project documents."""

    async def create(self, project: Project) -> Project:
        await project.insert()
        return project

    async def get(self, id: PydanticObjectId | str) -> Project | None:
        doc: Project | None = await Project.get(id)
        return doc

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Project]:
        items: list[Project] = (
            await Project.find_all().skip(skip).limit(limit).to_list()
        )
        return items

    async def update(
        self, id: PydanticObjectId | str, patch: Mapping[str, Any]
    ) -> Project | None:
        doc: Project | None = await Project.get(id)
        if doc is None:
            return None
        for k, v in patch.items():
            setattr(doc, k, v)
        await doc.save()
        return doc

    async def delete(self, id: PydanticObjectId | str) -> bool:
        doc = await Project.get(id)
        if doc is None:
            return False
        await doc.delete()
        return True
