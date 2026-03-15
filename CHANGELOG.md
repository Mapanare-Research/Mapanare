# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-XX

### Added

- **Language specification freeze**: SPEC.md promoted to "1.0 Final" — syntax, semantics, and type system are frozen; future changes require RFC + deprecation cycle
- **Spec compliance tests**: 85 tests covering all grammar rules (parse + semantic + LLVM); 20 negative tests for error diagnostics
- **Spec cross-reference tests**: automated validation of 32 keywords, 25 TypeKinds, 28 operators against grammar, semantic checker, and emitters
- **Formal memory model** (`docs/MEMORY_MODEL.md`): documents arena lifecycle, string ownership (tag-bit system), struct/enum/list/map ownership, agent message passing, signal/stream/closure lifecycle
- **Stability policy** (`docs/STABILITY.md`): backwards compatibility guarantees, semantic versioning contract, deprecation cycle, what is and is not frozen
- **RFC process** (`docs/rfcs/RFC_PROCESS.md`): when RFCs are required, template, review process, acceptance criteria
- **Migration guide template** (`docs/MIGRATION_TEMPLATE.md`): standardized format for communicating breaking changes
- **Fixed-point verification script** (`scripts/verify_fixed_point.sh`): automated 3-stage self-compilation pipeline (stage1 -> stage2 -> stage3, binary diff)
- **Deprecation warning support**: `@deprecated("message")` decorator emits compiler warnings on function calls
- **`--edition` flag**: future-proofing for language editions (default: `2026`, no-op for now)
- **Version-stamped binaries**: compiler version embedded in LLVM IR metadata (`!mapanare.version`)
- **Security audit**: C runtime audited for buffer overflows, use-after-free, integer overflows, thread safety, TLS security

### Changed

- SPEC.md version bumped to 1.0.0, status to "1.0 Final"
- Python backend marked as "legacy, for reference only" in all documentation
- Bootstrap verification tests updated to use MIR-based emitter pipeline
- Stage 1 tests skip correctly on Windows (ELF binary detection)
- Debug print statements removed from self-hosted compiler sources (parser.mn, emit_llvm.mn, main.mn)
- Compiler pipeline optimized: 805ms -> 503ms (37% faster) for 7 stdlib modules
- README updated with current test count (3,600+) and v1.0 status
- 3,600+ tests passing (up from 3,400 in v0.9.0)

### Fixed

- Closure call crash when closure was `i8*` instead of `{i8*, i8*}` struct across basic blocks
- Copy propagation unsafe through FieldSet/IndexSet mutation targets (alloca mismatch)
- `.value` field assignment treated as SignalSet for all types (now checks `TypeKind.SIGNAL`)
- Function parameters not stored to allocas causing uninitialized memory in conditional branches
- Boxed struct field set (`_emit_field_set`) not handling heap allocation for recursive fields
- `_coerce_arg` struct-to-struct case allocating wrong size (now uses `max(src, dest)` with zero-fill)
- Nested `state.module.X.push()` losing data in self-hosted lowerer (2-level field write-back)
- `emit_instr` in self-hosted lowerer was a no-op (now uses IndexSet on shared blocks buffer)

## [0.9.0] - 2026-03-13

### Added

- **Native stdlib in Mapanare**: Seven stdlib modules written in `.mn`, compiled to LLVM IR — no Python at runtime
- **`encoding/json.mn`** (982 lines): Recursive descent JSON parser with escape handling, number parsing, arrays, objects; encoder + pretty-printer; SAX-style streaming parser (`stream_parse` → `Stream<JsonEvent>`); schema validation
- **`encoding/csv.mn`** (330 lines): RFC 4180 compliant CSV parser/writer; configurable delimiter and quote character; header row support; `to_string` serialization; `collect_rows` convenience function
- **`net/http.mn`** (1,103 lines): Full HTTP/1.1 client on C runtime TCP/TLS; URL parser (scheme, host, port, path, query); request builder; response parser (Content-Length + chunked transfer); redirect following; convenience wrappers (`get`/`post`/`put`/`delete`/`patch`/`head`/`options`); request fingerprinting
- **`net/http/server.mn`** (~600 lines): HTTP server with route matching and path parameters; middleware pattern (logging + CORS); request parsing; response building; static file serving; server listen loop
- **`net/websocket.mn`** (~1,120 lines): RFC 6455 WebSocket client + server; HTTP upgrade handshake; SHA-1 + Base64 accept key; frame encoding/decoding (7/16/64-bit payload length); client masking; ping/pong auto-respond; close handshake; message fragmentation
- **`crypto.mn`** (283 lines): Cryptographic primitives via C runtime — SHA-1, SHA-256, HMAC, Base64 encode/decode, random bytes, JWT helpers
- **`text/regex.mn`** (271 lines): Regular expressions via PCRE2 FFI (`dlopen`); match, search, replace, split operations
- **Cross-module LLVM compilation** (`multi_module.py`): Dependency graph with topological sort, name mangling (`{module_path}__` prefix), MIR symbol renaming, import remapping, MIR merging into single LLVM IR module; `--stdlib-path` CLI flag; incremental compilation with source hashing
- **Integration tests**: HTTP client↔server, JSON decode→encode round-trip, CSV parse→write pipeline, WebSocket frame encode/decode
- **Stdlib compilation benchmarks** (`bench_stdlib.py`): 5,159 lines of `.mn` → LLVM IR in ~880ms (5,866 lines/s)

### Changed

- Dato package updated to use `encoding/csv.mn` and `encoding/json.mn` via cross-module imports
- README feature status table updated: stdlib modules now Yes/Yes for LLVM backend
- SPEC.md updated with stdlib module documentation
- ROADMAP.md updated with v0.9.0 completion
- 3,400+ tests passing (up from 3,020 in v0.8.0)

### Fixed

- `.value` field access incorrectly treated as `SignalGet` for non-signal types
- Match arm payload types (`Ok(val)`) inferred as UNKNOWN — added `_infer_payload_type()` in lowerer
- For-loop iteration variable types inferred as UNKNOWN — added `_infer_iterable_elem_type()`
- `FieldGet` fallback extracting wrong struct field index when type is unknown
- Auto-declared function parameter types using LLVM value types instead of MIR semantic types
- Enum type resolution defaulting user-defined enums to STRUCT
- Enum tag extraction crash on pointer-typed values
- Switch on enum variants calling `int("GET")` instead of resolving variant tags
- Multi-line `new Struct { ... }` struct literals not parsing correctly (tests updated to single-line)
- Nullary enum variant `Null` treated as function type instead of value (use `Null()`)

## [0.8.0] - 2026-03-13

### Added

- **LLVM Map/Dict codegen**: Robin Hood hash table in C runtime (`__mn_map_new`, `__mn_map_set`, `__mn_map_get`, `__mn_map_del`, `__mn_map_iter`, `__mn_map_contains`); both AST and MIR emitters; map literals, indexing, assignment, iteration all work natively
- **LLVM signal reactivity**: Full dependency graph in C runtime — computed signals with lazy recomputation, subscriber notification, batched updates (`__mn_signal_computed`, `__mn_signal_subscribe`, `__mn_signal_batch_begin/end`), topological propagation order
- **LLVM stream operators**: Native stream runtime with `__mn_stream_from_list`, `__mn_stream_map`, `__mn_stream_filter`, `__mn_stream_take`, `__mn_stream_skip`, `__mn_stream_collect`, `__mn_stream_fold`, `__mn_stream_bounded` (backpressure); pipe operator (`|>`) targets stream operations; `for x in stream` iteration
- **LLVM closure capture**: Environment struct generation per lambda, free variable analysis, arena-allocated closure environments (`{fn_ptr, env_ptr}`), `ClosureCreate`/`ClosureCall`/`EnvLoad` MIR instructions; both AST and MIR emitters
- **Complete string methods on LLVM**: `contains`, `split`, `trim`, `trim_start`, `trim_end`, `to_upper`, `to_lower`, `replace` — all via C runtime functions + both emitters
- **Pipe definitions on LLVM**: `pipe Name { A |> B |> C }` compiles to agent spawn chains in both emitters
- **C runtime TCP sockets**: `__mn_tcp_connect`, `__mn_tcp_listen`, `__mn_tcp_accept`, `__mn_tcp_send`, `__mn_tcp_recv`, `__mn_tcp_close`, `__mn_tcp_set_timeout`; cross-platform (POSIX + Winsock2)
- **C runtime TLS**: `__mn_tls_init`, `__mn_tls_connect`, `__mn_tls_read`, `__mn_tls_write`, `__mn_tls_close`; dynamic OpenSSL loading via dlopen/LoadLibrary, SNI support
- **C runtime file I/O**: `__mn_file_open`, `__mn_file_read_fd`, `__mn_file_write_fd`, `__mn_file_close`, `__mn_file_stat`, `__mn_dir_list`
- **C runtime event loop**: `__mn_event_loop_new`, `__mn_event_loop_add_fd`, `__mn_event_loop_remove_fd`, `__mn_event_loop_run`, `__mn_event_loop_run_once`; epoll (Linux), kqueue (macOS), select fallback (Windows)
- Stream fusion in MIR optimizer: map+map, map+filter, filter+filter fusion passes
- 37 new map tests (codegen + runtime), 26 signal tests, 34 stream tests, 18 closure tests, TCP/TLS/file I/O/event loop tests

### Changed

- README feature status table updated to reflect full LLVM backend parity — all core features now Yes/Yes
- REPL removed from CLI listing and feature table (never fully implemented)
- Tensor/GPU section rewritten honestly — experimental prototypes only, no language integration
- SPEC.md updated with closure semantics, map codegen on LLVM, signal/stream LLVM status
- ROADMAP.md updated with v0.8.0 release entry and feature status
- 3,020 tests passing (up from 2,983 in v0.7.0)

### Fixed

- MIR emitter `EnumTag` for non-enum types in nested pattern matching
- DCE not tracking `InterpString` references (string interpolation on LLVM)
- `while` loop `break`/`continue` on LLVM backend

## [0.7.0] - 2026-03-12

### Added

- **Self-hosted MIR lowering** (`lower.mn`): 2,629 lines of Mapanare translating AST → MIR, completing the self-hosted compiler pipeline (7 modules, 8,288+ lines)
- **Self-hosted LLVM emitter rewrite** (`emit_llvm.mn`): rewrote to consume MIR instead of AST (~1,050 lines), matching the bootstrap architecture
- **Built-in test runner**: `mapanare test` discovers and runs `@test` functions in `.mn` files; `assert` statement in grammar, AST, MIR, and both emitters; `--filter` for substring matching
- **Agent observability**: OpenTelemetry-compatible tracing (`--trace` flag), OTLP HTTP export, W3C Trace Context spans for agent lifecycle (spawn, send, handle, stop, pause, resume)
- **Prometheus metrics**: `--metrics :PORT` flag serves agent counters (spawns, messages, errors, stops) and handle-duration histograms
- **Structured error codes**: 33 codes in `MN-X0000` format across parse (MN-P), semantic (MN-S), lowering (MN-L), codegen (MN-C), runtime (MN-R), and tooling (MN-T) categories
- **DWARF debug info**: `mapanare build -g` emits compile units, function info, line numbers, variable debug info, and struct type metadata for `gdb`/`lldb` debugging
- **Deployment infrastructure**: `mapanare deploy init` scaffolds Dockerfile; `HealthServer` with `/health`, `/ready`, `/status` endpoints; `SupervisionTree` with one-for-one, one-for-all, rest-for-one strategies; `@supervised` decorator; SIGTERM graceful shutdown with drain timeout
- **Native runtime trace hooks**: C runtime `mapanare_trace_hook_fn` callback for spawn/send/handle/stop/pause/resume/error events
- **CI bootstrap verification**: parse verification and module resolution tests for self-hosted compiler

### Changed

- Self-hosted compiler driver (`main.mn`) wired to AST → MIR → LLVM pipeline
- SPEC.md updated to v0.7.0: new sections for testing (10), observability (11), and deployment (12)
- ROADMAP.md updated with v0.7.0 release and self-hosted compiler status (7,500+ lines across 7 modules)
- Bootstrap snapshot remains at v0.6.0 (self-hosted binary compilation blocked by bootstrap emitter gaps)
- 2,983 tests passing (up from 2,538 in v0.6.0)

## [0.6.0] - 2026-03-12

### Added

- **MIR pipeline**: Typed SSA-based intermediate representation between AST and code emission (`mir.py`, `mir_builder.py`, `lower.py`)
- **MIR lowering**: AST → MIR translation pass (1,397 lines) covering all language constructs — expressions, control flow, agents, signals, streams, pattern matching, string interpolation
- **MIR optimizer** (`mir_opt.py`): Constant folding, dead code elimination, copy propagation, basic block merging, unreachable block removal
- **MIR → LLVM emitter** (`emit_llvm_mir.py`): Translates MIR basic blocks to LLVM IR via llvmlite
- **MIR → Python emitter** (`emit_python_mir.py`): Translates MIR to Python source code
- **`emit-mir` CLI command**: Dump MIR text representation for debugging
- **Bootstrap Makefile** (`bootstrap/Makefile`): `make bootstrap` and `make verify` for three-stage bootstrap verification

### Changed

- Bootstrap snapshot updated to v0.6.0 (22 files: all compiler modules + grammar)
- `bootstrap/README.md` rewritten with MIR pipeline documentation and file index
- SPEC.md Appendix B rewritten with full MIR description (instruction categories, optimizer passes, pipeline diagram)
- ROADMAP.md architecture diagram updated to show AST → MIR → Optimizer → Emitter pipeline
- ROADMAP.md release history updated with v0.5.0 and v0.6.0 entries
- SPEC.md version bumped to 0.6.0
- 2,538 tests passing (up from 2,200+ in v0.5.0)

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
- **Roadmap** (`docs/roadmap/ROADMAP.md`): phased plan through v1.0
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
- **Agent-pipeline benchmark** (`benchmarks/cross_language/05_agent_pipeline`) with .mn/.py/.go/.rs versions
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

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/Mapanare-Research/Mapanare/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Mapanare-Research/Mapanare/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Mapanare-Research/Mapanare/releases/tag/v0.1.0
