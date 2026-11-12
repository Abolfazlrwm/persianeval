"""Generate the spelling task: 200 Persian orthography / encoding items.

Four item types: Arab-script homoglyph detection, homoglyph choice,
sentence correction and half-space (ZWNJ) usage. All corruption is applied
systematically over a curated pool, so every expected answer is known.
"""

from __future__ import annotations

import random
from typing import Any

from scripts.generate_data.common import write_jsonl

#: Words vulnerable to Arabic ي/ك homoglyph confusion: (word) -> arabized form.
HOMOGLYPH_WORDS = [
    "یک",
    "کتاب",
    "کلید",
    "یار",
    "ایران",
    "کوه",
    "کار",
    "کبوتر",
    "یاد",
    "کام",
    "کامل",
    "کرم",
    "کیف",
    "سال",
    "کاشی",
    "یخ",
    "کلام",
    "یکان",
    "کلان",
    "کیوان",
    "کارگاه",
    "یافتن",
    "کنار",
    "کاشان",
    "یلدا",
    "کاشانه",
    "یارانه",
    "کبوترخانه",
    "کلیدها",
    "کتابخانه",
    "یادگار",
    "کارخانه",
    "کوشش",
    "یکنواخت",
    "کاردانی",
    "یکنفره",
    "کالبد",
    "یاور",
    "کدبانو",
    "یاغی",
    "کبوتر",
    "کیلومتر",
    "یال",
    "کارنامه",
    "کانون",
    "یقه",
    "کاسه",
    "کرم",
    "یخچال",
    "کویر",
    "کاوه",
    "یغما",
    "کلان‌شهر",
    "کیفیت",
    "کمان",
    "یاری",
    "کاکتوس",
    "یکدست",
    "کوزه",
    "یخبندان",
]

#: Clean sentences used for yes/no homoglyph detection.
CLEAN_SENTENCES = [
    "ایران کشوری با تاریخ کهن است.",
    "کتاب‌های من روی میز کار قرار دارند.",
    "کوه دماوند در شمال کشور قرار دارد.",
    "یکی از بهترین دوستان من اهل تبریز است.",
    "کلید خانه را گم کرده بودم.",
    "کاشی‌کاری‌های اصفهان مشهور جهان‌اند.",
    "سال نو را با شادی آغاز کردیم.",
    "یادگیری زبان فارسی لذت‌بخش است.",
    "کارگران امروز پروژه را تمام کردند.",
    "کبوترهای روی پشت‌بام پرواز کردند.",
    "کیف چرمی جدیدی از بازار گرفتم.",
    "شب یلدا با خانواده کنار هم بودیم.",
    "کوهنوردان قله سبلان را فتح کردند.",
    "یک لیوان چای داغ لطف بزرگی است.",
    "کاوشگران آثار باستانی را یافتند.",
    "کرم‌های ابریشم در لاهیجان پرورش می‌یابند.",
    "یاور همیشگی‌ام در سختی‌ها خانواده‌ام است.",
    "کلاس‌های زبان در دانشگاه برقرار است.",
    "یادگاری‌های سفر را نگه می‌دارم.",
    "کارنامه تحصیلی‌اش عالی بود.",
    "کلان‌شهر تهران ترافیک سنگینی دارد.",
    "کیفیت هوای امروز مناسب بود.",
    "یکدستی کلمات فارسی اهمیت دارد.",
    "کوزه‌های سفالی در گلخانه چیده شده‌اند.",
    "یخچال را با دقت تمیز کردم.",
    "کمانگیران در جنگ‌های باستان مهارت داشتند.",
    "کاسه‌های سرامیک در بازار عرضه شد.",
    "یغمای جعفرزاده شاعر معاصر گیلان است.",
    "کاروان تجارت از جاده ابریشم می‌گذشت.",
    "یکنواختی بیابان با چشمه‌ای شکسته می‌شد.",
]

#: Compound words and verb forms requiring a zero-width non-joiner.
ZWNJ_PAIRS = [
    "می‌روم",
    "می‌گویم",
    "نمی‌دانم",
    "نمی‌روم",
    "می‌خواهم",
    "می‌کنیم",
    "می‌بینم",
    "نمی‌شود",
    "می‌آید",
    "نمی‌توانم",
    "بی‌کار",
    "بی‌رحمانه",
    "هم‌کار",
    "هم‌کلاسی",
    "هم‌سایه",
    "نیم‌روز",
    "نیم‌ساعت",
    "بین‌المللی",
    "کتاب‌ها",
    "خانه‌ها",
    "بچه‌ها",
    "درخت‌ها",
    "مدادها",
    "پنجره‌ها",
    "گل‌ها",
    "چشم‌ها",
    "سخن‌ها",
    "دیوارها",
    "می‌پرسد",
    "می‌نویسد",
    "نمی‌خندد",
    "می‌خندد",
    "بی‌نظیر",
    "هم‌راه",
    "نیم‌کره",
    "بین‌راهی",
    "کتاب‌فروشی",
    "خانه‌سازی",
    "می‌رسد",
    "نمی‌رسد",
]

SENTENCE_TEMPLATES = [
    "دیروز من یک {word} جدید خریدم.",
    "او {word} خود را گم کرده است.",
    "این {word} را از بازار تهیه کن.",
]


def to_arabic_script(text: str) -> str:
    """Corrupt Persian yeh/kaf into their Arabic homoglyphs."""
    return text.replace("ی", "ي").replace("ک", "ك")


def main() -> None:
    """Generate exactly 200 spelling samples in four families."""
    rng = random.Random(42)
    rows: list[dict[str, Any]] = []

    # Family 1 (58): choose the standard spelling between two homoglyph variants.
    words = list(dict.fromkeys(HOMOGLYPH_WORDS))  # pool contains 2 historical dups
    for position, word in enumerate(words):
        corrupted = to_arabic_script(word)
        first_is_correct = position % 2 == 0
        option_a = word if first_is_correct else corrupted
        option_b = corrupted if first_is_correct else word
        rows.append(
            {
                "id": f"spelling-{len(rows) + 1:04d}",
                "prompt": (
                    "کدام نگارش با معیارهای رسمی زبان فارسی درست است؟ "
                    f"فقط همان کلمهٔ درست را بنویس.\nالف) {option_a}\nب) {option_b}"
                ),
                "expected": word,
                "metadata": {"family": "homoglyph_choice", "error": "yeh_kaf"},
            }
        )

    # Family 2 (60): detect Arabic-script remnants in sentences (yes/no).
    for position, sentence in enumerate(CLEAN_SENTENCES[:30] * 2):
        is_corrupted = position >= 30
        text = to_arabic_script(sentence) if is_corrupted else sentence
        rows.append(
            {
                "id": f"spelling-{len(rows) + 1:04d}",
                "prompt": (
                    "آیا در عبارت زیر هم‌گردانی (استفاده از حروف عربی «ي/ك» به‌جای «ی/ک») "
                    "وجود دارد؟ فقط «بله» یا «خیر» بنویس.\nعبارت: «" + text + "»"
                ),
                "expected": "بله" if is_corrupted else "خیر",
                "metadata": {"family": "homoglyph_detect", "error": "yeh_kaf"},
            }
        )

    # Family 3 (50): correct a sentence containing one corrupted word.
    # (i*7) mod len(combos) is injective for i in 0..49 (gcd(7, len)=1), so all
    # 50 (template, word) pairs are distinct and prompts cannot collide.
    combos = [(t, w) for t in range(len(SENTENCE_TEMPLATES)) for w in words]
    for position in range(50):
        template_index, word = combos[(position * 7) % len(combos)]
        template = SENTENCE_TEMPLATES[template_index]
        corrupted_sentence = template.format(word=to_arabic_script(word))
        expected_sentence = template.format(word=word)
        rows.append(
            {
                "id": f"spelling-{len(rows) + 1:04d}",
                "prompt": (
                    "در جملهٔ زیر خطای هم‌گردانی وجود دارد. آن را اصلاح کن و فقط "
                    "جملهٔ درست را بنویس.\nجمله: «" + corrupted_sentence + "»"
                ),
                "expected": expected_sentence,
                "metadata": {"family": "sentence_fix", "error": "yeh_kaf", "word": word},
            }
        )

    # Family 4 (32): choose between missing and correct half-space (ZWNJ).
    sampled = rng.sample(ZWNJ_PAIRS, k=32)
    for position, word in enumerate(sampled):
        joined = word.replace("\u200c", "")
        first_is_correct = position % 2 == 0
        option_a = word if first_is_correct else joined
        option_b = joined if first_is_correct else word
        rows.append(
            {
                "id": f"spelling-{len(rows) + 1:04d}",
                "prompt": (
                    "کدام نگارش مطابق دستور خطّ فارسی (موضوع: نیم‌فاصله) درست است؟ "
                    f"فقط همان کلمهٔ درست را بنویس.\nالف) {option_a}\nب) {option_b}"
                ),
                "expected": word,
                "metadata": {"family": "zwnj_choice", "error": "zwnj"},
            }
        )

    assert len(rows) == 200, f"expected 200 rows, got {len(rows)}"
    assert len({row["id"] for row in rows}) == 200, "ids must be unique"
    assert len({row["prompt"] for row in rows}) == 200, "prompts must be unique"
    write_jsonl("spelling", rows)


if __name__ == "__main__":
    main()
