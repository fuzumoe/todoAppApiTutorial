from beanie import Link
from pydantic import Field

from app.models.base import BaseDoc
from app.models.enums import TaskStatus
from app.models.project import Project
from app.models.user import User


class Task(BaseDoc):
    description: str = Field(..., alias="description")
    project: Link[Project] = Field(..., alias="projectId")
    assigned_to: Link[User] | None = Field(default=None, alias="assignedTo")
    status: TaskStatus = Field(default=TaskStatus.PENDING, alias="status")

    class Settings:
        name = "tasks"
