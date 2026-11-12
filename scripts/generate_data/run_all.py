"""Regenerate every PersianEval v1 dataset and its checksums.

Run from the repository root:

    python scripts/generate_data/run_all.py
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from persianeval.tasks.base import DATA_ROOT

GENERATORS: tuple[str, ...] = (
    "gen_reasoning.py",
    "gen_spelling.py",
    "gen_cultural.py",
    "gen_reading.py",
    "gen_translation.py",
    "gen_rag.py",
    "gen_bias.py",
    "gen_code.py",
)


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Run all generators, then refresh data/v1/SHA256SUMS."""
    repo_root = Path(__file__).resolve().parents[2]
    for generator in GENERATORS:
        module = f"scripts.generate_data.{generator.removesuffix('.py')}"
        subprocess.run([sys.executable, "-m", module], cwd=repo_root, check=True)

    data_files = sorted(DATA_ROOT.glob("*.jsonl"))
    lines = [f"{sha256_file(path)}  {path.name}" for path in data_files]
    (DATA_ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"checksums for {len(data_files)} files written to {DATA_ROOT / 'SHA256SUMS'}")


if __name__ == "__main__":
    main()
