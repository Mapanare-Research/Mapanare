# v4 — Production, Refactor & Evolution

**Era:** v4.0.0+
**Theme:** Ship it, then fix the foundation, then evolve

---

## Goal

Three phases:

1. **v4.0.0** — Production release. Other people can use it.
2. **v4.1.0-v4.7.0** — Architectural refactor. Fix memory leaks, thread safety, type system, and dead code. No new language features until v4.7.0.
3. **v4.8.0** — Solid core. Fix every Culebra finding, replace hardcoded tables, fix memory safety.
4. **v4.9.0+** — Language evolution. Tensor shapes, GPU auto-kernels, reactive async, FFI bindings.

## Headline Techs

- Self-hosted compiler: 15,000+ lines of .mn, 11 modules, fixed-point verified
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
| **v4.8.0** | | Solid Core | Fix all Culebra findings, field indices, MIRType enum, workarounds, semantic.mn memory safety, string pooling, self-hosted optimizer |
| **v4.9.0+** | | Language Evolution | Tensor shapes, `@gpu` auto-kernels, reactive async, FFI bindings |

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
v4.8.0+ Evolution ──── new language features (ONLY after v4.7.0 is complete)
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
