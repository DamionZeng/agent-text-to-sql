from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.models.base import Base
from app.models.datasource import DatasourceMySQL
from app.models.meta_draft import MetaDraftMySQL
from app.models.table_info import TableInfoMySQL
from app.models.column_info import ColumnInfoMySQL
from app.models.metric_info import MetricInfoMySQL
from app.models.column_metric import ColumnMetricMySQL
from app.core.log import logger
from app.clients.datasource import datasource_manager
from app.repositories.mysql.meta.datasource_repository import DatasourceRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI 应用启动前执行
    embedding_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()
    meta_mysql_client_manager.init()

    # 自动同步 meta 数据库表结构
    await _init_meta_tables()

    await _register_datasources()

    yield
    # FastAPI 应用结束前执行

    await datasource_manager.close_all()

    await qdrant_client_manager.close()
    await es_client_manager.close()
    await meta_mysql_client_manager.close()


async def _init_meta_tables():
    """自动创建 meta 数据库中所有缺失的表，并同步缺失的列"""
    async with meta_mysql_client_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_sync_missing_columns)


def _sync_missing_columns(sync_conn):
    """检测并添加模型中存在但数据库表中缺失的列"""
    inspector = inspect(sync_conn)
    for table_name, table_obj in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue
        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
        for column in table_obj.columns:
            if column.name not in existing_columns:
                col_type = column.type.compile(sync_conn.dialect)
                nullable = '' if column.nullable else ' NOT NULL'
                default = ''
                if column.server_default is not None:
                    default = f' DEFAULT {column.server_default.arg.text}'
                elif column.default is not None and column.default.is_scalar:
                    val = column.default.arg
                    if isinstance(val, str):
                        default = f" DEFAULT '{val}'"
                    elif isinstance(val, (int, float)):
                        default = f' DEFAULT {val}'
                elif column.default is not None and column.default.is_callable:
                    if hasattr(column.default, 'arg') and callable(column.default.arg):
                        fn_name = column.default.arg.__name__ if hasattr(column.default.arg, '__name__') else ''
                        if 'datetime' in fn_name.lower() or 'now' in fn_name.lower():
                            default = ' DEFAULT CURRENT_TIMESTAMP'
                comment = f" COMMENT '{column.comment}'" if column.comment else ''
                sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column.name}` {col_type}{nullable}{default}{comment}"
                sync_conn.execute(text(sql))


async def _register_datasources():
    """启动时预注册所有数据源到 datasource_manager"""
    try:
        async with meta_mysql_client_manager.session_factory() as session:
            repo = DatasourceRepository(session)
            datasources = await repo.list_all()
            for ds in datasources:
                datasource_manager.register(ds)
            logger.info(f"启动时预注册 {len(datasources)} 个数据源")
    except Exception as e:
        logger.warning(f"预注册数据源失败（可能表尚未创建）: {e}")
