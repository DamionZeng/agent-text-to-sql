from dataclasses import asdict

from app.entities.chart_config import ChartConfig
from app.models.chart_config import ChartConfigMySQL


class ChartConfigMapper:
    @staticmethod
    def to_entity(model: ChartConfigMySQL) -> ChartConfig:
        return ChartConfig(
            id=model.id,
            datasource_id=model.datasource_id,
            name=model.name,
            chart_type=model.chart_type,
            sql_text=model.sql_text,
            echarts_option=model.echarts_option or {},
            auto_generated=model.auto_generated or False,
            query_params=model.query_params,
            width=model.width or 6,
            height=model.height or 400,
            refresh_interval=model.refresh_interval or 0,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: ChartConfig) -> ChartConfigMySQL:
        return ChartConfigMySQL(**asdict(entity))