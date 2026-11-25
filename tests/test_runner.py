"""End-to-end runner, cache, rate-limiter and provider tests (fully offline)."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

from persianeval.harness.providers import (
    AnthropicProvider,
    DummyProvider,
    LLMResponse,
    OllamaProvider,
    OpenAIProvider,
    ProviderError,
    RateLimiter,
    ScriptedProvider,
    ZaiProvider,
    create_provider,
)
from persianeval.harness.results import load_json, save_json, save_parquet
from persianeval.harness.runner import Cache, run_task
from persianeval.tasks import get_task


# ---------------------------------------------------------------- rate limiter
def test_rate_limiter_enforces_window() -> None:
    async def scenario() -> float:
        # 3 slots per 0.3 s window: the 4th request must wait ~0.3 s.
        limiter = RateLimiter(requests_per_minute=3, window_seconds=0.3)
        start = time.perf_counter()
        for _ in range(4):
            await limiter.acquire()
        return time.perf_counter() - start

    elapsed = asyncio.run(scenario())
    assert 0.15 <= elapsed <= 2.0


def test_rate_limiter_unlimited_is_noop() -> None:
    async def scenario() -> float:
        limiter = RateLimiter(None)
        start = time.perf_counter()
        for _ in range(100):
            await limiter.acquire()
        return time.perf_counter() - start

    assert asyncio.run(scenario()) < 0.2


# ------------------------------------------------------------------- providers
def test_scripted_provider_replays_in_order() -> None:
    provider = ScriptedProvider(["الف", "ب"])
    outputs = asyncio.run(gather_texts(provider, prompts=["1", "2", "3", "4"]))
    assert outputs == ["الف", "ب", "الف", "ب"]
    assert provider.calls == 4


async def gather_texts(provider: ScriptedProvider, prompts: list[str]) -> list[str]:
    responses: list[str] = []
    for prompt in prompts:
        response = await provider.complete(prompt)
        responses.append(response.text)
    return responses


def test_dummy_provider_offline_answer() -> None:
    provider = DummyProvider()
    response = asyncio.run(provider.complete("هر چیزی"))
    assert "PersianEval" in response.text


def test_create_provider_unknown_name_raises() -> None:
    with pytest.raises(ProviderError, match="unknown provider"):
        create_provider("spacegpt", "x")


def test_create_provider_openai_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        create_provider("openai", "gpt-4o")


def test_create_provider_vllm_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VLLM_BASE_URL", raising=False)
    with pytest.raises(ProviderError, match="VLLM_BASE_URL"):
        create_provider("vllm", "Qwen/Qwen2.5-7B-Instruct")


def test_openai_provider_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "gpt-4o"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "پاسخ"}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
        )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = OpenAIProvider("gpt-4o")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    response = asyncio.run(provider.complete("سلام", system="سیستم"))
    assert response.text == "پاسخ"
    assert response.input_tokens == 11 and response.output_tokens == 7
    asyncio.run(provider.aclose())


def test_openai_provider_retries_on_500_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = OpenAIProvider("gpt-4o", max_retries=3)
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    response = asyncio.run(provider.complete("x"))
    assert response.text == "ok"
    assert attempts["count"] == 2
    assert provider.stats["retries"] == 1
    asyncio.run(provider.aclose())


def test_openai_provider_gives_up_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = OpenAIProvider("gpt-4o", max_retries=2)
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="failed after 3 attempts"):
        asyncio.run(provider.complete("x"))
    asyncio.run(provider.aclose())


def test_zai_provider_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "glm-4-plus"
        assert request.headers["Authorization"] == "Bearer zai-key"
        assert request.url.path.endswith("/chat/completions")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "پاسخ"}}],
                "usage": {"prompt_tokens": 9, "completion_tokens": 4},
            },
        )

    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    provider = ZaiProvider("glm-4-plus", base_url="https://api.example.test/v4")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    response = asyncio.run(provider.complete("سلام", system="سیستم"))
    assert response.text == "پاسخ"
    assert response.input_tokens == 9 and response.output_tokens == 4
    asyncio.run(provider.aclose())


def test_create_provider_zai_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match=r"Z\.ai API key missing"):
        create_provider("zai", "glm-4-plus")


def test_zai_provider_defaults_to_public_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZAI_API_KEY", "zai-key")
    provider = ZaiProvider("glm-4-plus")
    assert provider.provider_name == "zai"
    assert provider._base_url == "https://api.z.ai/api/paas/v4"
    asyncio.run(provider.aclose())


def test_openai_provider_non_retryable_4xx(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = OpenAIProvider("gpt-4o")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="HTTP 401"):
        asyncio.run(provider.complete("x"))
    assert provider.stats["retries"] == 0
    asyncio.run(provider.aclose())


def test_anthropic_provider_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "درست"}, {"type": "text", "text": " است"}],
                "usage": {"input_tokens": 5, "output_tokens": 9},
            },
        )

    provider = AnthropicProvider("claude-sonnet-4-5", api_key="test-key")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    response = asyncio.run(provider.complete("q"))
    assert response.text == "درست است"
    asyncio.run(provider.aclose())


def test_anthropic_provider_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider("claude-sonnet-4-5")


def test_ollama_provider_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.0
        return httpx.Response(
            200,
            json={"message": {"content": "جواب محلی"}, "prompt_eval_count": 3, "eval_count": 4},
        )

    provider = OllamaProvider("qwen2.5:7b-instruct", base_url="http://mock")
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    response = asyncio.run(provider.complete("q"))
    assert response.text == "جواب محلی"
    assert response.input_tokens == 3
    asyncio.run(provider.aclose())


# ----------------------------------------------------------------------- cache
def test_cache_roundtrip_and_corruption(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    response = LLMResponse(text="پاسخ", input_tokens=1, output_tokens=2, latency_ms=3.0)
    kwargs: dict[str, Any] = {
        "provider_name": "openai",
        "model": "gpt-4o",
        "task_name": "reasoning",
        "seed": 42,
        "sample_id": "reasoning-0001",
        "prompt": "p",
    }
    assert cache.get(**kwargs) is None
    cache.put(**kwargs, response=response)
    hit = cache.get(**kwargs)
    assert hit is not None and hit.text == "پاسخ" and hit.output_tokens == 2

    # A corrupt entry is treated as a miss, not an exception.
    next(iter(tmp_path.rglob("*.json"))).write_text("{broken", encoding="utf-8")
    assert cache.get(**kwargs) is None


def test_cache_key_separates_seeds_and_prompts(tmp_path: Path) -> None:
    cache = Cache(tmp_path)
    base = {
        "provider_name": "p",
        "model": "m",
        "task_name": "t",
        "sample_id": "s",
        "prompt": "same-prompt",
    }
    cache.put(seed=1, **base, response=LLMResponse(text="one"))
    cache.put(seed=2, **base, response=LLMResponse(text="two"))
    assert cache.get(seed=1, **base).text == "one"  # type: ignore[union-attr]
    assert cache.get(seed=2, **base).text == "two"  # type: ignore[union-attr]


# ---------------------------------------------------------------------- runner
def test_run_task_scripted_perfect_and_cached_rerun(tmp_path: Path) -> None:
    task = get_task("cultural_knowledge")
    samples = sorted(task.load_samples(), key=lambda s: s.id)[:4]
    provider = ScriptedProvider([sample.expected for sample in samples])
    cache_root = tmp_path / "cache"

    # max_requests (not limit) keeps the deterministic first-4 subset.
    first = asyncio.run(
        run_task(task, provider, max_requests=4, seed=42, cache_root=cache_root, concurrency=2)
    )
    assert first.metrics["accuracy"] == 1.0
    assert first.n_items == 4
    assert provider.calls == 4

    second = asyncio.run(
        run_task(task, provider, max_requests=4, seed=42, cache_root=cache_root, concurrency=2)
    )
    assert second.metrics["accuracy"] == 1.0
    assert provider.calls == 4  # no new API calls
    assert second.n_cached == 4


def test_run_task_zero_accuracy_on_wrong_answers(tmp_path: Path) -> None:
    task = get_task("reasoning")
    result = asyncio.run(
        run_task(
            task,
            ScriptedProvider(["۱۲۳۴۵"]),
            limit=3,
            seed=7,
            cache_root=tmp_path / "cache",
        )
    )
    assert result.metrics["accuracy"] == 0.0
    assert all(item.score == 0.0 for item in result.items)


def test_run_task_judge_scoring_with_scripted_judge(tmp_path: Path) -> None:
    task = get_task("translation_fa_en")
    provider = ScriptedProvider(["whatever the model said"] * 3)
    judge = ScriptedProvider(
        [
            '{"score": 0.9, "rationale": "dobra"}',
            '{"score": 0.5, "rationale": "meh"}',
            '{"score": 10, "rationale": "perfect"}',  # 10-point scale rescaled to 1.0
        ]
    )
    result = asyncio.run(
        run_task(task, provider, judge_provider=judge, limit=3, seed=3, cache_root=tmp_path / "c")
    )
    assert result.metrics["accuracy"] == pytest.approx(2 / 3, abs=1e-3)
    assert result.items[0].scorer == "llm_judge"
    assert result.items[0].details["rationale"] == "dobra"


def test_run_task_max_requests_caps_items(tmp_path: Path) -> None:
    task = get_task("spelling")
    provider = DummyProvider()
    result = asyncio.run(run_task(task, provider, max_requests=2, seed=1, cache_root=tmp_path / "c"))
    assert result.n_items == 2


def test_run_result_json_roundtrip(tmp_path: Path) -> None:
    task = get_task("reading_comprehension")
    result = asyncio.run(run_task(task, DummyProvider(), limit=2, seed=5, cache_root=tmp_path / "c"))
    path = save_json(result, tmp_path / "run.json")
    loaded = load_json(path)
    assert loaded == result


def test_run_result_parquet_output(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    task = get_task("cultural_knowledge")
    result = asyncio.run(run_task(task, DummyProvider(), limit=3, seed=9, cache_root=tmp_path / "c"))
    path = save_parquet(result, tmp_path / "run.parquet")
    assert path.exists() and path.stat().st_size > 0
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    assert table.num_rows == 3


# ------------------------------------------------------------------- CLI smoke
def test_cli_tasks_and_offline_run(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from persianeval.cli import app

    runner = CliRunner()
    listed = runner.invoke(app, ["tasks"])
    assert listed.exit_code == 0
    assert "reasoning" in listed.output

    run = runner.invoke(
        app,
        [
            "run",
            "--task",
            "reasoning",
            "--provider",
            "dummy",
            "--model",
            "demo",
            "--limit",
            "3",
            "--out",
            str(tmp_path / "results"),
            "--no-cache",
            "--org",
            "TestOrg",
            "--license",
            "Apache-2.0",
        ],
    )
    assert run.exit_code == 0, run.output
    files = list((tmp_path / "results").iterdir())
    assert {path.suffix for path in files} == {".json", ".parquet"}


def test_cli_leaderboard_command(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from persianeval.cli import app

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    task = get_task("reasoning")
    result = asyncio.run(run_task(task, DummyProvider(), limit=2, seed=1, org="Org", license_id="Apache-2.0"))
    save_json(result, results_dir / "demo.json")

    runner = CliRunner()
    outcome = runner.invoke(
        app,
        ["leaderboard", "--results-dir", str(results_dir), "--out", str(tmp_path / "site")],
    )
    assert outcome.exit_code == 0, outcome.output
    assert (tmp_path / "site" / "index.html").exists()
    assert (tmp_path / "site" / "data.json").exists()


def test_cli_run_unknown_task_fails_cleanly() -> None:
    from typer.testing import CliRunner

    from persianeval.cli import app

    outcome = CliRunner().invoke(app, ["run", "--task", "nope", "--provider", "dummy", "--model", "m"])
    assert outcome.exit_code == 2
