.PHONY: help install test test-cov lint format run-api run-agents clean

help:
	@echo "StudentFlow — commandes disponibles :"
	@echo "  make install      Install en mode dev (pip install -e .[dev])"
	@echo "  make test         Lance pytest"
	@echo "  make test-cov     Tests + coverage"
	@echo "  make lint         ruff check"
	@echo "  make format       ruff format"
	@echo "  make run-api      Lance l'API FastAPI (uvicorn, reload)"
	@echo "  make run-agents   Lance les 3 agents en boucle"
	@echo "  make clean        Supprime caches et builds"

install:
	pip install -e .[dev]

test:
	pytest

test-cov:
	pytest --cov=studentflow --cov-report=term-missing

lint:
	ruff check src tests

format:
	ruff format src tests

run-api:
	uvicorn studentflow.api:app --reload --host 0.0.0.0 --port 8000

run-agents:
	python -m studentflow.cli run-agents

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
