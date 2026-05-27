from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.entities.dataset import Dataset
from app.entities.dataset_field import DatasetField
from app.models.dataset import DatasetMySQL, DatasetFieldMySQL
from app.repositories.mysql.meta.mappers.dataset_mapper import DatasetMapper, DatasetFieldMapper

class DatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dataset: Dataset) -> Dataset:
        model = DatasetMapper.to_model(dataset)
        self.session.add(model)
        await self.session.commit()
        return dataset

    async def get_by_id(self, dataset_id: str) -> Dataset | None:
        result = await self.session.get(DatasetMySQL, dataset_id)
        return DatasetMapper.to_entity(result) if result else None

    async def list_all(self, offset: int = 0, limit: int = 20) -> list[Dataset]:
        stmt = select(DatasetMySQL).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [DatasetMapper.to_entity(r) for r in result.scalars().all()]
        
    async def create_field(self, field: DatasetField) -> DatasetField:
        model = DatasetFieldMapper.to_model(field)
        self.session.add(model)
        await self.session.commit()
        return field

    async def get_fields(self, dataset_id: str) -> list[DatasetField]:
        stmt = select(DatasetFieldMySQL).where(DatasetFieldMySQL.dataset_id == dataset_id).order_by(DatasetFieldMySQL.sort_order)
        result = await self.session.execute(stmt)
        return [DatasetFieldMapper.to_entity(r) for r in result.scalars().all()]
