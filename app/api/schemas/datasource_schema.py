from pydantic import BaseModel, Field
from datetime import datetime


class DatasourceCreateSchema(BaseModel):
    name: str = Field(..., max_length=128)
    type: str = Field(..., max_length=32)
    host: str = Field(..., max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database: str = Field(..., max_length=128)
    username: str = Field(..., max_length=128)
    password: str = Field(..., max_length=255)


class DatasourceUpdateSchema(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    database: str | None = Field(default=None, max_length=128)
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=255)


class DatasourceResponseSchema(BaseModel):
    id: str
    name: str
    type: str
    host: str
    port: int
    database: str
    username: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasourceListResponseSchema(BaseModel):
    items: list[DatasourceResponseSchema]


class DatasourceTestSchema(BaseModel):
    type: str = Field(..., max_length=32)
    host: str = Field(..., max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database: str = Field(..., max_length=128)
    username: str = Field(..., max_length=128)
    password: str = Field(..., max_length=255)


class DatasourceTestResponseSchema(BaseModel):
    success: bool
    message: str
