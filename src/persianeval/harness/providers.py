"""Async LLM providers: OpenAI, Anthropic, Ollama, vLLM + offline helpers.

All providers share a token-bucket-free sliding-window rate limiter, retry
with exponential backoff on 429/5xx and transport errors, and are built on
``httpx.AsyncClient``.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Any, ClassVar, Final

import httpx

_DEFAULT_TIMEOUT_S: Final[float] = 120.0
_DEFAULT_MAX_RETRIES: Final[int] = 5
_RETRYABLE_STATUS: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})


class ProviderError(RuntimeError):
    """Raised for configuration, authentication or unrecoverable API errors."""


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """A single completion returned by any provider.

    Attributes:
        text: The assistant text content.
        input_tokens: Prompt token count when the provider reports it.
        output_tokens: Completion token count when the provider reports it.
        latency_ms: Wall-clock latency of the API call in milliseconds.
        raw: Provider-specific payload kept for debugging (never uploaded).
    """

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0.0
    raw: dict[str, Any] | None = None


class RateLimiter:
    """Sliding-window rate limiter shared per provider instance.

    Args:
        requests_per_minute: Maximum requests allowed in the window;
            ``None`` disables limiting.
        window_seconds: Width of the sliding window in seconds. The
            production default is 60; tests shrink it to keep runtime low.
    """

    def __init__(self, requests_per_minute: int | None, *, window_seconds: float = 60.0) -> None:
        self._rpm = requests_per_minute
        self._window = window_seconds
        self._slots: deque[float] = deque()
        self._lock = asyncio.Lock()

    @property
    def requests_per_minute(self) -> int | None:
        """Configured limit, or ``None`` when unlimited."""
        return self._rpm

    async def acquire(self) -> None:
        """Await until one request slot is available."""
        if self._rpm is None:
            return
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._slots and now - self._slots[0] >= self._window:
                    self._slots.popleft()
                if len(self._slots) < self._rpm:
                    self._slots.append(now)
                    return
                delay = self._window - (now - self._slots[0]) + 0.005
                await asyncio.sleep(delay)


class BaseProvider(ABC):
    """Common async plumbing for all providers.

    Subclasses implement :meth:`_complete_once`; :meth:`complete` adds the
    rate limiter and retry/backoff loop on top.

    Args:
        model: Model identifier sent to the API.
        rpm: Optional per-provider requests-per-minute limit.
        timeout_s: HTTP timeout in seconds.
        max_retries: Number of retries after the first failed attempt.
    """

    #: Short name used in result files and the cache key.
    provider_name: ClassVar[str] = "base"

    def __init__(
        self,
        model: str,
        *,
        rpm: int | None = None,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self.model = model
        self.stats: dict[str, int] = {"requests": 0, "retries": 0}
        self._limiter = RateLimiter(rpm)
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout_s))
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Complete a prompt with rate limiting and retries.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            max_tokens: Optional completion budget forwarded to the API.
            temperature: Sampling temperature; PersianEval pins 0.0 for
                reproducibility.

        Returns:
            The parsed :class:`LLMResponse`.

        Raises:
            ProviderError: After exhausting all retries, or on a
                non-retryable HTTP error.
        """
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            await self._limiter.acquire()
            try:
                return await self._complete_once(
                    prompt, system=system, max_tokens=max_tokens, temperature=temperature
                )
            except (httpx.TransportError, _RetryableStatusError) as exc:
                last_error = exc
                self.stats["retries"] += 1
                if attempt >= self._max_retries:
                    break
                delay = 0.5 * (2**attempt) + random.uniform(0.0, 0.25)
                await asyncio.sleep(delay)
        msg = f"{self.provider_name}:{self.model} failed after {self._max_retries + 1} attempts: {last_error}"
        raise ProviderError(msg) from last_error

    @abstractmethod
    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        max_tokens: int | None,
        temperature: float,
    ) -> LLMResponse:
        """Perform exactly one API call (no retries)."""


class _RetryableStatusError(RuntimeError):
    """Internal signal for HTTP statuses worth retrying."""


class OpenAIProvider(BaseProvider):
    """OpenAI Chat Completions provider (also speaks vLLM / OpenAI-compatible).

    Args:
        model: e.g. ``"gpt-4o"``.
        base_url: API root; defaults to ``https://api.openai.com/v1``.
        api_key: Bearer token; defaults to ``OPENAI_API_KEY``.
    """

    provider_name: ClassVar[str] = "openai"

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            msg = "OpenAI API key missing: set OPENAI_API_KEY or pass api_key explicitly"
            raise ProviderError(msg)
        self._api_key = resolved_key

    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        max_tokens: int | None,
        temperature: float,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        response = await self._post_json("/chat/completions", payload)
        choices = response.get("choices") or []
        if not choices:
            msg = f"OpenAI returned no choices: {response}"
            raise ProviderError(msg)
        usage = response.get("usage") or {}
        return LLMResponse(
            text=str(choices[0].get("message", {}).get("content", "")),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_ms=response.get("_latency_ms", 0.0),  # replaced below
            raw=response,
        )

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON to the OpenAI-compatible API and parse the response."""
        client = self._ensure_client()
        start = time.perf_counter()
        response = await client.post(
            f"{self._base_url.rstrip('/')}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        if response.status_code >= 400:
            if response.status_code in _RETRYABLE_STATUS:
                raise _RetryableStatusError(f"HTTP {response.status_code}: {response.text[:200]}")
            msg = f"HTTP {response.status_code}: {response.text[:200]}"
            raise ProviderError(msg)
        data: dict[str, Any] = response.json()
        data["_latency_ms"] = latency_ms
        return data


class AnthropicProvider(BaseProvider):
    """Anthropic Messages API provider.

    Args:
        model: e.g. ``"claude-sonnet-4-5"``.
        base_url: API root; defaults to ``https://api.anthropic.com``.
        api_key: API key; defaults to ``ANTHROPIC_API_KEY``.
    """

    provider_name: ClassVar[str] = "anthropic"

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self._base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            msg = "Anthropic API key missing: set ANTHROPIC_API_KEY or pass api_key explicitly"
            raise ProviderError(msg)
        self._api_key = resolved_key

    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        max_tokens: int | None,
        temperature: float,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens if max_tokens is not None else 1024,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        client = self._ensure_client()
        start = time.perf_counter()
        response = await client.post(
            f"{self._base_url.rstrip('/')}/v1/messages",
            json=payload,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        if response.status_code >= 400:
            if response.status_code in _RETRYABLE_STATUS:
                raise _RetryableStatusError(f"HTTP {response.status_code}: {response.text[:200]}")
            msg = f"HTTP {response.status_code}: {response.text[:200]}"
            raise ProviderError(msg)
        data: dict[str, Any] = response.json()
        blocks = data.get("content") or []
        text = "".join(str(block.get("text", "")) for block in blocks if block.get("type") == "text")
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=latency_ms,
            raw=data,
        )


class OllamaProvider(BaseProvider):
    """Ollama provider for local open-source models.

    Args:
        model: e.g. ``"qwen2.5:7b-instruct"``.
        base_url: Ollama root; defaults to ``OLLAMA_BASE_URL`` or
            ``http://localhost:11434``.
    """

    provider_name: ClassVar[str] = "ollama"

    def __init__(self, model: str, *, base_url: str | None = None, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self._base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        max_tokens: int | None,
        temperature: float,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        client = self._ensure_client()
        start = time.perf_counter()
        response = await client.post(
            f"{self._base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False, "options": options},
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        if response.status_code >= 400:
            if response.status_code in _RETRYABLE_STATUS:
                raise _RetryableStatusError(f"HTTP {response.status_code}: {response.text[:200]}")
            msg = f"HTTP {response.status_code}: {response.text[:200]}"
            raise ProviderError(msg)
        data: dict[str, Any] = response.json()
        message = data.get("message") or {}
        return LLMResponse(
            text=str(message.get("content", "")),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=latency_ms,
            raw=data,
        )


class ScriptedProvider(BaseProvider):
    """Deterministic offline provider returning pre-scripted responses.

    Used by the test suite and for pipeline validation runs; it never talks
    to a network. Responses are returned in order and the list cycles when
    exhausted.

    Args:
        responses: The canned responses to replay.
    """

    provider_name: ClassVar[str] = "scripted"

    def __init__(self, responses: list[str], model: str = "scripted", **kwargs: Any) -> None:
        super().__init__(model=model, **kwargs)
        if not responses:
            msg = "ScriptedProvider requires at least one response"
            raise ProviderError(msg)
        self._responses = responses
        self._cursor = 0

    @property
    def calls(self) -> int:
        """Number of completed API calls (used by tests and cache checks)."""
        return self._cursor

    async def _complete_once(
        self,
        prompt: str,
        *,
        system: str | None,
        max_tokens: int | None,
        temperature: float,
    ) -> LLMResponse:
        text = self._responses[self._cursor % len(self._responses)]
        self._cursor += 1
        return LLMResponse(text=text, latency_ms=0.0)


class DummyProvider(ScriptedProvider):
    """Offline provider for validating the CLI pipeline end to end.

    Returns a single fixed Persian string; never intended for real scoring.
    """

    provider_name: ClassVar[str] = "dummy"

    def __init__(self, model: str = "demo", **kwargs: Any) -> None:
        super().__init__(
            responses=["پاسخ آفلاین نمونه برای اعتبارسنجی خط لوله PersianEval."],
            model=model,
            **kwargs,
        )


def create_provider(
    provider: str,
    model: str,
    *,
    base_url: str | None = None,
    rpm: int | None = None,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> BaseProvider:
    """Factory mapping CLI provider names to provider instances.

    Args:
        provider: One of ``openai``, ``anthropic``, ``ollama``, ``vllm``,
            ``dummy``.
        model: Model identifier.
        base_url: Optional endpoint override (``vllm`` requires it or the
            ``VLLM_BASE_URL`` environment variable).
        rpm: Requests-per-minute cap for this provider instance.
        timeout_s: HTTP timeout in seconds.
        max_retries: Retry budget per request.

    Returns:
        A configured, ready-to-use provider.

    Raises:
        ProviderError: On unknown provider names or missing configuration.
    """
    common: dict[str, Any] = {"rpm": rpm, "timeout_s": timeout_s, "max_retries": max_retries}
    if provider == "openai":
        return OpenAIProvider(model, **common)
    if provider == "anthropic":
        return AnthropicProvider(model, **common)
    if provider == "ollama":
        return OllamaProvider(model, base_url=base_url, **common)
    if provider == "vllm":
        resolved_url = base_url or os.environ.get("VLLM_BASE_URL")
        if not resolved_url:
            msg = "vLLM requires --base-url or the VLLM_BASE_URL environment variable"
            raise ProviderError(msg)
        return OpenAIProvider(
            model,
            base_url=resolved_url.rstrip("/"),
            api_key=os.environ.get("VLLM_API_KEY", "EMPTY"),
            **common,
        )
    if provider == "dummy":
        return DummyProvider(model=model, **common)
    msg = f"unknown provider '{provider}'; expected one of: openai, anthropic, ollama, vllm, dummy"
    raise ProviderError(msg)
