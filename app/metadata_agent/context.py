from typing import TypedDict

from langchain.chat_models import init_chat_model

from app.repositories.mysql.meta.datasource_repository import DatasourceRepository


class MetaAgentContext(TypedDict):
    llm: init_chat_model
    datasource_repository: DatasourceRepository
