"""Cultural knowledge task: Iranian history, literature and geography MCQs."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec


class CulturalKnowledgeTask(AbstractTask):
    """Four-choice questions on Iranian history, literature and geography.

    Restricted to high-confidence, textbook-level facts; every item carries
    its category in metadata.
    """

    name = "cultural_knowledge"
    title_en = "Cultural Knowledge (IR)"
    title_fa = "دانش فرهنگی ایران"
    description_en = (
        "Multiple-choice questions on Iranian history, literature, "
        "geography and culture (textbook-level, high-confidence facts)."
    )
    description_fa = "پرسش‌های چهارگزینه‌ای از تاریخ، ادبیات، جغرافیا و فرهنگ ایران (سطح کتاب‌های درسی)."
    data_file = "cultural_knowledge.jsonl"
    min_samples = 200
    system_prompt = "فقط حرف گزینهٔ درست (الف، ب، ج یا د) را بنویس."
    scoring = ScoringSpec(kind=ScoringKind.EXACT)
    source = (
        "Expert-authored MCQs from public-domain textbook-level knowledge "
        "(scripts/generate_data/gen_cultural.py). Apache-2.0."
    )
