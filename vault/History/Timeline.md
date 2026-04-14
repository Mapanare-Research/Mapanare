---
aliases: [History, Project Timeline, History MOC]
type: moc
---

# Timeline

Map of Content for Mapanare project history. From first commit to v4.120.0 gate.

## Eras

| Era | Versions | Theme | Key Deliverable |
|-----|----------|-------|-----------------|
| [[v0 Era - Foundation]] | v0.1.0 - v0.9.0 | Foundation & Bootstrap | Self-hosted compiler, MIR pipeline, native stdlib |
| [[v1 Era - Stability]] | v1.0.0 - v1.3.0 | Stability & Production | SPEC 1.0 Final, 15/15 golden at -O1, AI/data/web stdlib |
| [[v2 Era - Platform Expansion]] | v2.0.0 - v2.2.0 | Platform Expansion | WASM + GPU + mobile, stage2 IR validates |
| [[v3 Era - Syntax Revolution]] | v3.0.0 - v3.47.0 | Syntax Overhaul & Self-Hosted Maturity | Fixed-point, generics/traits, transpilers, 9.79/10 panel |
| [[v4 Era - Production]] | v4.0.0 - v4.120.0 | Production Release & Maturity | Production ship, recovery, coroutines, v5 gate |

## v4 Sub-Eras

| Sub-Era | Versions | Theme | Summary |
|---------|----------|-------|---------|
| Phases 1-4 | v4.0.0 - v4.26.0 | Foundation, refactor, evolution, CRISIS | Production release, 13K dead lines deleted, fixed-point bootstrap, then 6 hollow features shipped leading to 8.2/10 NEEDS WORK |
| Recovery | v4.27.0 - v4.32.0 | Zero new features, process hardening | 48 items closed, CHANGELOG honesty, panel returned to 9.343/10 |
| Arcs 1-9 | v4.33.0 - v4.76.0 | Real features with real tests | Error handling, LSP, tensors, AI/LLM, compiler debt, deprecation, DWARF, coroutines. 9 arcs, 9 panels. |
| Arcs 10-14 | v4.77.0 - v4.99.0 | Integration, optimization, benchmarks | Integration test harness, MIR inlining, escape analysis, structured concurrency, v5 gate fail (6.59/10) |
| Phases A-F | v4.100.0 - v4.120.0 | Bug fixes, verification, v5 gate attempt 2 | Emitter corruption fixed, sanitizer infra, cross-language benchmarks, target v4.120.0 panel |

## Key Milestones

- **v0.2.0** -- First self-compilation. 5,800+ lines of `.mn` compile themselves via the bootstrap compiler.
- **v0.6.0** -- Bootstrap frozen, MIR pipeline. SSA-based intermediate representation with optimizer and dual emitters. Python bootstrap locked at this version forever.
- **v0.9.0** -- Native stdlib (JSON, HTTP, WebSocket). First `.mn` modules that compile to LLVM IR without Python.
- **v1.0.0** -- SPEC 1.0 Final, language freeze. No new syntax or semantic changes from this point.
- **v1.0.11** -- 15/15 golden at -O1. The 11-patch hardening series culminates in all golden tests passing with optimization.
- **v2.0.0** -- WASM + GPU + mobile. WebAssembly backend, CUDA/Vulkan via dlopen, iOS/Android cross-compilation.
- **v2.1.0** -- Stage2 IR validates. `llvm-as` accepts the IR produced by mnc-stage1 compiling itself.
- **v3.0.0** -- Syntax revolution. Indentation-based, bilingual keywords (`tipo`/`modo`/`@agent`), zero backwards compatibility. 25% fewer tokens.
- **v3.3.0** -- Fixed-point achieved. stage3 == stage4 -- the compiler produces identical output when compiling itself twice.
- **v3.47.0** -- Production gate. 9.79/10 panel score, unanimous PASS, zero CRITICAL/HIGH issues. Ready for v4.0.0.
- **v4.0.0** -- Production release. Other people can use it: install, write, compile, run.
- **v4.17.0** -- Fixed-point bootstrap. mnc-stage1 compiles itself. Python bootstrap becomes optional.
- **v4.26.0** -- THE CRISIS. 8.2/10 panel score, 4 NEEDS WORK. 6 hollow features shipped across 8 versions. Largest single-cycle regression in project history.
- **v4.31.0** -- Recovery complete. 9.343/10, 5 PASS + 2 PASS WITH NOTES, zero NEEDS WORK. Process hardened.
- **v4.76.0** -- Coroutine completion. 8.86/10 panel. First 10/10 ever ([[Coral]]). async/await is real with 70 tests.
- **v4.99.0** -- v5 gate fail. 6.59/10, 3 NEEDS WORK. Tagged-pointer UB, list indexing bug, async linking identified as v5-blocking.
- **v4.101.0** -- Emitter corruption fixed. Python emitter's drop glue was freeing heap strings moved into lists/structs. Six sites gained move-semantics. The root cause behind the v4.99.0 failure.

## Panel Score Trajectory

```
v3.47.0  9.79  -- production gate baseline
v4.26.0  8.20  -- CRISIS (4 NEEDS WORK, 6 hollow features)
v4.31.0  9.34  -- recovery close
v4.36.0  9.50  -- Arc 1 peak
v4.41.0  9.36  -- Arc 2
v4.46.0  8.99  -- Arc 3
v4.51.0  8.90  -- Arc 4
v4.56.0  9.00  -- Arc 5
v4.61.0  8.71  -- Arc 6
v4.66.0  7.71  -- Arc 7 (lowest non-crisis)
v4.71.0  8.29  -- Arc 8
v4.76.0  8.86  -- Arc 9 (first 10/10 ever)
v4.91.0  8.57  -- Arc 12
v4.96.0  8.57  -- Arc 13
v4.99.0  6.59  -- v5 gate FAIL
v4.106.0 7.87  -- Phase B (+1.28, largest single-arc improvement since recovery)
```

## See Also

- [[Dashboard]] -- current state, active docket, release phases
- [[Benchmarks Overview]] -- performance across versions
- [[Reviewer Profiles]] -- 7 reviewers, focus areas, score trends
