# ADR 0002: Scoring Policy — Normalization, thresholds and judging

- **Status:** Accepted · **Date:** 2026-11-12

<div dir="ltr">

## Context

Persian answers arrive with mixed scripts (Arabic vs Persian yeh/kaf), mixed digits
(Persian vs ASCII), optional half-spaces, polite prefixes (`پاسخ:`) and trailing units
(`تومان`). A naive `==` comparison would punish correct answers; a naive `in` comparison
would accept rambles.

## Decision

1. One canonical `normalize_text` pipeline (documented in `docs/methodology.md`) runs
   before every string comparison; the ZWNJ is preserved only for the spelling task,
   which explicitly tests it.
2. `exact` accepts full response, first token or last token (after normalization and
   optional `strip_tokens`); everything stricter stays strict.
3. `fuzzy` = SequenceMatcher ratio + containment bonus; thresholds are per task
   (reading 0.85, spelling 0.90) and recorded in every result file.
4. `judge` prompts are public constants in the task class; output must be JSON
   `{"score", "rationale"}`; 0-10 scales are rescaled; parse failures score 0 with the
   error recorded. Pass thresholds: 0.70 (bias), 0.75 (translation, code).
5. Temperature is pinned to 0.0 and judge max_tokens to 512 for reproducibility.

## Consequences

- Scoring is inspectable and diffable — changing a rubric is a visible, reviewable PR.
- v0.1 judge tasks default to self-judging (same model); the weekly leaderboard treats
  these as directional. v0.2 introduces a fixed cross-judge model configured per run.

</div>

<div dir="rtl">

## فارسی

**زمینه:** پاسخ‌های فارسی با نگارش ترکیبی (ي/ی، ك/ک)، ارقام مختلف، نیم‌فاصلهٔ اختیاری، پیشوند
«پاسخ:» و واحدهای پایانی («تومان») می‌آیند؛ مقایسهٔ سخت‌گیرانهٔ `==` پاسخ درست را جریمه و
مقایسهٔ سطحی `in` پاسخ‌های پرگور را قبول می‌کند.

**تصمیم:** یک خط لولهٔ `normalize_text` قبل از همهٔ مقایسه‌ها؛ حذف نیم‌فاصله فقط در تسک spelling
غیرفعال می‌شود. `exact` سه نامزد را می‌پذیرد (کل پاسخ، نخستین توکن، آخرین توکن). `fuzzy` نسبت
SequenceMatcher با پاداش اشتمال است و آستانه‌های هر تسک در فایل نتایج ثبت می‌شود. پرامپت داورها
ثابت و عمومی‌اند، خروجی باید JSON باشد، مقیاس ۰-۱۰ به ۰-۱ تبدیل و خرابیِ تجزیه امتیاز صفر می‌گیرد.
دمای صفر و max_tokens داور = ۵۱۲ برای تکرارپذیری.

**پیامد:** امتیازدهی قابل بازبینی است؛ تغییر رubric یک PR مرئی است. در v0.1 داوریِ خودِ مدل
پیش‌فرض است و لیدربورد این اعداد را جهت‌نما می‌داند؛ v0.2 داور ثابت جداگانه خواهد داشت.

</div>
