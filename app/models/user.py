from typing import Annotated, ClassVar

from beanie import Indexed
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.models.base import BaseDoc
from app.models.enums import Role


class User(BaseDoc):
    full_name: str = Field(..., alias="fullName")
    # Use Annotated to declare Beanie index metadata without tripping mypy
    email: Annotated[str, Indexed(unique=True)] = Field(..., alias="email")
    # SECURITY NOTE: store a **hash**, not a plaintext password
    password_hash: str = Field(
        ..., alias="password"
    )  # you can still alias as 'password' for I/O
    roles: list[Role] = Field(default_factory=lambda: [Role.USER], alias="roles")

    class Settings:
        name: ClassVar[str] = "users"  # collection

        indexes: ClassVar[list[IndexModel]] = [IndexModel([("createdAt", ASCENDING)])]

    def __repr__(self) -> str:
        return f"<User {self.email} roles={self.roles}>"
