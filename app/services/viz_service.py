import json

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.agents.viz_agent.context import VizAgentContext
from app.agents.viz_agent.graph import recommend_graph, generate_graph
from app.agents.viz_agent.state import VizAgentState
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.viz.chart_config_repository import ChartConfigRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class VizService:
    def __init__(
        self,
        meta_mysql_repository: MetaMysqlRepository,
        datasource_repository: DatasourceRepository,
        chart_config_repository: ChartConfigRepository,
        embedding_client: HuggingFaceEndpointEmbeddings,
        column_qdrant_repository: ColumnQdrantRepository,
        value_es_repository: ValueEsRepository,
        metric_qdrant_repository: MetricQdrantRepository,
    ):
        self.meta_mysql_repository = meta_mysql_repository
        self.datasource_repository = datasource_repository
        self.chart_config_repository = chart_config_repository
        self.embedding_client = embedding_client
        self.column_qdrant_repository = column_qdrant_repository
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository

    def _build_context(self) -> VizAgentContext:
        return VizAgentContext(
            meta_mysql_repository=self.meta_mysql_repository,
            datasource_repository=self.datasource_repository,
            chart_config_repository=self.chart_config_repository,
            embedding_client=self.embedding_client,
            column_qdrant_repository=self.column_qdrant_repository,
            value_es_repository=self.value_es_repository,
            metric_qdrant_repository=self.metric_qdrant_repository,
        )

    async def recommend_chart(self, datasource_id: str, sql: str, query_result: list[dict]):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = self._build_context()
        state = VizAgentState(
            datasource_id=datasource_id,
            query="",
            sql=sql,
            query_result=query_result,
        )
        try:
            async for chunk in recommend_graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"

    async def generate_charts(self, datasource_id: str, query: str):
        from app.clients.datasource import datasource_manager

        if datasource_id and not datasource_manager.is_registered(datasource_id):
            datasource = await self.datasource_repository.get_by_id(datasource_id)
            if datasource:
                datasource_manager.register(datasource)

        context = self._build_context()
        state = VizAgentState(
            datasource_id=datasource_id,
            query=query,
        )
        try:
            async for chunk in generate_graph.astream(input=state, context=context, stream_mode="custom"):
                yield f"data: {json.dumps(chunk, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False, default=str)}\n\n"

    async def get_chart_config(self, chart_id: str):
        return await self.chart_config_repository.get_by_id(chart_id)

    async def list_charts(self, datasource_id: str, offset: int = 0, limit: int = 20):
        return await self.chart_config_repository.list_by_datasource(datasource_id, offset, limit)

    async def delete_chart(self, chart_id: str) -> bool:
        return await self.chart_config_repository.delete(chart_id)