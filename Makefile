.PHONY: install build build-native bootstrap test lint fmt clean benchmark benchmark-runtime benchmark-cross-lang benchmark-report

install:
	pip install -e ".[dev]"

build:
	pip install -e .

build-native:  ## Build from seed (no Python required — needs gcc + llvm)
	bash scripts/build_from_seed.sh

bootstrap:  ## Three-stage fixed-point verification
	bash scripts/verify_fixed_point.sh

test:
	pytest tests/ -v -n auto --durations=20

lint:
	ruff check . && black --check . && mypy mapanare/ runtime/

fmt:
	black . && ruff check --fix .

benchmark: benchmark-runtime benchmark-cross-lang

benchmark-runtime:
	python -m benchmarks.run_all

benchmark-cross-lang:
	python -m benchmarks.cross_language.run_benchmarks

benchmark-report:
	python -m benchmarks.generate_report

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .pytest_cache *.egg-info dist build
