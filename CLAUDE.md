# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mapanare is an AI-native compiled programming language (v0.7.0) with first-class agents, signals, streams, and tensors. It compiles to Python (transpiler, legacy) and LLVM IR (native backend via llvmlite). The self-hosted compiler is 8,288+ lines of `.mn` across 7 modules in `mapanare/self/`. The project is on a path to full Python independence — stdlib modules will be rewritten in `.mn` and compiled natively.

## Current Version & Roadmap

- **v0.7.0** (current) — Self-hosted compiler, MIR pipeline, test runner, observability, DWARF debug
- **v0.8.0** (next) — LLVM backend parity: maps, signals, streams, closures + C runtime expansion (TCP, TLS, file I/O, event loop)
- **v0.9.0** — Native stdlib in `.mn`: HTTP client/server, JSON, WebSocket, regex, crypto
- **v1.0.0** — Language freeze, self-hosted fixed-point, formal memory model
- **v1.1.0** — AI native: LLM drivers, embeddings, RAG as stdlib
- **v1.2.0** — Data & storage: SQL drivers, Dato v1.0, YAML/TOML
- **v1.3.0** — Web platform & security: crawler, vulnerability scanner, web framework
- **v2.0.0** — GPU, WASM, mobile, Python backend deprecated

See `docs/roadmap/ROADMAP.md` for the full roadmap and `docs/roadmap/v0.8.0/PLAN.md` for the current execution plan.

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v
make lint             # ruff check . && black --check . && mypy mapanare/ runtime/
make fmt              # black . && ruff check --fix .
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches and egg-info

# Run specific tests
pytest tests/parser/ -v              # Parser tests only
pytest tests/semantic/test_types.py  # Single test file
pytest tests/llvm/ -v                # LLVM emitter tests
pytest tests/bootstrap/ -v           # Self-hosted compiler tests
```

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I rules), **MyPy** strict mode
- Target Python 3.11+ (for bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source → Lark LALR parser → AST (dataclasses) → Semantic checker → MIR lowering → MIR optimizer (O0-O3) → Emitter
                                                                                                                 ├→ emit_python.py     → Python source (legacy)
                                                                                                                 ├→ emit_python_mir.py → Python source (MIR-based)
                                                                                                                 ├→ emit_llvm.py       → LLVM IR (AST-based)
                                                                                                                 └→ emit_llvm_mir.py   → LLVM IR (MIR-based, preferred)
```

Key modules in `mapanare/`:
- `cli.py` — Entry point, command dispatch (run, build, jit, check, compile, emit-llvm, emit-mir, fmt, test, lint, doc, deploy, init)
- `parser.py` — Lark transformer: parse tree → AST dataclass nodes
- `ast_nodes.py` — All AST node definitions
- `semantic.py` — Two-pass type checker and scope resolver
- `mir.py` / `mir_builder.py` — MIR data structures and builder
- `lower.py` — AST → MIR lowering (1,397 lines)
- `mir_opt.py` — MIR optimizer passes (constant folding, DCE, copy propagation, block merging)
- `optimizer.py` — AST-level optimizer (constant folding, DCE, agent inlining, stream fusion)
- `emit_python.py` — Python transpiler (agents→asyncio, signals→reactive, streams→async generators)
- `emit_python_mir.py` — MIR-based Python transpiler
- `emit_llvm.py` — LLVM IR generation via llvmlite (AST-based)
- `emit_llvm_mir.py` — LLVM IR generation via llvmlite (MIR-based, preferred for new features)
- `types.py` — **Single source of truth** for the type system (TypeKind enum, TypeInfo, builtin registries)
- `mapanare.lark` — LALR grammar with 13-level precedence climbing
- `tracing.py` — OpenTelemetry-compatible tracing
- `diagnostics.py` — Rust-style structured error output
- `test_runner.py` — Built-in test runner for `mapanare test`
- `deploy.py` — Deployment scaffolding (Dockerfile, health checks)

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`, `result.py`, `deploy.py` — asyncio-based agents, reactive signals, async stream operators, Result/Option types, deployment infrastructure. **Legacy — will be replaced by native .mn stdlib.**

**Native C runtime** (`runtime/native/`): Arena-based memory (no GC), lock-free SPSC ring buffers, thread pool with work stealing, agent lifecycle, trace hooks. Used by the LLVM backend. **Expanding in v0.8.0** to include TCP sockets, TLS (OpenSSL), file I/O, and event loop primitives.

## LLVM Backend Status (v0.7.0 — honest assessment)

**Working:** Functions, structs, enums, pattern matching, control flow, type inference, generics, Result/Option, print/println, builtins, lists, agents (full lifecycle), traits, module imports, pipes (`|>` for function application).

**Partial:** String methods (7 of 12), signals (get/set only, no reactivity), closures (no capture).

**Not working:** Maps/Dicts (NotImplementedError), streams (stub), pipe definitions (multi-agent composition), stdlib modules (Python-only).

New LLVM features should target `emit_llvm_mir.py` (MIR-based emitter), not `emit_llvm.py` (AST-based).

## Type System (mapanare/types.py)

All type definitions, builtin registries, and type-name mappings live in `types.py`:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP, OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println, len, str, int, float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare→Python name mapping used by emitters
- `PYTHON_TYPE_MAP`: Type→Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

7 modules, 8,288+ lines of Mapanare. Mirrors the Python bootstrap pipeline:

| Module | Lines | Role |
|--------|-------|------|
| `lexer.mn` | 498 | Character-by-character tokenizer |
| `ast.mn` | 255 | AST node definitions (structs + enums) |
| `parser.mn` | 1,721 | Recursive descent parser, 13-level precedence |
| `semantic.mn` | 1,607 | Two-pass type checker and scope resolver |
| `lower.mn` | 2,629 | AST → MIR lowering |
| `emit_llvm.mn` | 1,497 | MIR → LLVM IR string emitter |
| `main.mn` | 81 | Compiler driver |

**Patterns:** Constructor functions (`let r: T = first_field; return r`), state-threading (functions thread state structs), no struct literal syntax in grammar yet.

**Fixed-point verification** blocked by cross-module LLVM compilation (v0.9.0) and enum lowering gaps.

## Key Conventions

- Grammar lives in `mapanare/mapanare.lark` (also bootstrapped copy in `bootstrap/`)
- Emitters detect used features (agents, signals, streams) and import only as needed
- Builtins are dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted compiler sources are in `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Design philosophy: `docs/manifesto.md` | RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Current plan: `docs/roadmap/v0.8.0/PLAN.md`
- Version tracked in `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

Starting with v0.8.0, the project moves toward Python independence:
- **Stdlib in .mn:** New stdlib modules are written in Mapanare (`.mn`), compiled to native code via LLVM. No more Python `.py` stdlib files.
- **C runtime as foundation:** OS-level primitives (sockets, TLS, file I/O) live in the C runtime. Everything above (HTTP, JSON, routing) is pure Mapanare.
- **Test on LLVM:** Every test should run on the LLVM backend, not just Python.
- **Python backend = legacy:** Kept for reference and bootstrapping, but not the target for new features.

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame/data analysis package (pandas+numpy replacement), written in .mn
- Future packages: `net/crawl` (web crawler), `security/scan` (vulnerability scanner), AI/LLM drivers

## CI

GitHub Actions on push/PR to `dev`: format check (black) → lint (ruff) → type check (mypy) → tests (pytest). Matrix: Python 3.11, 3.12 on Ubuntu.
