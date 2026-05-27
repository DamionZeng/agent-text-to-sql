import uuid
from app.entities.data_screen import DataScreen
from app.entities.data_screen_component import DataScreenComponent
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
