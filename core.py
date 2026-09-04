from ingestion import ingestion, parser
from rag.retriever import retrieve
from store.qdrant import QdrantVectorStore

def process_and_store_rules(input_path: str, pattern_for_files: str, embedding_adapter, vector_store: QdrantVectorStore, collection_name: str):
    """
    Process the rules from the input path and store them in the vector store.
    """
    # Parse the rules
    content = parser.rules_parser(input_path, pattern_for_files)

    # Store embeddings in the vector store
    ingestion.store_embeddings(content, embedding_adapter, vector_store, collection_name)


def retrieve_similar_rules(query: str, embedding_adapter, vector_store: QdrantVectorStore, collection_name: str, top_k: int = 5):
    """
    Retrieve the most similar rules from the vector store based on the query.
    """
    # Retrieve similar rules
    results = retrieve(query, embedding_adapter, vector_store, collection_name, top_k)

    return results