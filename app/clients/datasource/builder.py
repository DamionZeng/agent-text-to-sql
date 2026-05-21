from app.entities.datasource import Datasource
from app.clients.datasource.config import DatasourceConfig


class DatasourceConfigBuilder:
    def __init__(self):
        self._datasource_id: str | None = None
        self._db_type: str | None = None
        self._host: str | None = None
        self._port: int | None = None
        self._database: str | None = None
        self._username: str | None = None
        self._password: str | None = None

    def from_entity(self, datasource: Datasource) -> "DatasourceConfigBuilder":
        self._datasource_id = datasource.id
        self._db_type = datasource.type.lower()
        self._host = datasource.host
        self._port = datasource.port
        self._database = datasource.database
        self._username = datasource.username
        self._password = datasource.password
        return self

    def datasource_id(self, value: str) -> "DatasourceConfigBuilder":
        self._datasource_id = value
        return self

    def db_type(self, value: str) -> "DatasourceConfigBuilder":
        self._db_type = value.lower()
        return self

    def host(self, value: str) -> "DatasourceConfigBuilder":
        self._host = value
        return self

    def port(self, value: int) -> "DatasourceConfigBuilder":
        self._port = value
        return self

    def database(self, value: str) -> "DatasourceConfigBuilder":
        self._database = value
        return self

    def username(self, value: str) -> "DatasourceConfigBuilder":
        self._username = value
        return self

    def password(self, value: str) -> "DatasourceConfigBuilder":
        self._password = value
        return self

    def build(self) -> DatasourceConfig:
        if not all([self._datasource_id, self._db_type, self._host,
                     self._port, self._database, self._username, self._password]):
            raise ValueError("数据源配置不完整，所有字段均为必填")
        return DatasourceConfig(
            datasource_id=self._datasource_id,
            db_type=self._db_type,
            host=self._host,
            port=self._port,
            database=self._database,
            username=self._username,
            password=self._password,
        )
