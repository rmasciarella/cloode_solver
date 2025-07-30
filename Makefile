# Modular Solver Makefile

PYTHON = .venv/bin/python
UV_RUN = PYTHONPATH=src uv run

# --- Environment Setup ---

dev:
	uv venv --python=3.11
	uv pip install --requirements .uv.lock

lock:
	uv pip compile --output-file .uv.lock pyproject.toml

relock:
	uv pip compile --upgrade --output-file .uv.lock pyproject.toml

# --- Code Quality ---

lint:
	uv run ruff check .
	uv run black --check .
	uv run mypy src/

format:
	uv run black .
	uv run ruff check . --fix

check-format:
	uv run black --check .

# --- Testing ---

test:
	$(UV_RUN) pytest

test-cov:
	$(UV_RUN) pytest --cov=solver --cov-report=term-missing

# --- Run App ---

run:
	$(UV_RUN) python src/solver/main.py

# --- CI Gate ---

ci: lint check-format test

# --- Cleanup ---

clean:
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache .uv.lock __pycache__ dist build

.PHONY: dev lock relock lint format check-format test test-cov run clean ci
