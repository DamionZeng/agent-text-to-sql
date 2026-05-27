import os

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write(path, content):
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

# 1. Mappers
dataset_mapper = """
from app.entities.dataset import Dataset, DatasetField
from app.models.dataset import DatasetMySQL, DatasetFieldMySQL

class DatasetMapper:
    @staticmethod
    def to_model(entity: Dataset) -> DatasetMySQL:
        return DatasetMySQL(
            id=entity.id,
            name=entity.name,
            datasource_id=entity.datasource_id,
            type=entity.type,
            info=entity.info,
            description=entity.description,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DatasetMySQL) -> Dataset:
        return Dataset(
            id=model.id,
            name=model.name,
            datasource_id=model.datasource_id,
            type=model.type,
            info=model.info,
            description=model.description,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

class DatasetFieldMapper:
    @staticmethod
    def to_model(entity: DatasetField) -> DatasetFieldMySQL:
        return DatasetFieldMySQL(
            id=entity.id,
            dataset_id=entity.dataset_id,
            origin_name=entity.origin_name,
            name=entity.name,
            data_type=entity.data_type,
            role=entity.role,
            ext_field=entity.ext_field,
            expression=entity.expression,
            checked=entity.checked,
            sort_order=entity.sort_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DatasetFieldMySQL) -> DatasetField:
        return DatasetField(
            id=model.id,
            dataset_id=model.dataset_id,
            origin_name=model.origin_name,
            name=model.name,
            data_type=model.data_type,
            role=model.role,
            ext_field=model.ext_field,
            expression=model.expression,
            checked=model.checked,
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
"""
write("app/repositories/mysql/meta/mappers/dataset_mapper.py", dataset_mapper)

data_screen_mapper = """
from app.entities.data_screen import DataScreen, DataScreenComponent
from app.models.data_screen import DataScreenMySQL, DataScreenComponentMySQL

class DataScreenMapper:
    @staticmethod
    def to_model(entity: DataScreen) -> DataScreenMySQL:
        return DataScreenMySQL(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            cover=entity.cover,
            canvas_style_data=entity.canvas_style_data,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DataScreenMySQL) -> DataScreen:
        return DataScreen(
            id=model.id,
            name=model.name,
            description=model.description,
            cover=model.cover,
            canvas_style_data=model.canvas_style_data,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

class DataScreenComponentMapper:
    @staticmethod
    def to_model(entity: DataScreenComponent) -> DataScreenComponentMySQL:
        return DataScreenComponentMySQL(
            id=entity.id,
            data_screen_id=entity.data_screen_id,
            chart_config_id=entity.chart_config_id,
            type=entity.type,
            component_data=entity.component_data,
            sort_order=entity.sort_order,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_entity(model: DataScreenComponentMySQL) -> DataScreenComponent:
        return DataScreenComponent(
            id=model.id,
            data_screen_id=model.data_screen_id,
            chart_config_id=model.chart_config_id,
            type=model.type,
            component_data=model.component_data,
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
"""
write("app/repositories/mysql/viz/mappers/data_screen_mapper.py", data_screen_mapper)

# 2. Repositories
dataset_repo = """
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.entities.dataset import Dataset, DatasetField
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
"""
write("app/repositories/mysql/meta/dataset_repository.py", dataset_repo)

data_screen_repo = """
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.entities.data_screen import DataScreen, DataScreenComponent
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
"""
write("app/repositories/mysql/viz/data_screen_repository.py", data_screen_repo)

# 3. Services (Simplified)
dataset_service = """
import uuid
from app.entities.dataset import Dataset, DatasetField
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
"""
write("app/services/dataset_service.py", dataset_service)

data_screen_service = """
import uuid
from app.entities.data_screen import DataScreen, DataScreenComponent
from app.repositories.mysql.viz.data_screen_repository import DataScreenRepository
from app.api.schemas.data_screen_schema import DataScreenCreate

class DataScreenService:
    def __init__(self, repository: DataScreenRepository):
        self.repository = repository

    async def create_screen(self, schema: DataScreenCreate) -> DataScreen:
        screen_id = str(uuid.uuid4())
        screen = DataScreen(
            id=screen_id,
            name=schema.name,
            description=schema.description,
            cover=schema.cover,
            canvas_style_data=schema.canvas_style_data,
            status=schema.status
        )
        await self.repository.create(screen)
        
        if schema.components:
            for c in schema.components:
                c_entity = DataScreenComponent(
                    id=str(uuid.uuid4()),
                    data_screen_id=screen_id,
                    chart_config_id=c.chart_config_id,
                    type=c.type,
                    component_data=c.component_data,
                    sort_order=c.sort_order
                )
                await self.repository.create_component(c_entity)
        return screen

    async def get_screen(self, screen_id: str) -> DataScreen | None:
        return await self.repository.get_by_id(screen_id)

    async def list_screens(self) -> list[DataScreen]:
        return await self.repository.list_all()
"""
write("app/services/data_screen_service.py", data_screen_service)

# 4. Routers
dataset_router = """
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.api.schemas.dataset_schema import DatasetCreate, DatasetResponse
from app.repositories.mysql.meta.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])

def get_dataset_service(session: AsyncSession = Depends(get_db)):
    repo = DatasetRepository(session)
    return DatasetService(repo)

@router.post("", response_model=dict)
async def create_dataset(schema: DatasetCreate, service: DatasetService = Depends(get_dataset_service)):
    ds = await service.create_dataset(schema)
    return {"id": ds.id}

@router.get("", response_model=list[DatasetResponse])
async def list_datasets(service: DatasetService = Depends(get_dataset_service)):
    return await service.list_datasets()
"""
write("app/api/routers/dataset_router.py", dataset_router)

data_screen_router = """
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.api.schemas.data_screen_schema import DataScreenCreate, DataScreenResponse
from app.repositories.mysql.viz.data_screen_repository import DataScreenRepository
from app.services.data_screen_service import DataScreenService

router = APIRouter(prefix="/data-screens", tags=["Data Screens"])

def get_screen_service(session: AsyncSession = Depends(get_db)):
    repo = DataScreenRepository(session)
    return DataScreenService(repo)

@router.post("", response_model=dict)
async def create_screen(schema: DataScreenCreate, service: DataScreenService = Depends(get_screen_service)):
    screen = await service.create_screen(schema)
    return {"id": screen.id}

@router.get("", response_model=list[DataScreenResponse])
async def list_screens(service: DataScreenService = Depends(get_screen_service)):
    return await service.list_screens()
"""
write("app/api/routers/data_screen_router.py", data_screen_router)
print("Boilerplate generated successfully.")
