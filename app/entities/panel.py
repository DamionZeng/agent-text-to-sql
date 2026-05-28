from dataclasses import dataclass
from datetime import datetime


@dataclass
class Panel:
    id: str
    dashboard_id: str
    chart_config_id: str | None = None
    chart_type: str | None = None
    title: str | None = None
    layout_x: int = 0
    layout_y: int = 0
    layout_w: int = 6
    layout_h: int = 4
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None