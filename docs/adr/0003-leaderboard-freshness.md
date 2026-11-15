# ADR 0003: Leaderboard Freshness — Weekly seeded subsample

- **Status:** Accepted · **Date:** 2026-11-12

<div dir="ltr">

## Context

The full benchmark is 200 items × 8 tasks per model (1,600 in total). Running it weekly on GitHub-hosted
runners with 7-9B local models would take many hours per model and risk flaky,
incomplete runs; running it never would make the leaderboard stale.

## Decision

- The weekly action evaluates a **seeded 50-item subsample per task** (seed = ISO week,
  `date +%G%V`): deterministic, publishable, and cheap enough to finish reliably.
- The seed and limit are recorded in every run result, so any subsample can be
  reproduced exactly and audited.
- **Full 1,600-item runs** run at every release (v0.x tags) and are marked as the
  authoritative numbers in `data.json` (`"scope": "full"` vs `"weekly"`).
- Model list lives in the workflow env; adding a model is a one-line PR.
- Raw results are published as `data.json` next to the page, so every number on the
  leaderboard is one click away from its source.

## Consequences

- Weekly numbers have wider confidence intervals than full runs; the site labels them.
- CI cost stays bounded (~1 hour per model per week on a public runner).

</div>

<div dir="rtl">

## فارسی

**زمینه:** بنچمارک کامل ۹۸۰ نمونه در ۸ تسک است؛ اجرای هفتگی کامل با مدل‌های محلی ۷-۹ میلیارد
پارامتری روی رانرهای GitHub چند ساعت طول می‌کشد و شکننده است؛ عدم اجرا هم لیدربورد را کهنه می‌کند.

**تصمیم:** اکشن هفتگی زیرنمونهٔ seedدار ۵۰تایی از هر تسک را می‌سنجد (seed = هفتهٔ ISO)؛ قطعی،
قابل انتشار و ارزان. seed و limit در نتایج ثبت می‌شود تا هر زیرنمونه دقیقاً بازتولید و ممیزی
شود. اجرای کامل ۹۸۰تایی در هر ریلیز انجام و اعداد آن به‌عنوان مرجع در `data.json` علامت‌گذاری
می‌شود. فهرست مدل‌ها در env ورک‌فلو است و افزودن مدل یک خط PR است. نتایج خام کنار صفحه منتشر
می‌شود تا هر عدد لیدربورد یک کلیک با منبعش فاصله داشته باشد.

**پیامد:** اعداد هفتگی بازهٔ اطمینان بزرگ‌تری دارند و سایت این را برچسب می‌زند؛ هزینهٔ CI محدود
می‌ماند (حدود یک ساعت به‌ازای هر مدل در هفته).

</div>
