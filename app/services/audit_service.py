from typing import Any

from app.repositories.audit import AuditRepository

from .orm_service import ORMService


class AuditService(ORMService[AuditRepository]):
    async def get_audit(self, audit_id: Any) -> Any | None:
        return await self.get(audit_id)

    async def list_audits(self, *, limit: int = 50, offset: int = 0) -> Any:
        return await self.list(limit=limit, offset=offset)
