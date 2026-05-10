"""
threshold_sweep.py — Sweep the agentic reformulation threshold τ.

Directly addresses tutor feedback that the threshold was hardcoded to 0.0
without justification. For each τ in TAU_GRID we run the agentic pipeline
on the full test set and report:
    NDCG@5 / MRR / P@5 / R@5  (retrieval quality)
    avg iters                  (how often reformulation fires)
    n_fired                    (count of queries where iters >= 1)
    avg latency                (wall-clock per query)

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
    load_test_set,
    ndcg_at_k,
    reciprocal_rank,
    precision_at_k,
    recall_at_k,
    average_precision,
    K_NDCG, K_PRECISION, K_RECALL,
    TEST_SET_PATH,
)

TAU_GRID = [0.0, 0.5, 1.0, 2.0, 3.0]
RETRIEVE_K = 20
RERANK_N = 5
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "threshold_sweep_results.json")


def _evaluate_one(tau: float, queries: list[dict]) -> dict:
    metrics = {"ndcg@5": [], "mrr": [], "precision@5": [], "recall@5": [], "map": []}
    iters = []
    elapsed = []
    fired = 0
    for q in queries:
        expected = set(q["expected_doc_ids"])
        t0 = time.perf_counter()
        result = agentic.run(
            q["query"],
            retrieve_k=RETRIEVE_K,
            rerank_n=RERANK_N,
            reformulate_threshold=tau,
        )
        elapsed.append(time.perf_counter() - t0)
        reranked = result.reranked
        metrics["ndcg@5"].append(ndcg_at_k(reranked, expected, K_NDCG))
        metrics["mrr"].append(reciprocal_rank(reranked, expected))
        metrics["precision@5"].append(precision_at_k(reranked, expected, K_PRECISION))
        metrics["recall@5"].append(recall_at_k(reranked, expected, K_RECALL))
        metrics["map"].append(average_precision(reranked, expected))
        iters.append(result.iterations)
        if result.iterations >= 1:
            fired += 1
    n = len(queries)
    return {
        "ndcg@5": sum(metrics["ndcg@5"]) / n,
        "mrr": sum(metrics["mrr"]) / n,
        "precision@5": sum(metrics["precision@5"]) / n,
        "recall@5": sum(metrics["recall@5"]) / n,
        "map": sum(metrics["map"]) / n,
        "avg_iters": sum(iters) / n,
        "n_fired": fired,
        "avg_elapsed_s": sum(elapsed) / n,
    }


def run_threshold_sweep(write_results: bool) -> None:
    queries = load_test_set(TEST_SET_PATH)
    print(f"Loaded {len(queries)} queries — sweeping τ over {TAU_GRID}")

    rows = {}
    for tau in TAU_GRID:
        print(f"\n=== τ = {tau} ===")
        agg = _evaluate_one(tau, queries)
        rows[tau] = agg
        print(
            f"  ndcg={agg['ndcg@5']:.3f}  mrr={agg['mrr']:.3f}  "
            f"p@5={agg['precision@5']:.3f}  r@5={agg['recall@5']:.3f}  "
            f"map={agg['map']:.3f}  iters={agg['avg_iters']:.2f}  "
            f"fired={agg['n_fired']}/{len(queries)}  time={agg['avg_elapsed_s']:.2f}s"
        )

    print("\nThreshold sweep — metric vs τ")
    print(f"{'τ':>5} {'NDCG@5':>9} {'MRR':>7} {'P@5':>7} {'R@5':>7} {'MAP':>7} "
          f"{'iters':>7} {'fired':>7} {'time(s)':>9}")
    print("-" * 70)
    for tau in TAU_GRID:
        r = rows[tau]
        print(
            f"{tau:>5.1f} {r['ndcg@5']:>9.3f} {r['mrr']:>7.3f} "
            f"{r['precision@5']:>7.3f} {r['recall@5']:>7.3f} {r['map']:>7.3f} "
            f"{r['avg_iters']:>7.2f} {r['n_fired']:>7d} {r['avg_elapsed_s']:>9.2f}"
        )

    if write_results:
        out = {str(tau): vals for tau, vals in rows.items()}
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"tau_grid": TAU_GRID, "retrieve_k": RETRIEVE_K,
                       "rerank_n": RERANK_N, "results": out}, f, indent=2)
        print(f"\nThreshold sweep written to {RESULTS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep the agentic reformulation threshold.")
    parser.add_argument("--write-results", action="store_true",
                        help="Write the sweep to evaluation/threshold_sweep_results.json")
    args = parser.parse_args()
    run_threshold_sweep(write_results=args.write_results)


if __name__ == "__main__":
    main()
