# PersianEval v1 Data — Provenance, Licenses & Methodology

<div dir="rtl">

## فارسی

این پوشه شامل مجموعه‌داده‌های فریزشدهٔ نسخهٔ v1 است. هر فایل JSONL با اسکیمای صریح
`{"id", "prompt", "expected", "metadata"}` و فایل `SHA256SUMS` برای اطمینان از تغییرنکردن
داده‌ها ارائه می‌شود. هیچ نمونه‌ای پس از انتشار نسخه تغییر نمی‌کند؛ نسخه‌های بعدی در پوشه‌های
جدا (v2 و ...) منتشر می‌شوند.

| فایل | تعداد نمونه | روش گردآوری | هدف نسخهٔ 0.2 |
|---|---|---|---|
| `reasoning.jsonl` | ۲۰۰ | تولید برنامه‌نویسی‌شده با پاسخ‌های محاسبه‌شده (۷ خانوادهٔ مسئله) | ۳۰۰ |
| `spelling.jsonl` | ۲۰۰ | تولید سیستماتیک از بانک واژه/جمله با خرابی عمدی هم‌گردانی | ۲۵۰ |
| `cultural_knowledge.jsonl` | ۲۰۰ | نگارش دستی (سطح کتاب‌های درسی، حقایق بااطمینان) | ۳۰۰ |
| `reading_comprehension.jsonl` | ۲۰۰ | ۵۰ متن دست‌نویس × ۴ پرسش | ۳۰۰ (۷۵ متن) |
| `translation_fa_en.jsonl` | ۲۰۰ | جفت‌جمله‌های دست‌نویس در ۴ سبک | ۳۰۰ (زیرمجموعهٔ FLORES-200) |
| `rag_faithfulness.jsonl` | ۲۰۰ | ۵۰ متن سنتزی × ۲ پرسش × پاسخ وفادار/غیروفادار | ۳۰۰ |
| `bias_detection.jsonl` | ۲۰۰ | ۱۴ قالب روی ۹ گروه ایرانی + ۲۴ آیتم جنسیتی + ۵۰ کنترل | ۳۰۰ |
| `code_with_persian_comments.jsonl` | ۲۰۰ | ۱۵ خانوادهٔ تابع با واریانت‌های متفاوت و تست‌های محاسبه‌شده | ۳۰۰ |

### روش‌شناسی در یک نگاه

- **پاسخ صحیح با ساخت تضمین‌شده:** در تسک‌های تولیدشده به‌صورت برنامه‌نویسی (reasoning،
  spelling، rag، code)، پاسخ مرجع با کد محاسبه می‌شود، نه با حدس انسانی.
- **متن‌های سنتزی برای RAG:** متن‌های `rag_faithfulness` آگاهانه سنتزی‌اند (نهادها و اعداد
  فرضی) چون معیار سنجش «وفاداری به متنِ ارائه‌شده» است نه دانش جهانی؛ این کار از اختلاف نظر
  واقعیتی هم جلوگیری می‌کند.
- **حقایق با اطمینان بالا برای دانش فرهنگی:** پرسش‌های `cultural_knowledge` به حقایق
  سطح کتاب‌های درسی محدود شده‌اند.
- **داوری شفاف:** پرامپت داورِ هر تسک LLM-judge در سورس همان کلاس تسک و در
  `docs/methodology.md` عمومی است.

### لایسنس

کل مجموعه‌داده (مثل کد) تحت **Apache-2.0** منتشر می‌شود و بازاستفادهٔ تجاری و پژوهشی آزاد است.
هیچ بخشی از داده از دیتاست‌های محدودیت‌دار کپی نشده است؛ برای v0.2 که زیرمجموعه‌ای از
FLORES-200 (لایسنس CC-BY-SA) اضافه می‌شود، فایل لایسنس جداگانه در همین پوشه قرار می‌گیرد.

### بازتولید

```bash
python scripts/generate_data/run_all.py   # همهٔ فایل‌ها + SHA256SUMS را بازتولید می‌کند
sha256sum -c src/persianeval/data/v1/SHA256SUMS --directory src/persianeval/data/v1
```

</div>

---

<div dir="ltr">

## English

This directory holds the frozen v1 datasets. Every JSONL file follows the explicit schema
`{"id", "prompt", "expected", "metadata"}` and is covered by `SHA256SUMS` so any
accidental mutation is caught in CI. Samples never change after a release; future dataset
revisions ship in new directories (v2, ...).

See the Persian table above for per-task counts, collection method and the v0.2 target.
Highlights:

- **Correct-by-construction answers** for programmatically generated tasks (reasoning,
  spelling, rag, code): reference answers are computed by code, not guessed.
- **Synthetic passages** for RAG faithfulness — deliberately fictional entities/numbers,
  because the skill under test is grounding in the *provided* text, not world knowledge.
- **High-confidence textbook facts only** for cultural knowledge.
- **Judge prompts are public** — they live in each task class source and in
  `docs/methodology.md`.

### License

The datasets ship under the same **Apache-2.0** license as the code. No data was copied
from restricted datasets; the planned FLORES-200 subset (CC-BY-SA) for v0.2 will carry its
own license note in this directory.

### Reproducibility

```bash
python scripts/generate_data/run_all.py   # regenerates every file + SHA256SUMS
sha256sum -c src/persianeval/data/v1/SHA256SUMS --directory src/persianeval/data/v1
```

</div>
