from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="normal_logs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
client.create_collection(
    collection_name="exception_rules",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
client.create_collection(
    collection_name="anomaly_logs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)
