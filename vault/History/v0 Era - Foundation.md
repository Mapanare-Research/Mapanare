---
era: v0
versions: v0.1.0 - v0.9.0
theme: Foundation & Bootstrap
releases: 9
tests_start: 1400
tests_end: 3400
---

# v0 Era -- Foundation & Bootstrap

Nine releases from blank repo to self-hosting compiler with native stdlib. Everything that came after was built on this foundation.

## Summary

The v0 era started with a Lark LALR parser and dual emitters (Python transpiler + LLVM IR via llvmlite). Self-hosting arrived at [[v0.2.0]] -- 5,800+ lines of Mapanare compiling themselves through the bootstrap compiler. The MIR pipeline landed at [[v0.6.0]], introducing an SSA-based intermediate representation with ~35 instruction types, an optimizer (O0-O3), and dual emitters. The Python bootstrap was frozen at v0.6.0 and never touched again.

By [[v0.9.0]] the native stdlib shipped: JSON, CSV, HTTP, WebSocket, crypto, regex -- all written in `.mn`, all compiled to LLVM IR without Python. The C runtime grew from scratch to include arena-based memory (no GC), lock-free SPSC ring buffers, a thread pool with work stealing, TCP sockets, TLS (OpenSSL via dlopen), file I/O, and an event loop (epoll/select).

3,400+ tests by the end of the era.

## Versions

| Version | Highlights |
|---------|------------|
| **v0.1.0** | Bootstrap compiler, Lark parser, semantic checker, Python + LLVM emitters, runtime, LSP, VS Code extension, CLI, stdlib, 1,400+ tests |
| **v0.2.0** | First self-compilation. LLVM string/list codegen, C runtime (ring buffers, thread pool), self-hosted lexer + parser + semantic + emitter (5,800+ lines .mn) |
| **v0.3.0** | Traits, module resolution, LLVM agent codegen, arena memory, TypeKind enum, 1,960+ tests |
| **v0.3.1** | Dynamic versioning from VERSION file, documentation tests |
| **v0.4.0** | Scope cleanup, C runtime hardening (sanitizers, CI), structured diagnostics, C FFI, self-hosted verification |
| **v0.5.0** | String interpolation, linter, Python interop, WASM playground, package registry, doc generator, 2,200+ tests |
| **v0.6.0** | MIR pipeline (SSA IR, lowering, optimizer, dual emitters). Bootstrap frozen at this version. 2,500+ tests |
| **v0.7.0** | Self-hosted MIR lowering (lower.mn), built-in test runner, agent observability, DWARF debug info, 2,983 tests |
| **v0.8.0** | LLVM backend parity (maps, signals, streams, closures), complete string methods, C runtime TCP/TLS/file I/O/event loop, 3,020 tests |
| **v0.9.0** | Native stdlib in .mn (JSON, CSV, HTTP, WebSocket, crypto, regex), cross-module LLVM compilation, 3,400+ tests |

## Headline Technologies

- **Lark LALR parser** with 13-level precedence climbing
- **Dual emitters**: Python transpiler + LLVM IR via llvmlite
- **SSA-based MIR** intermediate representation with ~35 instruction types
- **Arena-based C runtime** -- no garbage collector, deterministic lifetimes
- **Lock-free SPSC ring buffers** for agent message passing
- **Thread pool with work stealing** for concurrent task execution
- **Self-hosted compiler**: 8,288+ lines of `.mn` across 7 modules by end of era

## Key Decisions

1. **Arena memory over GC.** Simpler, faster, predictable lifetimes. This decision defined the runtime's character for every subsequent era.
2. **MIR as the right abstraction.** SSA IR between AST and emission enabled optimizer passes and multiple backends without duplicating logic.
3. **Bootstrap freeze at v0.6.0.** Locking the Python compiler gave a stable reference point. All future self-hosted work measures against this frozen snapshot.
4. **Recursive descent for self-hosted.** The self-hosted parser uses recursive descent, not Lark -- critical for Python independence.

## Lessons Learned

- Code review at v0.2.0 returned 6.6/10 median. All v0.3.0 work directly addressed those concerns. Review-driven iteration works from the start.
- Moving `experimental/` out of core (v0.4.0) clarified what the language actually is. Scope reduction pays off.
- LLVM string memory management was a recurring issue from v0.1.0 through v0.8.0. String leaks are genuinely hard in a systems language without GC.

## Test Growth

1,400 -> 1,960 -> 2,200 -> 2,500 -> 2,983 -> 3,020 -> 3,400+

## See Also

- [[Timeline]] -- full project history
- [[v1 Era - Stability]] -- next era
