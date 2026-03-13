# v0.3.0 Summary — "Depth Over Breadth"

**Released:** March 2026
**Test count:** 1,960+
**Theme:** Traits, module resolution, LLVM agent codegen, arena memory, type formalization

---

## What shipped

- **Arena-based memory management:** per-scope arenas in C runtime, `__mn_str_free` with tag-bit heap/constant distinction, scope-based arena insertion in LLVM emitter
- **TypeKind enum:** replaced all string-based type comparisons in `semantic.py` with `TypeKind` enum (25 kinds), `TypeInfo` dataclass, unified builtin registries in `types.py`
- **LLVM agent codegen:** `spawn`, `send` (`<-`), `sync` targeting C runtime with real OS threads, agent handler dispatch, supervision policy codegen
- **Module resolution:** file-based imports with `pub` visibility, circular dependency detection, transitive imports, RFC `0003-module-resolution.md`
- **Traits:** `trait` / `impl Trait for Type`, trait bounds on generics (`fn sort<T: Ord>`), builtin traits (`Display`, `Eq`, `Ord`, `Hash`), monomorphization on LLVM, Protocol on Python
- **Getting Started guide:** 12-section tutorial from install to agent pipelines, all code samples verified by 19 e2e tests
- **Community governance:** CODE_OF_CONDUCT, SECURITY.md, GOVERNANCE.md, issue/PR templates, CONTRIBUTING.md expanded
- **110+ e2e tests:** arithmetic, strings, structs, enums, agents, signals, streams, modules, cross-backend consistency
- **Benchmark rewrite:** stream benchmark now uses actual streams, concurrency benchmark uses parallel message passing, agent pipeline benchmark added
- **CHANGELOG populated:** backfilled v0.1.0 and v0.2.0 entries from git history

## What didn't ship

- Phase 4 (Polish & Ship) partially deferred: scope reduction, C runtime hardening, and FFI basics moved to v0.4.0
- Discord channel seeding (copy prepared but manual posting required)
- Agent benchmark on native backend (codegen ready, linker integration deferred)

## Key metrics

| Metric | Value |
|--------|-------|
| Tests | 1,960+ |
| New e2e tests | 110+ |
| New trait tests | 38 |
| New module tests | 28 |
| New LLVM agent tests | 27 |
| RFCs written | 3 (memory, modules, traits) |

## Review panel impact

Reviewers scored v0.2.0 at mean 6.6/10. All top concerns from 6/7 reviewers (memory, agents, modules, types, benchmarks, changelog, tutorial, governance) were addressed in this release.
