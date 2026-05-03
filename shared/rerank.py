"""
rerank.py — Cross-encoder re-ranking of retrieved chunks.

Shared by Pipelines 2 and 3. Two improvements over a plain top-N cut:

    1. Optional absolute score threshold — chunks below it are dropped, so the
       LLM does not get padded with weak context (addresses the "top-20 has
       too much noise" feedback).
    2. Optional MMR (Maximal Marginal Relevance) selection — picks chunks that
       are both relevant AND diverse, reducing near-duplicate context.
"""

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from shared.retrieve import RetrievedChunk

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
EMBED_MODEL_FOR_MMR = "all-MiniLM-L6-v2"

DEFAULT_N = 5
DEFAULT_SCORE_THRESHOLD: float | None = None  # disabled by default
DEFAULT_USE_MMR = False
DEFAULT_MMR_LAMBDA = 0.7  # 1.0 = pure relevance, 0.0 = pure diversity

_encoder: CrossEncoder | None = None
_mmr_embedder: SentenceTransformer | None = None


def _get_encoder() -> CrossEncoder:
    """Lazy-load the cross-encoder model to save memory."""
    global _encoder
    if _encoder is None:
        print(f"[Reranker] Loading model: {RERANK_MODEL} ...")
        _encoder = CrossEncoder(RERANK_MODEL)
    return _encoder


def _get_mmr_embedder() -> SentenceTransformer:
    global _mmr_embedder
    if _mmr_embedder is None:
        _mmr_embedder = SentenceTransformer(EMBED_MODEL_FOR_MMR)
    return _mmr_embedder


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _mmr_select(
    query: str,
    candidates: list[RetrievedChunk],
    n: int,
    lambda_: float,
) -> list[RetrievedChunk]:
    """Greedy MMR over chunks already sorted by relevance score."""
    if not candidates:
        return []
    if n >= len(candidates):
        return candidates

    embedder = _get_mmr_embedder()
    texts = [c.text for c in candidates]
    chunk_embs = np.array(embedder.encode(texts, show_progress_bar=False))
    query_emb = np.array(embedder.encode([query], show_progress_bar=False)[0])

    relevance = np.array([_cosine(query_emb, e) for e in chunk_embs])

    selected_idx: list[int] = []
    remaining = list(range(len(candidates)))

    first = int(np.argmax(relevance))
    selected_idx.append(first)
    remaining.remove(first)

    while remaining and len(selected_idx) < n:
        best_idx = -1
        best_score = -float("inf")
        for i in remaining:
            sim_to_selected = max(_cosine(chunk_embs[i], chunk_embs[j]) for j in selected_idx)
            mmr = lambda_ * relevance[i] - (1 - lambda_) * sim_to_selected
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        selected_idx.append(best_idx)
        remaining.remove(best_idx)

    return [candidates[i] for i in selected_idx]


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    n: int = DEFAULT_N,
    score_threshold: float | None = DEFAULT_SCORE_THRESHOLD,
    use_mmr: bool = DEFAULT_USE_MMR,
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
) -> list[RetrievedChunk]:
    """
    Re-score query–chunk pairs with a cross-encoder and return the top n.

    Args:
        query: user query
        chunks: candidates from the retriever
        n: maximum chunks to return
        score_threshold: drop any chunk with cross-encoder score below this.
            None disables the filter (default).
        use_mmr: if True, select n via MMR instead of pure top-n by score.
        mmr_lambda: relevance/diversity trade-off (1.0 = pure relevance).
    """
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

    rescored.sort(key=lambda c: c.score, reverse=True)

    if score_threshold is not None:
        rescored = [c for c in rescored if c.score >= score_threshold]
        if not rescored:
            return []

    if use_mmr:
        return _mmr_select(query, rescored, n=n, lambda_=mmr_lambda)

    return rescored[:n]
