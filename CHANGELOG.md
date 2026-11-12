# Changelog

All notable changes to PersianEval are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-12

Initial public release.

### Added

- **8 evaluation tasks** with frozen, checksummed datasets (980 samples total):
  `reasoning` (200), `spelling` (200), `cultural_knowledge` (100),
  `translation_fa_en` (100), `rag_faithfulness` (100), `bias_detection` (100),
  `code_with_persian_comments` (100), `reading_comprehension` (80).
- **Async harness** (`persianeval.harness`): concurrency with per-provider rate
  limiting, exponential-backoff retries, response caching keyed by
  `provider+model+task+seed+prompt`, JSON + Parquet output with an explicit
  pydantic schema.
- **Providers**: OpenAI, Anthropic, Ollama, vLLM (OpenAI-compatible) plus
  offline `dummy`/`scripted` providers for pipeline validation.
- **Scoring**: Persian-aware normalization (homoglyphs, digits, ZWNJ, diacritics),
  exact / fuzzy / LLM-as-judge scorers with public judge prompts.
- **CLI** (`persianeval`): `tasks`, `run`, `leaderboard` commands with budget
  controls (`--max-tokens`, `--max-requests-per-minute`, `--max-requests`).
- **Static leaderboard site**: dependency-free sortable table, pure-SVG radar
  chart, `data.json` artifact, empty-state page, generated via Jinja2.
- **CI**: ruff + `mypy --strict` + pytest (coverage ≥ 80%) on Python 3.11–3.13,
  dataset checksum verification; weekly leaderboard workflow with seeded 50-item
  subsamples (ADR 0003); release workflow with PyPI trusted publishing.
- **Docs**: bilingual README/methodology/CONTRIBUTING, task-authoring guide,
  three ADRs, CITATION.cff, Code of Conduct.

[0.1.0]: https://github.com/Abolfazlrwm/persianeval/releases/tag/v0.1.0
