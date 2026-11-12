"""Data integrity: schema, uniqueness, counts and SHA-256 checksums."""

from __future__ import annotations

import hashlib
import json

import pytest

from persianeval.tasks import get_task
from persianeval.tasks.base import DATA_ROOT

CHECKSUM_FILE = DATA_ROOT / "SHA256SUMS"


def test_checksum_file_covers_every_dataset() -> None:
    datasets = {path.name for path in DATA_ROOT.glob("*.jsonl")}
    listed = {line.split("  ")[1] for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines()}
    assert listed == datasets


@pytest.mark.parametrize("dataset", sorted(path.name for path in DATA_ROOT.glob("*.jsonl")), ids=str)
def test_dataset_matches_recorded_checksum(dataset: str) -> None:
    lines = CHECKSUM_FILE.read_text(encoding="utf-8").splitlines()
    expected = next(line.split("  ")[0] for line in lines if line.endswith(dataset))
    digest = hashlib.sha256((DATA_ROOT / dataset).read_bytes()).hexdigest()
    assert digest == expected


@pytest.mark.parametrize("dataset", sorted(path.name for path in DATA_ROOT.glob("*.jsonl")), ids=str)
def test_dataset_rows_match_schema(dataset: str) -> None:
    task_name = dataset.removesuffix(".jsonl")
    task = get_task(task_name)
    seen_ids: set[str] = set()
    for lineno, line in enumerate((DATA_ROOT / dataset).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        assert set(row) == {"id", "prompt", "expected", "metadata"}, f"{dataset}:{lineno}"
        assert isinstance(row["metadata"], dict), f"{dataset}:{lineno}"
        assert row["id"] not in seen_ids, f"duplicate id at {dataset}:{lineno}"
        seen_ids.add(row["id"])
        assert row["prompt"].strip() and row["expected"].strip(), f"{dataset}:{lineno}"
    assert len(seen_ids) >= task.min_samples


def test_translation_directions_are_balanced() -> None:
    rows = [
        json.loads(line)
        for line in (DATA_ROOT / "translation_fa_en.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    directions = {row["metadata"]["direction"] for row in rows}
    assert directions == {"fa2en", "en2fa"}
    registers = {row["metadata"]["register"] for row in rows}
    assert registers == {"everyday", "proverb", "formal", "question"}


def test_cultural_options_always_four_with_valid_answer() -> None:
    rows = [
        json.loads(line)
        for line in (DATA_ROOT / "cultural_knowledge.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    for row in rows:
        assert len(row["metadata"]["options"]) == 4
        assert row["expected"] in {"الف", "ب", "ج", "د"}
        answer_index = {"الف": 0, "ب": 1, "ج": 2, "د": 3}[row["expected"]]
        answer_text = row["metadata"]["options"][answer_index]
        assert answer_text == row["metadata"]["answer_text"]


def test_dataset_prompts_are_unique() -> None:
    for path in DATA_ROOT.glob("*.jsonl"):
        prompts = [
            json.loads(line)["prompt"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(prompts) == len(set(prompts)), f"duplicate prompts in {path.name}"


def test_no_placeholder_markers_in_datasets() -> None:
    for path in DATA_ROOT.glob("*.jsonl"):
        content = path.read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX", "PLACEHOLDER", "?????"):
            assert marker not in content, f"{marker} found in {path.name}"
