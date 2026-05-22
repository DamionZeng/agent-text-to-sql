from typing import TypedDict

from app.entities.chart_config import ChartConfig


class VizAgentState(TypedDict, total=False):
    query: str
    datasource_id: str
    sql: str
    query_result: list[dict]

    chart_type: str
    chart_title: str

    chart_plans: list[dict]
    chart_id: str
    chart_configs: list[dict]
    chart_ids: list[str]