# Submitting results to the leaderboard

The leaderboard has two entry paths. Pick the one that matches your setup;
both end up on the same page, and neither bypasses the validator.

<div dir="rtl">

# ارسال نتایج به لیدربورد

برای رسیدن به لیدربورد دو مسیر وجود دارد؛ مسیری را انتخاب کنید که با شرایط
شما سازگار است. هر دو مسیر از یک اعتبارسنج عبور می‌کنند.

</div>

---

## Path A — one line in the weekly workflow

If your model is reachable from GitHub-hosted runners (OpenAI, Anthropic,
Z.ai hosted APIs, or anything behind a public endpoint), add it to the
model matrix in `.github/workflows/leaderboard.yml`. The weekly schedule
then evaluates it with the current ISO-week seed and rebuilds the page.
No result files to attach — the run is reproducible from the workflow log.

```yaml
    strategy:
      matrix:
        model: [glm-4-plus, gpt-4o-mini]   # add yours here
```

**Requirement:** the repository secret that carries your API key
(e.g. `OPENAI_API_KEY`) must exist. Keep `temperature` at `0` — the
harness default — so the run is deterministic.

<div dir="rtl">

## مسیر الف — یک خط در ورک‌فلوی هفتگی

اگر مدل شما از رانرهای GitHub در دسترس است، آن را به ماتریس مدل‌ها در
`.github/workflows/leaderboard.yml` اضافه کنید. اجرای هفتگی با seed هفتهٔ
ISO جاری انجام می‌شود و صفحه بازسازی می‌شود. کلید API را به‌صورت secret
نگه دارید و `temperature` را صفر بگذارید تا اجرا قطعی باشد.

</div>

---

## Path B — a results PR from your own run

For local models (Ollama, vLLM) or hosted models whose keys cannot be
shared, run the harness yourself and open a PR with the JSON files.

### 1. Pick the protocol (ADR 0003)

| Mode | Command | Notes |
|------|---------|-------|
| Full corpus (preferred) | omit `--limit` | all 200 items per task |
| Weekly subsample | `--limit 20 --seed $(date -u +%G%V)` | the exact weekly protocol |

State which mode you used in the PR description; a result without a
protocol statement cannot be ranked next to full-corpus runs.

### 2. Run the harness

```bash
pip install persianeval

# Hosted API example
persianeval run --task reasoning --provider openai --model gpt-4o \
    --org "OpenAI" --license "Proprietary (hosted API)" --out results

# Local model example
persianeval run --task reasoning --provider ollama \
    --model qwen2.5:7b-instruct --org "community" \
    --license "Apache-2.0" --request-timeout 300 --out results
```

Repeat per task, or loop over `persianeval tasks`. Keep `temperature`
at its default (0.0) and set `--org`/`--license` so the leaderboard
renders complete rows.

### 3. Validate before opening the PR

```bash
persianeval validate-results results
```

Everything printed as `FAIL` must be fixed — CI runs the same command and
will reject the PR. `WARN` lines are informational: cache hits, subset
runs below the task minimum, nonzero temperature, empty metadata.

### 4. What to commit

```bash
git checkout -b results/my-model
git add results/<task>__<model>.json     # JSON only
git commit -m "results: my-model over the week-N subsample"
```

- Commit the JSON files only. `results/*.parquet` and `.persianeval_cache/`
  stay local (the JSON *is* the audit trail — see `results/README.md`).
- Never edit metrics or per-item scores by hand. The validator recomputes
  `accuracy` and `mean_score` from the per-item data and a mismatch fails
  CI; hand-edited entries are also a ban-worthy offense against the
  project's honesty policy.

### 5. Open the PR

Use the default PR template, state the protocol (mode, seed, command) and
link to where a reviewer can reproduce the run. A maintainer re-checks the
metadata (provider, org, license) before merging; the next leaderboard
build picks the files up automatically.

<div dir="rtl">

## مسیر ب — PR نتایج از اجرای شخصی

برای مدل‌های محلی (Ollama، vLLM) یا مدل‌هایی که کلیدشان قابل اشتراک نیست،
خودتان هارنس را اجرا کنید و فایل‌های JSON را با PR بفرستید.

**۱. پروتکل را انتخاب کنید (ADR 0003):** یا کورپوس کامل (بدون `--limit`)
یا زیرنمونهٔ هفتگی با `--limit 20 --seed $(date -u +%G%V)`. حالت مورد
استفاده را در توضیح PR بنویسید.

**۲. هارنس را اجرا کنید:** به نمونه‌های بالا نگاه کنید؛ `temperature` صفر
بماند و `--org`/`--license` را تنظیم کنید.

**۳. قبل از PR اعتبارسنجی کنید:** `persianeval validate-results results` —
هر خط `FAIL` باید رفع شود، چون CI همین دستور را اجرا می‌کند.

**۴. چه چیزی کامیت شود:** فقط JSON. فایل‌های parquet و کش محلی می‌مانند.
ویرایش دستی متریک‌ها ممنوع است؛ اعتبارسنج دقت را از دادهٔ آیتم‌ها
بازمحاسبه می‌کند و مغایرت، CI را قرمز می‌کند.

**۵. PR را باز کنید:** پروتکل (حالت، seed، دستور اجرا) را ذکر کنید تا
بازبینی بتواند اجرا را بازتولید کند. پس از مرج، ساخت بعدی لیدربورد فایل‌ها
را خودکار برمی‌دارد.

</div>
