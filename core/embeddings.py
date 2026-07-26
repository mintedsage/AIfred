"""
embeddings.py — turns text into vectors, entirely on your machine.

Uses sentence-transformers. The model weights are downloaded once from
Hugging Face the first time Alfred runs, cached under ~/.cache, and never
contacted again — this is the only "setup requires internet" step in the
whole project, matching the "offline after setup" requirement.
"""

from functools import lru_cache
import numpy as np

from config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the rest of the app can be explored/tested without
    # requiring the (fairly heavy) sentence-transformers import at module load.
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed(text: str) -> np.ndarray:
    """Return a single embedding vector (float32 numpy array) for a piece of text."""
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype=np.float32)


def embed_many(texts: list[str]) -> np.ndarray:
    """Batch version of embed(), returns a 2D array of shape (n, dim)."""
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    query_vec: shape (dim,)
    matrix: shape (n, dim)
    Returns similarity scores, shape (n,). Vectors are assumed pre-normalized,
    so this is just a dot product.
    """
    if matrix.size == 0:
        return np.array([])
    return matrix @ query_vec
