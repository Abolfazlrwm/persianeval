"""Tests for persianeval.harness.validation and the validate-results CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from persianeval.cli import app
from persianeval.harness.results import ItemResult, RunResult, save_json, utc_now_iso
from persianeval.harness.validation import check_result, collect_json_files, validate_file

runner = CliRunner()

# Registered task names are stable; reasoning is used as the fixture task.
FIXTURE_TASK = "reasoning"


def make_items(n: int, *, score: float = 1.0) -> list[ItemResult]:
    """Build n deterministic, uniquely-identified items."""
    return [
        ItemResult(
            id=f"item-{i:04d}",
            score=score,
            passed=score >= 0.5,
            response=f"response {i}",
            expected=f"expected {i}",
            scorer="exact_match",
            latency_ms=10.0,
        )
        for i in range(n)
    ]


def make_result(n: int = 2, **overrides: Any) -> RunResult:
    """Build a self-consistent result whose metrics match its items."""
    supplied: list[ItemResult] | None = overrides.pop("items", None)
    items = supplied if supplied is not None else make_items(n)
    n_passed = sum(item.passed for item in items)
    count = len(items)
    defaults: dict[str, Any] = {
        "run_id": "deadbeef1234",
        "task": FIXTURE_TASK,
        "model": "test-model",
        "provider": "dummy",
        "org": "Test Org",
        "license": "Apache-2.0",
        "seed": 42,
        "temperature": 0.0,
        "max_tokens": 128,
        "concurrency": 1,
        "started_at": utc_now_iso(),
        "finished_at": utc_now_iso(),
        "n_items": count,
        "n_cached": 0,
        "metrics": {
            "accuracy": round(n_passed / count, 4) if count else 0.0,
            "mean_score": round(sum(i.score for i in items) / count, 4) if count else 0.0,
            "avg_latency_ms": 10.0,
        },
        "items": items,
    }
    defaults.update(overrides)
    return RunResult.model_validate(defaults)


def write_result(tmp_path: Path, result: RunResult, name: str = "run.json") -> Path:
    """Persist a result fixture and return its path."""
    path = tmp_path / name
    save_json(result, path)
    return path


# ---------------------------------------------------------------------------
# check_result: clean pass
# ---------------------------------------------------------------------------


def test_check_result_accepts_full_corpus_run() -> None:
    """A 200-item run (task minimum) with matching metrics has no findings."""
    errors, warnings = check_result(make_result(200))
    assert errors == []
    assert warnings == []


def test_check_result_flags_subset_run_as_warning_only() -> None:
    errors, warnings = check_result(make_result(20))
    assert errors == []
    assert any("subset run" in warning for warning in warnings)


# ---------------------------------------------------------------------------
# check_result: errors
# ---------------------------------------------------------------------------


def test_check_result_flags_unknown_task() -> None:
    errors, _ = check_result(make_result(task="not_a_task"))
    assert any("unknown task" in error for error in errors)


def test_check_result_flags_n_items_mismatch() -> None:
    errors, _ = check_result(make_result(n=5, n_items=9))
    assert any("n_items=9 but 5 items" in error for error in errors)


def test_check_result_flags_zero_items() -> None:
    errors, _ = check_result(make_result(n=1, items=make_items(0), n_items=0))
    assert any("no scored items" in error for error in errors)


def test_check_result_flags_duplicate_item_ids() -> None:
    items = make_items(2)
    items[1] = items[0].model_copy()
    errors, _ = check_result(make_result(items=items))
    assert any("duplicate item id" in error for error in errors)


def test_check_result_flags_score_out_of_range() -> None:
    items = [make_items(1)[0].model_copy(update={"score": 1.5})]
    errors, _ = check_result(make_result(items=items))
    assert any("outside [0, 1]" in error for error in errors)


def test_check_result_flags_accuracy_drift() -> None:
    result = make_result()
    result.metrics["accuracy"] = 0.99  # items say 1.0
    errors, _ = check_result(result)
    assert any("accuracy" in error and "does not match" in error for error in errors)


def test_check_result_flags_mean_score_drift() -> None:
    result = make_result()
    result.metrics["mean_score"] = 0.42  # items say 1.0
    errors, _ = check_result(result)
    assert any("mean_score" in error and "does not match" in error for error in errors)


def test_check_result_flags_metrics_outside_unit_range() -> None:
    result = make_result()
    result.metrics["accuracy"] = 1.5
    result.metrics["mean_score"] = -0.1
    errors, _ = check_result(result)
    assert any("metrics.accuracy outside" in error for error in errors)
    assert any("metrics.mean_score outside" in error for error in errors)


def test_check_result_flags_finished_before_started() -> None:
    errors, _ = check_result(
        make_result(
            started_at="2026-11-25T12:00:00+00:00",
            finished_at="2026-11-25T11:00:00+00:00",
        )
    )
    assert any("before started_at" in error for error in errors)


def test_check_result_flags_invalid_timestamps() -> None:
    errors, _ = check_result(make_result(started_at="yesterday", finished_at="tomorrow-ish"))
    assert any("ISO-8601" in error for error in errors)


def test_check_result_flags_empty_model_and_provider() -> None:
    errors, _ = check_result(make_result(model="", provider=""))
    assert any("model is empty" in error for error in errors)
    assert any("provider is empty" in error for error in errors)


def test_check_result_flags_wrong_schema_version() -> None:
    errors, _ = check_result(make_result(schema_version="9.9"))
    assert any("unsupported schema_version" in error for error in errors)


# ---------------------------------------------------------------------------
# check_result: warnings
# ---------------------------------------------------------------------------


def test_check_result_warns_on_nondeterministic_temperature() -> None:
    _, warnings = check_result(make_result(temperature=0.7))
    assert any("temperature" in warning for warning in warnings)


def test_check_result_warns_on_cached_items() -> None:
    _, warnings = check_result(make_result(n_cached=3))
    assert any("cache" in warning for warning in warnings)


def test_check_result_warns_on_missing_metadata() -> None:
    _, warnings = check_result(make_result(org="", license=""))
    assert any("org metadata is empty" in warning for warning in warnings)
    assert any("license metadata is empty" in warning for warning in warnings)


# ---------------------------------------------------------------------------
# validate_file / collect_json_files
# ---------------------------------------------------------------------------


def test_validate_file_reports_unparsable_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text('{"hello": "world"}', encoding="utf-8")
    errors, warnings = validate_file(path)
    assert len(errors) == 1
    assert "not a valid RunResult JSON file" in errors[0]
    assert warnings == []


def test_collect_json_files_expands_directories(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "b.json").write_text("{}", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    files = collect_json_files([tmp_path / "a.json", tmp_path])
    names = [file.name for file in files]
    assert names == ["a.json", "b.json"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_validate_results_passes_with_warnings(tmp_path: Path) -> None:
    path = write_result(tmp_path, make_result(20))  # subset run -> warnings
    exit_code = runner.invoke(app, ["validate-results", str(path)]).exit_code
    assert exit_code == 0


def test_cli_validate_results_fails_on_drift(tmp_path: Path) -> None:
    result = make_result()
    result.metrics["accuracy"] = 0.123
    path = write_result(tmp_path, result)
    outcome = runner.invoke(app, ["validate-results", str(path)])
    assert outcome.exit_code == 1
    assert "FAIL" in outcome.output


def test_cli_validate_results_fails_on_unparsable_file(tmp_path: Path) -> None:
    path = tmp_path / "garbage.json"
    path.write_text("[]", encoding="utf-8")
    outcome = runner.invoke(app, ["validate-results", str(path)])
    assert outcome.exit_code == 1


def test_cli_validate_results_directory(tmp_path: Path) -> None:
    write_result(tmp_path, make_result(20), name="one.json")
    write_result(tmp_path, make_result(20), name="two.json")
    (tmp_path / "notes.txt").write_text("skip me", encoding="utf-8")
    outcome = runner.invoke(app, ["validate-results", str(tmp_path)])
    assert outcome.exit_code == 0
    assert "all 2 file(s) valid" in outcome.output


def test_cli_validate_results_no_files_found(tmp_path: Path) -> None:
    outcome = runner.invoke(app, ["validate-results", str(tmp_path)])
    assert outcome.exit_code == 2
    assert "no *.json files" in outcome.output


# ---------------------------------------------------------------------------
# Real committed results must validate cleanly (structure, not scores).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "result_file",
    sorted((Path(__file__).parent.parent / "results").glob("*.json")),
    ids=lambda path: path.stem,
)
def test_committed_results_have_no_errors(result_file: Path) -> None:
    errors, _ = validate_file(result_file)
    assert errors == []
