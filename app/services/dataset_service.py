import uuid
from app.entities.dataset import Dataset
from app.entities.dataset_field import DatasetField
from app.repositories.mysql.meta.dataset_repository import DatasetRepository
from app.api.schemas.dataset_schema import DatasetCreate

class DatasetService:
    def __init__(self, repository: DatasetRepository):
        self.repository = repository

    async def create_dataset(self, schema: DatasetCreate) -> Dataset:
        ds_id = str(uuid.uuid4())
        ds = Dataset(
            id=ds_id,
            name=schema.name,
            datasource_id=schema.datasource_id,
            type=schema.type,
            info=schema.info,
            description=schema.description,
            status=schema.status
        )
        await self.repository.create(ds)
        
        if schema.fields:
            for f in schema.fields:
                f_entity = DatasetField(
                    id=str(uuid.uuid4()),
                    dataset_id=ds_id,
                    origin_name=f.origin_name,
                    name=f.name,
                    data_type=f.data_type,
                    role=f.role,
                    ext_field=f.ext_field,
                    expression=f.expression,
                    checked=f.checked,
                    sort_order=f.sort_order
                )
                await self.repository.create_field(f_entity)
        return ds

    async def get_dataset(self, dataset_id: str) -> Dataset | None:
        return await self.repository.get_by_id(dataset_id)

    async def list_datasets(self) -> list[Dataset]:
        return await self.repository.list_all()
