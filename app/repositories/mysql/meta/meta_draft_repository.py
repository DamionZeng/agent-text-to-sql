from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.meta_draft import MetaDraft
from app.models.meta_draft import MetaDraftMySQL
from app.repositories.mysql.meta.mappers.meta_draft_mapper import MetaDraftMapper


class MetaDraftRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, meta_draft: MetaDraft) -> MetaDraft:
        model = MetaDraftMapper.to_model(meta_draft)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return MetaDraftMapper.to_entity(model)

    async def get_by_id(self, draft_id: str) -> MetaDraft | None:
        result = await self.session.get(MetaDraftMySQL, draft_id)
        if result:
            return MetaDraftMapper.to_entity(result)
        return None

    async def get_latest_by_datasource_id(self, datasource_id: str) -> MetaDraft | None:
        result = await self.session.execute(
            select(MetaDraftMySQL)
            .where(MetaDraftMySQL.datasource_id == datasource_id)
            .order_by(MetaDraftMySQL.version.desc())
        )
        row = result.scalars().first()
        if row:
            return MetaDraftMapper.to_entity(row)
        return None

    async def get_by_datasource_id(self, datasource_id: str) -> MetaDraft | None:
        return await self.get_latest_by_datasource_id(datasource_id)

    async def list_by_datasource_id(self, datasource_id: str, offset: int = 0, limit: int | None = None) -> list[MetaDraft]:
        stmt = (
            select(MetaDraftMySQL)
            .where(MetaDraftMySQL.datasource_id == datasource_id)
            .order_by(MetaDraftMySQL.version.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [MetaDraftMapper.to_entity(row) for row in rows]

    async def count_by_datasource_id(self, datasource_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(MetaDraftMySQL).where(MetaDraftMySQL.datasource_id == datasource_id)
        )
        return result.scalar() or 0

    async def get_next_version(self, datasource_id: str) -> int:
        result = await self.session.execute(
            select(func.max(MetaDraftMySQL.version))
            .where(MetaDraftMySQL.datasource_id == datasource_id)
        )
        max_version = result.scalar()
        return (max_version or 0) + 1

    async def update(self, meta_draft: MetaDraft) -> MetaDraft:
        model = MetaDraftMapper.to_model(meta_draft)
        merged = await self.session.merge(model)
        await self.session.flush()
        await self.session.refresh(merged)
        return MetaDraftMapper.to_entity(merged)

    async def delete_by_datasource_id(self, datasource_id: str) -> bool:
        result = await self.session.execute(
            select(MetaDraftMySQL).where(MetaDraftMySQL.datasource_id == datasource_id)
        )
        rows = result.scalars().all()
        for row in rows:
            await self.session.delete(row)
        if rows:
            await self.session.flush()
            return True
        return False