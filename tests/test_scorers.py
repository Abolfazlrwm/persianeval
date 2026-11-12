"""Tests for normalization and the three scorer families."""

from __future__ import annotations

import pytest

from persianeval.harness.scorers import (
    ExactScorer,
    FuzzyScorer,
    JudgeParseError,
    LLMJudgeScorer,
    normalize_text,
    parse_judge_output,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("يک كتاب", "یک کتاب"),  # Arabic yeh/kaf -> Persian
        ("۱۲۳۴۵", "12345"),  # Persian digits -> ASCII
        ("٤٥٦", "456"),  # Arabic-Indic digits -> ASCII
        ("می‌روم", "میروم"),  # ZWNJ removed by default
        ("کتا ب", "کتا ب"),  # plain spaces collapsed, not removed
        ("Hello, World!", "hello world"),  # punctuation + case
        ("مُثَلَّث", "مثلث"),  # diacritics stripped
        ("", ""),
    ],
)
def test_normalize_text(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_normalize_text_can_keep_zwnj() -> None:
    assert normalize_text("می‌روم", keep_zwnj=True) == "می\u200cروم"


@pytest.mark.parametrize(
    ("expected", "response", "passed"),
    [
        ("۴۸۰۰۰", "۴۸٬۰۰۰", True),  # separator + digits normalized
        ("یک کتاب", "يک كتاب", True),
        ("بله", "بله.", True),
        ("بله", "خیر", False),
        ("۱۲۳۴۵", "۱۲۳۴۶", False),
    ],
)
def test_exact_scorer(expected: str, response: str, passed: bool) -> None:
    result = ExactScorer().score(expected, response)
    assert result.passed is passed
    assert result.score == (1.0 if passed else 0.0)


def test_exact_scorer_strips_tokens() -> None:
    scorer = ExactScorer(strip_tokens=("تومان", "ریال"))
    assert scorer.score("۴۸۰۰۰", "۴۸۰۰۰ تومان").passed
    assert scorer.score("۳۰۰", "پاسخ: ۳۰۰ ریال").passed
    assert not scorer.score("۴۸۰۰۰", "۴۸۰۰۱ تومان").passed


def test_fuzzy_scorer_threshold_and_containment() -> None:
    scorer = FuzzyScorer(threshold=0.85)
    high = scorer.score("خراسان جنوبی", "خراسان جنوبی است")
    assert high.passed
    assert high.details["contained"] is True
    miss = scorer.score("بله", "خیر")
    assert not miss.passed
    assert miss.details["contained"] is False


def test_fuzzy_scorer_respects_zwnj_flag() -> None:
    keeper = FuzzyScorer(threshold=1.0, keep_zwnj=True)
    assert not keeper.score("می‌روم", "میروم").passed
    dropper = FuzzyScorer(threshold=1.0)
    assert dropper.score("می‌روم", "میروم").passed


def test_parse_judge_output_valid_json() -> None:
    score, rationale = parse_judge_output('{"score": 0.9, "rationale": "ترجمه خوب"}')
    assert score == pytest.approx(0.9)
    assert rationale == "ترجمه خوب"


def test_parse_judge_output_embedded_json_and_ten_scale() -> None:
    text = 'پاسخ نهایی: {"score": 8, "rationale": "خوب"}'
    score, _ = parse_judge_output(text)
    assert score == pytest.approx(0.8)


def test_parse_judge_output_clamps_and_rejects() -> None:
    assert parse_judge_output('{"score": 15, "rationale": ""}')[0] == 1.0
    assert parse_judge_output('{"score": -2, "rationale": ""}')[0] == 0.0
    with pytest.raises(JudgeParseError):
        parse_judge_output("no json here")
    with pytest.raises(JudgeParseError):
        parse_judge_output('{"score": "high"}')


def test_llm_judge_scorer_builds_prompt_and_scores() -> None:
    scorer = LLMJudgeScorer("پرسش: {question}\nپاسخ مدل: {response}", pass_threshold=0.7)
    prompt = scorer.build_prompt({"question": "س"}, "پ")
    assert prompt == "پرسش: س\nپاسخ مدل: پ"
    good = scorer.score('{"score": 0.95, "rationale": "ok"}')
    assert good.passed and good.score == pytest.approx(0.95)
    bad = scorer.score('{"score": 0.4, "rationale": "ok"}')
    assert not bad.passed
    broken = scorer.score("گاربرج")
    assert broken.score == 0.0 and not broken.passed
    assert "error" in broken.details
