from typing import Any, Generic, Protocol, TypeVar, runtime_checkable


@runtime_checkable
class RepositoryProtocol(Protocol):
    async def create(self, data: dict[str, Any]) -> Any:
        ...

    async def get(self, id_: Any) -> Any | None:
        ...

    async def list(
        self, *, limit: int = 50, offset: int = 0, filters: dict[str, Any] | None = None
    ) -> Any:
        ...

    async def update(self, id_: Any, data: dict[str, Any]) -> Any | None:
        ...

    async def delete(self, id_: Any) -> bool:
        ...


R = TypeVar("R", bound=RepositoryProtocol)


class ORMService(Generic[R]):
    """Thin async service layer delegating to a repository.

    The repository is expected to provide async methods: create, get, list, update, delete.
    Implementations can add higher-level behaviors (validation, mapping, etc.).
    """

    def __init__(self, repository: R) -> None:
        self.repository = repository

    async def create(self, data: dict[str, Any]) -> Any:
        return await self.repository.create(data)

    async def get(self, id_: Any) -> Any | None:
        return await self.repository.get(id_)

    async def list(
        self, *, limit: int = 50, offset: int = 0, filters: dict[str, Any] | None = None
    ) -> Any:
        return await self.repository.list(
            limit=limit, offset=offset, filters=filters or {}
        )

    async def update(self, id_: Any, data: dict[str, Any]) -> Any | None:
        return await self.repository.update(id_, data)

    async def delete(self, id_: Any) -> bool:
        result = await self.repository.delete(id_)
        return bool(result)
