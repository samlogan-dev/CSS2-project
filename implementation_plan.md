# Implementation Plan

> **Status:** All five phases are complete. This document is the original plan preserved for reference, annotated with what was actually built.

## Overview

Build a single Python repository with one shared knowledge base and test set, then run the same queries through three pipelines of increasing complexity to compare retrieval and answer quality.

**Research question:** Does adding agentic complexity (re-ranking, query reformulation, conditional routing) meaningfully improve retrieval quality over simpler approaches?

---

## The Three Pipelines

### Pipeline 1: Naive RAG (no framework)
- Plain Python — no LangGraph, no LangChain
- Embed query → ChromaDB similarity search → top-k chunks straight into Claude prompt → answer
- ~30 lines of code. The control group.

### Pipeline 2: RAG Chain (LangGraph, linear)
- LangGraph with a simple linear graph: `retrieve → rerank → synthesise`
- Adds a cross-encoder re-ranking step between retrieval and synthesis
- Still a straight line — no loops, no decisions

### Pipeline 3: Agentic RAG (LangGraph, with routing)
- LangGraph with conditional edges
- Same as Pipeline 2, but: if the re-ranker confidence is low, reformulate the query and retry (max 2 retries)
- Adds a relevance check node that decides whether to loop or proceed
- This is the "agentic" part — the system makes decisions instead of blindly proceeding

### What stays the same across all three
- Same ChromaDB vector store + embeddings
- Same document corpus
- Same Claude API call for synthesis (same model, same system prompt)
- Same test set and evaluation metrics

---

## Repo Structure (as built)

```
CSS2-project/
├── docs/                        # enterprise knowledge base (markdown)
│   ├── policy-leave.md
│   ├── policy-remote-work.md
│   ├── policy-expenses.md
│   ├── policy-code-of-conduct.md
│   ├── policy-budget.md
│   ├── runbook-deploy.md
│   ├── runbook-incident-response.md
│   ├── runbook-database-backup.md
│   ├── guide-onboarding.md
│   ├── guide-it-setup.md
│   ├── faq-hr.md
│   ├── faq-it.md
│   ├── faq-finance.md
│   ├── faq-legal.md
│   ├── brief-project-atlas.md
│   ├── brief-project-sentinel.md
│   ├── brief-project-nova.md
│   ├── brief-project-meridian.md
│   └── brief-project-compass.md
├── ingest.py                    # chunk + embed docs → ChromaDB
├── chroma_db/                   # persisted vector store (built by ingest)
├── pipelines/
│   ├── naive.py                 # Pipeline 1: vector search → LLM
│   ├── rag_chain.py             # Pipeline 2: retrieve → rerank → synthesise (LangGraph)
│   └── agentic.py               # Pipeline 3: Pipeline 2 + reformulation loop (LangGraph)
├── shared/
│   ├── retrieve.py              # ChromaDB vector search (shared by all pipelines)
│   ├── rerank.py                # cross-encoder re-ranking (Pipelines 2 & 3)
│   └── synthesise.py            # Claude API call (shared by all pipelines)
├── evaluation/
│   ├── test_set.json            # 26 manually authored query entries
│   ├── evaluate.py              # runs all 3 pipelines, computes metrics, outputs comparison
│   └── results.json             # full per-query results (written by --write-results)
├── main.py                      # CLI entry point
├── requirements.txt
└── README.md
```

---

## Phase 1: Knowledge Base + Ingestion ✓ done

**Goal:** Create the document corpus and embed it into ChromaDB.

### 1.1 — Create `docs/`
- Write 10–15 sample enterprise documents (markdown)
- Types: HR policies, technical runbooks, onboarding guides, IT FAQs, project briefs
- 300–800 words each — long enough to require chunking
- Include some cross-referencing between docs (e.g. an FAQ that references a policy) to test multi-doc queries

### 1.2 — Implement `ingest.py`
- Load all `.md` files from `docs/`
- Chunk with a simple recursive character splitter (~500 chars, ~50 overlap)
- Embed with `sentence-transformers` (`all-MiniLM-L6-v2`)
- Store in a local ChromaDB collection with metadata (source file, chunk index)
- Idempotent — clears and rebuilds on each run

---

## Phase 2: Shared Components ✓ done

**Goal:** Build the retrieval, re-ranking, and synthesis functions that the pipelines share.

### 2.1 — `shared/retrieve.py`
- Query ChromaDB with an embedded query
- Return top-k chunks (default k=20) with scores and metadata

### 2.2 — `shared/rerank.py`
- Score query–chunk pairs with `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Return top-n (default n=5) sorted by relevance score

### 2.3 — `shared/synthesise.py`
- Build a grounded prompt: context chunks + query → Claude (`claude-haiku-4-5`)
- Return the answer and source references
- Same prompt template used by all three pipelines

---

## Phase 3: Pipelines ✓ done

**Goal:** Implement the three pipelines using the shared components.

### 3.1 — `pipelines/naive.py` (Pipeline 1)
- Plain Python function, no framework
- `retrieve(query, k=5) → synthesise(query, chunks) → answer`
- No re-ranking — just takes the top 5 from vector search directly

### 3.2 — `pipelines/rag_chain.py` (Pipeline 2)
- LangGraph linear graph: `retrieve → rerank → synthesise`
- Define state schema, three nodes, two edges
- No conditional logic — always runs the full chain

### 3.3 — `pipelines/agentic.py` (Pipeline 3)
- LangGraph graph with a conditional edge after re-ranking
- Adds a `check_relevance` node: if the top re-ranked chunk score < threshold, reformulate the query (via Claude) and loop back to retrieve
- Max 2 retries before proceeding with best available results
- Tracks iteration count in state

---

## Phase 4: Evaluation ✓ done

**Goal:** Build a test set and run all three pipelines through it.

### 4.1 — `evaluation/test_set.json`
- **26** manually authored query entries (10 easy, 10 medium, 6 hard)
- Each entry: `{ "id", "difficulty", "query", "expected_doc_ids", "ground_truth_answer" }`
- Easy = single-doc factual; medium = correct doc selection required; hard = multi-doc synthesis

### 4.2 — `evaluation/evaluate.py`
- For each query, runs all three pipelines
- Computes metrics on each pipeline's **final reranked list** (the 5 chunks that reach the LLM):
  - **NDCG@5** — ranking quality (ideal DCG = observed relevance vector sorted descending)
  - **MRR** — reciprocal rank of the first relevant chunk
  - **Precision@5** — fraction of top 5 whose source is in `expected_doc_ids`
- A chunk is "relevant" iff its `source` is in `expected_doc_ids`
- Prints an overall side-by-side table plus per-difficulty breakdown
- `--write-results` writes full per-query results to `evaluation/results.json`

> Note: the original plan specified NDCG@10. All pipelines return exactly 5 chunks to synthesis, so NDCG@10 reduces to NDCG@5 — renamed to be accurate.

---

## Phase 5: CLI + Packaging ✓ done

### 5.1 — `main.py`
```
python main.py ingest                                    # build the vector store
python main.py query "question" --pipeline naive|chain|agentic
python main.py evaluate [--write-results]                # run all pipelines on test set
```

The `query` subcommand prints the answer, source list, the final ranked chunks with scores, and (for `agentic`) the reformulation iteration count.

### 5.2 — `requirements.txt`
```
langgraph
langchain-core
chromadb
sentence-transformers
anthropic
python-dotenv
```

---

## Build Order

```
Phase 1 (docs + ingest)      ✓ done
    ↓
Phase 2 (shared components)  ✓ done
    ↓
Phase 3 (three pipelines)    ✓ done
    ↓
Phase 4 (evaluation)         ✓ done
    ↓
Phase 5 (CLI)                ✓ done
```

---

## Dependencies

- Python 3.10+
- `ANTHROPIC_API_KEY` env var
- Everything runs locally except Claude API calls
- No Docker, no external databases, no config files
