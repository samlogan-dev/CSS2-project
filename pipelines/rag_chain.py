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

RETRIEVE_K = 20
RERANK_N = 5


class ChainState(TypedDict, total=False):
    query: str
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    answer: Answer


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


def _retrieve_node(state: ChainState) -> ChainState:
    return {"retrieved": retrieve(state["query"], k=RETRIEVE_K)}


def _rerank_node(state: ChainState) -> ChainState:
    return {"reranked": rerank(state["query"], state["retrieved"], n=RERANK_N)}


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


def run(query: str) -> PipelineResult:
    final_state = _get_graph().invoke({"query": query})
    return PipelineResult(
        answer=final_state["answer"],
        retrieved=final_state["retrieved"],
        reranked=final_state["reranked"],
        iterations=1,
    )
