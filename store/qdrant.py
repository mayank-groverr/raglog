from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class QdrantVectorStore:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)

    def create_collection(self, name: str, size: int) -> None:
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE),
        )

    def upsert(
        self, collection: str, id: str, vector: list[float], payload: dict
    ) -> None:
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(id=id, vector=vector, payload=payload)],
        )

    def search(self, collection: str, vector: list[float], top_k: int = 5):
        return self.client.query_points(
            collection_name=collection,
            query_vector=vector,
            limit=top_k,
        )

    def delete(self, collection: str, id: str) -> None:
        self.client.delete(
            collection_name=collection,
            points_selector=[id],
        )
