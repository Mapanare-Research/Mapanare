---
era: v4
versions: v4.0.0 - v4.120.0
theme: Production Release & Maturity
releases: 100+
status: ongoing
tests_current: 5374
golden_current: 62
panel_peak: 9.50
panel_low: 6.59
---

# v4 Era -- Production

One hundred plus releases and counting. The era where other people can use it -- and where the project learned the difference between "it compiles" and "it works."

## Summary

[[v4.0.0]] was the production release: install, write, compile, run. [[v4.2.0]] deleted 13,000 lines of dead emitters (3 LLVM emitters reduced to 1). The architectural refactor sequence (v4.2.0 - v4.17.0) systematically fixed memory leaks, thread safety, type system holes, and dead code, culminating in [[v4.17.0]] where mnc-stage1 compiled itself -- fixed-point bootstrap, Python becomes optional.

Then the evolution arc (v4.18.0 - v4.26.0) shipped 6 hollow features in 8 versions. [[v4.26.0]] returned the largest single-cycle regression in project history: 9.79 to 8.2, 4 NEEDS WORK. `const` was a parser alias with no immutability. `@gpu` raised `NotImplementedError`. `await` was a pure identity function. The 7-reviewer panel installed the recovery process that would govern all subsequent work.

The recovery arc (v4.27.0 - v4.31.0) closed 48 items with zero new features. [[v4.31.0]] panel: 9.343/10, 5 PASS + 2 PASS WITH NOTES, zero NEEDS WORK. Process hardened: CHANGELOG honesty CI, docs-drift detector, carry-forward queue.

The 45-release post-recovery roadmap (v4.33.0 - v4.76.0) delivered real features with real tests across 9 thematic arcs. [[v4.76.0]] shipped async/await with real LLVM coroutines -- 8.86/10, and [[Coral]] gave the project its first ever 10/10 individual reviewer score. The plan worked: "The plan was never about the features. It was about the cadence."

The v5 gate at [[v4.99.0]] failed: 6.59/10, 3 NEEDS WORK. Tagged-pointer UB, list indexing bug, and async linking were identified as v5-blocking. [[v4.101.0]] found the root cause -- the Python emitter's drop glue was freeing heap strings that had been moved into lists or stored as struct fields. Six sites gained move-semantics. The emitter corruption that caused the v4.99.0 failure was a pre-existing bug, not caused by the tagged-pointer change.

Current: v4.108.0. fib(35) in 19.6ms (1.1x Rust). 5,374 tests, 62 golden. Target: [[v4.120.0]] panel for v5 gate attempt 2.

## Sub-Eras

### Phases 1-4: Foundation to CRISIS (v4.0.0 - v4.26.0)

| Phase | Versions | Theme |
|-------|----------|-------|
| Production | v4.0.0 | Ship it. Other people can use it. |
| Refactor | v4.1.0 - v4.7.0 | Ecosystem infra, emitter consolidation, drop glue, thread safety, type system, self-hosted quality, optimizer |
| Deep Fixes | v4.8.0 - v4.13.0 | Workaround fixes, semantic safety, drop glue complete, global constants, self-hosted optimizer, Culebra gate |
| Final Maturity | v4.14.0 - v4.17.0 | Break fix, module-level let, optimizer complete, fixed-point bootstrap |
| Evolution | v4.18.0 - v4.26.0 | Tensor shapes, GPU auto-kernels, reactive async, FFI, const. **6 hollow features. CRISIS.** |

### Recovery (v4.27.0 - v4.32.0)

Zero new features. 48 items closed. Process hardened.

| Version | Theme |
|---------|-------|
| **v4.27.0** | Honesty Recovery (CRITICAL): 8 CRITICAL items, FFI argtypes, `@gpu` removed, `const` reverted, MIR verifier wired |
| **v4.28.0** | Concurrency: signal/agent/registry races, matmul carry-forwards (27 versions overdue) |
| **v4.29.0** | Build infrastructure: orphaned files, `extern "Python"` decision, CI hollow-feature gate |
| **v4.30.0** | Codegen: `await` decision, optimizer non-convergence ICE, six 7-cycle emitter items |
| **v4.31.0** | Documentation truth: SPEC sync, CHANGELOG honesty CI. **Panel: 9.343/10, recovery terminates** |
| **v4.32.0** | Arc-end closure: 9 HIGH/MEDIUM from v4.31.0 panel |

### Arcs 1-9: Real Features with Real Tests (v4.33.0 - v4.76.0)

Every arc follows: 3-4 feature releases followed by 1 panel release.

| Arc | Versions | Theme | Panel Score |
|-----|----------|-------|-------------|
| 1 | v4.33.0 - v4.36.0 | Error Handling + Pattern Matching | 9.50 |
| 2 | v4.37.0 - v4.41.0 | LSP Maturity | 9.36 |
| 3 | v4.42.0 - v4.46.0 | Tensor Completeness | 8.99 |
| 4 | v4.47.0 - v4.51.0 | Stdlib AI/LLM | 8.90 |
| 5 | v4.52.0 - v4.56.0 | Compiler Debt Drain | 9.00 |
| 6 | v4.57.0 - v4.61.0 | Deprecation + Deletion | 8.71 |
| 7 | v4.62.0 - v4.66.0 | DWARF Debug Info | 7.71 |
| 8 | v4.67.0 - v4.71.0 | Coroutine Foundation | 8.29 |
| 9 | v4.72.0 - v4.76.0 | Coroutine Completion | 8.86 (first 10/10 ever) |

### Arcs 10-14: Integration, Optimization, Benchmarks (v4.77.0 - v4.99.0)

| Arc | Versions | Theme | Key Result |
|-----|----------|-------|------------|
| 10 | v4.77.0+ | Integration Test Harness | 58 golden through full LLVM pipeline |
| 12 | v4.87.0 - v4.91.0 | MIR Function Inlining + Escape Analysis | fib 1.1x Rust, panel 8.57/10 |
| 13 | v4.92.0 - v4.96.0 | Structured Concurrency + StringBuilder | Multi-threaded scheduler, panel 8.57/10 |
| 14 | v4.97.0 - v4.99.0 | Final Panel | **v5 gate FAIL: 6.59/10** |

### Phases A-F: Bug Sprint to v5 Gate Attempt 2 (v4.100.0 - v4.120.0)

| Phase | Versions | Theme |
|-------|----------|-------|
| **A** Bug Sprint | v4.100.0 - v4.103.0 | Critical docket fixes: tagged-pointer UB, emitter corruption (move-semantics), async linking, else/sino, closure types |
| **B** Rebuild + Verify | v4.104.0 - v4.106.0 | Golden verification, sanitizer infra (valgrind/ASan/TSan), panel 7.87/10 |
| **C** Benchmark Truth | v4.107.0 - v4.110.0 | Cross-language benchmarks (6 Go + 6 C programs), StringBuilder, optimizer ROI |
| **D** Self-Hosted + Testing | v4.111.0 - v4.114.0 | Fixed-point, medium docket items, panel |
| **E** Polish + Docs | v4.115.0 - v4.117.0 | Async I/O, docs, sanitizer CI |
| **F** Gate | v4.118.0 - v4.120.0 | Final benchmark, retrospective, panel (v5 gate attempt 2) |

## Headline Technologies

- **Emitter consolidation**: 3 LLVM emitters to 1, ~13,000 lines deleted
- **Fixed-point bootstrap**: mnc-stage1 compiles itself, 3-stage verification
- **7-reviewer panel system**: 9 scheduled panels across the post-recovery roadmap
- **LLVM coroutines**: `coro.id`/`coro.begin`/`coro.suspend`/`coro.end`, C runtime scheduler
- **MIR optimizer**: constant folding, copy propagation, dead block elimination, function inlining, escape analysis (heap-to-stack promotion)
- **Cross-language benchmarks**: C (gcc/clang), Rust, Go, Mapanare, Python across 6 workloads
- **Move-semantics in drop glue**: the fix that closed the v4.99.0 root cause
- **Sanitizer infrastructure**: valgrind, ASan, TSan CI jobs with baseline-checker scripts

## Key Decisions

1. **Delete before fixing.** v4.2.0 deleted 13K lines of dead emitters before touching any features. You cannot fix drop glue with 3 competing emitters.
2. **Sequential refactor.** Each version v4.2.0 through v4.7.0 builds on the previous. Drop glue needs one emitter. Thread safety needs clear memory ownership. Optimizer needs correct type system.
3. **Panel-terminated recovery.** The recovery arc terminates externally -- when the panel says it does, not when the lead does.
4. **Cadence over features.** 9 arcs of 5 releases, panel at the end of each. The structure prevented scope creep and the CRISIS from repeating.
5. **Option B after v5 gate fail.** Continue v4.100.0+ instead of tagging v5. Fix the bugs first.

## Lessons Learned

- Production readiness is a specific milestone. "The compiler works" (v1.0.0) is different from "other people can use it" (v4.0.0).
- Features that parse but do not run are worse than missing features. The v4.26.0 crisis proved this.
- CHANGELOG honesty is a CI-enforceable property. After the crisis, automated scripts verify that advertised tests actually exist.
- The 7-reviewer panel system is the most important process innovation in the project. It caught the crisis, terminated the recovery, and provided calibrated feedback across 9 arcs.
- Move-semantics gaps are invisible until they are catastrophic. The v4.101.0 root cause -- drop glue freeing strings that had been moved into lists -- had been present for many versions.

## Performance (v4.107.0 benchmarks)

Geometric mean across 4 non-DCE'd correct workloads (C gcc -O2 = 1.0x baseline):

| Language | Geomean vs C |
|----------|-------------|
| C (gcc -O2) | 1.0x |
| C (clang -O2) | ~1.0x |
| Rust -O | ~1.1x |
| Go | ~1.3x |
| **Mapanare O2** | **9.5x** |
| Python 3.12 | ~425x |

Pure compute (fib, prime_sieve) is on par with Rust. enum_match 27x slower (boxed-enum overhead). string_concat 1278x slower (StringBuilder target).

## See Also

- [[v3 Era - Syntax Revolution]] -- previous era
- [[Timeline]] -- full project history
- [[Dashboard]] -- current state, active docket
- [[v4.76.0]] -- first 10/10 (Coral)
- [[v4.99.0]] -- v5 gate fail
- [[v4.101.0]] -- emitter corruption fixed
