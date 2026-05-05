<div align="center">

<img width="1280" height="640" alt="mapanare-repo" src="https://github.com/user-attachments/assets/176d26e7-0c42-49ef-99d2-b8192cd75e53" />

# Mapanare

**/mah-pah-NAH-reh/**

**The AI-native programming language.**

*Agents. Signals. Streams. Tensors. First-class, not frameworks.*

Compiles to native binaries via LLVM and WebAssembly.
**~168x faster than Python. On par with Rust and C.**

English | [Español](docs/README.es.md) | [中文版](docs/README.zh-CN.md) | [Português](docs/README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Native_Backend-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-Backend-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)
![Platform](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.44.1-blue.svg?style=flat-square)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-5800+_passing-brightgreen.svg?style=flat-square)]()
[![Goldens](https://img.shields.io/badge/goldens-96%2F96-brightgreen.svg?style=flat-square)]()
[![CI](https://github.com/Mapanare-Research/Mapanare/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/Mapanare-Research/Mapanare/actions/workflows/ci.yml?query=branch%3Adev)
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Website**](https://mapanare.dev) · [**Docs**](https://mapanare.dev/docs) · [**Download**](https://mapanare.dev/download) · [**Discord**](https://discord.gg/5hpGBm3WXf)

</div>

---

## Install

```bash
curl -fsSL https://mapanare.dev/install | bash
```

```powershell
# Windows (PowerShell) - includes a bundled Windows SDK by default,
# so `mnc run` and `mnc build` work with no separate install.
irm https://mapanare.dev/install.ps1 | iex

# Want the minimal ZIP and bring your own clang/gcc? Set either env var first:
$env:MAPANARE_NO_BUNDLED_TOOLCHAIN = "1"; irm https://mapanare.dev/install.ps1 | iex
# Legacy alias also works:
$env:MAPANARE_NO_BUNDLED_LLVM = "1"; irm https://mapanare.dev/install.ps1 | iex
```

Or download binaries from [Releases](https://github.com/Mapanare-Research/Mapanare/releases). Use the Windows SDK ZIP for clean-machine native builds or the minimal ZIP when you already have a compiler. **All v5.33.0+ release tarballs and Windows ZIPs ship a real native `mnc` binary** (Linux x86_64 + macOS arm64 added in v5.33.0; Windows x86_64 since v5.32.0) — `mnc --version`, `mnc run`, and `mnc build` no longer dispatch through the Python bootstrap. The Python `mapanare`/`mnc` console-script remains as the bootstrap path for clean clones and pip-installs without a release bundle. See [`docs/THIRD-PARTY-LICENSES.md`](docs/THIRD-PARTY-LICENSES.md) for bundled SDK licenses.

> **macOS users:** if you downloaded the tarball over the network and Gatekeeper quarantines `mnc` on first run, clear the attribute with `xattr -d com.apple.quarantine ./mapanare/mnc`. Proper Developer ID notarization is tracked for v5.34.0+; v5.33.0 ships ad-hoc-signed binaries.

### Quick start with Docker

[![mapanare-builder](https://img.shields.io/badge/ghcr.io-mapanare--builder-2496ED?style=flat-square&logo=docker&logoColor=white)](https://github.com/mapanare-research/Mapanare/pkgs/container/mapanare-builder)
[![mapanare-runtime](https://img.shields.io/badge/ghcr.io-mapanare--runtime-2496ED?style=flat-square&logo=docker&logoColor=white)](https://github.com/mapanare-research/Mapanare/pkgs/container/mapanare-runtime)

No host toolchain? Compile and run inside the official images:

```bash
mnc init demo --docker && cd demo
docker build -t demo .
docker run --rm demo
```

The multi-stage Dockerfile uses
`ghcr.io/mapanare-research/mapanare-builder` for the build and
`mapanare-runtime` for the final image (~115 MB). See
[`docs/guides/docker.md`](docs/guides/docker.md).

---

## Hello World

```bash
mnc init hello && cd hello
mnc run main.mn
```

`mnc init` scaffolds a runnable project (terse `main.mn`,
`mapanare.toml`, `.gitignore`, `README.md`). For a one-liner:

```mn
fn main():
    print("hello from mapanare")
```

```bash
mnc run hello.mn        # compile + run
mnc build hello.mn      # produce a native binary
mnc check hello.mn      # type-check, no codegen
mnc lsp                 # start the language server (stdio)
```

(`mapanare` is also installed as an alias for `mnc`.)

Source canonicalization: [`docs/guides/formatter.md`](docs/guides/formatter.md).
New project scaffolding: [`docs/guides/init.md`](docs/guides/init.md).
VS Code: [`docs/guides/lsp.md`](docs/guides/lsp.md).
Docker: [`docs/guides/docker.md`](docs/guides/docker.md).

VS Code users: install
[the official extension](https://github.com/Mapanare-Research/mapanare-vscode)
(`mapanare-research.mapanare`). Neovim/Helix setup lives in
[`docs/guides/lsp.md`](docs/guides/lsp.md).

---

## Write Python, Compile Native

Take your existing Python scripts and compile them to native binaries:

```bash
mnc build your_script.py -o your_script
./your_script   # 33-239x faster
```

| Script | Python 3 | Mapanare (native) | Speedup |
|---|---:|---:|---:|
| numerical_compute (10M iterations) | 2,557 ms | 10.7 ms | **239x** |
| collatz_explorer (5M range) | 30,636 ms | 446.8 ms | **69x** |
| prime_sieve (2M range) | 3,832 ms | 108.8 ms | **35x** |
| fibonacci(40) | 8,220 ms | 193.7 ms | **42x** |
| primes (500K) | 995 ms | 30.6 ms | **33x** |

[Python to Native guide](https://mapanare.dev/docs/guides/python-to-native)

---

## Language Features

```mn
// Agents — first-class concurrent actors
agent Counter:
    state count: Int = 0
    on increment: count = count + 1
    on get_count -> Int = count

// Signals — reactive state
let temperature = signal(72.0)
let alert = computed(|| temperature.get() > 100.0)

// Streams — composable data pipelines
let results = data_stream
    |> filter(|x| x > 0)
    |> map(|x| x * 2)
    |> collect()

// Comprehensions + implicit-return one-liner
fn double(x: Int) -> Int = x * 2
let doubled: List<Int> = [double(x) for x in xs if x > 0]
let lookup: Map<Int, Int> = #{ k: k * k for k in 0..10 }

// Pattern matching
match response:
    Ok(data) => process(data),
    Err(e) => print(e)

// AI stdlib
import ai::llm
let answer = ask(ollama("llama3.2"), "What is Mapanare?")
```

Full language reference, tutorials, and cookbook at [mapanare.dev/docs](https://mapanare.dev/docs).

### Native compiler — what `mnc-stage1` ships

The self-hosted compiler runs the full corpus (96/96 native goldens at v5.27.0):

- **Tensors** — literals, multi-dim indexing, NumPy-style broadcasting, slicing, reductions (sum / mean / max / min / argmax / argmin).
- **Async / await / `block_on`** — real LLVM coroutines (`presplitcoroutine` + `@llvm.coro.id/begin/save/suspend/end`) with scheduler-driven suspension.
- **Closure-typed parameters** — `fn apply(f: fn(Int) -> Int, x: Int)` lowered through indirect-call SSA.
- **Or-pattern matching with guards** — `Plus | Minus if cond => body` over enum variants and built-in constructors (`None` / `Some` / `Ok` / `Err`).
- **Drop-glue ownership tracking** — string / list / boxed / tensor lifetimes tracked through return paths and loop iterations; valgrind / ASan / LSan / TSan all clean on the corpus.

Self-host 3-stage fixed-point: STRICT (stage2.ll == stage3.ll byte-identical at 241k lines; restored v5.9.0 — DX.2 closed the v4.140.0–v5.8.x VERSION-metadata diff at the source; held through v5.17.0's mechanical brace → colon rewrite, v5.20.0's struct ergonomics, v5.21.0's chained comparisons, v5.23.0's CI recovery, v5.23.2's bootstrap brace-deprecation mirror, v5.24.0's Hy.\* hygiene gates, v5.25.0's Pv.\* prevention infrastructure, v5.26.0's Mb.7 codegen fix + Mb.9 Win64 ABI, v5.26.1's Eu.\* enum-payload closures, and v5.27.0's Mc.\* parity arc closeout — longest streak in project history at 23 consecutive releases).

---

## Benchmarks

Geometric mean across 6 cross-language benchmarks (median of 10 runs):

| | vs Python | vs Go | vs Rust | vs C (gcc) |
|---|---:|---:|---:|---:|
| **Mapanare** | **168x faster** | 0.85x (faster) | 1.17x | 0.96x |

The self-hosted compiler compiles itself to a strict 3-stage fixed
point (stage2.ll == stage3.ll byte-identical at 241k lines; strict
since v5.9.0, held through 23 consecutive releases — see "Native
compiler" above). 5,800+ tests passing, zero flaky across 40+
sequential runs.

[Full benchmark report](benchmarks/FINAL_REPORT.md)

---

## Build from Source

```bash
git clone https://github.com/Mapanare-Research/Mapanare.git
cd Mapanare
bash scripts/build_from_seed.sh    # no Python needed
./mnc hello.mn                     # compile and run (default)
./mnc emit-llvm hello.mn           # compile to LLVM IR
./mnc fmt mapanare/self/           # canonicalize whitespace (v5.13.0+)
```

> **v5.9.1 BREAKING:** `mnc <file.mn>` now compiles and runs the
> program. The IR-emission path moved to `mnc emit-llvm <file.mn>`
> (`-o <path>` writes to file). CI scripts that piped
> `mnc file.mn > out.ll` should switch to
> `mnc emit-llvm file.mn -o out.ll`.

For development (requires Python 3.11+):

```bash
pip install -e ".[dev]"
make test
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Language changes require an [RFC](docs/rfcs/).

## License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

**Mapanare** — The language AI deserves.

[Report Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Request Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Made with care by [Juan Denis](https://juandenis.com)

</div>
