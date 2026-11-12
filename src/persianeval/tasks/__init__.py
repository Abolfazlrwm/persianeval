"""Task registry for PersianEval.

Builtin tasks are subclasses of :class:`~persianeval.tasks.base.AbstractTask`
living in this package. External packages can plug in additional tasks by
exposing an entry point in the ``persianeval.tasks`` group.
"""

from __future__ import annotations

import logging
from importlib import metadata
from typing import Final

from persianeval.tasks.base import (
    AbstractTask,
    Sample,
    SampleValidationError,
    ScoringKind,
    ScoringSpec,
)
from persianeval.tasks.bias_detection import BiasDetectionTask
from persianeval.tasks.code_with_persian_comments import CodeWithPersianCommentsTask
from persianeval.tasks.cultural_knowledge import CulturalKnowledgeTask
from persianeval.tasks.rag_faithfulness import RagFaithfulnessTask
from persianeval.tasks.reading_comprehension import ReadingComprehensionTask
from persianeval.tasks.reasoning import ReasoningTask
from persianeval.tasks.spelling import SpellingTask
from persianeval.tasks.translation_fa_en import TranslationFaEnTask

_LOGGER = logging.getLogger(__name__)

_BUILTIN: Final[tuple[type[AbstractTask], ...]] = (
    ReasoningTask,
    ReadingComprehensionTask,
    SpellingTask,
    CulturalKnowledgeTask,
    TranslationFaEnTask,
    RagFaithfulnessTask,
    BiasDetectionTask,
    CodeWithPersianCommentsTask,
)

#: Entry point group scanned for third-party tasks.
ENTRY_POINT_GROUP: Final[str] = "persianeval.tasks"


def builtin_task_classes() -> tuple[type[AbstractTask], ...]:
    """Return the eight builtin task classes, in canonical order."""
    return _BUILTIN


def all_task_classes() -> dict[str, type[AbstractTask]]:
    """Return the merged registry of builtin and third-party task classes.

    Third-party tasks are discovered via the ``persianeval.tasks`` entry
    point group. Broken entry points are logged and skipped so that one
    bad plugin cannot take the whole CLI down.

    Returns:
        Mapping from task name to task class.
    """
    registry: dict[str, type[AbstractTask]] = {cls.name: cls for cls in _BUILTIN}
    for entry_point in metadata.entry_points(group=ENTRY_POINT_GROUP):
        try:
            loaded: object = entry_point.load()
        except Exception:
            _LOGGER.warning("skipping broken task entry point '%s'", entry_point.name)
            continue
        if isinstance(loaded, type) and issubclass(loaded, AbstractTask):
            registry.setdefault(loaded.name, loaded)
    return registry


def get_task(name: str) -> AbstractTask:
    """Instantiate a task by its machine name.

    Args:
        name: Task name, e.g. ``"reasoning"``.

    Returns:
        A fresh, stateless task instance.

    Raises:
        KeyError: If no task with that name is registered.
    """
    try:
        return all_task_classes()[name]()
    except KeyError:
        available = ", ".join(sorted(all_task_classes()))
        msg = f"unknown task '{name}'; available tasks: {available}"
        raise KeyError(msg) from None


def list_task_names() -> list[str]:
    """Return all registered task names, sorted alphabetically."""
    return sorted(all_task_classes())


__all__ = [
    "AbstractTask",
    "Sample",
    "SampleValidationError",
    "ScoringKind",
    "ScoringSpec",
    "all_task_classes",
    "builtin_task_classes",
    "get_task",
    "list_task_names",
]
