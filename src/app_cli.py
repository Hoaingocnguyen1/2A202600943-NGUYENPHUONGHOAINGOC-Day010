"""Unified CLI for the Day 10 data pipeline lab.

Examples
--------
    python -m app_cli phase1
    python -m app_cli corruption
    python -m app_cli all --refresh-source --run-ragas
    python -m app_cli phase1 --provider openai --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import os


def _apply_env(args: argparse.Namespace) -> None:
    """Translate CLI flags into the env vars that `load_settings` reads."""
    if args.refresh_source:
        os.environ["REFRESH_SOURCE"] = "1"
    if args.refresh_test_set:
        os.environ["REFRESH_TEST_SET"] = "1"
    if args.run_ragas:
        os.environ["RUN_RAGAS"] = "1"
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="day10",
        description="Run the Day 10 data pipeline / observability lab.",
    )
    parser.add_argument(
        "stage",
        choices=["phase1", "corruption", "all"],
        help="Which pipeline to run.",
    )
    parser.add_argument("--refresh-source", action="store_true", help="Force a fresh fetch from the source API.")
    parser.add_argument("--refresh-test-set", action="store_true", help="Rebuild the evaluation test set.")
    parser.add_argument("--run-ragas", action="store_true", help="Enable the slower Ragas evaluation pass.")
    parser.add_argument("--provider", default=None, help="Override LLM_PROVIDER (openai, gemini, anthropic, ...).")
    parser.add_argument("--model", default=None, help="Override LLM_MODEL.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    _apply_env(args)

    # Import after env is set so settings pick up the overrides.
    from pipelines.corruption_flow import main as corruption_main
    from pipelines.phase1 import main as phase1_main

    if args.stage in {"phase1", "all"}:
        phase1_main()
    if args.stage in {"corruption", "all"}:
        corruption_main()


if __name__ == "__main__":
    main()
