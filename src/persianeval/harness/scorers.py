"""Persian-aware scoring: exact, fuzzy and LLM-as-judge scorers."""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Final

#: Persian / Arabic characters unified to their canonical Persian form.
_CHAR_MAP: Final[dict[str, str]] = {
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ه",
    "ۀ": "ه",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
}

#: Arabic diacritics (tashkeel) plus tatweel.
_DIACRITICS_RE: Final[re.Pattern[str]] = re.compile(r"[\u064B-\u065F\u0670\u0640]")

#: Anything that is not a word character or whitespace (persian punctuation included).
_PUNCT_RE: Final[re.Pattern[str]] = re.compile(r"[^\w\s]+", re.UNICODE)

#: Numeric thousand separators removed *between digits* before punctuation stripping.
_NUMERIC_SEPARATOR_RE: Final[re.Pattern[str]] = re.compile(r"(?<=\d)[,\u066c](?=\d)")

_ZWNJ: Final[str] = "\u200c"

#: Punctuation sweep that spares the ZWNJ (used when keep_zwnj=True).
_PUNCT_KEEP_ZWNJ_RE: Final[re.Pattern[str]] = re.compile(r"[^\w\s\u200c]+", re.UNICODE)


def normalize_text(text: str, *, keep_zwnj: bool = False) -> str:
    """Normalize Persian text for robust answer comparison.

    The normalization pipeline: lower-case; map Arabic ``ي/ك`` to Persian
    ``ی/ک``; map Persian and Arabic-Indic digits to ASCII; strip numeric
    thousand separators between digits; strip diacritics and tatweel;
    optionally keep the zero-width non-joiner; drop punctuation; collapse
    whitespace.

    Args:
        text: Raw model response or reference answer.
        keep_zwnj: When ``True`` the zero-width non-joiner (U+200C) is kept,
            which matters for tasks that explicitly test half-space usage.

    Returns:
        The normalized string.
    """
    lowered = text.strip().lower()
    mapped = "".join(_CHAR_MAP.get(char, char) for char in lowered)
    without_diacritics = _DIACRITICS_RE.sub("", mapped)
    without_separators = _NUMERIC_SEPARATOR_RE.sub("", without_diacritics)
    # Handle the ZWNJ explicitly before the punctuation sweep replaces it with a space.
    if keep_zwnj:
        without_punct = _PUNCT_KEEP_ZWNJ_RE.sub(" ", without_separators)
    else:
        without_punct = _PUNCT_RE.sub(" ", without_separators.replace(_ZWNJ, ""))
    return " ".join(without_punct.split())


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """Outcome of scoring a single item.

    Attributes:
        score: Continuous score in ``[0, 1]`` (1/0 for exact, similarity
            ratio for fuzzy, judge score for judge).
        passed: Whether the item counts towards the task's accuracy metric.
        details: Scorer-specific diagnostics (e.g. judge rationale).
    """

    score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


class ExactScorer:
    """Exact-match scorer over normalized text with documented leniency.

    The normalized response is accepted when the full string, its first
    token, or its last token equals the normalized reference. Prefix/suffix
    tokens (``پاسخ:``) and trailing units (``تومان``) are the common well-
    behaved response shapes; anything beyond that stays strict.

    Args:
        strip_tokens: Extra tokens removed from the *response* before
            comparison (e.g. currency units after a numeric answer).
        keep_zwnj: Forwarded to :func:`normalize_text`.
    """

    def __init__(self, strip_tokens: tuple[str, ...] = (), *, keep_zwnj: bool = False) -> None:
        self._strip_tokens = strip_tokens
        self._keep_zwnj = keep_zwnj

    @property
    def name(self) -> str:
        """Human-readable scorer name used in result files."""
        return "exact"

    def score(self, expected: str, response: str) -> ScoreResult:
        """Compare ``response`` to ``expected`` after normalization.

        Args:
            expected: Reference answer.
            response: Raw model response.

        Returns:
            A :class:`ScoreResult` with score 1.0 or 0.0.
        """
        candidate = normalize_text(response, keep_zwnj=self._keep_zwnj)
        for token in self._strip_tokens:
            candidate = candidate.replace(f" {token}", "").replace(token, "")
        reference = normalize_text(expected, keep_zwnj=self._keep_zwnj)
        tokens = candidate.split()
        candidates = {candidate, tokens[0] if tokens else "", tokens[-1] if tokens else ""}
        passed = reference in candidates
        return ScoreResult(score=1.0 if passed else 0.0, passed=passed)


class FuzzyScorer:
    """Similarity scorer with a containment bonus for short answers.

    The similarity is the ``difflib.SequenceMatcher`` ratio over normalized
    text; if the normalized reference appears verbatim inside the response
    the score is promoted to 1.0 (long-winded answers that contain the
    correct short answer still pass — a deliberate leniency documented in
    ``docs/methodology.md``).

    Args:
        threshold: Minimum score for an item to pass.
        keep_zwnj: Forwarded to :func:`normalize_text`.
    """

    def __init__(self, threshold: float = 0.90, *, keep_zwnj: bool = False) -> None:
        self._threshold = threshold
        self._keep_zwnj = keep_zwnj

    @property
    def name(self) -> str:
        """Human-readable scorer name used in result files."""
        return f"fuzzy@{self._threshold:.2f}"

    def score(self, expected: str, response: str) -> ScoreResult:
        """Score ``response`` against ``expected`` by fuzzy similarity.

        Args:
            expected: Reference answer.
            response: Raw model response.

        Returns:
            A :class:`ScoreResult` with the similarity score.
        """
        reference = normalize_text(expected, keep_zwnj=self._keep_zwnj)
        candidate = normalize_text(response, keep_zwnj=self._keep_zwnj)
        contained = bool(reference) and reference in candidate
        ratio = difflib.SequenceMatcher(None, reference, candidate).ratio()
        score = 1.0 if contained else ratio
        passed = score >= self._threshold
        return ScoreResult(
            score=round(score, 4),
            passed=passed,
            details={"similarity": round(ratio, 4), "contained": contained},
        )


class JudgeParseError(ValueError):
    """Raised when the judge model does not return parseable JSON."""


_JUDGE_JSON_RE: Final[re.Pattern[str]] = re.compile(r"\{.*\}", re.DOTALL)


def parse_judge_output(text: str) -> tuple[float, str]:
    """Parse the JSON verdict emitted by an LLM judge.

    Accepts a bare JSON object or a JSON object embedded in surrounding
    prose. Scores reported on a 0-10 scale are rescaled to 0-1; any value
    outside ``[0, 1]`` after rescaling is clamped.

    Args:
        text: Raw judge model output.

    Returns:
        Tuple ``(score, rationale)`` with ``score`` in ``[0, 1]``.

    Raises:
        JudgeParseError: If no JSON object with a numeric ``score`` key can
            be extracted.
    """
    candidates = [text]
    match = _JUDGE_JSON_RE.search(text)
    if match:
        candidates.insert(0, match.group(0))
    for candidate in candidates:
        try:
            payload: Any = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or "score" not in payload:
            continue
        raw_score = payload["score"]
        if not isinstance(raw_score, (int, float)) or isinstance(raw_score, bool):
            continue
        score = float(raw_score)
        if score > 1.0 and score <= 10.0:
            score = score / 10.0
        score = min(1.0, max(0.0, score))
        rationale = str(payload.get("rationale", ""))
        return score, rationale
    msg = f"judge output does not contain a parseable JSON verdict: {text!r}"
    raise JudgeParseError(msg)


class LLMJudgeScorer:
    """LLM-as-judge scorer: prompt building plus robust output parsing.

    The actual judge inference is performed by the runner through a
    provider; this class owns the prompt template and parsing so both can
    be unit-tested without any network access.

    Args:
        judge_prompt: Template string rendered with the task's judge
            context plus ``response``.
        pass_threshold: Score at or above which the item passes.
    """

    def __init__(self, judge_prompt: str, pass_threshold: float = 0.70) -> None:
        self._judge_prompt = judge_prompt
        self._pass_threshold = pass_threshold

    @property
    def name(self) -> str:
        """Human-readable scorer name used in result files."""
        return "llm_judge"

    @property
    def judge_prompt(self) -> str:
        """The raw judge prompt template."""
        return self._judge_prompt

    def build_prompt(self, context: dict[str, str], response: str) -> str:
        """Render the judge prompt for one item.

        Args:
            context: Named fields from :meth:`AbstractTask.judge_context`.
            response: Raw response of the model under evaluation.

        Returns:
            The fully rendered judge prompt.

        Raises:
            KeyError: If the template references an unknown field.
        """
        return self._judge_prompt.format(**context, response=response)

    def score(self, judge_output: str) -> ScoreResult:
        """Convert a judge model's raw output into a :class:`ScoreResult`.

        Args:
            judge_output: Raw text returned by the judge model.

        Returns:
            A :class:`ScoreResult`; unparseable output scores 0.0 with the
            parse error recorded in ``details``.
        """
        try:
            value, rationale = parse_judge_output(judge_output)
        except JudgeParseError as exc:
            return ScoreResult(score=0.0, passed=False, details={"error": str(exc)})
        return ScoreResult(
            score=value,
            passed=value >= self._pass_threshold,
            details={"rationale": rationale},
        )


#: System prompt used for every judge call in the harness.
JUDGE_SYSTEM_PROMPT: Final[str] = (
    "تو داور دقیق، بی‌طرف و منصف ارزیابی مدل‌های زبانی هستی. "
    "پاسخ مدل را صرفاً بر اساس معیارهای اعلام‌شده بسنج و تحت تأثیر لحن یا طول پاسخ قرار نگیر. "
    'همیشه فقط یک شیء JSON معتبر با کلیدهای "score" و "rationale" برگردان.'
)
