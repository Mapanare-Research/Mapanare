# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Memory management RFC (`docs/rfcs/0002-memory-management.md`) — arena + RC hybrid strategy
- Arena allocator in C runtime (`mn_arena_create`, `mn_arena_alloc`, `mn_arena_destroy`)
- Proper `__mn_str_free` with heap/constant tagging via LSB tag bit
- `__mn_list_free_strings` for freeing list-contained elements
- Scope-based arena insertion in LLVM emitter — arenas created at function entry, destroyed at exit
- Agent-scoped arena API stubs (wiring deferred to Phase 2.1)
- Memory stress tests (`tests/native/test_memory_stress.py`)
- `TypeKind` enum with 25 type kinds and `TypeInfo` dataclass in `mapanare/types.py`
- Canonical builtin registries (`BUILTIN_FUNCTIONS`, `BUILTIN_CALL_MAP`, `PYTHON_TYPE_MAP`) in `types.py`
- Type system tests (`tests/semantic/test_types.py`)
- LLVM memory management tests (`tests/llvm/test_memory.py`)
- Agent-pipeline benchmark (`test_vs/05_agent_pipeline`) with .mn/.py/.go/.rs versions
- Benchmark integrity tests (`tests/benchmarks/test_benchmark_integrity.py`)
- `CLAUDE.md` with repo guidance for AI-assisted development

### Changed

- Semantic checker refactored to use `TypeKind` enum instead of string-based type comparisons
- All emitters now import builtin registries from `types.py` (single source of truth)
- Stream benchmark (`03_stream_pipeline.mn`) rewritten to use actual stream primitives
- Concurrency benchmark (`02_concurrency.mn`) rewritten with real parallel message passing
- Benchmark README updated with "Features Tested" column and honest notes
- `docs/SPEC.md` updated to say "arena-based" instead of "ownership-based" memory management
- C runtime expanded with arena allocator, improved string/list memory management

### Fixed

- All type error messages now use `TypeInfo.display_name` for consistent formatting
- LLVM emitter syncs builtin assertions with canonical type registries

## [0.2.0] - 2026-03-08

### Added

- Native C runtime (`runtime/native/mapanare_core.c`, `mapanare_core.h`) with arena-based memory, lock-free SPSC ring buffers, and thread pool with work stealing
- LLVM backend: string and list codegen with proper memory management
- Self-hosted recursive-descent parser (`mapanare/self/parser.mn`, ~1500 lines)
- Self-hosted semantic checker (`mapanare/self/semantic.mn`, ~800 lines)
- Self-hosted LLVM emitter (`mapanare/self/emit_llvm.mn`, ~1630 lines)
- Compiler driver for orchestrating the full compilation pipeline
- `str()`, `int()`, `float()` builtin conversion functions
- `while` loops and `Map` type in AST and parser
- REPL / interactive mode
- Implicit top-level statements (scripting mode)
- Two-pass semantic checker with type inference improvements

### Changed

- Package renamed from `mapa` to `mapanare` (all imports, CLI, tests updated)
- Docs moved: `SPEC.md` → `docs/SPEC.md`, `rfcs/` → `docs/rfcs/`
- Packaging scripts moved to `packaging/` directory
- CI pointed to `dev` branch; release workflow removed in favor of publish workflow
- Python emitter enhanced for while loops and map literals

## [0.1.0] - 2026-02-20

### Added

- **Compiler pipeline**: Lark LALR parser → AST (dataclasses) → semantic checker → optimizer → emitters
- **LALR grammar** (`mapanare.lark`) with 13-level precedence climbing
- **AST nodes**: full dataclass-based node definitions for all language constructs
- **Semantic checker**: two-pass type checker and scope resolver
- **Optimizer**: constant folding, dead code elimination, agent inlining, stream fusion (O0–O3)
- **Python transpiler**: agents → asyncio, signals → reactive, streams → async generators
- **LLVM IR backend**: basic functions, structs, enums, arithmetic via llvmlite
- **CLI** with `compile`, `check`, `run`, `fmt`, `build`, `jit`, `emit-llvm`, and `init` commands
- **Runtime system**: asyncio-based agents, reactive signals, async stream operators, Result/Option types
- **Self-hosted compiler**: initial lexer (`lexer.mn`) and parser (`parser.mn`)
- **Language spec** (`docs/SPEC.md`): complete specification of syntax and semantics
- **Design manifesto** (`docs/manifesto.md`): language philosophy and goals
- **Agent syntax RFC** (`docs/rfcs/0001-agent-syntax.md`)
- **Benchmark suite**: matrix multiply, concurrency, stream pipeline, fibonacci with Python/Go/Rust comparisons
- **VSCode extension**: syntax highlighting, snippets, language configuration
- **LSP server**: basic analysis and diagnostics
- **Stdlib modules**: math, text, time, io, log, http, pkg (Python backend)
- **Test suite**: 1400+ tests covering parser, semantic, optimizer, emitters, runtime, LLVM, CLI, and more
- **CI pipeline**: GitHub Actions with Python 3.11/3.12 matrix on Ubuntu
- **PyPI publishing** workflow
- **GPU module** (`gpu.py`) and **model loading** (`model.py`) — experimental
- **Tensor operations** (`tensor.py`) — experimental
- `CONTRIBUTING.md`, `LICENSE` (MIT), and project scaffolding

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mapanare-Research/Mapanare/releases/tag/v0.1.0
