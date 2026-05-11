# Task 3 Code Changes

Two pieces of new work, in priority order. Both address specific feedback received on the Task 2 submission.

---

## 1. Threshold Sweep (Priority: High)

**Why:** The feedback asked "What is the actual threshold, and how did you determine it?" The answer currently is that τ = 0.0 was chosen as the natural decision boundary for the ms-marco cross-encoder (scores above 0 indicate positive relevance; below 0 indicates the model considers the passage non-relevant). However, we need to empirically validate this by sweeping over threshold values and showing that 0.0 is a reasonable choice.

**What to build:** A new script `evaluation/threshold_sweep.py` that runs the agentic pipeline with multiple threshold values and reports metrics for each.

### Step 1 — Modify `pipelines/agentic.py` to accept a threshold parameter

Add `score_threshold` as an optional field in `AgenticState` and read it in `_decide_after_rerank`. This avoids rebuilding the graph for each threshold — the decision function reads from state dynamically.

```python
# AgenticState — add one field:
class AgenticState(TypedDict, total=False):
    original_query: str
    query: str
    retrieved: list[RetrievedChunk]
    reranked: list[RetrievedChunk]
    answer: Answer
    iterations: int
    score_threshold: float   # ← ADD THIS

# _decide_after_rerank — read threshold from state with fallback:
def _decide_after_rerank(state: AgenticState) -> str:
    reranked = state.get("reranked", [])
    iterations = state.get("iterations", 0)
    threshold = state.get("score_threshold", SCORE_THRESHOLD)  # ← USE STATE VALUE

    if not reranked:
        return "synthesise"
    top_score = reranked[0].score
    if top_score >= threshold:
        return "synthesise"
    if iterations >= MAX_RETRIES:
        return "synthesise"
    return "reformulate"

# run() — accept and pass through threshold:
def run(query: str, score_threshold: float = SCORE_THRESHOLD) -> PipelineResult:
    final_state = _get_graph().invoke(
        {
            "original_query": query,
            "query": query,
            "iterations": 0,
            "score_threshold": score_threshold,   # ← ADD THIS
        }
    )
    return PipelineResult(
        answer=final_state["answer"],
        retrieved=final_state["retrieved"],
        reranked=final_state["reranked"],
        iterations=final_state.get("iterations", 0),
    )
```

The default value (`SCORE_THRESHOLD = 0.0`) is unchanged, so existing code that calls `agentic.run(query)` without a threshold argument continues to work as before.

### Step 2 — Create `evaluation/threshold_sweep.py`

This script sweeps the threshold over `[-10.0, -5.0, -2.0, 0.0, 2.0, 5.0]`, runs the agentic pipeline on all 26 queries for each threshold, and computes aggregate metrics.

```python
"""
threshold_sweep.py — Sweep SCORE_THRESHOLD for the agentic pipeline.

Runs the agentic pipeline on all 26 test queries for each threshold value
and reports NDCG@5, MRR, Precision@5, avg reformulations, and avg latency.

Usage:
    python evaluation/threshold_sweep.py
    python evaluation/threshold_sweep.py --write-results
"""

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines import agentic
from evaluation.evaluate import (
    load_test_set, ndcg_at_k, reciprocal_rank, precision_at_k, aggregate
)

TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_set.json")
SWEEP_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "threshold_sweep_results.json")

THRESHOLDS = [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0]
K = 5


def run_sweep(write_results: bool) -> None:
    queries = load_test_set(TEST_SET_PATH)
    sweep_results = {}

    for threshold in THRESHOLDS:
        print(f"\nThreshold = {threshold:+.1f}")
        per_query = []
        for q in queries:
            expected = set(q["expected_doc_ids"])
            t0 = time.perf_counter()
            result = agentic.run(q["query"], score_threshold=threshold)
            elapsed = time.perf_counter() - t0
            reranked = result.reranked
            per_query.append({
                "id": q["id"],
                "difficulty": q["difficulty"],
                "metrics": {
                    "ndcg@5": ndcg_at_k(reranked, expected, K),
                    "mrr": reciprocal_rank(reranked, expected),
                    "precision@5": precision_at_k(reranked, expected, K),
                },
                "iterations": result.iterations,
                "elapsed_s": round(elapsed, 2),
            })
            print(f"  {q['id']} iters={result.iterations} {elapsed:.1f}s")

        summary = aggregate(per_query)
        sweep_results[str(threshold)] = {"overall": summary, "per_query": per_query}
        print(
            f"  → NDCG={summary['ndcg@5']:.3f}  MRR={summary['mrr']:.3f}  "
            f"P@5={summary['precision@5']:.3f}  "
            f"avg_reformulations={summary['avg_iterations']:.2f}  "
            f"avg_time={summary['avg_elapsed_s']:.2f}s"
        )

    print("\n\nSUMMARY TABLE")
    print(f"{'threshold':>10} {'NDCG@5':>8} {'MRR':>8} {'P@5':>8} {'avg reform':>12} {'avg time':>10}")
    print("-" * 60)
    for threshold in THRESHOLDS:
        s = sweep_results[str(threshold)]["overall"]
        print(
            f"{threshold:>+10.1f} {s['ndcg@5']:>8.3f} {s['mrr']:>8.3f} "
            f"{s['precision@5']:>8.3f} {s['avg_iterations']:>12.2f} "
            f"{s['avg_elapsed_s']:>9.2f}s"
        )

    if write_results:
        with open(SWEEP_RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(sweep_results, f, indent=2)
        print(f"\nResults written to {SWEEP_RESULTS_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-results", action="store_true")
    args = parser.parse_args()
    run_sweep(write_results=args.write_results)


if __name__ == "__main__":
    main()
```

### Step 3 — Run the sweep and save results

```bash
source venv/bin/activate
python evaluation/threshold_sweep.py --write-results
```

This will create `evaluation/threshold_sweep_results.json` and print a summary table. **Copy the printed summary table into the chat so the paper can be updated.**

---

## 2. Latency Split by Reformulation (Priority: Medium — no new code needed)

**Why:** The feedback noted: "you are averaging out the time penalty for the Agentic call. Claude is only called on maybe 4 of the 26 queries, so the actual time cost for the full agentic procedure would be greater."

The fix is to report latency separately for queries that triggered reformulation vs. those that didn't. This can be computed from `evaluation/results.json` without re-running anything.

Add the following analysis script, or just run it in a Python REPL and report the numbers:

```python
import json

with open("evaluation/results.json") as f:
    results = json.load(f)

agentic_queries = results["agentic"]["per_query"]

reformulated = [q for q in agentic_queries if q["iterations"] > 0]
not_reformulated = [q for q in agentic_queries if q["iterations"] == 0]

def avg_time(qs):
    return sum(q["elapsed_s"] for q in qs) / len(qs)

print(f"Reformulated ({len(reformulated)} queries): avg {avg_time(reformulated):.2f}s")
print(f"Not reformulated ({len(not_reformulated)} queries): avg {avg_time(not_reformulated):.2f}s")
print("Individual reformulated queries:")
for q in reformulated:
    print(f"  {q['id']} ({q['difficulty']}): iters={q['iterations']}, time={q['elapsed_s']}s")
```

**Copy the output of this into the chat so the paper latency section can be updated.**

---

## What NOT to change

- Do not modify `evaluate.py`, `naive.py`, `rag_chain.py`, `shared/`, or `ingest.py`
- Do not re-run the main evaluation (`python main.py evaluate`) — existing `results.json` is the authoritative result
- Do not add BLEU or LLM-as-judge evaluation — out of scope

## Definition of done

1. `pipelines/agentic.py` modified to accept `score_threshold` parameter (default unchanged at 0.0)
2. `evaluation/threshold_sweep.py` created and runnable
3. `evaluation/threshold_sweep_results.json` written after running the sweep
4. Latency split numbers computed and reported in the chat
