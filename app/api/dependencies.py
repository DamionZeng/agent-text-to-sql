from fastapi import Depends
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository
from app.repositories.mysql.meta.meta_draft_repository import MetaDraftRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.metadata_service import MetadataService
from app.services.meta_knowledge_service import MetaKnowledgeService
from app.services.query_service import QueryService

async def get_meta_session():
    async with meta_mysql_client_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_embedding_client():
    return embedding_client_manager.client

async def get_column_qdrant_repository():
    return ColumnQdrantRepository(qdrant_client_manager.client)

async def get_value_es_repository():
    return ValueEsRepository(es_client_manager.client)

async def get_metric_qdrant_repository():
    return MetricQdrantRepository(qdrant_client_manager.client)

async def get_meta_mysql_repository(session: AsyncSession = Depends(get_meta_session)):
    return MetaMysqlRepository(session)

async def get_datasource_repository(session: AsyncSession = Depends(get_meta_session)):
    return DatasourceRepository(session)

async def get_meta_draft_repository(session: AsyncSession = Depends(get_meta_session)):
    return MetaDraftRepository(session)

async def get_meta_knowledge_service(
    session: AsyncSession = Depends(get_meta_session)
) -> MetaKnowledgeService:
    from app.clients.datasource import datasource_manager

    meta_mysql_repository = MetaMysqlRepository(session)
    return MetaKnowledgeService(
        meta_mysql_repository=meta_mysql_repository,
        dw_session=session,
        datasource_type="mysql",
        column_qdrant_repository=ColumnQdrantRepository(qdrant_client_manager.client),
        metric_qdrant_repository=MetricQdrantRepository(qdrant_client_manager.client),
        value_es_repository=ValueEsRepository(es_client_manager.client),
        embedding_client=embedding_client_manager.client
    )

async def get_query_service(
        embedding_client: HuggingFaceEndpointEmbeddings = Depends(get_embedding_client),
        column_qdrant_repository: ColumnQdrantRepository = Depends(get_column_qdrant_repository),
        value_es_repository: ValueEsRepository = Depends(get_value_es_repository),
        metric_qdrant_repository: MetricQdrantRepository = Depends(get_metric_qdrant_repository),
        meta_mysql_repository: MetaMysqlRepository = Depends(get_meta_mysql_repository),
        datasource_repository: DatasourceRepository = Depends(get_datasource_repository)
) -> QueryService:
    return QueryService(
        embedding_client=embedding_client,
        column_qdrant_repository=column_qdrant_repository,
        value_es_repository=value_es_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        meta_mysql_repository=meta_mysql_repository,
        datasource_repository=datasource_repository
    )

async def get_metadata_service(
    embedding_client: HuggingFaceEndpointEmbeddings = Depends(get_embedding_client),
    column_qdrant_repository: ColumnQdrantRepository = Depends(get_column_qdrant_repository),
    value_es_repository: ValueEsRepository = Depends(get_value_es_repository),
    metric_qdrant_repository: MetricQdrantRepository = Depends(get_metric_qdrant_repository),
    meta_mysql_repository: MetaMysqlRepository = Depends(get_meta_mysql_repository),
    datasource_repository: DatasourceRepository = Depends(get_datasource_repository),
    meta_draft_repository: MetaDraftRepository = Depends(get_meta_draft_repository),
    meta_knowledge_service: MetaKnowledgeService = Depends(get_meta_knowledge_service)
) -> MetadataService:
    return MetadataService(
        embedding_client=embedding_client,
        column_qdrant_repository=column_qdrant_repository,
        value_es_repository=value_es_repository,
        metric_qdrant_repository=metric_qdrant_repository,
        meta_mysql_repository=meta_mysql_repository,
        datasource_repository=datasource_repository,
        meta_draft_repository=meta_draft_repository,
        meta_knowledge_service=meta_knowledge_service
    )
