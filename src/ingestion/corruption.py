from __future__ import annotations

from datetime import date

import pandas as pd

from core.utils import write_json


def _rebuild_embedding_text(row: pd.Series) -> str:
    lines = [
        f"Title: {row['title']}",
        f"Summary: {row['summary']}",
    ]
    if row.get("authors_joined"):
        lines.append(f"Authors: {row['authors_joined']}")
    if row.get("categories_joined"):
        lines.append(f"Categories: {row['categories_joined']}")
    return "\n".join(lines)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate several realistic data-corruption scenarios.

    1. Drop some latest records.
    2. Blank summary on some rows.
    3. Inject noise into text.
    4. Truncate titles.
    5. Make published dates stale.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Write a corruption log.
    """
    if df is None or df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")

    corrupted = df.copy().reset_index(drop=True)
    n = len(corrupted)
    log: dict[str, object] = {"original_rows": n, "operations": []}

    # 1. Drop a handful of the latest records (df is sorted newest first).
    drop_count = max(1, n // 6)
    dropped_ids = corrupted.head(drop_count)["paper_id"].tolist()
    corrupted = corrupted.iloc[drop_count:].reset_index(drop=True)
    log["operations"].append({"op": "drop_latest_records", "count": drop_count, "paper_ids": dropped_ids})

    # 2. Blank out summaries on some rows.
    blank_count = max(1, len(corrupted) // 5)
    blank_idx = corrupted.head(blank_count).index
    corrupted.loc[blank_idx, "summary"] = ""
    corrupted.loc[blank_idx, "summary_chars"] = 0
    log["operations"].append({"op": "blank_summary", "count": int(blank_count)})

    # 3. Inject noise into some summaries.
    noise = " ###@@@ corrupted-token lorem-ipsum-noise %%% "
    noise_idx = corrupted.iloc[blank_count : blank_count + max(1, len(corrupted) // 5)].index
    corrupted.loc[noise_idx, "summary"] = corrupted.loc[noise_idx, "summary"].astype(str) + noise
    corrupted.loc[noise_idx, "summary_chars"] = corrupted.loc[noise_idx, "summary"].str.len()
    log["operations"].append({"op": "inject_noise", "count": int(len(noise_idx))})

    # 4. Truncate titles on some rows.
    trunc_count = max(1, len(corrupted) // 5)
    trunc_idx = corrupted.tail(trunc_count).index
    corrupted.loc[trunc_idx, "title"] = corrupted.loc[trunc_idx, "title"].str[:8]
    log["operations"].append({"op": "truncate_title", "count": int(trunc_count)})

    # 5. Make some publication dates stale (very old).
    stale_count = max(1, len(corrupted) // 4)
    stale_idx = corrupted.tail(stale_count).index
    stale_value = "2005-01-01"
    corrupted.loc[stale_idx, "published"] = stale_value
    today = date.today()
    stale_age = (today - date(2005, 1, 1)).days
    corrupted.loc[stale_idx, "age_days"] = stale_age
    log["operations"].append({"op": "stale_publication_date", "count": int(stale_count), "set_to": stale_value})

    # 7. Rebuild embedding text so corruption actually reaches the index.
    corrupted["text_for_embedding"] = corrupted.apply(_rebuild_embedding_text, axis=1)

    # 6. Add duplicate rows (after rebuild so duplicates carry corrupted text).
    dup_count = max(1, len(corrupted) // 6)
    duplicates = corrupted.head(dup_count).copy()
    corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
    log["operations"].append({"op": "add_duplicates", "count": int(dup_count)})

    log["corrupted_rows"] = len(corrupted)
    write_json(output_log_path, log)
    return corrupted
