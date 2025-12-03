from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.user import User


class UserRepository:
    """Repository for User documents.

    Minimal CRUD + a convenience finder.
    Intended to be consumed by services/routers.
    """
 