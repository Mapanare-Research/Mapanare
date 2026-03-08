.PHONY: install build test lint fmt clean benchmark benchmark-report

install:
	pip install -e ".[dev]"

build:
	pip install -e .

test:
	pytest tests/ -v

lint:
	ruff check . && black --check . && mypy mapa/ runtime/

fmt:
	black . && ruff check --fix .

benchmark:
	python -m benchmarks.run_all

benchmark-report:
	python -m benchmarks.generate_report

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache *.egg-info dist build
