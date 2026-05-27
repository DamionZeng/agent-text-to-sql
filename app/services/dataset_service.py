import uuid
from app.entities.dataset import Dataset
from app.entities.dataset_field import DatasetField
from app.repositories.mysql.meta.dataset_repository import DatasetRepository
from app.api.schemas.dataset_schema import DatasetCreate, DatasetUpdate

class DatasetService:
    def __init__(self, repository: DatasetRepository):
        self.repository = repository

    async def create_dataset(self, schema: DatasetCreate) -> Dataset:
        ds_id = str(uuid.uuid4())
        ds = Dataset(
            id=ds_id,
            name=schema.name,
            datasource_id=schema.datasource_id,
            group_id=schema.group_id,
            type=schema.type,
            info=schema.info,
            description=schema.description,
            status=schema.status
        )
        await self.repository.create(ds)
        return ds

    async def update_dataset(self, dataset_id: str, schema: DatasetUpdate) -> Dataset:
        existing = await self.repository.get_by_id(dataset_id)
        if not existing:
            raise ValueError("Dataset not found")
        
        if schema.name is not None: existing.name = schema.name
        if schema.datasource_id is not None: existing.datasource_id = schema.datasource_id
        if schema.group_id is not None: existing.group_id = schema.group_id
        if schema.type is not None: existing.type = schema.type
        if schema.info is not None: existing.info = schema.info
        if schema.description is not None: existing.description = schema.description
        if schema.status is not None: existing.status = schema.status
        
        await self.repository.update(existing)
        return existing

    async def delete_dataset(self, dataset_id: str) -> None:
        await self.repository.delete(dataset_id)

    async def get_dataset(self, dataset_id: str) -> Dataset | None:
        return await self.repository.get_by_id(dataset_id)

    async def list_datasets(self, group_id: str | None = None) -> list[Dataset]:
        return await self.repository.list_all(group_id=group_id)

    # ========== Groups ==========
    async def create_group(self, name: str) -> str:
        return await self.repository.create_group(name)

    async def list_groups(self) -> list[dict]:
        return await self.repository.list_groups()

    async def delete_group(self, group_id: str) -> None:
        await self.repository.delete_group(group_id)
