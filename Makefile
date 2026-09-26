.PHONY: install setup test test-unit test-integration test-e2e debug lint list-categories list-movies list-series show-logs sync-dry sync-live clean

install:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

setup:
	.venv/bin/python -m src.args --setup

debug:
	.venv/bin/python -m src.debug

test:
	.venv/bin/pytest -v --cov=src
	.venv/bin/python -m src.args --test

test-unit:
	.venv/bin/pytest tests/unit/ -v

test-integration:
	.venv/bin/pytest tests/integration/ -v

test-e2e:
	.venv/bin/pytest tests/e2e/ -v

lint:
	.venv/bin/flake8 src tests

list-categories:
	.venv/bin/python -m src.args --list-categories

list-movies:
	.venv/bin/python -m src.args --list-movies

list-series:
	.venv/bin/python -m src.args --list-series

show-logs:
	.venv/bin/python -m src.args --show-logs

sync-dry:
	.venv/bin/python -m src.args --sync --dry-run

sync-live:
	.venv/bin/python -m src.args --sync

clean:
	rm -rf .venv .pytest_cache __pycache__ src/__pycache__ tests/__pycache__ .coverage data/state.json data/cache.json logs/release_history.log logs/debug_report.txt
