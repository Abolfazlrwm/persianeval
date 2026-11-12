"""Generate the code-with-Persian-comments task: 200 items over 15 families.

Each item provides a Python signature, Persian docstring/comments and
hidden test cases whose outputs are computed by running the reference
implementation inside this generator (correct by construction).

Every family is parameterized by a ``variant`` index; a ``random.Random``
seeded with the stable string ``"<family>:<variant>"`` derives deterministic
per-variant test inputs, so all 200 prompts are unique while staying
reproducible across processes and Python versions.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from scripts.generate_data.common import write_jsonl

FAMILY_WEIGHTS: dict[str, int] = {
    "sum_list": 14,
    "reverse_string": 13,
    "count_char": 13,
    "max_without_builtin": 13,
    "fibonacci": 14,
    "is_palindrome": 13,
    "celsius_to_fahrenheit": 13,
    "gcd": 13,
    "count_words": 13,
    "flatten_one_level": 14,
    "unique_sorted": 13,
    "factorial": 13,
    "is_leap_year": 13,
    "second_largest": 14,
    "power_without_operator": 14,
}

_FA_WORDS = [
    "سلام",
    "دنیا",
    "کتاب",
    "باران",
    "دریا",
    "کوه",
    "ستاره",
    "پنجره",
    "مهتاب",
    "کویر",
    "شمشاد",
    "بهار",
]
_FA_CHARS = ["ب", "ن", "ش", "ا", "ر"]
_PALINDROME_POOL = [
    "کوک",
    "حباب",
    "سعادت",
    "درد",
    "شوش",
    "داد",
    "راز",
    "لبخند",
    "گاه",
    "مهر",
    "نیل",
    "کبریت",
]


def repr_args(args: list[Any]) -> str:
    """Render a Python argument list for the judge prompt."""
    return "(" + ", ".join(repr(arg) for arg in args) + ")"


def family_sum_list(variant: int) -> dict[str, Any]:
    """Sum a list of integers without sum()."""
    rng = random.Random(f"sum_list:{variant}")
    cases = [
        [variant],
        rng.sample(range(-99, 100), 5),
        [rng.randint(0, 500) for _ in range(3)],
        [],
    ]
    solution = "    total = 0\n    for value in numbers:\n        total += value\n    return total"
    return {
        "name": "sum_list",
        "signature": "def sum_list(numbers: list[int]) -> int:",
        "doc": "مجموع همهٔ عددهای لیست را برمی‌گرداند. برای لیست خالی صفر برمی‌گرداند.",
        "tests": [(case, sum(case)) for case in cases],
        "solution": f"def sum_list(numbers: list[int]) -> int:\n{solution}",
    }


def family_reverse_string(variant: int) -> dict[str, Any]:
    """Reverse a string without slicing shortcuts."""
    rng = random.Random(f"reverse_string:{variant}")
    cases = [*rng.sample(_FA_WORDS, 4), "", f"v{variant}x", rng.choice(_FA_CHARS)]
    solution = "    result = ''\n    for char in text:\n        result = char + result\n    return result"
    return {
        "name": "reverse_string",
        "signature": "def reverse_string(text: str) -> str:",
        "doc": "معکوس رشتهٔ ورودی را برمی‌گرداند.",
        "tests": [([case], case[::-1]) for case in cases],
        "solution": f"def reverse_string(text: str) -> str:\n{solution}",
    }


def family_count_char(variant: int) -> dict[str, Any]:
    """Count occurrences of a character."""
    rng = random.Random(f"count_char:{variant}")
    word = rng.choice(_FA_WORDS)
    cases = [
        ("گل" * (variant + 1), "ل"),
        (word, rng.choice(word)),
        ("", "ا"),
        (rng.choice(_FA_WORDS), rng.choice(_FA_CHARS)),
    ]
    solution = "    count = 0\n    for char in text:\n"
    solution += "        if char == target:\n            count += 1\n    return count"
    return {
        "name": "count_char",
        "signature": "def count_char(text: str, target: str) -> int:",
        "doc": "تعداد تکرار کاراکتر target در متن را می‌شمارد (حساس به بزرگی و کوچکی).",
        "tests": [(list(case), case[0].count(case[1])) for case in cases],
        "solution": f"def count_char(text: str, target: str) -> int:\n{solution}",
    }


def family_max_without_builtin(variant: int) -> dict[str, Any]:
    """Find the maximum of a list without max()."""
    rng = random.Random(f"max_without_builtin:{variant}")
    cases = [
        [variant + 1000, variant, -variant - 1000],
        rng.sample(range(-50, 51), rng.randint(2, 5)),
        [rng.randint(-99, 99) for _ in range(4)],
    ]
    solution = "    largest = numbers[0]\n    for value in numbers[1:]:\n"
    solution += "        if value > largest:\n            largest = value\n    return largest"
    return {
        "name": "max_without_builtin",
        "signature": "def max_without_builtin(numbers: list[int]) -> int:",
        "doc": "بزرگ‌ترین عدد لیست را بدون استفاده از تابع max برمی‌گرداند. لیست همیشه ناخالی است.",
        "tests": [(case, max(case)) for case in cases],
        "solution": f"def max_without_builtin(numbers: list[int]) -> int:\n{solution}",
    }


def family_fibonacci(variant: int) -> dict[str, Any]:
    """Iterative Fibonacci."""
    rng = random.Random(f"fibonacci:{variant}")
    cases = [variant + 15, *rng.sample(range(1, 15), 3)]

    def fib(n: int) -> int:
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return a

    solution = "    a, b = 1, 1\n    for _ in range(n - 1):\n        a, b = b, a + b\n    return a"
    return {
        "name": "fibonacci",
        "signature": "def fibonacci(n: int) -> int:",
        "doc": "عدد nاُم دنبالهٔ فیبوناچی را با شروع از ۱ و ۱ برمی‌گرداند. n همیشه حداقل ۱ است.",
        "tests": [([n], fib(n)) for n in cases],
        "solution": f"def fibonacci(n: int) -> int:\n{solution}",
        "check": {n: fib(n) for n in cases},
    }


def family_is_palindrome(variant: int) -> dict[str, Any]:
    """Palindrome check."""
    rng = random.Random(f"is_palindrome:{variant}")
    cases = [f"ک{'ا' * variant}ک", *rng.sample(_PALINDROME_POOL, 4), "", "ب"]
    solution = "    return text == text[::-1]"
    return {
        "name": "is_palindrome",
        "signature": "def is_palindrome(text: str) -> bool:",
        "doc": "بررسی می‌کند که آیا متن، قلب‌القول (پالیندروم) است یا نه.",
        "tests": [([case], case == case[::-1]) for case in cases],
        "solution": f"def is_palindrome(text: str) -> bool:\n{solution}",
    }


def family_celsius_to_fahrenheit(variant: int) -> dict[str, Any]:
    """Temperature conversion."""
    rng = random.Random(f"celsius_to_fahrenheit:{variant}")
    hot, cold = round(rng.uniform(-40.0, 120.0), 1), round(rng.uniform(-40.0, 120.0), 1)
    cases = [variant + 20.5, hot, cold, 0.0, 100.0]
    solution = "    return celsius * 9 / 5 + 32"
    return {
        "name": "celsius_to_fahrenheit",
        "signature": "def celsius_to_fahrenheit(celsius: float) -> float:",
        "doc": "دما را از سلسیوس به فارنهایت تبدیل می‌کند.",
        "tests": [([c], round(c * 9 / 5 + 32, 2)) for c in cases],
        "solution": f"def celsius_to_fahrenheit(celsius: float) -> float:\n{solution}",
    }


def family_gcd(variant: int) -> dict[str, Any]:
    """Euclidean GCD."""
    rng = random.Random(f"gcd:{variant}")
    cases = [
        (variant * 100 + 3, variant * 100 + 7),
        (12, 18),
        (rng.randint(2, 60), rng.randint(2, 60)),
        (9, 9),
        (rng.randint(2, 60), rng.randint(2, 60)),
    ]

    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    solution = "    while b:\n        a, b = b, a % b\n    return a"
    return {
        "name": "gcd",
        "signature": "def gcd(a: int, b: int) -> int:",
        "doc": "بزرگ‌ترین مقسوم‌علیه مشترک دو عدد را با الگوریتم اقلیدسی برمی‌گرداند.",
        "tests": [(list(case), gcd(*case)) for case in cases],
        "solution": f"def gcd(a: int, b: int) -> int:\n{solution}",
    }


def family_count_words(variant: int) -> dict[str, Any]:
    """Count words in a sentence."""
    rng = random.Random(f"count_words:{variant}")
    cases = [
        " ".join(["سطر"] * (variant + 1)) + " پایان",
        " ".join(rng.sample(_FA_WORDS, rng.randint(1, 5))),
        "کتاب   کهن   امروزی",
        "",
    ]
    solution = "    return len(sentence.split())"
    return {
        "name": "count_words",
        "signature": "def count_words(sentence: str) -> int:",
        "doc": "تعداد کلمه‌های جمله را برمی‌گرداند (کلمه‌ها با فاصله جدا شده‌اند).",
        "tests": [([case], len(case.split())) for case in cases],
        "solution": f"def count_words(sentence: str) -> int:\n{solution}",
    }


def family_flatten_one_level(variant: int) -> dict[str, Any]:
    """Flatten a list of lists one level deep."""
    rng = random.Random(f"flatten_one_level:{variant}")
    cases = [
        [[variant], [variant + 1, variant + 2]],
        [rng.sample(range(0, 20), rng.randint(0, 4)) for _ in range(3)],
        [],
    ]
    solution = "    result = []\n    for inner in nested:\n        result.extend(inner)\n    return result"
    return {
        "name": "flatten_one_level",
        "signature": "def flatten_one_level(nested: list[list[int]]) -> list[int]:",
        "doc": "لیستی از لیست‌ها را فقط یک سطح صاف می‌کند.",
        "tests": [(case, [item for inner in case for item in inner]) for case in cases],
        "solution": f"def flatten_one_level(nested: list[list[int]]) -> list[int]:\n{solution}",
    }


def family_unique_sorted(variant: int) -> dict[str, Any]:
    """Deduplicate and sort."""
    rng = random.Random(f"unique_sorted:{variant}")
    cases = [
        [variant, -variant, variant],
        rng.choices(range(-9, 10), k=6),
        rng.sample(range(0, 30), 4),
        [],
    ]
    solution = "    return sorted(set(values))"
    return {
        "name": "unique_sorted",
        "signature": "def unique_sorted(values: list[int]) -> list[int]:",
        "doc": "تکرارها را حذف و نتیجه را به‌صورت صعودی مرتب برمی‌گرداند.",
        "tests": [(case, sorted(set(case))) for case in cases],
        "solution": f"def unique_sorted(values: list[int]) -> list[int]:\n{solution}",
    }


def family_factorial(variant: int) -> dict[str, Any]:
    """Iterative factorial."""
    rng = random.Random(f"factorial:{variant}")
    cases = [variant + 10, *rng.sample(range(0, 10), 2), 0]
    solution = "    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result"
    return {
        "name": "factorial",
        "signature": "def factorial(n: int) -> int:",
        "doc": "فاکتوریل n را به‌صورت حلقه‌ای حساب می‌کند (n >= 0).",
        "tests": [([n], __import__("math").factorial(n)) for n in cases],
        "solution": f"def factorial(n: int) -> int:\n{solution}",
    }


def family_is_leap_year(variant: int) -> dict[str, Any]:
    """Gregorian leap year."""
    rng = random.Random(f"is_leap_year:{variant}")
    cases = [2000 + variant, *rng.sample(range(1800, 1900), 3), 1900, 2024]

    def is_leap(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    solution = "    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)"
    return {
        "name": "is_leap_year",
        "signature": "def is_leap_year(year: int) -> bool:",
        "doc": "بررسی می‌کند که آیا سال میلادی، سال کبیسه است یا نه.",
        "tests": [([year], is_leap(year)) for year in cases],
        "solution": f"def is_leap_year(year: int) -> bool:\n{solution}",
    }


def family_second_largest(variant: int) -> dict[str, Any]:
    """Second-largest distinct element."""
    rng = random.Random(f"second_largest:{variant}")
    cases = [
        [variant],
        [rng.randint(1, 4)] * 3,
        rng.choices(range(-9, 10), k=4),
        rng.sample(range(-9, 10), 4),
        [7],
    ]
    solution = (
        "    distinct = sorted(set(values), reverse=True)\n"
        "    if len(distinct) < 2:\n"
        "        return None\n"
        "    return distinct[1]"
    )
    return {
        "name": "second_largest",
        "signature": "def second_largest(values: list[int]) -> int | None:",
        "doc": "دومین عدد بزرگِ متمایز لیست را برمی‌گرداند؛ اگر وجود نداشت None برمی‌گرداند.",
        "tests": [
            ([case], sorted(set(case), reverse=True)[1] if len(set(case)) >= 2 else None) for case in cases
        ],
        "solution": f"def second_largest(values: list[int]) -> int | None:\n{solution}",
    }


def family_power_without_operator(variant: int) -> dict[str, Any]:
    """Integer power without the ** operator; exponent >= 0."""
    rng = random.Random(f"power_without_operator:{variant}")
    cases = [
        (variant + 50, variant % 4),
        (rng.randint(-6, 6), rng.randint(0, 5)),
        (2, 5),
        (rng.randint(-6, 6), rng.randint(0, 5)),
        (5, 0),
    ]

    def power(base: int, exponent: int) -> int:
        result = 1
        for _ in range(exponent):
            result *= base
        return result

    solution = "    result = 1\n    for _ in range(exponent):\n        result *= base\n    return result"
    return {
        "name": "power_without_operator",
        "signature": "def power_without_operator(base: int, exponent: int) -> int:",
        "doc": "توان عدد صحیح را بدون استفاده از عملگر ** حساب می‌کند. توان همیشه بزرگ‌تر یا مساوی صفر است.",
        "tests": [(list(case), power(*case)) for case in cases],
        "solution": f"def power_without_operator(base: int, exponent: int) -> int:\n{solution}",
    }


FAMILIES: list[Callable[[int], dict[str, Any]]] = [
    family_sum_list,
    family_reverse_string,
    family_count_char,
    family_max_without_builtin,
    family_fibonacci,
    family_is_palindrome,
    family_celsius_to_fahrenheit,
    family_gcd,
    family_count_words,
    family_flatten_one_level,
    family_unique_sorted,
    family_factorial,
    family_is_leap_year,
    family_second_largest,
    family_power_without_operator,
]


def build_prompt(item: dict[str, Any]) -> str:
    """Compose the full exercise prompt from the family template."""
    tests_rendered = "\n".join(f"# {repr_args(args)} -> {expected!r}" for args, expected in item["tests"])
    return (
        f"تابع زیر را طوری کامل کن که کامنت‌های فارسی و امضای تابع حفظ شود:\n\n"
        f"{item['signature']}\n"
        f'    """{item["doc"]}"""\n'
        f"    # پیاده‌سازی شما\n\n"
        f"تست‌های مورد انتظار:\n{tests_rendered}\n\n"
        "فقط کد پایتون تابع را بنویس (امضا + بدنه) و از هیچ توابع داخلی ممنوعِ صورت تمرین استفاده نکن."
    )


def main() -> None:
    """Generate exactly 200 code-completion samples."""
    rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        weight = FAMILY_WEIGHTS[family.__name__.removeprefix("family_")]
        for variant in range(weight):
            item = family(variant)
            rows.append(
                {
                    "id": f"code_with_persian_comments-{len(rows) + 1:04d}",
                    "prompt": build_prompt(item),
                    "expected": item["solution"],
                    "metadata": {
                        "family": item["name"],
                        "signature": item["signature"],
                        "tests": [[args, expected] for args, expected in item["tests"]],
                    },
                }
            )
    assert len(rows) == 200, f"expected 200 rows, got {len(rows)}"
    assert len({row["id"] for row in rows}) == 200, "ids must be unique"
    assert len({row["prompt"] for row in rows}) == 200, "prompts must be unique"
    write_jsonl("code_with_persian_comments", rows)


if __name__ == "__main__":
    main()
