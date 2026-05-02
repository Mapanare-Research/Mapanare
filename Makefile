# v4.29.0: force bash so the check-runtime-sources target can use
# process substitution. Without this, Debian/Ubuntu make falls back
# to /bin/dash which has no ``<(...)`` support.
SHELL := /bin/bash

.PHONY: install build build-native build-rt check-runtime-sources check-no-tracked-binaries bootstrap test lint fmt clean benchmark benchmark-runtime benchmark-cross-lang benchmark-report count-tests leak-check ci-gates clean-build-test

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

# v4.31.0: MAPANARE_VERSION comes from the VERSION file and is passed
# to every runtime .c at compile time. ``runtime/native/mapanare_io.c``
# uses it to build the User-Agent string for HTTP requests. Mamba
# flagged the hardcoded ``Mapanare/3.42`` string in the v4.26.0 panel
# (5+ minor versions stale); the macro wiring closes that carry-
# forward and guarantees the next staleness is a build-system bug.
MAPANARE_VERSION := $(shell cat VERSION)

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
		echo "  gcc -O2 -fPIC -DMAPANARE_VERSION=\"\\\"$(MAPANARE_VERSION)\\\"\" -c runtime/native/$$src -o $$obj"; \
		gcc -O2 -fPIC '-DMAPANARE_VERSION="$(MAPANARE_VERSION)"' -c -I runtime/native runtime/native/$$src -o $$obj || exit 1; \
	done
	@# v5.8.8: macOS needs mapanare_metal.m (Objective-C, Metal backend)
	@# in the archive too — mapanare_gpu.c's __APPLE__-guarded code path
	@# references mapanare_metal_available() / mapanare_metal_init() from
	@# mapanare_metal.m. Without this, the macOS integration tests
	@# (tests/integration/test_golden_pipeline.py for tensor goldens
	@# 49-53) fail to link with "Undefined symbols for architecture
	@# arm64". The .m file only compiles on Darwin; gated by uname.
	@if [ "$$(uname -s)" = "Darwin" ]; then \
		echo "  clang -O2 -fPIC -fobjc-arc -c runtime/native/mapanare_metal.m -o /tmp/mapanare_rt_mapanare_metal.o"; \
		clang -O2 -fPIC -fobjc-arc '-DMAPANARE_VERSION="$(MAPANARE_VERSION)"' -c -I runtime/native runtime/native/mapanare_metal.m -o /tmp/mapanare_rt_mapanare_metal.o || exit 1; \
	fi
	@ar rcs runtime/native/libmapanare_rt.a /tmp/mapanare_rt_*.o
	@rm -f /tmp/mapanare_rt_*.o
	@echo "Built runtime/native/libmapanare_rt.a ($(words $(RUNTIME_SOURCES)) modules + Metal on Darwin, -fPIC, MAPANARE_VERSION=$(MAPANARE_VERSION))"

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

# v4.32.0 Phase 2.1 (Boa M1): fail if any binary artifact is tracked
# in runtime/native/ or mapanare/self/. A committed archive / shared
# object / ELF / PE32 is source-clean, artifact-stale waiting to
# happen — the v4.31.0 arc-end panel caught libmapanare_rt.a carrying
# `__mn_list_oob_buf` after the source had removed it. This check
# complements check-runtime-sources on the binary side.
#
# Allowlist: mapanare/self/mnc-seed is the frozen v0.6.0 bootstrap
# binary and is deliberately tracked (there is no other way to build
# from scratch without Python).
check-no-tracked-binaries:  ## v4.32.0: fail if runtime/native or self/ contains tracked binaries
	@BINS=$$(git ls-files runtime/native/ mapanare/self/ | \
		grep -v '^mapanare/self/mnc-seed$$' | \
		xargs -I{} sh -c 'f=$$(file -b "{}" 2>/dev/null); case "$$f" in *ELF*|*"PE32"*|*"Mach-O"*|*"current ar archive"*|*"shared object"*) echo "{}";; esac'); \
	if [ -n "$$BINS" ]; then \
		echo "error: tracked binary artifact(s) found:"; \
		echo "$$BINS" | sed 's/^/  /'; \
		echo ""; \
		echo "Binary artifacts (.a, .o, .so, .dll, .exe, ELF/PE/Mach-O)"; \
		echo "should be built by 'make build-rt' or similar, never"; \
		echo "committed. 'git rm' the offending file(s) and add them"; \
		echo "to .gitignore. See v4.32.0 Phase 2.1 for the precedent."; \
		exit 1; \
	fi

bootstrap:  ## Three-stage fixed-point verification
	bash scripts/verify_fixed_point.sh

test:
	pytest tests/ -v -n auto --durations=20

count-tests:  ## v5.0.6 An.10: deterministic test count for release-note deltas
	@python scripts/count_tests.py

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

leak-check:  ## v5.4.2: compile+link+run every golden under LSan, gate against baseline
	@bash scripts/run_asan_leak_goldens.sh
	@python3 scripts/check_leak_summary.py

# v5.24.0 Hy.1 (Anaconda §2.D): single command running the full CI-gate
# inventory locally. Pre-release checklist shrinks to "run make ci-gates,
# expect zero violations." Eliminates the wired-but-unchecked failure
# mode that produced Reg.1 / hollow-feature gate / docs-drift gate
# silent failures across v5.17.0 → v5.22.0 (Anaconda's −1.30 grade hit).
# Cadence-check is intentionally non-blocking (warn-only) here — it
# fires hard in CI only when the v5.27.0 panel window opens.
ci-gates:  ## v5.24.0 Hy.1: run all CI gates locally, exit 1 on any failure
	@echo "=== Mapanare CI Gates ==="
	@python3 scripts/check_silent_skips.py tests/ && echo "  silent_skips: GREEN" || (echo "  silent_skips: RED"; exit 1)
	@python3 scripts/check_changelog_honesty.py && echo "  changelog_honesty: GREEN" || (echo "  changelog_honesty: RED"; exit 1)
	@python3 scripts/check_workflow_shapes.py && echo "  workflow_shapes: GREEN" || (echo "  workflow_shapes: RED"; exit 1)
	@python3 scripts/check_docs_drift.py && echo "  docs_drift: GREEN" || (echo "  docs_drift: RED"; exit 1)
	@python3 scripts/check_no_hollow_features.py && echo "  hollow_features: GREEN" || (echo "  hollow_features: RED"; exit 1)
	@python3 scripts/check_struct_registry.py && echo "  struct_registry: GREEN" || (echo "  struct_registry: RED"; exit 1)
	@python3 scripts/check_doc_freshness.py && echo "  doc_freshness: GREEN" || (echo "  doc_freshness: RED"; exit 1)
	@python3 scripts/check_cadence.py && echo "  cadence: GREEN" || echo "  cadence: WARN (non-blocking)"
	@$(MAKE) -s clean-build-test && echo "  clean-build-test: GREEN" || (echo "  clean-build-test: RED"; exit 1)
	@echo "=== All gates GREEN ==="

# v5.25.0 Pv.3: rebuild runtime archive from a clean state and run the
# @test runtime smoke test against it. Catches the runtime-archive
# rename / relocation class structurally — any future drift between
# what `make build-rt` produces and what `_find_runtime_lib()` looks
# for fails the gate at PR time, not on fresh-checkout CI. The
# explicit ``rm -f`` of the candidate artifacts is what makes the
# rebuild meaningful: ``make clean`` alone does not touch
# ``runtime/native/libmapanare_*.{a,so,dylib,dll}``.
clean-build-test:  ## v5.25.0 Pv.3: clean rebuild of runtime + @test smoke
	@rm -f runtime/native/libmapanare_rt.a \
	       runtime/native/libmapanare_runtime.so \
	       runtime/native/libmapanare_runtime.dylib \
	       runtime/native/libmapanare_runtime.dll
	@$(MAKE) -s build-rt >/dev/null
	@pytest tests/test_at_test_runtime.py tests/test_runtime_lib_lookup.py \
	        -q --no-header --tb=short
