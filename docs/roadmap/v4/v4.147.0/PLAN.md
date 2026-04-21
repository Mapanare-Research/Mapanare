# Mapanare v4.147.0 — E3: parameter-level `noalias` for hot loops

> **Unlock LLVM auto-vectorization.** Mapanare currently only sets
> `noalias` on allocator return values (`_RUNTIME_FN_ATTRS`). User-
> function parameters — including loop-bound slices and `List<Int>`
> pointers — carry no aliasing information, so LLVM conservatively
> assumes everything aliases and skips vectorization. The fix is an
> escape-analysis pass (MIR-level) that proves parameters non-aliasing
> and marks them accordingly. This is the biggest of the first five
> experiments (E1–E5) and the one most likely to trip the 5% rollback
> rule if the analysis is wrong.

**Status:** PLANNED
**Breaking:** No (perf patch, no API change)
**Prerequisite:** v4.146.0 shipped (E2 recorded)
**Estimated work:** 2–3 days
**Theme:** E3 — parameter-level `noalias` (escape-analysis-driven)

---

## Why this release, why now

The v5.1.0 perf story needs a vectorization narrative. Mapanare's
numeric benchmarks (quicksort, prime_sieve, struct_alloc) run tight
scalar loops where LLVM's `loop-vectorize` pass *would* fire if it
knew the two input buffers didn't overlap. Right now, emit_llvm_text
emits functions like `fn sort(arr: List<Int>)` as `%List = {ptr, i64, i64}`
parameters with no `noalias`, so `-Rpass=loop-vectorize` reports
"runtime dependency check failed" and falls back to scalar code.

Adding `noalias` unconditionally is unsound — two calls to
`foo(list_a, list_a)` would violate it and produce UB. The correct
fix is an MIR-level escape-analysis pass that proves, for each
parameter pair, that they cannot alias (because one is fresh-
allocated, or the call-site types are distinct, or the MIR never
aliases them). Parameters that pass the check get `noalias` in the
emitted IR; parameters that don't get nothing.

This is the arc's highest-risk experiment. If escape analysis is
over-eager, we introduce silent miscompilation — the nightmare
scenario. If it's under-eager, we get no speedup and the 5 % rule
rolls back the patch. The discipline here is: ship the analysis
conservatively, run valgrind + ASan on every vectorization-
sensitive bench, and only keep `noalias` on parameters we can
trivially prove non-aliasing.

## Baseline (measure before touching code)

```bash
echo "4.147.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Target benchmarks (the ones most likely to vectorize)
python3 benchmarks/cross_language/run_benchmarks.py \
  --only quicksort,prime_sieve,struct_alloc --runs 20 \
  --output benchmarks/cross_language/v4.147.0-baseline.json

# Full sweep for 5 % rule floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.147.0-full-baseline.json

# Vectorization diagnostic — count current -O3 vectorized loops
python3 -m mapanare emit-llvm benchmarks/optimizer/quicksort.mn -O3 -o /tmp/qs.ll
opt -O3 -pass-remarks-analysis=loop-vectorize /tmp/qs.ll -o /dev/null 2>&1 \
  | tee docs/roadmap/v4/v4.147.0/vec-baseline-quicksort.log
```

Write `docs/roadmap/v4/v4.147.0/BASELINE.md` with:
- Median wall for quicksort, prime_sieve, struct_alloc
- Count of `loop-vectorize` successes / failures per workload
- Ratio to Rust

## Hypothesis

Adding `noalias` to provably non-aliasing `List<T>`/slice parameters
unblocks LLVM's loop-vectorize on 2–5 hot loops in the numeric
benchmarks, yielding 15–40 % wall improvement on `quicksort` and
`prime_sieve`.

Concrete IR-level differences expected:

- **Parameter attributes:** Rust emits `noalias` on `&mut [i64]` / `&[i64]`
  arguments; Mapanare emits no aliasing attribute on `%List.Int` arg.
- **Vectorization remarks:** Rust gets "vectorized" remarks at -O3;
  Mapanare gets "loop not vectorized: cannot identify array bounds"
  or "runtime dependency check failed."
- **Instruction mix:** Post-patch, expect `<4 x i64>` SIMD ops in
  place of scalar `i64` ops in the inner loop.

## Phase 1 — IR diff vs Rust

```bash
# Quicksort
python3 -m mapanare emit-llvm benchmarks/optimizer/quicksort.mn -O3 -o /tmp/qs.mn.ll
rustc -O --emit=llvm-ir benchmarks/cross_language/rust/quicksort/src/main.rs \
  -o /tmp/qs.rs.ll

culebra extract /tmp/qs.mn.ll partition > /tmp/partition_mn.ll
# Rust partition function, extracted by mangled name
```

Write `docs/roadmap/v4/v4.147.0/IR_DIFF.md` covering at minimum:
- `partition` (quicksort hot loop)
- `sieve` (prime_sieve hot loop)
- `struct_alloc_loop` (struct_alloc hot loop)

Focus annotations on parameter attribute lists and inner-loop
vectorization shape.

## Phase 2 — Form hypothesis

Write `docs/roadmap/v4/v4.147.0/HYPOTHESIS.md`:

> *"MIR-level escape analysis proves that parameters of kind
> `List<T>` are non-aliasing when the call site passes distinct allocas.
> Emitting `noalias` on these parameters unblocks LLVM loop-vectorize
> on ≥ 2 of { quicksort, prime_sieve, struct_alloc }."*

Document the escape-analysis precision rules:

**Safe to mark `noalias`:**
- Parameter is `List<T>` / `Map<K,V>` / `String` with no re-binding
  inside function body.
- Call sites pass distinct SSA allocas (not the same value twice).
- Function does not capture the parameter into a closure.

**Unsafe (must NOT mark):**
- Function stores parameter into a shared data structure.
- Function calls itself recursively with the same parameter.
- Parameter is pattern-matched against another parameter.
- Function has any `*mut` / `&mut` style borrowing MIR primitives
  not covered by the safe-set.

## Phase 3 — Patch

Targets:

1. `mapanare/mir_opt.py` — new escape-analysis pass
   `mark_noalias_params`. Runs after copy-propagation, before emission.
   For each function:
   - Build the set of parameters that never escape (not stored, not
     returned, not captured).
   - Build the set of parameters that are never compared to another
     parameter.
   - Build the set of call sites where all `List<T>` args are distinct
     SSA values.
   - Intersect. Emit per-parameter `noalias_ok` metadata on the MIR
     function node.

2. `mapanare/emit_llvm_text.py` — consume the `noalias_ok` metadata
   and emit `noalias` on the corresponding parameter attribute lists.

3. `mapanare/semantic.py` — if escape-analysis needs additional capture
   info not already in MIR, wire it in as a non-breaking field.

Estimated diff:
- `mir_opt.py`: ~150–250 logic lines (new pass)
- `emit_llvm_text.py`: ~10–20 lines (attribute emission)
- `semantic.py`: ~0–40 lines (if capture info needed)

Add regression tests in `tests/mir_opt/test_noalias_pass.py`:
- Self-aliasing call rejected
- Captured-in-closure rejected
- Fresh-alloca call accepted
- Recursive call with same arg rejected

## Phase 4 — Re-measure

```bash
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py \
  --only quicksort,prime_sieve,struct_alloc --runs 20 \
  --output benchmarks/cross_language/v4.147.0-patched.json
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.147.0-full-patched.json

# Verify vectorization landed
opt -O3 -pass-remarks=loop-vectorize /tmp/qs.mn.patched.ll -o /dev/null 2>&1 \
  | tee docs/roadmap/v4/v4.147.0/vec-patched-quicksort.log

# Sanitizer sweep — MUST be clean after `noalias` changes
bash scripts/run_asan_goldens.sh 2>&1 | tail -5
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5
```

**5% rule:**
- At least one target benchmark (quicksort / prime_sieve / struct_alloc)
  must improve ≥ 5 %.
- No non-target benchmark may regress > 2 %.
- Zero new valgrind or ASan findings (hard gate — `noalias` + UB =
  disaster).

## Phase 5 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E3 | noalias on non-aliasing params | <win/dead-end> | quicksort +XX%, sieve +XX%, alloc +XX% | mir_opt.py::mark_noalias_params (+NNN LOC) | v4.147.0 |
```

Write `RESULTS.md` with vectorization-remark delta and wall-time delta
side-by-side, and `SESSION_REPORT.md` narrating the escape-analysis
design decisions in detail (this is the one experiment in the arc
where the analysis precision matters more than the delta).

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` with pre-patch numbers + vectorization-remark counts | yes |
| 2 | `IR_DIFF.md` covering quicksort + prime_sieve + struct_alloc hot loops | yes |
| 3 | `HYPOTHESIS.md` naming the escape-analysis precision rules | yes |
| 4 | New MIR pass `mark_noalias_params` in `mir_opt.py` | yes |
| 5 | Attribute emission hook in `emit_llvm_text.py` | yes |
| 6 | Unit tests for escape-analysis precision (≥ 4 tests) | yes |
| 7 | `RESULTS.md` with before/after numbers + vec-remark delta | yes |
| 8 | ≥ 1 target bench improves ≥ 5 % | yes |
| 9 | No bench regresses > 2 % | yes |
| 10 | Zero new valgrind ERRORS | yes |
| 11 | Zero new ASan ASAN_ERROR | yes |
| 12 | `PERF_EXPERIMENTS.md` entry added | yes |
| 13 | Non-bootstrap pytest: ≥ 5,171 passed / 0 failed (+4 escape-analysis) | yes |
| 14 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 15 | Native goldens: 54 / 66 | yes |
| 16 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 17 | All 8 CI gates green | yes |
| 18 | SESSION_REPORT.md written (detailed on precision rules) | yes |
| 19 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 20 | Tag `v4.147.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Escape analysis over-marks; two call sites pass aliased pointers; UB-driven silent miscompilation | medium | CRITICAL | Conservative precision rules (see HYPOTHESIS); full ASan + valgrind sweep on all 66 goldens + all 5160 tests; roll back on any new finding |
| Escape analysis is too conservative; no `noalias` emitted; no speedup | medium | medium | 5% rule fires; document as dead end; open Own.2 carrying forward the conservative-precision problem |
| `noalias` on `List<T>` trips a runtime invariant (e.g., internal sharing of a pooled allocation) | low | high | The runtime uses arena allocation with distinct allocas per `List<T>` construction; aliasing is not possible at the MIR level. Verify with grep for any pool-sharing code path before shipping |
| Vec-remark output changes across clang/LLVM versions — remarks log is noisy | medium | low | Check vec-remark counts via a script, not by eye; accept version-dependent phrasing if the SIMD ops appear in the IR |
| New MIR pass slows compile time > 10 % | low | low | Run `scripts/build_stage1.py` before / after; if > 10 % slowdown, optimize the pass (use SSA name-lookup sets, not linear scan) |

## What this release does NOT do

- Does not mark `noalias` unconditionally — escape analysis is
  required; no shortcuts.
- Does not touch the agent / signal / stream runtime — parameters
  that enter those pathways are explicitly excluded from `noalias`.
- Does not mirror into `mapanare/self/emit_llvm.mn` (parity follow-up).
- Does not redesign `List<T>` representation or the MIR capture model.
- Does not chase vectorization on string workloads (E4 covers strings
  separately).

## Carry-forward after v4.147.0

- If win: new Cb.13 or similar opens for self-hosted parity, LOW.
  A small Own.2 or similar may open for "escape analysis precision
  is conservative; could be tightened" as a research follow-up.
- If dead end: document the conservative-precision wall; the patch is
  rolled back; we proceed to E4 having learned that parameter-level
  noalias isn't the right lever for these workloads.
- If partial: keep only the parameters that cleared the analysis; note
  which didn't and why in SESSION_REPORT.
- All deltas republished at v4.153.0 pre-panel refresh.
