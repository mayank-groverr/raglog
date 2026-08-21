from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)


def create_collection(name, size_of_vector):
    client.recreate_collection(
        collection_name=name,
        vectors_config=VectorParams(size=size_of_vector, distance=Distance.COSINE),
    )
