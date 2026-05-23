from dataclasses import asdict

from app.entities.panel import Panel
from app.models.panel import PanelMySQL


class PanelMapper:
    @staticmethod
    def to_entity(model: PanelMySQL) -> Panel:
        return Panel(
            id=model.id,
            dashboard_id=model.dashboard_id,
            chart_config_id=model.chart_config_id,
            title=model.title,
            layout_x=model.layout_x or 0,
            layout_y=model.layout_y or 0,
            layout_w=model.layout_w or 6,
            layout_h=model.layout_h or 4,
            sort_order=model.sort_order or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Panel) -> PanelMySQL:
        return PanelMySQL(**asdict(entity))