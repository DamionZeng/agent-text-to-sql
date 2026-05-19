from dataclasses import dataclass
from datetime import datetime


@dataclass
class MetaDraft:
    id: str
    datasource_id: str
    config_json: dict
    status: str
    created_at: datetime
    updated_at: datetime
