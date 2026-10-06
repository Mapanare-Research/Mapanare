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

## Native string accumulation

The native optimizer now replaces eligible `result = result + chunk` loops
with a StringBuilder. It copies the initial value once, appends chunks with
amortized growth, and transfers the final buffer back to the string at exit.
Existing aliases of the initial string keep their original contents.

The first implementation requires a four-block function: entry, loop header,
single body, and returning exit. The local accumulator must have exactly one
load/concat/store update in the body and no other loop observations or writes.
Nested loops, breaks, early returns, unsupported MIR instructions and loops
that read the string in their condition or body remain unchanged. This is a
deliberately narrow optimization, not general loop or alias analysis.

GCC runtime builds also now handle shrinking string replacements correctly:
lengths are converted from unsigned bit fields to signed integers before
subtraction. A longer search string is rejected before any search reads.

## Remaining work

- Broaden native StringBuilder matching to more control-flow shapes, with
  proofs for exits, dominance and aliasing rather than block-order guesses.
- Native heap-to-stack promotion for containers requires alias/lifetime
  information and matching destruction behavior. The unused native escape
  scan is omitted from the production pipeline; ordinary structs already use
  SSA values/stack storage.
- Add parser, type-checker, optimizer, emission and linker phase timings,
  plus stable CI baseline artifacts for larger applications.
- The existing native emitter can miss the final string drop when a return
  block is emitted before an allocating inner loop. This was reproduced with
  the pre-change compiler. The nested-loop fallback test checks output,
  address safety and undefined behavior but disables leak detection for this
  known case; all transformed test cases are leak-checked.
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

## StringBuilder follow-up, 2026-10-06

The [follow-up measurement record](../../benchmarks/performance/2026-10-06-string-builder.json)
contains 15 runtime samples per workload/compiler and nine compile-latency
samples per case, collected after builds and tests finished on the same WSL2
machine. Both compilers used identical LLVM `-O2` flags and the same runtime
archive for the program-throughput comparison.

The 10,000-append string workload improved from **5.361 ms to 0.082 ms** median
(about **65x faster**). All six native workloads produced correct checksums.
Other workload medians were broadly similar; this is a string-loop improvement,
not a 65x improvement to arbitrary programs.

Hello IR emission measured 112.8 ms and compile-and-run 301.3 ms. Cached build
and release medians increased 5.4% and 6.1%, respectively, versus the saved
compiler in this run; all four cases passed the 10% relative regression gate.
The stripped compiler grew from 7,630,048 to 7,666,912 bytes (about 0.5%). The
new pass increases bootstrap IR from 2.462M to 2.525M lines, so its size ceiling
is now 2.6M; the 10 MB binary and five-second latency ceilings are unchanged.

Validation: 103/103 native goldens, 1,924 LLVM/MIR/optimizer/self-hosted/bootstrap
tests passed (five existing expected failures and two existing unexpected
passes), and 19 native integration/sanitizer tests passed. The final compiler
also emitted LLVM-valid code for its updated source. This does not close the
separate stage2/stage3 fixed-point failures described above.
