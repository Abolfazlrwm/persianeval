# Changelog

All notable changes to PersianEval are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-25

### Added

- `zai` provider: evaluate GLM models through Z.ai's OpenAI-compatible Chat
  Completions endpoint (`ZAI_API_KEY` / `ZAI_BASE_URL`, plus the usual
  `--base-url` override). It inherits the OpenAI request/response handling
  and the shared rate-limiter/retry plumbing, and is tested offline like the
  other providers.
- First published leaderboard run: GLM-4-Plus (Z.ai hosted API) over the
  weekly seeded subsample (20 items per task, seed 202648, ISO week 48).
  Seven of the eight tasks completed; `code_with_persian_comments` was cut
  short by the API's rate limit and stays pending, so its table cell shows
  a dash until a re-run lands.

### Changed

- Result JSONs from published runs are now committed under `results/` as the
  audit trail behind `leaderboard/data.json` (parquet files and caches stay
  git-ignored). The `site_only=true` dispatch of the leaderboard workflow
  builds the published page from these committed files.
- README leaderboard status section now describes the actual run instead of
  the empty-pipeline state.

## [0.1.2] - 2026-11-23

### Fixed

- `CITATION.cff` was still pinned to 0.1.0 with the original release date;
  the v0.1.1 fix (7ceae52) only touched the bibtex block in the README.
  Version and `date-released` now follow the tag.
- `docs/methodology.md` said the weekly action evaluates a 50-item subsample
  and that the full corpus is 980 samples. Both numbers predate the 2026-11-17
  amendment of ADR 0003 (subsample is 20 items) and the v1 corpus (1,600
  samples); corrected in both the English and Persian sections.
- Persian README typo: «خط لولهبورد» → «خط لیدربورد».

## [0.1.1] - 2026-11-15

### Fixed

- `cultural_knowledge-0014`: the prompt spelled زیگورات with the Arabic yeh
  (ي); it now uses the Persian ی consistently with the rest of the corpus.
  SHA-256 checksums regenerated.

### Changed

- Release workflow: the PyPI publish step is `continue-on-error` until the
  "trusted publisher" is registered on PyPI, keeping release runs green.

## [0.1.0] - 2026-11-12

Initial public release.

### Added

- **8 evaluation tasks** with frozen, checksummed datasets (1,600 samples total):
  `reasoning` (200), `spelling` (200), `cultural_knowledge` (200),
  `translation_fa_en` (200), `rag_faithfulness` (200), `bias_detection` (200),
  `code_with_persian_comments` (200), `reading_comprehension` (200).
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

[0.2.0]: https://github.com/Abolfazlrwm/persianeval/releases/tag/v0.2.0
[0.1.2]: https://github.com/Abolfazlrwm/persianeval/releases/tag/v0.1.2
[0.1.1]: https://github.com/Abolfazlrwm/persianeval/releases/tag/v0.1.1
[0.1.0]: https://github.com/Abolfazlrwm/persianeval/releases/tag/v0.1.0
