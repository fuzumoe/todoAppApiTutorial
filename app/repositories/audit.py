from collections.abc import Mapping
from typing import Any

from beanie import PydanticObjectId

from app.models.audit import Audit


class AuditRepository:
    """Repository for Audit documents."""

    async def create(self, audit: Audit) -> Audit:
        await audit.insert()
        return audit

    async def get(self, id: PydanticObjectId | str) -> Audit | None:
        doc: Audit | None = await Audit.get(id)
        return doc

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Audit]:
        items: list[Audit] = await Audit.find_all().skip(skip).limit(limit).to_list()
        return items

    async def update(
        self, id: PydanticObjectId | str, patch: Mapping[str, Any]
    ) -> Audit | None:
        doc: Audit | None = await Audit.get(id)
        if doc is None:
            return None
        for k, v in patch.items():
            setattr(doc, k, v)
        await doc.save()
        return doc

    async def delete(self, id: PydanticObjectId | str) -> bool:
        doc = await Audit.get(id)
        if doc is None:
            return False
        await doc.delete()
        return True
