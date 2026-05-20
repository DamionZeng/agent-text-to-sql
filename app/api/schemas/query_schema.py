from pydantic import BaseModel

class QuerySchema(BaseModel):
    query: str
    datasource_id: str | None = None
