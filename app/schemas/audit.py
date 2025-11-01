from __future__ import annotations

from pydantic import BaseModel


class AuditPostRequest(BaseModel):
    """Schema for creating an audit record via POST /audits."""
