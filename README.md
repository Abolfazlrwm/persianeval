<div dir="ltr" align="center">

<img src="docs/assets/banner.svg" alt="PersianEval — Open-source LLM benchmark for Persian" width="100%">

# PersianEval

**The first serious open-source benchmark for evaluating LLMs on Persian (Farsi).**
**اولین بنچمارک متن‌بازِ جدی برای ارزیابی مدل‌های زبانی فارسی**

[![CI](https://github.com/Abolfazlrwm/persianeval/actions/workflows/ci.yml/badge.svg)](https://github.com/Abolfazlrwm/persianeval/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/persianeval)](https://pypi.org/project/persianeval/)
[![Python](https://img.shields.io/pypi/pyversions/persianeval)](https://pypi.org/project/persianeval/)
[![License](https://img.shields.io/pypi/l/persianeval)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Abolfazlrwm/persianeval?style=social)](https://github.com/Abolfazlrwm/persianeval/stargazers)
[![PyPI downloads](https://img.shields.io/pypi/dm/persianeval)](https://pypi.org/project/persianeval/)

[English](#english) · [فارسی](#فارسی) · [Leaderboard](https://Abolfazlrwm.github.io/persianeval/)

</div>

<div dir="ltr">

## English

### Why this project matters

Persian is spoken by more than 100 million people, yet the LLM ecosystem has almost no
*trustworthy* way to measure Persian capability. Popular leaderboards barely cover Farsi,
translated datasets are often machine-translated and leaked into training data, and the
challenges that are uniquely Persian go unseen in most benchmarks: Arabic/Persian
homoglyphs (ي/ی، ك/ک), half-space rules (نیم‌فاصله), and the cultural commons of Iran.
**PersianEval** fills that gap with 8 frozen, checksummed tasks, a reproducible async
evaluation harness, and an auditable leaderboard pipeline. Everything (code, data,
prompts, judge prompts, scores) is Apache-2.0 and open.

### Tasks (8)

| Task | What it measures | Scoring | Min samples |
|---|---|---|---|
| `reasoning` | Multi-step arithmetic & logic in Persian (GSM8K-style, nativized) | exact | 200 |
| `reading_comprehension` | Passage + short literal questions | fuzzy ≥ 0.85 | 200 |
| `spelling` | ي/ی، ك/ك confusion, Arabic digits, ZWNJ (نیم‌فاصله) | fuzzy ≥ 0.90 | 200 |
| `cultural_knowledge` | Iranian history, literature, geography (MCQ) | exact | 200 |
| `translation_fa_en` | FA↔EN translation, 4 registers | LLM judge | 200 |
| `rag_faithfulness` | Is the answer grounded in the passage? (RAG companion) | exact | 200 |
| `bias_detection` | Stereotype generalization about Iranian groups & gender | LLM judge | 200 |
| `code_with_persian_comments` | Complete Python functions from Persian specs | LLM judge | 200 |

> Every task ships exactly **200 frozen, checksummed samples** since v0.1.0 (1,600 in total) —
> see [data provenance](src/persianeval/data/README.md) for per-task counts and sources.

### Quickstart

```bash
pip install persianeval
export OPENAI_API_KEY=sk-...            # or ANTHROPIC_API_KEY / ZAI_API_KEY / local Ollama
persianeval tasks                       # list the 8 tasks
persianeval run --task reasoning --provider openai --model gpt-4o-mini --rpm 60
persianeval leaderboard --results-dir results --out leaderboard   # static site
```

Every run is **reproducible**: fixed seed (default 42), temperature 0, responses cached per
`provider+model+task+seed+prompt` in `.persianeval_cache/`. Cost is controlled with
`--max-tokens`, `--max-requests-per-minute` and `--max-requests`.

### Sample CLI output

```text
$ persianeval run --task reasoning --provider dummy --model demo --limit 5
task=reasoning provider=dummy model=demo seed=42 temperature=0.0 concurrency=4
--------------------------------------------------------
accuracy : 0.00%   mean score: 0.000
items    : 5 (0 served from cache)
results  : results/reasoning__demo.json
results  : results/reasoning__demo.parquet
```

Results are written with an explicit pydantic schema (`RunResult`, schema version 1.0) to
both **JSON** and **Parquet**.

### Leaderboard

The leaderboard is a dependency-free static page (sortable table + radar chart) that
[`.github/workflows/leaderboard.yml`](.github/workflows/leaderboard.yml) is meant to
regenerate weekly by evaluating a rotating seeded sample of open-source models
(Qwen 2.5, Llama 3.1, Gemma 2, Aya Expanse) through local Ollama runners on GitHub-hosted
CPU runners.

**Status: first real run published (2026-11-25).** GLM-4-Plus (Z.ai hosted API) was
scored by the same harness on the weekly seeded subsample (20 items per task, seed
202648 = ISO week 48): overall **82.9**, with spelling, RAG faithfulness and bias at
100, reading comprehension 90, cultural knowledge 80, reasoning and translation 55.
Judge-scored tasks are self-judged by the model under evaluation (ADR 0002), so read
those numbers as directional. The `code_with_persian_comments` run is pending — the
API's rate limit cut the run short; it will be appended on a re-run and its table cell
shows a dash until then. Every published score is auditable: the per-item result files
are committed under [`results/`](results/). The open-source Ollama models (Qwen 2.5,
Llama 3.1, Gemma 2, Aya Expanse) join the table once a weekly CPU run fits the runner
budget again.

### Adding a model to the leaderboard

Two paths: a one-line addition to the weekly model matrix
(`.github/workflows/leaderboard.yml`) for models reachable from CI runners, or
a results PR from your own run — validated locally with
`persianeval validate-results` before you submit. Full walkthrough:
[`docs/submissions.md`](docs/submissions.md).

### Adding a task in 15 minutes

Implement `AbstractTask`, ship a JSONL file with `{"id","prompt","expected","metadata"}`,
register nothing — the entry-point group `persianeval.tasks` picks external packages up
automatically. Full walkthrough: [`docs/adding_a_task.md`](docs/adding_a_task.md).

### Contributing

PRs welcome — data additions must carry a documented source and a permissive license;
code must pass `ruff`, `mypy --strict` and `pytest ≥ 80%` coverage (CI enforces all
three). See [`CONTRIBUTING.md`](CONTRIBUTING.md).

### License & citation

Apache-2.0 — free for research and commercial use, including data reuse. If you use
PersianEval, please cite (see [`CITATION.cff`](CITATION.cff)):

```bibtex
@software{persianeval2026,
  title  = {PersianEval: An Open-Source Benchmark for Persian LLMs},
  author = {PersianEval Contributors},
  year   = {2026},
  url    = {https://github.com/Abolfazlrwm/persianeval},
  version= {v0.2.0}
}
```

</div>

<div dir="rtl">

## فارسی

### چرا این پروژه مهم است

بیش از ۱۰۰ میلیون نفر فارسی‌زبان‌اند، اما اکوسیستم مدل‌های زبانی تقریباً هیچ راه *قابل
اعتمادی* برای سنجش توانایی فارسی ندارد. لیدربوردهای معروف فارسی را پوشش نمی‌دهند،
دیتاست‌های ترجمه‌شده اغلب با ماشین ترجمه شده‌اند و احتمالاً به داده‌های آموزشی نشت کرده‌اند،
و چالش‌های «تک‌فارسی» (هم‌گردانی عربی/فارسی ي/ی، ك/ک؛ قواعد نیم‌فاصله؛ دانش فرهنگی
ایران) در بیشتر بنچمارک‌ها دیده نمی‌شوند. **PersianEval** این خلأ را پر می‌کند: ۸ تسک
فریزشده و checksumدار، یک هارنس ارزیابی async و تکرارپذیر، و یک خط لیدربوردِ ممیزی‌پذیر.
همه‌چیز (کد، داده، پرامپت، پرسش‌های داور و نتایج) با لایسنس Apache-2.0 باز است.

### تسک‌ها (۸ تسک)

| تسک | چه چیزی را می‌سنجد | امتیازدهی | حداقل نمونه |
|---|---|---|---|
| `reasoning` | استدلال چندمرحله‌ای ریاضی و منطقی به فارسی | exact | ۲۰۰ |
| `reading_comprehension` | متن + پرسش کوتاه مستقیم | fuzzy ≥ ۰٫۸۵ | ۲۰۰ |
| `spelling` | هم‌گردانی ي/ی و ك/ک، ارقام عربی، نیم‌فاصله | fuzzy ≥ ۰٫۹۰ | ۲۰۰ |
| `cultural_knowledge` | تاریخ، ادبیات و جغرافیای ایران (چهارگزینه‌ای) | exact | ۲۰۰ |
| `translation_fa_en` | ترجمهٔ دوسویه در چهار سبک | داور LLM | ۲۰۰ |
| `rag_faithfulness` | آیا پاسخ به متن وفادار است؟ (مکمل RAG فارسی) | exact | ۲۰۰ |
| `bias_detection` | تعمیم کلیشه دربارهٔ گروه‌های ایرانی و جنسیت | داور LLM | ۲۰۰ |
| `code_with_persian_comments` | تکمیل تابع پایتون از توضیح فارسی | داور LLM | ۲۰۰ |

> هر ۸ تسک از نسخهٔ 0.1.0 دقیقاً **۲۰۰ نمونهٔ فریزشده و checksumدار** دارند (مجموعاً
> ۱۶۰۰ نمونه) — شمارش دقیق و منبع هر تسک در
> [مستند داده‌ها](src/persianeval/data/README.md) آمده است.

### شروع سریع

```bash
pip install persianeval
export OPENAI_API_KEY=sk-...            # یا ANTHROPIC_API_KEY / ZAI_API_KEY / مدل محلی با Ollama
persianeval tasks                       # فهرست ۸ تسک
persianeval run --task reasoning --provider openai --model gpt-4o-mini --rpm 60
persianeval leaderboard --results-dir results --out leaderboard   # صفحهٔ استاتیک
```

هر اجرا **تکرارپذیر** است: seed ثابت (پیش‌فرض ۴۲)، دمای صفر، و کشِ پاسخ به‌ازای
`provider+model+task+seed+prompt` در `.persianeval_cache/`. هزینه با `--max-tokens`،
`--max-requests-per-minute` و `--max-requests` کنترل می‌شود.

### خروجی نمونهٔ CLI

```text
$ persianeval run --task reasoning --provider dummy --model demo --limit 5
task=reasoning provider=dummy model=demo seed=42 temperature=0.0 concurrency=4
--------------------------------------------------------
accuracy : 0.00%   mean score: 0.000
items    : 5 (0 served from cache)
results  : results/reasoning__demo.json
results  : results/reasoning__demo.parquet
```

نتایج با اسکیمای صریح pydantic (`RunResult`، نسخهٔ اسکیما ۱٫۰) در هر دو قالب **JSON** و
**Parquet** نوشته می‌شوند.

### لیدربورد

لیدربورد صفحه‌ای استاتیک و بدون وابستگی است (جدول قابل مرتب‌سازی + نمودار رادار) که
`.github/workflows/leaderboard.yml` قرار است هر هفته با ارزیابی نمونه‌ای چرخشی و seedدار از
مدل‌های اپن‌سورس (Qwen 2.5، Llama 3.1، Gemma 2 و Aya Expanse) روی رانرهای CPU گیت‌هاب
بازتولید کند.

**وضعیت: نخستین اجرای واقعی منتشر شد (۲۰۲۶-۱۱-۲۵).** GLM-4-Plus (API میزبانی‌شدهٔ Z.ai)
با همان هارنس روی زیرنمونهٔ هفتگی seedدار (۲۰ نمونه در هر تسک، seed ۲۰۲۶۴۸ = هفتهٔ ۴۸ ISO)
امتیازدهی شد: کلی **۸۲٫۹**؛ املا، وفاداری RAG و تشخیص تعصب ۱۰۰، درک مطلب ۹۰، دانش فرهنگی
۸۰، استدلال و ترجمه ۵۵. در تسک‌های داوری، همان مدلِ تحت ارزیابی داوری کرده است (ADR 0002)؛
پس این اعداد را جهت‌نما بدانید. اجرای `code_with_persian_comments` به‌خاطر محدودیت نرخ API
ناقص مانده و در اجرای بعدی اضافه می‌شود؛ تا آن موقع سلول جدول خط تیره نشان می‌دهد. هر
امتیاز منتشرشده قابل ممیزی است: فایل‌های نتیجهٔ تک‌تک آیتم‌ها در [`results/`](results/)
کامیت شده‌اند. مدل‌های اپن‌سورس Ollama (Qwen 2.5، Llama 3.1، Gemma 2، Aya Expanse) وقتی
بودجهٔ رانر CPU اجازهٔ اجرای هفتگی بدهد به جدول اضافه می‌شوند.

### افزودن مدل به لیدربورد

دو مسیر وجود دارد: افزودن یک خط به ماتریس مدل‌های هفتگی در
`.github/workflows/leaderboard.yml` برای مدل‌هایی که از رانرهای CI در دسترس‌اند،
یا ارسال PR نتایج از اجرای شخصی — که قبل از ارسال با
`persianeval validate-results` اعتبارسنجی می‌شود. راهنمای کامل:
[`docs/submissions.md`](docs/submissions.md).

### اضافه‌کردن تسک جدید در ۱۵ دقیقه

کافی است `AbstractTask` را پیاده کنید و یک فایل JSONL با اسکیمای
`{"id","prompt","expected","metadata"}` اضافه کنید؛ پکیج‌های بیرونی هم به‌صورت خودکار از
طریق گروه entry-point با نام `persianeval.tasks` شناسایی می‌شوند. راهنمای کامل:
[`docs/adding_a_task.md`](docs/adding_a_task.md).

### مشارکت

PR خوش‌آمدید — افزوده‌های داده باید منبع مستند و لایسنس آزاد داشته باشند؛ کد باید
`ruff`، `mypy --strict` و پوشش تست `pytest ≥ ۸۰٪` را پاس کند (CI هر سه را اجباری می‌کند).
بیشتر بخوانید: [`CONTRIBUTING.md`](CONTRIBUTING.md).

### لایسنس و ارجاع

Apache-2.0 — آزاد برای پژوهش و استفادهٔ تجاری، شامل بازاستفادهٔ داده‌ها. اگر از PersianEval
استفاده می‌کنید، لطفاً ارجاع دهید (بخش بالا / [`CITATION.cff`](CITATION.cff)).

</div>
