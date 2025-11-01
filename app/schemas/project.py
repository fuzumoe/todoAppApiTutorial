from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ResponseEnvelope


class ProjectPostRequest(BaseModel):
    """Schema for creating a project via POST /project."""


class ProjectRead(BaseModel):
    pass


class ProjectPostResponse(ResponseEnvelope[ProjectRead]):
    """Envelope wrapping the created project."""
