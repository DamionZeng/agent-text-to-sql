from dataclasses import asdict

from app.entities.dashboard import Dashboard
from app.models.dashboard import DashboardMySQL


class DashboardMapper:
    @staticmethod
    def to_entity(model: DashboardMySQL) -> Dashboard:
        return Dashboard(
            id=model.id,
            name=model.name,
            description=model.description,
            datasource_id=model.datasource_id,
            theme=model.theme or "dark",
            theme_config=model.theme_config,
            layout_config=model.layout_config,
            global_filters=model.global_filters,
            refresh_enabled=model.refresh_enabled or False,
            refresh_interval=model.refresh_interval or 60,
            thumbnail=model.thumbnail,
            auto_generated=model.auto_generated or False,
            status=model.status or "draft",
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Dashboard) -> DashboardMySQL:
        return DashboardMySQL(**asdict(entity))