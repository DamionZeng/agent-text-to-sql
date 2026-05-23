from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DashboardFilterMySQL(Base):
    __tablename__ = "dashboard_filter"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    dashboard_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dashboard.id", ondelete="CASCADE"),
        comment="所属大屏ID"
    )
    name: Mapped[str] = mapped_column(
        String(128),
        comment="筛选器名称"
    )
    label: Mapped[str] = mapped_column(
        String(255),
        comment="显示标签"
    )
    filter_type: Mapped[str] = mapped_column(
        String(32),
        comment="date_range / select / multi_select / input / cascader"
    )
    config: Mapped[dict | list | None] = mapped_column(
        JSON,
        comment="筛选器配置"
    )
    target_panels: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="联动目标面板ID列表"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )