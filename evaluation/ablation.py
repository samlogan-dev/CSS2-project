"""
ablation.py — Sweep RETRIEVE_K and report retrieval quality as a function of K.

Directly addresses reviewer feedback that "top-20 contains too much information".
For each K in K_GRID, we run the chain and agentic pipelines (which actually
use RETRIEVE_K → reranker → top-5) and report NDCG@5, MRR, P@5, R@5, MAP.

If the curve plateaus before 20 we have an empirical reason to drop it; if it
keeps climbing past 20 we have an empirical reason to defend it.

Usage:
    python evaluation/ablation.py
    python evaluation/ablation.py --write-results
"""

import argparse
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines import rag_chain, agentic
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

K_GRID = [3, 5, 10, 15, 20, 30, 50]
RERANK_N = 5
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "ablation_results.json")

# Each entry: (label, callable accepting query + retrieve_k -> PipelineResult)
PIPELINES_TO_SWEEP = {
    "chain":    lambda q, k: rag_chain.run(q, retrieve_k=k, rerank_n=RERANK_N),
    "agentic":  lambda q, k: agentic.run(q, retrieve_k=k, rerank_n=RERANK_N),
}


def _evaluate_one(pipeline_fn, queries: list[dict]) -> dict:
    metrics = {"ndcg@5": [], "mrr": [], "precision@5": [], "recall@5": [], "map": [], "elapsed_s": []}
    for q in queries:
        expected = set(q["expected_doc_ids"])
        t0 = time.perf_counter()
        result = pipeline_fn(q["query"])
        elapsed = time.perf_counter() - t0
        reranked = result.reranked
        metrics["ndcg@5"].append(ndcg_at_k(reranked, expected, K_NDCG))
        metrics["mrr"].append(reciprocal_rank(reranked, expected))
        metrics["precision@5"].append(precision_at_k(reranked, expected, K_PRECISION))
        metrics["recall@5"].append(recall_at_k(reranked, expected, K_RECALL))
        metrics["map"].append(average_precision(reranked, expected))
        metrics["elapsed_s"].append(elapsed)
    return {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}


def run_ablation(write_results: bool) -> None:
    queries = load_test_set(TEST_SET_PATH)
    print(f"Loaded {len(queries)} queries — sweeping K over {K_GRID}")

    sweep: dict[str, dict[int, dict]] = {name: {} for name in PIPELINES_TO_SWEEP}

    for name, runner in PIPELINES_TO_SWEEP.items():
        print(f"\n=== Pipeline: {name} ===")
        for K in K_GRID:
            print(f"  K={K:>3}  ", end="", flush=True)
            agg = _evaluate_one(lambda q, k=K, r=runner: r(q, k), queries)
            sweep[name][K] = agg
            print(
                f"ndcg={agg['ndcg@5']:.3f}  mrr={agg['mrr']:.3f}  "
                f"p@5={agg['precision@5']:.3f}  r@5={agg['recall@5']:.3f}  "
                f"map={agg['map']:.3f}  time={agg['elapsed_s']:.2f}s"
            )

    # Print a compact summary table per pipeline
    for name, by_k in sweep.items():
        print(f"\n{name.upper()} — metric vs K")
        print(f"{'K':>4} {'NDCG@5':>9} {'MRR':>7} {'P@5':>7} {'R@5':>7} {'MAP':>7} {'time(s)':>9}")
        print("-" * 56)
        for K in K_GRID:
            r = by_k[K]
            print(
                f"{K:>4} {r['ndcg@5']:>9.3f} {r['mrr']:>7.3f} "
                f"{r['precision@5']:>7.3f} {r['recall@5']:>7.3f} "
                f"{r['map']:>7.3f} {r['elapsed_s']:>9.2f}"
            )

    if write_results:
        # JSON keys must be strings.
        serialised = {
            name: {str(K): vals for K, vals in by_k.items()}
            for name, by_k in sweep.items()
        }
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"k_grid": K_GRID, "rerank_n": RERANK_N, "results": serialised}, f, indent=2)
        print(f"\nAblation results written to {RESULTS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep RETRIEVE_K and report retrieval metrics.")
    parser.add_argument("--write-results", action="store_true",
                        help="Write the sweep to evaluation/ablation_results.json")
    args = parser.parse_args()
    run_ablation(write_results=args.write_results)


if __name__ == "__main__":
    main()
