import uuid

from raglog.adpater.generic import EmbeddingsAdapter
from raglog.store.qdrant import QdrantVectorStore

def validate_embedding(embedding):
    """Validate that the embedding is a non-empty list of floats."""

    if not isinstance(embedding, list):
        raise TypeError("Embedding must be a list.")
    if not embedding:
        raise ValueError("Embedding cannot be empty.")
    if not all(isinstance(value, float) for value in embedding):
        raise TypeError("Embedding must contain only floats.")

    return True

# will be calling this method based on the parser length list
def create_and_validate_embeddings(adapter: EmbeddingsAdapter, text: str) -> list[float]:
    """Create embeddings for the given text using the provided adapter."""

    embedding = adapter.embed(text)
    validate_embedding(embedding)
    return embedding


def ingest_text(embeddings : list[list[float]], vector_Store: QdrantVectorStore, collection_name: str):
    """
    Ingest the given embeddings into the vector store.
    """
    list_of_point_structs = create_point_struct(embeddings, vector_Store)
    vector_Store.upsert_batch(points=list_of_point_structs, collection_name=collection_name)

