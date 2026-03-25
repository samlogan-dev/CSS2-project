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

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone and enter the repo

```bash
git clone <repo-url>
cd CSS2-project
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> First install may take a few minutes — `sentence-transformers` downloads the embedding model (~90 MB) on first use.

### 4. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your real key:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 5. Build the vector store

```bash
python main.py ingest
```

This loads all documents from `docs/`, chunks and embeds them, and writes the ChromaDB index to `chroma_db/`. You only need to run this once (or again if `docs/` changes).

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
