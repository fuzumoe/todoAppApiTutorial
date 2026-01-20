from typing import Any

from app.repositories.task import TaskRepository

from .orm_service import ORMService


class TaskService(ORMService[TaskRepository]):
    async def get_task(self, task_id: Any) -> Any | None:
        return await self.get(task_id)

    async def list_tasks(self, *, limit: int = 50, offset: int = 0) -> Any:
        return await self.list(limit=limit, offset=offset)
