import uuid
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.entities.dataset import Dataset
from app.entities.dataset_field import DatasetField
from app.models.dataset import DatasetMySQL, DatasetFieldMySQL, DatasetGroupMySQL
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

    async def list_all(self, offset: int = 0, limit: int = 20, group_id: str | None = None) -> list[Dataset]:
        stmt = select(DatasetMySQL)
        if group_id:
            if group_id == 'default':
                stmt = stmt.where(DatasetMySQL.group_id == None)
            else:
                stmt = stmt.where(DatasetMySQL.group_id == group_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return [DatasetMapper.to_entity(r) for r in result.scalars().all()]

    async def update(self, dataset: Dataset) -> Dataset:
        model = await self.session.get(DatasetMySQL, dataset.id)
        if model:
            model.name = dataset.name
            model.datasource_id = dataset.datasource_id
            model.group_id = dataset.group_id
            model.type = dataset.type
            model.info = dataset.info
            model.description = dataset.description
            model.status = dataset.status
            await self.session.commit()
        return dataset

    async def delete(self, dataset_id: str) -> None:
        model = await self.session.get(DatasetMySQL, dataset_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
        
    # ========== Dataset Group ==========
    async def create_group(self, name: str) -> str:
        group_id = str(uuid.uuid4())
        model = DatasetGroupMySQL(id=group_id, name=name)
        self.session.add(model)
        await self.session.commit()
        return group_id

    async def list_groups(self) -> list[dict]:
        # Get counts per group
        count_stmt = select(DatasetMySQL.group_id, func.count(DatasetMySQL.id).label("count")).group_by(DatasetMySQL.group_id)
        count_result = await self.session.execute(count_stmt)
        counts = {r.group_id: r.count for r in count_result.all() if r.group_id is not None}

        stmt = select(DatasetGroupMySQL)
        result = await self.session.execute(stmt)
        return [{"id": r.id, "name": r.name, "count": counts.get(r.id, 0)} for r in result.scalars().all()]

    async def get_counts(self) -> dict:
        # Total count
        total_stmt = select(func.count(DatasetMySQL.id))
        total_res = await self.session.execute(total_stmt)
        total_count = total_res.scalar() or 0

        # Default count (group_id is null)
        default_stmt = select(func.count(DatasetMySQL.id)).where(DatasetMySQL.group_id == None)
        default_res = await self.session.execute(default_stmt)
        default_count = default_res.scalar() or 0

        return {
            "total": total_count,
            "default": default_count
        }

    async def delete_group(self, group_id: str) -> None:
        model = await self.session.get(DatasetGroupMySQL, group_id)
        if model:
            await self.session.delete(model)
            # Nullify group_id in datasets
            await self.session.execute(
                update(DatasetMySQL).where(DatasetMySQL.group_id == group_id).values(group_id=None)
            )
            await self.session.commit()

    # Legacy fields support (if still needed by some code)
    async def create_field(self, field: DatasetField) -> DatasetField:
        model = DatasetFieldMapper.to_model(field)
        self.session.add(model)
        await self.session.commit()
        return field

    async def get_fields(self, dataset_id: str) -> list[DatasetField]:
        stmt = select(DatasetFieldMySQL).where(DatasetFieldMySQL.dataset_id == dataset_id).order_by(DatasetFieldMySQL.sort_order)
        result = await self.session.execute(stmt)
        return [DatasetFieldMapper.to_entity(r) for r in result.scalars().all()]
