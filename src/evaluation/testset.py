from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def _select_papers(df: pd.DataFrame, max_papers: int = 6) -> pd.DataFrame:
    """Pick representative papers: well-formed summary, authors and categories."""
    usable = df[
        (df["summary_chars"] >= 80)
        & (df["authors_joined"].astype(bool))
        & (df["categories_joined"].astype(bool))
    ]
    if usable.empty:
        usable = df
    return usable.head(max_papers)


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build an evaluation set from the cleaned dataframe.

    Each sample has: id, question_type, question, ground_truth, ground_truth_doc_ids.
    Question phrasing is aligned with the heuristic answer extractor in
    `retrieval/qa.py` (summary / authors / date / categories).
    """
    if df is None or df.empty or len(df) < 3:
        raise ValueError("Need at least 3 cleaned documents to build a test set.")

    selected = _select_papers(df)
    samples: list[dict[str, Any]] = []

    for _, row in selected.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]
        doc_ids = [paper_id]

        samples.append(
            {
                "id": f"summary::{paper_id}",
                "question_type": "summary",
                "question": f"Summarize the paper titled '{title}'.",
                "ground_truth": first_sentence(row["summary"]),
                "ground_truth_doc_ids": doc_ids,
            }
        )
        if row["authors_joined"]:
            samples.append(
                {
                    "id": f"authors::{paper_id}",
                    "question_type": "authors",
                    "question": f"Who authored the paper titled '{title}'?",
                    "ground_truth": row["authors_joined"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )
        if row["published"]:
            samples.append(
                {
                    "id": f"date::{paper_id}",
                    "question_type": "date",
                    "question": f"When was the paper titled '{title}' published on?",
                    "ground_truth": row["published"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )
        if row["categories_joined"]:
            samples.append(
                {
                    "id": f"categories::{paper_id}",
                    "question_type": "categories",
                    "question": f"What categories does the paper titled '{title}' belong to?",
                    "ground_truth": row["categories_joined"],
                    "ground_truth_doc_ids": doc_ids,
                }
            )

    write_json(output_path, samples)
    return samples
