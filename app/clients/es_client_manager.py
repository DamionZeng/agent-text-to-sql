import asyncio

from elasticsearch import AsyncElasticsearch
from app.conf.app_config import ESSettings, conf

class ESClientManager:

    def __init__(self, config:ESSettings):
        self.client: AsyncElasticsearch | None = None
        self.config: ESSettings = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        await self.client.close()


es_client_manager = ESClientManager(conf.es)

if __name__ == "__main__":
    es_client_manager.init()
    client = es_client_manager.client

    async def test():

        # 删除原索引--方便测试
        await client.indices.delete(
            index="books",
        )
        # 创建索引
        await client.indices.create(
            index="books",
        )
        # 插入document
        await client.index(
            index="books",
            document={
                "name": "Snow Crash",
                "author": "Neal Stephenson",
                "release_date": "2026-02-03",
                "page_count": 470
            },
        )

        resp = await client.search(
            index="books",
        )
        print(resp)

        await es_client_manager.close()

    asyncio.run(test())