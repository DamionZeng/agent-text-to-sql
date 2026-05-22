from typing import TypedDict


class MetaAgentState(TypedDict, total=False):
    datasource_id: str
    raw_schema: list[dict]
    table_classifications: dict[str, str]
    table_configs: list[dict]
    column_configs: list[dict]
    metric_configs: list[dict]
    meta_config: dict
    validation_result: dict
    sync_result: dict
    error: str | None
    retry_count: int