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
python main.py evaluate --write-results                  # also save per-query results to JSON
```

The `query` command prints the answer, cited sources, the final ranked chunks with relevance scores, and (for `agentic`) how many reformulation iterations were used.

## Evaluation Metrics

All metrics are computed on each pipeline's **final reranked list** — the 5 chunks that are actually passed to the LLM for synthesis.

- **NDCG@5** — ranking quality (ideal DCG is the DCG of the observed relevance vector sorted descending)
- **MRR** — reciprocal rank of the first relevant chunk
- **Precision@5** — fraction of the top 5 chunks whose source is in the query's `expected_doc_ids`

A chunk is considered "relevant" iff its source file appears in the query's `expected_doc_ids`.

Results are printed as an overall side-by-side table plus a per-difficulty breakdown (easy / medium / hard) and are optionally saved to `evaluation/results.json` via `--write-results`.

## Test Set

`evaluation/test_set.json` contains 26 manually authored queries:

- **10 easy** — single-doc factual lookups (e.g. "How many days of paid annual leave do full-time employees get?")
- **10 medium** — queries where the correct document must be selected from several plausible candidates
- **6 hard** — multi-doc synthesis queries whose answer spans two or more source files

Each entry has `id`, `difficulty`, `query`, `expected_doc_ids`, and a human-readable `ground_truth_answer`.

## Repo Layout

```
CSS2-project/
├── docs/                  # enterprise knowledge base (markdown)
├── ingest.py              # chunk + embed docs → ChromaDB
├── chroma_db/             # persisted vector store (built by ingest)
├── shared/
│   ├── retrieve.py        # ChromaDB vector search
│   ├── rerank.py          # cross-encoder re-ranking
│   └── synthesise.py      # Claude API call
├── pipelines/
│   ├── naive.py           # Pipeline 1: plain Python
│   ├── rag_chain.py       # Pipeline 2: LangGraph linear
│   └── agentic.py         # Pipeline 3: LangGraph + reformulation loop
├── evaluation/
│   ├── test_set.json      # 26 query entries
│   └── evaluate.py        # runs all pipelines + computes metrics
├── main.py                # CLI entry point
└── requirements.txt
```

## Requirements

- Python 3.10+
- `ANTHROPIC_API_KEY` env var
- Everything runs locally except Claude API calls
