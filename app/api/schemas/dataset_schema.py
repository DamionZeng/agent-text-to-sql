from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime

class DatasetFieldBase(BaseModel):
    origin_name: str = Field(..., description="Original field name")
    name: str = Field(..., description="Alias or display name")
    data_type: str = Field(..., description="Data type (string, number, date, etc)")
    role: str = Field("dimension", description="dimension or measure")
    ext_field: int = Field(0, description="0: original, 1: calculated field")
    expression: Optional[str] = Field(None, description="Expression if calculated field")
    checked: bool = Field(True, description="Whether the field is selected")
    sort_order: int = Field(0, description="Sort order")

class DatasetFieldCreate(DatasetFieldBase):
    pass

class DatasetFieldUpdate(BaseModel):
    name: Optional[str] = None
    data_type: Optional[str] = None
    role: Optional[str] = None
    expression: Optional[str] = None
    checked: Optional[bool] = None
    sort_order: Optional[int] = None

class DatasetFieldResponse(DatasetFieldBase):
    id: str
    dataset_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DatasetBase(BaseModel):
    name: str = Field(..., description="Dataset Name")
    datasource_id: str = Field(..., description="DataSource ID")
    type: str = Field("db_table", description="db_table, custom_sql")
    info: Optional[dict] = Field(None, description="JSON storing table_name or sql_text")
    description: Optional[str] = Field(None, description="Description")
    status: str = Field("active", description="active, inactive")

class DatasetCreate(DatasetBase):
    fields: Optional[List[DatasetFieldCreate]] = None

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    info: Optional[dict] = None
    description: Optional[str] = None
    status: Optional[str] = None
    fields: Optional[List[DatasetFieldCreate]] = None # Overwrite or update fields

class DatasetResponse(DatasetBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fields: Optional[List[DatasetFieldResponse]] = None

    class Config:
        orm_mode = True
