# Getting Started with Mapanare

> A practical "from zero to a native binary" walk, for developers
> already familiar with compiled languages. For a longer tutorial with
> agents, signals, streams, and pipelines, see
> [`docs/getting-started.md`](../getting-started.md).

This guide gets you:

1. Mapanare installed from source
2. A `hello.mn` compiled through the **Python bootstrap** into a native binary
3. Same `hello.mn` compiled through the **self-hosted compiler** (`mnc-stage1`)
4. Pointers to what to read next

All commands are tested on WSL2 Ubuntu 24.04. Linux and macOS should
work with the same commands. Windows users: use PowerShell for
installation, WSL for the build pipeline.

---

## 1. Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | 3.11+ | Runs the bootstrap compiler and the dev toolchain |
| `clang` | 15+ | Links LLVM IR into a native binary |
| `llvm-as`, `opt`, `llc` | 18.x | IR assembly, optimisation, machine code |
| `make` | any | Build runtime library |
| `git` | any | Clone the repo |

Ubuntu / WSL install:

```bash
sudo apt install -y python3 python3-venv build-essential \
                     clang-18 llvm-18 make git
```

macOS install (Homebrew):

```bash
brew install python@3.11 llvm@18 make git
```

Verify LLVM 18 is first on the path:

```bash
clang --version        # should print "clang version 18.x"
llvm-as --version      # should print "LLVM version 18.x"
```

### Native-mode prerequisites (LLVM backend)

Running `mapanare build` or the self-hosted compiler requires:

| Tool | Version | Install |
|---|---|---|
| LLVM | 17+ | `apt install llvm-17` / `brew install llvm` / Windows: WSL only |
| clang | matches LLVM | ships with LLVM |
| `opt`, `llc`, `llvm-as`, `lli` | matches LLVM | ships with LLVM |
| `clang` on PATH | — | ensure `/usr/lib/llvm-17/bin` is on PATH |
| `valgrind` (optional) | 3.19+ | for memory debugging |
| Python | 3.11+ | for bootstrap only |

**Windows users**: Native mode requires WSL2. Python bootstrap (which
transpiles to C or Python-side LLVM emission) works natively on
Windows but cannot self-host.

**Stack limit for `mnc-stage2`**: compiling `mapanare/self/mnc_all.mn`
through the stage2 binary requires a 64MB stack (v4.140.0 Cb.3). The
fixed-point verification script raises the limit automatically with
`ulimit -s 65536` at `scripts/verify_fixed_point.sh:58`. If you run
`mnc-stage2` directly on `mnc_all.mn`, raise the stack limit first or
you will see SIGSEGV (exit 139) with empty output. A lower limit
crashes before reaching the emission phase.

---

## 2. Clone and Install

```bash
git clone https://github.com/Mapanare-Research/Mapanare.git
cd Mapanare
make install           # pip install -e ".[dev]"
```

Verify the bootstrap compiler is on the path:

```bash
mapanare --version     # prints the VERSION file
```

Build the native C runtime:

```bash
make -C runtime/native
ls runtime/native/libmapanare_rt.a    # static library used for linking
```

---

## 3. Your First Program

Create `hello.mn`:

```mn
fn main() {
    print("Hello, Mapanare!")
}
```

Run it through the Python bootstrap (simplest path):

```bash
mapanare run hello.mn
# → Hello, Mapanare!
```

`mapanare run` parses, type-checks, lowers, optimises, emits LLVM IR,
invokes `clang` to produce a binary, and runs the binary — in one step.

---

## 4. Explicit Pipeline — Python Bootstrap

To see each stage, run them manually. This is the same pipeline the
async demos and golden tests use.

```bash
# Emit LLVM IR
python3 -m mapanare emit-llvm hello.mn -o /tmp/hello.ll

# Inspect the IR if curious
head -30 /tmp/hello.ll

# Optional optimisation pass
llvm-as /tmp/hello.ll -o /tmp/hello.bc
opt -O2 /tmp/hello.bc -o /tmp/hello_opt.bc
llc -filetype=obj /tmp/hello_opt.bc -o /tmp/hello.o

# Link against the native runtime
clang /tmp/hello.o \
      -L runtime/native -lmapanare_rt \
      -lpthread -lm -ldl \
      -o /tmp/hello

# Run
/tmp/hello
# → Hello, Mapanare!
```

For an `-O2` binary in one clang invocation:

```bash
clang -O2 /tmp/hello.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/hello
```

---

## 5. Explicit Pipeline — Self-Hosted Compiler

The self-hosted compiler (`mnc-stage1`) is written in Mapanare itself.
The bootstrap compiler builds it from the self-hosted sources in
`mapanare/self/`.

```bash
# Build mnc-stage1 from the self-hosted sources
python scripts/build_stage1.py
ls mapanare/self/mnc-stage1       # the self-hosted compiler binary

# Compile hello.mn with mnc-stage1
./mapanare/self/mnc-stage1 hello.mn > /tmp/hello_selfhosted.ll

# Link and run
clang /tmp/hello_selfhosted.ll \
      -L runtime/native -lmapanare_rt \
      -lpthread -lm -ldl \
      -o /tmp/hello_selfhosted
/tmp/hello_selfhosted
# → Hello, Mapanare!
```

The golden test suite validates the self-hosted compiler end-to-end:

```bash
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 --run
```

As of **v5.7.0** the self-hosted compiler passes **66/66** golden
tests through `test_native.py` — first time in project history. A
3-stage fixed point was first reached at v4.134.0; the In.1 inliner
re-enable at v5.1.2 temporarily regressed it (restoration tracked at
v5.3.2). The corpus is now at full parity with the Python bootstrap
for the test suite that defines "self-hosting." Remaining work is
v6.0 borrow-checker scope (Rt.04 multi-level alias analysis).

### What the self-hosted compiler doesn't do yet

| Feature | Status | Use this path instead |
|---|---|---|
| `async`/`await`/`block_on` | docket Sh.4 | Python bootstrap |
| Tensor primitives | docket Sh.6 | Python bootstrap (see SPEC §3.11) |
| `const` (partial — parser recognition restored v4.126.0, semantic gaps remain in `mnc-stage1`) | docket Sh.5 | Python bootstrap or module-level `let` |
| Closure-typed function parameters | docket Sh.7 | Python bootstrap; use concrete fn types |

See `docs/known_issues.md` for the full list of user-facing open
items and workarounds.

---

## 6. The Alternative Entry Point: Build From Seed

If you don't have Python, you can still bootstrap the compiler:

```bash
bash scripts/build_from_seed.sh
./mnc hello.mn       # compile a .mn file — LLVM IR on stdout
```

The seed binary is checked in and bootstraps the full self-hosted
compiler with only `gcc`/`clang` and `llvm` available. Python remains
required for the dev toolchain (tests, linters, benchmarks, the Python
transpiler).

---

## 7. Running the Tests

```bash
make test                             # full pytest suite
pytest tests/llvm/ -v -n auto         # just the LLVM-emitter tests
pytest tests/bootstrap/ -v -n auto    # self-hosted compiler tests
make lint                             # black + ruff + mypy
```

5,445+ tests. The `-n auto` flag (via `pytest-xdist`) runs in parallel.

---

## 8. Where to Go Next

| If you want to... | Read... |
|---|---|
| A feature-by-feature tour (agents, signals, streams, pipelines) | [`docs/getting-started.md`](../getting-started.md) |
| The formal language reference | [`docs/SPEC.md`](../SPEC.md) |
| Async / await patterns with native file and HTTP I/O | [`docs/cookbook/async.md`](../cookbook/async.md), [`docs/guides/async.md`](async.md) |
| How to debug a Mapanare program | [`docs/guides/debugging.md`](debugging.md) |
| Build an AI agent with LLM calls and structured extraction | [`docs/cookbook.md` — "Building an AI agent"](../cookbook.md#building-an-ai-agent-in-mapanare) |
| Cross-language benchmarks vs C/Rust/Go/Python | [`benchmarks/PHASE_C_RESULTS.md`](../../benchmarks/PHASE_C_RESULTS.md) |
| The release history + roadmap | [`docs/roadmap/ROADMAP.md`](../roadmap/ROADMAP.md) |
| Contribute a language change | [`docs/rfcs/`](../rfcs/) |

---

## Troubleshooting

**`clang` can't find `-lmapanare_rt`.** Build the runtime first:
`make -C runtime/native`.

**`llvm-as` rejects emitter output.** File a bug — this is a hard gate
in CI. Include the output of `python scripts/ir_doctor.py audit
<your_ir_file>.ll`.

**`mapanare` is not on the `PATH`.** Ensure your venv is activated, or
run as `python -m mapanare <command>`.

**Mixing LLVM versions.** Mapanare targets LLVM 18.x. Mismatched
versions of `llvm-as` / `opt` / `llc` / `clang` will produce
obscure link errors. Confirm with `clang --version` and
`llvm-as --version`.

**Async program crashes or produces wrong output.** Check
[`docs/cookbook/async.md` §11](../cookbook/async.md#11-two-emitter-bugs-to-know-about-sh9)
for the Sh.9a / Sh.9b workarounds before filing a bug.
