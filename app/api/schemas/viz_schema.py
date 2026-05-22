from pydantic import BaseModel, Field
from typing import Any


class ChartRecommendRequest(BaseModel):
    datasource_id: str = Field(..., description="数据源ID")
    sql: str = Field(..., description="SQL语句")
    query_result: list[dict[str, Any]] = Field(..., description="SQL查询结果")


class ChartGenerateRequest(BaseModel):
    datasource_id: str = Field(..., description="数据源ID")
    query: str = Field(..., description="用户自然语言描述")


class ChartConfigResponse(BaseModel):
    id: str
    datasource_id: str
    name: str
    chart_type: str
    sql_text: str
    echarts_option: dict[str, Any]
    auto_generated: bool
    width: int
    height: int
    refresh_interval: int