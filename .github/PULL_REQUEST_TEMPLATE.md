<!-- فارسی در پایین / Persian below -->

## Summary

What does this PR change, and why?

## Type of change

- [ ] Bug fix
- [ ] New task / dataset change
- [ ] Harness feature (runner, providers, scorers)
- [ ] Leaderboard / docs
- [ ] CI / packaging

## Checklist (non-negotiable standards)

- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy --strict src tests scripts` passes
- [ ] `pytest --cov-fail-under=80` passes; new code is covered
- [ ] No `TODO`/`FIXME`/placeholder text left behind
- [ ] Public APIs have NumPy-style docstrings
- [ ] **Data changes:** provenance documented in `src/persianeval/data/README.md`
      (source + license) and `SHA256SUMS` regenerated via
      `python scripts/generate_data/run_all.py`
- [ ] **Behavioral changes:** a matching ADR in `docs/adr/`
- [ ] User-facing changes documented in both English and Persian

---

## خلاصه

این PR چه چیزی را تغییر می‌دهد و چرا؟

## چک‌لیست

- [ ] `ruff` و `ruff format --check` سبز است
- [ ] `mypy --strict` سبز است
- [ ] `pytest` با پوشش ۸۰٪ سبز است؛ کد جدید پوشش دارد
- [ ] هیچ TODO یا متن ناقصی جا نمانده
- [ ] مستندات عمومی API به سبک NumPy نوشته شده
- [ ] تغییرات داده: منبع و لایسنس در README داده‌ها ثبت و checksumها بازتولید شده‌اند
- [ ] تغییرات رفتاری: ADR متناظر در `docs/adr/` نوشته شده
