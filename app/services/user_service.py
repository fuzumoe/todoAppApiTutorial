from typing import Any, Protocol, runtime_checkable

from app.repositories.user import UserRepository

from .orm_service import ORMService


@runtime_checkable
class HasEmailRepository(Protocol):
    async def get_by_email(self, email: str) -> Any:
        ...


class UserService(ORMService[UserRepository]):
    async def create_user(self, data: dict[str, Any]) -> Any:
        return await self.create(data)

    async def get_user(self, user_id: Any) -> Any | None:
        return await self.get(user_id)

    async def list_users(self, *, limit: int = 50, offset: int = 0) -> Any:
        return await self.list(limit=limit, offset=offset)

    async def update_user(self, user_id: Any, data: dict[str, Any]) -> Any | None:
        return await self.update(user_id, data)

    async def delete_user(self, user_id: Any) -> bool:
        return await self.delete(user_id)

    async def get_by_email(self, email: str) -> Any | None:
        # Delegate if repository supports get_by_email
        repo = self.repository
        if isinstance(repo, HasEmailRepository):
            return await repo.get_by_email(email)
        return None
