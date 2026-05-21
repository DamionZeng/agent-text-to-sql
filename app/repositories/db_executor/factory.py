from app.repositories.db_executor.base import DbQueryExecutor
from app.repositories.db_executor.mysql_executor import MySQLQueryExecutor
from app.repositories.db_executor.postgresql_executor import PostgreSQLQueryExecutor

_EXECUTOR_REGISTRY: dict[str, DbQueryExecutor] = {
    "mysql": MySQLQueryExecutor(),
    "postgresql": PostgreSQLQueryExecutor(),
}


def get_executor(db_type: str) -> DbQueryExecutor:
    executor = _EXECUTOR_REGISTRY.get(db_type)
    if not executor:
        raise ValueError(f"不支持的数据源类型: {db_type}，已注册类型: {list(_EXECUTOR_REGISTRY.keys())}")
    return executor


def register_executor(db_type: str, executor: DbQueryExecutor):
    _EXECUTOR_REGISTRY[db_type] = executor
