from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class DataScreen:
    id: str
    name: str
    description: str | None = None
    cover: str | None = None
    canvas_style_data: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None
