import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_meta_session,
    get_meta_mysql_repository,
    get_datasource_repository,
    get_embedding_client,
    get_column_qdrant_repository,
    get_value_es_repository,
    get_metric_qdrant_repository,
)
from app.api.schemas.viz_schema import ChartRecommendRequest, ChartGenerateRequest
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.viz.chart_config_repository import ChartConfigRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.es.value_es_respository import ValueEsRepository
from app.services.viz_service import VizService

router = APIRouter(prefix="/api/viz", tags=["viz"])


async def get_chart_config_repository(session: AsyncSession = Depends(get_meta_session)):
    return ChartConfigRepository(session)


async def get_viz_service(
    meta_mysql_repository: MetaMysqlRepository = Depends(get_meta_mysql_repository),
    datasource_repository: DatasourceRepository = Depends(get_datasource_repository),
    chart_config_repository: ChartConfigRepository = Depends(get_chart_config_repository),
    embedding_client: HuggingFaceEndpointEmbeddings = Depends(get_embedding_client),
    column_qdrant_repository: ColumnQdrantRepository = Depends(get_column_qdrant_repository),
    value_es_repository: ValueEsRepository = Depends(get_value_es_repository),
    metric_qdrant_repository: MetricQdrantRepository = Depends(get_metric_qdrant_repository),
) -> VizService:
    return VizService(
        meta_mysql_repository=meta_mysql_repository,
        datasource_repository=datasource_repository,
        chart_config_repository=chart_config_repository,
        embedding_client=embedding_client,
        column_qdrant_repository=column_qdrant_repository,
        value_es_repository=value_es_repository,
        metric_qdrant_repository=metric_qdrant_repository,
    )


@router.post("/charts/recommend", summary="一键成图（基于已有SQL结果推荐图表）")
async def recommend_chart(
    body: ChartRecommendRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    return StreamingResponse(
        viz_service.recommend_chart(
            datasource_id=body.datasource_id,
            sql=body.sql,
            query_result=body.query_result,
        ),
        media_type="text/event-stream",
    )


@router.post("/charts/generate", summary="一句话生成图表（AI全链路规划、查询、生成）")
async def generate_chart(
    body: ChartGenerateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    return StreamingResponse(
        viz_service.generate_charts(
            datasource_id=body.datasource_id,
            query=body.query,
        ),
        media_type="text/event-stream",
    )


@router.get("/charts/{chart_id}", summary="获取图表配置详情")
async def get_chart(
    chart_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    chart = await viz_service.get_chart_config(chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="图表不存在")
    return chart


@router.get("/charts", summary="列出某数据源下的图表")
async def list_charts(
    datasource_id: str = Query(..., description="数据源ID"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    viz_service: VizService = Depends(get_viz_service),
):
    return await viz_service.list_charts(datasource_id, offset, limit)


@router.delete("/charts/{chart_id}", summary="删除图表配置")
async def delete_chart(
    chart_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    success = await viz_service.delete_chart(chart_id)
    if not success:
        raise HTTPException(status_code=404, detail="图表不存在")
    return {"message": "删除成功"}