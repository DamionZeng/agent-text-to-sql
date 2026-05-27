from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DataScreenMySQL(Base):
    __tablename__ = "data_screen"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Data Screen Name"
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description"
    )
    cover: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Cover thumbnail base64/url"
    )
    canvas_style_data: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON storing canvas absolute styling data"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="draft",
        comment="draft / published"
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


class DataScreenComponentMySQL(Base):
    __tablename__ = "data_screen_component"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        comment="UUID"
    )
    data_screen_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="Data Screen ID"
    )
    chart_config_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Linked ChartConfig ID"
    )
    type: Mapped[str] = mapped_column(
        String(64),
        default="chart",
        comment="Component Type: chart, text, image, background, etc"
    )
    component_data: Mapped[dict | list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Absolute positioning & styling: left, top, width, height, z_index..."
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Z-Index or logical sort order"
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
