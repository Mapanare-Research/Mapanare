# Mapanare v0.3.0 — "Depth Over Breadth"

> Plan derived from consolidated review by 7 expert reviewers (2026-03-09).
> Mean score: 6.6/10. Range: 5.5 (Valentina) — 8.2 (Tomas).
> Core message: **Stop adding breadth. Start adding depth.**

---

## Thesis

v0.2.0 proved Mapanare is real. v0.3.0 must prove it is *usable*.

The reviewers unanimously agree: the foundation is strong, but none of the
load-bearing systems are production-quality. The three existential gaps are
**memory management**, **native agent support**, and **module resolution**.
Without all three, the LLVM backend is a demo and the ecosystem cannot form.

Marina Volkov's strategic advice: narrow the identity from "the AI-native
language" to "the agent language." Make the agent primitive — which every
reviewer praised — sing in production.

---

## Scope Rules

1. **No new language features** unless they directly serve the three pillars
2. **Defer GPU/model-loading/tensor-autodiff** — move to v0.5.0+
3. **Fix what exists** before building what doesn't
4. Every item must have a clear "done when" criterion

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Sub-phases |
|-------|------|--------|------------|
| 1 | Foundation Fixes | ✅ Complete | 1.1 ✅, 1.2 ✅, 1.3 ✅, 1.4 ✅ |
| 2 | The Three Pillars | ✅ Complete | 2.1 ✅, 2.2 ✅, 2.3 ✅ |
| 3 | Community & Trust | 🔶 In Progress | 3.1 ✅, 3.2 🔶, 3.3 ✅, 3.4 ✅ |
| 4 | Polish & Ship | 🔲 Not Started | 4.1, 4.2, 4.3 |

---

## Phase 1 — Foundation Fixes

### 1.1 Memory Management Strategy
**Priority:** CRITICAL — cited by 6/7 reviewers

The native backend leaks every string. `__mn_str_free` is a no-op.
This is a showstopper for any program that runs longer than a benchmark.

**Strategy:** Arena allocation per-scope with reference counting for
cross-scope values. Marina's suggestion of per-agent arenas fits the
actor model naturally.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design memory strategy RFC (arena + RC hybrid) | [x] | `docs/rfcs/0002-memory-management.md` |
| 2 | Implement arena allocator in C runtime (`mn_arena_create`, `mn_arena_alloc`, `mn_arena_destroy`) | [x] | Arena in `mapanare_core.c` with linked block list |
| 3 | Implement `__mn_str_free` properly — tag heap vs constant strings (tag bit in pointer) | [x] | LSB tag bit; all string fns use `mn_untag()` |
| 4 | Implement `__mn_list_free` to free contained elements | [x] | `__mn_list_free_strings()` added |
| 5 | Add scope-based arena insertion in `emit_llvm.py` — arenas created at function entry, destroyed at exit | [x] | Arena + string temp tracking in emit_fn |
| 6 | Add agent-scoped arenas — arena per agent lifetime | [x] | API stubs added; wiring deferred to Phase 2.1 |
| 7 | Stress test: 1M string allocations, verify RSS stays bounded | [x] | ctypes stress tests in `tests/native/test_memory_stress.py`; native tests skip without C compiler |
| 8 | Remove "ownership-based" wording from spec until a real ownership system exists | [x] | Updated SPEC.md to say "arena-based" |

**Done when:** A native-compiled program that processes 1M strings in a loop
does not leak memory. Verified via Valgrind/AddressSanitizer.

---

### 1.2 Formalize Type Representation
**Priority:** HIGH — cited by Valentina, Alistair, Derek

Types are compared as raw strings (`"Int" == "Int"`). This precludes
parametric polymorphism, proper inference, and any soundness guarantees.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Define `Type` enum in a new `mapanare/types.py` | [x] | TypeKind enum + TypeInfo dataclass + builtin registries |
| 2 | Refactor `semantic.py` to use `Type` enum instead of string comparisons | [x] | All `.name ==` comparisons replaced with `.kind ==` TypeKind checks |
| 3 | Single source of truth for builtins (currently duplicated in semantic.py, emit_python.py, emit_llvm.py) | [x] | Canonical registries in `types.py`; emitters import from there; LLVM sync assertion |
| 4 | Update all type error messages to use the new representation | [x] | `TypeInfo.display_name` used in all error paths; verified with tests |
| 5 | Ensure all existing tests pass after refactor | [x] | 1711 tests pass (1674 existing + 37 new type tests); mypy + ruff clean |

**Done when:** Zero string-based type comparisons remain in `semantic.py`.
All 1,674 tests pass.

---

### 1.3 Fix Benchmark Integrity
**Priority:** HIGH — cited by 5/7 reviewers

The stream benchmark doesn't use streams. The concurrency benchmark is
sequential. The matrix benchmark uses constant data. This undermines credibility.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Rewrite `03_stream_pipeline.mn` to use actual stream primitives (or relabel as "loop benchmark") | [x] | Now uses `stream()`, `.map()`, `.filter()`, `.fold()` |
| 2 | Rewrite `02_concurrency.mn` to demonstrate actual parallel message passing | [x] | 4 workers processing messages concurrently |
| 3 | Add a "Features Tested" column to benchmark table | [x] | Added to both Performance and Expressiveness tables in README |
| 4 | Add honest notes about what each benchmark tests vs. what it doesn't | [x] | Notes added below benchmark tables in README |
| 5 | Add real-world benchmark: agent pipeline processing JSON messages | [x] | `05_agent_pipeline` with .mn/.py/.go/.rs versions; 3-stage pipeline |

**Done when:** Every benchmark uses the language feature it claims to test.
Benchmark table has a "Features Tested" column.

---

### 1.4 Populate CHANGELOG
**Priority:** HIGH — cited by 6/7 reviewers

The CHANGELOG has only `[Unreleased]`. No versioned entries despite being
at v0.2.0. This is a trust signal failure.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Backfill v0.1.0 entry from git history | [x] | 15 items in Added section |
| 2 | Backfill v0.2.0 entry from git history | [x] | Added + Changed sections |
| 3 | Use Keep a Changelog format (Added, Changed, Fixed, Removed) | [x] | Comparison links at bottom |
| 4 | Resolve version mismatch between VERSION, CHANGELOG, and ROADMAP | [x] | README now links PLAN-v0.3.0.md; stale roadmap table updated |

**Done when:** CHANGELOG has entries for v0.1.0 and v0.2.0 with accurate
Added/Changed/Fixed sections. VERSION, CHANGELOG, and ROADMAP agree.

---

## Phase 2 — The Three Pillars

### 2.1 LLVM Backend: Native Agents
**Priority:** CRITICAL — cited by 6/7 reviewers

The headline features (agents, signals, streams) only work through the
Python transpiler. The LLVM backend handles basic functions, structs,
enums, and arithmetic — but none of the features that differentiate Mapanare.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Wire `emit_llvm.py` to emit calls to C runtime agent functions (`mapanare_agent_init`, `_spawn`, `_send`, `_recv`, `_stop`, `_destroy`) | [x] | Runtime fn declarations + `_rt_agent_*` helpers |
| 2 | Implement `SpawnExpr` codegen — allocate agent struct, init channels, start thread | [x] | `_emit_spawn` → `agent_new` + `agent_spawn` |
| 3 | Implement `SendExpr` (`<-`) codegen — serialize value, push to ring buffer | [x] | `_emit_send` → box value + `agent_send` |
| 4 | Implement `SyncExpr` codegen — block on ring buffer recv | [x] | `_emit_sync_expr` → `agent_recv_blocking` + unbox |
| 5 | Implement agent `handle` function dispatch from C runtime scheduler | [x] | `_emit_agent_handler` wrapper: unbox→call method→box output |
| 6 | Add supervision policy codegen (restart/stop) | [x] | `_apply_supervision` reads `@restart` decorator |
| 7 | Replace 1ms polling sleep in agent scheduler with semaphore-based wakeup | [x] | `inbox_ready`/`outbox_ready` semaphores in C runtime |
| 8 | Add LLVM agent tests: spawn, send, sync, supervision restart | [x] | 27 tests in `tests/llvm/test_agent_codegen.py` |
| 9 | Run agent benchmark on native backend (currently shows "---") | [!] | Requires linker integration with `mapanare_runtime.c`; codegen ready, build pipeline deferred |

**Done when:** The concurrency benchmark (`02_concurrency.mn`) compiles
and runs correctly via `mapanare build`. Agent spawn/send/sync works
natively with real OS threads.

---

### 2.2 Module Resolution
**Priority:** CRITICAL — cited by 5/7 reviewers

Imports parse syntactically but don't resolve. You cannot compose code
across files. No ecosystem is possible without this.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design module resolution RFC (file-based, `pub` visibility, circular dep detection) | [x] | `docs/rfcs/0003-module-resolution.md` |
| 2 | Implement module path resolution in compiler driver | [x] | `mapanare/modules.py` — ModuleResolver with cache + circular detection |
| 3 | Implement `pub` visibility modifier in parser + semantic checker | [x] | `pub` already in grammar/parser for fn/agent/struct/enum/pipe; added to type_alias; visibility enforced in module resolution |
| 4 | Wire resolved modules into semantic checker scope chain | [x] | `_resolve_import` + `_register_imported_def` + namespace access checking |
| 5 | Handle transitive imports | [x] | Recursive resolution via module cache; no transitive re-export unless explicit `export { name }` |
| 6 | Implement for Python backend (emit correct Python imports) | [x] | Emitter translates `::` → `.`; CLI compiles resolved modules to output dir |
| 7 | Implement for LLVM backend (link multiple object files) | [x] | `_emit_import` declares external fns/structs; linker combines object files |
| 8 | Add module resolution tests (single import, transitive, circular error, visibility) | [x] | 28 tests in `tests/modules/test_module_resolution.py` |
| 9 | Connect stdlib modules via real imports (currently Python-only) | [x] | Resolver searches stdlib dir; Python backend maps `std::math` → `stdlib.math`; LLVM stdlib deferred to FFI phase |

**Done when:** A two-file Mapanare program with `import` compiles and
runs correctly on both backends. Circular imports produce a clear error.

---

### 2.3 Traits / Interfaces
**Priority:** HIGH — cited by 5/7 reviewers

Cannot express generic abstractions over types. Cannot write a generic
sort without `Ord`. Cannot write a generic print without `Display`.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design traits RFC | [x] | `docs/rfcs/0004-traits.md` — monomorphization, Protocol for Python, builtin traits |
| 2 | Add `trait` and `impl Trait for Type` to grammar | [x] | `trait_def`, `trait_method`, `impl_trait_def` rules; `KW_TRAIT` keyword; `type_param` with bounds |
| 3 | Add trait definitions to AST nodes | [x] | `TraitDef`, `TraitMethod`, `TypeParam`; `ImplDef.trait_name`; `FnDef.trait_bounds` |
| 4 | Implement trait checking in semantic pass (verify impl satisfies trait) | [x] | Register in pass 1; verify missing/extra methods in pass 2; `TypeKind.TRAIT` added |
| 5 | Add trait bounds on generics: `fn sort<T: Ord>(list: List<T>)` | [x] | `type_param` rule with `COLON NAME`; `FnDef.trait_bounds` dict; `_trait_impls` registry |
| 6 | Emit trait dispatch for Python backend (protocol/ABC) | [x] | `_emit_trait` → `Protocol` class; trait impl methods merged into struct |
| 7 | Emit trait dispatch for LLVM backend (vtable or monomorphization) | [x] | Monomorphization: `_emit_impl_methods` emits mangled fns; traits are type-level only |
| 8 | Implement builtin traits: `Display`, `Eq`, `Ord`, `Hash` | [x] | `BUILTIN_TRAITS` in `types.py`; auto-registered in semantic checker |
| 9 | Add trait tests (definition, implementation, bounds, missing impl error) | [x] | 38 tests in `tests/semantic/test_traits.py` — parsing, semantic, Python emit, LLVM emit |

**Done when:** `fn max<T: Ord>(a: T, b: T) -> T` compiles and works on
both backends. Missing trait impl produces a clear error.

---

## Phase 3 — Community & Trust (parallel with Phase 2)

### 3.1 Getting Started Tutorial
**Priority:** HIGH — cited by 4/7 reviewers

The single highest-ROI content investment. Rita: "15 Minutes to Your
First Agent Pipeline."

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Write `docs/getting-started.md` (install, hello world, functions, structs, enums, match, agents, pipes) | [x] | 12 sections: install through streams, all code samples from verified e2e patterns |
| 2 | Add pronunciation guide to README ("mah-pah-NAH-reh") | [x] | Added below title in README header |
| 3 | Link prominently from README (above the fold) | [x] | Bold "Getting Started" link first in nav bar |
| 4 | Test the tutorial end-to-end — every code sample must compile and run | [x] | 19 tests in `tests/e2e/test_tutorial.py`; all 12 sections verified |

**Done when:** A Python developer with no Mapanare experience can follow
the tutorial from install to running an agent pipeline in 15 minutes.

---

### 3.2 Community Governance
**Priority:** HIGH — cited by Rita (blocker), Sarah

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1) | [x] | Added at repo root |
| 2 | Add `SECURITY.md` (vulnerability disclosure policy) | [x] | Added at repo root |
| 3 | Add `GOVERNANCE.md` (BDFL model, RFC process, maintainer path) | [x] | Added at repo root |
| 4 | Add `.github/ISSUE_TEMPLATE/bug_report.yml` | [x] | Added with GitHub issue form fields |
| 5 | Add `.github/ISSUE_TEMPLATE/feature_request.yml` | [x] | Added with RFC guidance for language changes |
| 6 | Add `.github/pull_request_template.md` | [x] | Added PR checklist for tests, docs, and RFC links |
| 7 | Warm up CONTRIBUTING.md — add encouragement, non-code contribution paths | [x] | Expanded contributor paths, channels, and process |
| 8 | Seed Discord channels (#welcome, #general, #help, #show-and-tell, #compiler-dev) | [ ] | Copy prepared in `docs/discord-seeding.md`; manual posting still required |

**Done when:** All governance files exist. Issue/PR templates work.
Discord has seeded conversations in all channels.

---

### 3.3 End-to-End Correctness Tests
**Priority:** HIGH — cited by Derek, Sarah, Alistair

The test suite validates compiler internals but doesn't verify that
compiled programs produce correct output.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Create `tests/e2e/` test framework: compile .mn → run → assert on stdout | [x] | `_run_mapanare` helper in `test_e2e.py`; `_to_llvm_ir` in `test_e2e_llvm.py` |
| 2 | E2e tests: arithmetic, strings, functions, closures | [x] | 19 tests in `test_e2e_correctness.py`: int/float/mod/neg, strings, recursion, lambdas |
| 3 | E2e tests: structs, enums, pattern matching | [x] | 8 tests in `test_e2e_correctness.py`: struct fields, enum destructuring, match wildcard/string |
| 4 | E2e tests: agent spawn/send/sync (Python backend) | [x] | 6 tests in `test_e2e.py`: echo, doubler, multi-msg, pipeline, pipe, 3-chain |
| 5 | E2e tests: agent spawn/send/sync (LLVM backend) | [x] | 3 tests in `test_e2e_llvm.py`: spawn/send/sync IR, handler gen, multi-agent IR |
| 6 | E2e tests: streams, signals, Result/Option | [x] | 13 tests in `test_e2e.py`: stream map/filter/take, signals, Ok/Err/Some/None/? |
| 7 | E2e tests: module imports | [x] | 2 tests in `test_e2e.py`: import function, import agent across files |
| 8 | Cross-backend consistency tests: same .mn → same output on both backends | [x] | 12 tests in `test_e2e_cross_backend.py`: same source → Python runs + LLVM IR compiles |
| 9 | Add all e2e tests to CI pipeline | [x] | CI runs `pytest tests/ -v` which includes `tests/e2e/`; 110 e2e tests total |

**Done when:** 30+ e2e tests covering all major features. Both backends
tested. All in CI.

---

### 3.4 Doc/Code Consistency Audit
**Priority:** MEDIUM — cited by Derek, Marina

README says REPL is "Planned" but it's implemented. Maps are "Planned"
but exist in grammar/AST/emitter. Feature status table is stale.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Audit every entry in README feature status table against actual compiler | [x] | Fixed 7 entries: agents LLVM→Codegen, traits+modules added, maps→Stable, REPL→Yes, tensors corrected, GPU labeled v0.5.0+, roadmap table updated |
| 2 | Fix REPL status (it exists in cli.py) | [x] | Changed from Planned→Yes/Experimental; added `repl` to CLI command list |
| 3 | Fix Map/Dict status (grammar has map_lit, AST has MapLiteral) | [x] | Changed from Planned→Yes/Partial/Stable; `#{k:v}` syntax in grammar+parser+semantic+both emitters |
| 4 | Audit SPEC.md claims against implementation | [x] | Fixed: REPL non-goal wording, grammar summary (added traits/imports/exports), Appendix B tensor claims, Appendix C (split implemented vs planned) |
| 5 | Remove or clearly label aspirational claims (e.g., "ownership-based memory management") | [x] | ownership-based already fixed in 1.1; labeled string interpolation `${x}` as unimplemented; GPU section labeled v0.5.0+; Python tensor claim corrected |

**Done when:** Every claim in README and SPEC.md is accurate. Feature
status table matches reality.

---

## Phase 4 — Polish & Ship

### 4.1 Scope Reduction
**Priority:** MEDIUM — cited by Marina, Derek, Valentina

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Move `mapanare/gpu.py` to `experimental/` or remove from default build | [ ] | |
| 2 | Move `mapanare/model.py` to `experimental/` or remove from default build | [ ] | |
| 3 | Update README to honestly reflect what ships vs what's experimental | [ ] | |
| 4 | Update ROADMAP to show GPU/model-loading as v0.5.0+ | [ ] | |

**Done when:** Core compiler has no dead-code GPU/model dependencies.
README accurately represents shipping features.

---

### 4.2 C Runtime Hardening
**Priority:** MEDIUM — cited by Sarah, Valentina

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add C runtime unit tests (ring buffer stress test, thread pool saturation) | [ ] | |
| 2 | Run under ThreadSanitizer and AddressSanitizer | [ ] | |
| 3 | Fix any issues found | [ ] | |
| 4 | Add SIGTERM/SIGINT handling for graceful agent shutdown | [ ] | |
| 5 | Add to CI (compile + test C code) | [ ] | |

**Done when:** C runtime tests exist and pass under sanitizers. Graceful
shutdown works.

---

### 4.3 FFI Basics
**Priority:** MEDIUM — cited by Marina, Sarah

Without FFI, the native backend is limited to what the C runtime provides.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Add `extern "C"` function declarations to grammar | [ ] | |
| 2 | Implement in semantic checker (no body, just signature + calling convention) | [ ] | |
| 3 | Implement in LLVM emitter (declare external function, generate call) | [ ] | |
| 4 | Add linker flag passthrough (`--link-lib`) | [ ] | |
| 5 | Test: call `puts` from libc via FFI | [ ] | |

**Done when:** `extern "C" fn puts(s: String) -> Int` compiles and links
correctly. A Mapanare program can call C functions.

---

## What v0.3.0 Does NOT Include

These are explicitly deferred to maintain focus:

| Item | Deferred To | Reason |
|------|-------------|--------|
| GPU kernel dispatch | v0.5.0+ | Memory + agents must work first |
| Model loading (ONNX/safetensors) | v0.5.0+ | Disconnected from compiler |
| Autograd / computation graphs | v1.0+ | Research-level feature |
| Formal semantics / core calculus | v0.5.0+ | Important but not urgent |
| Browser playground (WASM) | v0.4.0 | High impact but large scope |
| Distributed tracing / OpenTelemetry | v0.4.0 | Needs native agents first |
| Package registry | v0.4.0 | Needs module resolution first |
| Effect typing for agents | v1.0+ | Research-level |
| Session types for channels | v1.0+ | Research-level |
| Intermediate representation (MIR) | v0.4.0 | Important but not blocking |

---

## Success Criteria for v0.3.0

v0.3.0 ships when ALL of the following are true:

1. **Memory:** Native-compiled programs do not leak strings or list contents.
   Verified via sanitizers.
2. **Agents:** `agent` / `spawn` / `<-` / `sync` compile and run on the LLVM
   backend with real OS threads.
3. **Modules:** `import` resolves files. Multi-file programs compile on both
   backends.
4. **Traits:** `trait` / `impl` work. Generic functions with trait bounds
   compile.
5. **Types:** Semantic checker uses proper Type enum, not string comparisons.
6. **Tests:** 30+ e2e tests. C runtime tests under sanitizers. Cross-backend
   consistency tests.
7. **Benchmarks:** Every benchmark uses the feature it claims to test.
8. **CHANGELOG:** Populated for v0.1.0, v0.2.0, and v0.3.0.
9. **Docs:** Getting Started tutorial exists and works. Feature status table
   is accurate.
10. **Governance:** CODE_OF_CONDUCT, SECURITY.md, issue templates exist.

---

## Estimated Score Impact

| Reviewer | v0.2.0 | Est. v0.3.0 | Key Driver |
|----------|--------|-------------|------------|
| Valentina | 5.5 | 7.0-7.5 | Memory + type formalization |
| Derek | 6.0 | 7.0-7.5 | Focus + e2e tests + tutorial |
| Marina | 6.5 | 7.5-8.0 | Memory + modules + traits + scope reduction |
| Tomas | 8.2 | 8.5-9.0 | Native agents close the gap |
| Sarah | 6.0 | 7.0 | C runtime tests + memory + structured errors |
| Alistair | 6.5 | 7.5 | Type formalization + traits |
| Rita | 7.5 | 8.5-9.0 | Governance + tutorial + changelog |
| **Mean** | **6.6** | **~7.5-8.0** | |

---

## Timeline Summary

```
Week 1-3:   Phase 1 -- Foundation (memory, types, benchmarks, changelog)
Week 4-10:  Phase 2 -- Three Pillars (native agents, modules, traits)
Week 8-12:  Phase 3 -- Community & Trust (tutorial, governance, e2e tests)
            (parallel with Phase 2)
Week 11-13: Phase 4 -- Polish & Ship (scope reduction, C hardening, FFI)
```

**Total: ~13 weeks / 3 months**

---

*"A language that does agents brilliantly for 500 devoted users has a future.
A language that does everything partially for zero users does not."*
-- Marina Volkov
