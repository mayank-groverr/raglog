from raglog.adapter.generic.EmbeddingsAdapter
from raglog.store.qdrant import QdrantVectorStore

def validate_query(query: str) -> None:
    """Validate the user's query."""

    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    if not query.strip():
        raise ValueError("Query cannot be empty.")

def validate_embedding(embedding: list[float]) -> None:
    """Validate that the embedding is a non-empty list of floats."""

    
    if not isinstance(embedding, list):
        raise TypeError("Embedding must be a list.")

    if not all(isinstance(value, float) for value in embedding):
        raise TypeError("Embedding must contain only floats.")

def retrieve(
    query: str,
    embedding_adapter: EmbeddingsAdapter,
    vector_store: QdrantVectorStore,
    collection: str,
    top_k: int = 5,
):
    """
    Convert the query into an embedding and retrieve
    the most similar points from Qdrant.
    """

    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not collection:
        raise ValueError("Collection name cannot be empty.")

    query_embedding = embedding_adapter.embed(query)

    results = vector_store.search(
        collection=collection,
        vector=query_embedding,
        top_k=top_k,
    )

    return results