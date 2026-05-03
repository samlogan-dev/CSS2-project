"""
main.py — Unified CLI for the RAG pipeline comparison project.

Commands:
    python main.py ingest
        Build the ChromaDB vector store from docs/.

    python main.py query "your question" [--pipeline naive|chain|agentic]
        Run a single query through one pipeline and print the answer.

    python main.py evaluate [--write-results] [--judge]
        Run all three pipelines on the test set and print a comparison table.

    python main.py ablate [--write-results]
        Sweep RETRIEVE_K and report NDCG@5 / MRR / P@5 as a function of K.
"""

import argparse


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

    common_kwargs = {"mode": args.mode}
    if args.pipeline != "naive":
        common_kwargs.update(
            retrieve_k=args.retrieve_k,
            rerank_n=args.rerank_n,
            score_threshold=args.score_threshold,
            use_mmr=args.mmr,
        )
    else:
        common_kwargs.update(top_k=args.rerank_n)  # naive uses rerank_n as top_k

    result = run_fn(args.question, **common_kwargs)

    print(result.answer.text)
    print()
    print("Sources:")
    for source in result.answer.sources:
        print(f"  - {source}")

    if args.verbose:
        print()
        print(f"Pipeline:   {args.pipeline}")
        print(f"Mode:       {args.mode}")
        print(f"Tokens:     in={result.answer.input_tokens}  out={result.answer.output_tokens}")
        print(f"Retrieved:  {len(result.retrieved)} chunks → reranked to {len(result.reranked)}")
        print()
        print("Final ranked chunks:")
        for i, chunk in enumerate(result.reranked, start=1):
            print(f"  [{i}] {chunk.source}  chunk{chunk.chunk_index}  score={chunk.score:.3f}")
        if args.pipeline == "agentic":
            print(f"\nReformulation iterations: {result.iterations}")


def cmd_evaluate(args: argparse.Namespace) -> None:
    from evaluation.evaluate import run_evaluation
    run_evaluation(write_results=args.write_results, use_judge=args.judge)


def cmd_ablate(args: argparse.Namespace) -> None:
    from evaluation.ablation import run_ablation
    run_ablation(write_results=args.write_results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="RAG pipeline comparison — ingest, query, evaluate, ablate.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_ingest = subparsers.add_parser("ingest", help="Build the ChromaDB vector store.")
    p_ingest.set_defaults(func=cmd_ingest)

    p_query = subparsers.add_parser("query", help="Run a single query through one pipeline.")
    p_query.add_argument("question", help="The question to ask.")
    p_query.add_argument("--pipeline", choices=["naive", "chain", "agentic"], default="naive")
    p_query.add_argument("--mode", choices=["dense", "bm25", "hybrid"], default="dense",
                         help="Retrieval mode (default: dense).")
    p_query.add_argument("--retrieve-k", type=int, default=20,
                         help="Candidates to pull from the retriever (chain/agentic only).")
    p_query.add_argument("--rerank-n", type=int, default=5,
                         help="Chunks to keep after reranking (also = top_k for naive).")
    p_query.add_argument("--score-threshold", type=float, default=None,
                         help="Drop reranked chunks with score below this.")
    p_query.add_argument("--mmr", action="store_true",
                         help="Use MMR diversity selection at rerank time.")
    p_query.add_argument("-v", "--verbose", action="store_true",
                         help="Show retrieved chunks, scores, token counts.")
    p_query.set_defaults(func=cmd_query)

    p_eval = subparsers.add_parser("evaluate", help="Run all pipelines on the test set.")
    p_eval.add_argument("--write-results", action="store_true",
                        help="Write per-query results to evaluation/results.json")
    p_eval.add_argument("--judge", action="store_true",
                        help="Also run LLM-as-judge answer-quality scoring (extra OpenAI calls).")
    p_eval.set_defaults(func=cmd_evaluate)

    p_ablate = subparsers.add_parser(
        "ablate", help="Sweep RETRIEVE_K and report metrics as a function of K."
    )
    p_ablate.add_argument("--write-results", action="store_true",
                          help="Write the sweep to evaluation/ablation_results.json")
    p_ablate.set_defaults(func=cmd_ablate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
