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
