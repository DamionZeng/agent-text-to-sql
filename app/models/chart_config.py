from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChartConfigMySQL(Base):
    __tablename__ = "chart_config"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    datasource_id: Mapped[str] = mapped_column(
        String(36),
        comment="数据源ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        comment="图表名称"
    )
    chart_type: Mapped[str] = mapped_column(
        String(64),
        comment="图表类型: line/bar/pie/scatter/heatmap/radar/gauge/funnel/map/table/number_card/text"
    )
    sql_text: Mapped[str] = mapped_column(
        Text,
        comment="数据查询SQL"
    )
    echarts_option: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="ECharts完整配置"
    )
    auto_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否AI自动生成"
    )
    query_params: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="SQL模板参数定义"
    )
    width: Mapped[int] = mapped_column(
        Integer,
        default=6,
        comment="默认栅格宽度(1-12)"
    )
    height: Mapped[int] = mapped_column(
        Integer,
        default=400,
        comment="默认像素高度"
    )
    refresh_interval: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="自动刷新间隔(秒)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )