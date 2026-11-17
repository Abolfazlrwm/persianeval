# ADR 0003: Leaderboard Freshness — Weekly seeded subsample

- **Status:** Accepted (amended 2026-11-17) · **Date:** 2026-11-12

<div dir="ltr">

## Context

The full benchmark is 200 items × 8 tasks per model (1,600 in total). Running it weekly on GitHub-hosted
runners with 7-9B local models would take many hours per model and risk flaky,
incomplete runs; running it never would make the leaderboard stale.

## Decision

- The weekly action evaluates a **seeded subsample per task** (seed = ISO week,
  `date +%G%V`): deterministic, publishable, and cheap enough to finish reliably.
- **Amended 2026-11-17:** the subsample is **20 items per task** (down from 50).
  The 2026-11-16/17 leaderboard postmortem showed 7-9B CPU inference at roughly
  45 s/item cannot finish 8 tasks × 50 items inside the 350-minute job budget —
  gemma2:9b and aya-expanse:8b were killed mid-run. 20 items keeps the full
  weekly matrix inside the window; the seed and recorded limit still make every
  subsample exactly reproducible.
- The seed and limit are recorded in every run result, so any subsample can be
  reproduced exactly and audited.
- **Full 1,600-item runs** run at every release (v0.x tags) and are marked as the
  authoritative numbers in `data.json` (`"scope": "full"` vs `"weekly"`).
- Model list lives in the workflow env; adding a model is a one-line PR.
- Raw results are published as `data.json` next to the page, so every number on the
  leaderboard is one click away from its source.

- On partial matrix failure the site is still published from whichever result
  artifacts succeeded (a partially fresh leaderboard beats a stale one).

## Consequences

- Weekly numbers have wider confidence intervals than full runs; the site labels them.
- CI cost stays bounded (~2 hours per model per week on a public runner, CPU inference).

</div>

<div dir="rtl">

## فارسی

**زمینه:** بنچمارک کامل ۹۸۰ نمونه در ۸ تسک است؛ اجرای هفتگی کامل با مدل‌های محلی ۷-۹ میلیارد
پارامتری روی رانرهای GitHub چند ساعت طول می‌کشد و شکننده است؛ عدم اجرا هم لیدربورد را کهنه می‌کند.

**تصمیم:** اکشن هفتگی زیرنمونهٔ seedدار از هر تسک را می‌سنجد (seed = هفتهٔ ISO)؛ قطعی،
قابل انتشار و ارزان. **اصلاح ۱۴۰۵/۰۸/۲۶ (۲۰۲۶-۱۱-۱۷):** حجم زیرنمونه از ۵۰ به **۲۰ قلم در هر تسک**
کاهش یافت — بررسی رخداد ۲۰۲۶-۱۱-۱۶/۱۷ نشان داد استنتاج CPU مدل‌های ۷ تا ۹ میلیاردی با حدود ۴۵
ثانیه به‌ازای هر قلم، ۸ تسک × ۵۰ قلم را در بودجهٔ ۳۵۰ دقیقه‌ای جابجا نمی‌کند و gemma2:9b و
aya-expanse:8b وسط کار کشته می‌شدند. با ۲۰ قلم کل ماتریس هفتگی در پنجره جا می‌شود؛ seed و
limit ثبت‌شده در نتایج همچنان بازتولید دقیق هر زیرنمونه را تضمین می‌کند. در شکست جزئی ماتریس،
سایت از آرتیفکت‌های موفق منتشر می‌شود (لیدربورد نیمه‌تازه بهتر از لیدربورد کهنه است).

**پیامد:** اعداد هفتگی بازهٔ اطمینان بزرگ‌تری دارند و سایت این را برچسب می‌زند؛ هزینهٔ CI محدود
می‌ماند (حدود ۲ ساعت به‌ازای هر مدل در هفته روی رانر CPU).

</div>
