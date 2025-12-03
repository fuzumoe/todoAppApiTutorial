from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.task import Task


class TaskRepository:
    """Repository for Task documents."""

    
