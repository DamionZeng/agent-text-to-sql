from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.entities.data_screen import DataScreen
from app.entities.data_screen_component import DataScreenComponent
from app.models.data_screen import DataScreenMySQL, DataScreenComponentMySQL
from app.repositories.mysql.viz.mappers.data_screen_mapper import DataScreenMapper, DataScreenComponentMapper

class DataScreenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data_screen: DataScreen) -> DataScreen:
        model = DataScreenMapper.to_model(data_screen)
        self.session.add(model)
        await self.session.commit()
        return data_screen

    async def get_by_id(self, screen_id: str) -> DataScreen | None:
        result = await self.session.get(DataScreenMySQL, screen_id)
        return DataScreenMapper.to_entity(result) if result else None

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[DataScreen]:
        stmt = select(DataScreenMySQL).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [DataScreenMapper.to_entity(r) for r in result.scalars().all()]
        
    async def create_component(self, component: DataScreenComponent) -> DataScreenComponent:
        model = DataScreenComponentMapper.to_model(component)
        self.session.add(model)
        await self.session.commit()
        return component

    async def get_components(self, screen_id: str) -> list[DataScreenComponent]:
        stmt = select(DataScreenComponentMySQL).where(DataScreenComponentMySQL.data_screen_id == screen_id).order_by(DataScreenComponentMySQL.sort_order)
        result = await self.session.execute(stmt)
        return [DataScreenComponentMapper.to_entity(r) for r in result.scalars().all()]
