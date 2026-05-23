from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.panel import Panel
from app.models.panel import PanelMySQL
from app.repositories.mysql.viz.mappers.panel_mapper import PanelMapper


class PanelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, panel: Panel) -> Panel:
        model = PanelMapper.to_model(panel)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return PanelMapper.to_entity(model)

    async def get_by_id(self, panel_id: str) -> Panel | None:
        result = await self.session.get(PanelMySQL, panel_id)
        if result:
            return PanelMapper.to_entity(result)
        return None

    async def update(self, panel: Panel) -> Panel:
        model = PanelMapper.to_model(panel)
        merged = await self.session.merge(model)
        await self.session.commit()
        await self.session.refresh(merged)
        return PanelMapper.to_entity(merged)

    async def delete(self, panel_id: str) -> bool:
        model = await self.session.get(PanelMySQL, panel_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False

    async def list_by_dashboard(self, dashboard_id: str) -> list[Panel]:
        stmt = (
            select(PanelMySQL)
            .where(PanelMySQL.dashboard_id == dashboard_id)
            .order_by(PanelMySQL.sort_order)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [PanelMapper.to_entity(row) for row in rows]

    async def delete_by_dashboard(self, dashboard_id: str) -> None:
        stmt = delete(PanelMySQL).where(PanelMySQL.dashboard_id == dashboard_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def batch_update_layout(self, panels: list[Panel]) -> None:
        for panel in panels:
            stmt = (
                update(PanelMySQL)
                .where(PanelMySQL.id == panel.id)
                .values(
                    layout_x=panel.layout_x,
                    layout_y=panel.layout_y,
                    layout_w=panel.layout_w,
                    layout_h=panel.layout_h,
                    sort_order=panel.sort_order,
                )
            )
            await self.session.execute(stmt)
        await self.session.commit()