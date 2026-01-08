from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Status(str, Enum):
    success = "success"
    error = "error"


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response envelope.

    - status: overall status (success/error)
    - message: brief human-readable message
    - data: payload (generic)

    """
    status: Status = Field(default=Status.success)
    message: str = Field(default="Ok")
    data: T | None = None

class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Page(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta
