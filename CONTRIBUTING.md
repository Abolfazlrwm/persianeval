# Contributing to PersianEval — مشارکت در PersianEval

<div dir="ltr">

## English

Thank you for helping build the first serious open-source Persian LLM benchmark. Every
contribution type is welcome — data, code, docs, evaluations.

### Dev setup

```bash
git clone https://github.com/Abolfazlrwm/persianeval && cd persianeval
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make ci          # ruff + mypy --strict + pytest (coverage >= 80%)
```

### Ground rules

1. **The three gates are non-negotiable**: `ruff check .`, `mypy --strict src tests
   scripts`, `pytest --cov-fail-under=80`. CI enforces them on Python 3.11–3.13.
2. **No placeholders.** No `TODO`, `FIXME`, commented-out code or `pass` without a
   documented reason.
3. **Data is provenance-or-it-does-not-exist.** Any dataset change ships with its source
   and license in `src/persianeval/data/README.md` and regenerated `SHA256SUMS`
   (`python scripts/generate_data/run_all.py`).
4. **Decisions become ADRs.** Anything that changes scoring, task design or the
   leaderboard pipeline needs a short note in `docs/adr/`.
5. **Bilingual docs.** User-facing docs carry an English and a Persian section.
6. **NumPy-style docstrings** on every public API.

### Contribution types

- **New task** → follow `docs/adding_a_task.md`, then open a PR with the
  `task` label; also fill a "New evaluation task" issue first for discussion.
- **More samples for an existing task** → extend the generator script (correctness by
  construction beats hand-edited files) or add hand-authored items with metadata
  sources; regenerate checksums.
- **Harness/provider improvements** → please include an offline test (httpx
  `MockTransport` or `ScriptedProvider`) — no test, no merge.
- **Leaderboard models** → one-line change in `.github/workflows/leaderboard.yml`.

### Review process

Small PRs (< 400 lines) are reviewed within a few days. Data PRs get an extra
correctness pass: a maintainer re-runs the generator and verifies checksums.

</div>

---

<div dir="rtl">

## فارسی

از اینکه در ساخت اولین بنچمارک جدی متن‌باز برای مدل‌های زبانی فارسی کمک می‌کنید سپاسگزاریم.
هر نوع مشارکتی — داده، کد، مستندات، ارزیابی — خوش‌آمد است.

### راه‌اندازی محیط توسعه

```bash
git clone https://github.com/Abolfazlrwm/persianeval && cd persianeval
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make ci          # ruff + mypy --strict + pytest (پوشش ۸۰٪ به بالا)
```

### قواعد ضروری

۱. **سه گیت قابل مذاکره نیستند**: `ruff check .`، `mypy --strict src tests scripts` و
`pytest --cov-fail-under=80`؛ CI روی پایتون ۳٫۱۱ تا ۳٫۱۳ اجباری‌شان می‌کند.

۲. **هیچ placeholder ممنوع.** بدون `TODO`، `FIXME`، کد کامنت‌شده یا `pass` بی‌دلیل.

۳. **داده بدون منبع، وجود ندارد.** هر تغییر داده باید منبع و لایسنس در
`src/persianeval/data/README.md` و `SHA256SUMS` بازتولیدشده داشته باشد.

۴. **تصمیم‌ها ADR می‌شوند.** هر تغییری در امتیازدهی، طراحی تسک یا خط لولهٔ لیدربورد باید
یادداشت کوتاهی در `docs/adr/` داشته باشد.

۵. **مستندات دوزبانه** (انگلیسی + فارسی) و **docstring به سبک NumPy** برای APIهای عمومی.

### انواع مشارکت

- **تسک جدید** → طبق `docs/adding_a_task.md`؛ اول یک اِشوی «تسک ارزیابی جدید» برای بحث باز کنید.
- **افزودن نمونه به تسک موجود** → اسکریپت تولید را گسترش دهید (صحت با ساخت) یا نمونه‌های دستی با
  منبع در metadata اضافه کنید و checksumها را بازتولید کنید.
- **بهبود هارنس/پروایدر** → حتماً تست آفلاین (`MockTransport` یا `ScriptedProvider`) همراه باشد.
- **افزودن مدل به لیدربورد** → تغییر یک‌خطی در `.github/workflows/leaderboard.yml`.

### فرایند بازبینی

PRهای کوچک ظرف چند روز بازبینی می‌شوند؛ PRهای داده یک بازبینی صحتِ اضافه دارند: بازتولید
تولیدکننده و تطبیق checksumها.

</div>
