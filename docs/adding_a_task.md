# Adding a Task in 15 Minutes — اضافه‌کردن تسک در ۱۵ دقیقه

<div dir="ltr">

## English

The plugin contract is a single subclass plus a JSONL file. Nothing else needs to change.

**1. Create the data file** `src/persianeval/data/v1/my_task.jsonl` — one JSON object per
line with the frozen schema:

```json
{"id": "my_task-0001", "prompt": "full user prompt...", "expected": "reference", "metadata": {"source": "..."}}
```

At least 200 samples (100 for LLM-judge tasks). If you generate data with code, add a
script under `scripts/generate_data/` and run `python scripts/generate_data/run_all.py`
to refresh `SHA256SUMS`.

**2. Create the task class** `src/persianeval/tasks/my_task.py`:

```python
"""My task: one-line description."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec


class MyTask(AbstractTask):
    """Full docstring explaining what is measured and how."""

    name = "my_task"
    title_en = "My Task"
    title_fa = "تسک من"
    description_en = "What this measures, in one line."
    description_fa = "این تسک چه چیزی را می‌سنجد."
    data_file = "my_task.jsonl"
    min_samples = 200
    system_prompt = "Instructions to the model under evaluation."
    scoring = ScoringSpec(kind=ScoringKind.EXACT)
    source = "Provenance summary; full story in data README."
```

**3. Register it** — add `MyTask` to the `_BUILTIN` tuple in
`src/persianeval/tasks/__init__.py`. External packages can instead expose an entry point:

```toml
[project.entry-points."persianeval.tasks"]
my_task = "my_package.task:MyTask"
```

**4. Test it** — add cases to `tests/test_tasks.py` (the parametrized load test picks the
task up automatically), then run the gates:

```bash
ruff check . && mypy --strict src tests scripts && pytest
persianeval tasks && persianeval run --task my_task --provider dummy --model demo --limit 5
```

Judge tasks additionally define `scoring.judge_prompt` — a template that may use
`{question}`, `{expected}`, `{metadata}` and `{response}` and must produce a JSON verdict.

</div>

---

<div dir="rtl">

## فارسی

قرارداد پلاگین یک زیرکلاس به‌علاوهٔ یک فایل JSONL است؛ هیچ چیز دیگری لازم نیست تغییر کند.

**۱. فایل داده را بسازید** — `src/persianeval/data/v1/my_task.jsonl` با اسکیمای فریز
`{"id","prompt","expected","metadata"}` (یک شیء JSON در هر خط). حداقل ۲۰۰ نمونه (۱۰۰ برای
تسک‌های داوری). اگر داده را با کد تولید می‌کنید، اسکریپت را در `scripts/generate_data/` بگذارید و
`python scripts/generate_data/run_all.py` را اجرا کنید تا `SHA256SUMS` به‌روز شود.

**۲. کلاس تسک را بنویسید** (نمونهٔ کامل در بخش انگلیسی بالا) — فقط ClassVarها را پر کنید.

**۳. ثبت کنید** — `MyTask` را به تاپل `_BUILTIN` در `src/persianeval/tasks/__init__.py`
اضافه کنید؛ پکیج‌های بیرونی می‌توانند به‌جای آن از entry-point گروه `persianeval.tasks`
استفاده کنند.

**۴. تست کنید** — تست‌های پارامتری `test_tasks.py` تسک تازه را خودکار می‌بینند؛ سپس سه گیت
(`ruff`، `mypy --strict`، `pytest`) و دو دستور `persianeval tasks` /
`persianeval run --task my_task --provider dummy --model demo --limit 5` را اجرا کنید.

برای تسک‌های داوری، `scoring.judge_prompt` را تعریف کنید — قالبی که از
`{question}`، `{expected}`، `{metadata}` و `{response}` استفاده می‌کند و باید حکم JSON برگرداند.

</div>
