# Methodology — روش‌شناسی

<div dir="ltr">

## English

### Design principles

1. **Determinism by default.** Every run pins `seed=42` (configurable), `temperature=0.0`
   and caches responses per `provider+model+task+seed+prompt`. Re-running a finished task
   never re-bills the API.
2. **Frozen data.** Datasets live in `src/persianeval/data/v1`, are covered by
   `SHA256SUMS`, and never change after release. `test_data_integrity.py` verifies the
   schema, uniqueness, counts and checksums in CI.
3. **Explicit scoring.** Each task declares a `ScoringSpec` (exact / fuzzy / judge) in
   code; judge prompts are public and reviewable in the task class source.
4. **Honest provenance.** Every dataset documents how it was produced. Synthetic data is
   labeled synthetic; authored data is labeled authored.

### Scoring policy (summary of ADR 0002)

**Normalization** (applied before every string comparison): Arabic `ي/ك` → Persian
`ی/ک`; Persian and Arabic-Indic digits → ASCII; numeric thousand separators between
digits removed; Arabic diacritics and tatweel stripped; zero-width non-joiner removed
(except spelling tasks, which must test it); punctuation dropped; whitespace collapsed.

- **exact** — normalized equality of full response, first token or last token. Used when
  the answer is canonical (numbers, MCQ letters, بله/خیر). The first/last-token rule
  absorbs conventional prefixes like `پاسخ:` and trailing units like `تومان`.
- **fuzzy** — `difflib.SequenceMatcher` ratio over normalized text with a containment
  bonus (reference found inside response ⇒ 1.0). Thresholds: reading 0.85, spelling 0.90
  (with ZWNJ preserved).
- **LLM-as-judge** — the task's judge prompt is rendered with `{question}`, `{expected}`,
  `{metadata}` and `{response}`; the judge must return
  `{"score": 0..1, "rationale": "..."}`. Scores on a 0-10 scale are rescaled; unparseable
  output scores 0 and is recorded in `details.error`. Items pass at the task's
  `score_pass_threshold` (0.70–0.75).

**Known limitations (v0.1).** Judge tasks default to the same model self-judging, which
biases scores upward — the weekly leaderboard therefore treats judge-task numbers as
directional, and ADR 0002 plans a fixed cross-judge model for v0.2. Translation
references are expert-written but a single reference; judges are instructed to accept
reasonable paraphrases.

### Reproducing the leaderboard pipeline

```bash
ollama serve &                                # or any OpenAI-compatible server
persianeval run --task reasoning --provider ollama --model qwen2.5:7b-instruct --limit 50
persianeval leaderboard --results-dir results --out site
```

The weekly action (ADR 0003) evaluates a seeded 20-item subsample per task per model;
seeds follow the ISO week (`date +%G%V`) so each week's subset is deterministic and
publishable. Full 1600-item runs are done per release.

</div>

---

<div dir="rtl">

## فارسی

### اصول طراحی

۱. **تکرارپذیری به‌صورت پیش‌فرض.** هر اجرا `seed=42` (قابل تغییر)، دمای صفر و کشِ پاسخ به‌ازای
`provider+model+task+seed+prompt` دارد؛ اجرای دوبارهٔ یک تسک تمام‌شده هزینهٔ جدیدی ایجاد نمی‌کند.

۲. **دادهٔ فریز.** مجموعه‌داده‌ها در `src/persianeval/data/v1` با `SHA256SUMS` محافظت می‌شوند و
پس از انتشار تغییر نمی‌کنند؛ `test_data_integrity.py` اسکیما، یکتایی، تعداد و checksumها را در CI
کنترل می‌کند.

۳. **امتیازدهی صریح.** هر تسک `ScoringSpec` خودش (exact / fuzzy / judge) را در کد تعریف می‌کند؛
پرامپت داورها عمومی و در سورس کلاس تسک قابل بازبینی است.

۴. **منبع صادقانه.** هر دیتاست روش تولیدش را مستند می‌کند؛ دادهٔ سنتزی «سنتزی» و دادهٔ دست‌نویس
«دست‌نویس» معرفی می‌شود.

### سیاست امتیازدهی (خلاصهٔ ADR 0002)

**نرمال‌سازی** (پیش از هر مقایسهٔ رشته‌ای): «ي/ك» عربی → «ی/ک» فارسی؛ ارقام فارسی و عربی →
ASCII؛ حذف جداکنندهٔ هزارگان بین ارقام؛ حذف اعراب و کشیدگی؛ حذف نیم‌فاصله (به‌جز تسک spelling که
دقیقاً باید آن را بسنجد)؛ حذف علائم؛ یکسان‌سازی فاصله‌ها.

- **exact** — برابری کاملِ نرمال‌شده، یا نخستین/آخرین توکن پاسخ. برای پاسخ‌های قطعی (عدد، حرف
  گزینه، بله/خیر). قانون اولین/آخرین توکن، پیشوندهای متعارف مثل «پاسخ:» و واحدهای پایانی مثل
  «تومان» را می‌بلعد.
- **fuzzy** — نسبت `SequenceMatcher` روی متن نرمال‌شده با پاداشِ اشتمال (وجود پاسخ مرجع در متن
  پاسخ ⇒ ۱٫۰). آستانه‌ها: درک مطلب ۰٫۸۵، املا ۰٫۹۰ (با حفظ نیم‌فاصله).
- **داور LLM** — پرامپت داور با `{question}`، `{expected}`، `{metadata}` و `{response}` رندر
  می‌شود؛ داور باید `{"score": 0..1, "rationale": "..."}` برگرداند. مقیاس ۰ تا ۱۰ به ۰ تا ۱
  تبدیل می‌شود؛ خروجی تجزیه‌ناپذیر امتیاز صفر می‌گیرد و در `details.error` ثبت می‌شود.

**محدودیت‌های شناخته‌شده (v0.1).** در تسک‌های داوری، به‌طور پیش‌فرض همان مدلِ تحت ارزیابی خودش را
داوری می‌کند که امتیازها را به بالا می‌کشاند؛ به همین دلیل لیدربورد هفتگی اعداد تسک‌های داوری را
«جهت‌نما» می‌داند و ADR 0002 داور ثابتِ جداگانه برای v0.2 را برنامه‌ریزی کرده است.

### بازتولید خط لولهٔ لیدربورد

```bash
ollama serve &                                # یا هر سرور سازگار با OpenAI
persianeval run --task reasoning --provider ollama --model qwen2.5:7b-instruct --limit 50
persianeval leaderboard --results-dir results --out site
```

اکشن هفتگی (ADR 0003) هر هفته زیرنمونهٔ seedدارِ ۲۰تایی از هر تسک را برای هر مدل می‌سنجد؛ seed از
شمارهٔ هفتهٔ ISO به دست می‌آید (`date +%G%V`) تا زیرمجموعهٔ هر هفته قطعی و قابل انتشار باشد.
اجرای کامل ۱۶۰۰ نمونه‌ای در هر ریلیز انجام می‌شود.

</div>
