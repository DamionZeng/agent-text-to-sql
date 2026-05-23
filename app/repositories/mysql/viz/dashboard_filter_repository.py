from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.dashboard_filter import DashboardFilter
from app.models.dashboard_filter import DashboardFilterMySQL
from app.repositories.mysql.viz.mappers.dashboard_filter_mapper import DashboardFilterMapper


class DashboardFilterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dashboard_filter: DashboardFilter) -> DashboardFilter:
        model = DashboardFilterMapper.to_model(dashboard_filter)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return DashboardFilterMapper.to_entity(model)

    async def get_by_id(self, filter_id: str) -> DashboardFilter | None:
        result = await self.session.get(DashboardFilterMySQL, filter_id)
        if result:
            return DashboardFilterMapper.to_entity(result)
        return None

    async def update(self, dashboard_filter: DashboardFilter) -> DashboardFilter:
        model = DashboardFilterMapper.to_model(dashboard_filter)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return DashboardFilterMapper.to_entity(merged)

    async def delete(self, filter_id: str) -> bool:
        model = await self.session.get(DashboardFilterMySQL, filter_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

    async def list_by_dashboard(self, dashboard_id: str) -> list[DashboardFilter]:
        stmt = (
            select(DashboardFilterMySQL)
            .where(DashboardFilterMySQL.dashboard_id == dashboard_id)
            .order_by(DashboardFilterMySQL.sort_order)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [DashboardFilterMapper.to_entity(row) for row in rows]

    async def delete_by_dashboard(self, dashboard_id: str) -> None:
        stmt = delete(DashboardFilterMySQL).where(DashboardFilterMySQL.dashboard_id == dashboard_id)
        await self.session.execute(stmt)
        await self.session.commit()