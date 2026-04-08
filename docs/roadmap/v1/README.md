# v1 — Stability & Production Readiness

**Era:** v1.0.0 through v1.3.0
**Theme:** Freeze the language, harden the compiler, build the ecosystem

---

## Goal

Stabilize the language (SPEC 1.0 Final), achieve self-hosted fixed-point verification, formalize memory model, then expand into AI, data, and web — all compiled to native code via LLVM.

## Headline Techs

- Language specification freeze (SPEC 1.0 Final)
- Self-hosted compiler: mnc-stage1 15/15 golden tests at -O1
- Formal memory model (arena lifecycle)
- ASan/TSan clean (52/52 C runtime tests)
- AI stdlib: LLM drivers (OpenAI, Anthropic, local), embeddings, RAG
- Data engine (Dato): DataFrames, aggregations, joins
- Database drivers: SQLite, PostgreSQL, Redis, KV
- Web platform: HTTP server toolkit, web crawler, vulnerability scanner, HTTP fuzzer

## Versions

| Version | Codename | Highlights |
|---------|----------|------------|
| **v1.0.0** | Stable | Language freeze, emitter hardening (25+ bugs fixed), formal memory model, stability policy, 15/15 golden, 3,600+ tests |
| **v1.0.1** | Critical Bug Fixes | `_EarlyReturn.err` fix, DWARF/version strings, C runtime atomics |
| **v1.0.2** | Type System Soundness | `UNKNOWN == X` -> `False`, `is_compatible_with()`, partial generic arity fix |
| **v1.0.3** | MIR Emitter Memory | Arena lifecycle in MIR emitter, boxed+closure allocs through arena |
| **v1.0.4** | Drop Glue | Arena-based cleanup (explicit drop glue deferred — LLVM dominance errors) |
| **v1.0.5** | Self-Hosted Emitter | 15/15 golden tests pass; mnc-stage1 self-compilation blocked by SIGSEGV |
| **v1.0.6** | Self-Compilation | CI job added; fixed-point blocked by v1.0.5 crashes |
| **v1.0.7** | Codegen Improvements | Relaxed SSA, strict_ssa mode, MIR verifier test suite (32 tests) |
| **v1.0.8** | Optimizer & Toolchain | Algebraic simplification (5 rules), `$CC` support, `--werror`, `-O1` release builds |
| **v1.0.9** | Stdlib & Language Polish | Match exhaustiveness checking, async-only-when-needed, stdlib dedup |
| **v1.0.10** | Production Hardening | ASan/TSan clean (52/52), C hardening pass, 3,697 tests |
| **v1.0.11** | Self-Hosted Compiler Fixes | Pointer-only large structs, stack alignment fix, **15/15 golden at -O1**, self-compilation unblocked |
| **v1.1.0** | AI Native | LLM drivers (OpenAI, Anthropic, local), embedding providers, RAG pipeline |
| **v1.2.0** | Data & Storage | Dato data engine, database drivers (SQLite, PostgreSQL, Redis, KV), TOML/YAML encoding, filesystem stdlib |
| **v1.3.0** | Web & Security | Web crawler, vulnerability scanner, HTTP fuzzer, HTTP server toolkit (auth, sessions, rate limiting, SSE) |

## Key Features Delivered

- Language specification frozen — no new syntax, semantic, or type system changes
- Stability policy: breaking changes require RFC + deprecation period
- Self-hosted compiler: mnc-stage1 producing working binaries, 15/15 golden at -O1
- Memory model formalized: arena lifecycle, drop glue design (partial)
- 11-patch hardening series (v1.0.1-v1.0.11) addressing 34 code review issues
- AI stdlib: LLM drivers for 3 providers, embedding with batching/caching, RAG with chunking
- Dato DataFrame library: tables, aggregations, joins, null handling, reshape, CSV/JSON I/O
- Database drivers: SQLite, PostgreSQL, Redis, KV store, connection pooling, migrations
- Encoding: TOML and YAML parsers/serializers
- Web platform: HTTP server toolkit, web crawler (robots.txt, frontier), vuln scanner, HTTP fuzzer
- Filesystem stdlib: read, write, walk, glob, metadata, temp files

## Lessons Learned

1. **Review-driven iteration works** — 7-reviewer panel at v1.0.0 found 34 issues; the v1.0.x patch series systematically addressed each one
2. **Drop glue is genuinely hard** — LLVM dominance errors across basic blocks forced deferral; arena handles most cases anyway
3. **Self-compilation crashes are systemic** — SIGSEGV on large modules (v1.0.5-v1.0.6) revealed deep codegen issues that took multiple patches
4. **Freeze before expand** — locking the language at v1.0.0 gave confidence to build AI/data/web stdlib without worrying about language churn
5. **Security by default** — parameterized SQL, validated FFI boundaries, ASan/TSan clean runtime from the start
6. **Python backend is legacy** — confirmed at v1.0.0, no new features on Python backend from this point forward

## Test Growth

3,600+ -> 3,697 -> 3,698 (v1.0.x hardening focused on quality, not quantity)
