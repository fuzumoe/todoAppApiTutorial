from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Status(str, Enum):
    pass


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response envelope.

    - status: overall status (success/error)
    - message: brief human-readable message
    - data: payload (generic)
    """


class PageMeta(BaseModel):
    pass


class Page(BaseModel, Generic[T]):
    pass
