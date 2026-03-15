# Mapanare Roadmap

> **Mapanare** is an AI-native compiled programming language.
> Agents, signals, streams, and tensors are first-class primitives — not libraries.
>
> [mapanare.dev](https://mapanare.dev) · [GitHub](https://github.com/Mapanare-Research/Mapanare)

---

## Where We Are (v1.0.0)

Mapanare is stable. The language specification is frozen at v1.0 Final — syntax, semantics,
and type system changes now require RFC + deprecation cycle. The compiler pipeline is hardened,
the memory model is formally documented, and stability guarantees are published. Seven stdlib
modules compile natively via LLVM. The self-hosted compiler (8,288+ lines) passes IR verification.
**No Python required at runtime.** **3,600+ tests pass** across the full pipeline.

### What works today

- **Full compiler pipeline** — Lexer, parser, semantic checker, MIR lowering, MIR optimizer (O0–O3), code emitter
- **MIR pipeline** — Typed SSA-based intermediate representation with basic blocks and explicit terminators
- **Two compilation targets** — Native binaries via LLVM IR (production) and Python transpilation (legacy, for reference and bootstrapping only)
- **Self-hosted compiler** — 8,288+ lines of `.mn` across 7 modules (lexer, ast, parser, semantic, lower, emit_llvm, main)
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
- **Native C runtime** — Arena-based memory, lock-free SPSC ring buffers, thread pool, semaphore-based scheduling
- **LLVM agent codegen** — `spawn`, `send` (`<-`), `sync` targeting C runtime with OS threads
- **Cross-compilation** — Linux x64, macOS ARM64, Windows x64
- **Optimization passes** — Constant folding, DCE, agent inlining, stream fusion
- **LSP server** — Diagnostics, hover, go-to-definition, find-references, autocomplete
- **VS Code extension** — Syntax highlighting, LSP integration, snippets, commands
- **Package manager** — Project manifests (`mapanare.toml`), git-based installation, dependency resolution
- **Standard library** — I/O, HTTP, time, math, text, structured logging (Python-only, see v0.9.0 for native)
- **Formatter** — `mapanare fmt` for consistent code style
- **Binary distribution** — PyInstaller builds, install scripts (Unix + Windows), GitHub Releases CI
- **Getting Started guide** — 12-section tutorial from install to streams

### LLVM Backend Feature Status

| Feature | Python Backend | LLVM Backend | Notes |
|---------|:-:|:-:|--------|
| Functions, closures, lambdas | Yes | Yes | Full closure capture via environment structs |
| Structs, enums, pattern matching | Yes | Yes | Full tagged union + switch |
| `if`/`else`, `for..in`, `while` | Yes | Yes | |
| Type inference, generics | Yes | Yes | |
| `Result`/`Option` | Yes | Yes | |
| `print`/`println`, `str`/`int`/`float`/`len` | Yes | Yes | |
| Lists: literals, indexing, `push`/`pop`/`length` | Yes | Yes | |
| String methods | Yes | Yes | All methods: length, find, substring, contains, split, trim, replace, to_upper, to_lower |
| Dictionaries/Maps | Yes | Yes | Robin Hood hash table in C runtime |
| Traits (`trait`, `impl Trait for Type`) | Yes | Yes | |
| Module imports (`import`, `pub`, multi-file) | Yes | Yes | |
| Agents (spawn, channels, sync) | Yes | Yes | Full lifecycle |
| Signals (reactive state) | Yes | Yes | Full reactivity: computed, subscribers, batched updates |
| Streams + `\|>` pipe operator | Yes | Yes | map, filter, take, skip, collect, fold, backpressure |
| Pipes (multi-agent composition) | Yes | Yes | Agent spawn chain compilation |
| Tensors | No | No | Experimental only, no language integration |
| Standard library modules | Partial | Yes | 7 native `.mn` modules: JSON, CSV, HTTP, server, WebSocket, crypto, regex |

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
| **v1.0.0** ✅ | Stable | Language freeze (SPEC 1.0 Final), emitter hardening (25+ bugs fixed), self-hosted fixed-point pipeline, formal memory model, stability policy, C runtime security audit, 3,600+ tests |

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

### v1.0.0 — "Stable"

> The language is frozen. Breaking changes require an RFC and deprecation cycle.
> No new features — hardening, documentation, and guarantees only.

#### Language Freeze

- Language specification promoted from "Working Draft" to "1.0 Final"
- All syntax, semantics, and type rules documented and frozen
- New features require RFC + deprecation cycle after this point

#### Self-Hosted Fixed Point

- Stage 1: Python bootstrap compiles self-hosted `.mn` → native binary
- Stage 2: Native binary compiles self-hosted `.mn` → verify identical IR
- Three-stage bootstrap verification in CI
- The compiler can compile itself without Python

#### Formal Memory Model

- Arena lifecycle documented (allocation, scope cleanup, free)
- String ownership rules (tag-bit system for heap vs. constant)
- Agent message passing ownership transfer
- Signal/stream value lifecycle

#### Stability Guarantees

- Backwards compatibility policy defined
- Deprecation cycle: warn for one minor version, remove in next major
- Semantic versioning contract published
- Migration guide template for breaking changes

#### Final Hardening

- Full test pass across both backends
- Performance regression sweep
- Security audit of C runtime (buffer overflows, use-after-free)
- All documentation current and cross-referenced

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

### v2.0.0 — "Ecosystem"

> The package ecosystem self-sustains. Mapanare applications replace Python equivalents.

#### Performance & Compute

- GPU kernel dispatch (`@gpu` / `@cpu` annotations → CUDA/Metal/Vulkan via SPIR-V)
- Tensor autograd (automatic differentiation for ML training loops)
- SIMD intrinsics for vectorized data processing (Dato acceleration)
- SPIR-V backend for GPU compute shaders

#### Language Evolution

- Effect typing (compile-time tracking of agent side effects)
- Session types (static protocol verification for channels)
- Hot code reload (swap agent code without restart)
- Formal semantics (core calculus with soundness proofs)

#### Platform Targets

- WASM backend (browser-native Mapanare, not Pyodide wrapper)
- Mobile compilation target (iOS/Android via LLVM)
- Desktop app framework (native windowing, not Electron)

#### Python Deprecation Timeline

- v1.0.0: Python backend marked as "legacy, for reference only"
- v1.2.0: Python backend removed from default build
- v2.0.0: Python backend archived in `bootstrap/`
- The Python bootstrap compiler remains in `bootstrap/` permanently as the Stage 0 seed

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
            │  Language freeze, self-hosted fixed point
            │  No new features — hardening only
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
                 └→ v2.0.0 (Ecosystem)
                      GPU, WASM, mobile, Python deprecated
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
| Fixed-point verification | — | ⏳ Blocked by bootstrap emitter gaps (v1.0.0) |
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
└────────────────────────┬─────────────────────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
               Python      LLVM IR
            (transpile)      │
            [legacy]    ┌────┴────┐
                        ▼         ▼
                   Native x86  Native ARM
```

Native dependency layers (post-v1.0):
```
Layer 3: stdlib/*.mn        ← Mapanare modules (json, http, sql, etc.)
Layer 2: mapanare/self/*.mn ← Self-hosted compiler (8,288+ lines)
Layer 1: runtime/native/*.c ← C runtime (memory, threads, sockets, TLS)
Layer 0: LLVM               ← Code generation target
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

In March 2026, a panel of 7 expert reviewers scored Mapanare at **6.6/10** (range: 5.5–8.2).
Their top concerns and what we did about them:

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

---

## Contributing

1. Read [`SPEC.md`](SPEC.md) to understand the language design
2. Browse [open issues](https://github.com/Mapanare-Research/Mapanare/issues) for something that interests you
3. All PRs require tests
4. Language changes require an [RFC](rfcs/) first

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for full guidelines.

---

*Built by [Mapanare Research](https://github.com/Mapanare-Research) · [mapanare.dev](https://mapanare.dev)*
