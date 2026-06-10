from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import html
import re
import time

import requests

from core.config import Settings
from core.utils import compact_join, normalize_whitespace, write_json

CROSSREF_WORKS_URL = "https://api.crossref.org/works"
SELECT_FIELDS = (
    "DOI,title,abstract,author,subject,issued,published,"
    "published-print,published-online,created,deposited,indexed,"
    "URL,link,container-title,type"
)
REQUEST_HEADERS = {
    "User-Agent": "day10-data-observability-lab/0.1 (mailto:student@example.com)"
}


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_jats(value: str) -> str:
    """Remove JATS/XML tags that Crossref wraps abstracts in and normalize text."""
    if not value:
        return ""
    no_tags = re.sub(r"<[^>]+>", " ", value)
    text = normalize_whitespace(html.unescape(no_tags))
    # Collapse spaces that the tag removal may have left before punctuation.
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def _date_parts_to_iso(date_parts: list | None) -> str:
    """Convert a Crossref `date-parts` structure into an ISO `YYYY-MM-DD` string."""
    if not date_parts:
        return ""
    parts = date_parts[0] if date_parts and isinstance(date_parts[0], list) else date_parts
    if not parts:
        return ""
    year = parts[0]
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    try:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except (TypeError, ValueError):
        return ""


def _pick_date(item: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        block = item.get(key) or {}
        iso = _date_parts_to_iso(block.get("date-parts"))
        if iso:
            return iso
    return ""


def _author_names(item: dict) -> list[str]:
    names: list[str] = []
    for author in item.get("author", []) or []:
        given = normalize_whitespace(author.get("given", ""))
        family = normalize_whitespace(author.get("family", ""))
        full = compact_join([given, family], sep=" ")
        if not full:
            full = normalize_whitespace(author.get("name", ""))
        if full:
            names.append(full)
    return names


def _pdf_url(item: dict) -> str:
    for link in item.get("link", []) or []:
        if "pdf" in (link.get("content-type", "").lower()):
            return link.get("URL", "")
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref `/works` payload into a list of PaperRecord.

    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    items = (payload or {}).get("message", {}).get("items", []) or []
    records: list[PaperRecord] = []
    seen: set[str] = set()

    for item in items:
        paper_id = normalize_whitespace(str(item.get("DOI", "")))
        title_list = item.get("title") or []
        title = normalize_whitespace(title_list[0]) if title_list else ""

        # Drop records that cannot be identified or used downstream.
        if not paper_id or not title or paper_id.lower() in seen:
            continue
        seen.add(paper_id.lower())

        summary = _strip_jats(item.get("abstract", ""))
        authors = _author_names(item)
        categories = [normalize_whitespace(c) for c in (item.get("subject") or []) if c]
        primary_category = categories[0] if categories else ""
        published = _pick_date(item, ("issued", "published", "published-print", "published-online", "created"))
        updated = _pick_date(item, ("deposited", "indexed", "created")) or published
        container = item.get("container-title") or []
        comment = normalize_whitespace(container[0]) if container else normalize_whitespace(str(item.get("type", "")))

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=normalize_whitespace(str(item.get("URL", ""))),
                pdf_url=_pdf_url(item),
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call the Crossref API, persist the raw response, and parse records.

    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "select": SELECT_FIELDS,
        "sort": "published",
        "order": "desc",
    }

    payload: dict | None = None
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = requests.get(
                CROSSREF_WORKS_URL,
                params=params,
                headers=REQUEST_HEADERS,
                timeout=30,
            )
            if response.status_code in {429, 500, 502, 503, 504}:
                time.sleep(min(2 ** attempt, 16))
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:  # network / transient errors
            last_error = exc
            time.sleep(min(2 ** attempt, 16))

    if payload is None:
        raise RuntimeError(f"Failed to fetch Crossref data after retries: {last_error}")

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read the parsed raw-records JSON snapshot and map back to PaperRecord."""
    from core.utils import read_json

    rows = read_json(path)
    records: list[PaperRecord] = []
    for row in rows:
        records.append(
            PaperRecord(
                paper_id=row["paper_id"],
                title=row["title"],
                summary=row.get("summary", ""),
                authors=list(row.get("authors", [])),
                categories=list(row.get("categories", [])),
                primary_category=row.get("primary_category", ""),
                published=row.get("published", ""),
                updated=row.get("updated", ""),
                abs_url=row.get("abs_url", ""),
                pdf_url=row.get("pdf_url", ""),
                comment=row.get("comment", ""),
            )
        )
    return records
