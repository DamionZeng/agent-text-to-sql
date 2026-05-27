from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_meta_session
from app.api.schemas.dataset_schema import DatasetCreate, DatasetResponse
from app.repositories.mysql.meta.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

def get_dataset_service(session: AsyncSession = Depends(get_meta_session)):
    repo = DatasetRepository(session)
    return DatasetService(repo)

@router.post("", response_model=dict)
async def create_dataset(schema: DatasetCreate, service: DatasetService = Depends(get_dataset_service)):
    ds = await service.create_dataset(schema)
    return {"id": ds.id}

@router.get("", response_model=list[DatasetResponse])
async def list_datasets(service: DatasetService = Depends(get_dataset_service)):
    return await service.list_datasets()
