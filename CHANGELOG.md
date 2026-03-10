# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-03-10

### Changed

- Version source of truth consolidated to `VERSION` file
- CLI reads version via `importlib.metadata` instead of hardcoded string
- Publish workflow reads version from `VERSION` file instead of parsing `cli.py`

### Fixed

- PyPI publish failing with 400 due to stale version in `cli.py`
- Benchmark test hardcoded version string

## [0.3.0] - 2026-03-10

### Added

- **Traits system**: `trait` and `impl Trait for Type` syntax, trait bounds on generics, builtin traits (`Display`, `Eq`, `Ord`, `Hash`), monomorphization for LLVM backend, Protocol emission for Python backend
- **Module resolution**: file-based imports with `pub` visibility, circular dependency detection, transitive imports, stdlib module wiring, multi-file compilation on both backends
- **LLVM native agents**: `spawn`, `send` (`<-`), `sync` codegen targeting C runtime with OS threads, agent handler dispatch, supervision policy codegen (`@restart`)
- **Semaphore-based agent scheduling**: replaced 1ms polling sleep with `inbox_ready`/`outbox_ready` semaphores in C runtime
- **Arena-based memory management**: arena allocator in C runtime, scope-based arena insertion in LLVM emitter, heap/constant string tagging via LSB tag bit, `__mn_str_free` and `__mn_list_free_strings`
- **Formal type representation**: `TypeKind` enum (25 kinds), `TypeInfo` dataclass, canonical builtin registries in `mapanare/types.py`
- **Getting Started tutorial** (`docs/getting-started.md`) — 12 sections from install to streams
- **Community governance**: `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, issue/PR templates
- **110+ end-to-end tests**: correctness, cross-backend consistency, tutorial verification
- **Memory stress tests** (`tests/native/test_memory_stress.py`)
- **Agent-pipeline benchmark** (`test_vs/05_agent_pipeline`) with .mn/.py/.go/.rs versions
- **RFCs**: memory management (0002), module resolution (0003), traits (0004)
- `CLAUDE.md` with repo guidance for AI-assisted development
- 1968 total tests (up from ~1400 in v0.2.0)

### Changed

- Semantic checker refactored to use `TypeKind` enum instead of string-based type comparisons
- All emitters import builtin registries from `types.py` (single source of truth)
- Stream benchmark rewritten to use actual stream primitives
- Concurrency benchmark rewritten with real parallel message passing
- Benchmark tables updated with "Features Tested" column and honest notes
- `docs/SPEC.md` updated: arena-based memory, grammar summary with traits/imports, accurate appendices
- C runtime expanded with arena allocator, semaphore-based scheduling, improved memory management
- README feature status table audited and corrected against actual implementation
- CONTRIBUTING.md expanded with non-code contribution paths

### Fixed

- All type error messages now use `TypeInfo.display_name` for consistent formatting
- LLVM emitter syncs builtin assertions with canonical type registries
- REPL status corrected from "Planned" to "Experimental" in README
- Map/Dict status corrected from "Planned" to "Stable" in README
- 7 stale feature status entries corrected

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

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mapanare-Research/Mapanare/releases/tag/v0.1.0
