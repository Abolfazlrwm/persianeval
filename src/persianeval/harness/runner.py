"""Async evaluation runner: concurrency, caching, scoring, aggregation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Any

from persianeval.harness.providers import BaseProvider, LLMResponse
from persianeval.harness.results import ItemResult, RunResult, utc_now_iso
from persianeval.harness.scorers import (
    ExactScorer,
    FuzzyScorer,
    LLMJudgeScorer,
    ScoreResult,
)
from persianeval.tasks.base import AbstractTask, Sample, ScoringKind

_LOGGER = logging.getLogger(__name__)


class Cache:
    """Filesystem response cache keyed by provider+model+task+seed+prompt.

    Cached runs are bit-for-bit reproducible: a cache hit returns the exact
    stored response, so re-running with the same seed never re-bills the
    API for already-seen prompts.

    Args:
        root: Directory for cache entries; created on demand.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, parts: list[str]) -> Path:
        digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.json"

    def get(
        self,
        *,
        provider_name: str,
        model: str,
        task_name: str,
        seed: int,
        sample_id: str,
        prompt: str,
    ) -> LLMResponse | None:
        """Return the cached response for this key, or ``None``.

        Corrupt or unreadable entries are logged and treated as misses.
        """
        path = self._path([provider_name, model, task_name, str(seed), sample_id, prompt])
        if not path.exists():
            return None
        try:
            payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return LLMResponse(
                text=str(payload["text"]),
                input_tokens=payload.get("input_tokens"),
                output_tokens=payload.get("output_tokens"),
                latency_ms=float(payload.get("latency_ms", 0.0)),
            )
        except (OSError, ValueError, KeyError, TypeError):
            _LOGGER.warning("ignoring corrupt cache entry %s", path)
            return None

    def put(
        self,
        *,
        provider_name: str,
        model: str,
        task_name: str,
        seed: int,
        sample_id: str,
        prompt: str,
        response: LLMResponse,
    ) -> None:
        """Store a response atomically (write to temp file, then rename)."""
        path = self._path([provider_name, model, task_name, str(seed), sample_id, prompt])
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "text": response.text,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


async def _score_item(
    task: AbstractTask,
    sample: Sample,
    response_text: str,
    judge_provider: BaseProvider | None,
) -> tuple[float, bool, dict[str, Any], str]:
    """Score one response according to the task's scoring spec.

    Returns:
        Tuple ``(score, passed, details, scorer_name)``.
    """
    spec = task.scoring
    if spec.kind is ScoringKind.EXACT:
        result: ScoreResult = ExactScorer(task.exact_strip_tokens, keep_zwnj=spec.normalize_keep_zwnj).score(
            sample.expected, response_text
        )
        return result.score, result.passed, result.details, "exact"
    if spec.kind is ScoringKind.FUZZY:
        fuzzy = FuzzyScorer(spec.fuzzy_threshold, keep_zwnj=spec.normalize_keep_zwnj)
        fuzzy_result = fuzzy.score(sample.expected, response_text)
        return fuzzy_result.score, fuzzy_result.passed, fuzzy_result.details, fuzzy.name

    # ScoringKind.JUDGE
    if spec.judge_prompt is None:  # guarded by ScoringSpec validation
        msg = f"task '{task.name}' has a judge spec without a prompt"
        raise RuntimeError(msg)
    if judge_provider is None:
        msg = (
            f"task '{task.name}' is scored by an LLM judge and therefore requires "
            "a provider; pass --provider or --judge-model"
        )
        raise RuntimeError(msg)
    judge = LLMJudgeScorer(spec.judge_prompt, spec.score_pass_threshold)
    prompt = judge.build_prompt(task.judge_context(sample), response_text)
    judge_response = await judge_provider.complete(
        prompt,
        system="تو داور دقیق و بی‌طرف هستی و همیشه فقط JSON معتبر برمی‌گردانی.",
        max_tokens=512,
        temperature=0.0,
    )
    result = judge.score(judge_response.text)
    return result.score, result.passed, result.details, judge.name


async def run_task(
    task: AbstractTask,
    provider: BaseProvider,
    *,
    judge_provider: BaseProvider | None = None,
    limit: int | None = None,
    max_requests: int | None = None,
    seed: int = 42,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    concurrency: int = 4,
    cache_root: Path | None = None,
    org: str = "",
    license_id: str = "",
) -> RunResult:
    """Evaluate a task against a provider and return the full run result.

    The run is reproducible: a fixed ``seed`` selects the sample subset,
    temperature defaults to 0 and responses are cached per
    provider+model+task+seed+prompt.

    Args:
        task: The task to evaluate.
        provider: The model under evaluation.
        judge_provider: Provider used for LLM-as-judge scoring; defaults to
            the evaluation provider itself.
        limit: Random (seeded) subset size; ``None`` evaluates everything.
        max_requests: Hard cap on evaluated items (API budget control).
        seed: RNG seed for subset selection.
        temperature: Sampling temperature for the evaluated model.
        max_tokens: Completion budget per item.
        concurrency: Maximum in-flight API requests.
        cache_root: Enables the response cache when given.
        org: Organization metadata recorded in the result.
        license_id: License metadata recorded in the result.

    Returns:
        The aggregated :class:`RunResult`.

    Raises:
        RuntimeError: On judge tasks without a judge provider.
    """
    samples = sorted(task.load_samples(), key=lambda s: s.id)
    rng = random.Random(seed)
    if limit is not None and limit < len(samples):
        samples = sorted(rng.sample(samples, limit), key=lambda s: s.id)
    if max_requests is not None and max_requests < len(samples):
        samples = samples[:max_requests]

    cache = Cache(cache_root) if cache_root is not None else None
    effective_judge = judge_provider if judge_provider is not None else provider
    semaphore = asyncio.Semaphore(concurrency)
    started_at = utc_now_iso()

    async def evaluate(sample: Sample) -> ItemResult:
        async with semaphore:
            prompt = task.build_prompt(sample)
            was_cached = False
            cached = (
                cache.get(
                    provider_name=provider.provider_name,
                    model=provider.model,
                    task_name=task.name,
                    seed=seed,
                    sample_id=sample.id,
                    prompt=prompt,
                )
                if cache is not None
                else None
            )
            if cached is not None:
                response = cached
                was_cached = True
            else:
                response = await provider.complete(
                    prompt,
                    system=task.system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if cache is not None:
                    cache.put(
                        provider_name=provider.provider_name,
                        model=provider.model,
                        task_name=task.name,
                        seed=seed,
                        sample_id=sample.id,
                        prompt=prompt,
                        response=response,
                    )
            item_start = time.perf_counter()
            score, passed, details, scorer_name = await _score_item(
                task, sample, response.text, effective_judge
            )
            return ItemResult(
                id=sample.id,
                score=score,
                passed=passed,
                response=response.text,
                expected=sample.expected,
                scorer=scorer_name,
                details=details,
                latency_ms=round((time.perf_counter() - item_start) * 1000.0, 2),
                cached=was_cached,
            )

    _LOGGER.info(
        "running task '%s' on %s:%s (%d items)",
        task.name,
        provider.provider_name,
        provider.model,
        len(samples),
    )
    items = list(await asyncio.gather(*(evaluate(sample) for sample in samples)))
    n_cached = sum(1 for item in items if item.cached)
    n_passed = sum(1 for item in items if item.passed)
    mean_score = sum(item.score for item in items) / len(items) if items else 0.0
    avg_latency = sum(item.latency_ms for item in items) / len(items) if items else 0.0

    return RunResult(
        run_id=uuid.uuid4().hex[:12],
        task=task.name,
        model=provider.model,
        provider=provider.provider_name,
        org=org,
        license=license_id,
        seed=seed,
        temperature=temperature,
        max_tokens=max_tokens,
        concurrency=concurrency,
        started_at=started_at,
        finished_at=utc_now_iso(),
        n_items=len(items),
        n_cached=n_cached,
        metrics={
            "accuracy": round(n_passed / len(items), 4) if items else 0.0,
            "mean_score": round(mean_score, 4),
            "avg_latency_ms": round(avg_latency, 2),
        },
        items=items,
    )
