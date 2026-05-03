"""
evaluate.py — Run all three pipelines on the test set and compare retrieval quality.

Retrieval metrics (computed on each pipeline's final ranked list — the chunks
that are actually passed to the LLM for synthesis):

    NDCG@5       — ranking quality
    MRR          — reciprocal rank of the first relevant chunk
    Precision@5  — fraction of top 5 that are from an expected doc
    Recall@5     — fraction of expected docs covered by the top 5
    MAP          — mean average precision over the top-5 list

Aggregate reporting adds:
    - 95% bootstrap confidence intervals around each per-pipeline mean.
    - Paired permutation tests between pipelines (chain vs naive, agentic vs chain).
    - Per-query average input/output tokens (proxy for cost).
    - Average wall-clock latency per query.

If --judge is passed, an LLM-as-judge step also scores answer quality vs.
ground_truth_answer (1–5 scale), letting you measure whether better retrieval
actually produces better answers (Zhaoyan's question).

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --write-results
    python evaluation/evaluate.py --judge --write-results
"""

import argparse
import json
import math
import os
import random
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
K_RECALL = 5

BOOTSTRAP_SAMPLES = 1000
PERMUTATION_SAMPLES = 1000
RANDOM_SEED = 42


# ---------------- Retrieval metrics ---------------- #

def _relevance_vector(chunks: list[RetrievedChunk], expected: set[str]) -> list[int]:
    return [1 if c.source in expected else 0 for c in chunks]


def precision_at_k(chunks: list[RetrievedChunk], expected: set[str], k: int) -> float:
    if not chunks:
        return 0.0
    top = chunks[:k]
    hits = sum(1 for c in top if c.source in expected)
    return hits / k


def recall_at_k(chunks: list[RetrievedChunk], expected: set[str], k: int) -> float:
    """Fraction of expected docs covered (any chunk) within the top k."""
    if not expected:
        return 0.0
    top = chunks[:k]
    found_sources = {c.source for c in top if c.source in expected}
    return len(found_sources) / len(expected)


def reciprocal_rank(chunks: list[RetrievedChunk], expected: set[str]) -> float:
    for i, chunk in enumerate(chunks, start=1):
        if chunk.source in expected:
            return 1.0 / i
    return 0.0


def average_precision(chunks: list[RetrievedChunk], expected: set[str]) -> float:
    """
    Document-level Average Precision over the top-5 list.

    Each *unique source document* is counted as a hit at the rank of its first
    appearing chunk; subsequent chunks from the same source do not re-trigger a
    hit. This bounds AP to [0, 1] regardless of how many chunks share a source.
    """
    if not expected or not chunks:
        return 0.0
    seen: set[str] = set()
    hits = 0
    score = 0.0
    for i, chunk in enumerate(chunks, start=1):
        if chunk.source in expected and chunk.source not in seen:
            seen.add(chunk.source)
            hits += 1
            score += hits / i
    return score / len(expected)


def ndcg_at_k(chunks: list[RetrievedChunk], expected: set[str], k: int) -> float:
    rels = _relevance_vector(chunks[:k], expected)
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(rels))
    ideal_rels = sorted(rels, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_rels))
    if idcg == 0:
        return 0.0
    return dcg / idcg


# ---------------- Statistical helpers ---------------- #

def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def bootstrap_ci(values: list[float], n_samples: int = BOOTSTRAP_SAMPLES,
                 alpha: float = 0.05, rng: random.Random | None = None) -> tuple[float, float]:
    """Return (lower, upper) percentile bootstrap CI for the mean."""
    if not values:
        return (0.0, 0.0)
    rng = rng or random.Random(RANDOM_SEED)
    n = len(values)
    means = []
    for _ in range(n_samples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(_mean(sample))
    means.sort()
    lo = means[int((alpha / 2) * n_samples)]
    hi = means[int((1 - alpha / 2) * n_samples) - 1]
    return (lo, hi)


def paired_permutation_p(a: list[float], b: list[float],
                         n_samples: int = PERMUTATION_SAMPLES,
                         rng: random.Random | None = None) -> float:
    """
    Two-sided paired permutation test: under H0 (no difference), the per-query
    label assignment is exchangeable. Returns the p-value for |mean(a) - mean(b)|.
    """
    if len(a) != len(b) or not a:
        return 1.0
    rng = rng or random.Random(RANDOM_SEED + 1)
    observed = abs(_mean(a) - _mean(b))
    diffs = [ai - bi for ai, bi in zip(a, b)]
    count = 0
    for _ in range(n_samples):
        signs = [1 if rng.random() < 0.5 else -1 for _ in diffs]
        permuted_diff = sum(s * d for s, d in zip(signs, diffs)) / len(diffs)
        if abs(permuted_diff) >= observed - 1e-12:
            count += 1
    return count / n_samples


# ---------------- Per-query evaluation ---------------- #

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
        "input_tokens": result.answer.input_tokens,
        "output_tokens": result.answer.output_tokens,
        "answer_text": result.answer.text,
        "ground_truth_answer": query_entry.get("ground_truth_answer", ""),
        "metrics": {
            "ndcg@5": ndcg_at_k(reranked, expected, K_NDCG),
            "mrr": reciprocal_rank(reranked, expected),
            "precision@5": precision_at_k(reranked, expected, K_PRECISION),
            "recall@5": recall_at_k(reranked, expected, K_RECALL),
            "map": average_precision(reranked, expected),
        },
    }


# ---------------- LLM-as-judge ---------------- #

JUDGE_SYSTEM = (
    "You are a strict evaluator scoring how well a candidate answer matches a "
    "reference answer to a question about internal company documentation. "
    "Score on a 1–5 scale: "
    "5 = fully correct and complete, "
    "4 = correct but slightly incomplete, "
    "3 = partially correct, "
    "2 = mostly wrong, "
    "1 = completely wrong or refuses to answer. "
    "Respond with ONLY the integer score and nothing else."
)


def llm_judge_score(query: str, candidate: str, reference: str) -> int:
    """Ask GPT-4o to grade the candidate answer against the reference. Returns 1–5."""
    import os
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    user_msg = (
        f"Question: {query}\n\n"
        f"Reference answer: {reference}\n\n"
        f"Candidate answer: {candidate}\n\n"
        f"Score (1-5):"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=8,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    for ch in text:
        if ch.isdigit():
            n = int(ch)
            return max(1, min(5, n))
    return 1


# ---------------- Aggregation + reporting ---------------- #

METRIC_KEYS = ("ndcg@5", "mrr", "precision@5", "recall@5", "map")


def aggregate(per_query: list[dict]) -> dict:
    n = len(per_query)
    if n == 0:
        return {k: 0.0 for k in METRIC_KEYS} | {
            "avg_iterations": 0.0, "avg_elapsed_s": 0.0,
            "avg_input_tokens": 0.0, "avg_output_tokens": 0.0,
        }
    out = {}
    for k in METRIC_KEYS:
        out[k] = _mean([r["metrics"][k] for r in per_query])
    out["avg_iterations"] = _mean([r["iterations"] for r in per_query])
    out["avg_elapsed_s"] = _mean([r["elapsed_s"] for r in per_query])
    out["avg_input_tokens"] = _mean([r["input_tokens"] for r in per_query])
    out["avg_output_tokens"] = _mean([r["output_tokens"] for r in per_query])
    if "judge_score" in per_query[0]:
        out["judge_score"] = _mean([r["judge_score"] for r in per_query])
    return out


def aggregate_with_cis(per_query: list[dict]) -> dict:
    rng = random.Random(RANDOM_SEED)
    out = aggregate(per_query)
    cis = {}
    for k in METRIC_KEYS:
        cis[k] = bootstrap_ci([r["metrics"][k] for r in per_query], rng=rng)
    if "judge_score" in (per_query[0] if per_query else {}):
        cis["judge_score"] = bootstrap_ci([r["judge_score"] for r in per_query], rng=rng)
    out["ci95"] = {k: {"lo": round(lo, 3), "hi": round(hi, 3)} for k, (lo, hi) in cis.items()}
    return out


def aggregate_by_difficulty(per_query: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = {}
    for r in per_query:
        buckets.setdefault(r["difficulty"], []).append(r)
    return {difficulty: aggregate(items) for difficulty, items in buckets.items()}


def pairwise_significance(summaries: dict) -> dict:
    """For each metric, run paired permutation test on every pipeline pair."""
    names = list(summaries.keys())
    out = {}
    for k in METRIC_KEYS:
        out[k] = {}
        for i, a_name in enumerate(names):
            for b_name in names[i + 1:]:
                a_vals = [r["metrics"][k] for r in summaries[a_name]["per_query"]]
                b_vals = [r["metrics"][k] for r in summaries[b_name]["per_query"]]
                p = paired_permutation_p(a_vals, b_vals)
                out[k][f"{a_name} vs {b_name}"] = round(p, 4)
    return out


def print_summary_table(summaries: dict, significance: dict | None) -> None:
    metric_cols = ["NDCG@5", "MRR", "P@5", "R@5", "MAP"]
    metric_keys = ["ndcg@5", "mrr", "precision@5", "recall@5", "map"]

    header = (
        f"{'pipeline':<10} "
        + " ".join(f"{c:>14}" for c in metric_cols)
        + f" {'iters':>7} {'time(s)':>8} {'in_tok':>8} {'out_tok':>8}"
    )
    has_judge = any("judge_score" in s["overall"] for s in summaries.values())
    if has_judge:
        header += f" {'judge':>7}"

    print()
    print("=" * len(header))
    print("OVERALL  (95% bootstrap CI in brackets)")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for name, summary in summaries.items():
        overall = summary["overall"]
        cis = overall.get("ci95", {})
        cells = []
        for k in metric_keys:
            mean = overall[k]
            ci = cis.get(k)
            if ci:
                cells.append(f"{mean:.3f}[{ci['lo']:.2f},{ci['hi']:.2f}]")
            else:
                cells.append(f"{mean:.3f}")
        line = (
            f"{name:<10} "
            + " ".join(f"{c:>14}" for c in cells)
            + f" {overall['avg_iterations']:>7.2f} "
            f"{overall['avg_elapsed_s']:>8.2f} "
            f"{overall['avg_input_tokens']:>8.0f} "
            f"{overall['avg_output_tokens']:>8.0f}"
        )
        if has_judge and "judge_score" in overall:
            line += f" {overall['judge_score']:>7.2f}"
        print(line)

    if significance:
        print()
        print("PAIRED PERMUTATION p-VALUES  (n=1000)")
        print("-" * len(header))
        for k in metric_keys:
            row = significance.get(k, {})
            cells = ", ".join(f"{pair}: p={p:.3f}" for pair, p in row.items())
            print(f"  {k:<12} {cells}")

    # Per-difficulty (no CIs to keep the table compact)
    all_difficulties: set[str] = set()
    for summary in summaries.values():
        all_difficulties.update(summary["by_difficulty"].keys())

    short_header = (
        f"{'pipeline':<10} "
        + " ".join(f"{c:>8}" for c in metric_cols)
        + f" {'iters':>7} {'time(s)':>8}"
    )
    for difficulty in sorted(all_difficulties):
        print()
        print("=" * len(short_header))
        print(f"BY DIFFICULTY: {difficulty}")
        print("=" * len(short_header))
        print(short_header)
        print("-" * len(short_header))
        for name, summary in summaries.items():
            bucket = summary["by_difficulty"].get(difficulty)
            if bucket is None:
                continue
            line = (
                f"{name:<10} "
                + " ".join(f"{bucket[k]:>8.3f}" for k in metric_keys)
                + f" {bucket['avg_iterations']:>7.2f} "
                f"{bucket['avg_elapsed_s']:>8.2f}"
            )
            print(line)
    print()


def load_test_set(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["queries"]


def run_evaluation(write_results: bool, use_judge: bool = False) -> None:
    queries = load_test_set(TEST_SET_PATH)
    print(f"Loaded {len(queries)} queries from {TEST_SET_PATH}")
    if use_judge:
        print("LLM-as-judge enabled — every pipeline will incur extra OpenAI calls.")

    summaries: dict[str, dict] = {}

    for name, pipeline_fn in PIPELINES.items():
        print(f"\nRunning pipeline: {name}")
        per_query = []
        for i, q in enumerate(queries, start=1):
            print(f"  [{i:>2}/{len(queries)}] {q['id']} ({q['difficulty']}) ", end="", flush=True)
            result = evaluate_query(pipeline_fn, q)
            if use_judge:
                try:
                    result["judge_score"] = llm_judge_score(
                        result["query"], result["answer_text"], result["ground_truth_answer"]
                    )
                except Exception as e:
                    print(f"  [judge failed: {e}] ", end="")
                    result["judge_score"] = 0
            per_query.append(result)
            m = result["metrics"]
            judge_str = f" judge={result.get('judge_score', '-')}" if use_judge else ""
            print(
                f"ndcg={m['ndcg@5']:.2f} mrr={m['mrr']:.2f} "
                f"p@5={m['precision@5']:.2f} r@5={m['recall@5']:.2f} "
                f"map={m['map']:.2f} iters={result['iterations']} "
                f"{result['elapsed_s']:.1f}s{judge_str}"
            )
        summaries[name] = {
            "overall": aggregate_with_cis(per_query),
            "by_difficulty": aggregate_by_difficulty(per_query),
            "per_query": per_query,
        }

    significance = pairwise_significance(summaries)
    print_summary_table(summaries, significance)

    if write_results:
        # Strip the heavy `per_query` arrays from the printable view but keep them in the file.
        out = {
            "summaries": summaries,
            "pairwise_significance": significance,
        }
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"Results written to {RESULTS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG pipelines on the test set.")
    parser.add_argument("--write-results", action="store_true",
                        help="Write per-query results to evaluation/results.json")
    parser.add_argument("--judge", action="store_true",
                        help="Enable LLM-as-judge answer-quality scoring (1–5).")
    args = parser.parse_args()
    run_evaluation(write_results=args.write_results, use_judge=args.judge)


if __name__ == "__main__":
    main()
