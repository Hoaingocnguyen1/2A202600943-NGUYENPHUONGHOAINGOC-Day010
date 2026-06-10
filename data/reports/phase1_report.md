# Phase 1 - Baseline Pipeline Report

_Generated at 2026-06-10T07:43:18.855699+00:00_

## Source
- API: Crossref REST API
- Query: agentic retrieval augmented generation large language model
- Filter: from-pub-date:2025-12-12,has-abstract:true
- Records fetched: 24
- Clean records: 24

## Evaluation Metrics
| Metric | Value |
| --- | --- |
| samples | 18 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 1.0000 |
| mean_judge_score | 5 |

- Ragas: {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}

### Per question-type breakdown
| Question type | Samples | Hit rate | Mean token F1 | Judge accuracy |
| --- | --- | --- | --- | --- |
| authors | 6 | 1.0000 | 1.0000 | 1.0000 |
| date | 6 | 1.0000 | 1.0000 | 1.0000 |
| summary | 6 | 1.0000 | 1.0000 | 1.0000 |

## Data Quality
- Rows: 24
- Passed checks: 6/6
- Overall success: yes

| Check | Success | Observed | Expected |
| --- | --- | --- | --- |
| row_count_minimum | yes | 24 | >= 5 |
| paper_id_not_null | yes | 0 | 0 nulls |
| paper_id_unique | yes | 0 | 0 duplicates |
| title_not_null | yes | 0 | 0 nulls |
| summary_min_length | yes | 0 | 0 rows < 80 chars |
| freshness_within_threshold | yes | 0 | 0 rows older than 180 days |

## Freshness
- Latest published: 2027-05-07
- Oldest published: 2026-12-01
- Fresh rows: 24 / 24
- Stale rows: 0 (ratio 0.0)
- Is fresh: yes

