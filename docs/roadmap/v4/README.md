# v4 — Production Release

**Era:** v4.0.0+
**Theme:** Build real programs. Install -> write -> compile -> run.

---

## Goal

Other people can use it. A developer who isn't the compiler author can install Mapanare, write a program, compile it, and run it. CLI tools, file processors, HTTP clients, GPU programs — all work end-to-end.

## Headline Techs

- Self-hosted compiler: 15,000+ lines of .mn, 11 modules
- 40/40 golden tests, 4,845+ pytest tests
- 7-reviewer code review: 9.79/10 (unanimous PASS)
- Fixed-point verified: the compiler compiles itself
- All C runtime modules linked: core, IO, runtime, GPU
- Multi-language transpilation: Python, PHP, TypeScript, Go
- Package manager: install, dependency resolution
- Full I/O: TCP, TLS, HTTP, crypto, regex, file, stdin

## Versions

| Version | Codename | Highlights |
|---------|----------|------------|
| **v4.0.0** | Mapanare | Production release. Build CLI tools, file processors, HTTP clients, GPU programs. Full install->write->compile->run workflow. |

## What v4.0.0 Means

A user can:

1. **Write a CLI program** — read stdin, process files, write output
2. **Fetch data over HTTP** — from a native binary, no Python
3. **Transpile code** — .py/.php/.ts/.go file to Mapanare and run natively
4. **Install a package** — `mapanare install` with dependency resolution
5. **Get useful errors** — error messages with line numbers, Levenshtein suggestions
6. **Use GPU** — @gpu annotated functions with graceful CPU fallback

## Prerequisites (all completed)

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
2. **The gap between "compiler works" and "language is usable" is large** — v3.41.0 through v3.47.0 were all about bridging that gap (linking existing C code, adding stdin, wiring examples)
3. **Cumulative quality compounds** — 9.79/10 review score didn't happen at once; it accumulated across 70+ versions of systematic improvement

## What's Next

- **v4.1.0** — Post-production improvements (TBD)
