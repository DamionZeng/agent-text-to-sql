from dataclasses import dataclass
from datetime import datetime

@dataclass
class DatasetField:
    id: str
    dataset_id: str
    origin_name: str
    name: str
    data_type: str
    role: str = "dimension"  # dimension, measure
    ext_field: int = 0       # 0: origin, 1: calculated
    expression: str | None = None
    checked: bool = True
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
