"""
naive.py — Pipeline 1 (control group).

Plain Python, no framework, no re-ranking.
    retrieve(query, k=5) → synthesise(query, chunks) → answer
"""

from dataclasses import dataclass

from shared.retrieve import retrieve, RetrievedChunk
from shared.synthesise import synthesise, Answer

DEFAULT_TOP_K = 5
DEFAULT_MODE = "dense"


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


def run(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    mode: str = DEFAULT_MODE,
    doc_types: list[str] | None = None,
) -> PipelineResult:
    chunks = retrieve(query, k=top_k, mode=mode, doc_types=doc_types)
    answer = synthesise(query, chunks)
    return PipelineResult(
        answer=answer,
        retrieved=chunks,
        reranked=chunks,
        iterations=1,
    )
