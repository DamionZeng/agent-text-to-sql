from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.mysql.viz.chart_config_repository import ChartConfigRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class VizAgentContext(TypedDict):
    chart_config_repository: ChartConfigRepository
    meta_mysql_repository: MetaMysqlRepository
    datasource_repository: DatasourceRepository

    column_qdrant_repository: ColumnQdrantRepository
    embedding_client: HuggingFaceEndpointEmbeddings
    metric_qdrant_repository: MetricQdrantRepository
    value_es_repository: ValueEsRepository