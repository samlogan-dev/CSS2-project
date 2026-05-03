# RAG Pipeline Comparison

**Research question:** Does adding agentic complexity (re-ranking, query reformulation, conditional routing) meaningfully improve retrieval quality over simpler approaches?

## The Three Pipelines

| Pipeline | Description |
|----------|-------------|
| **Naive RAG** | Vector search → top-k chunks → GPT-4o. Plain Python, no framework. |
| **RAG Chain** | LangGraph linear graph: retrieve → rerank → synthesise. |
| **Agentic RAG** | RAG Chain + conditional loop: if relevance is low, reformulate the query and retry (max 2 retries). |

All three pipelines share the same ChromaDB vector store, document corpus, OpenAI model (gpt-4o), and evaluation set.

## Retrieval modes

`shared/retrieve.py` supports three modes (selectable per query / per evaluation):

- **`dense`** — ChromaDB cosine over MiniLM embeddings (default).
- **`bm25`** — Lexical Okapi BM25 over the same chunk corpus.
- **`hybrid`** — Reciprocal Rank Fusion of dense + BM25.

`shared/rerank.py` adds two optional improvements on top of plain top-N:
- **Score threshold** — drop chunks whose cross-encoder score falls below a cutoff (instead of always padding to N).
- **MMR** — Maximal Marginal Relevance selection for diversity, configurable via `mmr_lambda` (1.0 = pure relevance, 0.0 = pure diversity).

## Setup

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

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
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Build the vector store

```bash
python main.py ingest
```

This loads all documents from `docs/`, chunks and embeds them, and writes the ChromaDB index to `chroma_db/`. You only need to run this once (or again if `docs/` changes).

## Usage

```bash
# Build the vector store
python main.py ingest

# Single query (clean output by default; -v shows scores + token usage)
python main.py query "your question" --pipeline agentic
python main.py query "your question" --pipeline chain --mode hybrid -v

# Tune retrieval per call
python main.py query "your question" --pipeline chain --retrieve-k 10 --rerank-n 3 --mmr

# Full evaluation (retrieval metrics + bootstrap CIs + permutation tests)
python main.py evaluate
python main.py evaluate --write-results            # also save JSON
python main.py evaluate --judge --write-results    # add LLM-as-judge answer scoring

# Top-K ablation — sweep RETRIEVE_K and report metrics as a function of K
python main.py ablate --write-results
```

The `query` command prints just the answer + sources by default. Pass `-v` / `--verbose` to also see the final ranked chunks, scores, and token counts.

## Evaluation Metrics

All metrics are computed on each pipeline's **final reranked list** — the chunks actually passed to the LLM for synthesis.

- **NDCG@5** — ranking quality
- **MRR** — reciprocal rank of the first relevant chunk
- **Precision@5** — fraction of the top 5 whose source is in `expected_doc_ids`
- **Recall@5** — fraction of expected documents covered within the top 5
- **MAP** — mean average precision over the top-5 list

The evaluation harness also reports:
- **95% bootstrap CIs** around every per-pipeline mean (`n=1000` resamples).
- **Paired permutation p-values** for every pipeline pair on every metric — so you can claim "agentic > chain on NDCG@5 at p=0.03" rather than just "0.04 higher".
- **Average input/output tokens per query** (proxy for $ cost).
- **Average wall-clock latency per query.**
- **LLM-as-judge answer score (1–5)** when `--judge` is passed — uses GPT-4o to grade each answer against the ground truth, so you can measure whether better retrieval actually produces better answers, not just better-ranked chunks.

A chunk is "relevant" iff its source file appears in the query's `expected_doc_ids`.

## Ablations

`python main.py ablate` sweeps `RETRIEVE_K ∈ {3, 5, 10, 15, 20, 30, 50}` for the chain and agentic pipelines and reports every retrieval metric at each setting plus average latency. The output makes the cost / quality trade-off explicit and provides empirical justification for the chosen `RETRIEVE_K`.

## Test Set

`evaluation/test_set.json` contains 26 manually authored queries:

- **10 easy** — single-doc factual lookups
- **10 medium** — queries where the correct document must be selected from several plausible candidates
- **6 hard** — multi-doc synthesis queries whose answer spans two or more source files

Each entry has `id`, `difficulty`, `query`, `expected_doc_ids`, and a human-readable `ground_truth_answer` (used by the optional `--judge` evaluation).

## Repo Layout

```
CSS2-project/
├── docs/                  # enterprise knowledge base (markdown)
├── ingest.py              # chunk + embed docs → ChromaDB
├── chroma_db/             # persisted vector store (built by ingest)
├── shared/
│   ├── retrieve.py        # dense / BM25 / hybrid retrieval
│   ├── rerank.py          # cross-encoder + optional MMR + score threshold
│   └── synthesise.py      # OpenAI API call (returns token usage)
├── pipelines/
│   ├── naive.py           # Pipeline 1: plain Python
│   ├── rag_chain.py       # Pipeline 2: LangGraph linear
│   └── agentic.py         # Pipeline 3: LangGraph + reformulation loop
├── evaluation/
│   ├── test_set.json      # 26 query entries
│   ├── evaluate.py        # main eval harness (CIs, significance, judge, cost)
│   └── ablation.py        # RETRIEVE_K sweep
├── main.py                # CLI entry point
└── requirements.txt
```

## Requirements

- Python 3.10+
- `OPENAI_API_KEY` env var
- Everything runs locally except OpenAI API calls
