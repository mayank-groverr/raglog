from store.qdrant import QdrantVectorStore
from adapter.generic import EmbeddingsAdapter
import requests
from core import process_and_store_rules, retrieve_similar_rules


# Only for development. To be changed with actual test methods using pytest library
class Adapter(EmbeddingsAdapter):
    def __init__(
        self,
        url: str = "http://localhost:11434/api/embed",
        model: str = "nomic-embed-text"
    ):
        self.url = url
        self.model = model

    def embed(self, text: str) -> list[float]:

        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "input": text
            }
        )

        response.raise_for_status()

        data = response.json()

        return data["embeddings"][0]



vector_store = QdrantVectorStore()


# process_and_store_rules(
#     "C:\\Users\\Mayank\\Desktop\\rules",
#     r"^exceptions-rule\d*\.txt$",
#     Adapter(),
#     vector_store,
#     "test"
# )


results = retrieve_similar_rules(
    "ERROR Authentication service unavailable",
    Adapter(),
    vector_store,
    "test",
    top_k=5
)


print(results)