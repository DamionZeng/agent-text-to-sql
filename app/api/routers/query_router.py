from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QueryRequest
from app.services.query_service import QueryService

query_router = APIRouter(prefix="/api/query", tags=["query"])


@query_router.post("")
async def query(
        request: QueryRequest,
        query_service: QueryService = Depends(get_query_service),
):
    return StreamingResponse(
        query_service.query(request.query, request.datasource_id),
        media_type="text/event-stream",
    )
