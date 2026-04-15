"""
main.py — Unified CLI for the RAG pipeline comparison project.

Commands:
    python main.py ingest
        Build the ChromaDB vector store from docs/.

    python main.py query "your question" [--pipeline naive|chain|agentic]
        Run a single query through one pipeline and print the answer.

    python main.py evaluate [--write-results]
        Run all three pipelines on the test set and print a comparison table.
"""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()


def cmd_ingest(_: argparse.Namespace) -> None:
    from ingest import ingest
    ingest()


def cmd_query(args: argparse.Namespace) -> None:
    from pipelines import naive, rag_chain, agentic

    runners = {
        "naive": naive.run,
        "chain": rag_chain.run,
        "agentic": agentic.run,
    }
    run_fn = runners[args.pipeline]

    print(f"Pipeline: {args.pipeline}")
    print(f"Query:    {args.question}")
    print()

    result = run_fn(args.question)

    print("--- Answer ---")
    print(result.answer.text)
    print()
    print("--- Sources ---")
    for source in result.answer.sources:
        print(f"  - {source}")
    print()
    print("--- Retrieved chunks (final) ---")
    for i, chunk in enumerate(result.reranked, start=1):
        print(f"  [{i}] {chunk.source}  chunk{chunk.chunk_index}  score={chunk.score:.3f}")
    if args.pipeline == "agentic":
        print()
        print(f"Reformulation iterations: {result.iterations}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    from evaluation.evaluate import run_evaluation
    run_evaluation(write_results=args.write_results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="RAG pipeline comparison — ingest, query, and evaluate.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_ingest = subparsers.add_parser("ingest", help="Build the ChromaDB vector store.")
    p_ingest.set_defaults(func=cmd_ingest)

    p_query = subparsers.add_parser("query", help="Run a single query through one pipeline.")
    p_query.add_argument("question", help="The question to ask.")
    p_query.add_argument(
        "--pipeline",
        choices=["naive", "chain", "agentic"],
        default="naive",
        help="Which pipeline to use (default: naive).",
    )
    p_query.set_defaults(func=cmd_query)

    p_eval = subparsers.add_parser("evaluate", help="Run all pipelines on the test set.")
    p_eval.add_argument(
        "--write-results",
        action="store_true",
        help="Write per-query results to evaluation/results.json",
    )
    p_eval.set_defaults(func=cmd_evaluate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
