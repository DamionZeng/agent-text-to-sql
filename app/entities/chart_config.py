from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class ChartConfig:
    id: str
    datasource_id: str
    name: str
    chart_type: str
    sql_text: str
    echarts_option: dict[str, Any] = field(default_factory=dict)
    auto_generated: bool = False
    query_params: dict[str, Any] | None = None
    dataset_id: str | None = None
    width: int = 6
    height: int = 400
    refresh_interval: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None