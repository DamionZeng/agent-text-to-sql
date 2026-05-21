from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.datasource.builder import DatasourceConfigBuilder
from app.clients.datasource.config import DatasourceConfig
from app.clients.datasource.factory import get_factory
from app.entities.datasource import Datasource
from app.core.log import logger


class DatasourceManager:
    _instance: "DatasourceManager | None" = None

    def __new__(cls) -> "DatasourceManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines: dict[str, "tuple"] = {}
            cls._instance._configs: dict[str, DatasourceConfig] = {}
        return cls._instance

    def register(self, datasource: Datasource):
        config = DatasourceConfigBuilder().from_entity(datasource).build()
        self._configs[config.cache_key] = config

    def register_config(self, config: DatasourceConfig):
        self._configs[config.cache_key] = config

    def unregister(self, datasource_id: str):
        self._configs.pop(datasource_id, None)
        self._dispose_engine(datasource_id)

    def _get_or_create_engine(self, datasource_id: str):
        if datasource_id in self._engines:
            return self._engines[datasource_id]

        config = self._configs.get(datasource_id)
        if not config:
            raise ValueError(f"数据源未注册: {datasource_id}")

        factory = get_factory(config.db_type)
        engine = factory.create_engine(config)
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=True)
        self._engines[datasource_id] = (engine, session_factory)
        logger.info(f"数据源引擎已创建: {datasource_id} ({config.db_type})")
        return self._engines[datasource_id]

    def _dispose_engine(self, datasource_id: str):
        entry = self._engines.pop(datasource_id, None)
        if entry:
            engine, _ = entry
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(engine.dispose())
                else:
                    loop.run_until_complete(engine.dispose())
            except Exception:
                pass
            logger.info(f"数据源引擎已销毁: {datasource_id}")

    @asynccontextmanager
    async def get_session(self, datasource_id: str):
        _, session_factory = self._get_or_create_engine(datasource_id)
        async with session_factory() as session:
            yield session

    async def get_session_factory(self, datasource_id: str):
        _, session_factory = self._get_or_create_engine(datasource_id)
        return session_factory

    async def test_connection(self, datasource: Datasource) -> bool:
        config = DatasourceConfigBuilder().from_entity(datasource).build()
        factory = get_factory(config.db_type)
        engine = factory.create_engine(config)
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        finally:
            await engine.dispose()

    async def test_connection_by_config(self, config: DatasourceConfig) -> bool:
        factory = get_factory(config.db_type)
        engine = factory.create_engine(config)
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        finally:
            await engine.dispose()

    async def close_all(self):
        for datasource_id in list(self._engines.keys()):
            entry = self._engines.pop(datasource_id)
            engine, _ = entry
            await engine.dispose()
            logger.info(f"数据源引擎已关闭: {datasource_id}")
        self._configs.clear()

    def is_registered(self, datasource_id: str) -> bool:
        return datasource_id in self._configs

    def get_config(self, datasource_id: str) -> DatasourceConfig | None:
        return self._configs.get(datasource_id)


datasource_manager = DatasourceManager()
