from __future__ import annotations

import pandas as pd

from observability.quality import build_freshness_report, run_data_quality_checks


def test_quality_passes_on_clean_data(clean_df, settings):
    result = run_data_quality_checks(clean_df, settings, "baseline")
    assert result["success"] is True
    assert result["failure_count"] == 0
    # Report file is persisted under the quality dir.
    assert (settings.paths.quality_dir / "baseline_quality.json").exists()


def test_quality_flags_duplicates_and_stale(clean_df, settings):
    bad = pd.concat([clean_df, clean_df.iloc[[0]]], ignore_index=True)  # duplicate id
    bad.loc[bad.index[-1], "age_days"] = settings.freshness_threshold_days + 1000  # stale
    result = run_data_quality_checks(bad, settings, "corrupted")
    checks = {c["name"]: c["success"] for c in result["checks"]}
    assert checks["paper_id_unique"] is False
    assert checks["freshness_within_threshold"] is False
    assert result["success"] is False


def test_freshness_report(clean_df, settings, tmp_path):
    report_path = tmp_path / "freshness.json"
    payload = build_freshness_report(clean_df, settings, report_path)
    assert report_path.exists()
    assert payload["total_rows"] == len(clean_df)
    assert payload["stale_rows"] == 0
    assert payload["is_fresh"] is True
    assert payload["latest_published"] >= payload["oldest_published"]
