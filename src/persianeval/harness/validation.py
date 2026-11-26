"""Structural validation of run-result files for leaderboard submissions.

``persianeval validate-results`` runs a set of offline, objective checks on
``RunResult`` JSON files before they are submitted to the leaderboard:

* schema conformance (pydantic ``RunResult``) and schema version
* the task name must be a registered task
* ``n_items`` must match the number of scored items; ids must be unique
* per-item scores must be within ``[0, 1]``
* reported ``accuracy`` / ``mean_score`` must match the per-item data
  (beyond the 4-decimal rounding tolerance used by the runner)
* timestamps must be ISO-8601 and ordered (``finished_at >= started_at``)

Anything that cannot be verified objectively (sampling temperature, cached
responses, subset runs, missing metadata) is reported as a *warning*, never
an error: warnings do not fail CI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from persianeval.harness.results import SCHEMA_VERSION, RunResult, load_json
from persianeval.tasks import all_task_classes

#: Max drift between reported and recomputed metrics caused by the runner
#: rounding metrics to four decimal places.
ROUNDING_TOLERANCE: Final[float] = 5e-4


def _parse_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp, assuming UTC for naive values.

    Args:
        raw: Timestamp string from a result file.

    Returns:
        A timezone-aware datetime.

    Raises:
        ValueError: If the string is not valid ISO-8601.
    """
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def check_result(result: RunResult) -> tuple[list[str], list[str]]:
    """Validate one parsed run result.

    Args:
        result: The run result to inspect.

    Returns:
        A ``(errors, warnings)`` tuple. Errors mean the file is not a
        trustworthy leaderboard entry; warnings are informational only.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if result.schema_version != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version {result.schema_version!r} (expected {SCHEMA_VERSION!r})")
    if not result.model:
        errors.append("model is empty")
    if not result.provider:
        errors.append("provider is empty")

    tasks = all_task_classes()
    min_samples: int | None = None
    if result.task not in tasks:
        errors.append(f"unknown task {result.task!r}; registered tasks: {', '.join(sorted(tasks))}")
    else:
        min_samples = tasks[result.task]().min_samples

    if result.n_items == 0:
        errors.append("run has no scored items")
    elif result.n_items != len(result.items):
        errors.append(f"n_items={result.n_items} but {len(result.items)} items are listed")

    seen_ids: set[str] = set()
    for item in result.items:
        if item.id in seen_ids:
            errors.append(f"duplicate item id {item.id!r}")
        seen_ids.add(item.id)
        if not 0.0 <= item.score <= 1.0:
            errors.append(f"item {item.id!r}: score {item.score} outside [0, 1]")

    if result.items:
        n_passed = sum(item.passed for item in result.items)
        recomputed_accuracy = n_passed / len(result.items)
        if not 0.0 <= result.metrics.get("accuracy", -1.0) <= 1.0:
            errors.append("metrics.accuracy outside [0, 1]")
        elif abs(result.metrics.get("accuracy", 0.0) - recomputed_accuracy) > ROUNDING_TOLERANCE:
            errors.append(
                f"metrics.accuracy {result.metrics.get('accuracy', 0.0)} does not match the "
                f"per-item data (recomputed {recomputed_accuracy:.4f} "
                f"from {n_passed}/{len(result.items)} passed)"
            )

        recomputed_mean = sum(item.score for item in result.items) / len(result.items)
        if not 0.0 <= result.metrics.get("mean_score", -1.0) <= 1.0:
            errors.append("metrics.mean_score outside [0, 1]")
        elif abs(result.metrics.get("mean_score", 0.0) - recomputed_mean) > ROUNDING_TOLERANCE:
            errors.append(
                f"metrics.mean_score {result.metrics.get('mean_score', 0.0)} does not match the "
                f"per-item scores (recomputed {recomputed_mean:.4f})"
            )
    elif "accuracy" in result.metrics or "mean_score" in result.metrics:
        errors.append("metrics reported without any items")

    try:
        started = _parse_timestamp(result.started_at)
        finished = _parse_timestamp(result.finished_at)
    except ValueError:
        errors.append("started_at/finished_at are not valid ISO-8601 timestamps")
    else:
        if finished < started:
            errors.append(f"finished_at {result.finished_at} is before started_at {result.started_at}")

    if result.temperature != 0.0:
        warnings.append(
            f"temperature={result.temperature} (leaderboard runs are expected to be deterministic)"
        )
    if result.n_cached > 0:
        warnings.append(f"{result.n_cached} item(s) were served from the response cache")
    if min_samples is not None and 0 < result.n_items < min_samples:
        warnings.append(
            f"subset run: {result.n_items} items is below the task minimum of {min_samples} "
            "(full-corpus runs are preferred; seeded weekly subsamples are accepted)"
        )
    if not result.org:
        warnings.append("org metadata is empty; the leaderboard will render an empty cell")
    if not result.license:
        warnings.append("license metadata is empty; the leaderboard will render an empty cell")

    return errors, warnings


def validate_file(path: Path) -> tuple[list[str], list[str]]:
    """Load and validate one result JSON file.

    Args:
        path: Path to a ``RunResult`` JSON file.

    Returns:
        A ``(errors, warnings)`` tuple. An unreadable or unparsable file
        yields a single error and no warnings.
    """
    try:
        result = load_json(path)
    except (OSError, ValidationError) as exc:
        summary = str(exc).split("For more information", maxsplit=1)[0].strip()
        return ([f"not a valid RunResult JSON file: {summary}"], [])
    return check_result(result)


def collect_json_files(paths: list[Path]) -> list[Path]:
    """Expand user-supplied paths into the concrete list of JSON files.

    Args:
        paths: Files and/or directories. Directories are scanned
            (non-recursively) for ``*.json``.

    Returns:
        The expanded, de-duplicated file list in input order.
    """
    files: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        candidates = sorted(path.glob("*.json")) if path.is_dir() else [path]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files
