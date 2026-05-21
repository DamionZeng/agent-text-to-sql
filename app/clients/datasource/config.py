from dataclasses import dataclass


@dataclass(frozen=True)
class DatasourceConfig:
    datasource_id: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str

    @property
    def cache_key(self) -> str:
        return self.datasource_id
