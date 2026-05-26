from typing import TypedDict

from app.entities.column_info import ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str


class VizAgentState(TypedDict, total=False):

    query: str
    datasource_id: str
    keywords: list[str]

    retrieved_column_infos: list[ColumnInfo]
    retrieved_metric_infos: list[MetricInfo]
    retrieved_value_infos: list[ValueInfo]

    table_infos: list[TableInfoState]
    metric_infos: list[MetricInfoState]

    date_info: DateInfoState
    db_info: DBInfoState

    sql: str
    query_result: list[dict]

    error: str
    retry_count: int

    chart_type: str
    chart_title: str

    chart_id: str
    chart_configs: list[dict]
    chart_ids: list[str]

    dashboard_id: str
    dashboard_name: str
    dashboard_description: str
    query_results: list[list[dict]]
    layout_plan: list[dict]