"""Typer-based command line interface for PersianEval.

Examples:
    persianeval tasks
    persianeval run --task reasoning --provider openai --model gpt-4o --rpm 60
    persianeval run --task spelling --provider ollama --model qwen2.5:7b-instruct
    persianeval leaderboard --results-dir results --out leaderboard
"""

from __future__ import annotations

import asyncio
import logging
from importlib import metadata
from pathlib import Path
from typing import Annotated, Final

import typer

from persianeval.harness.providers import ProviderError, create_provider
from persianeval.harness.results import save_json, save_parquet
from persianeval.harness.runner import run_task
from persianeval.leaderboard.generate import generate_site
from persianeval.tasks import get_task

app: Final[typer.Typer] = typer.Typer(
    name="persianeval",
    help="Open-source benchmark for Persian (Farsi) LLMs.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

_LOGGING_FORMAT: Final[str] = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"persianeval {metadata.version('persianeval')}")
        raise typer.Exit


@app.command()
def tasks() -> None:
    """List all registered evaluation tasks."""
    from persianeval.tasks import all_task_classes

    typer.echo(f"{'TASK':<28} {'MIN SAMPLES':>11}  TITLE")
    for task_class in all_task_classes().values():
        instance = task_class()
        typer.echo(
            f"{instance.name:<28} {instance.min_samples:>11}  {instance.title_en} — {instance.title_fa}"
        )


@app.command()
def run(
    task: Annotated[str, typer.Option(help="Task name (see `persianeval tasks`).")],
    model: Annotated[str, typer.Option(help="Model identifier, e.g. gpt-4o or qwen2.5:7b-instruct.")],
    provider: Annotated[str, typer.Option(help="openai | anthropic | ollama | vllm | dummy")] = "openai",
    base_url: Annotated[str | None, typer.Option(help="Endpoint override (vLLM/self-hosted).")] = None,
    org: Annotated[str, typer.Option(help="Organization metadata for the leaderboard.")] = "",
    license_id: Annotated[str, typer.Option("--license", help="Model license metadata.")] = "",
    limit: Annotated[int | None, typer.Option(help="Seeded random subset size.")] = None,
    max_requests: Annotated[
        int | None, typer.Option("--max-requests", help="Hard cap on evaluated items (API budget).")
    ] = None,
    max_requests_per_minute: Annotated[
        int | None,
        typer.Option("--max-requests-per-minute", help="Per-provider rate limit (RPM)."),
    ] = None,
    max_tokens: Annotated[int, typer.Option(help="Completion budget per item.")] = 1024,
    concurrency: Annotated[int, typer.Option(help="Maximum in-flight API requests.")] = 4,
    request_timeout: Annotated[
        float,
        typer.Option(
            "--request-timeout",
            help="Per-request HTTP timeout in seconds. CPU-served local models (Ollama on a "
            "runner without a GPU) routinely need more than the 120s default.",
        ),
    ] = 120.0,
    seed: Annotated[int, typer.Option(help="RNG seed for subset selection.")] = 42,
    temperature: Annotated[float, typer.Option(help="Sampling temperature (default 0.0).")] = 0.0,
    out_dir: Annotated[Path, typer.Option("--out", help="Directory for result files.")] = Path("results"),
    cache_dir: Annotated[Path, typer.Option(help="Response cache directory.")] = Path(".persianeval_cache"),
    no_cache: Annotated[bool, typer.Option(help="Disable the response cache.")] = False,
) -> None:
    """Evaluate a task against a model and write JSON + Parquet results."""
    logging.basicConfig(level=logging.INFO, format=_LOGGING_FORMAT)
    try:
        task_obj = get_task(task)
        provider_obj = create_provider(
            provider, model, base_url=base_url, rpm=max_requests_per_minute, timeout_s=request_timeout
        )
    except (KeyError, ProviderError, ValueError) as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(
        f"task={task_obj.name} provider={provider_obj.provider_name} model={model} "
        f"seed={seed} temperature={temperature} concurrency={concurrency}"
    )

    async def _run_and_close():
        """Run the task and close the provider inside the same event loop.

        httpx/anyio async primitives are bound to the event loop that created
        them; closing the client from a second ``asyncio.run`` loop raised
        ``RuntimeError: Event loop is closed`` after a successful run, which
        made the CLI exit non-zero *before* ``save_json`` and silently
        discarded the finished run's results (leaderboard postmortem
        2026-11-17: every judge-scored task lost its results on all 3 retry
        attempts because judge calls are never cache hits).
        """
        try:
            return await run_task(
                task_obj,
                provider_obj,
                limit=limit,
                max_requests=max_requests,
                seed=seed,
                temperature=temperature,
                max_tokens=max_tokens,
                concurrency=concurrency,
                cache_root=None if no_cache else cache_dir,
                org=org,
                license_id=license_id,
            )
        finally:
            await provider_obj.aclose()

    result = asyncio.run(_run_and_close())

    slug = f"{result.task}__{model}".replace("/", "-")
    json_path = save_json(result, out_dir / f"{slug}.json")
    parquet_path = save_parquet(result, out_dir / f"{slug}.parquet")

    accuracy = result.metrics.get("accuracy", 0.0)
    mean_score = result.metrics.get("mean_score", 0.0)
    typer.echo("-" * 56)
    typer.echo(f"accuracy : {accuracy:.2%}   mean score: {mean_score:.3f}")
    typer.echo(f"items    : {result.n_items} ({result.n_cached} served from cache)")
    typer.echo(f"results  : {json_path}")
    typer.echo(f"results  : {parquet_path}")


@app.command()
def leaderboard(
    results_dir: Annotated[
        Path, typer.Option(exists=True, file_okay=False, help="Directory containing *.json run results.")
    ],
    out: Annotated[Path, typer.Option(help="Output directory for the static site.")] = Path("leaderboard"),
    title: Annotated[str, typer.Option(help="Site title.")] = "PersianEval Leaderboard",
) -> None:
    """Build the static leaderboard site from run results."""
    index_path = generate_site(results_dir, out, title=title)
    typer.echo(f"leaderboard written to {index_path}")


@app.callback()
def _root_callback(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit."),
    ] = None,
) -> None:
    """PersianEval command line interface."""


def main() -> None:
    """Console-script entry point (see ``[project.scripts]`` in pyproject.toml)."""
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
