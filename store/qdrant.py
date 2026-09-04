import httpx
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams
from tenacity import (  # type: ignore
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def translate_qdrant_error(e: Exception, collection: str, extra: str = "") -> Exception:
    """Turn Qdrant's raw exceptions into something callers can actually branch on."""
    if isinstance(e, UnexpectedResponse):
        if e.status_code == 404:
            return ValueError(f"Collection '{collection}' not found{extra}")
        if e.status_code == 409:
            return ValueError(f"Collection '{collection}' already exists")
        if e.status_code == 400:
            return ValueError(f"Bad request for collection '{collection}': {e}{extra}")
        return e
    if isinstance(e, httpx.ConnectError):
        return ConnectionError("Qdrant server unreachable")
    if isinstance(e, httpx.TimeoutException):
        return TimeoutError("Qdrant request timed out")
    return e


# Retry only on things that are actually worth retrying - a dropped connection
# or a slow server, not a 404 or a bad payload.
retry_on_transient = retry(
    retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    reraise=True,
)


class QdrantVectorStore:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)

    # Create a new collection
    @retry_on_transient
    def create_collection(self, name: str, size: int) -> None:
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
        except (UnexpectedResponse, httpx.ConnectError, httpx.TimeoutException) as e:
            raise translate_qdrant_error(e, name) from e

    # Insert a single record into a collection
    @retry_on_transient
    def upsert_single(
        self, collection: str, id: str, vector: list[float], payload: dict
    ) -> None:
        try:
            self.client.upsert(
                collection_name=collection,
                points=[PointStruct(id=id, vector=vector, payload=payload)],
            )
        except (UnexpectedResponse, httpx.ConnectError, httpx.TimeoutException) as e:
            raise translate_qdrant_error(e, collection, extra=f" (id '{id}')") from e

    # Batch upsert - just hands the points straight to upsert, no need to
    # unpack into separate vectors/payloads/ids lists.
    @retry_on_transient
    def upsert_batch(self, collection: str, points: list[PointStruct]) -> None:
        try:
            self.client.upsert(collection_name=collection, points=points)
        except (UnexpectedResponse, httpx.ConnectError, httpx.TimeoutException) as e:
            raise translate_qdrant_error(e, collection, extra=" (batch)") from e

    # Search for the closest vectors in a collection
    @retry_on_transient
    def search(self, collection: str, vector: list[float], top_k: int = 5):
        try:
            return self.client.query_points(
                collection_name=collection,
                query=vector,
                limit=top_k,
            )
        except (UnexpectedResponse, httpx.ConnectError, httpx.TimeoutException) as e:
            raise translate_qdrant_error(e, collection, extra=" (dim mismatch?)") from e

    # Delete a record from a collection
    @retry_on_transient
    def delete(self, collection: str, id: str) -> None:
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=[id],
            )
        except (UnexpectedResponse, httpx.ConnectError, httpx.TimeoutException) as e:
            raise translate_qdrant_error(e, collection, extra=f" or id '{id}'") from e

    @retry_on_transient
    def create_point_Struct(self, id: str , vector: list[float], payload: dict) -> PointStruct:
        """
        Function to create a PointStruct object for Qdrant.
        arguments: id: (of type: str), vector: (of type: list[float]), payload: (of type: dict)
        returns: PointStruct object.
        """
        return PointStruct(id=id, vector=vector, payload=payload)

    @retry_on_transient
    def collection_exists(self, collection: str) -> bool:
        """
        To check if a collection exists in Qdrant.
        arguments: collection: (of type: str)
        returns: True if the collection exists, False otherwise.
        """
        return self.client.collection_exists(collection)