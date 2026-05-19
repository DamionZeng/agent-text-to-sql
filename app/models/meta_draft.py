from datetime import datetime

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MetaDraftMySQL(Base):
    __tablename__ = "meta_draft"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="草稿ID"
    )
    datasource_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="关联数据源ID"
    )
    config_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="完整的MetaConfig JSON"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        comment="状态: draft, published"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
