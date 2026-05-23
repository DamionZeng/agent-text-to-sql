from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DashboardMySQL(Base):
    __tablename__ = "dashboard"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        comment="大屏名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    datasource_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="默认数据源ID"
    )
    theme: Mapped[str] = mapped_column(
        String(64),
        default="dark",
        comment="dark / light / custom"
    )
    theme_config: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="自定义主题配置"
    )
    layout_config: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="栅格设置"
    )
    global_filters: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="全局筛选器定义数组"
    )
    refresh_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="启用自动刷新"
    )
    refresh_interval: Mapped[int] = mapped_column(
        Integer,
        default=60,
        comment="全局刷新间隔(秒)"
    )
    thumbnail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="缩略图base64"
    )
    auto_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否AI生成"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        comment="draft / published / archived"
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