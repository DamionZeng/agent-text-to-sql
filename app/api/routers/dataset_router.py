from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_meta_session
from app.api.schemas.dataset_schema import DatasetCreate, DatasetUpdate, DatasetResponse
from app.repositories.mysql.meta.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

def get_dataset_service(session: AsyncSession = Depends(get_meta_session)):
    repo = DatasetRepository(session)
    return DatasetService(repo)

# ========== Group Endpoints (Must come before dynamic dataset paths) ==========

@router.get("/groups", response_model=list[dict])
async def list_groups(service: DatasetService = Depends(get_dataset_service)):
    return await service.list_groups()

@router.get("/counts", response_model=dict)
async def get_counts(service: DatasetService = Depends(get_dataset_service)):
    return await service.get_counts()

@router.post("/groups", response_model=dict)
async def create_group(payload: dict, service: DatasetService = Depends(get_dataset_service)):
    name = payload.get("name")
    if not name: raise HTTPException(status_code=400, detail="Name required")
    group_id = await service.create_group(name)
    return {"id": group_id}

@router.delete("/groups/{group_id}", response_model=dict)
async def delete_group(group_id: str, service: DatasetService = Depends(get_dataset_service)):
    await service.delete_group(group_id)
    return {"success": True}

# ========== Dataset Endpoints ==========

@router.post("", response_model=dict)
async def create_dataset(schema: DatasetCreate, service: DatasetService = Depends(get_dataset_service)):
    ds = await service.create_dataset(schema)
    return {"id": ds.id}

@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    group_id: str | None = Query(None),
    service: DatasetService = Depends(get_dataset_service)
):
    return await service.list_datasets(group_id=group_id)

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
