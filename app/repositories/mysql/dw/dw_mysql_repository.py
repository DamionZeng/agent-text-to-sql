from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import DBInfoState


class DWMysqlRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def read(self):
        pass

    def write(self):
        pass

    async def get_column_type(self, table_name) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        result_dict = result.mappings().fetchall()
        return {row['Field']: row['Type'] for row in result_dict}

    async def get_column_value(self, table_name, column_name, limit=10):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    async def get_db_info(self) -> DBInfoState:
        sql = "select version()"
        result = await self.session.execute(text(sql))
        version = result.scalar()
        return DBInfoState(dialect="mysql", version=version)

    async def validate_sql(self, sql: str):
        sql = f"EXPLAIN {sql}"
        await self.session.execute(text(sql))

    async def run_sql(self, sql: str) -> list[dict]:
        result = await self.session.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]

