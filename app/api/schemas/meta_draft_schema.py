from pydantic import BaseModel
from datetime import datetime


class MetaDraftSaveSchema(BaseModel):
    config_json: dict


class MetaDraftResponseSchema(BaseModel):
    id: str
    datasource_id: str
    config_json: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
