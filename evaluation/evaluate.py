"""
evaluate.py — Run all three pipelines on the test set and compare retrieval quality.

Metrics (computed on each pipeline's final ranked list — the chunks that are
actually passed to the LLM for synthesis):

    NDCG@5       — ranking quality
    MRR          — reciprocal rank of the first relevant chunk
    Precision@5  — fraction of the top 5 chunks that are from an expected doc

A chunk is "relevant" if its source file is in the query's expected_doc_ids.

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --write-results
"""

import argparse
import json
import math
import os
import sys
import time

# Allow running from project root or evaluation/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines import naive, rag_chain, agentic
from shared.retrieve import RetrievedChunk

TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_set.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")

PIPELINES = {
    "naive": naive.run,
    "chain": rag_chain.run,
    "agentic": agentic.run,
}

K_PRECISION = 5
K_NDCG = 5


def load_test_set(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["queries"]


def _relevance_vector(chunks: list[RetrievedChunk], expected: set[str]) -> list[int]:
    return [1 if c.source in expected else 0 for c in chunks]


def precision_at_k(chunks: list[RetrievedChunk], expected: set[str], k: int) -> float:
    if not chunks:
        return 0.0
    top = chunks[:k]
    hits = sum(1 for c in top if c.source in expected)
    return hits / k


def reciprocal_rank(chunks: list[RetrievedChunk], expected: set[str]) -> float:
    for i, chunk in enumerate(chunks, start=1):
        if chunk.source in expected:
            return 1.0 / i
    return 0.0


def ndcg_at_k(chunks: list[RetrievedChunk], expected: set[str], k: int) -> float:
    """
    NDCG@k with binary relevance. The ideal DCG is the DCG of the same
    relevance vector sorted descending — i.e., the best possible ranking of
    the observed hits.
    """
    rels = _relevance_vector(chunks[:k], expected)
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(rels))
    ideal_rels = sorted(rels, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_rels))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_query(pipeline_fn, query_entry: dict) -> dict:
    query = query_entry["query"]
    expected = set(query_entry["expected_doc_ids"])

    t0 = time.perf_counter()
    result = pipeline_fn(query)
    elapsed = time.perf_counter() - t0

    reranked = result.reranked

    return {
        "id": query_entry["id"],
        "difficulty": query_entry["difficulty"],
        "query": query,
        "expected_doc_ids": sorted(expected),
        "retrieved_sources": [c.source for c in reranked],
        "top_scores": [round(c.score, 3) for c in reranked],
        "iterations": result.iterations,
        "elapsed_s": round(elapsed, 2),
        "metrics": {
            "ndcg@5": ndcg_at_k(reranked, expected, K_NDCG),
            "mrr": reciprocal_rank(reranked, expected),
            "precision@5": precision_at_k(reranked, expected, K_PRECISION),
        },
    }


def aggregate(per_query: list[dict]) -> dict:
    n = len(per_query)
    if n == 0:
        return {"ndcg@5": 0.0, "mrr": 0.0, "precision@5": 0.0, "avg_iterations": 0.0, "avg_elapsed_s": 0.0}
    return {
        "ndcg@5": sum(r["metrics"]["ndcg@5"] for r in per_query) / n,
        "mrr": sum(r["metrics"]["mrr"] for r in per_query) / n,
        "precision@5": sum(r["metrics"]["precision@5"] for r in per_query) / n,
        "avg_iterations": sum(r["iterations"] for r in per_query) / n,
        "avg_elapsed_s": sum(r["elapsed_s"] for r in per_query) / n,
    }


def aggregate_by_difficulty(per_query: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = {}
    for r in per_query:
        buckets.setdefault(r["difficulty"], []).append(r)
    return {difficulty: aggregate(items) for difficulty, items in buckets.items()}


def print_summary_table(summaries: dict) -> None:
    header = f"{'pipeline':<10} {'NDCG@5':>8} {'MRR':>8} {'P@5':>8} {'avg iters':>10} {'avg time':>10}"
    print()
    print("=" * len(header))
    print("OVERALL")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for name, summary in summaries.items():
        overall = summary["overall"]
        print(
            f"{name:<10} "
            f"{overall['ndcg@5']:>8.3f} "
            f"{overall['mrr']:>8.3f} "
            f"{overall['precision@5']:>8.3f} "
            f"{overall['avg_iterations']:>10.2f} "
            f"{overall['avg_elapsed_s']:>9.2f}s"
        )

    # Per-difficulty breakdown
    all_difficulties: set[str] = set()
    for summary in summaries.values():
        all_difficulties.update(summary["by_difficulty"].keys())

    for difficulty in sorted(all_difficulties):
        print()
        print("=" * len(header))
        print(f"BY DIFFICULTY: {difficulty}")
        print("=" * len(header))
        print(header)
        print("-" * len(header))
        for name, summary in summaries.items():
            bucket = summary["by_difficulty"].get(difficulty)
            if bucket is None:
                continue
            print(
                f"{name:<10} "
                f"{bucket['ndcg@5']:>8.3f} "
                f"{bucket['mrr']:>8.3f} "
                f"{bucket['precision@5']:>8.3f} "
                f"{bucket['avg_iterations']:>10.2f} "
                f"{bucket['avg_elapsed_s']:>9.2f}s"
            )
    print()


def run_evaluation(write_results: bool) -> None:
    queries = load_test_set(TEST_SET_PATH)
    print(f"Loaded {len(queries)} queries from {TEST_SET_PATH}")

    summaries: dict[str, dict] = {}

    for name, pipeline_fn in PIPELINES.items():
        print(f"\nRunning pipeline: {name}")
        per_query = []
        for i, q in enumerate(queries, start=1):
            print(f"  [{i:>2}/{len(queries)}] {q['id']} ({q['difficulty']}) ", end="", flush=True)
            result = evaluate_query(pipeline_fn, q)
            per_query.append(result)
            m = result["metrics"]
            print(
                f"ndcg={m['ndcg@5']:.2f} mrr={m['mrr']:.2f} "
                f"p@5={m['precision@5']:.2f} iters={result['iterations']} "
                f"{result['elapsed_s']:.1f}s"
            )
        summaries[name] = {
            "overall": aggregate(per_query),
            "by_difficulty": aggregate_by_difficulty(per_query),
            "per_query": per_query,
        }

    print_summary_table(summaries)

    if write_results:
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)
        print(f"Results written to {RESULTS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG pipelines on the test set.")
    parser.add_argument(
        "--write-results",
        action="store_true",
        help="Write full per-query results to evaluation/results.json",
    )
    args = parser.parse_args()
    run_evaluation(write_results=args.write_results)


if __name__ == "__main__":
    main()
