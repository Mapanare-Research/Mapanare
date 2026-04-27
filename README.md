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
[![Version](https://img.shields.io/badge/version-5.8.6-blue.svg?style=flat-square)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-5800+_passing-brightgreen.svg?style=flat-square)]()
[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
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
# Windows (PowerShell)
irm https://mapanare.dev/install.ps1 | iex
```

Or download binaries from [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

---

## Hello World

```mn
fn main() {
    print("hello from mapanare")
}
```

```bash
mapanare run hello.mn        # compile + run
mapanare build hello.mn      # produce a native binary
```

---

## Write Python, Compile Native

Take your existing Python scripts and compile them to native binaries:

```bash
mapanare build your_script.py -o your_script
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
agent Counter {
    state count: Int = 0
    on increment { count = count + 1 }
    on get_count -> Int { return count }
}

// Signals — reactive state
let temperature = signal(72.0)
let alert = computed(() => temperature.get() > 100.0)

// Streams — composable data pipelines
let results = data_stream
    |> filter((x) => x > 0)
    |> map((x) => x * 2)
    |> collect()

// Pattern matching
match response {
    Ok(data) => process(data),
    Err(e) => print(e)
}

// AI stdlib
import ai::llm
let answer = ask(ollama("llama3.2"), "What is Mapanare?")
```

Full language reference, tutorials, and cookbook at [mapanare.dev/docs](https://mapanare.dev/docs).

### Native compiler — what `mnc-stage1` ships

The self-hosted compiler runs the full v5.7.0 corpus (66/66 native goldens):

- **Tensors** — literals, multi-dim indexing, NumPy-style broadcasting, slicing, reductions (sum / mean / max / min / argmax / argmin).
- **Async / await / `block_on`** — real LLVM coroutines (`presplitcoroutine` + `@llvm.coro.id/begin/save/suspend/end`) with scheduler-driven suspension.
- **Closure-typed parameters** — `fn apply(f: fn(Int) -> Int, x: Int)` lowered through indirect-call SSA.
- **Or-pattern matching with guards** — `Plus | Minus if cond => body` over enum variants and built-in constructors (`None` / `Some` / `Ok` / `Err`).
- **Drop-glue ownership tracking** — string / list / boxed / tensor lifetimes tracked through return paths and loop iterations; valgrind / ASan / LSan / TSan all clean on the corpus.

Self-host 3-stage fixed-point: NEAR (4-line VERSION-metadata diff over a 217k-line stage2.ll).

---

## Benchmarks

Geometric mean across 6 cross-language benchmarks (median of 10 runs):

| | vs Python | vs Go | vs Rust | vs C (gcc) |
|---|---:|---:|---:|---:|
| **Mapanare** | **168x faster** | 0.85x (faster) | 1.17x | 0.96x |

The self-hosted compiler compiles itself (3-stage fixed point reached
at v4.134.0; temporarily regressed at v5.1.2 from In.1 inliner
re-enable; restored to NEAR at v5.6.11, preserved through v5.8.0 —
4-line VERSION-metadata diff over a 217k-line stage2.ll). 5,720+
tests passing, zero flaky across 30 sequential runs.

[Full benchmark report](benchmarks/FINAL_REPORT_v4.153.md)

---

## Build from Source

```bash
git clone https://github.com/Mapanare-Research/Mapanare.git
cd Mapanare
bash scripts/build_from_seed.sh    # no Python needed
./mnc hello.mn                     # outputs LLVM IR
```

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
