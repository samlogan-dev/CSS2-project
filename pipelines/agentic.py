"""
agentic.py — Pipeline 3.

LangGraph graph with conditional edges.
Same as Pipeline 2, but: if the top re-ranked chunk score < threshold,
reformulate the query via Claude and retry. Max 2 retries.
"""

import os
from dataclasses import dataclass
from typing import TypedDict

from anthropic import Anthropic
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from shared.retrieve import retrieve, RetrievedChunk
from shared.rerank import rerank
from shared.synthesise import synthesise, Answer

load_dotenv()

RETRIEVE_K = 20
RERANK_N = 5
SCORE_THRESHOLD = 0.0
MAX_RETRIES = 2
REFORMULATE_MODEL = "claude-haiku-4-5"

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


@dataclass
class PipelineResult:
    answer: Answer
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    iterations: int


_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _reformulate(original_query: str) -> str:
    print(f"[Agentic] Reformulating query: '{original_query}'")
    client = _get_client()
    response = client.messages.create(
        model=REFORMULATE_MODEL,
        max_tokens=256,
        system=REFORMULATE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": REFORMULATE_USER.format(query=original_query),
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    new_query = text.strip().splitlines()[0] if text.strip() else original_query
    print(f"[Agentic] New query generated: '{new_query}'")
    return new_query


def _retrieve_node(state: AgenticState) -> AgenticState:
    return {"retrieved": retrieve(state["query"], k=RETRIEVE_K)}


def _rerank_node(state: AgenticState) -> AgenticState:
    return {"reranked": rerank(state["query"], state["retrieved"], n=RERANK_N)}


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

    if not reranked:
        print("[Router] No chunks retrieved. Routing to Synthesise.")
        return "synthesise"

    top_score = reranked[0].score
    print(f"[Router] Iteration {iterations} | Top Rerank Score: {top_score:.3f} | Threshold: {SCORE_THRESHOLD}")

    if top_score >= SCORE_THRESHOLD:
        print("[Router] Confidence threshold met. Routing to Synthesise.")
        return "synthesise"
    if iterations >= MAX_RETRIES:
        print(f"[Router] Max retries ({MAX_RETRIES}) reached. Routing to Synthesise.")
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


def run(query: str) -> PipelineResult:
    final_state = _get_graph().invoke(
        {
            "original_query": query,
            "query": query,
            "iterations": 0,
        }
    )
    return PipelineResult(
        answer=final_state["answer"],
        retrieved=final_state["retrieved"],
        reranked=final_state["reranked"],
        iterations=final_state.get("iterations", 0),
    )
