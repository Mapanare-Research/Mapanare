# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mapanare is an AI-native compiled programming language with first-class agents, signals, streams, and tensors. It compiles to LLVM IR (primary) and C (fallback via gcc). A WebAssembly backend exists for browser/server targets. The self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in `mapanare/self/`. The compiler compiles itself — `bash scripts/build_from_seed.sh` builds from source with no Python.

## Current Version & Roadmap

- **v4.118.0** (shipped) — **Phase F release 1: final cross-language benchmark.** The v4.120.0 panel's evidence document now exists. Zero compiler/runtime code changes; four version-string edits to `benchmarks/cross_language/run_benchmarks.py`. **All 6 workloads × 6 language configs × 10 runs ran to completion** (`fib_recursive`, `quicksort`, `struct_alloc`, `enum_match`, `prime_sieve`, `string_concat` × C gcc -O2 / C clang -O2 / Rust -O / Go / Mapanare O2 / Python 3.12) — 36/36 correct checksums, raw per-run data at `benchmarks/cross_language/v4.118.0-results.json`. **Plus 5 native-async workloads × 3 languages × 10 runs** (`01_sequential_chain` / `02_fanout` / `03_io_bound` / `04_mixed_cpu_io` / `05_backpressure` × Mapanare / Python asyncio / Go goroutines) — 15/15 correct checksums, raw data at `benchmarks/async/v4.118.0-async.json`. **First time async numbers link and execute for Mapanare** since v4.94.0 skipped the Mapanare side entirely with "linking currently fails." **Headlines (Mapanare O2 geomean across 6 workloads = 3.07 ms): 5.46× slower than C gcc -O2** (down from v4.107.0's 9.5×, a 2× narrowing attributable entirely to v4.108.0's Phase C string_concat fix), **1.13× slower than Rust**, **on par with Go (1.04×)**, **36.9× faster than Python 3.12**. **Async geomean 2.13 ms: 42.6× faster than Python asyncio, 1.74× slower than Go goroutines.** **Progress v4.82.0 → v4.118.0 (Mapanare O2 wall)**: `string_concat` **102.31 → 1.32 ms (77.5× speedup)** — the one real win, entirely from v4.108.0's auto-StringBuilder MIR pass; every other workload within ±10% once harness methodology (`/usr/bin/time -v` wrap adding ~1–3 ms spawn overhead) is normalised. **`benchmarks/FINAL_REPORT_v4.120.md`** (500 lines) publishes 7 tables (wall / memory / binary / LOC / speedup vs C / progress / async), 6 per-workload ASCII position charts, methodology with toolchain versions (gcc 13.3, clang 18.1, rustc 1.94.1, go 1.22.5, python 3.12, LLVM 18.1.3), spectrum analysis by workload category, and a reproducibility checklist. `libmapanare_rt.a` byte-identical to v4.117.0. **No new dockets; no CARRY_FORWARD closures** (measurement-only). Carry-forward for v5.x: Rt.1 (boxed-enum payload, `enum_match` 2× gap vs Rust), Qs.1 (`List<Int>` indexing), TBAA.1 (declared but not wired), Sh.4/5/6/7/8/9a/9b/10. **Next: v4.119.0 writes the retrospective — full v4.0.0 → v4.118.0 journey, compiled statistics, v5 readiness pre-panel audit. v4.120.0 is the panel — 7 reviewers, v5 gate attempt 2; the numbers from this release are the benchmark evidence.**
- **v4.117.0** (shipped) — **Phase E release 3: testing sweep — sanitizer CI, flaky audit, coverage.** Zero compiler/runtime code changes. Makes the test infrastructure production-grade before the v4.120.0 panel opens. **ASan and TSan CI gates** already permanent since v4.105.0 via `.github/workflows/sanitizers.yml` (valgrind full golden suite, ASan full golden suite with `check_asan_baseline.py` regression gate, tsan-async on goldens 55/56/57). This release **extends `tsan-async`** to cover the v4.115.0 native async I/O demos (`examples/async_file_io.mn`, `examples/async_http_demo.mn`); any future scheduler or coroutine-frame race under I/O-heavy workloads fails CI at PR time. **Flaky audit** (`tests/FLAKY_AUDIT.md`) ran pytest 5x against 1,501 tests across 9 subdirectories; pairwise `diff` of sorted failure sets across all 4 adjacent pairs is **empty**. **Zero flaky tests.** The 22 observed failures are deterministic pre-existing bugs (14 stale CLI tests asserting on pre-rename `mapanare compile`; 3 DWARF-deferral warnings for a SPEC §21.3-deferred feature; 2 drop-glue count drifts from v4.101.0 move-semantics; 1 linkage spec over-specification; 1 emitter-hardening count drift; 1 bounded-generic trait edge case) — catalogued per bucket, open for v4.120.0 panel. **Coverage report** (`tests/COVERAGE.md`) — pytest-cov 7.1.0 / coverage 7.13.5 on the 7 core-pipeline test directories. Aggregate **43%** (8,896 / 20,894 stmts); **within the core pipeline 73%**. Per-module: ast_nodes 100%, mir 95%, types 92%, lexer 89%, pattern_matching 88%, multi_module 83%, semantic 81%, parser 78%, mir_opt 72%, lower 69%, emit_llvm_text 65%. Below-50% tail: 13 modules at 0% because their tests live in out-of-scope dirs (lsp/emit_c/wasm/transpilers), 12 are real gaps (cli.py 25% — stale CLI tests, optimizer.py 9% — dead-code candidate, diagnostics.py 49%). 5 recommendations in COVERAGE.md for future work. **Integration pipeline hardening** (`tests/integration/test_pipeline_hardening.py`, 6 new tests, all PASS) — deliberately feeds broken inputs at each stage, asserts the `full_pipeline` harness captures the correct failing stage with a non-empty error: unparseable `.mn` → emit; hand-crafted invalid `.ll` → llvm-as non-zero exit; 42-exit binary → nonzero `pr.exit_code`; `sleep(60)` binary → `TimeoutExpired` raises cleanly; stdout mismatch vs `.expected` → reported on `stdout` stage (uses monkeypatch to isolate); negative control — hello.mn still passes. **New CI job** `ci.yml::coverage` (informational, not gating) runs the audit command and uploads coverage.xml as a 30-day artifact; flips to enforcing after 5 stable releases per PLAN.md risk register. `libmapanare_rt.a` byte-identical to v4.116.0. **No new dockets; no CARRY_FORWARD closures.** **Next: Phase E complete. Phase F opens at v4.118.0 — final cross-language benchmark with all Phase A–E fixes landed.**
- **v4.116.0** (shipped) — **Phase E release 2: documentation batch.** Five doc gaps flagged by Boa (and others) since v4.82.0 closed without touching a line of compiler/runtime/self-hosted code. **`README.md`** — version badge 4.31.0 → 4.116.0; headline benchmark line (50× faster than Python, 1.06× on par with Rust, 4.85× slower than C gcc -O2) linking to `benchmarks/PHASE_C_RESULTS.md`; self-hosted LOC 15K → 38K; Feature Status table adds async/await row; async example added to "The Language" section; stale "Coming in v4.2" corrected to "Planned" with status note; Roadmap table extended through v4.116.0 with v4.120.0 panel row. **`docs/SPEC.md`** — header 1.0.0 Final → 4.116.0 Live with sync-discipline note naming `mapanare.lark`, `types.py`, `self/lexer.mn` as canonical; §29 adds v4.115.0 status paragraph (cooperative-not-preemptive, native file+HTTP I/O demoed, mnc-stage1 async-lowering gap is Sh.4); §29.7 `for await` row reflagged as planned/v5.x. **`docs/cookbook/async.md`** — corrected stale `mnc run` claim; added §8 native compilation workflow, §9 file I/O example, §10 HTTP GET example, §11 Sh.9a/Sh.9b emitter-bug recipes with the workarounds shipped in the v4.115.0 demos. **`docs/guides/debugging.md`** — full rewrite (213+/164-) correcting the stale "Mapanare emits DWARF with -g" claim (SPEC §21.3 defers DWARF to v5.x; Rattler's v4.26.0 panel flag finally addressed in user-facing docs); new focus on valgrind as primary tool, ASan, TSan, ir_doctor.py, Culebra, integration harness, decision table mapping symptoms to tools. **`docs/guides/getting_started.md`** (NEW, 244 lines) — practical "from zero to a native binary" walk for developers familiar with compiled languages; complements the existing 624-line tutorial at `docs/getting-started.md`; covers prerequisites, Python bootstrap pipeline, mnc-stage1 pipeline, build-from-seed path, test suite, troubleshooting footer. **`docs/roadmap/v4/v4.116.0/VERIFICATION.md`** — panel-facing receipt: 7/7 compile-and-run snippets PASS, 3/3 async goldens regression-clean (42/43/110 unchanged), SPEC syntax review, shell-command spot-check. `libmapanare_rt.a` byte-identical to v4.115.0. **No new dockets**; all v4.115.0 dockets (Sh.9a, Sh.9b, Sh.10) remain open — now documented as user-facing recipes in the cookbook. **Next: v4.117.0 is test-suite hardening — ASan CI gate, TSan CI gate, flaky audit, coverage report, integration test hardening.**
- **v4.115.0** (shipped) — **Phase E release 1: async I/O demo running natively.** Closes the v4.99.0 panel's async-I/O gap. Two new example programs: **`examples/async_file_io.mn`** (cooperative async file I/O — seeds input file, reads back synchronously, runs an async pipeline of byte-based `count_lines` + `count_words` counters over the content, writes a two-field summary file from inside `await write_summary(...)`, reads back to verify — produces `async pipeline: lines=3 words=10` / `summary file: lines=3 words=10` at both `-O0` and `-O2`), and **`examples/async_http_demo.mn`** (real HTTP GET to `http://example.com/` returning 540 bytes, async pipeline `body_bytes` → `has_marker` → `write_summary`, deterministic non-crash exit if sandbox blocks outbound TCP). New **`docs/guides/async.md`** (244 lines) walks the mental model (cooperative, not preemptive), `async fn` / `await` / `block_on` syntax, both end-to-end examples, what-works and what-doesn't tables with docket IDs, and Sh.9 workaround recipes. **Zero compiler/runtime/self-hosted code changes** — Phase 4 explicitly confirmed no new C runtime symbols needed; `libmapanare_rt.a` byte-identical to v4.114.0. Two Python-bootstrap emitter bugs surfaced and worked around in both examples and the guide: **Sh.9a** (`await` on a String-returning async fn produces invalid IR — type mismatch between future-extraction GEP and inlined String return) and **Sh.9b** (DCE eliminates `await` calls whose Int return is unused, silently dropping the side-effecting C call inside — worked around by folding `wrote` into the pipeline's return encoding). **Sh.10** opened for making `__mn_file_read_async` user-callable (pre-requisite: Sh.9a). **v4.114.1 patch items deferred** per user direction: v4.112.0 release name rename, `tests/bootstrap/byref_test.mn` commit, site-4 cleanup comment — all carry into Phase E as open items. **Regression clean**: Python-bootstrap golden 63/64 (pre-existing `51_match_guards_and_or`), async goldens 55/56/57 → 42/43/110 unchanged. **Next: v4.116.0 documentation batch — README / SPEC / cookbook / getting-started pass.**
- **v4.114.0** (shipped) — **Phase D panel: NEEDS WORK @ 8.21/10, v4.114.1 patch scheduled.** Panel release with zero code changes. Seven reviewers graded v4.111.0-v4.113.0: **2 PASS (Viper 8.5, Boa 8.5), 5 PASS WITH NOTES (Rattler 8.2, Anaconda 7.8, Cobra 8.0, Coral 8.3, Mamba 8.2), 0 NEEDS WORK**. Aggregate **8.21 / 10** falls 0.29 below the Phase D PASS threshold of >= 8.5. Decision rule applies mechanically → NEEDS WORK → v4.114.1 patch. Panel is healthy (v4.106.0 was 7.87 with 3 reviewers at 7.5 and zero PASS; v4.114.0 is 8.21 with 2 PASS, no reviewer below 7.8; every moving reviewer moved up +0.34 aggregate). **11/11 v4.99.0 docket items confirmed CLOSED** with line-by-line evidence in `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md`. Panel artifacts: `MEASUREMENTS.md` (9 quantitative sections), `DOCKET_AUDIT.md` (11-item walk with file:line references), `.reviews/v4.114.0/PRE_PANEL_AUDIT.md` (19-claim fact-check), 7 reviewer files, `README.md` verdict summary. **v4.114.1 patch scope (~50 lines across 4 files)**: (HIGH) rename v4.112.0 "fixed-point verification" → "divergence analysis + byref fix" in CLAUDE.md + v4/README.md because the 3-stage script fails at Stage 1 on Sh.8; (HIGH) commit `tests/bootstrap/byref_test.mn` reproducing the v4.112.0 acceptance case instead of leaving it in `/tmp/`; (LOW) add cleanup-intent comment at `__mn_coro_register_wait` overflow site in `mapanare_runtime.c`. **Phase E deferred findings**: A.1 self-hosted pipeline CI gate (carry-forward v4.106.0), A.2 fixed-point CI red (Sh.8-blocked), B.1 async error-site reachability tests, Co.1 pre-existing user-code coroutine leaks, Instr.1 Culebra scan gap (three panels blocked). **Golden tests: 26/64 self-hosted preserved, 63/64 Python-bootstrap (pre-existing `51_match_guards_and_or`); valgrind 0 errors and ASan 0 errors on async + struct subset; byte-for-byte memory-neutral confirmed vs HEAD~4 control.** **Next: v4.114.1 patch then delta panel (Rattler + Cobra + Anaconda); if delta clears 8.5, Phase E opens at v4.115.0.**
- **v4.113.0** (shipped) — **Phase D release 3: last v4.99.0 docket items closed (#8, #10, #11).** Zero open items from the v4.99.0 panel after this release. **Docket #8 (MEDIUM, coroutine frame)**: `mn_coro_is_done` / `mn_coro_resume` in `runtime/native/mapanare_runtime.c` replaced raw `*(void**)handle` casts with a named `mn_coro_frame_prefix_t` struct documenting the LLVM switched-resume ABI (resume_fn at offset 0, destroy_fn at offset sizeof(void*)). Behaviourally equivalent — the cast compiles to the same load — but one named definition to update if the ABI ever moves. Verified byte-for-byte memory-neutral: `valgrind` output on 56/57 against a HEAD~4 control rebuild matches exactly (same leak sites in user coroutine bodies, not in our functions). All 3 async goldens still produce 42/43/110. **Docket #10 (LOW, SPEC keywords)**: new `docs/SPEC.md` §2.1.1 "Reserved Keyword Master List" — 42-row alphabetical table of every hard-reserved identifier with English/Spanish/category/AST role. Cross-references `mapanare/mapanare.lark:380-427` and `mapanare/self/lexer.mn:59-177`; audit recorded in `keyword-audit.md`. Stale "Soft-reserved (v4.30.0): async, await" text replaced — async/await have been hard keywords since v4.68.0/v4.72.0. Appendix C rewritten to distinguish future-reserved from hard-reserved; `continue` and `const` rows removed (both already tokenized). **Docket #11 (LOW, async errors)**: 5 async failure sites with silent-drop or NULL-deref behaviour replaced with specific stderr + deterministic exit(1): `__mn_coro_scheduler_init` checks every `pthread_create` return (names worker K of N + strerror — previously silently started fewer threads than reported and then hung); `__mn_coro_scheduler_register` refuses enqueue when scheduler uninitialised (previously span forever in zeroed deque) or when deque+overflow both full (previously dropped task but kept active_tasks counter); `__mn_coro_register_wait` bails on overflow-full with coroutine handle + Future address (previously a suspended await would never resume); `__mn_file_read_async` checks calloc + malloc + pthread_create individually. Site #2 manually triggered in isolation (exit 1 with the named message); remaining 4 require env stress. Added `#include <errno.h>`. **Golden tests: 26/64 preserved** (identical to v4.112.0, zero regressions); stage2 0/11 unchanged (pre-existing Sh.8 gap). 9/9 exit criteria green. **Next: v4.114.0 is the Phase D panel — 7 reviewers grade v4.111.0-v4.113.0.**
- **v4.112.0** (shipped) — **Phase D release 2: fixed-point verification + docket #7 closed.** Ran the 3-stage fixed-point script; classified divergences across 4 categories in `docs/roadmap/v4/v4.112.0/DIVERGENCE_ANALYSIS.md` (byref / structural / cosmetic / semantic-gap); closed docket #7 (byref size heuristic) via a single-file fix in `mapanare/self/emit_llvm.mn`. Added `struct_byte_size(st, ty)` resolving `%struct.Foo` through the registered `st.structs` table, returning real sizes computed from the inline `{...}` form — matching the Python bootstrap's `_tsz` algorithm at `emit_llvm_text.py:141`. Added `is_byref_type_st(st, ty)` as the state-aware replacement; all 7 call sites of the old `is_byref_type` updated to pass state. **Verified fix on `/tmp/byref_test.mn`**: 16-byte `Small` now passed by value (`%struct.Small %s`); 80-byte `Large` still by reference (`ptr %l.byref`); output correct; IR validates; pipeline runs. **Golden tests: 26/64 preserved** (zero regressions from v4.111.0). **Fixed-point convergence (stage2 == stage3) NOT measured** — stage1 can't self-compile because self-hosted `semantic.mn` doesn't register `None` as a constructor (pre-existing gap surfaced in v4.111.0's stage2 validation; Python bootstrap bypasses via `skip_check=True` in `build_stage1.py`). New docket **Sh.8** opened for self-hosted `None`/`Some`/`Ok` constructor registration. Docket Sh.3 CLOSED. 6/10 PLAN.md exit criteria green, 4/10 blocked on Sh.8 or culebra's long-running scan on 854K-line IR. **Next: v4.113.0 closes remaining v4.99.0 panel items (#8 coroutine frame, #10 keyword collision SPEC, #11 async errors). v4.114.0 is the Phase D panel.**
- **v4.111.0** (shipped) — **Phase D release 1: self-hosted golden test parity.** First Phase D release (self-hosted compiler maturity). Rebuilt `mnc-stage1` from the full self-hosted pipeline (`mapanare/self/*.mn`, 38,824 lines); ran all 64 golden tests; documented every failure with root-cause categorization across 9 categories in `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`. **Disabled 4 v4.97.0 MIR optimization passes** in `mapanare/self/mir_opt.mn::optimize_mir()` — `strength_reduce_function`, `inline_small_functions`, `licm_function`, `escape_analysis_function` — all zero-ROI per v4.109.0's forensics (LLVM subsumes the work at -O2), all flagged by v4.105.0's valgrind sweep (`mir_opt__block_successors` a 14× hot-frame). Single-file, 34-line diff. **Golden pass rate: 21/64 → 26/64** (+5 unblocks: 05_for_loop, 11_closure, 22_string_builder, 24_enum_methods, 25_fizzbuzz, 50_match_or_patterns). Effective rate **39/64** when counting Category A (13 tests that compile correctly but differ in function count from bootstrap because bootstrap still inlines; semantically equivalent IR). Remaining 25 real failures: 10 `__mn_str_starts_with` crashes in `emit_mir_call+0x23515` (docket Sh.2), 5 async-missing (Sh.4), 5 tensor-missing (Sh.6), 2 const-missing (Sh.5), 2 `lower_expr` crashes, 1 or-pattern (bootstrap also fails), 1 closure-typed (Sh.7), 1 gpu-tensor. Stage2 self-compilation: 0/11 modules (expected, Phase D2-3 target). `ir_doctor.py` `_FN_RE` regex flagged as harness gap (doesn't parse inline attribute syntax — produces false "0 functions" readings on self-hosted output). Dockets Sh.1-Sh.7 open for v4.112.0+. **v4.112.0 runs fixed-point verification; byref size heuristic (self-hosted emitter returns 256 for all named structs, docket Sh.3) is the known blocker.**
- **v4.110.0** (shipped) — **Phase C release 4 (final): full benchmark refresh with all fixes applied.** Pure measurement; zero code changes. Phase C closes. Publishes `benchmarks/PHASE_C_RESULTS.md` as canonical performance document, superseding `FINAL_REPORT.md` (v4.98.0) and `FULL_COMPARISON.md` (v4.107.0). **Geomeans across 5 correct workloads: 50× faster than Python, 1.06× slower than Rust (effectively on par), 2.10× slower than Go, 4.85× slower than C (gcc -O2)** — down from v4.107.0's 9.5× vs C, a 2× narrowing driven entirely by v4.108.0's StringBuilder fix (`string_concat` 94.57 → 1.36 ms, 70× speedup, 109× memory reduction). v4.82.0 cumulative geomean: **1.821×** (5 optimizer programs; string_concat's 75× carries it). v4.107.0 same-harness control confirms all non-string benchmarks are within ±5% noise; the v4.98.0 → v4.110.0 "regressions" on sub-millisecond benchmarks are harness-methodology artifacts (v4.98.0 lacked `/usr/bin/time -v` wrap; added in v4.107.0). `struct_alloc` Mapanare beats Rust 0.71× (arena vs Drop); `prime_sieve` ties Rust exactly (3.43 ms each); `enum_match` 22× slower than C confirms Rt.1 boxed-enum overhead is the largest remaining opportunity. `quicksort` checksum fails (docket Qs.1, `List<Int>` indexing). README performance section rewritten against current numbers. New dockets: Qs.1, Rt.1, TBAA.1, willreturn.1 carry forward to v4.111.0+. **Phase C complete. v4.111.0 opens Phase D: self-hosted compiler maturity.**
- **v4.109.0** (shipped) — **Phase C release 3: Arcs 11–12 optimizer ROI forensics.** Pure investigation, zero code changes. Answers why `TOTAL_RESULTS.md` showed 0.992× geomean at -O2 after 8 releases of optimizer work: the geomean hid heterogeneity. Per-workload: matmul_naive +24% (real Arc 11 win), quicksort +9% (near noise), fib 0% (within noise at any scale — H2 rejected via fib(45)), string_concat **−21%** (Arc 11 hints HURT after v4.108.0 — `willreturn` on `__mn_sb_*` declarations blocks DSE of stores the call observes). Per-hint discoveries: (1) **TBAA metadata is 100% dead** — defined in module header at `emit_llvm_text.py:910-926` but never attached to any load/store across all 4 optimizer benchmarks; the comment at line 913 describes intended wiring that was never written; Arc 11's TBAA contribution to alias analysis is exactly zero. (2) **Function attributes on runtime-call declarations** (`nounwind`, `willreturn`, `readonly`, `noalias`) are the *load-bearing* Arc 11 contribution — they cross pass boundaries via LLVM's module-level attribute table and change downstream decisions (early-cse, licm, mldst-motion, dse) without being consumed inline by any single pass. (3) **Inline `nsw`/`nuw` flags are mostly redundant** — LLVM independently infers all 13 `nuw` on matmul post-O2 even when the frontend strips them. Per-pass H3 subtly confirmed: zero instruction-level diffs from any of 10 LLVM passes (instcombine, indvars, licm, gvn, sroa, loop-vectorize, loop-unroll, early-cse, function-attrs, aggressive-instcombine) on hinted vs stripped input; matmul's 24% win is pass-ordering interaction through the attribute table. Published `benchmarks/optimizer/OPT_ROI_ANALYSIS.md` (264 lines). New dockets for v4.110.0+: TBAA wiring decision (remove or connect), `willreturn` audit on heap-modifying runtime calls in `RUNTIME_FN_ATTRS`, escape-analysis codegen wiring. Docket **Qs.1** (`List<Int>` indexing) carries forward.
- **v4.108.0** (shipped) — **Phase C release 2: string_concat fix — auto-StringBuilder — beats Python.** The one embarrassing number from v4.107.0's `FULL_COMPARISON.md` (94.57 ms, 9.8× slower than Python) is fixed. **55× faster wall (1.72 ms), 109× less memory** (2.3 MB vs 246 MB). Phase 1 audit found v4.95.0's `string_concat_optimization` MIR pass has been dead code for 13 versions — matched `Call("__mn_str_concat", ...)` but the MIR shape is `BinOp(ADD, String, String)` + `Copy(dest=lhs, src=binop.dest)` (the runtime call only appears during LLVM IR emission at `emit_llvm_text.py:2658`). Pass rewritten in `mapanare/mir_opt.py:string_concat_optimization` against the real pattern; it performs a CFG rewrite inside natural loops (single preheader + single exit, no other uses of the accumulator in the loop body), inserting `__mn_sb_new` in the preheader, replacing `BinOp + Copy` with `__mn_sb_append`, and prepending `__mn_sb_finish` to the exit block. Two new scalar-pointer runtime wrappers (`__mn_sb_new` + `__mn_sb_finish`) added because v4.95.0's `__mn_sb_create` returned a 24-byte struct by value (sret ABI) which the emitter's auto-declare path mis-typed — same bug silently broke `stdlib/ai/llm.mn` and `embedding.mn`'s explicit `sb_create`/`sb_to_string` builtins for 13 versions; lowering retargeted. Mapanare on string_concat: 5.6× faster than Python, 29× faster than Go, ~12% slower than Rust. Geometric mean across 4 correct non-DCE'd workloads: 9.5× slower than C gcc (v4.107.0) → **6.5× slower**. Other 5 workloads within run-to-run noise (no regressions). Golden tests 63/64 (pre-existing `51_match_guards_and_or`). Docket **Qs.1** (`List<Int>` indexing) carries forward.
- **v4.107.0** (shipped) — **Phase C release 1: cross-language benchmark surface.** Pure measurement; zero Mapanare code changes. 12 new benchmark programs (6 Go at `benchmarks/cross_language/go/`, 6 C at `benchmarks/cross_language/c/`) + rewritten harness `run_benchmarks.py` publish the full six-column comparison across C (gcc -O2), C (clang -O2), Rust -O, Go, Mapanare O2, Python 3.12 across 6 workloads (fib_recursive, quicksort, struct_alloc, enum_match, prime_sieve, string_concat). 10 runs per config, median of middle 8, `/usr/bin/time -v` wraps every run for accurate per-process peak RSS (fixes the `getrusage(RUSAGE_SELF).ru_maxrss` COW-fork inflation bug). **Geometric mean** across 4 correct non-DCE'd workloads: Mapanare is **9.5× slower than C gcc**, **on par with Rust on pure compute** (fib 1.13×, prime_sieve 1.68×), **1.3× slower than Go**, **44.6× faster than Python**. enum_match 27× slower confirms v4.106.0's **Rt.1** boxed-enum overhead. string_concat 1278× slower than C gcc (2× slower than Python!) is v4.108.0's StringBuilder target. 35/36 cells correct; strict checksum check (v4.107.0 tightened from v4.98.0's prefix-match) surfaced a pre-existing **`List<Int>` indexing bug** — `arr.push(42); print(str(arr[0]))` prints `<?>`. Docket **Qs.1** for v4.108.0+. Report: `benchmarks/cross_language/FULL_COMPARISON.md`.
- **v4.106.0** (shipped) — **Phase B panel: NEEDS WORK → v4.106.1 patch.** 7 reviewers graded v4.100.0–v4.105.0. **Aggregate 7.87/10** (+1.28 vs v4.99.0's 6.59, largest since v4.31.0 recovery close). Zero NEEDS WORK, 1 PASS (Boa 8.5), 6 PASS WITH NOTES (Rattler/Viper/Anaconda/Cobra/Coral/Mamba at 7.5-8.0). Below 8.0 threshold → v4.106.1 patch. All 5 v4.99.0 critical/high docket items CLOSED with evidence. **Load-bearing panel finding**: Rattler's IR inspection re-classified the `64_closure_typed` `-O2` miscompile from "LLVM opt bug" (my PRE_PANEL_AUDIT's initial read) to **Mapanare emitter bug** — 2-arg lambda emits `define internal void @lambda4(ptr, ptr, ptr)` while caller does `call i64 %cfn(ptr, i64, i64)`; opaque-pointer LLVM 18 accepts the mismatch silently. Promoted Cl.1 → Rt.1 HIGH. v4.106.1 narrow scope: **2 HIGH items** — Rt.1 (emitter signature fix) + Rt.2/Ih.1 (integration harness stdout-diff against bootstrap reference). Everything else (`As.1`, `Cb.1`, 12 Vg./As./Div./Rt./Cb./Co./Bo./Vp. items) deferred to Phase C (v4.107.0+). Re-panel Rattler/Anaconda/Coral after patch; if PASS, Phase B closes and Phase C (benchmarks) opens.
- **v4.105.0** (shipped) — Phase B release 2 (debugging infrastructure). Valgrind over all 64 goldens (0 CLEAN / 28 WARNINGS_ONLY / 36 ERRORS — top frames `mir_opt__block_successors` 14×, `__mn_list_free` 12×, `emit_llvm__emit_mir_call` 11×). ASan: 21 CLEAN / 17 ASAN_ERROR (12 heap-UAF in `mn_list_rc`, 5 global-buffer-overflow in `strtoll` on non-NUL-terminated IR globals). TSan: **3/3 async goldens race-free**; compiler-side flagged legacy `crash_handler` in `mnc_main.c` as async-signal-unsafe — Phase 4 fixes it with `__mn_install_crash_handler` + thread-local `__mn_set_current_source` breadcrumb (`[CRASH] SIGSEGV during compile at tests/golden/X.mn`). `.github/workflows/sanitizers.yml` (3 jobs) + baseline-checker scripts gate the regression surface. 10 new docket items (`Vg.1`–`Vg.7`, `As.1`–`As.3`) for v4.106.0 panel. 21/64 stage1 goldens unchanged from v4.104.0 (no regressions).
- **v4.104.0** (shipped) — Phase B release 1 (rebuild + verify). Zero code changes. `mnc-stage1` rebuilt cleanly at `-O2` (857k IR lines, 3.5 MB stripped, 1m21s). Full integration pipeline (`emit → llvm-as → opt -O2 → llc → clang → run`) passes **60/64** goldens; 2 skips (stdin/network); 2 FAILs (`51_match_guards_and_or` or-pattern rejection; `47_try_operator` emits invalid IR — 17-version latent bug caught by new `llvm-as` gate). Async goldens 55/56/57 all run natively (42/43/110) and valgrind clean. 21/64 through `mnc-stage1` unchanged from v4.103.0 (no regressions from Phase A). 5 divergence docket items (`Div.1`–`Div.5`) filed for v4.106.0 panel.
- **v4.103.0** (shipped) — Phase A release 4 (final). **Phase A COMPLETE** — all 5 critical/high docket items from the v4.99.0 panel are closed. Docket #4 (else/sino) fixed via deeper drop-glue discovery: `_emit_drop_glue_boxed` was freeing boxed-enum payloads reachable through the returned value but beyond `_extract_ret_ptrs`'s struct-walking reach; conservative skip when return has any ptr field. Docket #5 (closure types) fixed via 3 changes in `lower.py`: FnType → MIRType(FN), typed-var calls → ClosureCall, all lambdas → ClosureCreate. Golden tests 16/62 → 21/64 (5 unrelated passes from the boxed-drop fix). Next panel: v4.106.0.
- **v4.102.0** (shipped) — Phase A release 3. First native async run in project history. Two bugs fixed: `mn_coro_is_done` checked wrong frame offset (now `handle[0] == NULL` per LLVM 18's final-suspend lowering); `_do_block_on` reloaded the coroutine handle from a Future slot the coroutine overwrites with its return value (now reuses the cached handle). All 3 async goldens (55/56/57) run natively with expected outputs (42, 43, 110); valgrind clean; CI step added. Dockets #3 + #6 closed.
- **v4.101.0** (shipped) — Phase A release 2. Self-hosted emitter output corruption fixed: root cause was use-after-free drop glue in the Python emitter — heap strings pushed into lists / stored as struct fields were being freed at function return even though the container held live pointers to them. Six call sites in `mapanare/emit_llvm_text.py` gained move-semantics (`_move_resource`). `mnc-stage1` now emits clean, `llvm-as`-valid IR. Golden tests: 0/61 → 16/62. Dockets #1 + #2 closed.
- **v4.100.0** (shipped) — Phase A release 1. Tagged-pointer UB structurally removed via `MnString` bitfield (`len:63, is_heap:1`), ABI preserved at 16 bytes. `mnc-stage1` output corruption persists and is confirmed pre-existing (not caused by the UB); deferred to v4.101.0.
- **v4.99.0** (shipped) — Arc 14 panel: 6.59/10, Option B. v5 NOT tagged. Tagged-pointer UB, list indexing, async linking must be fixed.
- **v5.0.0** (when ready) — Major version tag. The lead's call. Zero additional work required — v4.76.0 is release-gate quality.

See `docs/roadmap/ROADMAP.md` for the full roadmap. Organized by era: `docs/roadmap/v0/` through `docs/roadmap/v4/`.

## Pre-Push Validation (MANDATORY)

**Before ANY commit or push**, run the full validation suite. This mirrors CI exactly and writes results to `error.log`:

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT emission (runs once)
.\dev.ps1 validate         # Same as above (default mode), runs once and exits
.\dev.ps1 validate -Watch  # Validate then watch for changes
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only (black + ruff + mypy)
.\dev.ps1 fmt              # Auto-format (black + ruff --fix)
.\dev.ps1 e2e              # End-to-end tests only
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for all `examples/wasm/*.mn` files — this is what catches WASM CI failures locally. Running just `pytest` is NOT sufficient; the WASM cross-compilation step in CI compiles those examples and will fail independently of pytest.

**Quick partial checks** (use these during development, but always run full validate before pushing):

```bash
# WASM emission only (fast, catches the most common CI-only failures)
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
python -m mapanare emit-wasm examples/wasm/wasi_app.mn -o /dev/null

# Lint only (no tests)
black --check . && ruff check . && mypy mapanare/ runtime/

# Single test file
pytest tests/semantic/test_types.py -v

# Single test directory
pytest tests/parser/ -v
pytest tests/llvm/ -v
pytest tests/wasm/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v (add -n auto for parallel)
make lint             # ruff check . && black --check . && mypy mapanare/ runtime/
make fmt              # black . && ruff check --fix .
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches and egg-info

# Run specific tests (always use -n auto for parallel execution via pytest-xdist)
pytest tests/parser/ -v -n auto              # Parser tests only
pytest tests/semantic/test_types.py -n auto  # Single test file
pytest tests/llvm/ -v -n auto               # LLVM emitter tests
pytest tests/bootstrap/ -v -n auto           # Self-hosted compiler tests

# Golden test harness (native compiler validation)
python scripts/test_native.py                                    # Bootstrap-only (Windows)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1  # Compare with native (WSL)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run  # Also run IR via lli
python scripts/test_native.py --bless                            # Regenerate reference files
python scripts/test_native.py --filter fib -v                    # One test, verbose

# Rebuild cycle (WSL) — one command for the full edit-compile-test loop
bash scripts/rebuild.sh              # concat + build + golden (default)
bash scripts/rebuild.sh quick        # concat + build only (fast iteration)
bash scripts/rebuild.sh full         # concat + build + golden + selftest + memory
bash scripts/rebuild.sh audit        # concat + build + audit main.ll
bash scripts/rebuild.sh worklist     # concat + build + show alloca alias work queue

# IR Doctor — per-function diagnostics for the self-hosted compiler
# Detects: ALLOCA_ALIAS (real vs mitigated), EMPTY_SWITCH, RET_TYPE_MISMATCH,
#          MISSING_PERCENT, DUPLICATE_CASE, PHI_UNDEF_REF, LOOP_PUSH, etc.
# Saves baselines to .ir_doctor/ — reruns show delta (fixed/new/regressed)
python scripts/ir_doctor.py audit mapanare/self/main.ll              # Audit + baseline + llvm-as
python scripts/ir_doctor.py --only lower__ audit mapanare/self/main.ll  # Audit specific module
python scripts/ir_doctor.py worklist mapanare/self/main.ll           # Functions needing recursive rewrite
python scripts/ir_doctor.py extract mapanare/self/main.ll lower__lower_match  # Dump one function's IR
python scripts/ir_doctor.py check file.ll                            # Just llvm-as validation
python scripts/ir_doctor.py golden                                   # Fresh compile+validate ALL golden (WSL, no cache)
python scripts/ir_doctor.py selftest                                 # Self-compile mnc_all.mn (WSL)
python scripts/ir_doctor.py memory                                   # Memory scaling test (WSL)
python scripts/ir_doctor.py table mapanare/self/main.ll              # Per-function metrics table
python scripts/ir_doctor.py --top 15 table mapanare/self/main.ll     # Top 15 largest functions
python scripts/ir_doctor.py fingerprint mapanare/self/main.ll        # JSON per-function hashes
python scripts/ir_doctor.py diff tests/golden/07_enum_match.mn       # Bootstrap vs stage1 (WSL)
python scripts/ir_doctor.py diff-ir a.ll b.ll                        # Compare two .ll files
python scripts/ir_doctor.py valgrind tests/golden/11_closure.mn       # Auto-run valgrind + map crash to fields (WSL)
python scripts/ir_doctor.py valgrind 11_closure.mn --struct EmitState  # Map against a different struct
python scripts/ir_doctor.py structmap LowerState                     # Show struct byte layout + field names
python scripts/ir_doctor.py structmap LowerState --offset 176        # What field is at byte 176?
python scripts/ir_doctor.py structmap                                # List all structs with sizes
python scripts/ir_doctor.py journal                                  # View debug history (runs + notes)
python scripts/ir_doctor.py note "tried X, result was Y"             # Add note to debug journal
python scripts/ir_doctor.py diff-all                                 # All golden tests (WSL)
python scripts/ir_doctor.py snapshot                                 # Generate .stage1.ll files (WSL)
python scripts/ir_doctor.py stage2                                   # Compile self-hosted modules through mnc-stage1, validate stage2 IR
python scripts/ir_doctor.py stage2 --timeout 60                      # With longer timeout
python scripts/ir_doctor.py valgrind-map ./mapanare/self/mnc-stage1 tests/golden/07_enum_match.mn  # Run valgrind and map crash offsets to struct fields
python scripts/ir_doctor.py valgrind-map --struct LowerState ./mnc some_file.mn  # Map against specific struct
python scripts/ir_doctor.py valgrind-map --timeout 60 ./my_binary --flag arg     # With timeout
python scripts/ir_doctor.py strings mapanare/self/main.ll                        # Validate string constant byte counts
python scripts/ir_doctor.py strings mapanare/self/main.ll -v                     # Also show duplicate strings
python scripts/ir_doctor.py xray                                                 # Full stage2 build + runtime test
python scripts/ir_doctor.py xray --timeout 60                                    # With longer timeout
python scripts/ir_doctor.py phi-check /tmp/stage2.ll                             # Validate PHI fix preserves structure

# MIR Trace — debug type inference issues in the Python lowerer
python scripts/mir_trace.py tests/golden/10_result.mn divide         # Trace types for one function
python scripts/mir_trace.py tests/golden/07_enum_match.mn            # Trace all functions in file
python scripts/mir_trace.py tests/golden/10_result.mn divide -v      # Verbose (all instructions)
python scripts/mir_trace.py tests/golden/10_result.mn divide --json  # JSON output
python scripts/mir_trace.py tests/golden/10_result.mn divide --compare  # Compare MIR vs stage1 IR

# Self-hosted compiler build + fixed-point (WSL/Linux only)
python scripts/build_stage1.py                   # Build mnc-stage1 from Python bootstrap
bash scripts/verify_fixed_point.sh               # 3-stage self-compilation verification
bash scripts/verify_fixed_point.sh --keep        # Keep intermediate IR for debugging

# Culebra v2.0.0 — compiler diagnostics for LLVM IR AND C source (Rust, installed in WSL)
# 29+ YAML templates across ABI, IR, Binary, Bootstrap categories. Nuclei-style pattern engine.
# Repo: C:\Users\Juan\Documents\GitHub\Culebra (also at github.com/Mapanare-Research/Culebra)
# crates.io: https://crates.io/crates/culebra

# --- Core scanning ---
culebra scan mapanare/self/main.ll                          # Run all templates against IR
culebra scan mapanare/self/main.ll --tags abi               # ABI checks only
culebra scan mapanare/self/main.ll --severity critical      # Critical findings only
culebra scan mapanare/self/main.ll --id option-type-pun-zeroinit  # One specific template
culebra scan mapanare/self/main.ll --autofix --dry-run      # Preview auto-fixes
culebra scan mapanare/self/main.ll --autofix                # Apply auto-fixes
culebra scan mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Cross-ref IR vs C structs
culebra scan mapanare/self/main.ll --format json            # JSON output
culebra scan mapanare/self/main.ll --format sarif           # SARIF for GitHub Code Scanning

# --- AI-optimized debugging (v0.3.0) ---
culebra triage mapanare/self/main.ll                        # Group findings by root cause, deduplicate
culebra triage mapanare/self/main.ll --format json          # Structured JSON for AI consumption
culebra compare stage1.ll stage2.ll --metric calls          # Per-function metric comparison (flags drops)
culebra compare stage1.ll stage2.ll --metric pushes --threshold 0.5  # Custom metric + threshold
culebra explain stage2.ll return-type-divergence            # Show matched IR in context + remediation
culebra explain stage2.ll option-type-pun-zeroinit --function parser  # Scoped to one function
culebra bisect stage1.ll stage2.ll                          # Find divergent functions ranked by impact
culebra bisect stage1.ll stage2.ll --top 30                 # Show more results
culebra verify stage2.ll return-type-divergence             # PASS/FAIL — verify a fix worked
culebra verify stage2.ll break-inside-nested-control --function tokenize  # Scoped verify

# --- C backend scanning (v2.0.0) — scan generated C for Mapanare v3.0.0 ---
culebra scan stage2.c                                       # Auto-detects .c, runs 8 C-specific templates
culebra scan stage2.c --tags c                              # C templates only
culebra scan stage2.c --id switch-no-break                  # Check for switch fallthrough
culebra scan stage2.c --id missing-typedef                  # Find undefined struct types
culebra diff stage1.c stage2.c                              # Fixed-point: compare C text output
culebra triage stage2.c --brief                             # Quick C summary
culebra summary stage2.c                                    # Full diagnostic (works for .c and .ll)
# C templates: switch-no-break, missing-typedef, null-deref-pattern, goto-dead-label,
#   union-tag-mismatch, large-struct-by-value, missing-return, buffer-overflow-pattern

# --- Debugging feedback loop (v1.2.0) — wrap commands, learn patterns, track journal ---
culebra wrap -- clang -c -O1 stage2.ll -o stage2.o          # Proxy command + log to .culebra-session.jsonl
culebra wrap -- valgrind /tmp/mnc-stage2 /tmp/tiny.mn        # Captures crashes, errors, output
culebra wrap -- llvm-as stage2.ll -o /dev/null               # Log LLVM errors for analysis
culebra learn                                                # Analyze session logs → extract error patterns + suggest templates
culebra learn -v                                             # Verbose: show individual failure details
culebra journal add "State doesn't persist in emit_instr" --action bug --tags "option,state" --function emit_instr
culebra journal add "Fixed MIRFunction field indices" --action fix --tags "field-index"
culebra journal add "mnc-stage2 runs!" --action milestone
culebra journal show                                         # View timeline of bugs/fixes/milestones
culebra journal show option                                  # Search journal by keyword

# --- Semi-dynamic analysis (v1.1.0) — call functions, probe values, test returns ---
culebra eval main.ll --function hardcoded_field_index --arg '"VarInfo"' --arg '"value"'  # Call and print return
culebra eval main.ll --function find_field_index --arg 0 --arg 0      # Integer args
culebra probe stage2.ll --function lower_fn --watch '%state'           # Inject printf, compile, run
culebra probe stage2.ll --function lower_fn --stop-at if_merge         # Stop at specific block
culebra test-fn main.ll --function hardcoded_field_index --arg 0 --arg 0 --expect-ret 1  # Unit test: PASS/FAIL

# --- Summary (v1.0.0) — one command for everything ---
culebra summary stage2.ll                                   # Scan + Types + Fields + Health + Score in 5 lines
culebra summary stage2.ll --struct LowerState               # Filter health to one struct

# --- Type inference + field audit (v0.9.0) — auto-generate types, detect index-0 bug ---
culebra infer-types stage2.ll                               # Infer missing type defs from insertvalue chains
culebra infer-types stage2.ll --ll                          # Output as valid LLVM IR (paste into file)
culebra field-index-audit stage2.ll                         # Find structs where ALL accesses use index 0
culebra field-index-audit stage2.ll --struct-filter LowerState  # Check specific struct

# --- Display + Inspection (v0.8.0) — syntax-highlighted IR, variable dumps, block walk ---
culebra pretty stage2.ll                                    # Module overview: stats, types, function size bars
culebra pretty stage2.ll --function lower_fn                # Syntax-highlighted IR with colored types/labels/terminators
culebra dump stage2.ll --function lower_fn                  # Variable dump: allocas, types, sizes, def-use counts, PHIs
culebra dump stage2.ll --function lower_fn -v               # Verbose: also show GEP chains
culebra inspect stage2.ll --function lower_fn               # Block-by-block control flow walk
culebra inspect stage2.ll --function lower_fn --block if_alpha  # Detail view of one block
culebra stacktrace crash.log --ir stage2.ll                 # Parse valgrind/ASAN/gdb output, map to IR

# --- Missing types (v0.7.0) — find undefined struct/enum types blocking compilation ---
culebra missing-types stage2.ll                             # Find all undefined named types
culebra missing-types stage2.ll -v                          # Also show which functions reference each

# --- Call graph + progress (v0.6.0) ---
culebra callchain stage2.ll --from lower --to current_block_terminated  # Find call paths between functions
culebra callchain stage2.ll --from lower_fn --to add_block --depth 5   # Shows struct types along chain
culebra progress stage2.ll                                              # IR stats + findings + health score
culebra progress stage2.ll -b my-baseline.json                         # Also compare against baseline

# --- Crash debugging (v0.5.0) — offset mapping, variable tracing, struct health ---
culebra crashmap stage2.ll --offset 0x20 --struct FnDefData  # "0x20 = field 4 (name: {ptr, i64})"
culebra crashmap stage2.ll --offset 0x20                     # Check all structs for that offset
culebra crashmap stage2.ll                                   # List all struct types with sizes
culebra trace stage2.ll --function lower_fn --var '%state'   # Follow variable through basic blocks
culebra trace stage2.ll --function tokenize --var '%pos'     # Shows every load/store/phi/call
culebra health stage2.ll --struct LowerState                 # PHI zeroinit, type-pun, null loads
culebra health stage2.ll                                     # Check all structs
culebra suggest stage2.ll --function lower_definition        # Prioritized fix suggestions for a function

# --- Baseline tracking (v0.4.0) — track progress across fix iterations ---
culebra baseline save stage2.ll                             # Save current findings as baseline
culebra baseline diff stage2.ll                             # Compare current scan vs baseline (Fixed/New/Remaining)
culebra baseline diff stage2.ll -b my-baseline.json         # Compare against specific baseline file

# --- Template assertions (v0.4.0) — CI gates and regression tests ---
culebra lint-template stage2.ll return-type-divergence --expect   # FAIL if template doesn't fire
culebra lint-template stage2.ll option-type-pun-zeroinit --reject # FAIL if template fires (regression)

# --- Triage --brief (v0.4.0) — minimal output for AI token efficiency ---
culebra triage stage2.ll --brief                            # One line: "9 root causes, 31 findings: ..."

# --- Diagnostic map (symptom → templates) ---
culebra map crash                                           # "what could cause this crash?"
culebra map "type mismatch"                                 # Search by symptom keyword
culebra map "zero tokens"                                   # Maps to relevant templates
culebra map phi                                             # PHI-related issues

# --- Drain queue (Mapanare integration) ---
culebra drain .culebra-queue.yaml                           # Process dynamically-queued checks
culebra drain .culebra-queue.yaml --clear                   # Process and clear queue

# --- IR analysis ---
culebra strings mapanare/self/main.ll                       # Validate [N x i8] byte counts
culebra audit mapanare/self/main.ll                         # Detect IR pathologies
culebra check mapanare/self/main.ll                         # Validate IR with llvm-as
culebra diff stage1.ll stage2.ll                            # Per-function structural diff
culebra extract mapanare/self/main.ll my_function           # Extract one function's IR
culebra table mapanare/self/main.ll --top 15                # Per-function metrics table

# --- ABI + binary ---
culebra abi mapanare/self/main.ll --header runtime/native/mapanare_runtime.c  # Struct layout + sret
culebra binary ./mapanare/self/mnc-stage1 --ir main.ll      # ELF/PE inspection + .rodata cross-ref

# --- Bootstrap pipeline ---
culebra phi-check /tmp/stage2.ll                            # Validate transform preserves IR
culebra pipeline                                            # Run full stage pipeline from culebra.toml
culebra fixedpoint ./mnc-stage1 mapanare/self/mnc_all.mn    # Fixed-point convergence detection

# --- Templates + workflows ---
culebra templates list                                      # List all templates
culebra templates show option-type-pun-zeroinit             # Full template details
culebra workflow bootstrap-health-check --input stage1_output=stage1.ll  # Multi-step validation
culebra workflow playground-mapanare --input stage2_output=stage2.ll     # Playground workflow

# --- Misc ---
culebra watch --patterns '*.ll,*.mn' culebra scan main.ll   # Watch + re-scan on change
culebra test                                                # Run all [[tests]] from culebra.toml
culebra run ./mnc-stage1 test.mn --expect "hello"           # Compile, run, check output
culebra init                                                # Generate starter culebra.toml
```

## Testing the Native Compiler

Golden test corpus lives in `tests/golden/*.mn` (15 programs covering all features). Reference IR in `tests/golden/*.ref.ll`.

**Workflow for debugging mnc-stage1:**
1. Make changes to `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. Rebuild: `python scripts/build_stage1.py`
3. Test: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. The harness compares mnc-stage1 output against the Python bootstrap — shows exactly which functions are missing or different.

Every run auto-updates `tests/golden/BENCHMARKS.md` with per-test metrics (source lines, IR lines, IR size, function count, compile time). Commit this file to track regressions over time.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I rules), **MyPy** strict mode
- Target Python 3.11+ (for bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source → Lark LALR parser → AST (dataclasses) → Semantic checker → MIR lowering → MIR optimizer (O0-O3) → Emitter
                                                                                                                 ├→ emit_llvm_text.py  → LLVM IR (text)
                                                                                                                 ├→ emit_c.py          → C source
                                                                                                                 └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:
- `cli.py` — Entry point, command dispatch (run, build, check, emit-llvm, emit-mir, emit-wasm, fmt, test, lint, doc, deploy, init)
- `parser.py` — Lark transformer: parse tree → AST dataclass nodes
- `ast_nodes.py` — All AST node definitions
- `semantic.py` — Two-pass type checker and scope resolver
- `mir.py` / `mir_builder.py` — MIR data structures and builder
- `lower.py` — AST → MIR lowering (1,397 lines)
- `mir_opt.py` — MIR optimizer passes (constant folding, DCE, copy propagation, block merging)
- `optimizer.py` — AST-level optimizer (constant folding, DCE, agent inlining, stream fusion)
- `emit_llvm_text.py` — LLVM IR generation (text-based)
- `emit_c.py` — C source generation from MIR
- `emit_wasm.py` — WebAssembly (WAT) generation from MIR (v2.0.0)
- `wasm_linker.py` — wasm-ld integration for multi-module WASM linking (v2.0.0)
- `types.py` — **Single source of truth** for the type system (TypeKind enum, TypeInfo, builtin registries)
- `mapanare.lark` — LALR grammar with 13-level precedence climbing
- `tracing.py` — OpenTelemetry-compatible tracing
- `diagnostics.py` — Rust-style structured error output
- `test_runner.py` — Built-in test runner for `mapanare test`
- `deploy.py` — Deployment scaffolding (Dockerfile, health checks)

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`, `result.py`, `deploy.py` — asyncio-based agents, reactive signals, async stream operators, Result/Option types, deployment infrastructure. **Legacy — will be replaced by native .mn stdlib.**

**Native C runtime** (`runtime/native/`): Arena-based memory (no GC), lock-free SPSC ring buffers, thread pool with work stealing, cooperative agent scheduler (mobile), agent lifecycle, trace hooks, TCP sockets, TLS (OpenSSL via dlopen), file I/O, event loop (epoll/select), string interning with configurable cap, memory profiling. Used by the LLVM backend.

## LLVM Backend Status (v2.0.0 — full parity + GPU)

**Working:** Functions, structs, enums, pattern matching, control flow, type inference, generics, Result/Option, print (println deprecated), builtins, lists, maps/dicts (Robin Hood hash table), agents (full lifecycle), signals (full reactivity: computed, subscribers, batched updates), streams (map/filter/take/skip/collect/fold, backpressure), closures (free variable capture via environment structs), traits, module imports, pipes (`|>` for function application), pipe definitions (multi-agent composition), all string methods, GPU kernel dispatch (`@gpu`/`@cuda`/`@vulkan` via MIR GpuKernel metadata → PTX/SPIR-V LLVM codegen).

**Not yet on LLVM:** Tensor reshape, mutable views, stepped slices (v5.x). The tensor surface (literals, indexing, broadcasting, reductions, slicing) is stable as of v4.45.0.

New LLVM features should target `emit_llvm_text.py` (the sole LLVM emitter).

## Type System (mapanare/types.py)

All type definitions, builtin registries, and type-name mappings live in `types.py`:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int, float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare→Python name mapping used by emitters
- `PYTHON_TYPE_MAP`: Type→Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, 14,000+ lines of Mapanare. Mirrors the Python bootstrap pipeline:

| Module | Lines | Role |
|--------|-------|------|
| `ast.mn` | 781 | AST node definitions (structs + enums) + shared constructors |
| `lexer.mn` | 575 | Character-by-character tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser, 13-level precedence |
| `semantic.mn` | 1,729 | Two-pass type checker and scope resolver |
| `mir.mn` | 791 | MIR data structures (types, values, instructions, blocks, module) |
| `lower_state.mn` | 587 | Lowerer state, scope management, lookups, type resolution |
| `lower.mn` | 3,602 | AST → MIR lowering (registration + expression/statement lowering) |
| `emit_llvm_ir.mn` | 258 | LLVM type constants and IR instruction string builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter (state, handlers, module emission) |
| `main.mn` | 537 | Compiler driver |

**Patterns:** Constructor functions (`let r: T = first_field; return r`), state-threading (functions thread state structs), no struct literal syntax in grammar yet.

**Fixed-point verification** blocked by cross-module LLVM compilation (v0.9.0) and enum lowering gaps.

## Key Conventions

- Grammar lives in `mapanare/mapanare.lark` (also bootstrapped copy in `bootstrap/`)
- Emitters detect used features (agents, signals, streams) and import only as needed
- Builtins are dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted compiler sources are in `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Design philosophy: `docs/manifesto.md` | RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs: `docs/roadmap/v0/` through `docs/roadmap/v4/`
- Version tracked in `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

Starting with v0.8.0, the project moves toward Python independence:
- **Stdlib in .mn:** New stdlib modules are written in Mapanare (`.mn`), compiled to native code via LLVM. No more Python `.py` stdlib files.
- **C runtime as foundation:** OS-level primitives (sockets, TLS, file I/O) live in the C runtime. Everything above (HTTP, JSON, routing) is pure Mapanare.
- **Test on LLVM:** Every test should run on the LLVM backend.

## GPU Backend (v2.0.0)

GPU compute via CUDA and Vulkan, loaded dynamically at runtime (no compile-time SDK dependency):
- **C runtime** (`runtime/native/mapanare_gpu.h/.c`): CUDA Driver API + Vulkan compute via dlopen
- **MIR metadata** (`mapanare/mir.py`): `MIRGpuKernel` dataclass with device, PTX/SPIR-V source, grid/block config
- **Lowering** (`mapanare/lower.py`): `@cuda`/`@vulkan`/`@gpu` decorators populate `MIRModule.gpu_kernels`
- **LLVM codegen** (`mapanare/emit_llvm_text.py`): PTX string embedding + `cuModuleLoadData`/`cuLaunchKernel`, SPIR-V byte embedding + Vulkan pipeline create/dispatch
- **Python layer** (`experimental/gpu.py`): Device detection, kernel dispatch abstractions
- **Stdlib** (`stdlib/gpu/`): `device.mn` (GPU detection), `tensor.mn` (GPU-accelerated tensors), `kernel.mn` (kernel management)
- **Annotations**: `@gpu`, `@cuda`, `@metal`, `@vulkan` on functions for automatic dispatch
- **Built-in kernels**: PTX for CUDA, GLSL/SPIR-V for Vulkan (tensor add/sub/mul/div/matmul)

## WebAssembly Backend (v2.0.0)

Compile Mapanare to WebAssembly for browser and server-side execution:
- **Emitter** (`mapanare/emit_wasm.py`): MIR → WAT text format (~2,785 lines)
- **Linker** (`mapanare/wasm_linker.py`): wasm-ld integration for multi-module linking, memory layout, import/export management
- **CLI**: `mapanare emit-wasm [--binary] [--link] [--wasi] source.mn [source2.mn ...]`
- **Targets**: `wasm32-unknown-unknown` (browser), `wasm32-wasi` (server)
- **JS runtime** (`playground/src/wasm-runtime.js`): Browser host for WASM modules
- **Stdlib** (`stdlib/wasm/`): `bridge.mn` (JS interop), `runtime.mn` (WASI + memory)
- **WASI support**: File I/O, environment, clock, random via WASI preview 1

## Mobile Targets (v2.0.0)

Cross-compilation targets for mobile platforms:
- `aarch64-apple-ios` — iOS ARM64
- `aarch64-linux-android` — Android ARM64
- `x86_64-linux-android` — Android emulator

Mobile-specific runtime features:
- **Cooperative agent scheduler** — single-threaded event-driven execution (default on mobile)
- **epoll event loop** — Linux/Android I/O multiplexing (kqueue on iOS deferred)
- **Smaller defaults** — 4KB arenas, 256-slot ring buffers, 64-slot agent queues, 1ms signal batch
- **String interning cap** — 4K entries on mobile vs 64K on desktop
- **Memory profiling** — `mapanare_memory_stats()` for arena/intern/agent usage tracking

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame/data analysis package (pandas+numpy replacement), written in .mn
- `net/crawl` (web crawler), `security/scan` (vulnerability scanner), `security/fuzz` (fuzzer) — all agents-based
- AI/LLM drivers (`stdlib/ai/`): LLM, embeddings, RAG

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — format check (black) → lint (ruff) → type check (mypy) → tests (pytest). Matrix: Python 3.11, 3.12 on Ubuntu.
- **native** — C runtime tests with plain gcc, AddressSanitizer, ThreadSanitizer.
- **wasm** — WASM cross-compilation: emit WAT, convert to WASM via wat2wasm, run WASI examples on wasmtime.
- **android** — Android cross-compilation: NDK setup, ARM64 + x86_64 `.o` generation, ELF format verification.

4,845+ tests across the full pipeline.

## Skills (slash commands)

These are invocable via `/skill-name` in Claude Code:

| Skill | Description |
|-------|-------------|
| `/golden` | Run the 15/15 golden test suite through mnc-stage1 + llvm-as. Shows delta from last run. |
| `/stage2` | Compile all self-hosted modules through mnc-stage1, validate stage2 IR. Tests self-compilation. |
| `/rebuild` | Full rebuild cycle: concat .mn sources → build mnc-stage1 → run golden tests. |
| `/ir-audit` | Audit LLVM IR for known pathologies (ALLOCA_ALIAS, RET_TYPE_MISMATCH, etc.) with baseline tracking. |
| `/valgrind-map` | Run valgrind on crashing binary, map byte offsets to struct fields automatically. |
| `/bump-version` | Bump version across VERSION, README, CHANGELOG, and all localized docs. |
| `/code-review` | Run a full 7-reviewer panel code review of the codebase. |
| `/create-pr` | Generate PR title and description from the current branch's commits. |
| `/simplify` | Review changed code for reuse, quality, and efficiency, then fix issues found. |
| `/autoresearch` | Autonomous experiment loop — iterative research with automatic follow-up. |
| `/culebra-scan` | Run Culebra v2.0.0 — 49 templates (41 IR + 8 C). Auto-detects .ll vs .c. Autofix, SARIF, triage. |
