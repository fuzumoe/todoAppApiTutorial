from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.project import Project


class ProjectRepository:
    """Repository for Project documents."""
 
