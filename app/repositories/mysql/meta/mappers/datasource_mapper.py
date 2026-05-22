from dataclasses import asdict

from app.core.crypto import encrypt, decrypt
from app.entities.datasource import Datasource
from app.models.datasource import DatasourceMySQL


class DatasourceMapper:
    @staticmethod
    def to_entity(datasource_mysql: DatasourceMySQL) -> Datasource:
        password = datasource_mysql.password
        if password:
            try:
                password = decrypt(password)
            except Exception:
                pass
        return Datasource(
            id=datasource_mysql.id,
            name=datasource_mysql.name,
            type=datasource_mysql.type,
            host=datasource_mysql.host,
            port=datasource_mysql.port,
            database=datasource_mysql.database,
            username=datasource_mysql.username,
            password=password,
            status=datasource_mysql.status,
            created_at=datasource_mysql.created_at,
            updated_at=datasource_mysql.updated_at,
        )

    @staticmethod
    def to_model(datasource: Datasource) -> DatasourceMySQL:
        data = asdict(datasource)
        if data.get("password"):
            data["password"] = encrypt(data["password"])
        return DatasourceMySQL(**data)
