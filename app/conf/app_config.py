import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogFileSettings(BaseModel):
    enable: bool = True
    level: str = "INFO"
    path: str = "logs"
    rotation: str = "10 MB"
    retention: str = "7 days"


class LogConsoleSettings(BaseModel):
    enable: bool = True
    level: str = "INFO"


class LoggingSettings(BaseModel):
    file: LogFileSettings = LogFileSettings()
    console: LogConsoleSettings = LogConsoleSettings()


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""


class QdrantSettings(BaseModel):
    host: str = "localhost"
    port: int = 6333
    embedding_size: int = 1024


class EmbeddingSettings(BaseModel):
    host: str = "localhost"
    port: int = 8081
    model: str = "BAAI/bge-large-zh-v1.5"


class ESSettings(BaseModel):
    host: str = "localhost"
    port: int = 9200
    index_name: str = "data_agent"


class LLMSettings(BaseModel):
    model_name: str = "gpt-5.2-codex"
    api_key: str = "DASHSCOPE_API_KEY"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class CryptoSettings(BaseModel):
    aes_key: str = ""


# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

    logging: LoggingSettings = LoggingSettings()
    db_meta: DatabaseSettings = Field(default_factory=DatabaseSettings)
    qdrant: QdrantSettings = QdrantSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    es: ESSettings = ESSettings()
    llm: LLMSettings = LLMSettings()
    crypto: CryptoSettings = CryptoSettings()


# Initialize settings
settings = AppSettings()

# For backward compatibility or if 'conf' variable name is preferred
conf = settings

if __name__ == "__main__":
    # Print settings to verify (excluding sensitive info)
    print(settings.model_dump(exclude={"llm": {"api_key"}, "db_meta": {"password"}}))
