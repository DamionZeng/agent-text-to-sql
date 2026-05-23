from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class Dashboard:
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