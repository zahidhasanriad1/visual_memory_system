from typing import Generic, TypeVar, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from vms_data_access.interfaces.i_base_repository import IBaseRepository

TEntity = TypeVar("TEntity")

class BaseRepository(IBaseRepository[TEntity], Generic[TEntity]):
    """Generic async repository for all CRUD operations."""

    def __init__(self, session: AsyncSession, entity_type: type[TEntity]) -> None:
        self._session = session
        self._entity_type = entity_type

    async def add_async(self, entity: TEntity) -> TEntity:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def get_by_id_async(self, entity_id: str) -> TEntity | None:
        return await self._session.get(self._entity_type, entity_id)

    async def list_async(self, limit: int = 100, offset: int = 0) -> Sequence[TEntity]:
        result = await self._session.execute(select(self._entity_type).limit(limit).offset(offset))
        return result.scalars().all()

    async def delete_async(self, entity: TEntity) -> None:
        await self._session.delete(entity)

    async def save_changes_async(self) -> None:
        await self._session.commit()
