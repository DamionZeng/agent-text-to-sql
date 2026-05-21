import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_datasource_repository, get_meta_draft_repository, get_meta_knowledge_service, get_metadata_service
from app.api.schemas.datasource_schema import (
    DatasourceCreateSchema, DatasourceUpdateSchema, DatasourceResponseSchema,
    DatasourceTestSchema, DatasourceTestResponseSchema
)
from app.api.schemas.meta_draft_schema import MetaDraftSaveSchema, MetaDraftResponseSchema, MetaDraftVersionItemSchema
from app.entities.datasource import Datasource
from app.entities.meta_draft import MetaDraft
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_draft_repository import MetaDraftRepository
from app.services.meta_knowledge_service import MetaKnowledgeService
from app.services.metadata_service import MetadataService

metadata_router = APIRouter(prefix="/api/metadata", tags=["metadata"])


# ========== 数据源管理 ==========

@metadata_router.post("/datasources", response_model=DatasourceResponseSchema)
async def create_datasource(
    schema: DatasourceCreateSchema,
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    datasource = Datasource(
        id=str(uuid.uuid4()),
        name=schema.name,
        type=schema.type,
        host=schema.host,
        port=schema.port,
        database=schema.database,
        username=schema.username,
        password=schema.password,
        status="inactive",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return await repo.create(datasource)


@metadata_router.get("/datasources", response_model=list[DatasourceResponseSchema])
async def list_datasources(
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    return await repo.list_all()


@metadata_router.get("/datasources/{datasource_id}", response_model=DatasourceResponseSchema)
async def get_datasource(
    datasource_id: str,
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    ds = await repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


@metadata_router.put("/datasources/{datasource_id}", response_model=DatasourceResponseSchema)
async def update_datasource(
    datasource_id: str,
    schema: DatasourceUpdateSchema,
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    ds = await repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    if schema.name is not None:
        ds.name = schema.name
    if schema.host is not None:
        ds.host = schema.host
    if schema.port is not None:
        ds.port = schema.port
    if schema.database is not None:
        ds.database = schema.database
    if schema.username is not None:
        ds.username = schema.username
    if schema.password is not None:
        ds.password = schema.password
    ds.updated_at = datetime.now()

    return await repo.update(ds)


@metadata_router.delete("/datasources/{datasource_id}")
async def delete_datasource(
    datasource_id: str,
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    success = await repo.delete(datasource_id)
    if not success:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"message": "删除成功"}


@metadata_router.post("/datasources/test", response_model=DatasourceTestResponseSchema)
async def test_datasource_connection_by_payload(
    schema: DatasourceTestSchema
):
    """在新增数据源前测试连接（不需要 datasource_id）"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        if schema.type == "mysql":
            url = f"mysql+asyncmy://{schema.username}:{schema.password}@{schema.host}:{schema.port}/{schema.database}?charset=utf8mb4"
        elif schema.type == "postgresql":
            url = f"postgresql+asyncpg://{schema.username}:{schema.password}@{schema.host}:{schema.port}/{schema.database}"
        else:
            return {"success": False, "message": f"不支持的数据源类型: {schema.type}"}

        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}


@metadata_router.post("/datasources/{datasource_id}/test")
async def test_datasource_connection(
    datasource_id: str,
    repo: DatasourceRepository = Depends(get_datasource_repository)
):
    ds = await repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        url = f"mysql+asyncmy://{ds.username}:{ds.password}@{ds.host}:{ds.port}/{ds.database}?charset=utf8mb4"
        engine = create_async_engine(url, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()

        ds.status = "active"
        ds.updated_at = datetime.now()
        await repo.update(ds)
        return {"success": True, "message": "连接成功"}
    except Exception as e:
        ds.status = "error"
        ds.updated_at = datetime.now()
        await repo.update(ds)
        return {"success": False, "message": f"连接失败: {str(e)}"}


# ========== 元数据草稿 ==========

@metadata_router.get("/datasources/{datasource_id}/draft", response_model=MetaDraftResponseSchema)
async def get_draft(
    datasource_id: str,
    repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    draft = await repo.get_latest_by_datasource_id(datasource_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    return draft


@metadata_router.get("/datasources/{datasource_id}/draft/versions", response_model=list[MetaDraftVersionItemSchema])
async def list_draft_versions(
    datasource_id: str,
    repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    return await repo.list_by_datasource_id(datasource_id)


@metadata_router.get("/datasources/{datasource_id}/draft/versions/{draft_id}", response_model=MetaDraftResponseSchema)
async def get_draft_version(
    datasource_id: str,
    draft_id: str,
    repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    draft = await repo.get_by_id(draft_id)
    if not draft or draft.datasource_id != datasource_id:
        raise HTTPException(status_code=404, detail="草稿版本不存在")
    return draft


@metadata_router.post("/datasources/{datasource_id}/draft", response_model=MetaDraftResponseSchema)
async def save_draft(
    datasource_id: str,
    schema: MetaDraftSaveSchema,
    draft_repo: MetaDraftRepository = Depends(get_meta_draft_repository),
    ds_repo: DatasourceRepository = Depends(get_datasource_repository)
):
    ds = await ds_repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    next_version = await draft_repo.get_next_version(datasource_id)

    draft = MetaDraft(
        id=str(uuid.uuid4()),
        datasource_id=datasource_id,
        config_json=schema.config_json,
        version=next_version,
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return await draft_repo.create(draft)


@metadata_router.post("/datasources/{datasource_id}/draft/{draft_id}/rollback", response_model=MetaDraftResponseSchema)
async def rollback_draft(
    datasource_id: str,
    draft_id: str,
    draft_repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    source = await draft_repo.get_by_id(draft_id)
    if not source or source.datasource_id != datasource_id:
        raise HTTPException(status_code=404, detail="草稿版本不存在")

    next_version = await draft_repo.get_next_version(datasource_id)

    draft = MetaDraft(
        id=str(uuid.uuid4()),
        datasource_id=datasource_id,
        config_json=source.config_json,
        version=next_version,
        status="draft",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return await draft_repo.create(draft)


@metadata_router.delete("/datasources/{datasource_id}/draft")
async def delete_draft(
    datasource_id: str,
    repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    success = await repo.delete_by_datasource_id(datasource_id)
    if not success:
        raise HTTPException(status_code=404, detail="草稿不存在")
    return {"message": "删除成功"}


# ========== 发布同步 ==========

@metadata_router.post("/datasources/{datasource_id}/publish")
async def publish_metadata(
    datasource_id: str,
    draft_repo: MetaDraftRepository = Depends(get_meta_draft_repository),
    ds_repo: DatasourceRepository = Depends(get_datasource_repository),
    meta_service: MetaKnowledgeService = Depends(get_meta_knowledge_service)
):
    ds = await ds_repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    draft = await draft_repo.get_by_datasource_id(datasource_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在，请先保存草稿")

    try:
        from app.conf.meta_config import MetaConfig, TableConfig, ColumnConfig, MetricConfig

        config_data = draft.config_json
        tables = []
        if config_data.get("tables"):
            for t in config_data["tables"]:
                columns = []
                for c in t.get("columns", []):
                    columns.append(ColumnConfig(
                        name=c["name"],
                        role=c.get("role", "dimension"),
                        description=c.get("description", ""),
                        alias=c.get("alias", []),
                        sync=c.get("sync", False)
                    ))
                tables.append(TableConfig(
                    name=t["name"],
                    role=t.get("role", "dim"),
                    description=t.get("description", ""),
                    columns=columns
                ))

        metrics = []
        if config_data.get("metrics"):
            for m in config_data["metrics"]:
                metrics.append(MetricConfig(
                    name=m["name"],
                    description=m.get("description", ""),
                    relevant_columns=m.get("relevant_columns", []),
                    alias=m.get("alias", [])
                ))

        meta_config = MetaConfig(tables=tables, metrics=metrics)

        datasource_prefix = f"{ds.type}_{ds.database}_"
        await meta_service.build_from_config(meta_config, datasource_prefix, datasource_id)

        draft.status = "published"
        draft.updated_at = datetime.now()
        await draft_repo.update(draft)

        return {"message": "发布成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


# ========== AI 同步 ==========

@metadata_router.post("/datasources/{datasource_id}/sync")
async def sync_metadata(
    datasource_id: str,
    ds_repo: DatasourceRepository = Depends(get_datasource_repository),
    metadata_service: MetadataService = Depends(get_metadata_service)
):
    ds = await ds_repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    return StreamingResponse(
        metadata_service.sync(datasource_id),
        media_type="text/event-stream"
    )
