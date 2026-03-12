# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-11

### Added

- **String interpolation**: `"Hello, ${name}!"` with `${expr}` syntax in both regular and triple-quoted strings; `InterpString` AST node; works on Python and LLVM backends
- **Multi-line strings**: `"""..."""` triple-quoted string literals
- **Linter**: `mapanare lint` with 8 rules (W001-W008): unused variables, unused imports, shadowing, unreachable code, unnecessary mut, empty match arms, unchecked results; `--fix` auto-repairs W002/W005; `@allow(rule)` suppression; LSP integration
- **Python interop**: `extern "Python" fn module::name(params) -> Type` for calling Python functions; type marshalling; `Result<T, String>` wraps exceptions; `--python-path` flag
- **WASM playground**: Browser-based editor at `play.mapanare.dev` via Pyodide; CodeMirror 6 with `.mn` syntax highlighting; 7 pre-loaded examples; share via URL hash
- **Package registry**: `mapanare publish`, `mapanare search`, `mapanare login`; FastAPI registry backend; semver resolution; `mapanare install` checks registry before git fallback; package browser UI
- **Doc comments**: `///` syntax captured in grammar as `DOC_COMMENT` tokens; `DocComment` AST node wraps definitions
- **Doc generator**: `mapanare doc <file>` generates styled HTML documentation from `///` doc comments
- **Language reference** (`docs/reference.md`): complete reference covering all types, keywords, operators, syntax, builtins, CLI commands, lint rules
- **Cookbook** (`docs/cookbook.md`): 14 real-world recipes from hello world to Python interop
- **Stdlib documentation** (`docs/stdlib.md`): API reference for all 7 stdlib modules
- **Migration guides**: `docs/for-python-devs.md`, `docs/for-rust-devs.md`, `docs/for-typescript-devs.md`
- 37 Python interop tests, 25 interpolation tests, 35 linter tests, playground tests, registry tests

### Changed

- README updated with v0.5.0 CLI commands (lint, doc, publish, search, login), roadmap status, stdlib reference link
- All compiler passes (parser, semantic, optimizer, emitters, linter, LSP) handle `DocComment` AST nodes

## [0.4.0] - 2026-03-11

### Added

- **FFI support**: `extern "C" fn` declarations for binding native libraries, `--link-lib` CLI flag for linker pass-through
- **Rich diagnostics**: Rust-style colorized error output with source spans, labels, and summary counts (`mapanare/diagnostics.py`)
- **Error recovery**: `mapanare check` uses `parse_recovering()` to collect multiple parse errors in a single pass, then runs semantic analysis on the partial AST
- **Parser span tracking**: all AST nodes now carry `Span` with line/column start and end positions
- **Native runtime hardening**: mutex-protected thread-pool work queue, atomic agent state transitions, arena bounds checking
- **CI native job**: compiles and runs C runtime tests with gcc, AddressSanitizer, and ThreadSanitizer
- **LSP enhancements**: symbol table construction, cross-reference indexing, go-to-definition, find-references, hover info
- **Bootstrap documentation** (`docs/BOOTSTRAP.md`): self-hosting compiler status and architecture
- **Roadmap** (`docs/ROADMAP.md`): phased plan through v1.0
- **Localized READMEs**: Spanish (`docs/README.es.md`), Portuguese (`docs/README.pt.md`), Chinese (`docs/README.zh-CN.md`)
- Scope-analysis tests (`tests/test_scope.py`)
- C runtime test harness (`tests/native/test_c_runtime.c`) and hardening tests (`tests/native/test_c_hardening.py`)
- FFI test suite (`tests/ffi/test_ffi.py`)
- Diagnostics test suite (`tests/diagnostics/test_diagnostics.py`)
- Bootstrap verification tests (`tests/bootstrap/test_verification.py`)
- Dev script (`dev.ps1`) now watches `*.c`/`*.h` files and runs gcc C runtime tests

### Changed

- GPU, model, and tensor modules moved from `mapanare/` to `experimental/` with clear opt-in boundary
- `mapanare/types.py` gains `EXPERIMENTAL_TYPES` registry separating experimental type metadata from core
- All CLI error output routes through the new diagnostics system instead of plain `print()`
- README updated with language selector badges linking to localized docs
- VSCode extension removed from tree (to be maintained separately)

### Fixed

- Thread-pool work queue race condition (missing mutex around push/pop)
- Agent state updates using non-atomic writes (now uses `__atomic_compare_exchange_n`)
- Missing `#include <unistd.h>` in C runtime for POSIX portability
- Unused local variables in `mapanare/lsp/analysis.py`

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

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mapanare-Research/Mapanare/releases/tag/v0.1.0
