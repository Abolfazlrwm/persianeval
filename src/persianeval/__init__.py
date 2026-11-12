"""PersianEval: the first serious open-source benchmark for Persian (Farsi) LLMs.

PersianEval ships 8 frozen evaluation tasks, an async provider-agnostic
harness (OpenAI, Anthropic, Ollama, vLLM), reproducible scoring
(exact / fuzzy / LLM-as-judge) and a static leaderboard generator.
"""

from __future__ import annotations

from importlib import metadata
from typing import Final

from persianeval.harness.results import ItemResult, RunResult
from persianeval.tasks import (
    AbstractTask,
    Sample,
    ScoringKind,
    ScoringSpec,
    all_task_classes,
    get_task,
    list_task_names,
)

try:  # pragma: no cover - depends on installation state
    _detected_version = metadata.version("persianeval")
except metadata.PackageNotFoundError:  # pragma: no cover - editable/source checkout
    _detected_version = "0.0.0.dev0"

__version__: Final[str] = _detected_version

__all__ = [
    "AbstractTask",
    "ItemResult",
    "RunResult",
    "Sample",
    "ScoringKind",
    "ScoringSpec",
    "__version__",
    "all_task_classes",
    "get_task",
    "list_task_names",
]
