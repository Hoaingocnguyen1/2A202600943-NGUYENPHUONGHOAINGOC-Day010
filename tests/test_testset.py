from __future__ import annotations

from core.utils import read_json
from evaluation.testset import build_test_set

REQUIRED_KEYS = {"id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"}


def test_build_test_set_schema(clean_df, tmp_path):
    out = tmp_path / "test_set.json"
    samples = build_test_set(clean_df, out)

    assert out.exists()
    assert read_json(out) == samples
    assert len(samples) > 0
    for sample in samples:
        assert REQUIRED_KEYS <= set(sample)
        assert sample["question_type"] in {"summary", "authors", "date", "categories"}
        assert isinstance(sample["ground_truth_doc_ids"], list) and sample["ground_truth_doc_ids"]


def test_ground_truth_doc_ids_reference_real_papers(clean_df, tmp_path):
    samples = build_test_set(clean_df, tmp_path / "ts.json")
    valid_ids = set(clean_df["paper_id"])
    for sample in samples:
        assert set(sample["ground_truth_doc_ids"]) <= valid_ids
