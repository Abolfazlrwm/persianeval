.PHONY: install fmt lint type test ci data leaderboard demo clean

install:            ## create the venv deps (already-installed envs are reused)
	pip install -e ".[dev]"

fmt:                ## auto-format and autofix
	ruff format .
	ruff check . --fix

lint:               ## lint only
	ruff check .

type:               ## strict type check
	mypy --strict src tests scripts

test:               ## tests with coverage gate
	pytest --cov=persianeval --cov-report=term-missing --cov-fail-under=80

ci: lint type test  ## everything CI runs

data:               ## regenerate all datasets + SHA256SUMS
	python scripts/generate_data/run_all.py

leaderboard:        ## rebuild the static site from results/
	persianeval leaderboard --results-dir results --out leaderboard

demo:               ## offline end-to-end validation run
	persianeval run --task reasoning --provider dummy --model demo --limit 5 --out results

clean:              ## remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache .persianeval_cache dist build *.egg-info
