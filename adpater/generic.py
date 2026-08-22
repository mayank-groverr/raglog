from abc import ABC, abstractmethod

"""
A interface for embeddings adapter.
You must implement this interface to create a new adapter for your embeddings.
"""
class EmbeddingsAdapter(ABC):

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Write the implementation to embed the given text and return the embedding 
           using the specific embedding model you want to use.
        """
        pass

