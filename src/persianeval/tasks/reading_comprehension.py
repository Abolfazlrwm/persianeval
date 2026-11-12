"""Reading comprehension task: Persian passage + short-answer questions."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec


class ReadingComprehensionTask(AbstractTask):
    """Read a Persian passage and answer short, literal questions.

    Passages cover Iranian culture, geography, science and daily life;
    every answer is extractable from the passage. Fuzzy scoring absorbs
    harmless wording differences.
    """

    name = "reading_comprehension"
    title_en = "Reading Comprehension (FA)"
    title_fa = "درک مطلب"
    description_en = "Persian passage plus short literal questions; answers are extractable from the passage."
    description_fa = "متن فارسی به‌همراه پرسش‌های کوتاه مستقیم؛ پاسخ هر پرسش از خود متن قابل استخراج است."
    data_file = "reading_comprehension.jsonl"
    min_samples = 200
    system_prompt = "با توجه به متن داده‌شده، فقط پاسخ کوتاه و مستقیم را بنویس؛ توضیح اضافه نده."
    scoring = ScoringSpec(kind=ScoringKind.FUZZY, fuzzy_threshold=0.85)
    source = (
        "Expert-authored passages on Iranian culture, geography and daily life "
        "(scripts/generate_data/gen_reading.py); all answers verbatim in text. Apache-2.0."
    )
