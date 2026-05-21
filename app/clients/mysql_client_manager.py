from app.conf.app_config import DatabaseSettings, conf
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


class MySQLClientManager:

    def __init__(self, config: DatabaseSettings):
        self.engine = None
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
