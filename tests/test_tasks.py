"""Tests for the task registry, sample loading and per-task invariants."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from persianeval.tasks import (
    builtin_task_classes,
    get_task,
    list_task_names,
)
from persianeval.tasks.base import SampleValidationError

EXPECTED_TASKS = {
    "reasoning",
    "reading_comprehension",
    "spelling",
    "cultural_knowledge",
    "translation_fa_en",
    "rag_faithfulness",
    "bias_detection",
    "code_with_persian_comments",
}


def test_registry_contains_exactly_the_eight_builtin_tasks() -> None:
    names = {task_class().name for task_class in builtin_task_classes()}
    assert names == EXPECTED_TASKS
    assert set(list_task_names()) == EXPECTED_TASKS


def test_get_task_returns_fresh_instances() -> None:
    first = get_task("reasoning")
    second = get_task("reasoning")
    assert first is not second
    assert first.name == second.name == "reasoning"


def test_get_task_unknown_name_raises_with_available_names() -> None:
    with pytest.raises(KeyError) as excinfo:
        get_task("does_not_exist")
    assert "reasoning" in str(excinfo.value)


def test_task_load_samples_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import persianeval.tasks.base as base

    monkeypatch.setattr(base, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(base, "_SAMPLE_CACHE", {})
    task = get_task("reasoning")
    with pytest.raises(FileNotFoundError):
        task.load_samples()


def test_load_samples_rejects_count_below_minimum(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import json

    import persianeval.tasks.base as base

    monkeypatch.setattr(base, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(base, "_SAMPLE_CACHE", {})
    row = {"id": "cultural_knowledge-0001", "prompt": "q", "expected": "الف", "metadata": {}}
    (tmp_path / "cultural_knowledge.jsonl").write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SampleValidationError):
        get_task("cultural_knowledge").load_samples()


@pytest.mark.parametrize("name", sorted(EXPECTED_TASKS))
def test_task_data_loads_and_meets_minimums(name: str) -> None:
    task = get_task(name)
    samples = task.load_samples()
    assert len(samples) >= task.min_samples
    assert len({sample.id for sample in samples}) == len(samples)
    for sample in samples:
        assert sample.id.startswith(f"{name}-")
        assert sample.prompt.strip()
        assert sample.expected.strip()


def test_reasoning_families_and_answer_format() -> None:
    task = get_task("reasoning")
    samples = task.load_samples()
    assert len(samples) == 200
    families = {sample.metadata["family"] for sample in samples}
    assert len(families) == 7
    # Every reasoning expected answer must be a Persian-digit number or a name.
    persian_digits = set("۰۱۲۳۴۵۶۷۸۹٬")
    for sample in samples[:20]:
        if sample.metadata["family"] == "ordering":
            continue
        assert set(sample.expected) & persian_digits, sample.expected


def test_rag_faithfulness_label_balance() -> None:
    samples = get_task("rag_faithfulness").load_samples()
    labels = [sample.metadata["label"] for sample in samples]
    assert labels.count("faithful") == 100
    assert labels.count("unfaithful") == 100


def test_spelling_covers_all_four_families() -> None:
    samples = get_task("spelling").load_samples()
    families = {sample.metadata["family"] for sample in samples}
    assert families == {"homoglyph_choice", "homoglyph_detect", "sentence_fix", "zwnj_choice"}


def test_bias_detection_axis_coverage() -> None:
    samples = get_task("bias_detection").load_samples()
    axes = {sample.metadata["axis"] for sample in samples}
    assert axes == {"ethnic_regional", "gender", "control"}
    groups = {sample.metadata["group"] for sample in samples if sample.metadata["group"]}
    assert len(groups) == 9


def test_code_task_tests_are_wellformed() -> None:
    samples = get_task("code_with_persian_comments").load_samples()
    for sample in samples[:10]:
        tests = sample.metadata["tests"]
        assert len(tests) >= 3
        for args, expected in tests:
            assert isinstance(args, list)
            assert expected is not None


def test_sample_from_dict_validation() -> None:
    from persianeval.tasks.base import Sample

    with pytest.raises(SampleValidationError):
        Sample.from_dict({"id": "x", "prompt": "y"}, task_name="t")
    with pytest.raises(SampleValidationError):
        Sample.from_dict({"id": "x", "prompt": "", "expected": "e"}, task_name="t")
    sample = Sample.from_dict(
        {"id": "t-1", "prompt": "q", "expected": "e", "metadata": {"k": 1}}, task_name="t"
    )
    assert sample.metadata == {"k": 1}


def test_load_samples_caches_per_task() -> None:
    task = get_task("cultural_knowledge")
    first = task.load_samples()
    second = task.load_samples()
    assert first is second


def test_deterministic_subset_sampling_is_seed_stable() -> None:
    samples = sorted(get_task("reasoning").load_samples(), key=lambda s: s.id)
    for seed in (1, 42):
        rng_a, rng_b = random.Random(seed), random.Random(seed)
        pick_a = sorted(rng_a.sample(samples, 10), key=lambda s: s.id)
        pick_b = sorted(rng_b.sample(samples, 10), key=lambda s: s.id)
        assert [s.id for s in pick_a] == [s.id for s in pick_b]
