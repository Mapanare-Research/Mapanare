.PHONY: install build build-native build-rt bootstrap test lint fmt clean benchmark benchmark-runtime benchmark-cross-lang benchmark-report

install:
	pip install -e ".[dev]"

build:
	pip install -e .

build-native:  ## Build from seed (no Python required — needs gcc + llvm)
	bash scripts/build_from_seed.sh

build-rt:  ## Pre-compile C runtime into static library (faster linking)
	# v4.27.0: build with -fPIC so the archive can be linked into FFI shared
	# libraries produced by `mapanare bind --lang python`. Without -fPIC, the
	# `mapanare bind` fallback path produced a .so that ctypes' RTLD_NOW would
	# reject because of text relocations and unresolved runtime symbols.
	gcc -O2 -fPIC -c -I runtime/native runtime/native/mapanare_core.c -o /tmp/mapanare_core.o
	gcc -O2 -fPIC -c runtime/native/mn_user_main.c -o /tmp/mn_user_main.o
	ar rcs runtime/native/libmapanare_rt.a /tmp/mapanare_core.o /tmp/mn_user_main.o
	rm -f /tmp/mapanare_core.o /tmp/mn_user_main.o
	@echo "Built runtime/native/libmapanare_rt.a (compiled with -fPIC for FFI)"

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
