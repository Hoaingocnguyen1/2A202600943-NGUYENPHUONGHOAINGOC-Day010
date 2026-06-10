from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, safe_slug, write_json

MIN_ROWS = 5
MIN_SUMMARY_CHARS = 80


def _check(name: str, success: bool, observed: Any, expected: str) -> dict[str, Any]:
    return {"name": name, "success": bool(success), "observed": observed, "expected": expected}


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run a small suite of data-quality checks and persist the result.

    Checks: row count, paper_id not-null & unique, title not-null,
    summary length, and freshness via age_days.
    """
    total = int(len(df))
    threshold = settings.freshness_threshold_days

    paper_id_nulls = int(df["paper_id"].isna().sum()) + int((df["paper_id"].astype(str).str.len() == 0).sum())
    duplicate_ids = int(df["paper_id"].duplicated().sum())
    title_nulls = int(df["title"].isna().sum()) + int((df["title"].astype(str).str.len() == 0).sum())
    short_summaries = int((df["summary_chars"] < MIN_SUMMARY_CHARS).sum())
    age = df["age_days"].dropna()
    stale_rows = int((age > threshold).sum()) if not age.empty else 0

    checks = [
        _check("row_count_minimum", total >= MIN_ROWS, total, f">= {MIN_ROWS}"),
        _check("paper_id_not_null", paper_id_nulls == 0, paper_id_nulls, "0 nulls"),
        _check("paper_id_unique", duplicate_ids == 0, duplicate_ids, "0 duplicates"),
        _check("title_not_null", title_nulls == 0, title_nulls, "0 nulls"),
        _check("summary_min_length", short_summaries == 0, short_summaries, f"0 rows < {MIN_SUMMARY_CHARS} chars"),
        _check("freshness_within_threshold", stale_rows == 0, stale_rows, f"0 rows older than {threshold} days"),
    ]

    success_count = sum(1 for c in checks if c["success"])
    payload = {
        "report_name": report_name,
        "generated_at": now_utc().isoformat(),
        "row_count": total,
        "checks": checks,
        "success_count": success_count,
        "failure_count": len(checks) - success_count,
        "success": success_count == len(checks),
    }

    output_path = settings.paths.quality_dir / f"{safe_slug(report_name)}_quality.json"
    write_json(output_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize dataset freshness based on published date and age_days."""
    threshold = settings.freshness_threshold_days
    published = df["published"].dropna()
    published = published[published.astype(str).str.len() > 0]
    age = df["age_days"].dropna()

    total = int(len(df))
    stale_rows = int((age > threshold).sum()) if not age.empty else 0
    fresh_rows = total - stale_rows
    newest_age = int(age.min()) if not age.empty else None
    oldest_age = int(age.max()) if not age.empty else None
    # Dataset is "fresh" only when the newest record is within the threshold
    # AND there are no stale rows dragging the corpus out of date.
    is_fresh = newest_age is not None and newest_age <= threshold and stale_rows == 0

    payload = {
        "generated_at": now_utc().isoformat(),
        "freshness_threshold_days": threshold,
        "total_rows": total,
        "latest_published": max(published) if not published.empty else None,
        "oldest_published": min(published) if not published.empty else None,
        "newest_age_days": newest_age,
        "oldest_age_days": oldest_age,
        "fresh_rows": fresh_rows,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_rows / total, 4) if total else 0.0,
        "is_fresh": bool(is_fresh),
    }

    write_json(report_path, payload)
    return payload
