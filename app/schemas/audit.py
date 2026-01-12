from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ResponseEnvelope


class AuditPostRequest(BaseModel):
    """Schema for creating an audit record via POST /audits."""

    model_config = ConfigDict(extra="ignore")

    actor_id: str = Field(
        ..., validation_alias="actorId", serialization_alias="actorId"
    )
    action: str
    detail: str


class AuditRead(BaseModel):
    id: str = Field(serialization_alias="id")
    actor_id: str = Field(serialization_alias="actorId")
    action: str
    detail: str


class AuditPostResponse(ResponseEnvelope[AuditRead]):
    """Envelope wrapping the created audit record."""
