from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    datasource_id: str | None = None
