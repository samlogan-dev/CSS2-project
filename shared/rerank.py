"""
rerank.py — Cross-encoder re-ranking of retrieved chunks.

Shared by Pipelines 2 and 3.
"""

from sentence_transformers import CrossEncoder

from shared.retrieve import RetrievedChunk

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_N = 5

_encoder: CrossEncoder | None = None


def _get_encoder() -> CrossEncoder:
    """Lazy-load the cross-encoder model to save memory."""
    global _encoder
    if _encoder is None:
        print(f"[Reranker] Loading model: {RERANK_MODEL} ...")
        _encoder = CrossEncoder(RERANK_MODEL)
    return _encoder


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    n: int = DEFAULT_N,
) -> list[RetrievedChunk]:
    """Re-score query–chunk pairs with a cross-encoder and return the top n."""
    if not chunks:
        return []

    encoder = _get_encoder()
    pairs = [(query, chunk.text) for chunk in chunks]
    scores = encoder.predict(pairs)

    rescored = [
        RetrievedChunk(
            id=chunk.id,
            text=chunk.text,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            score=float(score),
        )
        for chunk, score in zip(chunks, scores)
    ]

    # Sort chunks by cross-encoder score (highest first)
    rescored.sort(key=lambda c: c.score, reverse=True)
    return rescored[:n]
