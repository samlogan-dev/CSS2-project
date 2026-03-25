# RAG Pipeline Comparison

**Research question:** Does adding agentic complexity (re-ranking, query reformulation, conditional routing) meaningfully improve retrieval quality over simpler approaches?

## The Three Pipelines

| Pipeline | Description |
|----------|-------------|
| **Naive RAG** | Vector search → top-k chunks → Claude. Plain Python, no framework. |
| **RAG Chain** | LangGraph linear graph: retrieve → rerank → synthesise. |
| **Agentic RAG** | RAG Chain + conditional loop: if relevance is low, reformulate the query and retry (max 2 retries). |

All three pipelines share the same ChromaDB vector store, document corpus, Claude model, and evaluation set.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
python main.py ingest                                    # build the vector store
python main.py query "your question" --pipeline naive    # naive | chain | agentic
python main.py evaluate                                  # run all pipelines on the test set
```

## Evaluation Metrics

- **NDCG@10** — ranking quality
- **MRR** — position of first relevant result
- **Precision@5** — fraction of top 5 that are relevant

Results are printed as a side-by-side comparison table and optionally saved to `evaluation/results.json`.

## Requirements

- Python 3.10+
- `ANTHROPIC_API_KEY` env var
- Everything runs locally except Claude API calls
