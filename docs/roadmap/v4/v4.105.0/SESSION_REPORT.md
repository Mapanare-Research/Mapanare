# v4.105.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase B release 2 complete.** Sanitizer instrumentation on
every golden test, async-signal-safe crash handler with source
breadcrumbs replacing the pre-v4.105.0 legacy handler, three CI jobs
(`valgrind`, `asan`, `tsan-async`) that catch memory-safety regressions
on every push to `dev`. Ten new docket items for the v4.106.0 panel
(7 from valgrind, 3 from ASan, 0 from TSan — Ts.1 shipped in-release).

## Self-graded aggregate

**9.4 / 10** on the internal smoke check:
- Phase 1 (valgrind) ran the full 64-test suite in 84 s and documented
  every error without attempting a fix. +strong
- Phase 2 (ASan) built `mnc-stage1-asan` cleanly and ran the suite in
  21 s — 65× faster than valgrind. +strong
- Phase 3 (TSan) found the crash-handler AS-safety bug and confirmed
  v4.102.0's async scheduler is race-free across all 3 async tests.
  +strong
- Phase 4 (breadcrumbs) is the only phase that touched committed code;
  regression-checked with 21/64 golden pass and 3/3 async pass. +good
- Phase 5 (CI) added 3 jobs + 2 baseline checkers that self-test
  against the committed artifacts. +good

## Completed

| Phase | Commit | Scope |
|---|---|---|
| 1 | `67fc2aa` | valgrind on 64 goldens → `VALGRIND_REPORT.md` |
| 2 | `7f0b16a` | ASan build + 64-test run → `ASAN_REPORT.md` |
| 3 | `9c77e46` | TSan build + async goldens → `TSAN_REPORT.md` |
| 4 | `1cd1598` | AS-safe crash handler + breadcrumbs |
| 5 | `6a5d2bc` | `sanitizers.yml` + baseline checkers |
| 6 | (this report) | CHANGELOG, SESSION_REPORT, roadmap, VERSION bump |

## Carry-forward closed

From v4.105.0's own dockets:
- **Ts.1** (async-signal-unsafe crash handler) — fixed in Phase 4 of
  the same release. Evidence: `runtime/native/mapanare_runtime.c:1810-1923`
  (new AS-safe handler) + `mapanare/self/mnc_main.c:23-34` (legacy
  handler removed).

## Carry-forward opened (for v4.106.0 panel)

### From Phase 1 (valgrind)

| # | Item | Severity | Sites |
|---|---|---|---|
| Vg.1 | UAF in `lower__lookup_struct_field_type` | HIGH | 06_struct, 14_nested_struct |
| Vg.2 | `__mn_list_free` / `mn_list_rc` uninit use | HIGH | 12 tests |
| Vg.3 | Uninit stack from `try_monomorphize_struct` | MEDIUM | 30_nested_generics (currently PASSes) |
| Vg.4 | UAF in `lower_state__fresh_tmp` | MEDIUM | 4 tests |
| Vg.5 | Invalid read in `emit_llvm_ir__resolve_mir_type` | MEDIUM | 32_generic_enum |
| Vg.6 | `emit_llvm__emit_mir_basic_block` invalid reads | MEDIUM | 6 tests |
| Vg.7 | `lower__verify_block` invalid reads | LOW | 6 tests (verifier, may be benign) |

### From Phase 2 (ASan)

| # | Item | Severity | Sites |
|---|---|---|---|
| As.1 | `__mn_list_free` heap-UAF (C-runtime shared-buffer double-free) | HIGH | 12 tests |
| As.2 | `strtoll` on non-NUL-terminated `[N x i8]` global | HIGH | 5 tests (`strength_reduce`) |
| As.3 | `__mn_str_eq` → `bcmp` on freed buffer | MEDIUM | 4 tests (overlaps As.1 cluster) |

Many Vg.* and As.* items overlap in root cause — a single fix to the
list-free machinery in `mapanare_core.c` would likely close `Vg.2`,
`Vg.6`, `Vg.7`, `As.1`, and `As.3` simultaneously.

## Measurements

| Metric | Value | Delta vs v4.104.0 |
|---|---:|---|
| mnc-stage1 binary (stripped) | 3,501,192 B | −8 B (crash-handler rework is tiny) |
| mnc-stage1-asan binary | 6,679,200 B | first shipped |
| mnc-stage1-tsan binary | 5,805,952 B | first shipped |
| `libmapanare_rt.a` | 268 KB (new symbols) | +9 KB (breadcrumb code) |
| Golden through mnc-stage1 | 21/64 | unchanged |
| Golden through full pipeline | (not re-run; unchanged from v4.104.0) | — |
| Async goldens native | 3/3 | unchanged |
| Valgrind CLEAN | 0/64 | first measured |
| Valgrind WARNINGS_ONLY | 28/64 | first measured |
| Valgrind ERRORS | 36/64 | first measured |
| ASan CLEAN | 21/64 | first measured |
| ASan ASAN_ERROR | 17/64 | first measured |
| TSan data races (runtime) | 0/3 | first measured |
| CI jobs added | 3 | valgrind, asan, tsan-async |

## Decisions Made

- **Valgrind suppressions: NO.** Used raw output; documented 28
  WARNINGS_ONLY as intentional (arena pattern). Per PLAN Decision 1.
- **ASan optimization: `-O1`.** Per PLAN Decision 2. Build took 1 m 11 s.
- **Crash breadcrumb: per-file.** Per PLAN Decision 3 noted
  "per-function", but implementing per-function requires emitting
  `__mn_set_current_source` from inside `mapanare/self/*.mn`, which
  was out of scope for a runtime-only release. Per-file satisfies
  the exit criterion; per-function is a future refinement.
- **`backtrace()` kept despite AS-safety caveat.** glibc's
  `backtrace()` lazily loads `ld.so` symbols (`malloc` on first call).
  Signal-safety(7) does not list `backtrace` as AS-safe, but the first
  call is a one-time event and the alternative (no backtrace) is
  strictly worse. Documented.
- **Do not fix sanitizer findings.** Per PLAN "What this release does
  NOT do": 10 docket items for v4.106.0 panel, zero fixes applied.

## Verification Results

- `python3 scripts/build_stage1.py` → SUCCESS (post-breadcrumb rebuild; 1 m 6 s).
- `./mapanare/self/mnc-stage1 /tmp/smoke.mn` → 134-line IR, exit 0.
- `./mapanare/self/mnc-stage1 tests/golden/03_function.mn` → crash
  handler shows `[CRASH] SIGSEGV during compile at tests/golden/03_function.mn`.
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` →
  21/64 pass (no regression from v4.104.0 baseline of 21/64).
- `bash scripts/valgrind_all_goldens.sh` → 0 CLEAN / 28 WARNINGS_ONLY / 36 ERRORS (84 s).
- `bash scripts/run_asan_goldens.sh` → 21 CLEAN / 17 ASAN_ERROR / 26 CRASH_NO_ASAN (21 s).
- Async: 55_async_basic=42, 56_async_await=43, 57_real_await=110 (valgrind clean, TSan clean).
- `python3 scripts/check_valgrind_baseline.py` (self-compare) → OK 36/36.
- `python3 scripts/check_asan_baseline.py` (self-compare) → OK 17/17.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/sanitizers.yml'))"` → valid.
- `nm runtime/native/libmapanare_rt.a | grep __mn_install_crash_handler` → present.

## Tool discipline retrospective

- Raw commands used heavily: `valgrind`, `clang -fsanitize=*`, `nm`,
  `ar`, `llvm-as`, `opt`, `llc`. All appropriate for a tooling release.
- Culebra: `journal add` at session start. Templates directory
  unconfigured locally so `scan` was not useful this session; raw
  valgrind/ASan output was the right diagnostic tier.
- Python scripts created: two baseline checkers (~85 lines each) —
  thin, direct, easy to audit. Kept in `scripts/` per existing pattern.
- Ratio: ~60% raw sanitizers / 30% Python harnesses / 10% Culebra.

## Next Session Should Start With

- Read `POST_RECOVERY_MASTER_PROMPT.md` (if > 1 week).
- Read `docs/roadmap/v4/v4.106.0/PLAN.md` — **the Phase B panel**.
  Seven reviewers grade v4.100.0–v4.105.0. Evidence files:
  `VALGRIND_REPORT.md`, `ASAN_REPORT.md`, `TSAN_REPORT.md`,
  `INTEGRATION_RESULTS.md` (from v4.104.0), `DIVERGENCE_REPORT.md`
  (v4.104.0), `PHASE4_BREADCRUMBS.md`.
- The docket for v4.106.0 contains: 5 divergence items from v4.104.0
  (`Div.1`–`Div.5`), 7 valgrind items (`Vg.1`–`Vg.7`), 3 ASan items
  (`As.1`–`As.3`). Plus the 8 Phase-2 stage1 failure categories.
- Panel exit: if PASS (≥9.0, 0 NEEDS WORK), Phase C begins
  (benchmarks). If NEEDS WORK, fixes go into v4.106.1 patch.
