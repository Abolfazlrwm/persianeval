Run results (JSON/Parquet) are produced by `persianeval run`.

- `*.json` files from published leaderboard runs are **committed on purpose**:
  they are the audit trail behind `leaderboard/data.json` (every row there can
  be traced back to a per-item score) and the fallback that the
  `site_only=true` dispatch of `.github/workflows/leaderboard.yml` publishes
  to GitHub Pages when the weekly evaluation is skipped.
- `*.parquet` files and the response cache stay local; CI and local runs write
  them here and they are git-ignored.

Each JSON records the full run context (provider, model, seed, temperature,
limit, per-item scores), so a committed file is exactly reproducible with the
same seed.
