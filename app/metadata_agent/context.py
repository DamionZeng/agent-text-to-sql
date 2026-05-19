from typing import TypedDict

from langchain.chat_models import init_chat_model

from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.repositories.es.value_es_respository import ValueEsRepository


class MetaAgentContext(TypedDict):
    llm: init_chat_model
    datasource_repository: DatasourceRepository
    meta_mysql_repository: MetaMysqlRepository
    column_qdrant_repository: ColumnQdrantRepository
    metric_qdrant_repository: MetricQdrantRepository
    value_es_repository: ValueEsRepository
