from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Dataset:
    id: str
    name: str
    datasource_id: str
    group_id: str | None = None
    type: str = "db_table"  # db_table, custom_sql
    info: dict[str, Any] | None = None  # Stores table_name or sql_text
    description: str | None = None
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
