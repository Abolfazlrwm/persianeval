"""Explicit result schemas (pydantic) with JSON and Parquet persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, Field

#: Version of the on-disk result schema; bumped on breaking changes.
SCHEMA_VERSION: Final[str] = "1.0"


class ItemResult(BaseModel):
    """Scored outcome for a single sample."""

    id: str
    score: float
    passed: bool
    response: str
    expected: str
    scorer: str
    details: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0
    cached: bool = False


class RunResult(BaseModel):
    """Complete, self-describing output of one evaluation run."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    task: str
    model: str
    provider: str
    org: str = ""
    license: str = ""
    seed: int
    temperature: float
    max_tokens: int
    concurrency: int
    started_at: str
    finished_at: str
    n_items: int
    n_cached: int = 0
    metrics: dict[str, float] = Field(default_factory=dict)
    items: list[ItemResult] = Field(default_factory=list)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def save_json(result: RunResult, path: Path) -> Path:
    """Persist a run result as UTF-8 JSON.

    Args:
        result: The run to persist.
        path: Destination file (parent directories are created).

    Returns:
        The written path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_json(path: Path) -> RunResult:
    """Load a run result from JSON.

    Args:
        path: Source file.

    Returns:
        The validated :class:`RunResult`.
    """
    return RunResult.model_validate_json(path.read_text(encoding="utf-8"))


def save_parquet(result: RunResult, path: Path) -> Path:
    """Persist the run's items (plus run metadata) as Parquet.

    Args:
        result: The run to persist.
        path: Destination file (parent directories are created).

    Returns:
        The written path.

    Raises:
        RuntimeError: If ``pyarrow`` is not importable.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - pyarrow is a core dependency
        msg = "pyarrow is required for Parquet output: pip install pyarrow"
        raise RuntimeError(msg) from exc

    rows: list[dict[str, Any]] = []
    for item in result.items:
        rows.append(
            {
                "run_id": result.run_id,
                "task": result.task,
                "model": result.model,
                "provider": result.provider,
                "org": result.org,
                "license": result.license,
                "seed": result.seed,
                "temperature": result.temperature,
                "item_id": item.id,
                "score": item.score,
                "passed": item.passed,
                "response": item.response,
                "expected": item.expected,
                "scorer": item.scorer,
                "details_json": json.dumps(item.details, ensure_ascii=False),
                "latency_ms": item.latency_ms,
                "cached": item.cached,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression="snappy")
    return path


def model_slug(model: str) -> str:
    """Return a filesystem-safe slug for a model identifier."""
    return "".join(char if char.isalnum() or char in "-._" else "-" for char in model).strip("-")
