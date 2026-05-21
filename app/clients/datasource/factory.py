from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker

from app.clients.datasource.config import DatasourceConfig


class DatasourceFactory(ABC):
    @abstractmethod
    def create_engine(self, config: DatasourceConfig) -> AsyncEngine:
        pass

    @abstractmethod
    def build_url(self, config: DatasourceConfig) -> str:
        pass


class MySQLDatasourceFactory(DatasourceFactory):
    def build_url(self, config: DatasourceConfig) -> str:
        return (
            f"mysql+asyncmy://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}?charset=utf8mb4"
        )

    def create_engine(self, config: DatasourceConfig) -> AsyncEngine:
        url = self.build_url(config)
        return create_async_engine(url, pool_size=5, pool_pre_ping=True)


class PostgreSQLDatasourceFactory(DatasourceFactory):
    def build_url(self, config: DatasourceConfig) -> str:
        return (
            f"postgresql+asyncpg://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}"
        )

    def create_engine(self, config: DatasourceConfig) -> AsyncEngine:
        url = self.build_url(config)
        return create_async_engine(url, pool_size=5, pool_pre_ping=True)


_FACTORY_REGISTRY: dict[str, DatasourceFactory] = {
    "mysql": MySQLDatasourceFactory(),
    "postgresql": PostgreSQLDatasourceFactory(),
}


def get_factory(db_type: str) -> DatasourceFactory:
    factory = _FACTORY_REGISTRY.get(db_type)
    if not factory:
        raise ValueError(f"不支持的数据源类型: {db_type}，已注册类型: {list(_FACTORY_REGISTRY.keys())}")
    return factory


def register_factory(db_type: str, factory: DatasourceFactory):
    _FACTORY_REGISTRY[db_type] = factory
