# ADR 0001: Task Design — Class-per-task over YAML

- **Status:** Accepted · **Date:** 2026-11-12

<div dir="ltr">

## Context

Every evaluation task needs: frozen data, a prompt strategy, a scorer, judge context and
display metadata. Two obvious shapes exist: fully declarative (YAML/JSON task specs
interpreted by one generic engine) or one Python subclass per task.

## Decision

Each task is a Python subclass of `AbstractTask` with ClassVar configuration, plus a
JSONL data file. Task discovery merges builtin classes with third-party entry points
(`persianeval.tasks` group).

## Rationale

- Judge tasks need real logic (context assembly, per-task rubrics) that YAML specs
  uglify or cannot express; Python keeps those reviewable and typed.
- `mypy --strict` can check task definitions; YAML specs get checked only at runtime.
- The 15-minute "add a task" path is preserved because the ClassVar surface is small;
  genericity lives in the harness, not in a spec language.
- Entry points give us the plugin architecture without a config-parser of our own.

## Consequences

- Adding a task requires a code PR (acceptable — data changes are PRs anyway).
- Non-developer contributions happen at the data layer (JSONL + generator scripts),
  which is where correctness matters most.

</div>

<div dir="rtl">

## فارسی

**زمینه:** هر تسک به دادهٔ فریز، استراتژی پرامپت، امتیازدهی، زمینهٔ داوری و متادیتا نیاز دارد؛
دو شکل رایج: تعریف کامل declarative (YAML) یا یک زیرکلاس پایتون برای هر تسک.

**تصمیم:** هر تسک زیرکلاسی از `AbstractTask` با تنظیمات ClassVar به‌علاوهٔ فایل JSONL است؛
کشف تسک‌ها ترکیبی از کلاس‌های داخلی و entry-pointهای خارجی (گروه `persianeval.tasks`) است.

**دلیل:** تسک‌های داوری به منطق واقعی نیاز دارند که در YAML زشت یا ناممکن است؛ `mypy --strict`
تعریف تسک‌ها را چک می‌کند؛ مسیر «افزودن تسک در ۱۵ دقیقه» حفظ شده چون سطح ClassVar کوچک است.

**پیامد:** افزودن تسک نیازمند PR کد است (قابل قبول)؛ مشارکت غیرتوسعه‌دهنده‌ها در لایهٔ داده
(JSONL + اسکریپت‌های تولید) اتفاق می‌افتد که مهم‌ترین لایه از نظر صحت است.

</div>
