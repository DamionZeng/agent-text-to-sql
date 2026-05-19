from langgraph.runtime import Runtime

from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.state import MetaAgentState
from app.core.log import logger


async def build_knowledge(state: MetaAgentState, runtime: Runtime[MetaAgentContext]) -> dict:
    """调用 MetaKnowledgeService 写入 DB + 向量库 + ES"""
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "build_knowledge", "status": "running", "message": "正在同步到知识库..."})

    meta_config = state["meta_config"]
    datasource_id = state["datasource_id"]

    try:
        from app.conf.meta_config import MetaConfig, TableConfig, ColumnConfig, MetricConfig

        tables = []
        for t in meta_config.get("tables", []):
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
        for m in meta_config.get("metrics", []):
            metrics.append(MetricConfig(
                name=m["name"],
                description=m.get("description", ""),
                relevant_columns=m.get("relevant_columns", []),
                alias=m.get("alias", [])
            ))

        config = MetaConfig(tables=tables, metrics=metrics)

        writer({"type": "progress", "step": "build_knowledge", "status": "running", "message": "写入 MySQL..."})
        
        from app.services.meta_knowledge_service import MetaKnowledgeService
        from app.clients.mysql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
        from app.clients.qdrant_client_manager import qdrant_client_manager
        from app.clients.es_client_manager import es_client_manager
        from app.clients.embedding_client_manager import embedding_client_manager
        from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
        from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
        from app.repositories.mysql.dw.dw_mysql_repository import DWMysqlRepository
        from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
        from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
        from app.repositories.es.value_es_respository import ValueEsRepository

        async with meta_mysql_client_manager.session_factory() as meta_session:
            async with dw_mysql_client_manager.session_factory() as dw_session:
                datasource_repository = DatasourceRepository(meta_session)
                datasource = await datasource_repository.get_by_id(datasource_id)
                
                if not datasource:
                    raise ValueError(f"数据源不存在: {datasource_id}")
                
                datasource_prefix = f"{datasource.type}_{datasource.database}_"
                
                meta_mysql_repository = MetaMysqlRepository(meta_session)
                dw_mysql_repository = DWMysqlRepository(dw_session)
                column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
                metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
                value_es_repository = ValueEsRepository(es_client_manager.client)
                
                service = MetaKnowledgeService(
                    meta_mysql_repository=meta_mysql_repository,
                    dw_mysql_repository=dw_mysql_repository,
                    column_qdrant_repository=column_qdrant_repository,
                    metric_qdrant_repository=metric_qdrant_repository,
                    value_es_repository=value_es_repository,
                    embedding_client=embedding_client_manager.client
                )
                
                await service.build_from_config(config, datasource_prefix, datasource_id)
                
                await meta_session.commit()

        writer({"type": "progress", "step": "build_knowledge", "status": "success", "message": "同步完成"})
        logger.info(f"build_knowledge 完成: {len(tables)} 表, {len(metrics)} 指标")
        return {
            "meta_config": meta_config,
            "sync_result": {
                "tables": len(tables),
                "columns": sum(len(t.columns) for t in tables),
                "metrics": len(metrics)
            },
            "error": None
        }
    except Exception as e:
        logger.error(f"build_knowledge 失败: {str(e)}")
        writer({"type": "progress", "step": "build_knowledge", "status": "error", "message": str(e)})
        return {"sync_result": None, "error": f"同步失败: {str(e)}"}
