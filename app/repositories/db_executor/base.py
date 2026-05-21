from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ColumnMeta:
    name: str
    type: str


@dataclass
class TableMeta:
    name: str
    columns: list[ColumnMeta]


class DbQueryExecutor(ABC):
    @abstractmethod
    async def list_tables(self, session: AsyncSession, database: str) -> list[str]:
        pass

    @abstractmethod
    async def get_columns(self, session: AsyncSession, table_name: str, database: str) -> list[ColumnMeta]:
        pass

    @abstractmethod
    async def get_column_values(self, session: AsyncSession, table_name: str, column_name: str, limit: int = 10) -> list[Any]:
        pass

    @abstractmethod
    async def get_column_types(self, session: AsyncSession, table_name: str) -> dict[str, str]:
        pass

    @abstractmethod
    async def explain_sql(self, session: AsyncSession, sql: str) -> None:
        pass

    @abstractmethod
    async def get_version(self, session: AsyncSession) -> str:
        pass

    async def query(self, session: AsyncSession, sql: str) -> list[dict]:
        from sqlalchemy import text
        result = await session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]

    async def execute(self, session: AsyncSession, sql: str) -> None:
        from sqlalchemy import text
        await session.execute(text(sql))
