"""
rag_chain.py — Pipeline 2.

LangGraph linear graph: retrieve → rerank → synthesise.
Adds cross-encoder re-ranking between retrieval and synthesis.
No loops or conditional logic.
"""

from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import StateGraph, END

from shared.retrieve import retrieve, RetrievedChunk
from shared.rerank import rerank
from shared.synthesise import synthesise, Answer

DEFAULT_RETRIEVE_K = 20
DEFAULT_RERANK_N = 5
DEFAULT_MODE = "dense"


class ChainState(TypedDict, total=False):
    query: str
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    answer: Answer
    # Per-call config
    retrieve_k: int
    rerank_n: int
    mode: str
    doc_types: list[str] | None
    score_threshold: float | None
    use_mmr: bool
    mmr_lambda: float


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


def _retrieve_node(state: ChainState) -> ChainState:
    return {
        "retrieved": retrieve(
            state["query"],
            k=state.get("retrieve_k", DEFAULT_RETRIEVE_K),
            mode=state.get("mode", DEFAULT_MODE),
            doc_types=state.get("doc_types"),
        )
    }


def _rerank_node(state: ChainState) -> ChainState:
    return {
        "reranked": rerank(
            state["query"],
            state["retrieved"],
            n=state.get("rerank_n", DEFAULT_RERANK_N),
            score_threshold=state.get("score_threshold"),
            use_mmr=state.get("use_mmr", False),
            mmr_lambda=state.get("mmr_lambda", 0.7),
        )
    }


def _synthesise_node(state: ChainState) -> ChainState:
    return {"answer": synthesise(state["query"], state["reranked"])}


def _build_graph():
    graph = StateGraph(ChainState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("rerank", _rerank_node)
    graph.add_node("synthesise", _synthesise_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_edge("rerank", "synthesise")
    graph.add_edge("synthesise", END)
    return graph.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def run(
    query: str,
    retrieve_k: int = DEFAULT_RETRIEVE_K,
    rerank_n: int = DEFAULT_RERANK_N,
    mode: str = DEFAULT_MODE,
    doc_types: list[str] | None = None,
    score_threshold: float | None = None,
    use_mmr: bool = False,
    mmr_lambda: float = 0.7,
) -> PipelineResult:
    final_state = _get_graph().invoke(
        {
            "query": query,
            "retrieve_k": retrieve_k,
            "rerank_n": rerank_n,
            "mode": mode,
            "doc_types": doc_types,
            "score_threshold": score_threshold,
            "use_mmr": use_mmr,
            "mmr_lambda": mmr_lambda,
        }
    )
    return PipelineResult(
        answer=final_state["answer"],
        retrieved=final_state["retrieved"],
        reranked=final_state["reranked"],
        iterations=1,
    )
