from dataclasses import asdict

from app.entities.dashboard_filter import DashboardFilter
from app.models.dashboard_filter import DashboardFilterMySQL


class DashboardFilterMapper:
    @staticmethod
    def to_entity(model: DashboardFilterMySQL) -> DashboardFilter:
        return DashboardFilter(
            id=model.id,
            dashboard_id=model.dashboard_id,
            name=model.name,
            label=model.label,
            filter_type=model.filter_type,
            config=model.config or {},
            target_panels=model.target_panels,
            sort_order=model.sort_order or 0,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: DashboardFilter) -> DashboardFilterMySQL:
        return DashboardFilterMySQL(**asdict(entity))