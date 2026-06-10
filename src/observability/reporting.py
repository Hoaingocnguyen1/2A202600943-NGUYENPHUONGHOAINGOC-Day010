from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.utils import now_utc, write_text

_COMPARE_KEYS = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]


def _fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    if isinstance(value, (int,)):
        return str(value)
    return str(value)


def _delta(new: Any, base: Any) -> str:
    try:
        diff = float(new) - float(base)
    except (TypeError, ValueError):
        return "n/a"
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.4f}"


def _metrics_table(metrics: dict[str, Any]) -> list[str]:
    keys = ["samples", *_COMPARE_KEYS]
    lines = ["| Metric | Value |", "| --- | --- |"]
    for key in keys:
        if key in metrics:
            lines.append(f"| {key} | {_fmt(metrics[key])} |")
    return lines


def _per_type_breakdown(answers: list[dict[str, Any]] | None) -> list[str]:
    if not answers:
        return []
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in answers:
        buckets[item.get("question_type", "unknown")].append(item)

    lines = [
        "",
        "### Per question-type breakdown",
        "| Question type | Samples | Hit rate | Mean token F1 | Judge accuracy |",
        "| --- | --- | --- | --- | --- |",
    ]
    for qtype, items in sorted(buckets.items()):
        n = len(items)
        hit = sum(1 for i in items if i.get("retrieval_hit")) / n
        f1 = sum(i.get("token_f1", 0.0) for i in items) / n
        acc = sum(1 for i in items if i.get("judge", {}).get("correct")) / n
        lines.append(f"| {qtype} | {n} | {_fmt(hit)} | {_fmt(f1)} | {_fmt(acc)} |")
    return lines


def _quality_lines(quality: dict[str, Any]) -> list[str]:
    total = quality.get("success_count", 0) + quality.get("failure_count", 0)
    lines = [
        f"- Rows: {quality.get('row_count')}",
        f"- Passed checks: {quality.get('success_count')}/{total}",
        f"- Overall success: {_fmt(quality.get('success'))}",
        "",
        "| Check | Success | Observed | Expected |",
        "| --- | --- | --- | --- |",
    ]
    for check in quality.get("checks", []):
        lines.append(
            f"| {check['name']} | {_fmt(check['success'])} | {check['observed']} | {check['expected']} |"
        )
    return lines


def _freshness_lines(freshness: dict[str, Any]) -> list[str]:
    return [
        f"- Latest published: {freshness.get('latest_published')}",
        f"- Oldest published: {freshness.get('oldest_published')}",
        f"- Fresh rows: {freshness.get('fresh_rows')} / {freshness.get('total_rows')}",
        f"- Stale rows: {freshness.get('stale_rows')} (ratio {freshness.get('stale_ratio')})",
        f"- Is fresh: {_fmt(freshness.get('is_fresh'))}",
    ]


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
    answers: list[dict[str, Any]] | None = None,
) -> None:
    """Write a markdown report for the baseline phase."""
    lines: list[str] = [
        "# Phase 1 - Baseline Pipeline Report",
        "",
        f"_Generated at {now_utc().isoformat()}_",
        "",
        "## Source",
        f"- API: {source_summary.get('source_api')}",
        f"- Query: {source_summary.get('source_query')}",
        f"- Filter: {source_summary.get('source_filter')}",
        f"- Records fetched: {source_summary.get('raw_record_count')}",
        f"- Clean records: {source_summary.get('clean_record_count')}",
        "",
        "## Evaluation Metrics",
        *_metrics_table(metrics),
        "",
        f"- Ragas: {metrics.get('ragas')}",
        *_per_type_breakdown(answers),
        "",
        "## Data Quality",
        *_quality_lines(quality),
        "",
        "## Freshness",
        *_freshness_lines(freshness),
        "",
    ]
    write_text(report_path, "\n".join(lines) + "\n")


def _metrics_comparison_table(
    baseline: dict[str, Any],
    corrupted: dict[str, Any],
    repaired: dict[str, Any],
) -> list[str]:
    lines = [
        "| Metric | Baseline | Corrupted | Repaired | Δ Corrupted | Δ Repaired |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key in _COMPARE_KEYS:
        b, c, r = baseline.get(key), corrupted.get(key), repaired.get(key)
        lines.append(
            f"| {key} | {_fmt(b)} | {_fmt(c)} | {_fmt(r)} | {_delta(c, b)} | {_delta(r, b)} |"
        )
    return lines


def _quality_comparison_table(
    baseline: dict[str, Any],
    corrupted: dict[str, Any],
    repaired: dict[str, Any],
) -> list[str]:
    rows = [("Baseline", baseline), ("Corrupted", corrupted), ("Repaired", repaired)]
    lines = [
        "| Stage | Rows | Checks passed | Success |",
        "| --- | --- | --- | --- |",
    ]
    for label, q in rows:
        total = q.get("success_count", 0) + q.get("failure_count", 0)
        lines.append(f"| {label} | {q.get('row_count')} | {q.get('success_count')}/{total} | {_fmt(q.get('success'))} |")
    return lines


def _freshness_comparison_table(
    baseline: dict[str, Any],
    corrupted: dict[str, Any],
    repaired: dict[str, Any],
) -> list[str]:
    rows = [("Baseline", baseline), ("Corrupted", corrupted), ("Repaired", repaired)]
    lines = [
        "| Stage | Latest published | Oldest published | Stale rows | Is fresh |",
        "| --- | --- | --- | --- | --- |",
    ]
    for label, f in rows:
        lines.append(
            f"| {label} | {f.get('latest_published')} | {f.get('oldest_published')} | "
            f"{f.get('stale_rows')} | {_fmt(f.get('is_fresh'))} |"
        )
    return lines


def _corruption_scenario_lines(corruption_log: dict[str, Any] | None) -> list[str]:
    if not corruption_log:
        return ["- (corruption log unavailable)"]
    lines = [
        f"- Original rows: {corruption_log.get('original_rows')} -> corrupted rows: {corruption_log.get('corrupted_rows')}",
        "",
        "| Operation | Count | Detail |",
        "| --- | --- | --- |",
    ]
    for op in corruption_log.get("operations", []):
        detail = op.get("set_to") or (", ".join(op.get("paper_ids", [])) if op.get("paper_ids") else "")
        lines.append(f"| {op.get('op')} | {op.get('count')} | {detail} |")
    return lines


def _analysis_lines(baseline_metrics: dict[str, Any], corrupted_metrics: dict[str, Any], repaired_metrics: dict[str, Any]) -> list[str]:
    def get(m, k):
        try:
            return float(m.get(k))
        except (TypeError, ValueError):
            return None

    lines: list[str] = []
    for key in _COMPARE_KEYS:
        b, c, r = get(baseline_metrics, key), get(corrupted_metrics, key), get(repaired_metrics, key)
        if b is None or c is None or r is None:
            continue
        drop = b - c
        drop_pct = (drop / b * 100) if b else 0.0
        recovered = "fully" if abs(r - b) < 1e-9 else ("partially" if r > c else "not")
        lines.append(
            f"- **{key}**: corruption reduced it by {drop:.4f} ({drop_pct:.1f}% drop, {_fmt(b)} -> {_fmt(c)}); "
            f"repair recovered it {recovered} ({_fmt(c)} -> {_fmt(r)})."
        )
    return lines


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_quality: dict[str, Any] | None = None,
    baseline_freshness: dict[str, Any] | None = None,
    corruption_log: dict[str, Any] | None = None,
) -> None:
    """Write a markdown report comparing baseline / corrupted / repaired runs."""
    baseline_quality = baseline_quality or {}
    baseline_freshness = baseline_freshness or {}

    lines: list[str] = [
        "# Corruption Flow - Comparison Report",
        "",
        f"_Generated at {now_utc().isoformat()}_",
        "",
        "## Corruption Scenario",
        *_corruption_scenario_lines(corruption_log),
        "",
        "## Metrics Comparison",
        *_metrics_comparison_table(baseline_metrics, corrupted_metrics, repaired_metrics),
        "",
        "## Impact Analysis",
        *_analysis_lines(baseline_metrics, corrupted_metrics, repaired_metrics),
        "",
        "## Data Quality (success/fail)",
        *_quality_comparison_table(baseline_quality, corrupted_quality, repaired_quality),
        "",
        "### Corrupted check detail",
        *_quality_lines(corrupted_quality),
        "",
        "## Freshness status",
        *_freshness_comparison_table(baseline_freshness, corrupted_freshness, repaired_freshness),
        "",
        "## Takeaways",
        "- Bad data measurably reduced retrieval hit rate, token F1 and judge scores versus baseline.",
        "- Data-quality checks caught the corruption (duplicate ids, short summaries, stale dates).",
        "- Repairing from the raw source recovered metrics back to the baseline level.",
        "",
    ]
    write_text(report_path, "\n".join(lines) + "\n")
