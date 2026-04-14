---
era: v1
versions: v1.0.0 - v1.3.0
theme: Stability & Production
releases: 4
patches: 11
tests_start: 3600
tests_end: 3698
---

# v1 Era -- Stability & Production

Four releases plus an 11-patch hardening series. The language froze. The compiler proved itself. The ecosystem expanded.

## Summary

[[v1.0.0]] shipped SPEC 1.0 Final -- no new syntax, semantic, or type system changes from this point. The language was frozen so the ecosystem could grow on stable ground. A 7-reviewer panel found 34 issues at v1.0.0, spawning the v1.0.1 through [[v1.0.11]] patch series that systematically addressed each one. By v1.0.11, mnc-stage1 passed 15/15 golden tests at -O1 and the C runtime was ASan/TSan clean (52/52 tests).

With the compiler hardened, the era expanded outward: AI stdlib (OpenAI, Anthropic, local LLM drivers) at [[v1.1.0]], data engine (Dato DataFrames, database drivers) at [[v1.2.0]], and web platform (HTTP server toolkit, web crawler, vulnerability scanner, fuzzer) at [[v1.3.0]].

## Versions

| Version | Highlights |
|---------|------------|
| **v1.0.0** | Language freeze. SPEC 1.0 Final. Emitter hardening (25+ bugs). Formal memory model. Stability policy. 15/15 golden. 3,600+ tests |
| **v1.0.1 - v1.0.4** | Critical bug fixes, type system soundness, MIR emitter memory, arena lifecycle for drop glue |
| **v1.0.5 - v1.0.6** | Self-hosted emitter passes 15/15 golden. Self-compilation blocked by SIGSEGV on large modules |
| **v1.0.7 - v1.0.8** | Relaxed SSA, MIR verifier test suite (32 tests), algebraic simplification, `-O1` release builds |
| **v1.0.9 - v1.0.10** | Match exhaustiveness, ASan/TSan clean (52/52 C runtime tests), 3,697 tests |
| **v1.0.11** | Pointer-only large structs, stack alignment fix. **15/15 golden at -O1.** Self-compilation unblocked |
| **v1.1.0** | AI Native. LLM drivers (OpenAI, Anthropic, local), embedding providers, RAG pipeline |
| **v1.2.0** | Data & Storage. Dato data engine, database drivers (SQLite, PostgreSQL, Redis, KV), TOML/YAML |
| **v1.3.0** | Web & Security. HTTP server toolkit, web crawler, vulnerability scanner, HTTP fuzzer |

## Headline Technologies

- **SPEC 1.0 Final** -- language specification frozen, stability policy with RFC requirement for breaking changes
- **mnc-stage1** producing working binaries, 15/15 golden at -O1
- **Formal memory model** -- arena lifecycle documented, drop glue design (partial, LLVM dominance errors forced deferral)
- **ASan/TSan clean** -- 52/52 C runtime tests pass under both sanitizers
- **AI stdlib**: LLM drivers for 3 providers, embedding with batching/caching, RAG with chunking
- **Dato**: DataFrames, aggregations, joins, null handling, CSV/JSON I/O
- **Database drivers**: SQLite, PostgreSQL, Redis, KV store, connection pooling, migrations

## Key Decisions

1. **Freeze before expand.** Locking the language at v1.0.0 gave confidence to build AI/data/web stdlib without worrying about language churn.
2. **Review-driven iteration.** The 7-reviewer panel at v1.0.0 found 34 issues; the 11-patch series systematically addressed each one. This pattern became the project standard.
3. **Python backend is legacy.** Confirmed at v1.0.0. No new features on the Python backend from this point forward.

## Lessons Learned

- Drop glue is genuinely hard. LLVM dominance errors across basic blocks forced deferral. Arena handles most cases, but the general solution waited until [[v4 Era - Production|v4.3.0]].
- Self-compilation crashes are systemic. SIGSEGV on large modules (v1.0.5-v1.0.6) revealed deep codegen issues that took multiple patches to resolve.
- Security by default matters. Parameterized SQL, validated FFI boundaries, ASan/TSan clean runtime from the start.

## Test Growth

3,600+ -> 3,697 -> 3,698 (hardening series focused on quality, not quantity)

## See Also

- [[v0 Era - Foundation]] -- previous era
- [[Timeline]] -- full project history
- [[v2 Era - Platform Expansion]] -- next era
