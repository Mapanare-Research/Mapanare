<div align="center">

<img width="3200" height="1344" alt="MapanareDevTo" src="https://github.com/user-attachments/assets/99b80387-afd9-4b07-beb8-59a8f63f7ac7" />

# Mapanare

**/mah-pah-NAH-reh/**

**The AI-native programming language.**

*Agents. Signals. Streams. Tensors. First-class, not frameworks.*

Built after years of hitting Python's limits in AI-native, concurrent, and tensor-heavy software.

Mapanare compiles to native binaries via LLVM and WebAssembly, with a self-hosted compiler in progress. A legacy Python transpiler backend exists for reference and bootstrapping only.

English | [Español](docs/README.es.md) | [中文版](docs/README.zh-CN.md) | [Português](docs/README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Native_Backend-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-Backend-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)
![Platform](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?style=flat-square)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-3698_passing-brightgreen.svg?style=flat-square)]()
[![CI](https://github.com/Mapanare-Research/Mapanare/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/Mapanare-Research/Mapanare/actions/workflows/ci.yml?query=branch%3Adev)
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Try it Online**](https://mapanare-research.github.io/mapanare/) · [**Getting Started**](docs/getting-started.md) · [Language Reference](docs/reference.md) · [Cookbook](docs/cookbook.md) · [Why Mapanare?](#why-mapanare) · [Install](#install) · [The Language](#the-language) · [Benchmarks](#benchmarks) · [CLI](#cli) · [Architecture](#compiler-architecture) · [Roadmap](docs/roadmap/ROADMAP.md) · [Contributing](#contributing) · [Discord](https://discord.gg/5hpGBm3WXf)

</div>

---

## Why Mapanare?

Mapanare started with a self-taught teenager in Venezuela building a calculator in ActionScript 2 for math class. Fifteen years later, after ColdFusion, PHP, and especially Python, the case for a new language became unavoidable. Python was the language that stuck the longest, but years of building AI-native, concurrent, and data-heavy systems with it made the cracks impossible to ignore.

Agents lived in frameworks. Reactive state lived in conventions. Streams were stitched together with libraries. Tensor mistakes showed up at runtime, sometimes after a long run was already underway. The compiler had no idea what kind of work the program was actually doing.

Mapanare exists because those are language problems, not library problems.

A familiar failure in today's stack looks like this:

```python
# Python / PyTorch
x = torch.randn(32, 768)
w = torch.randn(512, 256)
y = x @ w  # fails at runtime after the job has already started
```

```mn
// Mapanare (experimental LLVM tensor backend)
let x: Tensor<Float>[32, 768] = ...
let w: Tensor<Float>[512, 256] = ...
let y = x @ w    // compile error: incompatible tensor shapes
```

That same idea drives the rest of the language. Mapanare makes these primitives **part of the language**:

- **Agents** are as natural as functions — declare, spawn, send, and sync with dedicated syntax checked by the compiler
- **Signals** replace callback hell with automatic dependency tracking
- **Streams** compose with `|>` the way you think about data, with operator fusion built in
- **Tensors** get compile-time shape validation in the experimental LLVM backend
- **No OOP** — structs, enums, and pattern matching instead of class hierarchies

Read the full [manifesto](docs/manifesto.md).

---

## Install

### Linux / macOS

```bash
curl -fsSL https://mapanare.dev/install | bash
```

### Windows (PowerShell)

```powershell
irm https://mapanare.dev/install.ps1 | iex
```

### Manual Download

Download the latest binary from [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

| Platform | Archive |
|----------|---------|
| Linux (x64) | `mapanare-linux-x64.tar.gz` |
| macOS (Apple Silicon) | `mapanare-mac-arm64.tar.gz` |
| Windows (x64) | `mapanare-win-x64.zip` |

Extract and add `mapanare` to your PATH, then verify:

```bash
mapanare --version
```

---

## Feature Status

What works today vs. what's planned.

| Feature | LLVM Backend | WASM Backend | Python Backend | Status |
|---------|:-:|:-:|:-:|--------|
| Functions, closures, lambdas | Yes | Yes | Yes | Stable |
| Structs, enums, pattern matching | Yes | Yes | Yes | Stable |
| `if`/`else`, `for..in`, `while` | Yes | Yes | Yes | Stable |
| Type inference, generics | Yes | Yes | Yes | Stable |
| `Result`/`Option` | Yes | Yes | Yes | Stable |
| `print`/`println`, `str`/`int`/`float`/`len` | Yes | Yes | Yes | Stable |
| Lists: literals, indexing, `push`/`pop`/`length` | Yes | Yes | Yes | Stable |
| String methods: `length`/`find`/`substring`/`contains`/`split`/`trim`/`replace`/... | Yes | Yes | Yes | Stable |
| Dictionaries/Maps | Yes | Yes | Yes | Stable |
| Traits (`trait`, `impl Trait for Type`) | Yes | Yes | Yes | Stable |
| Module imports (`import`, `pub`, multi-file) | Yes | Yes | Yes | Stable |
| Agents (spawn, channels, sync) | Yes | Yes | Yes | Stable |
| Signals (reactive state, computed, batched) | Yes | Yes | Yes | Stable |
| Streams + `\|>` pipe operator | Yes | Yes | Yes | Stable |
| Pipes (multi-agent composition) | Yes | Yes | Yes | Stable |
| Tensors (shape validation, `@` matmul) | No | No | No | Experimental |
| GPU compute (`@gpu`, `@cuda`, `@vulkan`) | Yes | No | No | New in v2.0.0 |
| WebAssembly output (WAT/WASM) | — | Yes | — | New in v2.0.0 |
| WASI support (file I/O, env, clock) | — | Yes | — | New in v2.0.0 |
| AI stdlib (LLM, embeddings, RAG) | Yes | No | No | New in v1.1.0 |
| Data engine (Dato) | Yes | No | No | New in v1.2.0 |
| Database drivers (SQLite, Postgres, Redis) | Yes | No | No | New in v1.2.0 |
| Encoding (TOML, YAML) | Yes | No | No | New in v1.2.0 |
| Filesystem stdlib | Yes | No | No | New in v1.2.0 |
| Web crawler, vulnerability scanner, fuzzer | Yes | No | No | New in v1.3.0 |
| HTTP server toolkit | Yes | No | No | New in v1.3.0 |
| Cross-module LLVM compilation | Yes | — | Yes | Stable |
| Mobile targets (iOS, Android) | Planned | — | — | Planned |

---

## The Language

### Basics

```mn
fn main() {
    let name = "World"
    println("Hello, " + name + "!")

    let mut count = 0
    while count < 5 {
        println(str(count))
        count += 1
    }

    for i in 0..5 {
        println(str(i))
    }
}
```

### Structs, Enums & Pattern Matching

No classes, no inheritance. Structs, enums, and pattern matching instead.

```mn
enum Shape {
    Circle(Float),
    Rect(Float, Float),
}

fn area(s: Shape) -> Float {
    match s {
        Circle(r) => 3.14159 * r * r,
        Rect(w, h) => w * h,
    }
}
```

### Error Handling

```mn
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}

let value = divide(10.0, 3.0)?
```

### Lists & Strings

```mn
let mut items: List<Int> = []
items.push(1)
items.push(2)
items.push(3)
println(str(items.length()))    // 3
println(str(items[0]))         // 1

let s = "hello world"
println(str(s.length()))       // 11
println(s.substring(0, 5))    // hello
```

### Agents

Concurrent actors with typed channels.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

let greeter = spawn Greeter()
greeter.name <- "World"
let result = sync greeter.greeting
print(result)
```

### Signals

Reactive state with automatic dependency tracking.

```mn
let mut count = signal(0)
let doubled = signal { count * 2 }
```

### Streams

Async pipelines with the `|>` operator.

```mn
let data = stream([1, 2, 3, 4, 5])
let result = data
    |> filter(fn(x) { x > 2 })
    |> map(fn(x) { x * 10 })
```

### GPU Compute (v2.0.0)

GPU-accelerated tensor operations via CUDA and Vulkan, loaded dynamically at runtime.

```mn
@gpu
fn matmul(a: Tensor<Float>[M, K], b: Tensor<Float>[K, N]) -> Tensor<Float>[M, N] {
    return a @ b
}
```

### WebAssembly (v2.0.0)

Compile Mapanare to WebAssembly for browser and server-side execution.

```bash
mapanare emit-wasm hello.mn              # Emit WAT
mapanare emit-wasm --binary hello.mn     # Emit WAT + compile to WASM
```

---

## Benchmarks

Cross-language benchmarks comparing Mapanare against Python, Go, and Rust. Each benchmark runs 3 times; median wall time reported. Run `python -m benchmarks.cross_language.run_benchmarks` to reproduce.

### Performance (wall time, lower is better)

| Benchmark | Features Tested | Mapanare | MN Native (LLVM) | Python | Go | Rust | vs Python |
|-----------|-----------------|----------|-------------------|--------|----|------|-----------|
| Fibonacci (recursive, n=35) | Functions, recursion, arithmetic | 1.2104s | **0.0448s** | 1.1885s | 0.0341s | 0.0211s | 26.5x (native) |
| Message Passing (10K msgs) | Agents, spawn, send (`<-`), sync, concurrency | 0.9989s | — | 1.0978s | 0.0025s | 0.0203s | 1.1x |
| Stream Pipeline (1M items) | Streams, `stream()`, `.map()`, `.filter()`, `.fold()` | 1.1141s | **0.0165s** | 1.0342s | 0.0005s | 0.0001s | 62.8x (native) |
| Matrix Multiply (100x100) | Nested loops, arithmetic, variables | 0.1769s | **0.0199s** | 0.4556s | 0.0005s | 0.0009s | 22.9x (native) |
| Agent Pipeline (1K msgs) | Agents, spawn, send, sync, string ops, multi-stage | — | — | — | — | — | — |

### Expressiveness (lines of code, lower is better)

| Benchmark | Features Tested | Mapanare | Python | Go | Rust |
|-----------|-----------------|----------|--------|----|------|
| Fibonacci (recursive, n=35) | Functions, recursion | **8** | 12 | 18 | 23 |
| Message Passing (10K msgs) | Agents, channels | **16** | 28 | 27 | 32 |
| Stream Pipeline (1M items) | Stream primitives | **8** | 17 | 18 | 20 |
| Matrix Multiply (100x100) | Nested loops, math | **12** | 21 | 37 | 33 |
| Agent Pipeline (1K msgs) | Multi-stage agents, strings | **18** | 32 | 33 | 28 |

> **Key takeaway:** Mapanare's interpreted backend matches Python speed (it transpiles to Python), but the LLVM native backend delivers **22-63x** speedups over Python. Mapanare programs are consistently the shortest across all benchmarks.

**Benchmark notes:**
- **Fibonacci:** Tests pure computation speed. No I/O, no concurrency. Interpreted backend runs as Python; native backend compiles to LLVM IR.
- **Message Passing:** Tests agent spawn/send/sync with 4 concurrent workers. Interpreted backend uses asyncio (single-threaded cooperative concurrency); native backend not yet wired (Phase 2.1).
- **Stream Pipeline:** Tests `stream()`, `.map()`, `.filter()`, `.fold()` primitives with stream fusion. Does NOT test backpressure or hot streams.
- **Matrix Multiply:** Tests nested loops and arithmetic. Uses constant initialization (`1.0 * 2.0`), not realistic matrix data — measures loop/arithmetic throughput only.
- **Agent Pipeline:** Tests real-world pattern: 3-stage pipeline (parse -> validate -> transform) processing string messages. Measures agent communication overhead across pipeline stages.

### Stream Pipelines (1M items, runtime microbenchmarks)

| Pipeline | Throughput | Avg Latency |
|----------|-----------|-------------|
| `fold_sum` | **10.3M items/sec** | 0.10 us |
| `take(1000)` | **6.3M items/sec** | 0.16 us |
| `filter` | **4.2M items/sec** | 0.24 us |
| `map` | **4.2M items/sec** | 0.24 us |
| `map \| filter` | **2.6M items/sec** | 0.39 us |
| `chained_maps(5)` | **1.7M items/sec** | 0.60 us |
| `chained_maps(10)` | **1.2M items/sec** | 0.80 us |

```bash
make benchmark                       # run all benchmarks
python -m benchmarks.cross_language.run_benchmarks     # cross-language comparison suite
```

---

## CLI

```
mapanare run <file>           Compile and run
mapanare build <file>         Compile to native binary via LLVM
mapanare jit <file>           JIT-compile and run natively
mapanare check <file>         Type-check only
mapanare compile <file>       Transpile to Python (deprecated)
mapanare emit-llvm <file>     Emit LLVM IR
mapanare emit-wasm <file>     Emit WebAssembly (WAT/WASM)
mapanare test [path]          Discover and run @test functions
mapanare fmt <file>           Format source code
mapanare lint <file>          Lint for code quality issues
mapanare doc <file>           Generate HTML docs from doc comments
mapanare deploy init          Scaffold Dockerfile and deploy config
mapanare init [path]          Initialize a new project
mapanare install <pkg>        Install a package
mapanare publish [path]       Publish package to registry
mapanare search <query>       Search package registry
mapanare login                Authenticate with registry
mapanare targets              List supported compilation targets
```

Options: `-O0` to `-O3` optimization levels, `-o <path>` output file, `--target <triple>` cross-compilation target, `--binary` (WASM binary output), `-g` debug info, `--trace` agent tracing, `--metrics :PORT` Prometheus metrics, `--filter` test filter.

---

## Compiler Architecture

```
.mn source -> Lexer -> Parser -> AST -> Semantic Analysis -> MIR Lowering -> MIR Optimizer -> Emit
                                                                                                 |
                                                                              LLVM IR | WASM | Python (deprecated)
                                                                                 |         |
                                                                          Native Binary   WAT/WASM
```

| Stage | Details |
|-------|---------|
| **Lexer** | Lark-based tokenizer (18 keywords, 29 operators) |
| **Parser** | LALR with precedence climbing |
| **Semantic** | Type checking, scope analysis, builtins registry |
| **MIR Lowering** | AST -> typed SSA intermediate representation with basic blocks |
| **MIR Optimizer** | Constant folding, dead code elimination, copy propagation, block merging (`-O0` to `-O3`) |
| **Emit LLVM** | MIR -> LLVM IR generation via llvmlite with cross-compilation targets |
| **Emit WASM** | MIR -> WebAssembly text format (WAT) with linear memory and JS bridge |
| **Emit Python** | MIR -> Python (deprecated): agents map to asyncio, signals to reactive containers |

---

## Runtime

| Primitive | Capabilities |
|-----------|-------------|
| **Agents** | Lifecycle management, typed channels, supervision (restart/stop), backpressure, metrics |
| **Signals** | Dependency graph with automatic recomputation, batched updates, change streams |
| **Streams** | Async iterables with fusion, hot/cold semantics, backpressure strategies (buffer, drop, error) |
| **Result/Option** | `Ok`/`Err`/`Some`/`None` with `?` operator support |
| **Native C** | Lock-free SPSC ring buffers, per-core thread pool, atomic backpressure counters |
| **GPU** | CUDA Driver API + Vulkan compute via `dlopen`, built-in tensor kernels (add/sub/mul/div/matmul) |

---

## Standard Library

| Module | Provides |
|--------|----------|
| `io` | File I/O agents, read/write helpers |
| `fs` | Filesystem operations: read, write, walk, glob, metadata, temp files |
| `http` | HTTP client/server agents, body parsing, cookies, sessions, rate limiting, SSE, templates |
| `time` | Timers, intervals, debounce, throttle, stopwatch |
| `math` | Constants, trig, statistics, linear algebra helpers |
| `text` | Case conversion, search, split/join, slug, padding |
| `log` | Structured logging with agent context, JSON/text output |
| `pkg` | Project manifests, package install, registry publish |
| `ai/llm` | LLM driver with provider abstraction (OpenAI, Anthropic, local), streaming, tool calls |
| `ai/embedding` | Embedding provider with batching, caching, similarity search |
| `ai/rag` | RAG pipeline with document chunking, vector store, retrieval |
| `db/sql` | SQL query builder and execution |
| `db/sqlite` | SQLite driver via native C runtime |
| `db/postgres` | PostgreSQL driver via native C runtime |
| `db/redis` | Redis client |
| `db/kv` | Key-value store abstraction |
| `db/pool` | Connection pooling |
| `db/migrate` | Schema migration runner |
| `encoding/toml` | TOML parser and serializer |
| `encoding/yaml` | YAML parser and serializer |
| `gpu/device` | GPU device detection and selection |
| `gpu/kernel` | Kernel management and dispatch |
| `gpu/tensor` | GPU-accelerated tensor operations |
| `wasm/bridge` | JavaScript interop: imports, exports, DOM access, events |
| `wasm/runtime` | WASI preview 1: file I/O, environment, clock, random |

See the full [stdlib reference](docs/stdlib.md).

---

## Ecosystem Packages

| Package | Description |
|---------|------------|
| **Dato** (`dato/`) | DataFrame/data analysis engine — tables, aggregations, joins, null handling, reshape, CSV/JSON I/O |
| **Crawl** (`crawl/`) | Web crawler with robots.txt, URL frontier, content extraction, persistence |
| **Scan** (`scan/`) | Template-driven vulnerability scanner with fingerprinting and report generation |
| **Fuzz** (`fuzz/`) | HTTP fuzzer with mutation engine and wordlist generation |

---

## GPU Compute (v2.0.0)

GPU compute via CUDA and Vulkan, loaded dynamically at runtime (no compile-time SDK dependency):

- `@gpu`, `@cuda`, `@vulkan` annotations on functions for automatic dispatch
- Built-in kernels: PTX for CUDA, GLSL/SPIR-V for Vulkan (tensor add/sub/mul/div/matmul)
- `stdlib/gpu/`: device detection, kernel management, GPU-accelerated tensors
- C runtime (`runtime/native/mapanare_gpu.c`): CUDA Driver API + Vulkan compute via `dlopen`

---

## WebAssembly Backend (v2.0.0)

Compile Mapanare to WebAssembly for browser and server-side execution:

- MIR-to-WAT emitter with linear memory, bump allocation, string constants, JS bridge
- Targets: `wasm32-unknown-unknown` (browser), `wasm32-wasi` (server)
- WASI preview 1 support: file I/O, environment, clock, random
- Playground runtime for in-browser execution

---

## Editor Support

### VS Code

The VS Code extension lives in its own repository: [mapanare-vscode](https://github.com/Mapanare-Research/mapanare-vscode)

- Syntax highlighting for `.mn` files
- Code snippets (agent, pipe, fn, signal, stream)
- LSP integration: hover, go-to-definition, find-references, diagnostics, autocomplete

Install the LSP server: `mapanare-lsp`

---

## AI Agent Skill

Give your AI coding agent full fluency in Mapanare. One command — your agent knows every keyword, type, pattern, and CLI command.

```bash
npx skills add Mapanare-Research/skills
```

Works with **Claude Code**, **Cursor**, **Windsurf**, and any agent that supports the [skills](https://skills.sh) ecosystem.

After installing, just ask your agent naturally:

| Prompt | What your agent does |
|--------|---------------------|
| *"Create an agent that monitors sensor data"* | Writes an agent with typed channels, signals, and anomaly detection |
| *"Build a data pipeline for sentiment analysis"* | Composes a multi-stage pipe with Fetcher |> Extractor |> Classifier |
| *"Track metrics with reactive state"* | Uses `signal()`, `computed {}`, and `batch {}` for automatic propagation |
| *"Matrix multiply with shape checking"* | Generates `Tensor<Float>[M, N]` with `@` operator — shapes verified at compile time |
| *"Process logs in real time"* | Builds a stream pipeline with `filter`, `throttle`, and `for_each` |
| *"Scaffold a new project"* | Runs `mapanare init`, knows all CLI flags and optimization levels |

See [Mapanare-Research/skills](https://github.com/Mapanare-Research/skills) for full examples and manual install instructions.

---

## Self-Hosted Compiler

The compiler is written in Mapanare itself (`mapanare/self/`) — 8,288+ lines across 7 modules:

- `lexer.mn` — Tokenizer (498 lines)
- `ast.mn` — AST definitions (255 lines)
- `parser.mn` — Recursive descent parser (1,721 lines)
- `semantic.mn` — Type checker (1,607 lines)
- `lower.mn` — MIR lowering (2,629 lines)
- `emit_llvm.mn` — LLVM IR emitter from MIR (1,497 lines)
- `main.mn` — Compiler driver (81 lines)

Bootstrap strategy: Python compiler (Stage 0) compiles self-hosted `.mn` sources (Stage 1), which must reproduce identical output (Stage 2 fixed-point verification).

---

## Project Structure

```
mapanare/
├── mapanare/              Compiler (lexer, parser, semantic, MIR, emit, optimizer, jit)
│   ├── self/              Self-hosted .mn compiler sources
│   └── lsp/               Language Server Protocol
├── runtime/               Runtime (agents, signals, streams, result types)
│   └── native/            Native C runtime (thread pool, ring buffers, GPU, DB)
├── stdlib/                Standard library (io, fs, http, ai, db, encoding, gpu, wasm, ...)
├── dato/                  Dato data engine (tables, aggregations, joins, I/O)
├── crawl/                 Web crawler (URL parser, robots.txt, frontier, extraction)
├── scan/                  Vulnerability scanner (templates, fingerprinting, reports)
├── fuzz/                  HTTP fuzzer (mutation engine, wordlists)
├── bootstrap/             Frozen Python compiler for bootstrapping
├── playground/            Browser-based playground with WASM runtime
├── tests/                 Test suite (3,698+ tests)
├── benchmarks/            Performance benchmarks
├── docs/                  Documentation
│   ├── rfcs/              Language change proposals
│   ├── roadmap/           Version roadmaps and plans
│   └── SPEC.md            Language specification
├── examples/              Example programs (GPU, WASM, ...)
├── packaging/             Installers and build specs
│   ├── install.sh         Linux/macOS installer
│   ├── install.ps1        Windows installer
│   └── mapanare.spec      PyInstaller spec for binary builds

```

---

## Development

```bash
git clone https://github.com/Mapanare-Research/Mapanare.git
cd Mapanare
make install        # pip install -e ".[dev]"
make test           # pytest tests/ -v
make lint           # ruff, black, mypy
make fmt            # auto-format
make benchmark      # run benchmarks
```

Requires Python 3.11+.

---

## Roadmap

| Version | Theme | Status |
|---------|-------|--------|
| **v0.1.0** | Foundation — bootstrap compiler, dual backends, runtime, LSP, stdlib | Released |
| **v0.2.0** | Self-Hosting — LLVM codegen, C runtime, self-hosted compiler (5,800 lines .mn) | Released |
| **v0.3.0** | Depth Over Breadth — traits, modules, agent codegen, arena memory, 1,960+ tests | Released |
| **v0.4.0** | Ready for the World — FFI, C runtime hardening, diagnostics, scope cleanup | Released |
| **v0.5.0** | The Ecosystem — interpolation, linter, Python interop, playground, registry, docs | Released |
| **v0.6.0** | Compiler Infrastructure — MIR pipeline, bootstrap frozen | Released |
| **v0.7.0** | Self-Standing — self-hosting, observability, test runner, deployment | Released |
| **v0.8.0** | Native Parity — LLVM backend completeness, C runtime expansion | Released |
| **v1.0.0** | Stable — language spec frozen, backwards compatibility guarantees | Released |
| **v1.1.0** | AI Native — LLM drivers, embeddings, RAG as stdlib | Released |
| **v1.2.0** | Data & Storage — SQL drivers, Dato v1.0, YAML/TOML, filesystem | Released |
| **v1.3.0** | Web & Security — crawler, vulnerability scanner, fuzzer, HTTP toolkit | Released |
| **v2.0.0** | GPU & WASM — GPU compute (CUDA/Vulkan), WebAssembly backend, mobile targets | **Current** |

See the full [ROADMAP](docs/roadmap/ROADMAP.md) for details.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Community standards and project
processes live in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
[GOVERNANCE.md](GOVERNANCE.md), and [SECURITY.md](SECURITY.md). Language
changes require an [RFC](docs/rfcs/).

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Mapanare** — The language AI deserves.

[Report Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Request Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Spec](docs/SPEC.md) · [Changelog](CHANGELOG.md) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Made with care by [Juan Denis](https://juandenis.com)

</div>
