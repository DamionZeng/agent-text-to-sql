import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agent.llm import llm
from app.metadata_agent.context import MetaAgentContext
from app.metadata_agent.graph import meta_agent_draft
from app.metadata_agent.state import MetaAgentState
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetadataService:
    def __init__(
        self,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueEsRepository,
        metric_qdrant_repository: MetricQdrantRepository,
        meta_mysql_repository: MetaMysqlRepository,
        datasource_repository: DatasourceRepository
    ):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.datasource_repository = datasource_repository

    async def sync(self, datasource_id: str):
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