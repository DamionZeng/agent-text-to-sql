import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agents.chat_agent.context import DataAgentContext
from app.agents.chat_agent.graph import graph
from app.agents.chat_agent.state import DataAgentState
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository

class QueryService:
    def __init__(self,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 column_qdrant_repository: ColumnQdrantRepository,
                 value_es_repository: ValueEsRepository,
                 metric_qdrant_repository: MetricQdrantRepository,
                 meta_mysql_repository: MetaMysqlRepository,
                 datasource_repository: DatasourceRepository):
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository
        self.meta_mysql_repository = meta_mysql_repository
        self.datasource_repository = datasource_repository

    async def query(self, query: str, datasource_id: str | None = None):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = DataAgentContext(
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
            meta_mysql_repository=self.meta_mysql_repository,
            datasource_repository=self.datasource_repository
        )
        state = DataAgentState(query=query, datasource_id=datasource_id or "")
        try:
            async for chunk in graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"
