---
era: v3
versions: v3.0.0 - v3.47.0
theme: Syntax Overhaul & Self-Hosted Maturity
releases: 48
tests_end: 4845
panel_score: 9.79
---

# v3 Era -- Syntax Revolution

Forty-eight releases -- the longest era. Zero backwards compatibility. The snake bites its own tail.

## Summary

[[v3.0.0]] broke everything on purpose: indentation-based syntax, bilingual keywords (`tipo`/`modo`/`@agent`), 25% fewer tokens. A C emit backend enabled portable bootstrapping without an LLVM dependency. Fixed-point was achieved at [[v3.3.0]] -- stage3 produces identical output to stage4, proving the compiler correct end-to-end. Two-stage bootstrap from seed binary means no Python required to build the compiler.

The middle era (v3.4.0 - v3.23.0) built out language completeness: generics with monomorphization, impl blocks (inherent + trait), trait bounds validation, memory safety (string drop glue, COW lists, string interning with thread safety), and the dynamic `any` type with tagged union dispatch.

The transpiler arc (v3.24.0 - v3.31.0) added Python, PHP, TypeScript, and Go transpilers -- each language's features map cleanly to Mapanare concepts (class to struct, try/except to Result, goroutine to agent, channel to stream).

The production gate (v3.32.0 - v3.47.0) hardened everything: incremental compilation, zero-Python driver, real I/O linked into native binaries, agent runtime with OS threads, package manager, GPU device detection and kernel launch. The era closed with [[v3.47.0]] at 9.79/10 from the 7-reviewer panel -- unanimous PASS, zero CRITICAL/HIGH issues. Ready for v4.0.0.

Venezuelan fauna codenames gave identity to each milestone: Cascabel, Cuaima, Coral, Lora, Tigra, Macagua, Tragavenado, Turpial, Guacamaya, and more.

40/40 golden tests. 4,845+ pytest. 15,000+ lines of self-hosted `.mn` across 11 modules.

## Sub-Eras

### v3.0.x -- Syntax Revolution (v3.0.0 - v3.0.3)

| Version | Highlights |
|---------|------------|
| **v3.0.0** | C emit backend, bilingual keywords, indentation syntax, tipo/modo, @Agent syntax, migration tool |
| **v3.0.1** | mnc-stage1 runs, string truncation blocks bootstrap |
| **v3.0.2** | 15/15 golden tests, struct names fixed |
| **v3.0.3** | 25/25 golden tests, PHI type recovery, `__op_*` fallback |

### v3.1.0 - v3.3.0 -- Bootstrap & Fixed Point

| Version | Highlights |
|---------|------------|
| **v3.1.0** | Native file I/O, string escapes, runtime functions |
| **v3.2.0** | Seed binary updated, 25/25 golden verified |
| **v3.3.0** | **FIXED POINT: stage3 == stage4.** String-tagged dispatch, sret ABI fix, COW write-back, two-stage bootstrap from seed |

### v3.4.0 - v3.9.x -- Language Completeness

| Version | Highlights |
|---------|------------|
| **v3.4.0** | Module imports, extern C functions, stdlib/math compiles and runs |
| **v3.5.0** | WASM stackifier, keyword-as-variable, native test runner |
| **v3.6.0** | Type system fixed, 35/35 stdlib, 25/25 golden, `mnc test/build` CLI |
| **v3.7.0** | Cross-module imports, 32MB thread stack, `mnc run`, 99 native assertions |
| **v3.8.0** | Loop bounds, method return types, substr fix, 104 native assertions |
| **v3.8.1** | Generics + impl blocks: monomorphization, trait dispatch, `impl Trait for Type` |
| **v3.9.0** | Generic impl blocks: `impl<T> Box<T>`, TraitDef variant, 31/31 golden, fixed point maintained |
| **v3.9.1** | CI green, generate `.ref.ll` for tests 16-31, clean artifacts |

### v3.10.0 - v3.23.0 -- Semantic Maturity & Safety

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.10.0** | -- | Error messages with line numbers, generic enums, trait method validation |
| **v3.13.0** | Cascabel | Memory safety: string drop glue, range iterator fix, COW list, intern thread safety |
| **v3.14.0** | Cuaima | Generic arity validation, arithmetic traits, TypeInfo hash fix |
| **v3.15.0** | Coral | C runtime correctness: list_concat UB, Windows handler deadlock, COW atomics |
| **v3.16.0** | Lora | Concurrency: signal thread-local + lock, deep free for maps/streams, string align 8 |
| **v3.17.0** | Tigra | Text emitter drop glue, function attributes, closure env sizing |
| **v3.18.0** | Macagua | Container memory: drop glue for lists/maps/signals/streams, per-function arenas |
| **v3.19.0** | Tragavenado | Self-hosted completeness: while/break/continue/assert, for-loop type inference |
| **v3.20.0** | Sapa | Type safety: arithmetic trait lowering, O2 convergence, `_coerce_arg` reduction |
| **v3.21.0** | Cascabel II | DX polish: REPL, test colors, docs fixes, native C tests |
| **v3.22.0** | Puare | Performance: `_coerce_arg` phase 2, Any reduction, deepcopy replacement, tensor PoC |
| **v3.23.0** | Tragavenado II | Dynamic `any` type: tagged MnValue union, `typeof` builtin, gradual typing |

### v3.24.0 - v3.31.0 -- Multi-Language Transpilation

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.24.0** | Macagua II | Python transpiler: class to struct, try/except to Result, type inference |
| **v3.25.0** | Cuaima | PHP transpiler: regex tokenizer, array heuristics, 47 tests |
| **v3.26.0** | Cunaguaro | Review gate: fix `any` type mapping, rebuild main.ll, PHP transpiler bugs |
| **v3.27.0** | Guio | Transpiler framework: shared `transpiler.mn`, TypeMapping, stdlib shim registry |
| **v3.28.0** | Danta | Self-hosted Python transpiler: `from_python.mn`, zero Python dependency |
| **v3.29.0** | Morrocoy | Self-hosted PHP transpiler: `from_php.mn`, zero Python dependency |
| **v3.30.0** | Turpial | TypeScript transpiler: interfaces to traits, classes to structs, async/await to agents |
| **v3.31.0** | Tonina | Go transpiler: goroutines to agents, channels to streams, error returns to Result |

### v3.32.0 - v3.47.0 -- Production Gate

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.32.0** | Sapoara | Review hardening: fix all remaining code review findings |
| **v3.33.0** | Curito | Final polish: dead code removal, overhead elimination |
| **v3.34.0** | Cachicamo | Zero-Python driver: `mnc run/build/compile` as default, <100ms startup |
| **v3.35.0** | Baquiro | Incremental compilation: hash-based caching, parallel modules, .mni interfaces |
| **v3.36.0** | Cunaguaro II | Performance: IR dedup <200K lines, binary <10MB, memory <512MB |
| **v3.37.0** | Araguato | Safe list growth, `no_drop_glue` removed, self-compilation restored (123MB, <1s) |
| **v3.38.0** | -- | Regenerate main.ll with GPU builtins, 40/40 golden through mnc-stage1 |
| **v3.39.0** | -- | `str_concat` early return, copy instead of borrow to prevent double-free |
| **v3.41.0** | Culebrita | IO Foundation: link `mapanare_io.c`, `read_line()`, file I/O fixes |
| **v3.42.0** | -- | Network native: TCP/TLS/HTTP client, crypto, regex from native binaries |
| **v3.43.0** | -- | Agent runtime: spawn/send/sync with real OS threads |
| **v3.44.0** | -- | Real examples: ALL examples run, transpile .py/.php end-to-end |
| **v3.45.0** | Turpial | Package manager: `mapanare install` works, error recovery, docs updated |
| **v3.46.0** | -- | GPU foundation: link `mapanare_gpu.c`, device detection, kernel launch |
| **v3.47.0** | Guacamaya | GPU examples: vector_add.mn, matmul_bench.mn, SPEC Section 23, v4.0.0 gate |

## Headline Technologies

- **C emit backend** (`emit_c.mn`) for portable bootstrapping without LLVM
- **Indentation syntax** with bilingual keywords (Spanglish/English)
- **tipo/modo unification**: struct+enum become `tipo`, trait becomes `modo`
- **Fixed-point verification**: stage3 == stage4 at v3.3.0
- **Two-stage bootstrap from seed binary**: no Python required
- **15,000+ lines self-hosted `.mn`** across 11 modules
- **Generic functions, structs, enums** with monomorphization
- **impl blocks** (inherent + trait) with trait bounds validation
- **Dynamic `any` type** with tagged union and runtime dispatch
- **Multi-language transpilers**: Python, PHP, TypeScript, Go to Mapanare
- **Agent runtime** with real OS threads (spawn/send/sync)

## Key Decisions

1. **Zero backwards compatibility.** With zero users, the freedom to redesign syntax without migration concerns was invaluable. This opportunity does not come twice.
2. **Fixed-point as proof of correctness.** stage3 == stage4 at v3.3.0 proved the compiler correct end-to-end. The most rigorous test possible.
3. **Review-driven gates.** v3.26.0 and v3.32.0 were explicit "fix all review findings" gates before proceeding. This pattern drove quality from 6.6/10 at v0.2.0 to 9.79/10 at v3.47.0.
4. **Link what's already written.** The C runtime code for I/O existed since v0.8.0 but was not wired into native binaries until v3.41.0.

## Lessons Learned

- The v3.x series was the longest era -- 48 releases spanning syntax reform, language completeness, transpilers, and production gate. Future major versions should be scoped tighter.
- Transpilation is natural. Python/PHP/TypeScript/Go features map cleanly to Mapanare concepts.
- Venezuelan fauna codenames (Cascabel, Cuaima, Coral, Lora, Tigra, Macagua, Turpial, Guacamaya) gave identity and character to the project.
- Code quality is measurable: 6.6/10 at v0.2.0 to 9.79/10 at v3.47.0 across the project lifetime.

## Test Growth

4,465+ -> 4,845+ (quality over quantity -- focus was on golden test coverage and code review scores)

## See Also

- [[v2 Era - Platform Expansion]] -- previous era
- [[Timeline]] -- full project history
- [[v4 Era - Production]] -- next era
