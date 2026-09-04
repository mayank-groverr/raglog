def validate_embedding(embedding):
    """Validate that the embedding is a non-empty list of floats."""

    if not isinstance(embedding, list):
        raise TypeError("Embedding must be a list.")
    if not embedding:
        raise ValueError("Embedding cannot be empty.")
    if not all(isinstance(value, float) for value in embedding):
        raise TypeError("Embedding must contain only floats.")
    return True