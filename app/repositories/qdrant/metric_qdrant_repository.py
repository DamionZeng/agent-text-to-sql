from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance
from app.conf.app_config import conf
from qdrant_client.http.models import PointStruct

from app.entities.metric_info import MetricInfo


class MetricQdrantRepository:

    collection_name = 'metric_info_collection'

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=conf.qdrant.embedding_size, distance=Distance.COSINE),
            )

    async def upsert(self, ids: list[str], embeddings:list[list[float]], payloads: list[dict], batch_size: int = 20):
        points: list[PointStruct] = [PointStruct(id=id, vector=embedding, payload=payload)
                                     for id, embedding, payload in zip(ids, embeddings, payloads)]
        for i in range(0, len(points), batch_size):
            await self.client.upsert(collection_name=self.collection_name, points=points[i:i + batch_size])

    async def search(self, embedding: list[float], score_threshold: float=0.6, limit: int=20) -> list[MetricInfo]:
        # 向量查询
        search_result = await self.client.query_points(
            collection_name= self.collection_name,
            query=embedding,
            limit=limit,
            score_threshold=score_threshold,
        )
        return [MetricInfo(**point.payload) for point in search_result.points]
