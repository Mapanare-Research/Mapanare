# v3 — Syntax Overhaul & Self-Hosted Maturity

**Era:** v3.0.0 through v3.47.0
**Theme:** Radical syntax reform, fixed-point achievement, multi-language transpilation, production readiness gate

---

## Goal

Break everything. Redesign the syntax from scratch (indentation-based, bilingual keywords, radical token reduction). Add a C emit backend for simpler bootstrapping. Achieve fixed-point (stage3 == stage4). Build transpilers for Python, PHP, TypeScript, and Go. Harden everything for v4.0.0 production release.

## Headline Techs

- C emit backend (emit_c.mn) for portable bootstrapping
- Indentation-based syntax with bilingual keywords (Spanglish/English)
- tipo/modo type unification (struct+enum -> tipo, trait -> modo)
- Fixed-point verified: stage3 == stage4 (v3.3.0)
- Two-stage bootstrap from seed: no Python required
- Multi-language transpilers: Python, PHP, TypeScript, Go
- 15,000+ lines self-hosted .mn across 11 modules
- 40/40 golden tests, 4,845+ pytest, 7-reviewer 9.79/10 score

## Sub-Eras

### v3.0.x — Syntax Revolution (v3.0.0 - v3.0.3)

The snake bites its own tail. Zero backwards compatibility.

| Version | Highlights |
|---------|------------|
| **v3.0.0** | C emit backend, bilingual keywords, indentation syntax, tipo/modo, @Agent syntax, migration tool |
| **v3.0.1** | mnc-stage1 runs, string truncation blocks bootstrap |
| **v3.0.2** | 15/15 golden tests, struct names fixed |
| **v3.0.3** | 25/25 golden tests, PHI type recovery, __op_* fallback |

### v3.1.0 - v3.3.0 — Bootstrap & Fixed Point

| Version | Highlights |
|---------|------------|
| **v3.1.0** | Native file I/O, string escapes, runtime functions |
| **v3.2.0** | Seed binary updated, 25/25 golden verified |
| **v3.3.0** | **FIXED POINT: stage3 == stage4.** String-tagged dispatch, sret ABI fix, COW write-back, two-stage bootstrap from seed |

### v3.4.0 - v3.9.x — Language Completeness

| Version | Highlights |
|---------|------------|
| **v3.4.0** | Module imports, extern C functions, stdlib/math compiles+runs |
| **v3.5.0** | WASM stackifier, keyword-as-variable, native test runner |
| **v3.6.0** | Type system fixed, 35/35 stdlib, 25/25 golden, mnc test/build CLI |
| **v3.7.0** | Cross-module imports, 32MB thread, `mnc run`, 99 native assertions |
| **v3.8.0** | Compiler hardening: loop bounds, method return types, 104 native assertions |
| **v3.8.1** | **Generics + impl blocks:** monomorphization, trait dispatch, `impl Trait for Type` |
| **v3.9.0** | **Generic impl blocks:** `impl<T> Box<T>`, TraitDef variant, 31/31 golden, fixed point maintained |
| **v3.9.1** | CI green, generate .ref.ll for tests 16-31, clean artifacts |

### v3.10.0 - v3.23.0 — Semantic Maturity & Safety

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.10.0** | | Error messages with line numbers, generic enums, trait method validation |
| **v3.13.0** | Cascabel | Memory safety: string drop glue, range iterator fix, COW list, intern thread safety |
| **v3.14.0** | Cuaima | Generic arity validation, arithmetic traits, TypeInfo hash fix, tutorial syntax |
| **v3.15.0** | Coral | C runtime correctness: list_concat UB, Windows handler deadlock, COW atomics |
| **v3.16.0** | Lora | Concurrency: signal thread-local + lock, deep free for maps/streams, string align 8 |
| **v3.17.0** | Tigra | Text emitter drop glue, function attributes, closure env sizing |
| **v3.18.0** | Macagua | Container memory: drop glue for lists/maps/signals/streams, per-function arenas |
| **v3.19.0** | Tragavenado | Self-hosted completeness: while/break/continue/assert, for-loop type inference, InterpString |
| **v3.20.0** | Sapa | Type safety: arithmetic trait lowering, O2 convergence, _coerce_arg reduction |
| **v3.21.0** | Cascabel II | DX polish: REPL, test colors, docs fixes, native C tests, WASM stubs |
| **v3.22.0** | Puare | Performance: _coerce_arg phase 2, Any reduction, deepcopy replacement, tensor PoC |
| **v3.23.0** | Tragavenado II | Dynamic `any` type: tagged MnValue union, `typeof` builtin, gradual typing |

### v3.24.0 - v3.31.0 — Multi-Language Transpilation

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.24.0** | Macagua II | **Python transpiler:** `mapanare compile main.py`, class->struct, try/except->Result, type inference |
| **v3.25.0** | Cuaima | **PHP transpiler:** `mapanare compile app.php`, regex tokenizer, array heuristics, 47 tests |
| **v3.26.0** | Cunaguaro | Review gate: fix `any` type mapping, rebuild main.ll, PHP transpiler bugs |
| **v3.27.0** | Guio | **Transpiler framework:** shared transpiler.mn, TypeMapping, stdlib shim registry |
| **v3.28.0** | Danta | **Self-hosted Python transpiler:** from_python.mn, zero Python dependency for .py |
| **v3.29.0** | Morrocoy | **Self-hosted PHP transpiler:** from_php.mn, zero Python dependency for .php |
| **v3.30.0** | Turpial | **TypeScript transpiler:** interfaces->traits, classes->structs, async/await->agents |
| **v3.31.0** | Tonina | **Go transpiler:** goroutines->agents, channels->streams, error returns->Result |

### v3.32.0 - v3.47.0 — Production Gate

| Version | Codename | Highlights |
|---------|----------|------------|
| **v3.32.0** | Sapoara | Review hardening: fix all remaining code review findings |
| **v3.33.0** | Curito | Final polish: dead code removal, overhead elimination, edge case hardening |
| **v3.34.0** | Cachicamo | Zero-Python driver: `mnc run/build/compile` as default, <100ms startup |
| **v3.35.0** | Baquiro | Incremental compilation: hash-based caching, parallel modules, .mni interfaces, --watch |
| **v3.36.0** | Cunaguaro II | Performance: IR dedup <200K lines, binary <10MB, memory <512MB |
| **v3.37.0** | | MIR constant propagation, transpiler type inference, build obj path fix |
| **v3.38.0** | | Regenerate main.ll with GPU builtins, 40/40 golden through mnc-stage1 |
| **v3.39.0** | | str_concat early return, copy instead of borrow to prevent double-free |
| **v3.41.0** | Culebrita | IO Foundation: link mapanare_io.c, read_line(), file I/O fixes, 35/35 golden |
| **v3.42.0** | | Network native: TCP/TLS/HTTP client, crypto, regex from native binaries |
| **v3.43.0** | | Agent runtime: spawn/send/sync with real OS threads |
| **v3.44.0** | | Real examples: ALL examples run, transpile .py/.php end-to-end |
| **v3.45.0** | Turpial | Package manager: `mapanare install` works, error recovery, docs updated |
| **v3.46.0** | | GPU foundation: link mapanare_gpu.c, device detection, kernel launch |
| **v3.47.0** | Guacamaya | GPU examples: vector_add.mn, matmul_bench.mn, SPEC Section 23, v4.0.0 gate |

## Key Features Delivered

- C emit backend for portable bootstrapping (no LLVM dependency for seed build)
- Radical syntax: indentation-based, bilingual (Spanglish/English), 25% token reduction
- tipo/modo unification: struct+enum -> tipo, trait -> modo
- Fixed-point verification: stage3 == stage4 (the compiler produces identical output when compiling itself twice)
- Two-stage bootstrap from seed binary: no Python required to build the compiler
- Self-hosted compiler: 15,000+ lines across 11 modules (ast, lexer, parser, semantic, mir, lower_state, lower, emit_llvm_ir, emit_llvm, emit_c, main)
- Generic functions, structs, and enums with monomorphization
- impl blocks (inherent + trait), trait bounds validation
- Dynamic `any` type with tagged union and runtime dispatch
- Multi-language transpilation: Python, PHP, TypeScript, Go -> Mapanare
- Transpiler framework: shared TypeMapping, stdlib shims, AST conversion
- 40/40 golden tests, 4,845+ pytest tests
- 7-reviewer code review score: 9.79/10 (unanimous PASS, zero CRITICAL/HIGH issues)
- Full I/O: TCP, TLS, HTTP client, crypto, regex, file I/O, stdin, all linked into native binaries
- Agent runtime: spawn/send/sync with real OS threads
- Package manager: install, dependency resolution, example packages
- GPU: device detection, kernel launch, vector_add/matmul examples

## Lessons Learned

1. **Zero users = zero concerns** — v3.0.0 broke everything intentionally; the freedom to redesign syntax without backwards compatibility was invaluable
2. **Fixed-point is the ultimate compiler test** — stage3 == stage4 at v3.3.0 proved the compiler is correct end-to-end
3. **Venezuelan fauna codenames** — Cascabel, Cuaima, Coral, Lora, Tigra, Macagua, Turpial, Guacamaya... gave identity to each milestone
4. **Transpilation is natural** — Python/PHP/TypeScript/Go features map cleanly to Mapanare concepts (class->struct, try/except->Result, goroutine->agent)
5. **Review-driven gates work** — v3.26.0 and v3.32.0 were explicit "fix all review findings" gates before proceeding
6. **The v3.x series was the longest** — 47+ releases spanning syntax reform, language completeness, transpilers, and production gate. Future major versions should be scoped tighter.
7. **Link what's already written** — v3.41.0's theme was "link mapanare_io.c"; the C runtime code existed since v0.8.0 but wasn't wired into native binaries until v3.41.0
8. **Code quality is measurable** — going from 6.6/10 (v0.2.0) to 9.79/10 (v3.40.0) in code review scores across the project lifetime

## Test Growth

4,465+ -> 4,845+ (quality over quantity in v3.x — focus was on golden test coverage and code review scores)
