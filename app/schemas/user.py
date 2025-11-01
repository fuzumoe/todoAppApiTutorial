from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ResponseEnvelope


class UserPostRequest(BaseModel):
    """Schema for creating a user via POST /users.

    Fields:
    - username (public API name; stored internally as full_name)
    - email
    - password
    - roles (optional)

    Extra fields are ignored to keep the payload strict but flexible.
    """


class UserRead(BaseModel):
    """Shape of a user returned by the API (no password)."""


class UserPostResponse(ResponseEnvelope[UserRead]):
    """Envelope wrapping the created user with status and message."""
