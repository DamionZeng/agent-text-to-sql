from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_meta_session
from app.api.schemas.dataset_schema import DatasetCreate, DatasetUpdate, DatasetResponse
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

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, service: DatasetService = Depends(get_dataset_service)):
    ds = await service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds

@router.put("/{dataset_id}", response_model=dict)
async def update_dataset(dataset_id: str, schema: DatasetUpdate, service: DatasetService = Depends(get_dataset_service)):
    try:
        await service.update_dataset(dataset_id, schema)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{dataset_id}", response_model=dict)
async def delete_dataset(dataset_id: str, service: DatasetService = Depends(get_dataset_service)):
    await service.delete_dataset(dataset_id)
    return {"success": True}
