from __future__ import annotations

from ingestion.crossref import parse_crossref_payload


def _payload() -> dict:
    return {
        "message": {
            "items": [
                {
                    "DOI": "10.1/abc",
                    "title": ["Sample Title"],
                    "abstract": "<jats:p>Hello <b>world</b>.</jats:p>",
                    "author": [{"given": "Jane", "family": "Doe"}, {"name": "Org Author"}],
                    "subject": ["Artificial Intelligence", "Machine Learning"],
                    "issued": {"date-parts": [[2026, 1, 15]]},
                    "deposited": {"date-parts": [[2026, 2, 1]]},
                    "URL": "https://doi.org/10.1/abc",
                    "link": [{"URL": "https://x/paper.pdf", "content-type": "application/pdf"}],
                    "container-title": ["Journal X"],
                },
                {"DOI": "10.1/abc", "title": ["Duplicate DOI"]},  # dropped: duplicate
                {"title": ["No DOI here"]},  # dropped: missing DOI
                {"DOI": "10.1/empty"},  # dropped: missing title
            ]
        }
    }


def test_parse_filters_invalid_and_duplicates():
    records = parse_crossref_payload(_payload())
    assert len(records) == 1


def test_parse_extracts_fields_and_strips_jats():
    record = parse_crossref_payload(_payload())[0]
    assert record.paper_id == "10.1/abc"
    assert record.title == "Sample Title"
    assert record.summary == "Hello world."  # JATS/HTML tags stripped, whitespace normalized
    assert record.authors == ["Jane Doe", "Org Author"]
    assert record.categories == ["Artificial Intelligence", "Machine Learning"]
    assert record.primary_category == "Artificial Intelligence"
    assert record.published == "2026-01-15"
    assert record.updated == "2026-02-01"
    assert record.pdf_url == "https://x/paper.pdf"
    assert record.comment == "Journal X"


def test_parse_handles_empty_payload():
    assert parse_crossref_payload({}) == []
    assert parse_crossref_payload({"message": {"items": []}}) == []
