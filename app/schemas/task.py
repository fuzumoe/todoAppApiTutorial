from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ResponseEnvelope


class TaskPostRequest(BaseModel):
    """Schema for creating a task via POST /tasks."""


class TaskRead(BaseModel):
    pass


class TaskPostResponse(ResponseEnvelope[TaskRead]):
    """Envelope wrapping the created task."""
