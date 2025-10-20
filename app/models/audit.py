from beanie import Link
from pydantic import Field

from app.models.base import BaseDoc
from app.models.user import User


class Audit(BaseDoc):
    actor: Link[User] = Field(..., alias="actor")  # who did it
    action: str = Field(..., alias="action")  # general_activity
    detail: str | None = Field(
        default=None, alias="detail"
    )  # sub_activity or extra info

    class Settings:
        name = "audit"
