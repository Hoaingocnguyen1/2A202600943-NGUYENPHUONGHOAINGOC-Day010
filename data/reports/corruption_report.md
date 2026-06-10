# Corruption Flow - Comparison Report

_Generated at 2026-06-10T08:14:07.802899+00:00_

## Corruption Scenario
- Original rows: 24 -> corrupted rows: 23

| Operation | Count | Detail |
| --- | --- | --- |
| drop_latest_records | 4 | 10.22158/eltls.v8n3p21, 10.26877/jipmat.v11i1.2279, 10.30656/1intech.v11i2.11359, 10.15294/jvce.v11i2.45302 |
| blank_summary | 4 |  |
| inject_noise | 4 |  |
| truncate_title | 4 |  |
| stale_publication_date | 5 | 2005-01-01 |
| add_duplicates | 3 |  |

## Metrics Comparison
| Metric | Baseline | Corrupted | Repaired | Δ Corrupted | Δ Repaired |
| --- | --- | --- | --- | --- | --- |
| retrieval_hit_rate | 1.0000 | 0.3333 | 1.0000 | -0.6667 | +0.0000 |
| mean_token_f1 | 1.0000 | 0.2987 | 1.0000 | -0.7013 | +0.0000 |
| judge_accuracy | 1.0000 | 0.3889 | 1.0000 | -0.6111 | +0.0000 |
| mean_judge_score | 5 | 2.6667 | 5 | -2.3333 | +0.0000 |

## Impact Analysis
- **retrieval_hit_rate**: corruption reduced it by 0.6667 (66.7% drop, 1.0000 -> 0.3333); repair recovered it fully (0.3333 -> 1.0000).
- **mean_token_f1**: corruption reduced it by 0.7013 (70.1% drop, 1.0000 -> 0.2987); repair recovered it fully (0.2987 -> 1.0000).
- **judge_accuracy**: corruption reduced it by 0.6111 (61.1% drop, 1.0000 -> 0.3889); repair recovered it fully (0.3889 -> 1.0000).
- **mean_judge_score**: corruption reduced it by 2.3333 (46.7% drop, 5.0000 -> 2.6667); repair recovered it fully (2.6667 -> 5.0000).

## Data Quality (success/fail)
| Stage | Rows | Checks passed | Success |
| --- | --- | --- | --- |
| Baseline | 24 | 6/6 | yes |
| Corrupted | 23 | 3/6 | no |
| Repaired | 24 | 6/6 | yes |

### Corrupted check detail
- Rows: 23
- Passed checks: 3/6
- Overall success: no

| Check | Success | Observed | Expected |
| --- | --- | --- | --- |
| row_count_minimum | yes | 23 | >= 5 |
| paper_id_not_null | yes | 0 | 0 nulls |
| paper_id_unique | no | 3 | 0 duplicates |
| title_not_null | yes | 0 | 0 nulls |
| summary_min_length | no | 7 | 0 rows < 80 chars |
| freshness_within_threshold | no | 5 | 0 rows older than 180 days |

## Freshness status
| Stage | Latest published | Oldest published | Stale rows | Is fresh |
| --- | --- | --- | --- | --- |
| Baseline | 2027-05-07 | 2026-12-01 | 0 | yes |
| Corrupted | 2026-12-31 | 2005-01-01 | 5 | no |
| Repaired | 2027-05-07 | 2026-12-01 | 0 | yes |

## Takeaways
- Bad data measurably reduced retrieval hit rate, token F1 and judge scores versus baseline.
- Data-quality checks caught the corruption (duplicate ids, short summaries, stale dates).
- Repairing from the raw source recovered metrics back to the baseline level.

