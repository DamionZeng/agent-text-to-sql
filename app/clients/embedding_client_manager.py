import asyncio

from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from app.conf.app_config import EmbeddingSettings,conf
from typing import Optional

class EmbeddingClientManager:
    def __init__(self, config: EmbeddingSettings):
        self.client: Optional[HuggingFaceEndpointEmbeddings] | None = None
        self.config: EmbeddingSettings = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        url = self._get_url()
        # Workaround for Pydantic validation error in langchain-huggingface 1.2.2+
        # which forbids URLs in the 'model' parameter.
        # We pass a dummy model name and the actual URL in model_kwargs.
        self.client = HuggingFaceEndpointEmbeddings(
            model="feature-extraction", # dummy repo id
            model_kwargs={"model": url},
            task="feature-extraction"
        )


embedding_client_manager = EmbeddingClientManager(conf.embedding)


if __name__ == "__main__":
    # Test
    embedding_client_manager.init()
    client = embedding_client_manager.client

    async def test():
        text = "What is deep learning?"
        query_result = await client.aembed_query(text)
        print(query_result[:3])
    asyncio.run(test())
