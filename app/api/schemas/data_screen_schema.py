from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class DataScreenComponentBase(BaseModel):
    chart_config_id: Optional[str] = Field(None, description="Linked ChartConfig ID")
    type: str = Field("chart", description="Component Type: chart, text, image, background, etc")
    component_data: Optional[dict] = Field(None, description="Absolute positioning & styling")
    sort_order: int = Field(0, description="Z-Index or logical sort order")

class DataScreenComponentCreate(DataScreenComponentBase):
    pass

class DataScreenComponentUpdate(BaseModel):
    chart_config_id: Optional[str] = None
    type: Optional[str] = None
    component_data: Optional[dict] = None
    sort_order: Optional[int] = None

class DataScreenComponentResponse(DataScreenComponentBase):
    id: str
    data_screen_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DataScreenBase(BaseModel):
    name: str = Field(..., description="Data Screen Name")
    description: Optional[str] = Field(None, description="Description")
    cover: Optional[str] = Field(None, description="Cover thumbnail base64/url")
    canvas_style_data: Optional[dict] = Field(default_factory=dict, description="JSON storing canvas absolute styling data")
    status: str = Field("draft", description="draft / published")

class DataScreenCreate(DataScreenBase):
    components: Optional[List[DataScreenComponentCreate]] = None

class DataScreenUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    canvas_style_data: Optional[dict] = None
    status: Optional[str] = None
    components: Optional[List[DataScreenComponentCreate]] = None

class DataScreenResponse(DataScreenBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    components: Optional[List[DataScreenComponentResponse]] = None

    class Config:
        orm_mode = True
