# Master Prompt — Roadmap to v4.0.0 (Production Release)

> Close all review items, fix CI, ship v4.0.0.
> Read CLAUDE.md for full project context.

---

## Current State

- **Version:** 3.35.0
- **Branch:** dev
- **Aggregate review score:** 9.44/10 (7 reviewers, all PASS)
- **Self-hosted compiler:** 20K+ lines, 16 modules, compiles itself
- **Transpilers:** Python, PHP, TypeScript, Go (all self-hosted in .mn)
- **CI status:** green (all lint/test/mypy pass, golden tests pass with regenerated main.ll)

## Completed Versions

### v3.34.0 — "Review Fixes" (DONE)

All 20 action items from the v3.33.0 code review addressed in one release:

- `__mn_map_new` explicit `val_type` parameter (eliminates size heuristic — 4 reviewers)
- `__mn_file_copy` returns -1 on write failure
- `__mn_signal_on_change` thread-safe locking
- LLVM 17+ opaque pointer fixes (bitcast removal, `ptr` syntax)
- `continue` added to SPEC keyword table
- `cow_shares` duplicate declaration removed
- Self-hosted `types_compatible` strengthened (param + return type comparison)
- `getattr` replaced with direct field access
- `is_digit` name collision resolved
- Shared `is_transpiler_alpha` (removed ~200 lines of duplication)
- Dead `llvm_list_type()` removed
- Module-scope `_ARITH_TRAIT_MAP` / `_OP_TO_TRAIT`
- `Err.unwrap()` -> `NoReturn`
- Version strings updated across codebase
- 843 tests passed, 0 failed

### v3.35.0 — "Break-in-For Fix" (DONE)

- Break-in-for bug investigated and confirmed already fixed in Python lowerer
- `lexer.mn:tokenize()` migrated from `for _ in 0..2000000` to `while pos < slen`
- 6 stale "avoids break-in-for bug" comments removed from `lower.mn`
- Golden test `33_break_continue.mn` added (break/continue/while validation)
- 680 tests passed, 0 failed

### CI Fixes (DONE)

- `noalias` emitted as return attribute (not function attribute) for LLVM compat
- `__mn_map_new` backward-compatible with 3-arg callers (sentinel-based fallback)
- Text emitter field-type codegen bug fixed (`_struct_field0_type` parser)
- `main.ll` regenerated (275K lines, current 5-field MnList ABI)
- Seed binary updated (matches current ABI)
- iOS `system()` guard: `#if/#elif/#else` so compiler never sees unavailable decl
- All CI jobs re-enabled (golden tests, stage2, bootstrap)

## What Remains for v4.0.0

v4.0.0 is a **pure quality gate** — no new features, just validation:

1. Update `VERSION` to `4.0.0`
2. Update `main.mn` version string to `"mapanare 4.0.0"`
3. Update version badges (README, README.es, CHANGELOG)
4. Final `bash scripts/rebuild.sh` (rebuild main.ll + mnc_all.mn)
5. Final `python scripts/test_native.py --bless` (re-bless golden refs)
6. Full validation: `make test && make lint`
7. Verify CI is green on all jobs
8. Tag `v4.0.0` and release

## Post-v4.0.0 Roadmap (v4.1+)

Items deferred from the review or identified during this sprint:

### Performance (originally planned for v3.34-v3.36)
- Native driver: `mnc run hello.mn` in <100ms (no Python)
- Incremental compilation: <2s rebuild after single-file change
- Binary size optimization: <10MB stripped
- IR blowup ratio: <10x source-to-IR
- Compile-time benchmarks in CI

### Language Features
- `const` keyword in grammar and spec (Coral)
- Tensor proof-of-concept compilation demo (Coral)
- `Map` literal syntax for self-hosted code (Coral)

### Self-Hosted Compiler
- Migrate remaining ~480 bounded-for loops to while/break/continue
- Fix text emitter semantic checker false positives for self-hosted compilation
- Achieve full fixed-point: stage2 == stage3

### Code Quality
- Refactor `_emit_drop_glue` into template helper (Cobra)
- Thread-safe `mn_init_tag_strings` (Viper)
- Iterative signal propagation (Viper)
- Root `conftest.py` for shared test fixtures (Anaconda)
- Remove deprecated llvmlite emitter (`emit_llvm_mir.py`, 5,293 lines)

## Rules

- Do NOT add features in v4.0.0 — it is a quality gate only
- Run full validation before tagging
- Verify CI green on ALL jobs (ci, self-hosted, bootstrap, native, wasm, android, macOS/iOS)
- Use `/bump-version` for the version bump
- Commit message: `v4.0.0: production release`
