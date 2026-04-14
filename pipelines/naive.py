"""
naive.py — Pipeline 1 (control group).

Plain Python, no framework, no re-ranking.
    retrieve(query, k=5) → synthesise(query, chunks) → answer
"""

from dataclasses import dataclass

from shared.retrieve import retrieve, RetrievedChunk
from shared.synthesise import synthesise, Answer

TOP_K = 5


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


def run(query: str) -> PipelineResult:
    chunks = retrieve(query, k=TOP_K)
    answer = synthesise(query, chunks)
    return PipelineResult(
        answer=answer,
        retrieved=chunks,
        reranked=chunks,
        iterations=1,
    )
