"""Translation task: Persian <-> English sentence pairs."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec

_JUDGE_PROMPT = """تو داور حرفه‌ای ترجمهٔ فارسی-انگلیسی هستی.
ترجمهٔ مرجع: {expected}
ترجمهٔ مدل: {response}

معیارها: وفاداری کامل به معنا (بدون افزودن یا حذف اطلاعات)، روانی و طبیعی‌بودن در زبان مقصد، حفظ لحن جمله.
خطای معنایی یا ترجمهٔ تحت‌اللفظی ناتمام امتیاز را به‌شدت کم می‌کند؛ تفاوت‌های سبکی جزئی مهم نیست.
فقط یک شیء JSON برگردان: {{"score": عدد بین 0 و 1, "rationale": توضیح کوتاه}}"""


class TranslationFaEnTask(AbstractTask):
    """Translate everyday, proverb and news sentences between FA and EN.

    Judge-scored against an expert reference translation, so partial
    credit reflects real translation quality instead of string equality.
    """

    name = "translation_fa_en"
    title_en = "Translation FA<->EN"
    title_fa = "ترجمهٔ فارسی-انگلیسی"
    description_en = (
        "Bidirectional FA<->EN translation of everyday, proverbial and "
        "news-register sentences; LLM-judge scored against references."
    )
    description_fa = (
        "ترجمهٔ دوسویهٔ جملات روزمره، ضرب‌المثل و خبری میان فارسی و انگلیسی؛ "
        "ارزیابی با داور مدل‌زبانی نسبت به ترجمهٔ مرجع."
    )
    data_file = "translation_fa_en.jsonl"
    min_samples = 200
    system_prompt = "فقط ترجمه را بنویس؛ هیچ توضیح، گیومه یا علامت اضافه‌ای ننویس."
    scoring = ScoringSpec(kind=ScoringKind.JUDGE, judge_prompt=_JUDGE_PROMPT, score_pass_threshold=0.75)
    source = (
        "Expert-authored sentence pairs in four registers "
        "(scripts/generate_data/gen_translation.py); a FLORES-200 subset is "
        "planned for v0.2. Apache-2.0."
    )
