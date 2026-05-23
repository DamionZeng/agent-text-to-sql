from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PanelMySQL(Base):
    __tablename__ = "panel"

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
    chart_config_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("chart_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联图表配置ID"
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="面板标题"
    )
    layout_x: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="栅格x坐标"
    )
    layout_y: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="栅格y坐标"
    )
    layout_w: Mapped[int] = mapped_column(
        Integer,
        default=6,
        comment="栅格宽度"
    )
    layout_h: Mapped[int] = mapped_column(
        Integer,
        default=4,
        comment="栅格高度"
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )