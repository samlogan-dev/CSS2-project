"""
agentic.py — Pipeline 3.

LangGraph graph with conditional edges.
Same as Pipeline 2, but: if the top re-ranked chunk score < threshold,
reformulate the query via GPT-4o and retry. Max 2 retries.
"""

import os
from dataclasses import dataclass
from typing import TypedDict

from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from shared.retrieve import retrieve, RetrievedChunk
from shared.rerank import rerank
from shared.synthesise import synthesise, Answer

load_dotenv()

DEFAULT_RETRIEVE_K = 20
DEFAULT_RERANK_N = 5
DEFAULT_MODE = "dense"
DEFAULT_REFORMULATE_THRESHOLD = 0.0
DEFAULT_MAX_RETRIES = 2
REFORMULATE_MODEL = "gpt-4o"

REFORMULATE_SYSTEM = (
    "You rewrite user questions to improve retrieval from an internal "
    "documentation vector store. Return ONLY the rewritten query as a single "
    "line of plain text — no preamble, no quotes, no explanation."
)

REFORMULATE_USER = """Original question: {query}

The previous retrieval returned weak results. Rewrite the question to be more \
specific, using likely terminology from enterprise HR, IT, and engineering \
documentation. Expand abbreviations and add keywords that would appear in a \
policy, runbook, or FAQ."""


class AgenticState(TypedDict, total=False):
    original_query: str
    query: str
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    answer: Answer
    iterations: int
    # Per-call config
    retrieve_k: int
    rerank_n: int
    mode: str
    doc_types: list[str] | None
    score_threshold: float | None
    use_mmr: bool
    mmr_lambda: float
    reformulate_threshold: float
    max_retries: int


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _reformulate(original_query: str) -> str:
    print(f"[Agentic] Reformulating query: '{original_query}'")
    client = _get_client()
    response = client.chat.completions.create(
        model=REFORMULATE_MODEL,
        max_tokens=256,
        messages=[
            {"role": "system", "content": REFORMULATE_SYSTEM},
            {
                "role": "user",
                "content": REFORMULATE_USER.format(query=original_query),
            },
        ],
    )
    text = response.choices[0].message.content or ""
    new_query = text.strip().splitlines()[0] if text.strip() else original_query
    print(f"[Agentic] New query generated: '{new_query}'")
    return new_query


def _retrieve_node(state: AgenticState) -> AgenticState:
    return {
        "retrieved": retrieve(
            state["query"],
            k=state.get("retrieve_k", DEFAULT_RETRIEVE_K),
            mode=state.get("mode", DEFAULT_MODE),
            doc_types=state.get("doc_types"),
        )
    }


def _rerank_node(state: AgenticState) -> AgenticState:
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


def _reformulate_node(state: AgenticState) -> AgenticState:
    new_query = _reformulate(state["original_query"])
    return {
        "query": new_query,
        "iterations": state.get("iterations", 0) + 1,
    }


def _synthesise_node(state: AgenticState) -> AgenticState:
    return {"answer": synthesise(state["original_query"], state["reranked"])}


def _decide_after_rerank(state: AgenticState) -> str:
    reranked = state.get("reranked", [])
    iterations = state.get("iterations", 0)
    threshold = state.get("reformulate_threshold", DEFAULT_REFORMULATE_THRESHOLD)
    max_retries = state.get("max_retries", DEFAULT_MAX_RETRIES)

    if not reranked:
        print("[Router] No chunks retrieved. Routing to Synthesise.")
        return "synthesise"

    top_score = reranked[0].score
    print(f"[Router] Iteration {iterations} | Top Rerank Score: {top_score:.3f} | Threshold: {threshold}")

    if top_score >= threshold:
        print("[Router] Confidence threshold met. Routing to Synthesise.")
        return "synthesise"
    if iterations >= max_retries:
        print(f"[Router] Max retries ({max_retries}) reached. Routing to Synthesise.")
        return "synthesise"

    print("[Router] Confidence low. Routing to Reformulate.")
    return "reformulate"


def _build_graph():
    graph = StateGraph(AgenticState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("rerank", _rerank_node)
    graph.add_node("reformulate", _reformulate_node)
    graph.add_node("synthesise", _synthesise_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "rerank")
    graph.add_conditional_edges(
        "rerank",
        _decide_after_rerank,
        {"reformulate": "reformulate", "synthesise": "synthesise"},
    )
    graph.add_edge("reformulate", "retrieve")
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
    reformulate_threshold: float = DEFAULT_REFORMULATE_THRESHOLD,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> PipelineResult:
    final_state = _get_graph().invoke(
        {
            "original_query": query,
            "query": query,
            "iterations": 0,
            "retrieve_k": retrieve_k,
            "rerank_n": rerank_n,
            "mode": mode,
            "doc_types": doc_types,
            "score_threshold": score_threshold,
            "use_mmr": use_mmr,
            "mmr_lambda": mmr_lambda,
            "reformulate_threshold": reformulate_threshold,
            "max_retries": max_retries,
        }
    )
    return PipelineResult(
        answer=final_state["answer"],
        retrieved=final_state["retrieved"],
        reranked=final_state["reranked"],
        iterations=final_state.get("iterations", 0),
    )
