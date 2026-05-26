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
from app.api.schemas.viz_schema import (
    ChartRecommendRequest,
    ChartGenerateRequest,
    DashboardCreateRequest,
    DashboardUpdateRequest,
    DashboardGenerateRequest,
    DashboardListRequest,
    PanelCreateRequest,
    PanelUpdateRequest,
    PanelBatchLayoutRequest,
    DashboardFilterCreateRequest,
    DashboardFilterUpdateRequest,
    AddPanelToDashboardRequest,
)
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.viz.chart_config_repository import ChartConfigRepository
from app.repositories.mysql.viz.dashboard_repository import DashboardRepository
from app.repositories.mysql.viz.panel_repository import PanelRepository
from app.repositories.mysql.viz.dashboard_filter_repository import DashboardFilterRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.es.value_es_respository import ValueEsRepository
from app.services.viz_service import VizService

router = APIRouter(prefix="/api/viz", tags=["viz"])


async def get_chart_config_repository(session: AsyncSession = Depends(get_meta_session)):
    return ChartConfigRepository(session)


async def get_dashboard_repository(session: AsyncSession = Depends(get_meta_session)):
    return DashboardRepository(session)


async def get_panel_repository(session: AsyncSession = Depends(get_meta_session)):
    return PanelRepository(session)


async def get_dashboard_filter_repository(session: AsyncSession = Depends(get_meta_session)):
    return DashboardFilterRepository(session)


async def get_viz_service(
    meta_mysql_repository: MetaMysqlRepository = Depends(get_meta_mysql_repository),
    datasource_repository: DatasourceRepository = Depends(get_datasource_repository),
    chart_config_repository: ChartConfigRepository = Depends(get_chart_config_repository),
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
    panel_repository: PanelRepository = Depends(get_panel_repository),
    dashboard_filter_repository: DashboardFilterRepository = Depends(get_dashboard_filter_repository),
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
        dashboard_repository=dashboard_repository,
        panel_repository=panel_repository,
        dashboard_filter_repository=dashboard_filter_repository,
    )


# ================ Chart APIs ================

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


@router.put("/charts/{chart_id}", summary="更新图表配置")
async def update_chart(
    chart_id: str,
    body: dict,
    viz_service: VizService = Depends(get_viz_service),
):
    chart = await viz_service.update_chart_config(chart_id, body)
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


# ================ Dashboard APIs ================

@router.post("/dashboards", summary="创建大屏")
async def create_dashboard(
    body: DashboardCreateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.create_dashboard(body.model_dump(exclude_none=True))
    return result


@router.post("/dashboards/generate", summary="AI一句话生成大屏（SSE流式）")
async def generate_dashboard(
    body: DashboardGenerateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    return StreamingResponse(
        viz_service.generate_dashboard(
            datasource_id=body.datasource_id,
            query=body.prompt,
        ),
        media_type="text/event-stream",
    )


@router.get("/dashboards", summary="大屏列表")
async def list_dashboards(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="draft / published / archived"),
    viz_service: VizService = Depends(get_viz_service),
):
    return await viz_service.list_dashboards(offset, limit, status)


@router.get("/dashboards/{dashboard_id}", summary="获取大屏完整配置（含所有panel和filters）")
async def get_dashboard(
    dashboard_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.get_dashboard(dashboard_id)
    if not result:
        raise HTTPException(status_code=404, detail="大屏不存在")
    return result


@router.put("/dashboards/{dashboard_id}", summary="更新大屏基本信息")
async def update_dashboard(
    dashboard_id: str,
    body: DashboardUpdateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.update_dashboard(dashboard_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="大屏不存在")
    return result


@router.delete("/dashboards/{dashboard_id}", summary="删除大屏（级联删除panel和filter）")
async def delete_dashboard(
    dashboard_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    success = await viz_service.delete_dashboard(dashboard_id)
    if not success:
        raise HTTPException(status_code=404, detail="大屏不存在")
    return {"message": "删除成功"}


# ================ Panel APIs ================

@router.post("/dashboards/{dashboard_id}/panels", summary="向大屏添加面板")
async def add_panel(
    dashboard_id: str,
    body: PanelCreateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.add_panel(dashboard_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail="大屏或图表不存在")
    return result


@router.put("/dashboards/{dashboard_id}/panels/{panel_id}", summary="更新面板（布局/配置）")
async def update_panel(
    dashboard_id: str,
    panel_id: str,
    body: PanelUpdateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.update_panel(panel_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="面板不存在")
    return result


@router.delete("/dashboards/{dashboard_id}/panels/{panel_id}", summary="删除面板")
async def delete_panel(
    dashboard_id: str,
    panel_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    success = await viz_service.delete_panel(panel_id)
    if not success:
        raise HTTPException(status_code=404, detail="面板不存在")
    return {"message": "删除成功"}


@router.put("/dashboards/{dashboard_id}/panels/reorder", summary="批量更新面板排序和布局")
async def batch_reorder_panels(
    dashboard_id: str,
    body: PanelBatchLayoutRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    await viz_service.batch_reorder_panels([p.model_dump(exclude_none=True) for p in body.panels])
    return {"message": "更新成功"}


# ================ DashboardFilter APIs ================

@router.get("/dashboards/{dashboard_id}/filters", summary="获取大屏全局筛选器列表")
async def get_filters(
    dashboard_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    return await viz_service.get_filters(dashboard_id)


@router.post("/dashboards/{dashboard_id}/filters", summary="添加全局筛选器")
async def add_filter(
    dashboard_id: str,
    body: DashboardFilterCreateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.add_filter(dashboard_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail="大屏不存在")
    return result


@router.put("/dashboards/{dashboard_id}/filters/{filter_id}", summary="更新筛选器")
async def update_filter(
    dashboard_id: str,
    filter_id: str,
    body: DashboardFilterUpdateRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.update_filter(filter_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="筛选器不存在")
    return result


@router.delete("/dashboards/{dashboard_id}/filters/{filter_id}", summary="删除筛选器")
async def delete_filter(
    dashboard_id: str,
    filter_id: str,
    viz_service: VizService = Depends(get_viz_service),
):
    success = await viz_service.delete_filter(filter_id)
    if not success:
        raise HTTPException(status_code=404, detail="筛选器不存在")
    return {"message": "删除成功"}


# ================ Bridge APIs ================

@router.post("/dashboards/{dashboard_id}/panels/add-chart", summary="将图表加入大屏（桥接功能）")
async def add_chart_to_dashboard(
    dashboard_id: str,
    body: AddPanelToDashboardRequest,
    viz_service: VizService = Depends(get_viz_service),
):
    result = await viz_service.add_panel(dashboard_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=404, detail="大屏或图表不存在")
    return result