from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_meta_session
from app.api.schemas.data_screen_schema import DataScreenCreate, DataScreenResponse
from app.repositories.mysql.viz.data_screen_repository import DataScreenRepository
from app.services.data_screen_service import DataScreenService

router = APIRouter(prefix="/api/viz/data-screens", tags=["Data Screens"])

def get_screen_service(session: AsyncSession = Depends(get_meta_session)):
    repo = DataScreenRepository(session)
    return DataScreenService(repo)

@router.post("", response_model=dict)
async def create_screen(schema: DataScreenCreate, service: DataScreenService = Depends(get_screen_service)):
    screen = await service.create_screen(schema)
    return {"id": screen.id}

@router.get("", response_model=list[DataScreenResponse])
async def list_screens(service: DataScreenService = Depends(get_screen_service)):
    return await service.list_screens()
