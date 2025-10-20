from typing import Any

from .audit import Audit
from .project import Project
from .task import Task
from .user import User

models: list[type[Any]] = [Audit, Project, Task, User]

__all__ = ["Audit", "Project", "Task", "User", "models"]
