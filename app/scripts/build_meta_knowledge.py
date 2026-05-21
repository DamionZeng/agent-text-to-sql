import argparse
import asyncio
from pathlib import Path

from app.clients.datasource import datasource_manager, DatasourceConfigBuilder
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.repositories.es.value_es_respository import ValueEsRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def build(config_path: Path):
    meta_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_client_manager.init()
    es_client_manager.init()

    async with meta_mysql_client_manager.session_factory() as meta_session:
        meta_mysql_repository = MetaMysqlRepository(meta_session)
        column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
        metric_qdrant_repository = MetricQdrantRepository(qdrant_client_manager.client)
        value_es_repository = ValueEsRepository(es_client_manager.client)

        meta_knowledge_service = MetaKnowledgeService(
            meta_mysql_repository=meta_mysql_repository,
            dw_session=meta_session,
            datasource_type="mysql",
            column_qdrant_repository=column_qdrant_repository,
            metric_qdrant_repository=metric_qdrant_repository,
            embedding_client=embedding_client_manager.client,
            value_es_repository=value_es_repository
        )
        await meta_knowledge_service.build(config_path)

    await datasource_manager.close_all()
    await meta_mysql_client_manager.close()
    await qdrant_client_manager.close()
    await es_client_manager.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="build",
        description='Calculate volume of a cylinder',
        epilog="Text at the bottom of help"
    )
    parser.add_argument('-c', '--conf')
    args = parser.parse_args()
    config_path = args.conf
    asyncio.run(build(config_path))
