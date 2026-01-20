from typing import Any, Protocol, runtime_checkable

from app.models.user import User

from .authentication import hash_password
from .orm_service import ORMService


class UserService(ORMService[User]):
    @runtime_checkable
    class HasEmailRepository(Protocol):
        async def get_by_email(self, email: str) -> Any:
            """Retrieve a user by their email address.

            Code challenge guidance:
            - Implement repository method to find a user by email.
            - Return the user document/model on success, or None if not found.
            - Treat email lookup as case-sensitive or normalize (document your choice).
            - Consider indexing or query efficiency (but keep implementation simple).
            """

    async def create_user(self, data: dict[str, Any]) -> Any:
        if data.get("password"):
            data = {**data, "password": hash_password(str(data["password"]))}
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
        """Find a user by email via repository.

        Code challenge behavior to implement:
        - If the underlying repository provides `get_by_email`, delegate to it.
        - Validate the `email` input (non-empty, basic format if desired).
        - Decide on case sensitivity and normalization; document your approach.
        - Return the found user or None if not found.

        Note: Keep this method simple; do not attempt complex caching or retries.
        """
        return None
