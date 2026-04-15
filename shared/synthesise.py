"""
synthesise.py — Build a grounded prompt from retrieved chunks and call Claude.

Shared by all three pipelines.
"""

import os
from dataclasses import dataclass

from anthropic import Anthropic

from shared.retrieve import RetrievedChunk

CLAUDE_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about an organisation's "
    "internal documentation. Answer using only the provided context. "
    "If the context does not contain the answer, say so plainly. "
    "Cite sources inline using the format [source_filename]."
)

USER_TEMPLATE = """Context:
{context}

Question: {query}

Answer the question using only the context above. Cite sources inline as [filename]."""


@dataclass
class Answer:
    text: str
    sources: list[str]


_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(f"[{chunk.source}]\n{chunk.text}")
    return "\n\n---\n\n".join(blocks)


def synthesise(query: str, chunks: list[RetrievedChunk]) -> Answer:
    """Build a grounded prompt and return Claude's answer with source references."""
    client = _get_client()

    context = _format_context(chunks)
    user_message = USER_TEMPLATE.format(context=context, query=query)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")

    seen: set[str] = set()
    sources: list[str] = []
    for chunk in chunks:
        if chunk.source not in seen:
            seen.add(chunk.source)
            sources.append(chunk.source)

    return Answer(text=text, sources=sources)
