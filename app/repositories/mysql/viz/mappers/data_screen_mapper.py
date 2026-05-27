from app.entities.data_screen import DataScreen
from app.entities.data_screen_component import DataScreenComponent
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
