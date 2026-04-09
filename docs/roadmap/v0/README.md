# v0 — Foundation & Bootstrap

**Era:** v0.1.0 through v0.9.0
**Theme:** From concept to self-hosting compiler with native stdlib

---

## Goal

Build a working compiler from scratch: parser, type checker, emitters, runtime, tooling. Then bootstrap it — write the compiler in its own language. End with native stdlib modules that compile to LLVM IR without Python.

## Headline Techs

- Lark LALR parser with 13-level precedence climbing
- Dual emitters: Python transpiler + LLVM IR via llvmlite
- SSA-based MIR intermediate representation
- Arena-based C runtime (no GC)
- Lock-free SPSC ring buffers, thread pool with work stealing
- Self-hosted compiler: 8,288+ lines of `.mn` across 7 modules

## Versions

| Version | Codename | Highlights |
|---------|----------|------------|
| **v0.1.0** | Foundation | Bootstrap compiler, Lark parser, semantic checker, Python + LLVM emitters, runtime, LSP, VS Code extension, CLI, stdlib, 1,400+ tests |
| **v0.2.0** | Self-Hosting | LLVM string/list codegen, C runtime (ring buffers, thread pool), self-hosted lexer + parser + semantic + emitter (5,800+ lines .mn) |
| **v0.3.0** | Depth Over Breadth | Traits, module resolution, LLVM agent codegen, arena memory, TypeKind enum, getting started guide, 1,960+ tests |
| **v0.3.1** | Release Polish | Dynamic versioning from VERSION file, documentation tests |
| **v0.4.0** | Ready for the World | Scope cleanup, C runtime hardening (sanitizers, CI), structured diagnostics, C FFI, self-hosted verification, LSP improvements |
| **v0.5.0** | The Ecosystem | String interpolation, linter, Python interop, WASM playground, package registry, doc generator, 2,200+ tests |
| **v0.6.0** | Compiler Infrastructure | MIR pipeline (SSA IR, lowering, optimizer, dual emitters), bootstrap frozen at v0.6.0, 2,500+ tests |
| **v0.7.0** | Self-Standing | Self-hosted MIR lowering (lower.mn), built-in test runner, agent observability, DWARF debug info, deployment infra, 2,983 tests |
| **v0.8.0** | Native Parity | LLVM backend parity (maps, signals, streams, closures), complete string methods, C runtime expansion (TCP, TLS, file I/O, event loop), 3,020 tests |
| **v0.9.0** | Connected | Native stdlib in .mn (JSON, CSV, HTTP, WebSocket, crypto, regex), cross-module LLVM compilation, 3,400+ tests |

## Key Features Delivered

- Full compiler pipeline: source -> Lark parser -> AST -> semantic checker -> MIR -> optimizer -> emitter
- All core language features: functions, structs, enums, pattern matching, generics, agents, signals, streams, pipes
- Python runtime: asyncio agents, reactive signals, async streams, Result/Option
- LLVM backend: full parity with Python backend by v0.8.0
- C runtime: arena memory, SPSC ring buffers, thread pool, TCP/TLS, file I/O, event loop
- Developer tooling: CLI, LSP, VS Code extension, formatter, linter, test runner, doc generator
- Self-hosted compiler: 8,288+ lines of .mn (lexer, ast, parser, semantic, lower, emit_llvm, main)
- MIR pipeline: SSA-based IR with ~35 instruction types, optimizer (O0-O3), dual emitters
- Native stdlib: JSON, CSV, HTTP, WebSocket, crypto, regex — all .mn, all LLVM-compiled
- Package registry, WASM playground, getting started guide, language reference, cookbook

## Lessons Learned

1. **Self-hosted uses recursive descent, not Lark** — critical for Python independence
2. **Arena memory beats GC** — simpler, faster, predictable lifetimes for a systems language
3. **MIR is the right abstraction** — SSA IR between AST and emission enables optimizer passes and multiple backends without duplicating logic
4. **Bootstrap freeze is liberating** — freezing the Python compiler at v0.6.0 gave a stable reference point for all future self-hosted work
5. **Code review drives quality** — v0.2.0 reviewed at 6.6/10 median; all v0.3.0 work directly addressed those concerns
6. **Scope reduction pays off** — moving experimental/ out of core (v0.4.0) clarified what the language actually is
7. **String leaks are hard** — LLVM string memory management was a recurring issue from v0.1.0 through v0.8.0

## Test Growth

1,400+ -> 1,960+ -> 2,200+ -> 2,500+ -> 2,983 -> 3,020 -> 3,400+
