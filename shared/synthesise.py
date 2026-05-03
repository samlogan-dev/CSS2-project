"""
synthesise.py — Build a grounded prompt from retrieved chunks and call OpenAI.

Shared by all three pipelines. Returns an Answer including token usage so the
evaluation harness can report cost-per-query.
"""

import os
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

from shared.retrieve import RetrievedChunk

load_dotenv()

OPENAI_MODEL = "gpt-4o"
MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about an organisation's "
    "internal documentation. Answer using only the provided context. "
    "If the context does not contain the answer, say so plainly. "
    "Cite sources inline using the format [source_filename]. "
    "Write in plain English — avoid jargon, define any acronyms on first use, "
    "and keep the answer concise."
)

USER_TEMPLATE = """Context:
{context}

Question: {query}

Answer the question using only the context above. Cite sources inline as [filename]."""


@dataclass
class Answer:
    text: str
    sources: list[str]
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = OPENAI_MODEL


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _format_context(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(f"[{chunk.source}]\n{chunk.text}")
    return "\n\n---\n\n".join(blocks)


def synthesise(query: str, chunks: list[RetrievedChunk]) -> Answer:
    """Build a grounded prompt and return GPT-4o's answer with source references."""
    client = _get_client()

    context = _format_context(chunks)
    user_message = USER_TEMPLATE.format(context=context, query=query)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    text = response.choices[0].message.content or ""

    seen: set[str] = set()
    sources: list[str] = []
    for chunk in chunks:
        if chunk.source not in seen:
            seen.add(chunk.source)
            sources.append(chunk.source)

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

    return Answer(
        text=text,
        sources=sources,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=OPENAI_MODEL,
    )
