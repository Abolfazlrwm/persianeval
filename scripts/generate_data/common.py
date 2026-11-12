"""Shared helpers for the PersianEval data generators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persianeval.tasks.base import DATA_ROOT

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
"""Persian digit glyphs indexed by their ASCII value."""


def fa_num(value: int) -> str:
    """Format an integer with Persian digits and the Persian thousands separator."""
    grouped = f"{value:,}".replace(",", "\u066c")
    return grouped.translate(str.maketrans("0123456789", FA_DIGITS))


def write_jsonl(task_name: str, rows: list[dict[str, Any]]) -> Path:
    """Write samples for a task to its frozen v1 JSONL file.

    Args:
        task_name: Machine task name (used as the output file name).
        rows: Sample dicts with ``id``, ``prompt``, ``expected``, ``metadata``.

    Returns:
        The written file path.
    """
    path = DATA_ROOT / f"{task_name}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{task_name}: wrote {len(rows)} samples -> {path}")
    return path
