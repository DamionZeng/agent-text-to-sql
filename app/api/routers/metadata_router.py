from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_metadata_service
from app.api.schemas.datasource_schema import (
    DatasourceCreateSchema, DatasourceUpdateSchema, DatasourceResponseSchema,
    DatasourceTestSchema, DatasourceTestResponseSchema
)
from app.api.schemas.meta_draft_schema import MetaDraftSaveSchema, MetaDraftResponseSchema, MetaDraftVersionItemSchema
from app.services.metadata_service import MetadataService

metadata_router = APIRouter(prefix="/api/metadata", tags=["metadata"])


# ========== 数据源管理 ==========

@metadata_router.post("/datasources", response_model=DatasourceResponseSchema)
async def create_datasource(
    schema: DatasourceCreateSchema,
    service: MetadataService = Depends(get_metadata_service)
):
    return await service.create_datasource(
        name=schema.name, type=schema.type, host=schema.host,
        port=schema.port, database=schema.database,
        username=schema.username, password=schema.password
    )


@metadata_router.get("/datasources", response_model=list[DatasourceResponseSchema])
async def list_datasources(
    service: MetadataService = Depends(get_metadata_service)
):
    return await service.list_datasources()


@metadata_router.get("/datasources/{datasource_id}", response_model=DatasourceResponseSchema)
async def get_datasource(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.get_datasource(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.put("/datasources/{datasource_id}", response_model=DatasourceResponseSchema)
async def update_datasource(
    datasource_id: str,
    schema: DatasourceUpdateSchema,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.update_datasource(datasource_id, schema.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.delete("/datasources/{datasource_id}")
async def delete_datasource(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        await service.delete_datasource(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "删除成功"}


@metadata_router.post("/datasources/test", response_model=DatasourceTestResponseSchema)
async def test_datasource_connection_by_payload(
    schema: DatasourceTestSchema,
    service: MetadataService = Depends(get_metadata_service)
):
    success, message = await service.test_connection_by_payload(
        type=schema.type, host=schema.host, port=schema.port,
        database=schema.database, username=schema.username, password=schema.password
    )
    return {"success": success, "message": message}


@metadata_router.post("/datasources/{datasource_id}/test")
async def test_datasource_connection(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        success, message = await service.test_connection(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": success, "message": message}


# ========== 元数据草稿 ==========

@metadata_router.get("/datasources/{datasource_id}/draft", response_model=MetaDraftResponseSchema)
async def get_draft(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.get_draft(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.get("/datasources/{datasource_id}/draft/versions", response_model=list[MetaDraftVersionItemSchema])
async def list_draft_versions(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    return await service.list_draft_versions(datasource_id)


@metadata_router.get("/datasources/{datasource_id}/draft/versions/{draft_id}", response_model=MetaDraftResponseSchema)
async def get_draft_version(
    datasource_id: str,
    draft_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.get_draft_version(datasource_id, draft_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.post("/datasources/{datasource_id}/draft", response_model=MetaDraftResponseSchema)
async def save_draft(
    datasource_id: str,
    schema: MetaDraftSaveSchema,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.save_draft(datasource_id, schema.config_json)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.post("/datasources/{datasource_id}/draft/{draft_id}/rollback", response_model=MetaDraftResponseSchema)
async def rollback_draft(
    datasource_id: str,
    draft_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        return await service.rollback_draft(datasource_id, draft_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@metadata_router.delete("/datasources/{datasource_id}/draft")
async def delete_draft(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        await service.delete_draft(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "删除成功"}


# ========== 发布同步 ==========

@metadata_router.post("/datasources/{datasource_id}/publish")
async def publish_metadata(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        await service.publish_metadata(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")
    return {"message": "发布成功"}


@metadata_router.post("/datasources/{datasource_id}/sync")
async def sync_metadata(
    datasource_id: str,
    service: MetadataService = Depends(get_metadata_service)
):
    try:
        await service.get_datasource(datasource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        service.sync(datasource_id),
        media_type="text/event-stream"
    )
