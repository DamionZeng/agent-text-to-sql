from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DatasetMySQL(Base):
    __tablename__ = "dataset"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Dataset Name"
    )
    group_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Group ID"
    )
    datasource_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="DataSource ID"
    )
    type: Mapped[str] = mapped_column(
        String(32),
        default="db_table",
        comment="db_table, custom_sql"
    )
    info: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON storing table_name or sql_text"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        comment="active, inactive"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Created At"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Updated At"
    )


class DatasetGroupMySQL(Base):
    __tablename__ = "dataset_group"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Group Name"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Created At"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Updated At"
    )


class DatasetFieldMySQL(Base):
    __tablename__ = "dataset_field"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="Dataset ID"
    )
    origin_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original field name"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Alias or display name"
    )
    data_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Data type (string, number, date, etc)"
    )
    role: Mapped[str] = mapped_column(
        String(32),
        default="dimension",
        comment="dimension or measure"
    )
    ext_field: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="0: original, 1: calculated field"
    )
    expression: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Expression if calculated field"
    )
    checked: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether the field is selected"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Sort order"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Created At"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Updated At"
    )
