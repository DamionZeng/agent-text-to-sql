from typing import TypedDict

from app.repositories.mysql.meta.datasource_repository import DatasourceRepository


class MetaAgentContext(TypedDict):
    datasource_repository: DatasourceRepository