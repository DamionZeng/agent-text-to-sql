from datetime import datetime

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DatasourceMySQL(Base):
    __tablename__ = "datasource"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="数据源ID"
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="数据源名称"
    )
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="数据源类型: mysql, postgresql, clickhouse..."
    )
    host: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="主机地址"
    )
    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="端口"
    )
    database: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="数据库名"
    )
    username: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="用户名"
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码(AES加密)"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="inactive",
        comment="状态: active, inactive, error"
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
