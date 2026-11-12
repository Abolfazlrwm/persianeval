"""Code-with-Persian-comments task: complete Python functions from Persian specs."""

from __future__ import annotations

from persianeval.tasks.base import AbstractTask, ScoringKind, ScoringSpec

_JUDGE_PROMPT = """تو داور ارشد مهندسی نرم‌افزار هستی و کد پایتون مدل را می‌سنجی.
صورت تمرین (کامنت‌ها فارسی): {question}
تست‌های مورد انتظار (هر مورد: ورودی -> خروجی): {metadata}
پاسخ مدل: {response}

معیارها: درستی الگوریتم نسبت به همهٔ تست‌ها، حفظ امضای تابع، مدیریت حالت‌های مرزی
ذکرشده در کامنت‌ها، و رعایت کامنت‌گذاری فارسی خوانا.
اگر کد حتی یک تست را رد می‌کند یا امضا را عوض می‌کند، امتیاز 0.3 یا کمتر بده.
کد را اجرا نمی‌کنی؛ فقط با تحلیل دقیق داوری کن.
فقط یک شیء JSON برگردان: {{"score": عدد بین 0 و 1, "rationale": توضیح کوتاه}}"""


class CodeWithPersianCommentsTask(AbstractTask):
    """Complete Python functions specified through Persian comments.

    Each item provides a signature, Persian docstring/comments and hidden
    test cases; the judge verifies correctness against the tests without
    executing untrusted model code. An opt-in sandboxed executor can be
    added later (see ADR 0002).
    """

    name = "code_with_persian_comments"
    title_en = "Code with Persian Comments"
    title_fa = "کدنویسی با کامنت فارسی"
    description_en = (
        "Python function completion from Persian-language specs and "
        "comments; judged against hidden input/output test cases."
    )
    description_fa = "تکمیل توابع پایتون بر اساس توضیحات و کامنت‌های فارسی؛ داوری بر اساس تست‌های ورودی/خروجی."
    data_file = "code_with_persian_comments.jsonl"
    min_samples = 200
    system_prompt = (
        "فقط بدنهٔ تابع خواسته‌شده را به زبان پایتون بنویس؛ کامنت‌های فارسی را حفظ کن "
        "و هیچ توضیح اضافه‌ای خارج از کد ننویس."
    )
    scoring = ScoringSpec(kind=ScoringKind.JUDGE, judge_prompt=_JUDGE_PROMPT, score_pass_threshold=0.75)
    source = (
        "15 parametric function families with computed test cases "
        "(scripts/generate_data/gen_code.py). Apache-2.0."
    )
