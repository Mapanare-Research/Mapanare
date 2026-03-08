# Mapanare

A compiled programming language where agents, signals, streams, and tensors are first-class primitives — not libraries.

Mapanare compiles to Python (transpiler) and native binaries (LLVM), with a self-hosted compiler in progress.

## Installation

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Mapanare-Research/Mapanare/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/Mapanare-Research/Mapanare/main/install.ps1 | iex
```

### Manual Download

Download the latest binary from the [Releases page](https://github.com/Mapanare-Research/Mapanare/releases).

| Platform | Archive |
|----------|---------|
| Linux (x64) | `mapa-linux-x64.tar.gz` |
| macOS (Apple Silicon) | `mapa-mac-arm64.tar.gz` |
| Windows (x64) | `mapa-win-x64.zip` |

Extract and add the `mapa` binary to your PATH.

```bash
mapa --version
```

## The Language

### Agents

Concurrent actors with typed channels, lifecycle management, and supervision.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

fn main() {
    let greeter = spawn Greeter()
    greeter.name <- "World"
    let result = sync greeter.greeting
    print(result)
}
```

### Signals

Reactive state with automatic dependency tracking and change propagation.

```mn
let mut count = signal(0)
let doubled = computed { count * 2 }

count.set(5)
print(doubled)  // 10

batch {
    count.set(10)
    // notifications coalesced until batch ends
}
```

### Streams

Async pipelines with backpressure, fusion, and composable operators.

```mn
let data = stream([1, 2, 3, 4, 5])
let result = data
    |> filter(fn(x) { x > 2 })
    |> map(fn(x) { x * 10 })
    |> fold(0, fn(acc, x) { acc + x })
```

Adjacent `map`/`filter` operators fuse into a single pass automatically.

### Pipes

Declarative multi-agent composition with type-checked data flow.

```mn
pipe ClassifyText {
    Tokenizer |> Classifier
}
```

### Tensors

N-dimensional arrays with compile-time shape validation.

```mn
let a: Tensor<Float>[3, 3] = identity(3)
let b: Tensor<Float>[3, 4] = zeros(3, 4)
let c = a @ b  // shape [3, 4] — inner dimensions checked at compile time
```

### Type System

Static typing with inference, generics, pattern matching, and error propagation.

```mn
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}

let value = divide(10.0, 3.0)?
```

### No OOP

No classes, no inheritance, no virtual methods. Structs, enums, and pattern matching instead.

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

## CLI

```
mapa run <file>           Compile and run
mapa build <file>         Compile to native binary via LLVM
mapa jit <file>           JIT-compile and run natively
mapa check <file>         Type-check only
mapa compile <file>       Transpile to Python
mapa emit-llvm <file>     Emit LLVM IR
mapa fmt <file>           Format source code
mapa init [path]          Initialize a new project
mapa install <pkg>        Install a package (git-based)
mapa targets              List supported compilation targets
```

Options: `-O0` to `-O3` optimization levels, `-o <path>` output file, `--target <triple>` cross-compilation target.

## Compiler Architecture

```
.mn source → Lexer → Parser → AST → Semantic Analysis → Optimizer → Emit
                                                                      ↓
                                                               Python | LLVM IR
                                                                      ↓
                                                       Interpreter | Native Binary
```

- **Lexer**: Lark-based tokenizer (18 keywords, 29 operators)
- **Parser**: LALR with precedence climbing
- **Semantic**: Type checking, scope analysis, builtins registry
- **Optimizer**: Constant folding, dead code elimination, agent inlining, stream fusion (`-O0` to `-O3`)
- **Emit Python**: Agents map to asyncio, signals to reactive containers, streams to async generators
- **Emit LLVM**: Full IR generation via llvmlite with cross-compilation targets

## Runtime

The runtime provides native implementations of the language primitives:

- **Agents**: Lifecycle management, typed channels, supervision (restart/stop policies), backpressure, metrics
- **Signals**: Dependency graph with automatic recomputation, batched updates, change streams
- **Streams**: Async iterables with fusion, hot/cold semantics, backpressure strategies (buffer, drop, error)
- **Result/Option**: `Ok`/`Err`/`Some`/`None` with `?` operator support
- **Native C Runtime**: Lock-free SPSC ring buffers, per-core thread pool, atomic backpressure counters

## Standard Library

| Module | Provides |
|--------|----------|
| `io` | File I/O agents, read/write helpers |
| `http` | HTTP client/server agents, get/post |
| `time` | Timers, intervals, debounce, throttle, stopwatch |
| `math` | Constants, trig, statistics, linear algebra helpers |
| `text` | Case conversion, search, split/join, slug, padding |
| `log` | Structured logging with agent context, JSON/text output |
| `pkg` | Project manifests, git-based package install, lock files |

## GPU & Tensors

- Device detection: CUDA, Metal, Vulkan
- `@gpu` / `@cpu` annotations for kernel dispatch
- Model loading: `.mnw` (native format), ONNX, safetensors, HuggingFace

## Editor Support

### VS Code

Extension in `editors/vscode/` with:

- Syntax highlighting for `.mn` files
- Code snippets (agent, pipe, fn, signal, stream)
- LSP integration: hover, go-to-definition, find-references, diagnostics, autocomplete

Install the LSP server: `mapanare-lsp`

## Self-Hosted Compiler

The compiler is being rewritten in Mapanare itself (`mapa/self/`):

- `lexer.mn` — Tokenizer
- `parser.mn` — Recursive descent parser
- `ast.mn` — 31 AST definitions
- `semantic.mn` — Type checker
- `emit_llvm.mn` — LLVM IR emitter

Bootstrap strategy: Python compiler (Stage 0) compiles self-hosted `.mn` sources (Stage 1), which must reproduce identical output (Stage 2 fixed-point verification).

## Project Structure

```
mapanare/
├── mapa/                  Compiler (lexer, parser, semantic, emit, optimizer, jit)
│   ├── self/              Self-hosted .mn compiler sources
│   └── lsp/               Language Server Protocol
├── runtime/               Runtime (agents, signals, streams, result types)
│   └── native/            Native C runtime (thread pool, ring buffers)
├── stdlib/                Standard library (io, http, time, math, text, log, pkg)
├── bootstrap/             Frozen Python compiler for bootstrapping
├── editors/vscode/        VS Code extension
├── tests/                 Test suite (~60 test files)
├── benchmarks/            Performance benchmarks
├── docs/                  Documentation
├── rfcs/                  Language change proposals
├── SPEC.md                Language specification
├── ROADMAP.md             Development roadmap
├── install.sh             Linux/macOS installer
├── install.ps1            Windows installer
└── mapa.spec              PyInstaller spec for binary builds
```

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Language changes require an [RFC](rfcs/).

## License

MIT
