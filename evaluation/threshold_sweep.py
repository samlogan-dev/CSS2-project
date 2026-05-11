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
