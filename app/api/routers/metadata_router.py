import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_meta_session, get_datasource_repository, get_meta_draft_repository, get_meta_knowledge_service
from app.api.schemas.datasource_schema import (
    DatasourceCreateSchema, DatasourceUpdateSchema, DatasourceResponseSchema,
    DatasourceTestSchema, DatasourceTestResponseSchema
)
from app.api.schemas.meta_draft_schema import MetaDraftSaveSchema, MetaDraftResponseSchema
from app.entities.datasource import Datasource
from app.entities.meta_draft import MetaDraft
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_draft_repository import MetaDraftRepository
from app.services.meta_knowledge_service import MetaKnowledgeService

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
    draft = await repo.get_by_datasource_id(datasource_id)
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    return draft


@metadata_router.put("/datasources/{datasource_id}/draft", response_model=MetaDraftResponseSchema)
async def save_draft(
    datasource_id: str,
    schema: MetaDraftSaveSchema,
    draft_repo: MetaDraftRepository = Depends(get_meta_draft_repository),
    ds_repo: DatasourceRepository = Depends(get_datasource_repository)
):
    ds = await ds_repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    existing = await draft_repo.get_by_datasource_id(datasource_id)
    if existing:
        existing.config_json = schema.config_json
        existing.updated_at = datetime.now()
        return await draft_repo.update(existing)
    else:
        draft = MetaDraft(
            id=str(uuid.uuid4()),
            datasource_id=datasource_id,
            config_json=schema.config_json,
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

        # 使用动态创建的 dw 连接来替换默认的 dw_mysql_repository
        # 这里简化处理，实际应该根据 datasource 创建动态连接
        # TODO: 支持动态数据源连接
        await meta_service.build_from_config(meta_config)

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
    draft_repo: MetaDraftRepository = Depends(get_meta_draft_repository)
):
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    ds = await ds_repo.get_by_id(datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    async def event_stream():
        from app.metadata_agent.graph import meta_agent
        from app.metadata_agent.state import MetaAgentState

        initial_state: MetaAgentState = {
            "datasource_id": datasource_id,
            "raw_schema": [],
            "table_classifications": {},
            "table_configs": [],
            "column_configs": [],
            "metric_configs": [],
            "meta_config": None,
            "validation_result": None,
            "sync_result": None,
            "error": None,
            "retry_count": 0
        }

        try:
            async for event in meta_agent.astream(initial_state):
                node_name = list(event.keys())[0] if event else "unknown"
                node_state = event.get(node_name, {})

                if "error" in node_state and node_state["error"]:
                    yield f"data: {json.dumps({'type': 'error', 'step': node_name, 'message': node_state['error']})}\n\n"
                    return

                if node_name == "analyze_schema":
                    tables_count = len(node_state.get("raw_schema", []))
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': f'获取到 {tables_count} 张表'})}\n\n"
                elif node_name == "classify_tables":
                    classifications = node_state.get("table_classifications", {})
                    dim_count = sum(1 for v in classifications.values() if v == "dim")
                    fact_count = sum(1 for v in classifications.values() if v == "fact")
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': f'识别到 {dim_count} 张维度表，{fact_count} 张事实表'})}\n\n"
                elif node_name == "infer_tables":
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': '表描述生成完成'})}\n\n"
                elif node_name == "infer_columns":
                    cols_count = len(node_state.get("column_configs", []))
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': f'字段推断完成，共 {cols_count} 个字段'})}\n\n"
                elif node_name == "infer_metrics":
                    metrics_count = len(node_state.get("metric_configs", []))
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': f'指标推断完成，共 {metrics_count} 个指标'})}\n\n"
                elif node_name == "assemble_config":
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': '配置组装完成'})}\n\n"
                elif node_name == "validate_config":
                    valid = node_state.get("validation_result", {}).get("valid", False)
                    if valid:
                        yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': '配置校验通过'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': '配置校验失败，正在重试...'})}\n\n"
                elif node_name == "build_knowledge":
                    sync_result = node_state.get("sync_result", {})
                    yield f"data: {json.dumps({'type': 'progress', 'step': node_name, 'message': '知识库构建完成'})}\n\n"

            # 最终返回 meta_config
            final_state = None
            async for event in meta_agent.astream(initial_state):
                final_state = event

            # 获取最终状态
            result_state = None
            async for event in meta_agent.astream(initial_state):
                result_state = event

            # 简化：直接执行一次获取结果
            from app.metadata_agent.graph import meta_agent
            final_result = await meta_agent.ainvoke(initial_state)
            meta_config = final_result.get("meta_config")

            if meta_config:
                # 保存为草稿
                existing = await draft_repo.get_by_datasource_id(datasource_id)
                if existing:
                    existing.config_json = meta_config
                    existing.updated_at = datetime.now()
                    await draft_repo.update(existing)
                else:
                    draft = MetaDraft(
                        id=str(uuid.uuid4()),
                        datasource_id=datasource_id,
                        config_json=meta_config,
                        status="draft",
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    await draft_repo.create(draft)

                yield f"data: {json.dumps({'type': 'result', 'data': {'meta_config': meta_config}})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': '未能生成配置'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
