# v4.29.0: force bash so the check-runtime-sources target can use
# process substitution. Without this, Debian/Ubuntu make falls back
# to /bin/dash which has no ``<(...)`` support.
SHELL := /bin/bash

.PHONY: install build build-native build-rt check-runtime-sources bootstrap test lint fmt clean benchmark benchmark-runtime benchmark-cross-lang benchmark-report

# v4.29.0: build-rt now enumerates every runtime object that is expected
# to land in libmapanare_rt.a. The list used to be hand-maintained and
# missed 4 of 5 v3.47.0 runtime files plus the two orphaned db/html
# modules added later (v4.26.0 panel: Anaconda HIGH). The
# check-runtime-sources target below diffs this list against the actual
# runtime/native/*.c files on disk and fails if they drift.
#
# ``mn_user_main.c`` provides the C ``main()`` wrapper for runnable
# binaries and is intentionally paired with core.c. ``mnc_main.c`` and
# ``mnc_driver.c`` are self-hosted driver shims that only link into
# mnc-stage1; they are NOT part of libmapanare_rt.a. The drift check
# respects this allowlist.
RUNTIME_SOURCES := \
	mapanare_core.c \
	mapanare_io.c \
	mapanare_runtime.c \
	mapanare_gpu.c \
	mapanare_gpu_builtins.c \
	mapanare_db.c \
	mapanare_html.c \
	mn_user_main.c

# Files under runtime/native/ that are deliberately not part of the
# runtime archive (they belong to the self-hosted driver).
RUNTIME_EXCLUDES := mnc_main.c mnc_driver.c

install:
	pip install -e ".[dev]"

build:
	pip install -e .

build-native:  ## Build from seed (no Python required — needs gcc + llvm)
	bash scripts/build_from_seed.sh

build-rt: check-runtime-sources  ## Pre-compile C runtime into static library (faster linking)
	# v4.27.0: build with -fPIC so the archive can be linked into FFI shared
	# libraries produced by `mapanare bind --lang python`. Without -fPIC, the
	# `mapanare bind` fallback path produced a .so that ctypes' RTLD_NOW would
	# reject because of text relocations and unresolved runtime symbols.
	# v4.29.0: every runtime source in $(RUNTIME_SOURCES) is compiled and
	# added to the archive. Previously only mapanare_core.c + mn_user_main.c
	# were included, which left mapanare_db.c (1,130 lines) and
	# mapanare_html.c (812 lines) and several other modules orphaned.
	@rm -f /tmp/mapanare_rt_*.o
	@for src in $(RUNTIME_SOURCES); do \
		obj=/tmp/mapanare_rt_$${src%.c}.o; \
		echo "  gcc -O2 -fPIC -c runtime/native/$$src -o $$obj"; \
		gcc -O2 -fPIC -c -I runtime/native runtime/native/$$src -o $$obj || exit 1; \
	done
	@ar rcs runtime/native/libmapanare_rt.a /tmp/mapanare_rt_*.o
	@rm -f /tmp/mapanare_rt_*.o
	@echo "Built runtime/native/libmapanare_rt.a ($(words $(RUNTIME_SOURCES)) modules, -fPIC)"

check-runtime-sources:  ## v4.29.0: fail if runtime/native/*.c drifts from RUNTIME_SOURCES
	@ACTUAL=$$(ls runtime/native/*.c | xargs -n1 basename | sort); \
	EXPECTED=$$(printf "%s\n" $(RUNTIME_SOURCES) $(RUNTIME_EXCLUDES) | sort); \
	DIFF=$$(diff <(echo "$$ACTUAL") <(echo "$$EXPECTED") || true); \
	if [ -n "$$DIFF" ]; then \
		echo "error: runtime/native/*.c drifted from Makefile enumeration:"; \
		echo "$$DIFF" | sed 's/^/  /'; \
		echo ""; \
		echo "Add any new file to RUNTIME_SOURCES (or RUNTIME_EXCLUDES if it"; \
		echo "belongs to the self-hosted driver) in the Makefile."; \
		exit 1; \
	fi

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
