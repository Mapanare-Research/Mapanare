# Mapanare v4.105.0 — Debugging Infrastructure: Valgrind, ASan, Crash Diagnostics

> **Phase B release 2.** v4.104.0 rebuilt mnc-stage1 and ran golden
> tests. This release builds confidence through debugging tools:
> valgrind on all 64 golden tests, AddressSanitizer and
> ThreadSanitizer builds, improved crash diagnostics, and CI gates
> that enforce sanitizer cleanliness on every push.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.104.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Instrument everything. Find what the tests cannot find. Make the tools run on every push.

---

## Scope

Phase A fixed bugs. v4.104.0 verified the fixes produce correct output.
v4.105.0 asks the deeper question: **is the correct output produced
safely?** Memory errors that happen to produce correct output today
will produce crashes tomorrow. Sanitizers find these.

The release has three pillars:

1. **Valgrind** -- run mnc-stage1 compiling each golden test. Detect
   uninitialised reads, invalid memory access, and leaks.
2. **Sanitizer builds** -- compile mnc-stage1 with ASan and TSan.
   Run the golden suite and async tests under instrumentation.
3. **Crash diagnostics** -- when mnc-stage1 crashes, it currently
   emits a bare segfault. Add breadcrumbs (`__mn_set_current_source`)
   so crashes report which source file and line was being compiled.
4. **CI gates** -- add valgrind and ASan jobs to GitHub Actions so
   regressions are caught on every push to `dev`.

## Phase 1 — Valgrind on all 64 golden tests

- [ ] Script: `scripts/valgrind_all_goldens.sh` (or extend existing if present)
  ```bash
  for mn in tests/golden/*.mn; do
      valgrind --leak-check=full --error-exitcode=1 \
          ./mapanare/self/mnc-stage1 "$mn" -o /tmp/$(basename "$mn" .mn).ll \
          2>&1 | tee valgrind_$(basename "$mn" .mn).log
  done
  ```
- [ ] Run on all 64 golden tests
- [ ] Classify per-test results: CLEAN / WARNINGS_ONLY / ERRORS
- [ ] For errors: extract the specific valgrind finding (uninit read, invalid read/write, use-after-free)
- [ ] Write `docs/roadmap/v4/v4.105.0/VALGRIND_REPORT.md` with per-test table
- [ ] Target: 0 errors across all 64 tests. Warnings (conditional jumps on uninit values) are documented but not blocking.

## Phase 2 — ASan build + golden suite

- [ ] Build mnc-stage1 with AddressSanitizer:
  ```bash
  clang -fsanitize=address -fno-omit-frame-pointer -O1 \
      mapanare/self/main.ll runtime/native/mapanare_runtime.c \
      -o mapanare/self/mnc-stage1-asan -lm -lpthread
  ```
- [ ] Run all 64 golden tests through `mnc-stage1-asan`
- [ ] Record per-test result: CLEAN / ASAN_ERROR (with error type)
- [ ] For ASan errors: capture the full ASan report (stack trace, allocation site, access site)
- [ ] Target: 0 ASan errors on the full golden suite
- [ ] If ASan finds issues: document them as docket items for v4.106.0 panel, do NOT fix in this release

## Phase 3 — TSan build + async golden tests

- [ ] Build mnc-stage1 with ThreadSanitizer:
  ```bash
  clang -fsanitize=thread -O1 \
      mapanare/self/main.ll runtime/native/mapanare_runtime.c \
      -o mapanare/self/mnc-stage1-tsan -lm -lpthread
  ```
- [ ] Run async golden tests (55-57) through `mnc-stage1-tsan`
- [ ] Record per-test result: CLEAN / DATA_RACE (with race description)
- [ ] If data races found: capture the TSan report, document as docket item
- [ ] Target: 0 data races on async tests

## Phase 4 — Crash diagnostics: source breadcrumbs

- [ ] Add `__mn_set_current_source(const char *filename, int line)` to the C runtime:
  ```c
  static __thread const char *mn_current_file = NULL;
  static __thread int mn_current_line = 0;

  void __mn_set_current_source(const char *filename, int line) {
      mn_current_file = filename;
      mn_current_line = line;
  }
  ```
- [ ] Add a signal handler for SIGSEGV/SIGABRT that prints the breadcrumb:
  ```c
  void __mn_crash_handler(int sig) {
      fprintf(stderr, "\nmnc-stage1 crashed (signal %d)", sig);
      if (mn_current_file) {
          fprintf(stderr, " while compiling %s:%d", mn_current_file, mn_current_line);
      }
      fprintf(stderr, "\n");
      _exit(128 + sig);
  }
  ```
- [ ] Wire the signal handler into the compiler driver's `main()`
- [ ] Emit `__mn_set_current_source` calls at key points in the compiler: file open, function entry, statement lowering
- [ ] Test: intentionally trigger a crash (compile a malformed file) and verify the breadcrumb appears
- [ ] Rebuild mnc-stage1 with the crash handler. Verify golden suite still passes.

## Phase 5 — CI gates: valgrind + ASan jobs

- [ ] Add `.github/workflows/sanitizers.yml`:
  ```yaml
  name: sanitizers
  on:
    push:
      branches: [dev]
    pull_request:
      branches: [dev]
  jobs:
    valgrind:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Install valgrind
          run: sudo apt-get install -y valgrind
        - name: Build mnc-stage1
          run: python scripts/build_stage1.py
        - name: Valgrind golden suite
          run: bash scripts/valgrind_all_goldens.sh
    asan:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Build mnc-stage1 with ASan
          run: |
            clang -fsanitize=address -fno-omit-frame-pointer -O1 \
                mapanare/self/main.ll runtime/native/mapanare_runtime.c \
                -o mapanare/self/mnc-stage1-asan -lm -lpthread
        - name: ASan golden suite
          run: |
            for mn in tests/golden/*.mn; do
                ./mapanare/self/mnc-stage1-asan "$mn" -o /dev/null || exit 1
            done
  ```
- [ ] Verify the workflow syntax is valid
- [ ] Test locally if possible (act or manual run)
- [ ] These jobs run on every push to `dev` and every PR

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.105.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Valgrind report for all 64 golden tests | `VALGRIND_REPORT.md` |
| 2 | 0 valgrind errors on golden suite (warnings acceptable) | report |
| 3 | ASan build of mnc-stage1 succeeds | build log |
| 4 | ASan report for all 64 golden tests | test log |
| 5 | 0 ASan errors on golden suite | test log |
| 6 | TSan report on async golden tests (55-57) | test log |
| 7 | Crash breadcrumbs implemented (`__mn_set_current_source` + signal handler) | diff of runtime + driver |
| 8 | CI workflow `sanitizers.yml` added | file in `.github/workflows/` |
| 9 | mnc-stage1 rebuilt with crash handler, golden suite still passes | test log |
| 10 | `SESSION_REPORT.md` written | file |

---

## What this release does NOT do

- **Fix bugs found by sanitizers** -- document them as docket items for the v4.106.0 panel. Fixing here would expand scope and delay the panel.
- **Add new features** -- this is pure debugging infrastructure.
- **Change optimizer passes** -- no modifications to `mir_opt.py`.
- **Change the grammar** -- no modifications to `mapanare.lark`.
- **Run the panel** -- that is v4.106.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Valgrind finds errors that Phase A was supposed to fix (e.g., tagged-pointer UB remnants) | medium | high | Document carefully. This is exactly why v4.105.0 exists -- to find these before the panel. |
| ASan build fails (incompatible with current IR emission) | medium | medium | Try `-O0` if `-O1` fails. If ASan cannot build mnc-stage1 at all, document as a known limitation and note in the panel evidence. |
| TSan false positives on the agent scheduler | medium | low | TSan false positives are common in lock-free code. Annotate with `__tsan_acquire`/`__tsan_release` if needed, or document as known false positives. |
| Crash handler interferes with normal operation | low | medium | The signal handler only fires on SIGSEGV/SIGABRT. Test thoroughly: golden suite must still pass with the handler installed. |
| CI jobs are too slow (valgrind on 64 tests) | medium | low | Set a timeout (15 minutes). If too slow, run valgrind on a subset (the 10 most complex golden tests) and document the limitation. |

---

## After v4.105.0

v4.106.0 is the Phase B panel. Seven reviewers grade v4.100.0-v4.105.0: are the critical bugs actually fixed? Does the native binary work? Are sanitizers clean? The v4.104.0 test results and v4.105.0 sanitizer reports are the primary evidence. If PASS, Phase C (benchmarks) begins. If NEEDS WORK, fixes go into v4.106.1.
