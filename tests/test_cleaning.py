from __future__ import annotations

from datetime import datetime

from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import PaperRecord

RUN_DATE = datetime(2026, 6, 10)


def test_clean_dataframe_has_expected_columns(clean_df):
    for col in [
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "categories_joined",
        "age_days",
        "summary_chars",
        "text_for_embedding",
    ]:
        assert col in clean_df.columns


def test_text_for_embedding_contains_core_fields(clean_df):
    row = clean_df.iloc[0]
    text = row["text_for_embedding"]
    assert row["title"] in text
    assert "Summary:" in text and "Authors:" in text and "Categories:" in text


def test_age_days_computed(clean_df):
    # Published 2026-05-01, run date 2026-06-10 -> 40 days.
    newest = clean_df[clean_df["published"] == "2026-05-01"].iloc[0]
    assert newest["age_days"] == (RUN_DATE.date() - datetime(2026, 5, 1).date()).days


def test_sorted_newest_first(clean_df):
    published = list(clean_df["published"])
    assert published == sorted(published, reverse=True)


def test_drops_empty_summary_and_duplicates():
    records = [
        PaperRecord("10.1/a", "Title A", "A long enough summary about RAG systems.", ["X"], ["CS"], "CS", "2026-05-01", "2026-05-01", "", "", ""),
        PaperRecord("10.1/a", "Title A dup", "Another summary duplicate id.", ["X"], ["CS"], "CS", "2026-04-01", "2026-04-01", "", "", ""),
        PaperRecord("10.1/b", "Title B", "", ["Y"], ["CS"], "CS", "2026-03-01", "2026-03-01", "", "", ""),
    ]
    df = build_clean_dataframe(records, RUN_DATE)
    assert list(df["paper_id"]) == ["10.1/a"]  # dup removed, empty-summary row dropped
