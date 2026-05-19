from dataclasses import dataclass
from datetime import datetime


@dataclass
class Datasource:
    id: str
    name: str
    type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    status: str
    created_at: datetime
    updated_at: datetime
