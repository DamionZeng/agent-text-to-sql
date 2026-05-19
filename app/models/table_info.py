from sqlalchemy import String, Text, Boolean
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class TableInfoMySQL(Base):
    __tablename__ = "table_info"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="表编号"
    )
    name: Mapped[str | None] = mapped_column(
        String(128),
        comment="表名称"
    )
    role: Mapped[str | None] = mapped_column(
        String(32),
        comment="表类型(fact/dim)"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        comment="表描述"
    )
    alias: Mapped[dict | list | None] = mapped_column(
        JSON,
        default=list,
        comment="表别名"
    )
    datasource_id: Mapped[str | None] = mapped_column(
        "datasource_id",
        String(64),
        comment="数据源ID"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )

