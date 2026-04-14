"""
retrieve.py — Query ChromaDB for the top-k most similar chunks.

Shared by all three pipelines.
"""

import os
from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "knowledge_base"
EMBED_MODEL = "all-MiniLM-L6-v2"

DEFAULT_K = 20


@dataclass
class RetrievedChunk:
    id: str
    text: str
    source: str
    chunk_index: int
    score: float


_model: SentenceTransformer | None = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def retrieve(query: str, k: int = DEFAULT_K) -> list[RetrievedChunk]:
    """Embed the query and return the top-k chunks from the vector store."""
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    for i, doc_id in enumerate(ids):
        # ChromaDB cosine distance → similarity = 1 - distance
        score = 1.0 - distances[i]
        chunks.append(
            RetrievedChunk(
                id=doc_id,
                text=documents[i],
                source=metadatas[i]["source"],
                chunk_index=metadatas[i]["chunk_index"],
                score=score,
            )
        )
    return chunks
