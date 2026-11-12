"""Static leaderboard site generator (Jinja2 + pure-SVG radar chart).

Reads ``RunResult`` JSON files, keeps the latest run per (model, task),
computes the overall score as the mean of per-task accuracies and renders
a self-contained static page (sortable table, radar chart, data.json) for
GitHub Pages — no external JavaScript dependencies.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic import ValidationError

from persianeval.harness.results import RunResult
from persianeval.tasks import builtin_task_classes

#: Short axis labels for the radar chart: (English, Persian).
TASK_LABELS: Final[list[tuple[str, str]]] = [
    ("Reasoning", "استدلال"),
    ("Reading", "درک مطلب"),
    ("Spelling", "املا"),
    ("Culture", "فرهنگ"),
    ("Translation", "ترجمه"),
    ("RAG", "وفاداری RAG"),
    ("Bias", "تعصب"),
    ("Code", "کد"),
]

#: Tailwind-free, dependency-free stylesheet embedded into the template.
PALETTE: Final[list[str]] = ["#0ea5a4", "#6366f1", "#f59e0b", "#ef4444", "#10b981", "#a855f7"]


def collect_results(results_dir: Path) -> list[RunResult]:
    """Load every valid ``*.json`` run result in a directory.

    Invalid or unrelated JSON files are logged and skipped.

    Args:
        results_dir: Directory to scan (non-recursive).

    Returns:
        All parseable run results, in directory order.
    """
    results: list[RunResult] = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            results.append(RunResult.model_validate_json(path.read_text(encoding="utf-8")))
        except (OSError, ValidationError):
            continue
    return results


def build_rows(results: list[RunResult]) -> list[dict[str, Any]]:
    """Aggregate run results into one leaderboard row per model.

    For every (model, task) pair the latest run by ``finished_at`` wins;
    the overall score is the mean of that model's per-task accuracies.

    Args:
        results: Parsed run results.

    Returns:
        Rows sorted by overall score (descending), each with ``rank``,
        ``model``, ``org``, ``license``, ``overall`` and per-task scores.
    """
    latest: dict[tuple[str, str], RunResult] = {}
    for result in results:
        key = (result.model, result.task)
        current = latest.get(key)
        if current is None or result.finished_at >= current.finished_at:
            latest[key] = result

    per_model: dict[str, dict[str, float]] = defaultdict(dict)
    meta: dict[str, tuple[str, str]] = {}
    for (model, task), result in latest.items():
        per_model[model][task] = float(result.metrics.get("accuracy", 0.0))
        meta[model] = (result.org, result.license)

    rows: list[dict[str, Any]] = []
    for model, task_scores in per_model.items():
        overall = sum(task_scores.values()) / len(task_scores) if task_scores else 0.0
        org, license_id = meta.get(model, ("", ""))
        rows.append(
            {
                "model": model,
                "org": org,
                "license": license_id,
                "overall": round(overall * 100.0, 1),
                "tasks": {task: round(score * 100.0, 1) for task, score in task_scores.items()},
                "colors": PALETTE[len(rows) % len(PALETTE)],
            }
        )
    rows.sort(key=lambda row: row["overall"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def radar_svg(rows: list[dict[str, Any]], *, size: int = 420) -> str:
    """Render a pure-SVG radar chart comparing up to six models.

    Args:
        rows: Leaderboard rows (only the first six are drawn).
        size: Square canvas size in pixels.

    Returns:
        SVG markup as a string (empty string when there is no data).
    """
    if not rows:
        return ""
    rows = rows[:6]
    task_names = [task_class().name for task_class in builtin_task_classes()]
    center = size / 2
    radius = size / 2 - 70
    axes = len(task_names)

    def point_at(fraction: float, value: float) -> str:
        angle = 2.0 * math.pi * fraction - math.pi / 2.0
        return (
            f"{center + radius * value * math.cos(angle):.1f},{center + radius * value * math.sin(angle):.1f}"
        )

    parts: list[str] = [
        f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="Radar chart" '
        f'xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{size}" height="{size}" fill="transparent"/>',
    ]
    for ring in (0.25, 0.5, 0.75, 1.0):
        ring_points = " ".join(point_at(i / axes, ring) for i in range(axes))
        parts.append(
            f'<polygon points="{ring_points}" fill="none" stroke="currentColor" '
            f'stroke-opacity="0.15" stroke-width="1"/>'
        )
    for index, _task_name in enumerate(task_names):
        x, y = (float(v) for v in point_at(index / axes, 1.0).split(","))
        parts.append(
            f'<line x1="{center}" y1="{center}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="currentColor" stroke-opacity="0.15" stroke-width="1"/>'
        )
        label_x = center + (radius + 22.0) * math.cos(2.0 * math.pi * index / axes - math.pi / 2.0)
        label_y = center + (radius + 22.0) * math.sin(2.0 * math.pi * index / axes - math.pi / 2.0)
        anchor = "middle" if abs(label_x - center) < 1.0 else ("start" if label_x > center else "end")
        parts.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-size="12" fill="currentColor" fill-opacity="0.7">'
            f"{TASK_LABELS[index][1]}</text>"
        )
    for row in rows:
        values = [row["tasks"].get(task_name, 0.0) / 100.0 for task_name in task_names]
        polygon_points = " ".join(point_at(i / axes, max(values[i], 0.02)) for i in range(axes))
        parts.append(
            f'<polygon points="{polygon_points}" fill="{row["colors"]}" fill-opacity="0.12" '
            f'stroke="{row["colors"]}" stroke-width="2"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def generate_site(results_dir: Path, out_dir: Path, *, title: str = "PersianEval Leaderboard") -> Path:
    """Render the full static leaderboard site.

    Writes ``index.html`` (self-contained page) and ``data.json`` (raw
    aggregated rows used as the downloadable artifact).

    Args:
        results_dir: Directory containing ``RunResult`` JSON files.
        out_dir: Destination directory for the site.
        title: Page title.

    Returns:
        Path of the generated ``index.html``.
    """
    rows = build_rows(collect_results(results_dir))
    environment = Environment(
        loader=PackageLoader("persianeval", "leaderboard/templates"),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = environment.get_template("index.html.j2")
    html = template.render(
        title=title,
        rows=rows,
        task_labels=TASK_LABELS,
        task_sources=[
            {"name": cls().name, "min_samples": cls().min_samples, "fa": cls().title_fa, "en": cls().title_en}
            for cls in builtin_task_classes()
        ],
        radar=radar_svg(rows),
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        has_results=bool(rows),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    (out_dir / "data.json").write_text(
        json.dumps(
            {"generated_at": datetime.now(UTC).isoformat(timespec="seconds"), "rows": rows},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return index_path


if __name__ == "__main__":  # pragma: no cover
    generate_site(Path("results"), Path("leaderboard"))
