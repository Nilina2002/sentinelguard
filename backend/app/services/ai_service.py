from __future__ import annotations

import uuid
from typing import Iterable, List, Optional

import chromadb  # type: ignore[import-not-found]
import numpy as np

EMBEDDING_DIMENSION = 512
SIMILARITY_THRESHOLD = 0.98
TOP_K_DEFAULT = 5

_client = chromadb.PersistentClient(path="chroma_db")
_image_collection = _client.get_or_create_collection(name="image_embeddings")
_blocklist_collection = _client.get_or_create_collection(name="blocklist_embeddings")


def normalize_embedding(embedding: Iterable[float]) -> List[float]:
    vector = np.array(list(embedding), dtype=np.float32)
    if vector.ndim != 1:
        raise ValueError("Embedding must be a 1-dimensional list")
    if vector.shape[0] != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Embedding dimension must be {EMBEDDING_DIMENSION}, got {vector.shape[0]}"
        )
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Embedding norm cannot be zero")
    return (vector / norm).tolist()

def upsert_image_embedding(image_id: int, embedding: Iterable[float], model_used: str = "custom-v1") -> str:
    vector_id = str(uuid.uuid4())
    normalized = normalize_embedding(embedding)
    _image_collection.upsert(
        ids=[vector_id],
        embeddings=[normalized],
        metadatas=[{"image_id": image_id, "model_used": model_used}],
    )
    return vector_id

def search_similar_images(embedding: Iterable[float], top_k: int = TOP_K_DEFAULT):
    normalized = normalize_embedding(embedding)
    result = _image_collection.query(
        query_embeddings=[normalized],
        n_results=max(1, top_k),
        include=["metadatas", "distances"],
    )
    matches = []
    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]

    for vector_id, distance, metadata in zip(ids, distances, metadatas):
        score = 1.0 - float(distance)
        matches.append(
            {
                "vector_id": vector_id,
                "image_id": int(metadata.get("image_id", 0)),
                "score": score,
                "model_used": metadata.get("model_used"),
            }
        )
    return matches

def get_image_embedding(vector_id: str) -> Optional[List[float]]:
    result = _image_collection.get(ids=[vector_id], include=["embeddings"])
    embeddings = result.get("embeddings")
    if embeddings is None or len(embeddings) == 0:
        return None
    first_embedding = embeddings[0]
    return [float(value) for value in first_embedding]

def add_to_blocklist(vector_id: str, embedding: Iterable[float], reason: str = "ncii"):
    normalized = normalize_embedding(embedding)
    _blocklist_collection.upsert(
        ids=[vector_id],
        embeddings=[normalized],
        metadatas=[{"reason": reason}],
    )

def is_blocklisted(embedding: Iterable[float], threshold: float = SIMILARITY_THRESHOLD) -> bool:
    normalized = normalize_embedding(embedding)
    result = _blocklist_collection.query(
        query_embeddings=[normalized],
        n_results=1,
        include=["distances"],
    )
    distances = result.get("distances", [[]])[0]
    if not distances:
        return False
    score = 1.0 - float(distances[0])
    return score >= threshold
