# Mapanare Roadmap

> **Mapanare** is an AI-native compiled programming language.
> Agents, signals, streams, and tensors are first-class primitives — not libraries.
>
> [mapanare.dev](https://mapanare.dev) · [GitHub](https://github.com/Mapanare-Research/Mapanare)

---

## Where We Are (v4.0.0 — Production Release)

**The compiler is production-quality.** Self-hosted compiler: 15,000+ lines of
`.mn` across 11 modules. Fixed-point verified (stage3 == stage4). 40/40 golden
tests, 4,845+ pytest tests. Seven independent reviewers gave 9.79/10 with
unanimous PASS and zero CRITICAL/HIGH issues.

**You can build real programs.** CLI tools, file processors, HTTP clients, GPU
programs. Install -> write -> compile -> run works end-to-end.

**Next:** v4.1.0 — ecosystem infrastructure (package registry, version manager, installers).

---

## What's Next

### v4.1.0 — Ecosystem Infrastructure (In Progress)

The compiler is done. Now make the ecosystem work like a real language toolchain.

| Phase | What | Status |
|-------|------|--------|
| **Phase 1** | Package registry persistence (PostgreSQL connection pool + retry), web login (GitHub OAuth + cookies), account dashboard, download page | **Done** |
| **Phase 2** | Install script `--version` flag, native compiler distribution in CI (`mnc` binaries alongside PyInstaller), cross-platform seed binaries | Planned |
| **Phase 3** | `mapanare-up` version manager (pyenv-style: `.mapanare-version`, shim-based dispatch, `install`/`list`/`default`/`use`/`update`) | Planned |
| **Phase 4** | CI release pipeline: native binary builds for Linux/macOS/Windows, SHA256 checksums, staged releases (beta/stable channels) | Planned |
| **Phase 5** | Blog tutorials (transpile Python, GPU compute), new doc pages (package manager, version manager), v4.0.0 docs audit | Planned |

### v4.2.0+ — Language Evolution & Adoption (Future)

**Auto-Generated FFI Bindings (the growth hack)**

Write performance-critical code in Mapanare (GPU kernels, data pipelines, tensor
math), compile to a shared library, and the compiler auto-generates typed
bindings for Python (`.pyi`), TypeScript (`.d.ts`), and Go — so existing
codebases can import Mapanare libraries with zero friction. This flips the
adoption model: you don't rewrite your stack, you accelerate the hot path.

```bash
mapanare build mylib.mn --lib --bindings   # .so + Python .pyi + TypeScript .d.ts + Go wrappers
```

**Compile-Time Tensor Shape Checking**

Connect `Tensor<Float>[shape]` to the `gpu_tensor_*` builtins with static shape
verification in the semantic analyzer. Combined with the `const` keyword,
tensor dimensions would be evaluated at compile time — multiplying a `[100, 50]`
by a `[20, 50]` is a compile error, not a GPU crash. This would make Mapanare
one of the safest languages for neural network math.

| Feature | Description |
|---------|-------------|
| **FFI binding generation** | `--bindings` flag on `mapanare build --lib`: auto-generate `.pyi`, `.d.ts`, Go wrappers from exported functions |
| **Compile-time tensor shapes** | Semantic analyzer validates `Tensor<Float>[M, K] @ Tensor<Float>[K, N]` — shape mismatch is a compile error |
| `const` keyword | Compile-time constants in grammar and semantic checker, enables static tensor dimensions |
| `@gpu` decorator codegen | Wire decorator recognition → kernel extraction → PTX/SPIR-V emission |
| Drop glue for struct returns | Fix the 8-cycle carry-forward: free locals when function returns a struct |
| Typed pointers cleanup | Replace `i64*`, `void ()*` in self-hosted emitter with opaque `ptr` |
| Async/await | First-class async functions with cooperative scheduling |
| LSP improvements | Better autocomplete, hover docs, find-all-references |

---

## Eras

The roadmap is organized into 5 major eras. Each era folder contains a README
with goals, features, and lessons learned, plus per-version PLAN.md and
SUMMARY.md files.

| Era | Theme | Versions | Key Milestone |
|-----|-------|----------|---------------|
| [**v0**](v0/) | Foundation & Bootstrap | v0.1.0 — v0.9.0 | Self-hosted compiler boots, MIR pipeline, native stdlib |
| [**v1**](v1/) | Stability & Production | v1.0.0 — v1.3.0 | Language frozen (SPEC 1.0), AI/data/web stdlib |
| [**v2**](v2/) | Platform Expansion | v2.0.0 — v2.2.0 | GPU, WASM, mobile, self-compilation progress |
| [**v3**](v3/) | Syntax & Self-Hosted Maturity | v3.0.0 — v3.47.0 | Radical syntax reform, fixed-point, transpilers, production gate |
| [**v4**](v4/) | Production & Ecosystem | v4.0.0+ | Build real programs, package registry, version manager, installers |

---

## Release History

### v0 — Foundation & Bootstrap

| Version | Theme | Highlights |
|---------|-------|------------|
| **v0.1.0** | Foundation | Bootstrap compiler, Lark parser, semantic checker, Python + LLVM emitters, runtime, LSP, 1,400+ tests |
| **v0.2.0** | Self-Hosting | LLVM string/list codegen, C runtime, self-hosted compiler (5,800+ lines .mn) |
| **v0.3.0** | Depth Over Breadth | Traits, module resolution, LLVM agent codegen, arena memory, TypeKind enum, 1,960+ tests |
| **v0.3.1** | Release Polish | Dynamic versioning from VERSION file |
| **v0.4.0** | Ready for the World | Scope cleanup, C runtime hardening, structured diagnostics, C FFI, self-hosted verification |
| **v0.5.0** | The Ecosystem | String interpolation, linter, Python interop, WASM playground, package registry, 2,200+ tests |
| **v0.6.0** | Compiler Infrastructure | MIR pipeline (SSA IR, lowering, optimizer), bootstrap frozen, 2,500+ tests |
| **v0.7.0** | Self-Standing | Self-hosted MIR lowering, test runner, agent observability, DWARF debug info, 2,983 tests |
| **v0.8.0** | Native Parity | LLVM backend parity, complete string methods, C runtime expansion (TCP, TLS, file I/O), 3,020 tests |
| **v0.9.0** | Connected | Native stdlib in .mn (JSON, CSV, HTTP, crypto, regex), cross-module LLVM, 3,400+ tests |

### v1 — Stability & Production

| Version | Theme | Highlights |
|---------|-------|------------|
| **v1.0.0** | Stable | Language freeze (SPEC 1.0 Final), emitter hardening, formal memory model, 15/15 golden, 3,600+ tests |
| **v1.0.1–v1.0.11** | Patch Series | 11 patches addressing 34 code review issues: type soundness, memory, drop glue, self-hosted fixes, ASan/TSan clean |
| **v1.1.0** | AI Native | LLM drivers (OpenAI, Anthropic, local), embeddings, RAG pipeline |
| **v1.2.0** | Data & Storage | Dato engine, database drivers (SQLite, PostgreSQL, Redis, KV), TOML/YAML, filesystem stdlib |
| **v1.3.0** | Web & Security | Web crawler, vulnerability scanner, HTTP fuzzer, HTTP server toolkit |

### v2 — Platform Expansion

| Version | Theme | Highlights |
|---------|-------|------------|
| **v2.0.0** | Beyond the Machine | WASM backend, GPU compute (CUDA + Vulkan), mobile targets (iOS, Android), Python deprecated, 4,465+ tests |
| **v2.0.1** | Trust Restoration | Fix 40 review issues: WASM correctness, GPU security, toolchain honesty |
| **v2.1.0** | Self-Compilation | Stage2 IR validates, 8 root causes fixed, mnc-stage2 reaches lowerer |
| **v2.2.0** | Stage2 Debugging | Valgrind crash diagnostics, struct field mapping, PHI type recovery, mnc-stage2 binary (3.8 MB) |

### v3 — Syntax & Self-Hosted Maturity

| Version | Theme | Highlights |
|---------|-------|------------|
| **v3.0.0** | La Culebra Se Muerde La Cola | C emit backend, bilingual keywords, indentation syntax, tipo/modo, @Agent |
| **v3.0.1–v3.0.3** | Bootstrap Fixes | mnc-stage1 runs, 25/25 golden, PHI type recovery |
| **v3.1.0–v3.2.0** | Native IO + Seed | File I/O, string escapes, seed binary updated |
| **v3.3.0** | **Fixed Point** | stage3 == stage4, two-stage bootstrap from seed, no Python required |
| **v3.4.0–v3.7.0** | Language Completeness | Module imports, WASM stackifier, type system, cross-module imports |
| **v3.8.0–v3.9.1** | Generics + Impl | Monomorphization, trait dispatch, generic impl blocks, 31/31 golden |
| **v3.10.0–v3.23.0** | Semantic Maturity | Error messages, memory safety, concurrency fixes, `any` type, optimizer convergence |
| **v3.24.0–v3.31.0** | Multi-Language Transpilation | Python, PHP, TypeScript, Go transpilers + shared framework |
| **v3.32.0–v3.36.0** | Review Hardening | Code review fixes, dead code removal, performance optimization |
| **v3.37.0–v3.47.0** | Production Gate | IO foundation, network, agents, examples, package manager, GPU — all prerequisites for v4.0.0 |

### v4 — Production & Ecosystem

| Version | Theme | Highlights |
|---------|-------|------------|
| **v4.0.0** | Mapanare | Build real programs. 15,000+ lines self-hosted, 40/40 golden, 4,845+ tests, 9.79/10 review |
| **v4.0.0** | Bug fixes | MIR constant propagation fix (loop back-edges), transpiler return type inference, `cmd_build` obj path collision |
| **v4.1.0** | Ecosystem (in progress) | Package registry persistence, web login, dashboard, download page, version manager, native CI binaries |

---

## What Works Today

- **Full compiler pipeline** — Lexer, parser, semantic checker, MIR lowering, optimizer (O0-O3), code emitter
- **Three compilation targets** — LLVM IR (production), WebAssembly (WAT/WASM), Python (deprecated)
- **Self-hosted compiler** — 15,000+ lines of .mn across 11 modules, fixed-point verified
- **GPU compute** — CUDA + Vulkan via dlopen, @gpu/@cuda/@vulkan annotations
- **WebAssembly** — MIR-to-WAT, WASI support, JS bridge, wasm-ld multi-module linking
- **AI stdlib** — LLM drivers, embeddings, RAG pipelines
- **Data** — Dato DataFrames, SQLite/PostgreSQL/Redis drivers, TOML/YAML encoding
- **Web** — HTTP server toolkit, web crawler, vulnerability scanner, HTTP fuzzer
- **Multi-language transpilation** — Python, PHP, TypeScript, Go -> Mapanare (29-68x speedup over Python)
- **Package manager** — `mapanare install` with dependency resolution, registry at mapanare.dev/packages
- **Package registry** — PostgreSQL-backed with GitHub OAuth login, web dashboard, download API
- **Developer tools** — CLI, LSP, VS Code extension, formatter, linter, test runner, doc generator
- **Website** — mapanare.dev with docs, benchmarks, blog, download page, package registry
- **Cross-compilation** — 9 targets (Linux, macOS, Windows, WASM, iOS, Android)

### Backend Feature Status

| Feature | LLVM | WASM | Python (deprecated) |
|---------|:----:|:----:|:-------------------:|
| Functions, closures, lambdas | Yes | Yes | Yes |
| Structs, enums, pattern matching | Yes | Yes | Yes |
| Control flow (if/else, for, while) | Yes | Yes | Yes |
| Type inference, generics | Yes | Yes | Yes |
| Result/Option | Yes | Yes | Yes |
| Builtins (print, str, int, float, len) | Yes | Yes | Yes |
| Lists, Maps/Dicts | Yes | Yes | Yes |
| String methods | Yes | Yes | Yes |
| Traits | Yes | Yes | Yes |
| Module imports | Yes | Yes | Yes |
| Agents, Signals, Streams, Pipes | Yes | Yes | Yes |
| GPU compute | Yes | No | No |
| Standard library (25+ modules) | Yes | Partial | Partial |

### Performance (LLVM native vs Python)

| Workload | Speedup |
|----------|---------|
| Fibonacci (recursive) | **26-41x faster** |
| Stream pipeline (1M items) | **62.8x faster** |
| Matrix multiply (100x100) | **22.9x faster** |
| Python transpile: Collatz (1M) | **68x faster** |
| Python transpile: Primes (500K) | **29x faster** |
| Agent message passing (10K) | On par |

---

## Test Growth

| Era | Tests | Key Quality Metric |
|-----|-------|--------------------|
| v0.1.0 | 1,400+ | Bootstrap works |
| v0.6.0 | 2,500+ | MIR pipeline validated |
| v0.9.0 | 3,400+ | Native stdlib compiles |
| v1.0.0 | 3,600+ | ASan/TSan clean (52/52) |
| v2.0.0 | 4,465+ | WASM + GPU + mobile CI |
| v4.0.0 | 4,845+ | 40/40 golden, 9.79/10 review |

---

## Directory Structure

```
docs/roadmap/
  ROADMAP.md          <- This file (index)
  v0/                 <- Foundation & Bootstrap (v0.1.0 - v0.9.0)
    README.md         <- Era summary: goals, features, lessons learned
    v0.1.0/PLAN.md    <- Detailed version plan
    v0.1.0/SUMMARY.md <- Post-release summary
    ...
  v1/                 <- Stability & Production (v1.0.0 - v1.3.0)
    README.md
    v1.0.0/PLAN.md
    ...
  v2/                 <- Platform Expansion (v2.0.0 - v2.2.0)
    README.md
    v2.0.0/PLAN.md
    ...
  v3/                 <- Syntax & Self-Hosted Maturity (v3.0.0 - v3.47.0)
    README.md
    v3.0.0/PLAN.md
    ...
  v4/                 <- Production & Ecosystem (v4.0.0+)
    README.md
    v4.0.0/PLAN.md
    v4.1.0/PLAN.md
```

Each version folder contains:
- **PLAN.md** — execution plan (phases, tasks, exit criteria)
- **SUMMARY.md** — post-release retrospective (where available)
- **PROMPT.md / prompt.md** — context prompt used during development (where available)
