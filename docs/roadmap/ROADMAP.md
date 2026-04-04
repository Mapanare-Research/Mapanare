# Mapanare Roadmap

> **Mapanare** is an AI-native compiled programming language.
> Agents, signals, streams, and tensors are first-class primitives — not libraries.
>
> [mapanare.dev](https://mapanare.dev) · [GitHub](https://github.com/Mapanare-Research/Mapanare)

---

## Where We Are (v3.3.0 — Fixed Point)

**The compiler compiles itself.** Mapanare v3.3.0 achieves self-hosting
fixed point: the self-compiled binary produces identical output when it
compiles itself again (stage3 == stage4). No Python is needed to build
the compiler — `bash scripts/build_from_seed.sh --verify` does a
two-stage bootstrap from the seed binary.

v3.0.0 introduced the C emit backend, bilingual keywords (Spanglish/English),
indentation-based syntax, tipo/modo type unification, and @Agent syntax.
v3.1.0-v3.2.0 achieved 25/25 golden tests on the self-hosted compiler.
v3.3.0 solved the enum tag mismatch via string-tagged dispatch, fixed
sret ABI, COW write-back, and field index bugs — enabling the fixed point.

**37 stdlib modules** in native `.mn` span AI, databases, encoding, HTTP,
filesystem, crypto, GPU, and WebAssembly. The self-hosted compiler is
9,400+ lines across 10 modules.

**No Python required to build.** **4,465+ tests pass** across the full pipeline.

### What works today

- **Full compiler pipeline** — Lexer, parser, semantic checker, MIR lowering, MIR optimizer (O0-O3), code emitter
- **MIR pipeline** — Typed SSA-based intermediate representation with basic blocks and explicit terminators
- **Three compilation targets** — Native binaries via LLVM IR (production), WebAssembly (WAT/WASM), and Python transpilation (deprecated)
- **Self-hosted compiler** — 8,288+ lines of `.mn` across 7 modules (lexer, ast, parser, semantic, lower, emit_llvm, main)
- **WebAssembly backend** — MIR-to-WAT emitter with linear memory, bump allocation, JS bridge, WASI support, wasm-ld multi-module linking
- **GPU compute** — CUDA Driver API + Vulkan compute via `dlopen`, `@gpu`/`@cuda`/`@vulkan` annotations, MIR GpuKernel metadata, PTX/SPIR-V LLVM codegen, built-in tensor kernels
- **AI stdlib** — LLM drivers (OpenAI, Anthropic, local), embedding providers, RAG pipelines
- **Data engine (Dato)** — Tables, aggregations, joins, null handling, reshape, CSV/JSON I/O
- **Database drivers** — SQLite, PostgreSQL, Redis, embedded KV, connection pooling, migrations
- **Encoding** — Full TOML and YAML parsers/serializers
- **Filesystem stdlib** — Read, write, walk, glob, metadata, temp files
- **Web & Security** — HTTP server toolkit, web crawler, vulnerability scanner, HTTP fuzzer
- **Built-in test runner** — `mapanare test` discovers `@test` functions, `assert` statement, `--filter` flag
- **Agent observability** — OpenTelemetry tracing (`--trace`), Prometheus metrics (`--metrics`), structured error codes (`MN-X0000`)
- **DWARF debug info** — `mapanare build -g` produces debuggable binaries with source mapping
- **Deployment infrastructure** — Dockerfile scaffolding, health/readiness endpoints, supervision trees, graceful shutdown
- **Agent system** — Spawn concurrent actors with typed channels, message passing, supervision policies
- **Reactive signals** — Automatic dependency tracking and recomputation
- **Stream processing** — Async iterables with fusion, backpressure, and `|>` pipe operator
- **Pattern matching** — Exhaustive `match` expressions with destructuring
- **Type system** — Static typing with inference, generics, `Option<T>`, `Result<T, E>`, `TypeKind` enum (25 kinds)
- **Traits** — `trait` / `impl Trait for Type`, trait bounds on generics, builtin traits (`Display`, `Eq`, `Ord`, `Hash`)
- **Module system** — File-based imports with `pub` visibility, circular dependency detection, multi-file compilation
- **Native C runtime** — Arena-based memory, lock-free SPSC ring buffers, thread pool, cooperative agent scheduler (mobile), epoll/select event loop, string interning, GPU runtime, DB runtime, HTML parser, memory profiling
- **LLVM agent codegen** — `spawn`, `send` (`<-`), `sync` targeting C runtime with OS threads
- **Cross-compilation** — Linux x64, macOS ARM64, Windows x64, wasm32-unknown-unknown, wasm32-wasi, aarch64-apple-ios, aarch64-linux-android
- **Optimization passes** — Constant folding, DCE, agent inlining, stream fusion
- **LSP server** — Diagnostics, hover, go-to-definition, find-references, autocomplete
- **VS Code extension** — Syntax highlighting, LSP integration, snippets, commands
- **Package manager** — Project manifests (`mapanare.toml`), git-based installation, dependency resolution
- **Standard library** — 25+ modules across AI, data, databases, encoding, filesystem, GPU, WASM, HTTP, and more
- **Formatter** — `mapanare fmt` for consistent code style
- **Binary distribution** — PyInstaller builds, install scripts (Unix + Windows), GitHub Releases CI
- **Getting Started guide** — 12-section tutorial from install to streams

### Backend Feature Status

| Feature | LLVM Backend | WASM Backend | Python Backend (deprecated) | Notes |
|---------|:-:|:-:|:-:|--------|
| Functions, closures, lambdas | Yes | Yes | Yes | Full closure capture via environment structs |
| Structs, enums, pattern matching | Yes | Yes | Yes | Full tagged union + switch |
| `if`/`else`, `for..in`, `while` | Yes | Yes | Yes | |
| Type inference, generics | Yes | Yes | Yes | |
| `Result`/`Option` | Yes | Yes | Yes | |
| `print`/`println`, `str`/`int`/`float`/`len` | Yes | Yes | Yes | |
| Lists: literals, indexing, `push`/`pop`/`length` | Yes | Yes | Yes | |
| String methods | Yes | Yes | Yes | All methods: length, find, substring, contains, split, trim, replace, to_upper, to_lower |
| Dictionaries/Maps | Yes | Yes | Yes | Robin Hood hash table in C runtime |
| Traits (`trait`, `impl Trait for Type`) | Yes | Yes | Yes | |
| Module imports (`import`, `pub`, multi-file) | Yes | Yes | Yes | |
| Agents (spawn, channels, sync) | Yes | Yes | Yes | Full lifecycle |
| Signals (reactive state) | Yes | Yes | Yes | Full reactivity: computed, subscribers, batched updates |
| Streams + `\|>` pipe operator | Yes | Yes | Yes | map, filter, take, skip, collect, fold, backpressure |
| Pipes (multi-agent composition) | Yes | Yes | Yes | Agent spawn chain compilation |
| Tensors | No | No | No | Experimental only, no language integration |
| GPU compute | Yes | No | No | CUDA + Vulkan via dlopen |
| Standard library modules | Yes | Partial | Partial | 25+ native `.mn` modules |

### Performance (LLVM native vs Python)

| Workload | Speedup |
|----------|---------|
| Fibonacci (recursive) | **22–26x faster** |
| Stream pipeline (1M items) | **62.8x faster** |
| Matrix multiply (100x100) | **22.9x faster** |
| Agent message passing (10K) | On par |

---

## Release History

| Version | Theme | Highlights |
|---------|-------|------------|
| **v0.1.0** ✅ | Foundation | Bootstrap compiler, Lark parser, semantic checker, Python emitter, LLVM backend (basic), runtime, LSP, VS Code extension, CLI, stdlib, benchmarks, 1,400+ tests |
| **v0.2.0** ✅ | Self-Hosting | LLVM string/list codegen, C runtime (ring buffers, thread pool), self-hosted lexer + parser + semantic + emitter (5,800+ lines .mn), `str`/`int`/`float` builtins |
| **v0.3.0** ✅ | Depth Over Breadth | Traits, module resolution, LLVM agent codegen, arena memory, `TypeKind` enum, getting started guide, governance, 110+ e2e tests, benchmarks rewrite, 1,960+ tests |
| **v0.3.1** ✅ | Release Polish | Dynamic versioning from `VERSION` file, documentation tests |
| **v0.4.0** ✅ | Ready for the World | Scope cleanup (`experimental/`), C runtime hardening (sanitizers, CI), structured diagnostics (spans, multi-error, recovery), C FFI (`extern "C"`, `--link-lib`), self-hosted verification (96 bootstrap tests), LSP improvements (incremental parse, cross-module go-to-def), VS Code extension extracted |
| **v0.5.0** ✅ | The Ecosystem | String interpolation, linter, Python interop, WASM playground, package registry, doc generator, language reference, cookbook, 2,200+ tests |
| **v0.6.0** ✅ | Compiler Infrastructure | MIR pipeline (SSA IR, lowering, optimizer, dual emitters), bootstrap frozen at v0.6.0, self-hosted semantic checker, 2,500+ tests |
| **v0.7.0** ✅ | Self-Standing | Self-hosted MIR lowering (lower.mn), built-in test runner, agent observability (tracing + metrics), DWARF debug info, deployment infrastructure, 2,983 tests |
| **v0.8.0** ✅ | Native Parity | LLVM backend parity (maps, signals, streams, closures), complete string methods, pipe definitions, C runtime expansion (TCP, TLS, file I/O, event loop), 3,020 tests |
| **v0.9.0** ✅ | Connected | Native stdlib in `.mn` (JSON, CSV, HTTP, WebSocket, crypto, regex), cross-module LLVM compilation, integration tests, Dato updated, 3,400+ tests |
| **v1.0.0** ✅ | Stable | Language freeze (SPEC 1.0 Final), emitter hardening (25+ bugs fixed), formal memory model, stability policy, C runtime security hardening, mnc-stage1 15/15 golden tests, 3,600+ tests |
| **v1.0.1** ✅ | Critical Bug Fixes | `_EarlyReturn.err` fix, DWARF/version strings to 1.0.0, C runtime atomics (acquire/release), SPSC explicit ordering |
| **v1.0.2** ✅ | Type System Soundness | `UNKNOWN == X` → `False`, `is_compatible_with()`, partial generic arity fix, 9 blanket exceptions replaced, `_coerce_arg` diagnostics |
| **v1.0.3** ✅ | MIR Emitter Memory | Arena lifecycle in MIR emitter, boxed+closure allocs through arena, agent queue drain, signal destructor callback |
| **v1.0.4** ✅ | Drop Glue | Arena-based cleanup (explicit drop glue deferred — LLVM dominance errors across basic blocks) |
| **v1.0.5** ✅ | Self-Hosted Emitter | 15/15 golden tests pass; mnc-stage1 self-compilation blocked by SIGSEGV on large modules |
| **v1.0.6** ✅ | Self-Compilation | CI job added (continue-on-error); fixed-point blocked by v1.0.5 crashes |
| **v1.0.7** ✅ | Codegen Improvements | Relaxed SSA docs, strict_ssa mode, has_side_effects property, MIR verifier test suite (32 tests) |
| **v1.0.8** ✅ | Optimizer & Toolchain | Algebraic simplification (5 rules), `$CC` support, `--werror`, host triple, `-O1` release builds |
| **v1.0.9** ✅ | Stdlib & Language Polish | Match exhaustiveness checking, async-only-when-needed, stdlib dedup (`string_utils.mn`) |
| **v1.0.10** ✅ | Production Hardening | ASan/TSan clean (52/52), C hardening pass, 3,697 tests, VERSION 1.0.10 |
| **v1.0.11** ✅ | Self-Hosted Compiler Fixes | Pointer-only large struct refactor, stack alignment fix, linkage fix, alloca size mismatch fix; **15/15 golden at -O1**, 3,698 tests, self-compilation unblocked |
| **v1.1.0** ✅ | AI Native | LLM drivers (OpenAI, Anthropic, local), embedding providers with batching/caching, RAG pipeline with chunking and vector store |
| **v1.2.0** ✅ | Data & Storage | Dato data engine (tables, aggregations, joins, reshape, I/O), database drivers (SQLite, PostgreSQL, Redis, KV, pooling, migrations), TOML/YAML encoding, filesystem stdlib |
| **v1.3.0** ✅ | Web & Security | Web crawler (robots.txt, frontier, extraction), vulnerability scanner (template-driven, fingerprinting), HTTP fuzzer (mutation engine), HTTP server toolkit (auth, body, cookies, sessions, rate limiting, SSE, templates) |
| **v2.0.0** ✅ | Beyond the Machine | WebAssembly backend (MIR-to-WAT, WASI, JS bridge, wasm-ld multi-module linking), GPU compute (CUDA + Vulkan via dlopen, MIR GpuKernel metadata, PTX/SPIR-V codegen), cross-compilation targets (wasm32, iOS, Android), mobile runtime (cooperative scheduler, epoll event loop, string interning cap, memory profiling), CI matrix (WASM + Android), Python backends deprecated, playground dual-mode (WASM+Pyodide), 4,465+ tests |
| **v2.1.0** ✅ | Self-Compilation Progress | Stage2 IR validates (llvm-as), 8 root causes fixed, mnc-stage2 reaches lowerer, systemic Python lowerer bugs documented |
| **v2.2.0** ✅ | Stage2 Debugging | Valgrind-based crash diagnostics, struct field offset mapping, PHI type recovery |
| **v3.0.0** ✅ | La Culebra Se Muerde La Cola | C emit backend, bilingual keywords (Spanglish/English), indentation syntax, tipo/modo type unification, @Agent syntax, migration tool |
| **v3.0.1** ✅ | Bootstrap Runs | mnc-stage1 runs, string truncation blocks bootstrap |
| **v3.0.2** ✅ | Golden Tests | 15/15 golden tests, struct names fixed |
| **v3.0.3** ✅ | Self-Compilation Fixes | 25/25 golden tests, PHI type recovery, __op_* fallback |
| **v3.1.0** ✅ | Native File I/O | Native file I/O, string escapes, runtime functions |
| **v3.2.0** ✅ | Seed Update | Seed binary updated, 25/25 golden verified |
| **v3.3.0** ✅ | **Fixed Point** | String-tagged dispatch (enum tag mismatch solved), sret ABI fix, COW write-back fix, field index fix, two-stage bootstrap from seed (no Python), fixed point: stage3 == stage4 |

---

## The Road Ahead

### v0.5.0 — "The Ecosystem" ✅

> Build the infrastructure that turns Mapanare from a compiler into a platform.
> See [`PLAN-v0.5.0.md`](v0.5.0/PLAN.md) for the detailed execution plan.

#### Phase 1: String Interpolation & Language Polish

- `"value is ${expr}"` syntax in grammar, parser, semantic, both emitters
- Multi-line string literals (`"""..."""`)
- Small grammar quality-of-life fixes deferred from prior versions

#### Phase 2: Linter

- `mapanare lint` — unused variables, shadowing, unreachable code, anti-patterns
- Integrated into LSP for real-time feedback
- `mapanare lint --fix` for auto-fixable issues

#### Phase 3: Python Interop

- `extern "Python"` calling convention
- Direct Python function calls from Mapanare (Python backend)
- Type marshalling between Mapanare and Python types
- Test: call numpy from Mapanare

#### Phase 4: WASM Playground (new repo: [`mapanare-playground`](#organization--repo-strategy))

- Compile Python transpiler backend to WASM (via Pyodide)
- Minimal web UI: editor, output panel, share button
- Pre-loaded getting-started examples
- Deploy to `play.mapanare.dev`

#### Phase 5: Package Registry (new repo: [`mapanare-registry`](#organization--repo-strategy))

- Registry backend at `mapanare.dev/packages`
- `mapanare search`, `mapanare publish` (install already works)
- Semantic versioning with conflict resolution
- Package categories and discoverability

#### Phase 6: Documentation & Ecosystem

- Language reference (all syntax, all types, all builtins)
- Cookbook: 10+ real-world examples
- `mapanare doc` — generate docs from doc comments
- Contributor onboarding improvements

---

### v0.6.0 — "Compiler Infrastructure" ✅

> Replace ad-hoc patterns with principled compiler architecture.

#### Intermediate Representation (MIR) ✅

- SSA-based, typed IR between AST and emission (`mir.py`, `mir_builder.py`)
- AST → MIR lowering pass (`lower.py`, 1,397 lines)
- MIR optimizer passes: constant folding, DCE, copy propagation, block merging (`mir_opt.py`)
- MIR → Python emitter (`emit_python_mir.py`)
- MIR → LLVM IR emitter (`emit_llvm_mir.py`)
- CLI commands: `emit-mir` for MIR text dump
- Enables future backends (WASM native, SPIR-V) without duplicating logic

#### Freeze Python Bootstrap ✅

- Python bootstrap frozen at v0.6.0 in `bootstrap/` (22 files)
- `bootstrap/Makefile` for three-stage bootstrap verification
- Self-hosted compiler continues development in `mapanare/self/*.mn`

---

### v0.7.0 — "Self-Standing" ✅

> Self-hosting completion, observability, and developer tools.

#### Self-Hosted MIR Lowering ✅

- `lower.mn` (2,629 lines): AST → MIR lowering in Mapanare, completing 7-module self-hosted compiler
- `emit_llvm.mn` rewritten to consume MIR instead of AST
- Compiler driver (`main.mn`) wired to AST → MIR → LLVM pipeline

#### Built-in Test Runner ✅

- `mapanare test` discovers and runs `@test` functions in `.mn` files
- `assert` statement in grammar, AST, MIR, and both emitters
- `--filter` flag for substring matching

#### Agent Observability ✅

- OpenTelemetry-compatible tracing with `--trace` flag (console and OTLP HTTP export)
- Prometheus metrics with `--metrics :PORT` flag
- 33 structured error codes in `MN-X0000` format
- Native C runtime trace hooks

#### DWARF Debug Info ✅

- `mapanare build -g` emits compile units, functions, line numbers, variables, struct types
- Source-level debugging with `gdb`/`lldb`

#### Deployment Infrastructure ✅

- `mapanare deploy init` scaffolds Dockerfile
- Health/readiness endpoints (`/health`, `/ready`, `/status`)
- Supervision trees (one-for-one, one-for-all, rest-for-one)
- `@supervised` decorator
- SIGTERM graceful shutdown with drain timeout

---

### v0.8.0 — "Native Parity" ✅

> Every core feature works on both backends. The LLVM backend is no longer a second-class citizen.
> See [`PLAN-v0.8.0.md`](v0.8.0/PLAN.md) for the detailed execution plan.

#### Phase 1: LLVM Map/Dict Codegen

- Map literal construction via C runtime hash table
- Key/value insertion, lookup, deletion, iteration
- C runtime: `__mn_map_new()`, `__mn_map_set()`, `__mn_map_get()`, `__mn_map_del()`, `__mn_map_iter()`
- Both AST and MIR emitters

#### Phase 2: LLVM Signal Reactivity

- Signal dependency graph in C runtime (not just get/set)
- Automatic recomputation when dependencies change
- Computed signals with lazy evaluation
- Subscriber notification, batched updates

#### Phase 3: LLVM Stream Operators

- Stream creation, `map`, `filter`, `take`, `skip`, `collect` on LLVM backend
- Pipe operator (`|>`) targeting native stream runtime
- Backpressure via bounded buffers in C runtime
- Stream fusion optimization in MIR optimizer

#### Phase 4: LLVM Closure Capture

- Free variable capture via closure environment structs
- Heap-allocated closure environments with arena integration
- Lambda expressions with captured variables

#### Phase 5: Remaining LLVM Gaps

- Complete string method coverage (all 12+ methods)
- Pipe definitions (multi-agent composition)
- Remaining builtin functions
- Cross-backend consistency tests: every Python test must pass on LLVM

#### Phase 6: C Runtime Expansion

- TCP socket primitives: `__mn_tcp_connect()`, `__mn_tcp_listen()`, `__mn_tcp_send()`, `__mn_tcp_recv()`
- TLS via OpenSSL FFI: `__mn_tls_handshake()`, `__mn_tls_read()`, `__mn_tls_write()`
- File I/O primitives: `__mn_file_open()`, `__mn_file_read()`, `__mn_file_write()`, `__mn_file_close()`
- Event loop: `__mn_event_loop_new()`, `__mn_event_loop_add_fd()`, `__mn_event_loop_run()` (epoll/kqueue/IOCP)
- These C primitives are the foundation for native stdlib in v0.9.0

#### Phase 7: Validation & Release

- Every test runs on LLVM backend, not just Python
- Feature status table in README updated to reflect reality
- Remove false claims (REPL, tensor integration)

---

### v0.9.0 — "Connected" ✅

> Mapanare can talk to the outside world. Stdlib modules are written in `.mn`,
> compiled natively — no Python at runtime.

**Philosophy:** One import, one module, no fragmentation. `import net::http` gives you
everything `requests`, `urllib3`, and `httpx` do in Python — in a single, native module.

#### Phase 1: `encoding/json.mn` — JSON Parser/Serializer

- Recursive descent JSON parser, pure Mapanare
- `json.decode<T>(str) -> Result<T, JsonError>` — typed deserialization
- `json.encode(value) -> String` — serialization
- Schema validation built-in
- Streaming parser for large documents

#### Phase 2: `encoding/csv.mn` — CSV Parser

- `csv.read(path) -> Result<Frame, CsvError>` (integrates with Dato)
- `csv.write(data, path) -> Result<Void, CsvError>`
- Configurable delimiter, quoting, headers

#### Phase 3: `net/http.mn` — Unified HTTP Client

- **One import, done.** No `requests` vs `urllib3` vs `httpx` fragmentation
- GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS
- Headers, query params, body (JSON, form, multipart, raw)
- Connection pooling, keep-alive, HTTP/1.1
- TLS/SSL with configurable cert validation
- Timeouts, retries with backoff, redirect following
- Response streaming (chunked transfer)
- Cookie jar
- Request/response interceptors (middleware hooks via traits)
- **Request fingerprinting** — every request gets a unique trace hash for debugging,
  replay, and audit. This is the foundation that makes crawler and security packages
  possible later. Think: every HTTP call is observable, hashable, and replayable.

#### Phase 4: `net/http/server.mn` — HTTP Server with Routing

- Route definitions with path params: `@route("/api/users/${id}")`
- Middleware chain (auth, logging, CORS, rate limiting) via traits
- Request/response types with typed headers
- Static file serving
- Agent-per-request model (each handler is a supervised agent)
- This is the Flask/FastAPI replacement — but native, compiled, agent-aware

#### Phase 5: `net/websocket.mn` — WebSocket Client + Server

- RFC 6455 WebSocket protocol
- Client: `ws.connect(url) -> Result<WsConnection, WsError>`
- Server: WebSocket upgrade from HTTP server
- Typed channels map naturally to WebSocket frames
- Ping/pong, close handshake, fragmentation

#### Phase 6: `crypto.mn` — Cryptographic Primitives

- Hashing: SHA-256, SHA-512, BLAKE2 (FFI to OpenSSL/libsodium)
- HMAC for message authentication
- JWT encode/decode/verify
- Base64 encode/decode
- Random bytes generation
- TLS certificate utilities

#### Phase 7: `text/regex.mn` — Regular Expressions

- NFA/DFA-based regex engine, pure Mapanare (or FFI to PCRE2)
- `regex.match(pattern, text) -> Option<Match>`
- `regex.find_all(pattern, text) -> List<Match>`
- `regex.replace(pattern, text, replacement) -> String`
- Capture groups, character classes, quantifiers
- Essential for data cleaning (Dato), crawling, and security scanning

#### Phase 8: Cross-Module LLVM Compilation

- Resolve imports across `.mn` files at LLVM IR level
- Link multiple LLVM modules into a single binary
- Stdlib modules available to LLVM backend

#### Phase 9: Validation & Release

- All stdlib modules tested as native binaries, not Python
- Dato package updated to use `encoding/csv.mn` and `encoding/json.mn`
- Integration tests: HTTP client → HTTP server round-trip in native binary

---

### v1.0.0 — "Stable" ✅

> The language is frozen. Breaking changes require an RFC and deprecation cycle.
> No new features — hardening, documentation, and guarantees only.

#### Language Freeze ✅

- Language specification promoted from "Working Draft" to "1.0 Final"
- All syntax, semantics, and type rules documented and frozen
- New features require RFC + deprecation cycle after this point

#### Self-Hosted Stage 1 ✅

- Python bootstrap compiles 8,632-line self-hosted compiler → 7.2MB native binary (`mnc-stage1`)
- `mnc-stage1` passes 15/15 golden tests (every language feature)
- Pointer-based enum dispatch, enum payload layout alignment, security-hardened C runtime
- Concatenation pipeline for single-file self-compilation (Python bootstrap verified)

#### Formal Memory Model ✅

- `docs/MEMORY_MODEL.md` (854 lines) — arena lifecycle, string ownership, struct/enum ownership,
  list/map lifecycle, agent message passing, signal/stream values, closure environments

#### Stability Guarantees ✅

- `docs/STABILITY.md` — backwards compatibility policy, deprecation cycle, semver contract
- `docs/MIGRATION_TEMPLATE.md` — migration guide template
- `docs/rfcs/RFC_PROCESS.md` — RFC process for language changes
- Deprecation warnings in semantic checker (`@deprecated`)
- `--edition` flag, version-stamped binaries

#### Hardening ✅

- 3,628 tests pass, 0 failures
- C runtime security audit completed (1 CRITICAL, 6 HIGH, 7 MEDIUM findings)
- CRITICAL + HIGH integer overflow fixes applied (checked arithmetic in list/string/map)
- Compiler pipeline optimized (805ms → 503ms, 37% faster)
- All documentation current and cross-referenced

---

### v1.0.1 — "Critical Bug Fixes"

> Trivial fixes that should have shipped with v1.0.0.
> Every item here is a one-liner or search-and-replace.
> Driven by [v1.0.0 code review](.reviews/v1.0.0/README.md) items #5, #6, #11, #12, #15, #22, #23.

#### Correctness Bugs

- Fix `_EarlyReturn.value` → `_EarlyReturn.err` in `emit_python_mir.py:465` (crashes every MIR `?` error path)
- Fix `AssertionError` typo → `AssertionError` in `emit_python_mir.py:959,964`, `bootstrap/emit_python_mir.py`, `docs/SPEC.md`, `test_test_runner.py`
- Fix MEMORY_MODEL.md lines 260-264 claiming "semantic checker enforces move semantics" (it does not — update docs to match reality)

#### Stale Version Strings

- DWARF producer string: `"mapanare 0.7.0"` → `"mapanare 1.0.0"` in `emit_llvm_mir.py:483`
- Self-hosted compiler: `"mapanare 0.8.0"` → `"mapanare 1.0.0"` in `mapanare/self/main.mn:29`

#### C Runtime Data Races

- Make `s_next_agent_id` atomic (`_Atomic uint64_t`) in `mapanare_runtime.c:441`
- Make `s_trace_hook` atomic (`_Atomic` function pointer) in `mapanare_runtime.c:165,1093`
- Use `memory_order_acquire`/`memory_order_release` in SPSC ring buffer instead of default `seq_cst` (`mapanare_runtime.c:96-113`)

---

### v1.0.2 — "Type System Soundness"

> Fix the type system holes that let incorrect programs compile silently.
> The single highest-impact change for compiler correctness.
> Driven by review items #1, #8, #14.

#### `TypeInfo.__eq__` Overhaul

- `UNKNOWN == X` must return `False`, not `True` (`types.py:121`)
- Add `TypeInfo.is_compatible_with(other)` for permissive matching where needed
- Fix partial generic matching: `len(self.args) != len(other.args)` must return `False` (`types.py:135-136`)
- Fix `make_type()` defaulting unknown types to `TypeKind.STRUCT` — should error instead (`types.py:338`)
- Audit and fix all call sites that relied on UNKNOWN compatibility (MethodCallExpr, SyncExpr, ErrorPropExpr, FieldAccessExpr, for-loop variables)

#### Emitter Safety

- Replace blanket `except Exception: pass` in `emit_llvm_mir.py` (lines 1503, 1728, 1730, 2782) with specific guards and DEBUG logging
- Add diagnostic counter to `_coerce_arg` fallback path — log warnings when memory reinterpretation fires

---

### v1.0.3 — "MIR Emitter Memory"

> The MIR emitter is the "preferred" path but ignores arenas entirely.
> Fix this so the preferred pipeline doesn't leak worse than the legacy one.
> Driven by review items #7, #10, #9.

#### Arena Integration for MIR Emitter

- Port `mn_arena_create`/`mn_arena_destroy` per-function lifecycle from AST emitter (`emit_llvm.py:844-891`) to MIR emitter (`emit_llvm_mir.py`)
- Route boxed field allocations (`emit_llvm_mir.py:2525, 2637, 2959`) through arena instead of raw `malloc`
- Route closure environment allocations (`emit_llvm_mir.py:3470`) through arena

#### Agent Message Queue Drain

- `mapanare_agent_destroy` must drain inbox/outbox and free remaining messages (match pool destroy behavior at `mapanare_runtime.c:405-408`)

#### Signal Type-Aware Cleanup

- Add destructor callback `void (*dtor)(void *value)` to `MnSignal` struct
- Call destructor on value overwrite and on `__mn_signal_free`
- Zero runtime cost when callback is NULL

---

### v1.0.4 — "Drop Glue"

> Stop leaking compound values. This is the most impactful change for practical memory safety.
> Driven by review items #3, #26.

#### String Drop Glue

- At function exit, emit `__mn_str_free` for all locally-created heap strings that are not returned
- Handle early return paths (break, return from nested scope)
- Struct fields containing strings: recursive cleanup on struct drop

#### Closure Environment Cleanup

- Emit `__mn_free(env_ptr)` when closure goes out of scope (simple case: non-escaping closures)
- For escaping closures: reference counting (increment on copy, decrement on scope exit)
- Track closure escape analysis in MIR lowerer

#### Range Iterator Cleanup

- Emit `free()` for range iterators on all exit paths (normal, break, return)
- Compiler must emit cleanup — runtime provides no safety net

#### Validation

- Add leak-detection tests: create closures in a loop, verify RSS does not grow unboundedly
- Add drop-glue tests for struct-containing-string patterns
- All existing tests must still pass (drop glue must not double-free)

---

### v1.0.5 — "Self-Hosted Emitter Completion"

> Fix self-hosted emitter gaps so `mnc-stage1` can compile its own source code.
> Each fix is small (20-30 lines of `.mn`) but there are many.

#### Self-Hosted Emitter Gaps

- Add `ListPush` instruction to `Instruction` enum, lowerer, and emitter
- Add string method dispatch in `emit_mir_call` (char_at, substr, contains, split, etc.)
- Handle `return List<T>` from functions (list built with push in loops)
- Handle large struct return-by-sret in self-hosted emitter
- Fix remaining match expression lowering for complex patterns

#### Validation

- `mnc-stage1` compiles `lexer.mn` without crashing
- `mnc-stage1` compiles all 7 modules individually
- `mnc-stage1` compiles `mnc_all.mn` (concatenated 8,632-line source)

---

### v1.0.6 — "Self-Compilation"

> The compiler compiles itself. Fixed-point verification passes.

#### Fixed-Point Verification

- Stage 2: `mnc-stage1` compiles `mnc_all.mn` → `mnc-stage2`
- Stage 3: `mnc-stage2` compiles `mnc_all.mn` → `mnc-stage3`
- Binary diff: `mnc-stage2 == mnc-stage3` (byte-identical — fixed point achieved)
- `scripts/verify_fixed_point.sh` updated for concatenated source
- Fixed-point job added to CI (gate for future releases)

---

### v1.0.7 — "Codegen Improvements"

> Fix MIR-path agent codegen gap, improve LLVM IR quality, harden the verifier.
> Driven by review items #13, #16, #21, #27, #30.

#### MIR Agent Handler Emission

- Emit `__mn_handler_{AgentName}` wrapper function in MIR emitter (currently only AST emitter does this)
- Pass handler function pointer to `mapanare_agent_new` instead of `null` (`emit_llvm_mir.py:3293`)
- Agents spawned via MIR path must process messages

#### Phi Node Improvements

- For clean SSA values (not mutated via field_set), emit proper LLVM phi nodes instead of alloca/load/store
- Keep alloca demotion only for genuinely mutable variables
- Add `nsw` (no signed wrap) flags to integer add/sub/mul for better LLVM optimization

#### MIR Verifier Hardening

- Document "relaxed SSA" invariant in `mir.py` module docstring (mutable variables may be redefined)
- Add optional `--strict-ssa` verification mode
- Integrate `MIRVerifier.verify_module()` into standard test suite — run on all 15 golden tests after lowering and after optimization

---

### v1.0.8 — "Optimizer & Toolchain"

> Improve the MIR optimizer and build infrastructure.
> Driven by review items #17, #24, #29.

#### Optimizer Improvements

- Implement dominance tree computation (Lengauer-Tarjan, ~100 lines)
- Add algebraic simplification to constant folder: `x + 0 = x`, `x * 1 = x`, `x * 0 = 0`, `x - x = 0`
- Improve constant propagation to work across basic blocks (not just Copy-of-Const)
- Add `has_side_effects` property to `Instruction` base class (replace fragile `_SIDE_EFFECT_TYPES` tuple)

#### Build System

- Build scripts respect `$CC` environment variable: `os.environ.get("CC", "gcc")` in `build_stage1.py`, `${CC:-gcc}` in `verify_fixed_point.sh`
- Add `--werror` flag to `mapanare check` and `mapanare build` (treat warnings as errors)
- Default to host target triple via `llvm.get_default_triple()` when none specified

#### Optimization Levels

- Use `opt_level=1` (not 0) for release builds in `build_stage1.py` — enables mem2reg, instcombine, simplifycfg, sroa

---

### v1.0.9 — "Stdlib & Language Polish"

> Fix the missing primitives that the stdlib revealed.
> Make the language comfortable for real-world code.
> Driven by review items #19, #20, #28, #33.

#### Missing String Primitives

- `starts_with(prefix)` and `ends_with(suffix)` string methods
- `StringBuilder` type or `join(separator, parts: List<String>)` builtin (eliminate O(n^2) concat)
- Character arithmetic: `ord(ch) -> Int` and `chr(code) -> String` builtins
- `byte_at(index)` → integer value for byte-level operations

#### Match Exhaustiveness

- Implement compile-time exhaustiveness checking for `match` on enums (spec promises this)
- Enumerate all variants, verify all covered, emit error for missing arms

#### Operator Dispatch Through Traits

- `==` calls `Eq::eq`, `<` calls `Ord::cmp` when trait is implemented
- Makes user-defined types work with generic algorithms

#### Async-Only-When-Needed

- Only make `main()` async when function body uses `spawn`/`sync`/`send`
- Simple programs skip asyncio overhead (~1-2ms startup savings)

#### Stdlib Deduplication

- Extract shared utilities (`to_lower_char`, `hex_digit_value`, `parse_int_manual`, `to_upper`) into `text/string_utils.mn`
- Update `net/http.mn`, `net/http/server.mn`, `encoding/json.mn` to import shared module

---

### v1.0.10 — "Production Hardening"

> Sanitizers clean, native tests passing, performance baselined, match exhaustiveness verified.
> The language is fully polished and ready for ecosystem development.

#### Memory Safety Verification

- AddressSanitizer clean on full test suite
- ThreadSanitizer clean on agent/concurrency tests
- Runtime debug mode: `mapanare build --debug-memory` for bounds checking
- Ownership rule tests (arena scoping, string tag-bit, agent message, closure environment, drop glue)

#### Native Test Coverage (Linux)

- Build I/O runtime on Linux (`build_io.py`)
- Event loop tests (7), file I/O tests (12), TCP tests (7), TLS tests (4)
- C hardening tests (2)
- Remaining skips audited — target ≤6 platform-specific skips

#### Performance Baselines

- Full benchmark suite results recorded as v1.0 baselines
- No regression > 10% vs v0.8.0
- Cross-module compilation overhead measured
- Measure impact of drop glue on common patterns

#### Remaining Security Fixes

- Signal lifetime management (null subscriber pointers on free)
- Thread-local signal state (or mutex protection)
- Batch pending array overflow prevention (grow beyond 256, or error on overflow)
- Signal handler async-signal-safety (set flag, handle in main thread)

---

### v1.1.0 — "AI Native"

> Mapanare's agent system becomes the best way to build AI applications.
> Prompture's core ideas become language primitives.

#### `ai/llm.mn` — Native LLM Driver System

- Each LLM provider is an agent: `agent OpenAIDriver { handle(prompt: LLMRequest) -> LLMResponse }`
- Built-in provider registry (OpenAI, Anthropic, Google, Groq, Ollama, local HTTP)
- Structured extraction: `extract<T>(model, prompt) -> Result<T, ExtractionError>`
- Tool/function calling as agent message passing
- Token tracking and cost as signal values (reactive cost monitoring)
- Streaming responses as first-class streams
- **Multi-agent patterns are just pipe composition:**
  - Sequential: `prompt |> model_a |> model_b`
  - Parallel: `spawn ModelA(prompt)` + `spawn ModelB(prompt)` + collect
  - Consensus: spawn N agents, vote on results
  - Debate: agents exchange messages via channels

#### `ai/embedding.mn` — Vector Embeddings

- Embedding generation via LLM provider agents
- Vector similarity (cosine, dot product, euclidean)
- In-memory vector index for small-scale RAG

#### `ai/rag.mn` — Retrieval-Augmented Generation

- Document chunking (semantic, sliding window)
- Chunk → embedding → index pipeline
- Query → retrieve → augment → generate pipeline
- All steps are agents connected by pipes

#### Plugin/Skill System Pattern

- Traits replace framework-level plugin systems (Tukuy equivalent)
- `trait Skill { fn name() -> String; fn execute(input: String) -> Result<String, Error> }`
- `impl Skill for WebSearch { ... }`
- Skills discoverable via module imports, no runtime registry needed

---

### v1.2.0 — "Data & Storage"

> Database access, data formats, and Dato maturity.

#### `db/sql.mn` — SQL Database Drivers

- PostgreSQL, SQLite, MySQL drivers (FFI to libpq, libsqlite3, libmysqlclient)
- Parameterized queries (no SQL injection by design — compile-time query validation)
- Connection pooling via agent supervision (each connection is a supervised agent)
- Transaction support with `Result`-based commit/rollback
- Migrations as first-class concept

#### `db/kv.mn` — Key-Value Store Interface

- Trait-based: `trait KVStore { fn get(key) -> Option<V>; fn set(key, value); ... }`
- Redis driver (FFI to hiredis)
- Embedded KV (arena-backed, in-process)

#### `encoding/yaml.mn`, `encoding/toml.mn`

- YAML parser/serializer, pure Mapanare
- TOML parser/serializer, pure Mapanare
- Both produce typed structs via `decode<T>(str) -> Result<T, Error>`

#### `fs.mn` — Filesystem Operations

- Directory walking, file watching (inotify/FSEvents/ReadDirectoryChanges FFI)
- Permissions, metadata, temp files
- Path manipulation utilities

#### Dato v1.0

- Real implementation on top of `encoding/csv.mn`, `encoding/json.mn`, `db/sql.mn`
- Typed columns (Int, Float, String, Bool — not string-erased)
- Columnar storage for memory efficiency
- Stream-based chunked processing for large files
- Agent-parallel transforms (split frame across N agents)
- Parquet I/O (FFI to Apache Arrow C library)
- Full `describe()`, aggregation, joins, pivot, melt
- `data |> filter(pred) |> group_by("col") |> mean_col("value")` — native, compiled

---

### v1.3.0 — "Web Platform & Security"

> Build full web apps and security tools in Mapanare.

#### Web Platform

- `net/http/server` v2 — sessions, cookie auth, auth middleware, SSE (Server-Sent Events)
- `net/tls.mn` — certificate management, Let's Encrypt automation
- React interop pattern: Mapanare backend + React frontend (like ServerKit architecture)
  - Static file serving, API routing, WebSocket bridge
  - Dev server with hot reload proxy
- Template engine for server-side rendering (optional)

#### `net/crawl` Package — Web Crawler

- Built on `net/http.mn` + agents for parallel crawling
- DOM parsing (FFI to a C HTML parser like lexbor or Gumbo)
- Driver plugin trait for headless browsers:
  - `trait BrowserDriver { fn navigate(url); fn query(selector) -> List<Element>; ... }`
  - Selenium/Playwright bridge via FFI or subprocess
- Rate limiting, politeness policies (robots.txt, sitemap parsing)
- Crawl state persistence (resume interrupted crawls)
- Request fingerprinting from `net/http` for deduplication

#### `security/scan` Package — Vulnerability Scanner

- Nuclei-inspired template-based scanning
- YAML scan templates define: request, matchers (status, header, body regex, response time)
- **Agents are the scanners** — each target gets a supervised scanner agent
- Parallel scanning is natural: spawn 100 scanner agents, collect findings
- Request fingerprinting + trace hashing for audit trails
- Severity classification (INFO, LOW, MEDIUM, HIGH, CRITICAL)
- Evidence collection and reporting
- Pluggable matcher system via traits:
  - `trait Matcher { fn matches(response: HttpResponse) -> Bool }`
  - Status matcher, header matcher, body regex matcher, response time matcher
- Integration with `net/crawl` for target discovery

#### `security/fuzz` Package — Fuzzing Primitives

- Input mutation strategies
- Coverage-guided fuzzing (using LLVM sanitizer integration)
- HTTP parameter fuzzing built on `net/http`

---

### v2.0.0 — "Beyond the Machine" ✅

> Every device. Every accelerator. No Python.
> See [`PLAN-v2.0.0.md`](v2.0.0/PLAN.md) for the detailed execution plan.

#### GPU Compute ✅

- GPU kernel dispatch (`@gpu` / `@cuda` / `@vulkan` annotations → CUDA/Vulkan via dlopen)
- MIR `GpuKernel` metadata, PTX string embedding, SPIR-V byte embedding in LLVM codegen
- C runtime: CUDA Driver API + Vulkan compute pipeline, tensor ops (add/sub/mul/div/matmul)
- Built-in GPU kernels (PTX for CUDA, GLSL/SPIR-V for Vulkan)
- GPU benchmarks: matmul, reduction, transfer, elementwise

#### WebAssembly Backend ✅

- MIR-to-WAT emitter (2,785 lines), linear memory, bump allocation, JS bridge, WASI support
- wasm-ld multi-module linking (`wasm_linker.py`): linker config, import/export tables, memory layout
- CLI: `mapanare emit-wasm [--binary] [--link] [--wasi]` with multi-file support
- Targets: `wasm32-unknown-unknown` (browser), `wasm32-wasi` (server)

#### Mobile Targets ✅

- Cross-compilation: `aarch64-apple-ios`, `aarch64-linux-android`, `x86_64-linux-android`
- Mobile-tuned C runtime: cooperative agent scheduler, smaller arenas/queues, epoll event loop
- String interning pool with configurable cap, memory profiling helpers

#### Platform Targets — Still Open

- Desktop app framework (native windowing, not Electron)

#### Python Deprecation ✅

- v1.0.0: Python backend marked as "legacy, for reference only"
- v1.2.0: Python backend removed from default build
- v2.0.0: Python backend archived in `bootstrap/`
- The Python bootstrap compiler remains in `bootstrap/` permanently as the Stage 0 seed

#### Future (post-v2.0.0)

- Tensor autograd (automatic differentiation for ML training loops)
- SIMD intrinsics for vectorized data processing (Dato acceleration)
- Effect typing (compile-time tracking of agent side effects)
- Session types (static protocol verification for channels)
- Hot code reload (swap agent code without restart)
- Formal semantics (core calculus with soundness proofs)

#### Ecosystem Vision

| Application | Built With |
|-------------|------------|
| CachiBot equivalent | Mapanare agents + `ai/llm` + `net/http/server` + React frontend |
| ServerKit equivalent | `net/http/server` + `net/websocket` + `db/sql` + agents for process management |
| Prompture equivalent | `ai/llm` stdlib — agents ARE the drivers, pipes ARE the groups |
| Tukuy equivalent | Traits + modules — `impl Skill for X` pattern |
| Dato (pandas replacement) | Native package — `frame \|> filter \|> group_by \|> mean_col` |
| Nuclei equivalent | `security/scan` package — agent-per-target, template-based |
| Firecrawl equivalent | `net/crawl` package — agent-based parallel crawling |

---

## Dependency Chain

```
v0.8.0 (Native Parity)
  │  LLVM: maps, signals, streams, closures
  │  C runtime: sockets, file I/O, event loop
  │
  └→ v0.9.0 (Connected)
       │  Stdlib in .mn: HTTP, JSON, WebSocket, regex, crypto
       │  Cross-module LLVM compilation
       │  Dato package starts working
       │
       └→ v1.0.0 (Stable)
            │  Language freeze, 15/15 golden tests
            │  No new features — hardening only
            │
            ├→ v1.0.1  Critical Bug Fixes (trivial: typos, version strings, data races)
            ├→ v1.0.2  Type System Soundness (UNKNOWN equality, partial generics)
            ├→ v1.0.3  MIR Emitter Memory (arena integration, agent drain, signal dtor)
            ├→ v1.0.4  Drop Glue (strings, closures, iterators)
            ├→ v1.0.5  Self-Hosted Emitter (ListPush, string methods, sret)
            ├→ v1.0.6  Self-Compilation (fixed-point: stage2 == stage3)
            ├→ v1.0.7  Codegen Improvements (MIR agent handler, phi nodes, nsw, verifier)
            ├→ v1.0.8  Optimizer & Toolchain (dominance tree, $CC, --werror, -O1)
            ├→ v1.0.9  Stdlib & Language Polish (string builder, exhaustiveness, trait ops)
            ├→ v1.0.10 Production Hardening (ASan/TSan clean, benchmarks, security)
            │
            │  ── language is fully polished after v1.0.10 ──
            │
            ├→ v1.1.0 (AI Native)
            │    LLM drivers, embeddings, RAG
            │    Prompture absorbed into stdlib
            │
            ├→ v1.2.0 (Data & Storage)
            │    SQL, KV, YAML, TOML, filesystem
            │    Dato v1.0 with typed columns
            │
            └→ v1.3.0 (Web Platform & Security)
                 │  Web framework, React interop
                 │  Crawler, vulnerability scanner, fuzzer
                 │
                 └→ v2.0.0 (Beyond the Machine) ✅
                      GPU (CUDA+Vulkan), WASM backend, mobile targets
                      Cooperative scheduler, wasm-ld, CI matrix
                      Python deprecated, 4,465+ tests
```

---

## How Language Primitives Map to Real-World Patterns

Mapanare's primitives aren't academic — they directly replace framework-level concepts:

| Concept | Python Framework | Mapanare Primitive |
|---------|-----------------|-------------------|
| LLM API calls | Prompture drivers (classes) | **Agents** — each provider is an agent |
| Multi-model orchestration | Prompture groups (library) | **Pipes** — `model_a \|> model_b \|> model_c` |
| Reactive state tracking | Custom event systems | **Signals** — `let cost = signal(0.0)` auto-propagates |
| Data streaming | SSE libraries, async generators | **Streams** — first-class `\|>` composition |
| Plugin systems | Tukuy (framework) | **Traits + Modules** — `impl Driver for OpenAI` |
| HTTP servers | Flask/FastAPI (framework) | **Agent-based server** — each handler is a supervised agent |
| WebSocket connections | Socket.io (library) | **Channel\<T\>** — typed bidirectional messaging |
| Background workers | Threading/asyncio | **Agent spawn** — supervised, observable, restartable |
| Config/data formats | Multiple packages (json, yaml, toml) | **`encoding/` stdlib** — one module per format |
| Database connections | SQLAlchemy + psycopg2 | **`db/sql`** — connection-per-agent, pool via supervision |
| Parallel scanning | ThreadPoolExecutor + requests | **Agents** — spawn 100 scanners, collect via channels |

---

## Self-Hosted Compiler Status

The compiler is written in Mapanare itself — 8,288+ lines across seven modules.

| Component | Lines | Status |
|-----------|------:|--------|
| Lexer (`lexer.mn`) | 498 | ✅ Complete |
| AST definitions (`ast.mn`) | 255 | ✅ Complete |
| Parser (`parser.mn`) | 1,721 | ✅ Complete |
| Semantic checker (`semantic.mn`) | 1,607 | ✅ Complete |
| MIR lowering (`lower.mn`) | 2,629 | ✅ Complete |
| LLVM IR emitter (`emit_llvm.mn`) | 1,497 | ✅ Complete (MIR-based rewrite) |
| Compiler driver (`main.mn`) | 81 | ✅ Complete (MIR pipeline wired) |
| Module resolution (`self::` imports) | — | ✅ Working |
| Fixed-point verification | — | ⏳ Blocked — cross-module LLVM compilation needed (v0.9.0 infra) |
| Bootstrap test suite (264 tests) | — | ✅ All passing |

---

## Architecture

```
yourfile.mn
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                  mapanare compiler                    │
│  Lexer → Parser → AST → Semantic Check → MIR Lower  │
│                                              │       │
│                                     MIR Optimizer    │
│                                        (O0–O3)      │
└──────────┬───────────────┬───────────────────────────┘
           │               │
      ┌────┴────┐     ┌────┴────┐
      ▼         ▼     ▼         ▼
   LLVM IR    WASM   Python   GPU Kernel
      │      (WAT)  [legacy]  (PTX/SPIR-V)
 ┌────┴────┐   │
 ▼    ▼    ▼   ▼
x86  ARM  iOS  Browser / WASI / Cloudflare
     Android
```

Native dependency layers (post-v2.0):
```
Layer 4: stdlib/*.mn        ← Mapanare modules (json, http, sql, gpu, wasm, etc.)
Layer 3: mapanare/self/*.mn ← Self-hosted compiler (8,288+ lines)
Layer 2: runtime/native/*.c ← C runtime (memory, threads, sockets, TLS, GPU, event loop)
Layer 1: LLVM / wasm-ld     ← Code generation and linking targets
Layer 0: OS / Browser       ← Linux, macOS, Windows, iOS, Android, WASI, browser
```

No Python required at runtime after v1.0.

---

## Organization & Repo Strategy

Mapanare is a monolith-first project. The compiler, runtime, stdlib, LSP, and C runtime
all change together and share one test suite — splitting them would mean coordinating
multiple PRs and version bumps for every change. Only split when a component has a
**different language, different build system, and never changes in the same PR** as the compiler.

### Current (`Mapanare-Research`)

| Repo | Purpose |
|------|---------|
| [`Mapanare`](https://github.com/Mapanare-Research/Mapanare) | Compiler, runtime, stdlib, LSP, C runtime, benchmarks, packaging |
| [`tree-sitter-mapanare`](https://github.com/Mapanare-Research/tree-sitter-mapanare) | Tree-sitter grammar for editors |
| [`skills`](https://github.com/Mapanare-Research/skills) | AI coding agent skills (Claude Code, Cursor, Windsurf) |
| [`.github`](https://github.com/Mapanare-Research/.github) | Org profile and default community health files |

### Planned New Repos

| Repo | When | Why Split |
|------|------|-----------|
| `mapanare-vscode` | v0.4.0 ✅ | TypeScript project, `npm publish` to VS Code marketplace |
| `mapanare-registry` | v0.5.0 ✅ | New web backend (different stack, separate deploy) |
| `mapanare-playground` | v0.5.0 ✅ | New web app (Pyodide/WASM, separate deploy pipeline) |
| `dato` | v0.9.0+ | Mapanare package — DataFrame/data analysis (pandas+numpy replacement) |

### What Stays in the Monolith (and why)

| Component | Why it stays |
|-----------|-------------|
| Compiler (`mapanare/`) | Core — everything depends on it |
| LSP (`mapanare/lsp/`) | Imports compiler directly, changes with it |
| C runtime (`runtime/native/`) | Tightly coupled to LLVM emitter |
| Python runtime (`runtime/`) | Legacy, tested with compiler until deprecated |
| Stdlib (`stdlib/`) | Tested with compiler, same release (migrating from .py to .mn) |
| Self-hosted sources (`mapanare/self/`) | Compiled by the bootstrap, same test suite |
| Bootstrap (`bootstrap/`) | Frozen reference, no independent changes |

---

## Review Panel Response

### v0.3.0 Review (March 9, 2026) — Aggregate **6.6/10** (range: 5.5–8.2)

7 expert reviewers. Their top concerns and what we did about them:

| Concern | Severity | Resolution |
|---------|----------|------------|
| Memory management undefined / leaking | CRITICAL | ✅ Arena-based memory in v0.3.0 |
| LLVM backend missing headline features | CRITICAL | ✅ Agent codegen in v0.3.0, full parity in v0.8.0 |
| No module resolution | CRITICAL | ✅ File-based imports in v0.3.0 |
| No traits / interfaces | HIGH | ✅ Trait system in v0.3.0 |
| String-based type comparisons | HIGH | ✅ TypeKind enum in v0.3.0 |
| Benchmark integrity issues | HIGH | ✅ Benchmarks rewritten in v0.3.0 |
| Empty CHANGELOG | HIGH | ✅ Populated in v0.3.0 |
| No Getting Started tutorial | HIGH | ✅ 12-section guide in v0.3.0 |
| No end-to-end tests | HIGH | ✅ 110+ e2e tests in v0.3.0 |
| No governance / templates | HIGH | ✅ COC, SECURITY, templates in v0.3.0 |
| Scope too broad (GPU/model) | MEDIUM | ✅ v0.4.0 scope reduction |
| No FFI | MEDIUM | ✅ v0.4.0 FFI |
| No intermediate representation | MEDIUM | ✅ MIR in v0.6.0 |
| No metrics / tracing | MEDIUM | ✅ v0.7.0 observability (tracing + metrics) |
| No browser playground | MEDIUM | ✅ v0.5.0 playground |

**All 15 items resolved.** Score rose from 6.6 → ~7.8 at v1.0.0.

### v1.0.0 Review (March 15, 2026) — Median **7.8/10** (range: 7.0–8.2)

7 reviewers, all issued **PASS WITH NOTES**. Full report: [`.reviews/v1.0.0/README.md`](../../.reviews/v1.0.0/README.md)

| Concern | Severity | Target |
|---------|----------|--------|
| `TypeInfo.__eq__` UNKNOWN == anything returns True | CRITICAL | 🔧 v1.0.2 |
| No ownership/borrowing enforcement (docs claim it exists) | CRITICAL | 🔧 v1.0.1 (doc fix) |
| Closure environments unconditionally leaked | CRITICAL | 🔧 v1.0.4 |
| Generics parsed but not monomorphized | CRITICAL | 📋 v1.1.0+ |
| `_EarlyReturn.value` should be `.err` (MIR emitter bug) | HIGH | 🔧 v1.0.1 |
| `AssertionError` typo across 4 files | HIGH | 🔧 v1.0.1 |
| MIR emitter does not use arenas | HIGH | 🔧 v1.0.3 |
| `_coerce_arg` 95-line type system bypass | HIGH | 🔧 v1.0.2 |
| Signal leaks string values on update | HIGH | 🔧 v1.0.3 |
| Agent destroy doesn't drain message queues | HIGH | 🔧 v1.0.3 |
| SPSC ring buffer uses seq_cst (perf) | HIGH | 🔧 v1.0.1 |
| Trace hook not atomic (data race) | HIGH | 🔧 v1.0.1 |
| Phi nodes demoted to alloca | MEDIUM | 🔧 v1.0.7 |
| Blanket `except Exception: pass` in emitter | MEDIUM | 🔧 v1.0.2 |
| `s_next_agent_id` not atomic | MEDIUM | 🔧 v1.0.1 |
| MIR verifier SSA relaxation undocumented | MEDIUM | 🔧 v1.0.7 |
| Optimizer lacks dominance-based analysis | MEDIUM | 🔧 v1.0.8 |
| Tensors specified but unimplemented | MEDIUM | 📋 v1.1.0+ |
| Stdlib missing primitives (char arith, string builder) | MEDIUM | 🔧 v1.0.9 |
| No match exhaustiveness checking | MEDIUM | 🔧 v1.0.9 |
| MIR agent handler passes null pointer | MEDIUM | 🔧 v1.0.7 |

**Strategic advice:** Reframe from "AI-native" to "agent-native" — the agent model is the real and unique contribution. Tensors and LLM integration are aspirational until they ship.

All 21 actionable items are mapped to v1.0.1–v1.0.10 patch releases. Generics monomorphization and tensors are deferred to v1.1.0+.

---

## Contributing

1. Read [`SPEC.md`](SPEC.md) to understand the language design
2. Browse [open issues](https://github.com/Mapanare-Research/Mapanare/issues) for something that interests you
3. All PRs require tests
4. Language changes require an [RFC](rfcs/) first

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for full guidelines.

---

*Built by [Mapanare Research](https://github.com/Mapanare-Research) · [mapanare.dev](https://mapanare.dev)*
