.PHONY: install setup test lint list-movies list-series show-logs sync-dry sync-live clean

install:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

setup:
	python src/args.py --setup

test:
	.venv/bin/pytest -v --cov=src
	.venv/bin/python src/args.py --test

lint:
	.venv/bin/flake8 src tests

list-movies:
	.venv/bin/python src/args.py --list-movies

list-series:
	.venv/bin/python src/args.py --list-series

show-logs:
	.venv/bin/python src/args.py --show-logs

sync-dry:
	.venv/bin/python src/args.py --sync --dry-run

sync-live:
	.venv/bin/python src/args.py --sync

clean:
	rm -rf .venv .pytest_cache __pycache__ src/__pycache__ tests/__pycache__ .coverage data/state.json data/cache.json logs/release_history.log
