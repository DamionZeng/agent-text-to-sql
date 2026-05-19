from typing import TypedDict, Optional


class RawColumnSchema(TypedDict):
    name: str
    type: str
    examples: list


class RawTableSchema(TypedDict):
    name: str
    columns: list[RawColumnSchema]


class TableConfigState(TypedDict):
    name: str
    role: str
    description: str


class ColumnConfigState(TypedDict):
    name: str
    type: str
    role: str
    description: str
    alias: list[str]
    sync: bool


class MetricConfigState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class MetaAgentState(TypedDict):
    datasource_id: str
    raw_schema: list[RawTableSchema]
    table_classifications: dict[str, str]
    table_configs: list[TableConfigState]
    column_configs: list[ColumnConfigState]
    metric_configs: list[MetricConfigState]
    meta_config: Optional[dict]
    validation_result: Optional[dict]
    sync_result: Optional[dict]
    error: Optional[str]
    retry_count: int
