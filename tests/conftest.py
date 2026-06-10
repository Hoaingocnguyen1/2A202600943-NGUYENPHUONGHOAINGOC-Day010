from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

# Make the `src` layout importable without installing the package.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import PaperRecord

RUN_DATE = datetime(2026, 6, 10)


def _record(idx: int, published: str, summary: str | None = None) -> PaperRecord:
    return PaperRecord(
        paper_id=f"10.1234/paper{idx}",
        title=f"Sample Paper {idx} on Retrieval Augmented Generation",
        summary=summary
        if summary is not None
        else (
            f"This paper number {idx} studies retrieval augmented generation and agentic "
            "large language models across several benchmark tasks and reports detailed results."
        ),
        authors=[f"Author {idx} A", f"Author {idx} B"],
        categories=["Computer Science", "Machine Learning"],
        primary_category="Computer Science",
        published=published,
        updated=published,
        abs_url=f"https://example.org/{idx}",
        pdf_url=f"https://example.org/{idx}.pdf",
        comment="Journal of Examples",
    )


@pytest.fixture
def sample_records() -> list[PaperRecord]:
    return [
        _record(1, "2026-05-01"),
        _record(2, "2026-04-01"),
        _record(3, "2026-03-01"),
        _record(4, "2026-02-01"),
        _record(5, "2026-01-15"),
        _record(6, "2025-12-20"),
    ]


@pytest.fixture
def clean_df(sample_records):
    return build_clean_dataframe(sample_records, RUN_DATE)


@pytest.fixture
def settings(tmp_path):
    from core.config import load_settings

    return load_settings(project_dir=tmp_path)
