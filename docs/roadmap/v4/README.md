# v4 — Production, Refactor & Evolution

**Era:** v4.0.0+
**Theme:** Ship it, then fix the foundation, then evolve

---

## Goal

Six phases:

1. **v4.0.0** — Production release. Other people can use it.
2. **v4.1.0-v4.7.0** — Architectural refactor. Fix memory leaks, thread safety, type system, and dead code. No new language features until v4.7.0.
3. **v4.8.0-v4.13.0** — Deep fixes. Workarounds, memory safety, drop glue, MIRType enum, optimizer, Culebra gate.
4. **v4.14.0-v4.17.0** — Final compiler maturity. Fix remaining bugs, complete optimizer, achieve fixed-point bootstrap (Python independence).
5. **v4.18.0-v4.26.0** — Language evolution. Tensor shapes, GPU auto-kernels, reactive async, FFI bindings, `const`. **Panel found 6 hollow features in 8 versions; verdict NEEDS WORK at v4.26.0 (9.79 → ~8.2).**
6. **v4.27.0-v4.31.0** — **Recovery arc.** Five focused versions, zero new features, terminate when next 7-reviewer panel certifies aggregate ≥9.0 with zero NEEDS WORK.

## Headline Techs

- Self-hosted compiler: 15,000+ lines of .mn, 10 modules, fixed-point verified
- 40/40 golden tests, 4,845+ pytest, 9.79/10 code review
- Architectural audit: 21 issues identified, systematic fix plan
- Emitter consolidation: 3 LLVM emitters -> 1 (delete ~8,500 lines)
- Drop glue rewrite: return-value escape analysis replaces `skip_struct_ret`
- Thread safety: signal mutex, atomic counters, COW struct-copy audit
- Type system: UNKNOWN split into UNRESOLVED/ERROR, self-hosted verifier

## Versions

| Version | Codename | Theme | Highlights |
|---------|----------|-------|------------|
| **v4.0.0** | Mapanare | Production Release | Build real programs. Install -> write -> compile -> run. |
| **v4.1.0** | | Ecosystem | Package registry (PostgreSQL, OAuth), version manager, native CI binaries |
| **v4.2.0** | | Clean House | Delete 3 dead emitters + emit_c.mn (~8,500 lines), remove `_coerce_arg`, one pipeline |
| **v4.3.0** | | Drop Glue | Fix `skip_struct_ret`, escape analysis, free string/map/stream/agent temporaries |
| **v4.4.0** | | Thread Safety | Signal free under lock, atomic counters, COW audit, agent lifecycle |
| **v4.5.0** | | Type System | UNKNOWN -> UNRESOLVED/ERROR, wire self-hosted semantic + MIR verifier |
| **v4.6.0** | | Self-Hosted Quality | Replace field tables, MIRType enum, fix workarounds, typed pointers |
| **v4.7.0** | | Optimizer | Unified fixpoint loop (O1+O2 merged) |
| **v4.7.1** | | Verify | WSL rebuild verified: 40/40 golden, 11/11 stage2 |
| **v4.8.0** | | Workaround Fixes | Fix substr bug (4 sites), PHI zeroinit (2), ABI mismatch (2) in emit_llvm.mn |
| **v4.9.0** | | Semantic Safety | Fix semantic.mn memory corruption, re-enable check() in compile() |
| **v4.10.0** | | Drop Glue Complete | Remove skip_struct_ret, add string pooling |
| **v4.11.0** | | Global Constants | Add module-level constant support, MIRType string→enum |
| **v4.12.0** | | Self-Hosted Optimizer | Constant folding, propagation, dead block elimination |
| **v4.13.0** | | Foundation Gate | Culebra clean, valgrind clean, all exit criteria met |
| **v4.14.0** | | Break Fix + 11/11 Stage2 | Fix 3 CRITICAL break-inside-nested-control, fix main.mn stage2 crash, 0 Culebra CRITICAL |
| **v4.15.0** | | Module-Level Let + MIRType Enum | LetDef in AST, top-level `let`, TypeKind enum replaces string-based MIRType.kind |
| **v4.16.0** | | Optimizer Complete | Enable dead block elimination, constant propagation, copy propagation, measure IR reduction |
| **v4.17.0** | | Fixed-Point Bootstrap | mnc-stage1 compiles itself, 3-stage verification, Python bootstrap becomes optional |
| **v4.18.0** | | Tensor Shapes + @gpu Auto-Kernels (claim) | `const` keyword (parser alias for module-level let, reverted v4.27.0), `Tensor<Float>[3,3]` shapes (grammar form; the `Tensor<Float, [3,3]>` form the original CHANGELOG claimed never parsed), `@gpu` decorator (raised `NotImplementedError` at `lower.py:986`, removed v4.27.0) |
| **v4.19.0** | | Reactive Async | async/await tied to Streams, backpressure via ring buffers, cooperative scheduling |
| **v4.20.0** | | Auto-Generated FFI Bindings | `mapanare bind --lang python\|ts\|go` generates bindings from .mn signatures |
| **v4.21.0** | | Optimizer Hardening | Constant folding correctness on loop back-edges, lint cleanup, CI gate |
| **v4.22.0** | | Dead Block Elimination | Fixed-point BFS, PHI-safe removal, SwitchCase fix |
| **v4.23.0** | | MIRType Int Tags | Zero string-based type comparisons, 110+ sites migrated |
| **v4.24.0** | | async/await Wired | Parser + lowerer + emitter in both pipelines, 46th golden test |
| **v4.25.0** | | FFI End-to-End | .mn → .so → Python ctypes calls compiled code; tensor shape checking E2E |
| **v4.26.0** | | `const` Keyword (claim) | Roadmap consolidation; **panel NEEDS WORK** — `const` shipped as parser alias without semantics; 6 hollow features documented across v4.18.0–v4.26.0 |
| **v4.27.0** | | Honesty Recovery (CRITICAL) | Close 8 CRITICAL panel items: FFI argtypes/restype, runtime `-fPIC`, MIR verifier wired into `compile()`, `const` reverted (Path B), `@gpu`/`@cuda`/`@vulkan` removed (Path B), diagnostics consolidated, CHANGELOG corrected |
| **v4.28.0** (planned) | | Concurrency + Carry-forwards | New races (signal/agent/registry); matmul carry-forwards (27 versions overdue); version string regression |
| **v4.29.0** (planned) | | Build Infrastructure + Test Honesty | Orphaned runtime files (1,942 lines); `extern "Python"` decision; CI hollow-feature gate; `verify_fixed_point.sh` teeth |
| **v4.30.0** (planned) | | Codegen + Emitter Carry-Forwards | `await` decision; agent dispatch; optimizer non-convergence ICE; six 7-cycle emitter items |
| **v4.31.0** | | Documentation Truth + Process | SPEC sync (26 versions); CHANGELOG honesty CI; docs-drift CI; **panel: 9.343/10, arc terminates** |
| **v4.32.0** | | Arc-End Panel Closure | Close 9 HIGH/MEDIUM from v4.31.0 panel; zero new features; first post-recovery release |
| | | | |
| | | **Post-Recovery Arcs (v4.33.0 → v4.76.0)** | See `POST_RECOVERY_ROADMAP.md` for individual version details |
| | | | |
| **v4.33.0–v4.36.0** | Arc 1 | Error Handling + Pattern Matching | `?` operator, decision-tree match rewrite, guards + or-patterns. Panel at v4.36.0 |
| **v4.37.0–v4.41.0** | Arc 2 | LSP Maturity | Go-to-def, find-refs, rename, completion, VS Code extension. Panel at v4.41.0 |
| **v4.42.0–v4.46.0** | Arc 3 | Tensor Completeness | Tensor literals, indexing, broadcasting, reductions + slicing. Panel at v4.46.0 |
| **v4.47.0–v4.51.0** | Arc 4 | Stdlib AI/LLM | Unified LLM interface, structured output, embeddings + RAG. Panel at v4.51.0 |
| **v4.52.0–v4.56.0** | Arc 5 | Compiler Debt Drain | Self-hosted semantic wiring (A7), UNRESOLVED/ERROR split (A8), `const` Path A. Panel at v4.56.0 |
| **v4.57.0–v4.61.0** | Arc 6 | Deprecation + Deletion | Python emitter, llvmlite JIT, dead code final pass. Panel at v4.61.0 |
| **v4.62.0–v4.66.0** | Arc 7 | DWARF Debug Info | `DICompileUnit`, `DISubprogram`, line metadata, `llvm.dbg.declare`. Panel at v4.66.0 |
| **v4.67.0–v4.71.0** | Arc 8 | Coroutine Foundation | v4.67.0: DESIGN.md shipped (no code). `async`/`await` grammar + AST, semantic, MIR suspension. Panel at v4.71.0 |
| **v4.72.0–v4.76.0** | Arc 9 | Coroutine Completion | Suspend/resume/destroy, scheduler, `for await`, end-to-end demos. Panel at v4.76.0 |
| | | | |
| | | **Arc 10: Integration Tests + Debt Zero (v4.77.0 →)** | |
| | | | |
| **v4.77.0** | Arc 10 | Integration Test Harness | 58 golden tests through full LLVM pipeline (emit → llvm-as → opt → llc → link → run). 46 pass, 5 xfail, 7 skip. |
| | | | |
| | | **Arc 12: LLVM + MIR Optimization (v4.87.0 →)** | |
| | | | |
| **v4.87.0** | Arc 12 | MIR Function Inlining | Cost-model inlining at O2 (< 20 instr, not recursive), single-block callees only. |
| **v4.88.0** | Arc 12 | Loop Detection + Strength Reduction | Dominators, natural loops, MIRLoop. Strength reduction (mod→AND). LICM built but disabled. |
| **v4.89.0** | Arc 12 | Escape Analysis | Heap-to-stack promotion for non-escaping allocations. 6 escape criteria, known non-capturing function set, 4KB size limit. |
| **v4.90.0** | Arc 12 | Cumulative Benchmark | 4/5 benchmarks within 2x of Rust. fib_recursive 1.1x Rust. string_concat -9.7%. O2 geomean 0.992x, O0 geomean 1.09x. |
| **v4.91.0** | Arc 12 | **Panel: 8.57/10 PASS** | 7 reviewers. All passes correct. Escape analysis emitter gap noted. Arc 12 closes. |
| | | | |
| | | **Arc 13: Structured Concurrency (v4.92.0 →)** | |
| | | | |
| **v4.92.0** | Arc 13 | Real Suspension at Await | coro.suspend replaces inline-resume. C runtime scheduler. Async file I/O. Golden test 58. |
| **v4.93.0** | Arc 13 | Multi-Threaded Scheduler | Chase-Lev work-stealing deques, N worker threads, condvar parking, spawn() builtin. Golden test 59. |
| **v4.94.0** | Arc 13 | Async Benchmark Suite | 5 workloads x 3 languages, harness, Python baselines. Mapanare runtime pending rebuild. |
| **v4.95.0** | Arc 13 | StringBuilder | C runtime StringBuilder (amortized O(1)). Loop-concat MIR pass. AI stdlib refactored. |
| **v4.96.0** | Arc 13 | **Panel: 8.57/10 PASS** | 7 reviewers. Multi-threaded async + StringBuilder validated. Mamba's v4.51.0 finding resolved. Arc 13 closes. |
| | | | |
| | | **Arc 14: Final Panel (v4.97.0 → v4.99.0)** | |
| | | | |
| **v4.99.0** | Arc 14 | **Panel: 6.59/10 NEEDS WORK** | 7 reviewers. Option B: continue v4.100.0+. v5.0.0 not tagged. Tagged-pointer UB, list indexing, async linking identified as v5-blocking. |
| | | | |
| | | **Phase A: Bug Sprint (v4.100.0 →)** | |
| | | | |
| **v4.100.0** | Phase A | Tagged-Pointer UB Fix (partial) | Docket #1: UB structurally eliminated via `MnString` bitfield (`len:63, is_heap:1`). ABI preserved (16 bytes). Self-hosted compiler output still corrupted — confirmed pre-existing, **not** caused by the tagged pointer; deferred to v4.101.0. |
| **v4.101.0** | Phase A | Self-Hosted Emitter Corruption Fixed | Dockets #1 + #2 closed. Python emitter's drop glue was freeing heap strings pushed into lists / stored as struct fields. Six sites in `emit_llvm_text.py` gained move-semantics. `mnc-stage1` now emits clean, `llvm-as`-valid IR. Golden: 0/61 → 16/62. Regression test `62_list_output.mn` added. |
| **v4.102.0** | Phase A | First Native Async Run | Dockets #3 + #6 closed. Two bugs: `mn_coro_is_done` checked wrong frame offset (fixed to `handle[0] == NULL` per LLVM's final-suspend lowering); `_do_block_on` reloaded the coroutine handle from a slot the coroutine overwrites with its return value (fixed to reuse cached handle). All 3 async goldens run natively (42, 43, 110). Valgrind clean. CI step added. |
| **v4.103.0** | Phase A | else/sino + Closure Types; Phase A Complete | Dockets #4 + #5 closed. Drop-glue was freeing boxed-enum payloads reachable only transitively through the returned value — conservative skip when ret has any ptr field unblocked nested if/else. FnType now resolves to MIRType(FN); typed-variable calls go through ClosureCall; no-capture lambdas always emit ClosureCreate. 5 unrelated goldens also pass now (boxed-drop side-effect). 16/62 → 21/64. Phase A scorecard: 5/5 critical/high docket items closed. |
| | | | |
| | | **Phase B: Verify & Measure (v4.104.0 →)** | |
| | | | |
| **v4.104.0** | Phase B | Rebuild + Golden Verification | Verification-only release (zero code changes). mnc-stage1 rebuilt cleanly at `-O2` (1m21s, 3.5 MB stripped); 21/64 goldens through mnc-stage1 (unchanged from v4.103.0 — no regressions); **60/64 through full integration pipeline** (emit → llvm-as → opt -O2 → llc → clang → run); **3/3 async goldens run natively with expected output** (42, 43, 110) and valgrind clean; 17/18 runnable stage1 tests produce byte-identical output to bootstrap. 5 divergence docket items opened (`Div.1`–`Div.5`) for v4.106.0 panel: 2 HIGH (stage1 ?-op wrong-type store, bootstrap ?-op invalid IR), 2 MEDIUM (Option payload ABI, or-pattern with enum constructor), 1 LOW (main return type). |
| **v4.105.0** | Phase B | Debugging Infrastructure (valgrind, ASan, TSan, crash breadcrumbs, CI) | Sanitizer instrumentation across the full suite. Valgrind: 0 CLEAN / 28 WARNINGS_ONLY / 36 ERRORS (top frames: `mir_opt__block_successors` 14×, `__mn_list_free` 12×, `emit_llvm__emit_mir_call` 11×). ASan: 21 CLEAN / 17 ASAN_ERROR (12 heap-UAF in `mn_list_rc`, 5 global-buffer-overflow in `strtoll` on non-NUL strings). TSan: **3/3 async goldens race-free**; compiler-side found legacy crash handler is async-signal-unsafe. Phase 4 ships the fix: new `__mn_install_crash_handler` with thread-local source breadcrumbs, output `[CRASH] SIGSEGV during compile at tests/golden/03_function.mn`. `.github/workflows/sanitizers.yml` adds 3 CI jobs (valgrind, asan, tsan-async) + baseline-checker scripts that fail on regression. 10 docket items (`Vg.1`–`Vg.7`, `As.1`–`As.3`) open for v4.106.0 panel. Zero regressions: 21/64 stage1 goldens unchanged. |
| **v4.106.0** | Phase B | **Panel: NEEDS WORK → v4.106.1 patch** | 7-reviewer Phase B panel on v4.100.0–v4.105.0. **Aggregate 7.87/10** (+1.28 vs v4.99.0's 6.59 — largest single-arc improvement since v4.31.0 recovery close). **Zero NEEDS WORK verdicts** (Rattler 7.8, Viper 7.5, Anaconda 7.8, Cobra 7.5, Coral 8.0, Boa **8.5 PASS**, Mamba 8.0 — 6 PASS WITH NOTES, 1 PASS). Aggregate < 8.0 PASS threshold → narrowly-scoped v4.106.1 patch. **All 5 v4.99.0 critical/high items CLOSED with evidence**. Load-bearing new finding: Rattler's IR inspection re-classified the `64_closure_typed` `-O2` miscompile from "LLVM opt bug" (PRE_PANEL_AUDIT's reading) to **Mapanare emitter bug** — 2-arg lambda emits `void(ptr, ptr, ptr)` instead of `i64(ptr, i64, i64)`, opaque-pointer LLVM 18 accepts silently. Promoted Cl.1 → Rt.1 HIGH. v4.106.1 narrow scope: **2 HIGH items only** — Rt.1 (emitter signature) + Rt.2/Ih.1 (integration harness stdout-diff). |
| **v4.107.0** | Phase C | **Cross-language benchmark surface (Go + C added)** | Pure measurement release. Zero Mapanare code changes. 12 new benchmark programs (6 Go + 6 C) + rewritten harness publish the full six-column comparison: C (gcc -O2), C (clang -O2), Rust -O, Go, Mapanare O2, Python 3.12 across 6 workloads (fib_recursive, quicksort, struct_alloc, enum_match, prime_sieve, string_concat). 10 runs per config, median of middle 8, `/usr/bin/time -v` for per-process peak RSS. Geometric mean (4 non-DCE'd correct workloads): Mapanare is **9.5× slower than C gcc**, **2.8× slower than Rust**, **1.3× slower than Go**, **44.6× faster than Python**. Pure compute (fib, prime_sieve) is on par with Rust; enum_match 27× slower confirms v4.106.0's **Rt.1** boxed-enum overhead; string_concat 1278× slower confirms it as v4.108.0's StringBuilder target. 35/36 cells correct; strict checksum check surfaced a pre-existing **`List<Int>` indexing bug** (docket **Qs.1**) that v4.98.0's prefix-match missed — Mapanare quicksort produces `1.4e15` instead of `485`. Report at `benchmarks/cross_language/FULL_COMPARISON.md`. |
| **v4.108.0** | Phase C | **string_concat fix — auto-StringBuilder — beats Python** | v4.107.0's embarrassing number (`string_concat` 94.57 ms, 9.8× slower than Python) fixed. **55× faster wall (1.72 ms), 109× less memory** (2.3 MB vs 246 MB). Phase 1 audit discovered v4.95.0's `string_concat_optimization` pass has been dead code since v4.95.0 — matched `Call("__mn_str_concat")` but the MIR lowers string `+` as `BinOp(ADD, String, String)` (the runtime call only appears during LLVM emission). Rewrote the pass against the correct MIR pattern; it now rewrites loop bodies to use the existing v4.95.0 C runtime StringBuilder via two new scalar-pointer wrappers `__mn_sb_new` / `__mn_sb_finish`. Also fixed a latent v4.95.0 bug where `stdlib/ai/llm.mn` and `embedding.mn`'s explicit `sb_create`/`sb_to_string` builtins lowered to struct-by-value ABIs the emitter mis-typed — silently UB since v4.95.0. Mapanare on string_concat: **5.6× faster than Python, 29× faster than Go, ~12% slower than Rust**. Geometric mean across 4 correct non-DCE'd workloads improves from 9.5× slower than C gcc (v4.107.0) to **6.5× slower**. Other 5 workloads unchanged (no regressions). Golden tests 63/64. Docket Qs.1 carried forward unchanged. |
| **v4.109.0** | Phase C | **Optimizer ROI analysis — forensics on Arcs 11–12** | Pure forensics, zero code changes. Answers why `TOTAL_RESULTS.md` showed 0.992× geomean at -O2 after 8 releases of optimizer work. Per-workload: matmul +24% (real Arc 11 win), quicksort +9% (edge of noise), fib 0% (within noise at any scale — H2 rejected via fib(45)), string_concat **−21%** (hints HURT after v4.108.0's StringBuilder pass — `willreturn` on `__mn_sb_*` declarations blocks DSE). Per-hint: **TBAA is 100% dead** (defined in module header, never attached to any load/store across all 4 benchmarks; emit_llvm_text.py:913 has a comment but no code); inline `nsw`/`nuw` are mostly redundant (matmul gets 13 `nuw` inferred even without frontend seeding); function attributes on runtime-call declarations are the *load-bearing* Arc 11 contribution — they cross pass boundaries via LLVM's module-level attribute table. Per-pass: 10 LLVM passes tested in isolation on hinted vs stripped input; zero instruction-level differences in any (pass × benchmark) cell — the matmul 24% win comes from pass-ordering interactions mediated by the attribute table, not inline hint consumption. New dockets: TBAA wiring decision, `willreturn` audit on heap-modifying runtime calls, escape-analysis codegen wiring. Published `benchmarks/optimizer/OPT_ROI_ANALYSIS.md`. |
| **v4.110.0** | Phase C | **Full benchmark refresh with all fixes — Phase C closes** | Pure measurement release, zero code changes. Publishes `benchmarks/PHASE_C_RESULTS.md` as canonical performance document, superseding `FINAL_REPORT.md` (v4.98.0) and `FULL_COMPARISON.md` (v4.107.0). **Geometric means across 5 correct workloads: 50× faster than Python, 1.06× slower than Rust (effectively on par), 2.10× slower than Go, 4.85× slower than C (gcc -O2)** — down from v4.107.0's 9.5× vs C ratio, a 2× narrowing driven entirely by v4.108.0's StringBuilder fix (`string_concat` 94.57 → 1.36 ms, 70× speedup, 109× memory reduction). v4.82.0 cumulative geomean: 1.821× (5 optimizer programs). v4.107.0 same-harness control: all non-string benchmarks within ±5% noise. `struct_alloc` Mapanare beats Rust 0.71× (arena bulk-free vs per-struct Drop); `prime_sieve` ties Rust exactly (3.43 ms each). Dockets Qs.1 (List<Int> indexing), Rt.1 (boxed enum overhead, enum_match 22× slower than C), TBAA.1, willreturn.1 carry to v4.111.0+. Phase C closes. README performance section rewritten against current numbers. |
| | | **Phase D: Self-Hosted Compiler Maturity (v4.111.0 →)** | |
| | | | |
| **v4.111.0** | Phase D | **Self-hosted golden parity — 26/64 + 13 structural-diff (Phase D opens)** | First Phase D release (self-hosted compiler maturity). Rebuilt `mnc-stage1` from the full self-hosted pipeline (`mapanare/self/*.mn`, 38,824 lines); ran all 64 golden tests; documented every failure with root-cause categorization across 9 categories in `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`. **Disabled 4 v4.97.0 MIR optimization passes** in `mapanare/self/mir_opt.mn::optimize_mir()` — `strength_reduce_function`, `inline_small_functions`, `licm_function`, `escape_analysis_function` — all zero-ROI per v4.109.0's forensics (LLVM subsumes the work at -O2), all producing invalid MIR that crashed downstream passes (v4.105.0 flagged `mir_opt__block_successors` as a 14× valgrind hot-frame). Single-file, 34-line diff. **Result: 21/64 → 26/64** (+5 golden unblocks: 05_for_loop, 11_closure, 22_string_builder, 24_enum_methods, 25_fizzbuzz, 50_match_or_patterns). Effective pass rate **39/64** (Category A: 13 tests that compile correctly but show different function count vs bootstrap because bootstrap still inlines — test_native.py strict-compare false-negatives). Remaining 25 actual failures: 10 `__mn_str_starts_with` crashes in `emit_mir_call+0x23515` (docket Sh.2), 5 async-missing (Sh.4), 5 tensor-missing (Sh.6), 2 const-missing (Sh.5), 2 lower_expr crashes, 1 or-pattern (bootstrap also fails), 1 closure-typed (Sh.7), 1 gpu-tensor. Stage2 self-compilation: 0/11 modules. `ir_doctor.py` `_FN_RE` regex doesn't parse inline attribute syntax (false "0 functions" readings; harness limitation documented). Dockets Sh.1-Sh.7 open for v4.112.0+. |
| **v4.112.0** | Phase D | **Fixed-point verification + docket #7 byref size fix (Sh.3 CLOSED)** | Ran the 3-stage fixed-point script, classified divergences, closed docket #7 (byref size heuristic). Single-file fix in `mapanare/self/emit_llvm.mn`: added `struct_byte_size(st, ty)` + `is_byref_type_st(st, ty)` that resolve `%struct.Foo` through `st.structs` and compute real sizes from the inline `{...}` form (matches Python bootstrap's `_tsz` at `emit_llvm_text.py:141`). All 7 call sites of `is_byref_type` updated to pass `st`. **Result on `/tmp/byref_test.mn`**: 16-byte `Small` now passed by value (`%struct.Small %s`); 80-byte `Large` still by reference (`ptr %l.byref`) — correct threshold behaviour. IR validates, binary runs, output correct (311). **Golden tests: 26/64 preserved** (zero regressions). **Fixed-point convergence NOT measured** — stage1 fails at Stage 1 of `verify_fixed_point.sh` with `Undefined variable 'None'` in `mnc_all.mn` because self-hosted `semantic.mn` doesn't register `None` as a constructor. Pre-existing gap; Python bootstrap bypasses via `skip_check=True` in `build_stage1.py`. New docket **Sh.8** opened for self-hosted `None`/`Some`/`Ok` constructor registration. 6/10 exit criteria green, 4/10 blocked on the `None` gap or culebra's long-running scan on 854K-line IR. Published `DIVERGENCE_ANALYSIS.md` with per-class breakdown. |
| **v4.113.0** | Phase D | **Coroutine frame decoupling + last v4.99.0 docket items closed (#8, #10, #11)** | Phase D release 3. Closes the three remaining v4.99.0 panel items — zero open from that panel after this release. **Docket #8 (MEDIUM)** — `mn_coro_is_done` / `mn_coro_resume` in `runtime/native/mapanare_runtime.c` replaced their raw `*(void**)handle` casts with a named `mn_coro_frame_prefix_t` struct documenting the LLVM switched-resume ABI (resume_fn at offset 0, destroy_fn at offset sizeof(void*)). Behaviourally equivalent; one named definition to update if the ABI ever moves. Verified byte-for-byte memory-neutral via pre-change control: `valgrind` leaks on `56_async_await` / `57_real_await` match HEAD~4 exactly, all three async goldens (55/56/57) still produce 42/43/110. **Docket #10 (LOW)** — new `docs/SPEC.md` §2.1.1 "Reserved Keyword Master List" publishes all 42 hard-reserved identifiers with English/Spanish/category/role; cross-references both `mapanare/mapanare.lark:380-427` and `mapanare/self/lexer.mn:59-177`; audit recorded in `keyword-audit.md`. Removed stale "Soft-reserved: async/await" text (those have been hard keywords since v4.68.0/v4.72.0). **Docket #11 (LOW)** — 5 async failure sites in `mapanare_runtime.c` replaced silent-drop / NULL-deref with specific stderr + exit(1): worker `pthread_create` failure (names worker K of N + strerror), scheduler-not-initialised guard, deque+overflow both full (decrements active_tasks + names both capacities), await with overflow full (prints handle + Future address), file_read_async allocation + pthread failures (each allocation named). Manually triggered site #2 in isolation; remaining 4 are wired guards requiring env stress to reach. **Golden tests: 26/64 preserved** (identical to v4.112.0); stage2 0/11 unchanged (pre-existing Sh.8 gap). After v4.113.0, zero open items from v4.99.0 panel; v4.114.0 is the Phase D panel. |
| **v4.114.0** | Phase D | **Phase D panel — NEEDS WORK @ 8.21 < 8.5 threshold** | Zero code changes. Seven reviewers graded v4.111.0-v4.113.0: **2 PASS (Viper 8.5 coroutine-frame memory-safety, Boa 8.5 async-error-message DX), 5 PASS WITH NOTES, 0 NEEDS WORK**. Aggregate **8.21 / 10** falls 0.29 below the Phase D PASS bar (>= 8.5, 0 NEEDS WORK). Decision rule applies mechanically → NEEDS WORK → v4.114.1 patch scheduled. The gap is not structural: v4.106.0 panel was 7.87 with 3 reviewers at 7.5 and zero PASS; v4.114.0 is 8.21 with 2 PASS and no reviewer below 7.8. Every reviewer who moved vs v4.106.0 moved up (+0.34 aggregate). **11/11 v4.99.0 docket items confirmed CLOSED** with line-by-line evidence in `DOCKET_AUDIT.md` — the docket is genuinely empty. Panel findings for v4.114.1 (HIGH): v4.112.0 release name "fixed-point verification" overreaches because the 3-stage script fails at Stage 1 on Sh.8 (doc-rename needed); `/tmp/byref_test.mn` referenced in v4.112.0 SR was never committed (commit `tests/bootstrap/byref_test.mn`). Panel findings for v4.114.1 (LOW): add cleanup-intent comment at site 4 (`__mn_coro_register_wait` overflow) in `mapanare_runtime.c`. Findings deferred to Phase E: self-hosted pipeline CI gate (A.1, carry-forward v4.106.0), fixed-point CI gate (A.2, blocked by Sh.8), async error reachability tests (B.1), pre-existing user-code coroutine leaks (Co.1), culebra scan gap over 854K-line main.ll (Instr.1, three panels blocked). v4.114.1 scope: ~50 lines across 4 files; delta panel (Rattler + Cobra + Anaconda) re-grades after patch. |
| | | **Phase E: Polish + v5.0.0 Prep (v4.115.0 →)** | |
| | | | |
| **v4.115.0** | Phase E | **Async I/O demo running natively — closes v4.99.0 async-I/O gap** | Phase E release 1. Two new example programs demonstrate real async I/O in native binaries: **`examples/async_file_io.mn`** (seeds an input file, reads back synchronously, runs an async pipeline of byte-based `count_lines` + `count_words` counters via `byte_at`, writes a two-field summary from inside `await write_summary(...)`, reads back to verify — output `async pipeline: lines=3 words=10` / `summary file: lines=3 words=10` at both `-O0` and `-O2`), and **`examples/async_http_demo.mn`** (real HTTP GET to `http://example.com/` returning 540 bytes, async pipeline of `body_bytes` → `has_marker` → `write_summary`, deterministic non-crash exit if the sandbox blocks outbound TCP). New **`docs/guides/async.md`** (244 lines) walks mental model, `async fn` / `await` / `block_on` syntax, both end-to-end examples, what-works / what-doesn't tables with docket IDs, and Sh.9 workaround recipes. **Zero compiler/runtime/self-hosted code changes** (Phase 4 confirmed no new C runtime symbols needed — `libmapanare_rt.a` byte-identical to v4.114.0). Two Python-bootstrap emitter bugs surfaced and worked around in both examples: **Sh.9a** (`await` on String-returning async fn produces invalid IR — type mismatch between future-extraction GEP and inlined String return) and **Sh.9b** (DCE eliminates `await` calls whose Int return is unused, silently dropping any side-effecting C call inside — worked around by folding `wrote` into the pipeline's return encoding). **Sh.10** opened for making `__mn_file_read_async` user-callable (pre-requisite: Sh.9a). **Regression clean**: Python-bootstrap 63/64, async goldens 55/56/57 → 42/43/110 unchanged. |
| **v4.116.0** | Phase E | **Documentation batch — five panel-flagged doc gaps closed** | Phase E release 2. Zero code changes. Closes five documentation gaps flagged by Boa (and others) since v4.82.0: (1) **`README.md`** — version badge 4.31.0 → 4.116.0, headline benchmark line (50× faster than Python, 1.06× on par with Rust, 4.85× slower than C gcc -O2) with link to `benchmarks/PHASE_C_RESULTS.md`, self-hosted LOC 15K → 38K, Feature Status table adds async/await row (New in v4.72.0, native I/O demos in v4.115.0), "Coming in v4.2" replaced with "Planned" + status note, Roadmap table extended through v4.116.0 with v4.120.0 panel row; (2) **`docs/SPEC.md`** — header 1.0.0 Final → 4.116.0 Live with sync-discipline note (mapanare.lark, types.py, self/lexer.mn as canonical sources), §29 gains v4.115.0 status paragraph (cooperative-not-preemptive, native I/O demoed, mnc-stage1 async-lowering gap is Sh.4), §29.7 `for await` row reflagged as planned/v5.x; (3) **`docs/cookbook/async.md`** — corrected stale `mnc run` claim (async compiles through Python bootstrap; mnc-stage1 doesn't lower async yet), added §8 native compilation workflow (emit-llvm → clang → binary at -O0 and -O2), §9 real file I/O example from v4.115.0, §10 real HTTP GET example from v4.115.0, §11 Sh.9a/Sh.9b emitter-bug recipes with the exact workarounds used by the demos; (4) **`docs/guides/debugging.md`** — full rewrite (213+/164-) correcting the stale "Mapanare emits DWARF with -g" claim (SPEC §21.3 defers DWARF to v5.x; the v4.26.0 Rattler panel flag is finally addressed in user-facing docs), new focus on valgrind as primary tool, ASan, TSan, ir_doctor.py, Culebra, integration harness, decision table mapping symptoms to tools; (5) **`docs/guides/getting_started.md`** (NEW, 244 lines) — practical "from zero to a native binary" walk for developers familiar with compiled languages, complements the existing 624-line tutorial at `docs/getting-started.md`, covers prerequisites, Python bootstrap pipeline, self-hosted mnc-stage1 pipeline, build-from-seed path, running tests, troubleshooting footer. **`docs/roadmap/v4/v4.116.0/VERIFICATION.md`** — panel-facing receipt documenting 7 compile-and-run snippets (all PASS), 3 async goldens (42/43/110 — zero drift from v4.115.0), SPEC syntax review, shell-command spot-check. `libmapanare_rt.a` byte-identical to v4.115.0. **No new dockets; no CARRY_FORWARD closures** (doc drift was a recurring panel comment, not a filed row). |
| **v4.117.0** | Phase E | **Testing sweep — sanitizer CI, flaky audit, coverage** | Phase E release 3. Zero compiler/runtime code changes. Makes the test infrastructure production-grade before the v4.120.0 panel opens. **ASan and TSan CI gates** — already permanent since v4.105.0 via `sanitizers.yml` (valgrind full golden suite, ASan full golden suite, tsan-async on goldens 55/56/57), each with a regression baseline via `check_asan_baseline.py`. This release **extends `tsan-async`** to cover the v4.115.0 native async I/O demos (`examples/async_file_io.mn`, `examples/async_http_demo.mn`); any future scheduler or coroutine-frame race under I/O-heavy workloads now fails CI at PR time. **Flaky audit** (`tests/FLAKY_AUDIT.md`) — pytest ran 5x against 1,501 tests across 9 subdirectories (golden/integration/llvm/lexer/parser/semantic/mir/emit/cli); pairwise `diff` of sorted failure sets across all 4 adjacent pairs is empty. **Zero flaky tests.** The 22 observed failures are deterministic pre-existing bugs (14 stale CLI tests asserting on pre-rename `mapanare compile` command; 3 DWARF-deferral warning tests for a SPEC §21.3-deferred feature; 2 drop-glue count drifts from v4.101.0 move-semantics; 1 cross-module linkage over-specification; 1 emitter-hardening count drift; 1 bounded-generic trait edge case) — catalogued per bucket in FLAKY_AUDIT.md, open for v4.120.0 panel review. **Coverage report** (`tests/COVERAGE.md`) — per-module coverage audit via pytest-cov 7.1.0 / coverage 7.13.5. Aggregate 43% (8,896 / 20,894 stmts); **within the core pipeline 73%**. Individual modules: ast_nodes 100%, mir 95%, types 92%, lexer 89%, pattern_matching 88%, multi_module 83%, semantic 81%, parser 78%, mir_opt 72%, lower 69%, emit_llvm_text 65%. Below-50% tail identified — 13 of them are 0% because their tests live in out-of-scope directories (lsp/emit_c/wasm/transpilers), 12 are real gaps (cli.py 25%, optimizer.py 9% — dead code candidate — diagnostics.py 49%). Five recommendations for future work. **Integration pipeline hardening** (`tests/integration/test_pipeline_hardening.py`, 6 new tests) — deliberately feeds broken inputs at each stage and asserts the `full_pipeline` harness captures the correct failing stage with a non-empty error: unparseable `.mn` → emit; hand-crafted invalid `.ll` → llvm-as; 42-exit binary → nonzero exit captured; `sleep(60)` binary → `TimeoutExpired` raises cleanly; stdout mismatch vs `.expected` → reported with diff; hello.mn happy path still passes. All 6 PASS. **New CI job** (`ci.yml::coverage`, informational not gating) runs the audit command and uploads coverage.xml as a 30-day artifact; flips to enforcing after 5 stable releases per PLAN.md risk register. `libmapanare_rt.a` byte-identical to v4.116.0. **No new dockets; no CARRY_FORWARD closures.** |
| **v4.120.0** | Phase F | **Panel: v5 gate attempt 2 → Option B (NOT tagged)** | Phase F panel. Seven reviewers graded the v4.100.0-v4.119.0 recovery arc. **Aggregate 8.21 / 10** (identical to v4.114.0). **Verdict: 2 PASS + 4 PASS WITH NOTES + 1 NEEDS WORK.** Per-reviewer: Rattler 8.3 LLVM/codegen PASS WITH NOTES (dings lint debt + Qs.1 reproduced fresh), Viper 8.4 memory safety PASS WITH NOTES (opens ASan.1 mn_list_rc UAF baseline review, notes Sh.2 as compile-side crash), **Anaconda 7.6 CI/testing NEEDS WORK** (the load-bearing finding: full pytest shows 73 failures, 51 outside v4.117.0 audit scope; `make lint` red with 302 findings), Cobra 7.9 self-hosted PASS WITH NOTES (Sh.8 fixed-point blocker, byref fix v4.112.0 verified in isolation, README "compiler compiles itself" needs precision), Coral 8.1 language design PASS WITH NOTES (struct-literal-syntax inconsistency, const-keyword half-life, SPEC §29 precision items), **Boa 8.7 documentation PASS** (read all four v4.119.0 panel-prep docs, spot-checked numbers, followed getting-started guide successfully), **Mamba 8.5 performance PASS** (reran benchmarks, numbers hold within ±5%, async 42.6× faster than Python / 1.74× slower than Go goroutines, libmapanare_rt.a byte-identical across 6 releases). **Decision rule**: aggregate 8.21 < 9.0 AND 1 NEEDS WORK → Option B (continue v4.121.0+). Lead independently chose Option B; no conflict. **v5.0.0 NOT tagged.** Zero compiler/runtime code changes. 17 carry-forward items opened: blockers (Qs.1, An.1, An.2, An.3, Sh.8, Rt.1), strongly-recommended (Sh.2, Cb.1/Co.1 README precision), polish (ASan.1, Cb.2, Co.2/Co.3/Co.4, Bo.1/Bo.2/Bo.3), deferred-to-v5.x (Sh.4/5/6/7, TBAA.1, willreturn.1, Sh.9a/9b/10, Instr.1). **Proposed 6-release closeout arc ending at v4.130.0 v5 gate attempt 3** (v4.121.0 test+lint hygiene → v4.122.0 Qs.1 + DWARF → v4.123.0 Rt.1 unbox → v4.124.0 Sh.8 ctor → v4.125.0 benchmark refresh → v4.126.0 dead-code sweep → v4.127-v4.129 buffer). `libmapanare_rt.a` byte-identical to v4.119.0. Panel score trajectory v4.99.0 → v4.106.0 → v4.114.0 → v4.120.0: **6.59 → 7.87 → 8.21 → 8.21**. |
| **v4.119.0** | Phase F | **Retrospective + pre-panel preparation — last release before the v4.120.0 panel** | Phase F release 2. Zero compiler/runtime code changes. Analysis and verification only. Four panel-facing documents committed at `docs/roadmap/v4/v4.120.0/` for the seven reviewers who will grade the v4.100.0-v4.119.0 recovery arc: **`RETROSPECTIVE.md`** (339 lines) — narrative of the full v4.x arc through feature arcs, v4.26.0 crisis (8.20/10, 4 NEEDS WORK), v4.31.0 recovery, v4.76.0 coroutine peak (8.86/10), v4.77-v4.99 drift without panel oversight, v4.99.0 v5-gate failure (6.59/10, 3 NEEDS WORK), and the 20-release six-phase recovery; names what worked (cadence discipline, panel system, docket-driven development, Culebra tooling, scope honesty) and what didn't (optimiser ROI miss on Arcs 11-12, documentation lag, deferred medium items, v4.112.0 naming churn); single load-bearing sentence: **"the recovery arc was net-negative lines of code: −1,155 net lines across v4.99.0 → v4.118.0 (−2,434 Python bootstrap, +939 self-hosted, +340 C runtime) — it removed more than it added."** **`STATISTICS.md`** (238 lines) — hard-number compilation with methodology footnotes for every figure: 121 v4.x release directories, panel score trajectory ASCII chart (v3.33.0 9.44 → v3.47.0 9.79 → v4.26.0 8.20 → v4.31.0 9.34 → v4.76.0 8.86 → v4.99.0 6.59 → v4.106.0 7.87 → v4.114.0 8.21 → v4.120.0 TBD), codebase size now + v4.99.0→v4.118.0 growth table, golden progress (0/61 → 26/64 literal / 39/64 effective), carry-forward ledger (11 open with severity breakdown), 10-gate CI inventory, benchmark geomean summary (5.46× vs C gcc, 36.9× faster than Python, 42.6× faster than Python asyncio, 1.74× slower than Go goroutines), recovery-arc file inventory. **`V5_READINESS.md`** (285 lines) — neutral feature-by-feature status matrix with ✅/◐/⬜/✖ legend across language core (24 features), runtime (11 primitives), self-hosted compiler (10 milestones), stdlib (11 modules), ecosystem (8 packages), documentation (11 artefacts), CI (11 gates); eight itemised "known gaps that would embarrass a v5 label" (self-hosted async/tensor/const/closure gaps Sh.4-7, unprovable fixed-point Sh.8, no package manager, Rt.1 boxed enum overhead, Qs.1 list indexing quirk, optimizer.py 9% coverage dead code, 14 stale CLI tests pre-rename, TBAA.1 declared-but-not-wired); closes with "nothing additional is required between v4.119.0 and v5.0.0 if the panel votes Option A" — the panel decision is the mechanical gate. **`AUDIT_NOTES.md`** (366 lines) — claim-level audit of all 19 SESSION_REPORTs v4.100.0 through v4.118.0: 47 spot-checked claims (MnString bitfield location, `_move_resource` call sites, `mn_coro_is_done` fix, `__mn_sb_new`/`__mn_sb_finish` wrappers, `mn_coro_frame_prefix_t` struct, SPEC §2.1.1 keyword table, file line counts, panel aggregates, golden counts), **0 material discrepancies, 3 cosmetic line-count drifts itemised** (OPT_ROI_ANALYSIS.md −1 line, DIVERGENCE_ANALYSIS.md −1 line, main.ll −3,073 lines consistent with v4.108.0 + v4.111.0 changes), methodology note on what was verified (file existence, symbol presence, docket ledger) vs what wasn't (runtime benchmarks, sanitizer re-runs — panel's own job). **SESSION_REPORTs were NOT retroactively edited** — the panel sees the originals with this audit as an overlay. `libmapanare_rt.a` byte-identical to v4.118.0. **No new dockets; no CARRY_FORWARD closures** (analysis-only). **Next: v4.120.0 — the panel. 7 reviewers. v5 gate attempt 2. Mechanical rule: aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A (tag v5.0.0); 8.5-9.0 → Option C (tag + continue); < 9.0 or any NEEDS WORK → Option B (continue v4.121.0+).** |
| **v4.118.0** | Phase F | **Final cross-language benchmark — definitive panel evidence** | Phase F release 1. The v4.120.0 panel's evidence document now exists. Zero compiler/runtime code changes; four single-line edits to `benchmarks/cross_language/run_benchmarks.py` (version strings only). **All 6 workloads × 6 language configurations × 10 runs** (`fib_recursive`, `quicksort`, `struct_alloc`, `enum_match`, `prime_sieve`, `string_concat` × C gcc -O2 / C clang -O2 / Rust -O / Go / Mapanare O2 / Python 3.12) — 36 cells, all correct checksums, raw data at `benchmarks/cross_language/v4.118.0-results.json`. **Plus 5 native-async workloads** (`01_sequential_chain`, `02_fanout`, `03_io_bound`, `04_mixed_cpu_io`, `05_backpressure` × Mapanare / Python asyncio / Go goroutines × 10 runs) — 15 cells, all correct, raw data at `benchmarks/async/v4.118.0-async.json`. First time this file has working Mapanare numbers since v4.94.0 had to skip them with "linking currently fails." **Headlines** (Mapanare O2 geomean across 6 workloads = 3.07 ms): **5.46× slower than C gcc -O2** (down from v4.107.0's 9.5×, a 2× narrowing entirely from Phase C's string_concat fix), **1.13× slower than Rust**, **1.04× slower than Go (on par)**, **36.9× faster than Python**. **Async geomean 2.13 ms**: **42.6× faster than Python asyncio**, **1.74× slower than Go goroutines**. **Progress v4.82.0 → v4.118.0 (Mapanare O2 wall)**: `fib_recursive` 20.43 → 18.91 ms (jitter); `quicksort` 1.79 → 2.45 ms (harness methodology); `string_concat` **102.31 → 1.32 ms (77.5× speedup)** — the one real win, entirely from v4.108.0's auto-StringBuilder MIR pass. Other cells are within ±10% when harness changes (`/usr/bin/time -v` wrap adding ~1–3 ms of spawn overhead) are accounted for. **`benchmarks/FINAL_REPORT_v4.120.md`** (500 lines) publishes 7 tables (wall / memory / binary / LOC / speedup vs C / progress / async), 6 per-workload ASCII position charts, methodology (hardware, toolchains: gcc 13.3, clang 18.1, rustc 1.94.1, go 1.22.5, python 3.12, LLVM 18.1.3), spectrum analysis by workload category, and a reproducibility checklist. `libmapanare_rt.a` byte-identical to v4.117.0. **No new dockets; no CARRY_FORWARD closures** (measurement-only). Carry-forward for v5.x: Rt.1 (boxed-enum payload), Qs.1 (List<Int> indexing), TBAA.1, Sh.4/5/6/7/8/9/10. |

## What v4.0.0 Delivered

A user can:

1. **Write a CLI program** — read stdin, process files, write output
2. **Fetch data over HTTP** — from a native binary, no Python
3. **Transpile code** — .py/.php/.ts/.go file to Mapanare and run natively
4. **Install a package** — `mapanare install` with dependency resolution
5. **Get useful errors** — error messages with line numbers, Levenshtein suggestions
6. **Use GPU** — @gpu annotated functions with graceful CPU fallback

## What the Architectural Audit Found (2026-04-08)

A deep audit after v4.0.0 revealed technical debt accumulated across 70+
versions. The issues fall into 6 categories:

### 1. Memory leaks (v4.3.0)
- `skip_struct_ret` disables ALL drop glue for struct-returning functions — deliberate leak to avoid use-after-free
- String concat intermediates never freed in loops
- Map iterators, stream closure envs, agent structs, intern table all leak
- Agent `destroy` cleans internals but never calls `free(agent)`

### 2. Concurrency races (v4.4.0)
- `__mn_signal_free` frees arrays without holding signal mutex — races with propagation
- Memory profiling counters are plain `int64_t` (racy under concurrent allocation)
- Arena allocator not thread-safe (dangerous for agent arenas)
- COW nested list corruption (known, worked around in `mnc_all.mn:6944`)
- In-flight messages leak when agent dies

### 3. Dead code / overlapping emitters (v4.2.0)
- 3 LLVM emitters exist, only 1 is used (~5,000 lines dead weight)
- `emit_c.mn` broken (references non-existent MIR types)
- `_coerce_arg` does raw memory reinterpretation at 36 call sites
- `--no-mir` and `--emitter llvmlite` flags lead to worse codegen

### 4. Silent type errors (v4.5.0)
- UNKNOWN type matches everything — failed inference compiles silently (~85 locations)
- Self-hosted semantic analysis imported but never called (1,900 lines dead)
- Self-hosted MIR verifier defined but never invoked
- Parser silently skips unknown tokens

### 5. Self-hosted fragility (v4.6.0)
- ~160 lines of hardcoded struct field index tables
- MIRType uses string comparisons (`t.kind == "int"`) instead of enum
- 3 active self-hosting workarounds (PHI zeroinitializer, substr off-by-one, ABI mismatch)
- 2 legacy typed pointers (`i64*`, `void ()*`)

### 6. Missed optimizations (v4.7.0)
- O1/O2 optimizer passes not in single fixpoint loop
- No constant propagation in self-hosted compiler
- Every `str(bool)` / `str(int)` allocates fresh
- No COW for strings (lists have it)

## The Refactor Sequence

```
v4.2.0  Clean House ─── reduce surface area (prerequisite for everything)
   │
v4.3.0  Drop Glue ──── fix memory leaks (needs single emitter from v4.2.0)
   │
v4.4.0  Thread Safety ─ fix concurrency (needs clear memory ownership from v4.3.0)
   │
v4.5.0  Type System ─── catch errors at compile time (needs stable foundation)
   │
v4.6.0  Self-Hosted ─── clean up the compiler itself (needs type system from v4.5.0)
   │
v4.7.0  Optimizer ───── better code generation (needs correct compiler from v4.6.0)
   │
v4.8.0-v4.13.0  Deep Fixes ── workarounds, memory safety, Culebra gate
   │
v4.14.0 Break Fix ───── fix CRITICAL break bug, 11/11 stage2
   │
v4.15.0 Module Let ──── top-level constants, MIRType enum
   │
v4.16.0 Optimizer ───── dead block elim, constant/copy propagation
   │
v4.17.0 Fixed Point ─── compiler compiles itself, Python optional
   │
v4.18.0+ Evolution ──── new language features (ONLY after v4.17.0 is complete)
```

Each version builds on the previous. You can't fix drop glue with 3 competing
emitters. You can't fix thread safety until memory ownership is clear. You can't
improve the optimizer until the type system is sound.

## Deprecated Emitter History

| Emitter | File | Era | Why it failed |
|---------|------|-----|--------------|
| AST + llvmlite | `emit_llvm.py` | v0.1-v0.8 | Couldn't leverage MIR optimizations; drop glue frees ALL strings without return-pointer comparison (use-after-free); llvmlite C++ dependency |
| MIR + llvmlite | `emit_llvm_mir.py` | v0.6-v1.0 | `_coerce_arg` grew to 36 call sites of raw memory reinterpretation; missing drop glue for lists/maps/signals/streams; global mutable state broke cross-compilation |
| MIR + text | `emit_llvm_text.py` | v3.0-now | **Winner.** Pure Python, comprehensive drop glue, return-pointer comparison. Only issue: `skip_struct_ret` bail-out (v4.3.0) |
| C output (.mn) | `emit_c.mn` | v3.0 | Written for older MIR; references non-existent types; never worked after MIR redesign |

## Prerequisites (all completed for v4.0.0)

| Prerequisite | Version | Status |
|-------------|---------|--------|
| IO Foundation (link mapanare_io.c) | v3.41.0 | Done |
| Network Native (TCP/TLS/HTTP) | v3.42.0 | Done |
| Agent Runtime (spawn/send/sync) | v3.43.0 | Done |
| Real Examples (all run) | v3.44.0 | Done |
| Package Manager | v3.45.0 | Done |
| GPU Foundation | v3.46.0 | Done |
| GPU Examples + Gate | v3.47.0 | Done |

## Lessons Learned

1. **Production readiness is a specific milestone** — "the compiler works" (v1.0.0) is different from "other people can use it" (v4.0.0)
2. **The gap between "compiler works" and "language is usable" is large** — v3.41.0 through v3.47.0 were all about bridging that gap
3. **Cumulative quality compounds** — 9.79/10 review score accumulated across 70+ versions
4. **Technical debt compounds too** — 3 emitters, each with different drop glue strategies, accumulated over v0-v3. The audit found 21 issues that were individually small but collectively severe.
5. **Audit after shipping, not before** — the v4.0.0 production milestone was the right time to stop and audit; doing it earlier would have blocked the release unnecessarily
6. **Fix foundations before features** — the v4.2.0-v4.7.0 sequence is deliberately sequential; each version builds on the previous one's fixes
7. **Document why things were abandoned** — the emitter deprecation history prevents repeating llvmlite's mistakes in future backend work
