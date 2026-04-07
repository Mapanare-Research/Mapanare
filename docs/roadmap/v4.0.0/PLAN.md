# Mapanare v4.0.0 — Production Release

> The compiler is ready for real programs.
> Everything before this was "it compiles itself."
> This is "other people can use it."

**Status:** PLANNED
**Estimated scope:** Integration + polish (1–2 sessions after v3.10.0)
**Breaking:** No (API stable from v3.x)

---

## What v4.0.0 Means

v4.0.0 is NOT a feature release. It's a **quality gate**. Everything
that was added in v3.x (generics, impls, traits, generic impls, self-hosted
compiler, fixed point) must be solid, documented, and tested.

The bar: **someone who reads the docs can write, compile, and run a
non-trivial Mapanare program without hitting compiler bugs.**

---

## Prerequisites (must be done in v3.9.1 + v3.10.0)

### From v3.9.1:
- [x] CI green on all platforms
- [x] 31+ golden tests with reference files
- [x] ir_doctor baseline current

### From v3.10.0:
- [x] Error messages with line numbers
- [x] Generic enums work
- [x] Trait method validation
- [x] Builtin coverage complete

---

## v4.0.0 Checklist

### 1. Documentation

- [ ] `docs/SPEC.md` updated for all v3.x features:
  - Generics syntax and semantics (Section 13)
  - Impl blocks (inherent + trait)
  - Generic impl blocks
  - Trait bounds
  - TraitDef
- [ ] `docs/GETTING_STARTED.md` — 12-section tutorial works end-to-end
- [ ] `CLAUDE.md` updated with v4.0.0 as current version
- [ ] `README.md` reflects v4.0.0 capabilities

### 2. End-to-End Demos

At least 3 non-trivial programs that compile and run natively:

- [ ] **Demo 1: Calculator** — Parse input, evaluate expressions, print result
- [ ] **Demo 2: File processor** — Read file, transform, write output
- [ ] **Demo 3: Data pipeline** — Generic structs + impl methods + collections

### 3. Compiler Quality

- [ ] Fixed point: stage3 == stage4 (must hold)
- [ ] Dead PHI eliminated in ALL stages (not just stage3+)
- [ ] No Culebra critical findings (except known sret ABI false positives)
- [ ] `culebra bisect stage2 stage3` shows 0 divergent functions

### 4. CI/CD

- [ ] All 6 CI jobs green: ci, self-hosted, bootstrap, native, wasm, android
- [ ] macOS + iOS cross-compilation green
- [ ] Bootstrap from seed works with current seed binary

### 5. Test Coverage

- [ ] 32+ golden tests
- [ ] 104+ native assertions
- [ ] 35+ stdlib modules compile
- [ ] 2500+ pytest tests pass
- [ ] All xfail tests either fixed or documented with timeline

### 6. Release Artifacts

- [ ] Version badge: 4.0.0
- [ ] CHANGELOG filled in for v3.9.1, v3.10.0, v4.0.0
- [ ] Seed binary updated
- [ ] Git tag: v4.0.0

---

## Non-Goals for v4.0.0

These are deferred to v4.1+:
- Trait objects / dynamic dispatch
- Higher-kinded types
- Const generics
- Associated types
- Async/await
- Package registry (crates.io equivalent)
- LSP server improvements
- GPU codegen maturity

---

## Version History → v4.0.0

| Version | Theme | Key Deliverables |
|---------|-------|------------------|
| v3.8.0 | Compiler hardening | Loop bounds, method return types, substr fix |
| v3.8.1 | Generics + Impl | Functions, structs, impl dispatch, trait bounds |
| v3.9.0 | Generic Impl Blocks | `impl<T>`, TraitDef, enum-field bug resolved, dead PHI fix |
| v3.9.1 | CI Green | Fix test failures, reference files, baseline |
| v3.10.0 | Error Messages | Line numbers, generic enums, trait validation |
| **v4.0.0** | **Production** | **Docs, demos, quality gate, release** |
