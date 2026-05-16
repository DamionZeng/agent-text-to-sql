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

class DataAgentState(TypedDict):

    query: str                                               # 用户查询输入
    keywords: list[str]                                      # 抽取关键词后返回的关键词列表

    retrieved_column_infos: list[ColumnInfo]                 # recall_column 返回的信息
    retrieved_metric_infos: list[MetricInfo]                 # recall_metric 返回的信息
    retrieved_value_infos: list[ValueInfo]                   # recall_value 返回信息

    table_infos: list[TableInfoState]
    metric_infos: list[MetricInfoState]

    date_info: DateInfoState
    db_info: DBInfoState

    sql: str

    error: str                                               # 校验sql时出现的错误信息
    retry_count: int                                         # sql校正次数
