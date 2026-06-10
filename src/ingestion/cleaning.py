from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _safe_age_days(published: str, run_date: datetime) -> int | None:
    if not published:
        return None
    try:
        published_date = datetime.fromisoformat(published).date()
    except ValueError:
        return None
    return (run_date.date() - published_date).days


def _build_embedding_text(title: str, summary: str, authors_joined: str, categories_joined: str) -> str:
    lines = [
        f"Title: {title}",
        f"Summary: {summary}",
    ]
    if authors_joined:
        lines.append(f"Authors: {authors_joined}")
    if categories_joined:
        lines.append(f"Categories: {categories_joined}")
    return "\n".join(lines)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready for embedding.

    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper: authors_joined, categories_joined, summary_chars, text_for_embedding.
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    rows: list[dict] = []
    for record in records:
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        authors = [normalize_whitespace(a) for a in record.authors if a and normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in record.categories if c and normalize_whitespace(c)]
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        published = record.published or ""
        age_days = _safe_age_days(published, run_date)

        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id),
                "title": title,
                "summary": summary,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": normalize_whitespace(record.primary_category),
                "published": published,
                "updated": record.updated or "",
                "age_days": age_days,
                "summary_chars": len(summary),
                "abs_url": record.abs_url or "",
                "pdf_url": record.pdf_url or "",
                "comment": normalize_whitespace(record.comment),
                "text_for_embedding": _build_embedding_text(title, summary, authors_joined, categories_joined),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Filter out rows missing the essentials needed for retrieval/QA.
    df = df[df["paper_id"].astype(bool)]
    df = df[df["title"].astype(bool)]
    df = df[df["summary"].str.len() > 0]

    # Drop duplicate papers, keeping the first (most recent after sort below).
    df = df.drop_duplicates(subset="paper_id", keep="first")

    # Newest first so freshness and "latest records" semantics are obvious.
    df = df.sort_values(by="published", ascending=False, na_position="last")
    df = df.reset_index(drop=True)
    return df
