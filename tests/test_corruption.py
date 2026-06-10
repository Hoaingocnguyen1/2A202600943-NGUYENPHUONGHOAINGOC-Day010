from __future__ import annotations

from core.utils import read_json
from ingestion.corruption import corrupt_clean_dataframe


def test_corruption_writes_log_and_changes_data(clean_df, tmp_path):
    log_path = tmp_path / "corruption_log.json"
    corrupted = corrupt_clean_dataframe(clean_df, log_path)

    assert log_path.exists()
    log = read_json(log_path)
    ops = {op["op"] for op in log["operations"]}
    assert {
        "drop_latest_records",
        "blank_summary",
        "inject_noise",
        "truncate_title",
        "stale_publication_date",
        "add_duplicates",
    } <= ops


def test_corruption_introduces_duplicates_and_blanks(clean_df, tmp_path):
    corrupted = corrupt_clean_dataframe(clean_df, tmp_path / "log.json")
    # Duplicates added -> at least one repeated paper_id.
    assert corrupted["paper_id"].duplicated().any()
    # Some summaries blanked out.
    assert (corrupted["summary"].astype(str).str.len() == 0).any()
    # A stale (very old) publication date was injected.
    assert (corrupted["published"] == "2005-01-01").any()
