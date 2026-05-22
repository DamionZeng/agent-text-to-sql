from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.chart_config import ChartConfig
from app.models.chart_config import ChartConfigMySQL
from app.repositories.mysql.viz.mappers.chart_config_mapper import ChartConfigMapper


class ChartConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, chart_config: ChartConfig) -> ChartConfig:
        model = ChartConfigMapper.to_model(chart_config)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return ChartConfigMapper.to_entity(model)

    async def get_by_id(self, chart_id: str) -> ChartConfig | None:
        result = await self.session.get(ChartConfigMySQL, chart_id)
        if result:
            return ChartConfigMapper.to_entity(result)
        return None

    async def update(self, chart_config: ChartConfig) -> ChartConfig:
        model = ChartConfigMapper.to_model(chart_config)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return ChartConfigMapper.to_entity(merged)

    async def delete(self, chart_id: str) -> bool:
        model = await self.session.get(ChartConfigMySQL, chart_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

    async def list_by_datasource(self, datasource_id: str, offset: int = 0, limit: int | None = None) -> list[ChartConfig]:
        stmt = select(ChartConfigMySQL).where(ChartConfigMySQL.datasource_id == datasource_id).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [ChartConfigMapper.to_entity(row) for row in rows]

    async def count_by_datasource(self, datasource_id: str) -> int:
        stmt = select(func.count()).select_from(ChartConfigMySQL).where(ChartConfigMySQL.datasource_id == datasource_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0