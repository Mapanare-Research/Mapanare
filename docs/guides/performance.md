# Measuring and improving native performance

Use `mnc build app.mn --release` for runtime measurements. This compiles and
links with `-O2 -flto`, then strips the executable. `mnc run` uses `-O0` to
favor development turnaround; its timings include compilation and linking.

## Repeated builds

Single-file native builds cache generated object code under
`.mnc_cache/objects`. The exact key includes generated IR, optimization flags,
the selected clang command and its version output. The compiler still resolves
imports and emits IR on every invocation, so dependency changes reach the key.
Linking always runs against the current runtime archive. A failed link from a
cached object triggers one fresh compilation before reporting failure.

Use `mnc build app.mn --no-cache` to bypass object reuse. Cache write failures
do not prevent a build. `mnc cache clean` removes cached objects. This is an
object cache, not an incremental parser or type checker.

From a source checkout, the Bash directory driver supports bounded parallel jobs:

```bash
mnc build path/to/project --jobs 4 --timing
mnc build path/to/project --release --jobs 4
```

The Bash directory driver keeps project/compiler/toolchain/flag contexts
separate and tracks local `self::` dependencies. Imports outside that known
dependency graph force rebuilding rather than risking stale objects. Failed
compiles cannot publish a new source hash for an old object. Concurrent build
invocations for the same context fail with a lock message; an interrupted
invocation may leave a `build.lock` directory that must be removed before
retrying. Module jobs within one invocation use separate output files.

## Compile latency

Run these on an otherwise idle machine from the repository root:

```bash
python3 benchmarks/compile_time.py --runs 10 --include-uncached --output before.json
# After changing the compiler, rebuild it, then:
python3 benchmarks/compile_time.py --runs 10 --include-uncached --output after.json --baseline before.json
```

Each case has one unmeasured warmup followed by repeated samples. Reports
contain all samples, medians, source/compiler hashes, and platform metadata.
The optional baseline gate defaults to a 10% maximum increase. Use a stable
runner and the same source and toolchain. `--source` selects a larger workload;
the default is the hello golden. Build and release cases include linking;
the run case also includes program execution. These are end-to-end timings,
not individual parser, optimizer, or linker profiles.

`tests/bench/bench_startup.sh --gate` runs the repeated suite with an absolute
five-second ceiling. Pass `--baseline` to enforce a relative limit too. Missing
compilers and compilation failures fail the check.

## Program throughput

```bash
python3 benchmarks/cross_language/run_benchmarks.py --compiler native --runs 10 --output native.json
python3 benchmarks/cross_language/run_benchmarks.py --compiler bootstrap --runs 10 --output bootstrap.json
```

The default is the native `mapanare/self/mnc-stage1` binary. `--mnc` selects
another native binary for comparison. Both compiler paths use the same LLVM
`-O2` pipeline and timing wrapper, so the experiment isolates generated code.
This runner does not benchmark the CLI's release/LTO build configuration.
Reports identify the compiler path. A missing tool, compile failure, failed
run, or incorrect checksum fails the suite; invalid results do not contribute
to geometric means. Compare the two reports separately rather than assuming
the native and bootstrap compilers generate equivalent machine code.

## Remaining work

- Native string concatenation still needs the loop-to-StringBuilder
  optimization available in the bootstrap pipeline. The native benchmark
  exposes this gap; existing bootstrap results cannot close it.
- Native heap-to-stack promotion for containers requires alias/lifetime
  information and matching destruction behavior. The unused native escape
  scan is omitted from the production pipeline; ordinary structs already use
  SSA values/stack storage.
- Add parser, type-checker, optimizer, emission and linker phase timings,
  plus stable CI baseline artifacts for larger applications.
- The optimized self-hosted stage2 candidate in this investigation passed
  99/103 goldens and crashed while emitting stage3. The working compiler remains the
  Python-bootstrap-built binary, which passed 103/103 goldens. Full fixed-point
  validation is still open; the rejected candidate was not installed.

Keep correctness gates alongside performance experiments: LLVM validation,
native goldens, output checks and bootstrap tests. A smaller or faster
self-hosted compiler is not a replacement for the bootstrap-built compiler
until it passes those same gates.

## Local measurements, 2026-10-06

The [measurement record](../../benchmarks/performance/2026-10-06.json) includes
raw compile-time samples, compiler hashes, runtime medians and test results.
On WSL2 with clang 18.1.3, a synthetic directory build with 3,000 comment lines
and a hello program fell from a 6,193 ms median to 415 ms (three fresh builds
per script, same native compiler). This isolates the benefit of eliminating
one `sed` process per source line; it is not a universal 15x compiler speedup.

Small single-file cache gains were mixed: hello release builds measured
488 ms cached versus 597 ms without object reuse, while quicksort development
builds measured 463 ms cached versus 448 ms without reuse. Cache hits were
independently verified through compiler invocation logs. The release flag now
performs real LTO, so its latency is not directly comparable with the old
release flag that omitted LTO.
