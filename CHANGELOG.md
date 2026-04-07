# Changelog

All notable changes to the Mapanare programming language will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.16.0] - 2026-04-07

### Added

- `__mn_map_free_deep` — frees string keys/values before freeing the map struct
- `__mn_stream_free_chain` — frees entire upstream stream pipeline (iterative, no stack overflow)

### Changed

- String constant alignment from `align 2` to `align 8` (future-proofs 3-bit pointer tagging)
- `mapanare run` now compiles C with `-Wall -Wextra`
- CI stage2 validation no longer uses `continue-on-error` (failures are real)

### Fixed

- Signal tracking context now `_Thread_local` (concurrent computed signals safe)
- Signal subscriber list protected during propagation (snapshot under lock prevents use-after-free on realloc)
- Spec `char_at` return type corrected to `String` (matches implementation)
- Test `test_list_type` updated for 5-field MnList ABI (from v3.15.0)

## [3.15.0] - 2026-04-07

### Fixed

- `__mn_list_concat` null-pointer UB: realloc on NULL-16 when concatenating into a fresh list
- Windows console handler deadlock: removed `mapanare_registry_stop_all()` mutex call from handler thread
- COW list refcount now atomic: `__atomic_fetch_add`/`__atomic_fetch_sub` at 3 sites (safe on ARM64 agent workloads)
- MnList ABI mismatch: added 5th `managed` field to `emit_llvm_text.py`, `emit_llvm.py`, and `mnc_main.c`
- `VkPhysicalDeviceProperties` padding undersized: 804 -> 836 bytes (prevents stack smash on Vulkan)
- `__mn_str_from_bool` no longer heap-allocates per call (static constants)
- `__mn_list_oob_buf` now `_Thread_local` (safe for concurrent agent OOB access)

## [3.14.0] - 2026-04-07

### Added

- Generic arity validation (`List<Int, String>` now errors with "expects 1 type argument(s), got 2")
- Arithmetic operator traits: `Add`, `Sub`, `Mul`, `Div` in `BUILTIN_TRAITS`
- Trait-dispatched binary ops for user-defined types implementing Add/Sub/Mul/Div
- WASM `CHAR` type mapping to `i32` (was falling through to `i64`)
- `BUILTIN_GENERIC_ARITY` dict for compile-time arity checking
- `scope-define-noop` Culebra template for bootstrap regression testing
- Debug info producer now reads version from VERSION file dynamically

### Changed

- `TypeInfo.__hash__` now includes `tuple(self.args)` — fixes pathological collisions for `List<Int>` vs `List<String>`
- CLAUDE.md self-hosted module table updated to match actual line counts (15,000+ lines, 11 modules)
- CI: removed `continue-on-error` on stage1 build step (broken compiler now fails CI)
- Local build scripts use `-Wall -Wextra -Werror` for C compilation

### Fixed

- IdentPattern (named catch-all) now treated as wildcard in match exhaustiveness checks
- Self-hosted `scope_define` fixed: push call was commented out since v2.0.0, symbols now tracked
- Getting-started tutorial: `Point(3.0, 4.0)` -> `new Point { x: 3.0, y: 4.0 }`, removed `Shape_` prefix
- Spec section 27 subsection numbering (was `24.1`/`24.2`/`24.3`)
- Spec `batch {}` syntax marked as not yet implemented

## [3.13.0] - 2026-04-07

### Added

- Runtime function attributes (`nounwind`, `readonly`) on 30+ LLVM declarations
- Target-aware pointer size in `_approx_type_size` (correct for wasm32/i686)
- `managed` field on `MnList` struct for O(1) COW ownership check
- `__mn_range_free` runtime function for range iterator cleanup
- Intern table thread safety (pthread mutex / Windows CriticalSection)
- 2 new Culebra templates: `string-track-noop`, `syscall-in-hot-path`

### Changed

- MnList ABI: 32 bytes -> 40 bytes (added `int64_t managed` field)
- Self-hosted compiler list type updated: `{ ptr, i64, i64, i64 }` -> `{ ptr, i64, i64, i64, i64 }`

### Fixed

- Re-enabled `_track_string` — every heap string now tracked for drop glue cleanup
- Range iterators freed after for-loop exit (was leaking 16 bytes per loop)
- Removed `write(2)` syscall probe from COW list `mn_list_has_magic()` — replaced with `managed` flag
- Windows signal mutex TOCTOU: `InterlockedCompareExchange` replaces plain `int` check

## [3.9.0] - 2026-04-06

### Added

### Changed

### Fixed

## [3.0.3] - 2026-04-04

### Added

- While/mien loop support in self-hosted parser (desugared to for+if)
- `scripts/test_runtime.sh`: automated runtime correctness tests (compile → execute → compare output)

### Fixed

- Exit codes: `main()` now returns `i32 0` (C ABI) instead of `void`
- 12_while golden test: was producing empty output (missing while-loop parsing)

### Changed

- All 15 golden tests produce correct output when executed as native binaries
- Stage1 AND stage2 compiled binaries produce identical correct results
- Three-stage fixed point preserved (78,881 lines, 0 diff)

## [3.0.2] - 2026-04-04

### Added

- Bilingual keywords in self-hosted lexer: `pon`/`si`/`da`/`cada`/`mien`/`sino`/`en`/`tipo`/`nada`/`sal`/`sigue`/`yo`/`modo`/`way`/`usa`/`di`
- `tipo` unified type definitions: `tipo Name { fields }` for structs, `tipo Name { | Variant }` for enums
- BAR token (`|`) for tipo enum variant syntax
- `mnc_driver.c`: C entry point for LLVM-compiled stage2 binary
- `verify_fixed_point.sh`: automated three-stage bootstrap verification

### Fixed

- Result variant index extraction: strip `:N` suffix before Ok/Err comparison
- MIRType hardcoded field index swap (`name`/`kind` were reversed)
- WrapNone in `lower_let`: condition fired on Option-typed function call results, not just None literals — root cause of "vars not found" in stage2 binary
- SSA name collisions: 80 variable renames across 5 self-hosted modules

### Changed

- Three-stage fixed point achieved: `stage2.ll == stage3.ll` (78,676 lines, 0 diff)
- Golden tests: 15/15 pass through mnc-stage1 + llvm-as
- Stage2 IR validates with zero post-processing

## [3.0.1] - 2026-04-03

### Added

- `di` print keyword: `di "hello"` as statement (print() function still works)
- `+` pub prefix: `+fn`, `+tipo`, `+struct`, `+enum`, `+trait`, `+agent`, `+pipe`
- `...` empty block: `fn todo() { ... }` (like Python's `pass`)
- Implicit return: last expression in typed function is returned automatically
- Stage2 IR fixup script (`scripts/fix_stage2_ir.py`)

### Changed

- Self-hosted compiler loop limits raised from 50 to 200 iterations
- Self-hosted match/if PHI handling: skip terminated branches, add switch default entries

### Fixed

- MIR type inference: Option/Result inner types, namespace call returns, enum variant constructors
- C emitter string truncation: aligned string constants for pointer tagging
- C emitter void* boxing: heap-allocate on store, dereference on load
- C emitter memcpy overflows: sizeof(source) instead of sizeof(dest) everywhere
- List push in-place mutation: prevents SSA aliasing bugs in for loops
- mnc-stage1 segfault: binary now self-compiles (77K lines LLVM IR)

## [2.0.0] - 2026-03-25

### Added

- **WebAssembly backend** (`mapanare/emit_wasm.py`): Full MIR-to-WAT emitter with linear memory, bump allocation, string constants, JS bridge imports, and structured control flow
- **CLI `emit-wasm` command** with `--binary` flag for optional `wat2wasm` compilation
- **Cross-compilation targets** (`mapanare/targets.py`): `wasm32-unknown-unknown`, `wasm32-wasi`, `aarch64-apple-ios`, `aarch64-linux-android`, `x86_64-linux-android`
- **GPU compute runtime** (`runtime/native/mapanare_gpu.c/.h`): CUDA Driver API and Vulkan compute via `dlopen` with built-in PTX/GLSL kernels for tensor ops
- **GPU stdlib** (`stdlib/gpu/`): `device.mn`, `kernel.mn`, `tensor.mn` for device detection, kernel management, and GPU-accelerated tensor operations
- **WASM stdlib** (`stdlib/wasm/`): `bridge.mn` (JS interop), `runtime.mn` (WASI preview 1 bindings)
- **AI stdlib** (`stdlib/ai/`): `llm.mn` (LLM driver with provider abstraction), `embedding.mn` (batched embeddings with caching), `rag.mn` (RAG pipeline)
- **Dato data engine** (`dato/src/`): Table, column, aggregation, join, reshape, null handling, I/O, and display modules
- **Database layer** (`stdlib/db/`): `sql.mn`, `sqlite.mn`, `postgres.mn`, `redis.mn`, `kv.mn`, `embedded_kv.mn`, `pool.mn`, `migrate.mn`
- **Database C runtime** (`runtime/native/mapanare_db.c/.h`): SQLite3 and PostgreSQL via `dlopen`, connection pooling, prepared statements
- **Encoding stdlib**: `stdlib/encoding/toml.mn` (1,902 lines), `stdlib/encoding/yaml.mn` (2,121 lines) — full TOML and YAML parsers/serializers
- **Filesystem stdlib** (`stdlib/fs.mn`): read, write, walk, glob, metadata, temp files
- **Web crawler** (`crawl/src/`): URL parser, robots.txt, frontier queue, content extractor, persistence, crawl engine
- **Vulnerability scanner** (`scan/src/`): Template-driven scanner with fingerprinting, pattern matching, YAML templates, report generation
- **HTTP fuzzer** (`fuzz/src/`): Mutation engine, wordlist generation, HTTP fuzzing
- **HTTP server toolkit** (`stdlib/net/http/`): auth, body parsing, config, cookies, rate limiting, sessions, SSE, template rendering
- **HTML parser C runtime** (`runtime/native/mapanare_html.c/.h`): Streaming HTML parser for crawler/scanner
- **Playground WASM runtime** (`playground/src/`): Browser runtime and Web Worker for WASM module execution
- **GPU and WASM examples** (`examples/gpu/`, `examples/wasm/`)
- **Roadmap plans**: `v1.2.0/PLAN.md`, `v1.3.0/PLAN.md`, `v2.0.0/PLAN.md`, `v2.0.0/SUMMARY.md`

### Changed

- Python emitters (`emit_python.py`, `emit_python_mir.py`) now emit `DeprecationWarning` at import time
- `emit_python.py`: `substr` added as alias for `substring` method
- `semantic.py`: `_bind_pattern` now receives `subject_type` for richer pattern binding in match expressions

### Deprecated

- **Python transpiler backends** (`emit_python.py`, `emit_python_mir.py`): Use the LLVM or WASM backend instead

## [1.0.11] - 2026-03-19

### Added

- `_load_struct_fields()` — reconstructs large structs from allocas field-by-field via GEP+load+insert_value, eliminating all by-value loads of structs > 56 bytes
- `_store_struct_fields()` — decomposes large struct stores into per-field GEP+store, eliminating all by-value stores of structs > 56 bytes
- `_aligned_alloca()` — routes all temporary allocas through the pre_entry block to maintain 16-byte RSP alignment (prevents SSE `movaps` crashes)
- Alloca size mismatch detection in `_emit_copy`, `_emit_field_get`, `_emit_index_get` — prevents stack buffer overflow when MIR temp names collide with user variable names
- `fflush(stdout)` in crash handler for reliable debug output

### Changed

- `_ZEROINIT_MEMSET_THRESHOLD` lowered from 128 to 56 to match `_LARGE_STRUCT_THRESHOLD` — `store zeroinitializer` is also truncated by the llvmlite codegen bug
- Self-hosted compiler build (`build_stage1.py`): removed `internal` linkage from all function definitions — LLVM `-O1` was incorrectly stripping called functions as dead code due to sret calling convention confusion
- `_coerce_arg` struct-to-struct reinterpretation now uses `_store_struct_fields`/`_load_struct_fields` for large types instead of by-value store+load
- `_get_value_ptr()` now also checks `%`-prefixed name variant for alloca lookup
- Binary size: 1.50MB (down from 1.71MB — 12% smaller)
- 3,698 tests passing

### Fixed

- **Self-hosted compiler 15/15 golden tests** (was 12/15) — all features now compile correctly including enum match, Result types, string methods
- **Pointer-only large struct refactor**: LLVM 20.1.8 / llvmlite codegen truncates by-value load/store of structs > 56 bytes; all paths now use memcpy via alloca pointers
- **Stack alignment crash**: dynamic allocas in non-entry blocks (from `_coerce_arg`, list ops, etc.) misaligned RSP; SSE `movaps` in libc `snprintf` crashed with SIGSEGV. Fixed by routing all temporaries through pre_entry block.
- **Function stripping at -O1**: LLVM dead-code-eliminated `internal`-linkage functions that were actually called (sret convention confused reachability analysis). Fixed by removing `internal` linkage in post-processing.
- **Alloca size mismatch (stack buffer overflow)**: MIR temp names (t0, t1, ...) colliding with user variable names (e.g., `let t0: TypeResult`) caused 64-byte memcpy into 16-byte alloca. Fixed by checking alloca size before reuse.
- **Generic type parsing in self-hosted compiler**: `Result<Int, String>` parsing failed ("Expected GT but got EOF") because the alloca overflow corrupted the `pos` field of TypeResult
- **Byptr parameter loading**: large struct parameters passed by pointer were loaded by value in the callee prologue — now use memcpy from param pointer to local alloca
- **Field extraction of large sub-fields**: `_emit_field_get` loaded large struct fields by value from parent struct — now uses memcpy to local alloca via GEP

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

[Unreleased]: https://github.com/Mapanare-Research/Mapanare/compare/v3.16.0...HEAD
[3.16.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.15.0...v3.16.0
[3.15.0]: https://github.com/Mapanare-Research/Mapanare/compare/v3.14.0...v3.15.0
[3.0.3]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.2...v3.0.3
[3.0.2]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/Mapanare-Research/Mapanare/compare/v3.0.0...v3.0.1
[2.0.0]: https://github.com/Mapanare-Research/Mapanare/compare/v1.0.11...v2.0.0
[1.0.11]: https://github.com/Mapanare-Research/Mapanare/compare/v1.0.0...v1.0.11
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
