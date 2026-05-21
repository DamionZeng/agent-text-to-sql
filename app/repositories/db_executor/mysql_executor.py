from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.db_executor.base import DbQueryExecutor, ColumnMeta


class MySQLQueryExecutor(DbQueryExecutor):
    async def list_tables(self, session: AsyncSession, database: str) -> list[str]:
        result = await session.execute(text("SHOW TABLES"))
        return [row[0] for row in result.fetchall()]

    async def get_columns(self, session: AsyncSession, table_name: str, database: str) -> list[ColumnMeta]:
        result = await session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
        return [ColumnMeta(name=row[0], type=row[1]) for row in result.fetchall()]

    async def get_column_values(self, session: AsyncSession, table_name: str, column_name: str, limit: int = 10) -> list[Any]:
        result = await session.execute(
            text(f"SELECT DISTINCT `{column_name}` FROM {table_name} LIMIT {limit}")
        )
        return [row[0] for row in result.fetchall()]

    async def get_column_types(self, session: AsyncSession, table_name: str) -> dict[str, str]:
        result = await session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
        return {row['Field']: row['Type'] for row in result.mappings().fetchall()}

    async def explain_sql(self, session: AsyncSession, sql: str) -> None:
        await session.execute(text(f"EXPLAIN {sql}"))

    async def get_version(self, session: AsyncSession) -> str:
        result = await session.execute(text("SELECT version()"))
        return result.scalar()
