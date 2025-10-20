from beanie import Link
from pydantic import Field

from app.models.base import BaseDoc
from app.models.user import User


class Project(BaseDoc):
    name: str = Field(..., alias="name")
    description: str | None = Field(default=None, alias="description")
    owner: Link[User] = Field(..., alias="ownerId")  # stored as reference

    class Settings:
        name = "projects"
