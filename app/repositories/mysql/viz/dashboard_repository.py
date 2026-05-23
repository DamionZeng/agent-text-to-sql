from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.dashboard import Dashboard
from app.models.dashboard import DashboardMySQL
from app.repositories.mysql.viz.mappers.dashboard_mapper import DashboardMapper


class DashboardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dashboard: Dashboard) -> Dashboard:
        model = DashboardMapper.to_model(dashboard)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return DashboardMapper.to_entity(model)

    async def get_by_id(self, dashboard_id: str) -> Dashboard | None:
        result = await self.session.get(DashboardMySQL, dashboard_id)
        if result:
            return DashboardMapper.to_entity(result)
        return None

    async def update(self, dashboard: Dashboard) -> Dashboard:
        model = DashboardMapper.to_model(dashboard)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return DashboardMapper.to_entity(merged)

    async def delete(self, dashboard_id: str) -> bool:
        model = await self.session.get(DashboardMySQL, dashboard_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

    async def list_all(
        self, offset: int = 0, limit: int = 20, status: str | None = None
    ) -> list[Dashboard]:
        stmt = select(DashboardMySQL).order_by(DashboardMySQL.updated_at.desc()).offset(offset).limit(limit)
        if status:
            stmt = stmt.where(DashboardMySQL.status == status)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [DashboardMapper.to_entity(row) for row in rows]

    async def count_all(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(DashboardMySQL)
        if status:
            stmt = stmt.where(DashboardMySQL.status == status)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update_status(self, dashboard_id: str, status: str) -> None:
        stmt = (
            update(DashboardMySQL)
            .where(DashboardMySQL.id == dashboard_id)
            .values(status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()