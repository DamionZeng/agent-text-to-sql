from dataclasses import dataclass, field
from typing import Any

@dataclass
class TableInfo:
    id: str
    name: str
    role: str
    description: str
    alias: list[Any] = field(default_factory=list)
    datasource_id: str | None = None
    is_active: bool = True

