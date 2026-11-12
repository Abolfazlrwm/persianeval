"""Reasoning task: Persian multi-step arithmetic and logic problems."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec


class ReasoningTask(AbstractTask):
    """Multi-step arithmetic word problems and logic puzzles in Persian.

    Modeled after GSM8K but nativized: Iranian contexts (bazaar, taxi,
    discounts in tomans, Iranian names) plus native logic items. Answers
    are exact numbers or person names, so scoring is deterministic.
    """

    name = "reasoning"
    title_en = "Reasoning (FA)"
    title_fa = "استدلال و حل مسئله"
    description_en = (
        "Multi-step arithmetic word problems and logic puzzles in Persian "
        "(GSM8K-style, nativized); exact numeric or nominal answers."
    )
    description_fa = (
        "مسئله‌های چندمرحله‌ای ریاضی و منطقی به فارسی (به سبک GSM8K و بومی‌سازی‌شده)؛ "
        "پاسخ‌ها دقیقاً عددی یا نامی هستند."
    )
    data_file = "reasoning.jsonl"
    min_samples = 200
    system_prompt = (
        "تو یک حل‌کننده دقیق مسئله هستی. مسئله را گام‌به‌گام حل کن و در پایان "
        "فقط عدد یا نام نهایی را به‌صورت ارقام فارسی بنویس."
    )
    exact_strip_tokens = (
        "تومان",
        "ریال",
        "نفر",
        "ساعت",
        "کیلومتر",
        "روز",
        "سال",
        "درصد",
        "عدد",
        "جواب",
        "پاسخ",
    )
    scoring = ScoringSpec(kind=ScoringKind.EXACT)
    source = (
        "Created programmatically by scripts/generate_data/gen_reasoning.py with "
        "verified-by-construction answers; 7 problem families. Apache-2.0."
    )
