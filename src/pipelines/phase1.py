from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _demo_agent(settings, index, test_set) -> None:
    """Optional: exercise the agent on a couple of questions; never fatal."""
    try:
        from retrieval.agent import build_agent, run_agent_question

        agent = build_agent(settings=settings, index=index)
        demos = []
        for item in test_set[:2]:
            answer = run_agent_question(agent, item["question"])
            demos.append({"question": item["question"], "answer": answer})
        write_json(settings.paths.demo_answers, demos)
        print(f"[phase1] agent demo saved -> {settings.paths.demo_answers}")
    except Exception as exc:  # noqa: BLE001 - demo is best-effort
        print(f"[phase1] agent demo skipped: {exc}")


def main() -> None:
    """Build the baseline pipeline end-to-end."""
    settings = load_settings()
    paths = settings.paths

    # 1-2. Load or fetch raw records.
    if settings.refresh_source or not paths.raw_records_json.exists():
        print("[phase1] fetching raw records from source...")
        records = fetch_source_records(settings)
    else:
        print("[phase1] loading cached raw records...")
        records = load_raw_records(paths.raw_records_json)
    print(f"[phase1] raw records: {len(records)}")

    # 3-4. Clean and persist.
    df = build_clean_dataframe(records, now_utc())
    print(f"[phase1] clean records: {len(df)}")
    write_csv(df, paths.clean_csv)
    write_json(paths.clean_json, df.to_dict(orient="records"))

    # 5. Build the embedding index.
    print("[phase1] building Chroma index...")
    index = LocalEmbeddingIndex.build(df, settings, paths.embeddings_json)

    # 6. Create or load the evaluation set.
    if settings.refresh_test_set or not paths.eval_testset.exists():
        print("[phase1] building test set...")
        test_set = build_test_set(df, paths.eval_testset)
    else:
        from core.utils import read_json

        test_set = read_json(paths.eval_testset)
    print(f"[phase1] test set samples: {len(test_set)}")

    # 7. Evaluate.
    print("[phase1] evaluating...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )

    # 8. Quality + freshness.
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, paths.freshness_report)

    # 9. Markdown report.
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_record_count": len(records),
        "clean_record_count": len(df),
    }
    generate_phase1_report(
        paths.baseline_report, source_summary, bundle.summary, quality, freshness, answers=bundle.answers
    )

    # 10. Optional agent demo.
    _demo_agent(settings, index, test_set)

    print("[phase1] done.")
    print(f"[phase1] metrics: {bundle.summary}")
    print(f"[phase1] report -> {paths.baseline_report}")


if __name__ == "__main__":
    main()
