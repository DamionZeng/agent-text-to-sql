from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class DashboardFilter:
    id: str
    dashboard_id: str
    name: str
    label: str
    filter_type: str
    config: dict[str, Any] = field(default_factory=dict)
    target_panels: list[str] | None = None
    sort_order: int = 0
    created_at: datetime | None = None