import asyncio

from sqlalchemy import text

from app.conf.app_config import DatabaseSettings, conf
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker


class MySQLClientManager:

    def __init__(self, config: DatabaseSettings):
        self.engine: AsyncEngine = None
        self.config = config
        self.session_factory = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init(self):
        self.engine = create_async_engine(self._get_url(), pool_size=10, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=True)

    async def close(self):
        await self.engine.dispose()


meta_mysql_client_manager = MySQLClientManager(conf.db_meta)
dw_mysql_client_manager = MySQLClientManager(conf.db_dw)

if __name__ == '__main__':
    # Test
    dw_mysql_client_manager.init()
    engine = dw_mysql_client_manager.engine

    async def test():
        async with dw_mysql_client_manager.session_factory() as session:
            sql = "select * from dw.fact_order limit 10"
            result = await session.execute(text(sql))
            rows = result.mappings().fetchall()
            print(rows[0])
    asyncio.run(test())

