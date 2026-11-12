"""Spelling & encoding task: Persian/Arabic script confusions and half-spaces."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec


class SpellingTask(AbstractTask):
    """Detect and fix Persian orthography and encoding mistakes.

    Covers the single biggest source of Persian text errors in the wild:
    Arabic ``ي/ك`` homoglyphs, Arabic-Indic digits, wrong ``ه/ۀ`` usage and
    missing zero-width non-joiners (نیم‌فاصله).
    """

    name = "spelling"
    title_en = "Spelling & Encoding (FA)"
    title_fa = "املا و هم‌گردانی"
    description_en = (
        "Persian orthography and script-encoding errors: Arabic yeh/kaf "
        "homoglyphs, Arabic digits, and zero-width non-joiner usage."
    )
    description_fa = "خطاهای نگارشی و هم‌گردانی فارسی: حروف عربی «ي/ك»، ارقام عربی و کاربرد نیم‌فاصله."
    data_file = "spelling.jsonl"
    min_samples = 200
    system_prompt = (
        "تو ویراستار دقیق متون فارسی هستی. دقیقاً طبق دستور هر پرسش پاسخ بده "
        "و از حروف فارسی (ی، ک) و نیم‌فاصله استاندارد استفاده کن."
    )
    scoring = ScoringSpec(kind=ScoringKind.FUZZY, fuzzy_threshold=0.90, normalize_keep_zwnj=True)
    source = (
        "Generated from a curated 200+ word/sentence pool with systematic "
        "Arab-script corruption (scripts/generate_data/gen_spelling.py). Apache-2.0."
    )
