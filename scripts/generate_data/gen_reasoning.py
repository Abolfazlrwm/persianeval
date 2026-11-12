"""Generate the reasoning task: 200 verified multi-step Persian problems.

Seven problem families; every expected answer is computed by this script,
so the dataset is correct by construction. Deterministic: seeded RNG.
"""

from __future__ import annotations

import random
from typing import Any

from scripts.generate_data.common import fa_num, write_jsonl

NAMES = ["علی", "مریم", "رضا", "سارا", "حسین", "نگار", "امیر", "الهام", "بهنام", "پریسا"]
ITEMS = [
    ("دفتر", 8_000, 15_000, 1_000, 1, 6),
    ("خودکار", 3_000, 7_000, 500, 1, 6),
    ("مداد", 2_000, 6_000, 500, 1, 6),
    ("کتاب", 20_000, 60_000, 5_000, 1, 3),
    ("کیف", 40_000, 90_000, 5_000, 1, 3),
    ("جامدادی", 15_000, 30_000, 1_000, 1, 4),
]
CITIES = ["تبریز", "شیراز", "اصفهان", "مشهد", "رشت", "کرمان", "اهواز", "یزد"]


def pick_price(rng: random.Random, low: int, high: int, step: int) -> int:
    """Pick a price on the allowed grid."""
    steps = (high - low) // step
    return low + step * rng.randrange(0, steps + 1)


def family_shopping(rng: random.Random, index: int) -> dict[str, Any]:
    """Two- or three-item shopping total with an exact tomans answer."""
    name, city = rng.choice(NAMES), rng.choice(CITIES)
    chosen = rng.sample(ITEMS, k=3)
    parts: list[str] = []
    total = 0
    item_count = 3 if index % 4 == 0 else 2
    for item_name, low, high, step, lo_c, hi_c in chosen[:item_count]:
        count = rng.randint(lo_c, hi_c)
        price = pick_price(rng, low, high, step)
        total += count * price
        parts.append(f"{fa_num(count)} {item_name} {fa_num(price)} تومانی")
    prompt = f"{name} در فروشگاهِ شهر {city} {' و '.join(parts)} می‌خرد. او چند تومان باید بپردازد؟"
    detail = "مجموع هزینه‌ها = " + fa_num(total)
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(total),
        "metadata": {"family": "shopping", "solution": detail},
    }


def family_travel(rng: random.Random, index: int) -> dict[str, Any]:
    """Speed / distance / time with integer hours (optionally two legs)."""
    name = rng.choice(NAMES)
    speed = rng.choice([40, 50, 60, 70, 80, 90])
    hours = rng.randint(2, 8)
    distance = speed * hours
    if index % 2 == 0:
        prompt = (
            f"اتوبوسی با سرعت متوسط {fa_num(speed)} کیلومتر بر ساعت مسیر {fa_num(distance)} "
            f"کیلومتری {name} را طی می‌کند. این سفر چند ساعت طول می‌کشد؟"
        )
        solution = f"{fa_num(distance)} ÷ {fa_num(speed)} = {fa_num(hours)}"
        expected = hours
    else:
        other_speed = rng.choice([s for s in [40, 50, 60, 80, 90] if s != speed])
        half = distance // 2
        if half % other_speed != 0:
            distance = speed * other_speed * 2 * hours
            half = distance // 2
        total_time = half // speed + half // other_speed
        prompt = (
            f"قطاری نیمهٔ اولِ مسیر {fa_num(distance)} کیلومتری را با سرعت {fa_num(speed)} و "
            f"نیمهٔ دوم را با سرعت {fa_num(other_speed)} کیلومتر بر ساعت می‌رود. "
            f"کل سفر چند ساعت طول می‌کشد؟"
        )
        solution = (
            f"نیمی از مسیر = {fa_num(half)}؛ زمان = {fa_num(half)}÷{fa_num(speed)} + "
            f"{fa_num(half)}÷{fa_num(other_speed)} = {fa_num(total_time)}"
        )
        expected = total_time
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(expected),
        "metadata": {"family": "travel", "solution": solution},
    }


def family_discount(rng: random.Random, index: int) -> dict[str, Any]:
    """Discount or VAT computation on a tomans price."""
    item = rng.choice(["پیراهن", "کفش", "کت", "توپ", "کوله‌پشتی"])
    price = 50_000 * rng.randint(4, 16)
    if index % 2 == 0:
        percent = rng.choice([10, 15, 20, 25, 30])
        final = price * (100 - percent) // 100
        prompt = (
            f"قیمت {item}ی {fa_num(price)} تومانی است. فروشگاه {fa_num(percent)} درصد تخفیف می‌دهد. "
            f"قیمت پس از تخفیف چند تومان می‌شود؟"
        )
        solution = f"{fa_num(price)} × {fa_num(100 - percent)}٪ = {fa_num(final)}"
    else:
        percent = 9
        final = price * 109 // 100
        prompt = (
            f"قیمت {item}ی {fa_num(price)} تومانی است. با افزودن {fa_num(percent)} درصد "
            f"مالیات بر ارزش افزوده، مبلغ نهایی چند تومان می‌شود؟"
        )
        solution = f"{fa_num(price)} × ۱۰۹٪ = {fa_num(final)}"
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(final),
        "metadata": {"family": "discount", "solution": solution},
    }


def family_age(rng: random.Random, index: int) -> dict[str, Any]:
    """Father/son age relations with integer solutions."""
    while True:
        father = rng.randint(30, 60)
        son = rng.randint(4, 25)
        k = rng.choice([2, 3])
        future = rng.random() < 0.5
        x = (father - k * son) / (k - 1) if future else (k * son - father) / (k - 1)
        if x.is_integer() and 0 < x <= 60 and father - son >= 18:
            years = int(x)
            if future:
                prompt = (
                    f"امسال سن پدر {fa_num(father)} و سن پسرش {fa_num(son)} سال است. "
                    f"چند سال دیگر سن پدر {fa_num(k)} برابر سن پسر می‌شود؟"
                )
                solution = f"{fa_num(father)} + x = {fa_num(k)}({fa_num(son)} + x) → x = {fa_num(years)}"
            else:
                prompt = (
                    f"امسال سن پدر {fa_num(father)} و سن پسرش {fa_num(son)} سال است. "
                    f"چند سال پیش سن پدر {fa_num(k)} برابر سن پسر بود؟"
                )
                solution = f"{fa_num(father)} - x = {fa_num(k)}({fa_num(son)} - x) → x = {fa_num(years)}"
            break
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(years),
        "metadata": {"family": "age", "solution": solution},
    }


def family_sequence(rng: random.Random, index: int) -> dict[str, Any]:
    """Arithmetic, geometric, Fibonacci-like or alternating sequences."""
    kind = ["arithmetic", "geometric", "fibonacci", "alternating"][index % 4]
    if kind == "arithmetic":
        a, d = rng.randint(3, 40), rng.randint(3, 12)
        terms = [a + d * i for i in range(6)]
        rule = f"هر جمله {fa_num(d)} واحد بیشتر از جملهٔ قبل"
    elif kind == "geometric":
        a, r = rng.randint(2, 9), rng.choice([2, 3, 4, 5])
        terms = [a * r**i for i in range(6)]
        rule = f"هر جمله در {fa_num(r)} ضرب می‌شود"
    elif kind == "fibonacci":
        a, b = rng.randint(1, 6), rng.randint(2, 8)
        terms = [a, b]
        for _ in range(4):
            terms.append(terms[-1] + terms[-2])
        rule = "هر جمله مجموع دو جملهٔ قبل"
    else:
        a, up, down = rng.randint(20, 60), rng.randint(6, 15), rng.randint(2, 7)
        terms = [a]
        for i in range(5):
            terms.append(terms[-1] + (up if i % 2 == 0 else -down))
        rule = f"جمله‌ها یکی درمیان {fa_num(up)} واحد زیاد و {fa_num(down)} واحد کم می‌شوند"
    shown = [fa_num(t) for t in terms[:5]]
    prompt = (
        f"الگوی دنبالهٔ زیر را پیدا کن و جملهٔ ششم را بنویس:\n"
        f"{shown[0]}، {shown[1]}، {shown[2]}، {shown[3]}، {shown[4]}، ...؟"
    )
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(terms[5]),
        "metadata": {"family": "sequence", "kind": kind, "solution": rule},
    }


def family_ordering(rng: random.Random, index: int) -> dict[str, Any]:
    """Height ordering chain; answer is a person's name."""
    count = 3 if index % 3 == 0 else 4
    people = rng.sample(NAMES, k=count)
    order = people[:]
    rng.shuffle(order)  # order[0] is the tallest
    statements = [f"{order[i]} بلندتر از {order[i + 1]} است" for i in range(count - 1)]
    ask = ["بلندترین", "کوتاه‌ترین", "دومین نفر از نظر قد"][index % 3]
    expected = {0: order[0], 1: order[-1], 2: order[1]}[index % 3]
    prompt = f"{'؛ '.join(statements)}.\nبر اساس این گفته‌ها، {ask} کدام است؟ فقط نام او را بنویس."
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": expected,
        "metadata": {"family": "ordering", "solution": " > ".join(order)},
    }


def family_work(rng: random.Random, index: int) -> dict[str, Any]:
    """Worker-days problems with integer answers."""
    days = rng.choice([6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 24])
    workers = rng.choice([2, 3, 4])
    if days % workers != 0:
        days = workers * rng.randint(3, 8)
    result = days // workers
    if index % 2 == 0:
        prompt = (
            f"اگر یک کارگر انجام یک کار ساختمانی را در {fa_num(days)} روز تمام کند، "
            f"{fa_num(workers)} کارگرِ هم‌سطح و هم‌سرعت، همان کار را در چند روز تمام می‌کنند؟"
        )
    else:
        prompt = (
            f"{fa_num(workers)} کارگرِ هم‌سطح، یک کار را در {fa_num(result)} روز تمام می‌کنند. "
            f"یک کارگر به‌تنهایی همان کار را در چند روز تمام می‌کند؟"
        )
        days, result = result, days
    return {
        "id": f"reasoning-{index:04d}",
        "prompt": prompt,
        "expected": fa_num(result),
        "metadata": {"family": "work", "solution": "روزها بر تعداد کارگرها تقسیم می‌شود (نسبت معکوس)"},
    }


def main() -> None:
    """Generate exactly 200 reasoning samples across the seven families."""
    rng = random.Random(42)
    generators = [
        (family_shopping, 40),
        (family_travel, 30),
        (family_discount, 30),
        (family_age, 25),
        (family_sequence, 35),
        (family_ordering, 25),
        (family_work, 15),
    ]
    rows: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()
    for generator, count in generators:
        attempts, added = 0, 0
        while added < count:
            attempts += 1
            if attempts > count * 200:
                msg = f"could not reach {count} unique prompts for {generator.__name__}"
                raise RuntimeError(msg)
            candidate = generator(rng, len(rows) + 1)
            if candidate["prompt"] in seen_prompts:
                continue  # small parameter spaces can collide; redraw deterministically
            seen_prompts.add(candidate["prompt"])
            rows.append(candidate)
            added += 1
    assert len(rows) == 200, f"expected 200 rows, got {len(rows)}"
    assert len({row["id"] for row in rows}) == 200, "ids must be unique"
    assert len({row["prompt"] for row in rows}) == 200, "prompts must be unique"
    write_jsonl("reasoning", rows)


if __name__ == "__main__":
    main()
