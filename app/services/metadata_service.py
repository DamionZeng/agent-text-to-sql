import json
import uuid
from datetime import datetime

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agents.common_nodes.llm import llm
from app.agents.metadata_agent.context import MetaAgentContext
from app.agents.metadata_agent.graph import meta_agent_draft
from app.agents.metadata_agent.state import MetaAgentState
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_draft_repository import MetaDraftRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


class MetadataService:
    def __init__(
        self,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueEsRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        meta_mysql_repository: MetaMysqlRepository,
        datasource_repository: DatasourceRepository,
        meta_draft_repository: MetaDraftRepository,
        meta_knowledge_service: MetaKnowledgeService,
    ):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.datasource_repository = datasource_repository
        self.meta_draft_repository = meta_draft_repository
        self.meta_knowledge_service = meta_knowledge_service

    # ========== 数据源管理 ==========

    async def create_datasource(self, name: str, type: str, host: str, port: int,
                                database: str, username: str, password: str):
        from app.entities.datasource import Datasource

        datasource = Datasource(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            status="inactive",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return await self.datasource_repository.create(datasource)

    async def list_datasources(self, page: int | None = None, page_size: int | None = None):
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            items = await self.datasource_repository.list_all(offset=offset, limit=page_size)
            total = await self.datasource_repository.count_all()
            return {"items": items, "total": total, "page": page, "page_size": page_size}
        return await self.datasource_repository.list_all()

    async def get_datasource(self, datasource_id: str):
        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")
        return ds

    async def update_datasource(self, datasource_id: str, updates: dict):
        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")

        field_map = ["name", "host", "port", "database", "username", "password"]
        for field in field_map:
            if field in updates and updates[field] is not None:
                setattr(ds, field, updates[field])
        ds.updated_at = datetime.now()

        return await self.datasource_repository.update(ds)

    async def delete_datasource(self, datasource_id: str):
        from app.clients.datasource import datasource_manager

        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")

        datasource_prefix = f"{ds.type}_{ds.database}_"
        table_ids, metric_ids, column_ids = await self.meta_mysql_repository.delete_all_by_datasource_id(
            datasource_id, datasource_prefix
        )

        if table_ids:
            await self.column_qdrant_repository.delete_by_table_ids(table_ids)

        if column_ids:
            await self.value_es_repository.delete_by_column_ids(column_ids)

        if metric_ids:
            await self.metric_qdrant_repository.delete_by_metric_ids(metric_ids)

        await self.meta_draft_repository.delete_by_datasource_id(datasource_id)

        datasource_manager.unregister(datasource_id)

        success = await self.datasource_repository.delete(datasource_id)
        if not success:
            raise ValueError("数据源不存在")

    async def test_connection_by_payload(self, type: str, host: str, port: int,
                                         database: str, username: str, password: str) -> tuple[bool, str]:
        from app.clients.datasource import datasource_manager, DatasourceConfigBuilder

        try:
            config = DatasourceConfigBuilder() \
                .datasource_id(f"test_{host}_{port}_{database}") \
                .db_type(type) \
                .host(host) \
                .port(port) \
                .database(database) \
                .username(username) \
                .password(password) \
                .build()

            success = await datasource_manager.test_connection_by_config(config)
            return success, "连接成功" if success else "连接失败"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    async def test_connection(self, datasource_id: str) -> tuple[bool, str]:
        from app.clients.datasource import datasource_manager

        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")

        try:
            success = await datasource_manager.test_connection(ds)
            ds.status = "active" if success else "error"
            ds.updated_at = datetime.now()
            await self.datasource_repository.update(ds)
            return success, "连接成功" if success else "连接失败"
        except Exception as e:
            ds.status = "error"
            ds.updated_at = datetime.now()
            await self.datasource_repository.update(ds)
            return False, f"连接失败: {str(e)}"

    # ========== 草稿管理 ==========

    async def get_draft(self, datasource_id: str):
        draft = await self.meta_draft_repository.get_latest_by_datasource_id(datasource_id)
        if not draft:
            raise ValueError("草稿不存在")
        return draft

    async def list_draft_versions(self, datasource_id: str, page: int | None = None, page_size: int | None = None):
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            items = await self.meta_draft_repository.list_by_datasource_id(datasource_id, offset=offset, limit=page_size)
            total = await self.meta_draft_repository.count_by_datasource_id(datasource_id)
            return {"items": items, "total": total, "page": page, "page_size": page_size}
        return await self.meta_draft_repository.list_by_datasource_id(datasource_id)

    async def get_draft_version(self, datasource_id: str, draft_id: str):
        draft = await self.meta_draft_repository.get_by_id(draft_id)
        if not draft or draft.datasource_id != datasource_id:
            raise ValueError("草稿版本不存在")
        return draft

    async def save_draft(self, datasource_id: str, config_json: dict):
        from app.entities.meta_draft import MetaDraft

        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")

        next_version = await self.meta_draft_repository.get_next_version(datasource_id)

        draft = MetaDraft(
            id=str(uuid.uuid4()),
            datasource_id=datasource_id,
            config_json=config_json,
            version=next_version,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return await self.meta_draft_repository.create(draft)

    async def rollback_draft(self, datasource_id: str, draft_id: str):
        from app.entities.meta_draft import MetaDraft

        source = await self.meta_draft_repository.get_by_id(draft_id)
        if not source or source.datasource_id != datasource_id:
            raise ValueError("草稿版本不存在")

        next_version = await self.meta_draft_repository.get_next_version(datasource_id)

        draft = MetaDraft(
            id=str(uuid.uuid4()),
            datasource_id=datasource_id,
            config_json=source.config_json,
            version=next_version,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return await self.meta_draft_repository.create(draft)

    async def delete_draft(self, datasource_id: str):
        success = await self.meta_draft_repository.delete_by_datasource_id(datasource_id)
        if not success:
            raise ValueError("草稿不存在")

    # ========== 发布同步 ==========

    async def publish_metadata(self, datasource_id: str):
        from app.clients.datasource import datasource_manager
        from app.conf.meta_config import MetaConfig

        ds = await self.datasource_repository.get_by_id(datasource_id)
        if not ds:
            raise ValueError("数据源不存在")

        draft = await self.meta_draft_repository.get_by_datasource_id(datasource_id)
        if not draft:
            raise ValueError("草稿不存在，请先保存草稿")

        config_data = draft.config_json
        if config_data is None:
            raise ValueError("草稿配置为空")

        meta_config = MetaConfig.from_dict(config_data)

        datasource_manager.register(ds)
        ds_config = datasource_manager.get_config(datasource_id)
        datasource_prefix = f"{ds_config.db_type}_{ds.database}_"

        async with datasource_manager.get_session(datasource_id) as dw_session:
            await self.meta_knowledge_service.build_from_config_with_session(
                meta_config, datasource_prefix, datasource_id, dw_session, ds_config.db_type
            )

        draft.status = "published"
        draft.updated_at = datetime.now()
        await self.meta_draft_repository.update(draft)

    # ========== AI 同步 ==========

    async def sync(self, datasource_id: str):
        from app.clients.datasource import datasource_manager

        if not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context: MetaAgentContext = {
            "llm": llm,
            "datasource_repository": self.datasource_repository,
            "meta_mysql_repository": self.meta_mysql_repository,
            "column_qdrant_repository": self.column_qdrant_repository,
            "metric_qdrant_repository": self.metric_qdrant_repository,
            "value_es_repository": self.value_es_repository
        }

        state: MetaAgentState = {
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
            async for chunk in meta_agent_draft.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"
