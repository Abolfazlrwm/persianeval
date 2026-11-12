"""Core task abstractions and the frozen sample schema.

Every evaluation task in PersianEval implements :class:`AbstractTask`.
Samples are frozen JSONL files under ``src/persianeval/data/v1`` with an
explicit schema: ``{"id", "prompt", "expected", "metadata"}``.
"""

from __future__ import annotations

import json
import logging
from abc import ABC
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Final

_LOGGER = logging.getLogger(__name__)

#: Root of the frozen, checksummed v1 dataset files.
DATA_ROOT: Final[Path] = Path(__file__).resolve().parent.parent / "data" / "v1"


class SampleValidationError(ValueError):
    """Raised when a sample or a data file violates the frozen schema."""


@dataclass(frozen=True, slots=True)
class Sample:
    """A single frozen evaluation sample.

    Attributes:
        id: Globally unique identifier within a task (e.g. ``reasoning-0001``).
        prompt: The complete user prompt shown to the model under evaluation.
        expected: The reference answer used by the task's scorer.
        metadata: Free-form, JSON-serializable provenance (family, source,
            label, solution). Never shown to the model.
    """

    id: str
    prompt: str
    expected: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, task_name: str = "?") -> Sample:
        """Build a :class:`Sample` from a decoded JSONL row and validate it.

        Args:
            raw: Decoded JSON object of one data-file line.
            task_name: Name of the owning task, used in error messages.

        Returns:
            The validated sample.

        Raises:
            SampleValidationError: If required keys are missing or have the
                wrong types.
        """
        required = ("id", "prompt", "expected")
        missing = [key for key in required if key not in raw]
        if missing:
            msg = f"task '{task_name}': sample row is missing keys {missing}"
            raise SampleValidationError(msg)
        for key in required:
            if not isinstance(raw[key], str) or not raw[key].strip():
                msg = f"task '{task_name}': field '{key}' must be a non-empty string"
                raise SampleValidationError(msg)
        metadata = raw.get("metadata", {})
        if not isinstance(metadata, dict):
            msg = f"task '{task_name}': field 'metadata' must be an object"
            raise SampleValidationError(msg)
        return cls(id=raw["id"], prompt=raw["prompt"], expected=raw["expected"], metadata=metadata)


class ScoringKind(StrEnum):
    """Scorer families supported by the harness."""

    EXACT = "exact"
    FUZZY = "fuzzy"
    JUDGE = "judge"


@dataclass(frozen=True, slots=True)
class ScoringSpec:
    """Declarative scoring configuration attached to a task.

    Attributes:
        kind: Which scorer family to use.
        fuzzy_threshold: Minimum similarity (0-1) for ``FUZZY`` to pass.
        judge_prompt: Prompt template for ``JUDGE`` tasks; rendered with the
            keys of :meth:`AbstractTask.judge_context` plus ``response``.
            Must contain only literal JSON braces (escape with ``{{``/``}}``).
        score_pass_threshold: Judge score (0-1) at or above which an item
            counts as passed.
        normalize_keep_zwnj: Keep the Persian zero-width non-joiner during
            normalization instead of stripping it.
    """

    kind: ScoringKind
    fuzzy_threshold: float = 0.90
    judge_prompt: str | None = None
    score_pass_threshold: float = 0.70
    normalize_keep_zwnj: bool = False

    def __post_init__(self) -> None:
        if self.kind is ScoringKind.JUDGE and self.judge_prompt is None:
            msg = "ScoringSpec with kind='judge' requires a judge_prompt template"
            raise ValueError(msg)
        if self.kind is not ScoringKind.JUDGE and self.judge_prompt is not None:
            msg = "judge_prompt is only meaningful for kind='judge'"
            raise ValueError(msg)
        if not 0.0 <= self.fuzzy_threshold <= 1.0 or not 0.0 <= self.score_pass_threshold <= 1.0:
            msg = "thresholds must be within [0, 1]"
            raise ValueError(msg)


class AbstractTask(ABC):
    """Plugin contract for every PersianEval evaluation task.

    Adding a task means subclassing this class, setting the ClassVars,
    shipping a JSONL data file and registering the subclass in
    :mod:`persianeval.tasks`. See ``docs/adding_a_task.md`` for the
    15-minute walkthrough.
    """

    #: Machine name used on the CLI (e.g. ``reasoning``).
    name: ClassVar[str]
    #: English display title.
    title_en: ClassVar[str]
    #: Persian display title.
    title_fa: ClassVar[str]
    #: One-line English description.
    description_en: ClassVar[str]
    #: One-line Persian description.
    description_fa: ClassVar[str]
    #: JSONL file name inside :data:`DATA_ROOT`.
    data_file: ClassVar[str]
    #: Minimum number of samples the file must contain (validated on load).
    min_samples: ClassVar[int]
    #: Scoring configuration.
    scoring: ClassVar[ScoringSpec]
    #: Optional system prompt passed to the model under evaluation.
    system_prompt: ClassVar[str] = ""
    #: Extra tokens stripped from *responses* before exact matching
    #: (e.g. ``"تومان"`` for numeric answers).
    exact_strip_tokens: ClassVar[tuple[str, ...]] = ()
    #: Human-readable provenance summary; the full story lives in
    #: ``src/persianeval/data/README.md``.
    source: ClassVar[str] = ""

    def data_path(self) -> Path:
        """Return the absolute path of this task's frozen data file."""
        return DATA_ROOT / self.data_file

    def load_samples(self) -> tuple[Sample, ...]:
        """Load, validate and cache the task's frozen samples.

        Returns:
            Tuple of validated samples, ordered as they appear in the file.

        Raises:
            FileNotFoundError: If the data file is missing.
            SampleValidationError: On malformed rows, duplicate ids or a
                sample count below :attr:`min_samples`.
        """
        cached = _SAMPLE_CACHE.get(self.name)
        if cached is not None:
            return cached

        path = self.data_path()
        if not path.exists():
            msg = f"data file for task '{self.name}' is missing: {path}"
            raise FileNotFoundError(msg)

        samples: list[Sample] = []
        seen: set[str] = set()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                raw: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError as exc:
                msg = f"{path}:{lineno}: invalid JSON ({exc})"
                raise SampleValidationError(msg) from exc
            sample = Sample.from_dict(raw, task_name=self.name)
            if sample.id in seen:
                msg = f"{path}:{lineno}: duplicate sample id '{sample.id}'"
                raise SampleValidationError(msg)
            seen.add(sample.id)
            samples.append(sample)

        if len(samples) < self.min_samples:
            msg = (
                f"task '{self.name}': {len(samples)} samples found in {path.name}, "
                f"but min_samples={self.min_samples}"
            )
            raise SampleValidationError(msg)

        _LOGGER.info("loaded %d samples for task '%s'", len(samples), self.name)
        _SAMPLE_CACHE[self.name] = tuple(samples)
        return _SAMPLE_CACHE[self.name]

    def build_prompt(self, sample: Sample) -> str:
        """Return the user prompt sent to the model for this sample.

        The frozen v1 datasets embed the complete instruction inside
        ``sample.prompt``; tasks that later need templating should override
        this method.

        Args:
            sample: The sample being evaluated.

        Returns:
            The final user prompt.
        """
        return sample.prompt

    def judge_context(self, sample: Sample) -> dict[str, str]:
        """Return the named fields available to a task's judge prompt.

        Args:
            sample: The sample being judged.

        Returns:
            Mapping with ``question``, ``expected`` and a canonical JSON
            dump of ``metadata``; judge prompts also receive ``response``.
        """
        return {
            "question": sample.prompt,
            "expected": sample.expected,
            "metadata": json.dumps(sample.metadata, ensure_ascii=False, sort_keys=True),
        }


#: Per-process memo for :meth:`AbstractTask.load_samples`.
_SAMPLE_CACHE: Final[dict[str, tuple[Sample, ...]]] = {}
