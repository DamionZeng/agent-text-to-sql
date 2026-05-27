from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class DataScreenComponent:
    id: str
    data_screen_id: str
    chart_config_id: str | None = None
    type: str = "chart"  # chart, text, image, etc.
    component_data: dict[str, Any] = field(default_factory=dict) # left, top, width, height, z_index, style
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
