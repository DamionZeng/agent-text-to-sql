from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


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


# ================ Dashboard Schemas ================

class DashboardCreateRequest(BaseModel):
    name: str = Field(..., description="大屏名称")
    description: str | None = Field(None, description="描述")
    datasource_id: str | None = Field(None, description="默认数据源ID")
    theme: str = Field("dark", description="dark / light / custom")
    theme_config: dict[str, Any] | None = Field(None, description="自定义主题配置")
    layout_config: dict[str, Any] | None = Field(None, description="栅格设置")
    refresh_enabled: bool = Field(False, description="启用自动刷新")
    refresh_interval: int = Field(60, ge=0, description="全局刷新间隔(秒)")


class DashboardUpdateRequest(BaseModel):
    name: str | None = Field(None, description="大屏名称")
    description: str | None = Field(None, description="描述")
    datasource_id: str | None = Field(None, description="默认数据源ID")
    theme: str | None = Field(None, description="dark / light / custom")
    theme_config: dict[str, Any] | None = Field(None, description="自定义主题配置")
    layout_config: dict[str, Any] | None = Field(None, description="栅格设置")
    refresh_enabled: bool | None = Field(None, description="启用自动刷新")
    refresh_interval: int | None = Field(None, ge=0, description="全局刷新间隔(秒)")
    status: str | None = Field(None, description="draft / published / archived")
    thumbnail: str | None = Field(None, description="缩略图base64")


class DashboardResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    datasource_id: str | None = None
    theme: str = "dark"
    theme_config: dict[str, Any] | None = None
    layout_config: dict[str, Any] | None = None
    global_filters: list[dict[str, Any]] | None = None
    refresh_enabled: bool = False
    refresh_interval: int = 60
    thumbnail: str | None = None
    auto_generated: bool = False
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class DashboardListResponse(BaseModel):
    total: int
    items: list[DashboardResponse]


class DashboardGenerateRequest(BaseModel):
    datasource_id: str = Field(..., description="数据源ID")
    prompt: str = Field(..., description="大屏需求描述")


# ================ Panel Schemas ================

class PanelCreateRequest(BaseModel):
    chart_config_id: str | None = Field(None, description="关联图表配置ID")
    title: str | None = Field(None, description="面板标题")
    layout_x: int = Field(0, ge=0, description="栅格x坐标")
    layout_y: int = Field(0, ge=0, description="栅格y坐标")
    layout_w: int = Field(6, ge=1, le=12, description="栅格宽度")
    layout_h: int = Field(4, ge=1, description="栅格高度")
    sort_order: int = Field(0, description="排序")


class PanelUpdateRequest(BaseModel):
    chart_config_id: str | None = Field(None, description="关联图表配置ID")
    title: str | None = Field(None, description="面板标题")
    layout_x: int | None = Field(None, ge=0, description="栅格x坐标")
    layout_y: int | None = Field(None, ge=0, description="栅格y坐标")
    layout_w: int | None = Field(None, ge=1, le=12, description="栅格宽度")
    layout_h: int | None = Field(None, ge=1, description="栅格高度")
    sort_order: int | None = Field(None, description="排序")


class PanelBatchLayoutRequest(BaseModel):
    panels: list[PanelUpdateRequest]


class PanelResponse(BaseModel):
    id: str
    dashboard_id: str
    chart_config_id: str | None = None
    title: str | None = None
    layout_x: int = 0
    layout_y: int = 0
    layout_w: int = 6
    layout_h: int = 4
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ================ DashboardFilter Schemas ================

class DashboardFilterCreateRequest(BaseModel):
    name: str = Field(..., description="筛选器名称")
    label: str = Field(..., description="显示标签")
    filter_type: str = Field(..., description="date_range / select / multi_select / input / cascader")
    config: dict[str, Any] = Field(default_factory=dict, description="筛选器配置")
    target_panels: list[str] | None = Field(None, description="联动目标面板ID列表")
    sort_order: int = Field(0, description="排序")


class DashboardFilterUpdateRequest(BaseModel):
    name: str | None = Field(None, description="筛选器名称")
    label: str | None = Field(None, description="显示标签")
    filter_type: str | None = Field(None, description="date_range / select / multi_select / input / cascader")
    config: dict[str, Any] | None = Field(None, description="筛选器配置")
    target_panels: list[str] | None = Field(None, description="联动目标面板ID列表")
    sort_order: int | None = Field(None, description="排序")


class DashboardFilterResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    label: str
    filter_type: str
    config: dict[str, Any]
    target_panels: list[str] | None = None
    sort_order: int = 0
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ================ Aggregate ================

class DashboardFullResponse(BaseModel):
    dashboard: DashboardResponse
    panels: list[PanelResponse] = []
    filters: list[DashboardFilterResponse] = []


class DashboardListRequest(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    status: str | None = Field(None, description="draft / published / archived")


class AddPanelToDashboardRequest(BaseModel):
    chart_config_id: str = Field(..., description="图表配置ID")
    title: str | None = Field(None, description="面板标题")
    layout_x: int = Field(0, ge=0, description="栅格x坐标")
    layout_y: int = Field(0, ge=0, description="栅格y坐标")
    layout_w: int = Field(6, ge=1, le=12, description="栅格宽度")
    layout_h: int = Field(4, ge=1, description="栅格高度")