"""
retrieve.py — Query ChromaDB for the top-k most similar chunks.

Supports three retrieval modes (default: dense):
    - "dense"  : ChromaDB cosine similarity over MiniLM embeddings.
    - "bm25"   : Lexical BM25 over the same chunk corpus.
    - "hybrid" : Reciprocal Rank Fusion (RRF) of the two.

Optional metadata filtering by document type prefix (e.g. "policy", "runbook",
"faq", "guide", "brief") lets the caller route queries to a topical subset of
the corpus before scoring.
"""

import math
import os
import re
from collections import Counter
from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "knowledge_base"
EMBED_MODEL = "all-MiniLM-L6-v2"

DEFAULT_K = 20
RRF_K_CONSTANT = 60  # Standard RRF constant from Cormack et al. (2009)

DOC_TYPES = ("policy", "runbook", "faq", "guide", "brief")


@dataclass
class RetrievedChunk:
    id: str
    text: str
    source: str
    chunk_index: int
    score: float


_model: SentenceTransformer | None = None
_collection = None
_bm25_index: "BM25Index | None" = None


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


# ---------- BM25 (Okapi) over the same chunks stored in ChromaDB ---------- #

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    """Minimal Okapi BM25 index built from the chunks in the Chroma collection."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.doc_ids: list[str] = []
        self.doc_texts: list[str] = []
        self.doc_metadatas: list[dict] = []
        self.doc_token_counts: list[Counter] = []
        self.doc_lengths: list[int] = []
        self.avgdl: float = 0.0
        self.df: Counter = Counter()
        self.N: int = 0

    def fit(self, ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        self.doc_ids = ids
        self.doc_texts = texts
        self.doc_metadatas = metadatas
        self.doc_token_counts = [Counter(_tokenize(t)) for t in texts]
        self.doc_lengths = [sum(c.values()) for c in self.doc_token_counts]
        self.avgdl = (sum(self.doc_lengths) / len(self.doc_lengths)) if self.doc_lengths else 0.0
        self.N = len(ids)

        df: Counter = Counter()
        for counts in self.doc_token_counts:
            for term in counts.keys():
                df[term] += 1
        self.df = df

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        if self.N == 0:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = [0.0] * self.N
        for term in tokens:
            df = self.df.get(term, 0)
            if df == 0:
                continue
            idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1.0)
            for i, counts in enumerate(self.doc_token_counts):
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                dl = self.doc_lengths[i]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1.0))
                scores[i] += idf * (tf * (self.k1 + 1)) / denom

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(i, s) for i, s in ranked[:k] if s > 0.0]


def _get_bm25_index() -> BM25Index:
    global _bm25_index
    if _bm25_index is None:
        coll = _get_collection()
        # Pull every chunk into memory once; the corpus is ~hundreds of chunks.
        all_data = coll.get(include=["documents", "metadatas"])
        idx = BM25Index()
        idx.fit(all_data["ids"], all_data["documents"], all_data["metadatas"])
        _bm25_index = idx
    return _bm25_index


# ---------- Public retrieval API ---------- #


def _post_filter(chunks: list[RetrievedChunk], doc_types: list[str] | None) -> list[RetrievedChunk]:
    if not doc_types:
        return chunks
    allowed = set(doc_types)
    filtered = []
    for c in chunks:
        prefix = c.source.split("-", 1)[0]
        if prefix in allowed:
            filtered.append(c)
    return filtered


def _dense_retrieve(query: str, k: int) -> list[RetrievedChunk]:
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    chunks = []
    for i, doc_id in enumerate(ids):
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


def _bm25_retrieve(query: str, k: int) -> list[RetrievedChunk]:
    idx = _get_bm25_index()
    hits = idx.search(query, k)
    chunks = []
    for doc_pos, score in hits:
        meta = idx.doc_metadatas[doc_pos]
        chunks.append(
            RetrievedChunk(
                id=idx.doc_ids[doc_pos],
                text=idx.doc_texts[doc_pos],
                source=meta["source"],
                chunk_index=meta["chunk_index"],
                score=float(score),
            )
        )
    return chunks


def _rrf_fuse(
    rankings: list[list[RetrievedChunk]],
    k: int,
    rrf_k: int = RRF_K_CONSTANT,
) -> list[RetrievedChunk]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion."""
    fused_scores: dict[str, float] = {}
    canonical: dict[str, RetrievedChunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, start=1):
            fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + 1.0 / (rrf_k + rank)
            canonical.setdefault(chunk.id, chunk)

    fused = []
    for chunk_id, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True):
        c = canonical[chunk_id]
        fused.append(
            RetrievedChunk(
                id=c.id, text=c.text, source=c.source,
                chunk_index=c.chunk_index, score=score,
            )
        )
    return fused[:k]


def retrieve(
    query: str,
    k: int = DEFAULT_K,
    mode: str = "dense",
    doc_types: list[str] | None = None,
) -> list[RetrievedChunk]:
    """
    Embed the query and return the top-k chunks from the vector store.

    Args:
        query: user query
        k: number of chunks to return
        mode: "dense" (default), "bm25", or "hybrid"
        doc_types: optional list of doc-type prefixes to filter to
                   (e.g. ["policy", "faq"])
    """
    if mode == "dense":
        raw = _dense_retrieve(query, k * 2 if doc_types else k)
        return _post_filter(raw, doc_types)[:k]

    if mode == "bm25":
        raw = _bm25_retrieve(query, k * 2 if doc_types else k)
        return _post_filter(raw, doc_types)[:k]

    if mode == "hybrid":
        dense = _dense_retrieve(query, k)
        sparse = _bm25_retrieve(query, k)
        fused = _rrf_fuse([dense, sparse], k=k * 2 if doc_types else k)
        return _post_filter(fused, doc_types)[:k]

    raise ValueError(f"Unknown retrieval mode: {mode!r} (expected dense|bm25|hybrid)")
