import uuid

from adapter.generic import EmbeddingsAdapter
from store.qdrant import QdrantVectorStore
from utils.embeddings_validator import validate_embedding


# will be calling this method based on the parser length list
def create_and_validate_embeddings(adapter: EmbeddingsAdapter, text: str) -> list[float]:
    """Create embeddings for the given text using the provided adapter."""

    embedding = adapter.embed(text)
    validate_embedding(embedding)
    return embedding


def store_embeddings(
    content: list[tuple],
    adapter: EmbeddingsAdapter,
    vector_store: QdrantVectorStore,
    collection_name: str
):
    """Store embeddings in the Qdrant vector store."""

    embeddings = []

    print("Creating embeddings for the parsed rules")

    for file_path, rule_identifier, rule_text in content:

        print(f"Creating embedding for {rule_identifier} : {rule_text}")

        embedding = create_and_validate_embeddings(
            adapter,
            rule_text
        )

        embeddings.append(embedding)

    if not embeddings:
        raise ValueError("No rules found to create embeddings.")

    # Store embeddings in Qdrant
    if not vector_store.collection_exists(collection_name):
        vector_store.create_collection(
            collection_name,
            len(embeddings[0])
        )

    points = [
        vector_store.create_point_Struct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "file_path": str(file_path),
                "rule_identifier": rule_identifier,
                "text": rule_text
            }
        )
        for embedding, (
            file_path,
            rule_identifier,
            rule_text
        ) in zip(embeddings, content)
    ]

    print(f"Storing {len(points)} embeddings in Qdrant")

    vector_store.upsert_batch(
        collection=collection_name,
        points=points
    )