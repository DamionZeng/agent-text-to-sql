from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.datasource import Datasource
from app.models.datasource import DatasourceMySQL
from app.repositories.mysql.meta.mappers.datasource_mapper import DatasourceMapper


class DatasourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, datasource: Datasource) -> Datasource:
        model = DatasourceMapper.to_model(datasource)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return DatasourceMapper.to_entity(model)

    async def get_by_id(self, datasource_id: str) -> Datasource | None:
        result = await self.session.get(DatasourceMySQL, datasource_id)
        if result:
            return DatasourceMapper.to_entity(result)
        return None

    async def list_all(self, offset: int = 0, limit: int | None = None) -> list[Datasource]:
        stmt = select(DatasourceMySQL).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [DatasourceMapper.to_entity(row) for row in rows]

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(DatasourceMySQL))
        return result.scalar() or 0

    async def update(self, datasource: Datasource) -> Datasource:
        model = DatasourceMapper.to_model(datasource)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return DatasourceMapper.to_entity(merged)

    async def delete(self, datasource_id: str) -> bool:
        model = await self.session.get(DatasourceMySQL, datasource_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False
