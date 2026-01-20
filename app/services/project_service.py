from typing import Any

from .orm_service import ORMService


class ProjectService(ORMService):
    async def get_project(self, project_id: Any) -> Any | None:
        return await self.get(project_id)

    async def list_projects(self, *, limit: int = 50, offset: int = 0) -> Any:
        return await self.list(limit=limit, offset=offset)
