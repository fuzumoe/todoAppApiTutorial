from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskStatus
from app.schemas.common import ResponseEnvelope


class TaskPostRequest(BaseModel):
    """Schema for creating a task via POST /tasks."""

    model_config = ConfigDict(extra="ignore")

    description: str
    project_id: str = Field(
        ..., validation_alias="projectId", serialization_alias="projectId"
    )
    assigned_to: str | None = Field(
        default=None, validation_alias="assignedTo", serialization_alias="assignedTo"
    )
    status: TaskStatus | None = Field(default=None)


class TaskRead(BaseModel):
    id: str = Field(serialization_alias="id")
    description: str
    project_id: str = Field(serialization_alias="projectId")
    assigned_to: str | None = Field(default=None, serialization_alias="assignedTo")
    status: TaskStatus


class TaskPostResponse(ResponseEnvelope[TaskRead]):
    """Envelope wrapping the created task."""
