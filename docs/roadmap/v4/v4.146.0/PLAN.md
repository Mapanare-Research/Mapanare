# Mapanare v4.146.0 — E2: `fib_recursive` calling convention / pure-CPU

> **Tighten the last 10 % on a pure-recursion workload.** `fib_recursive`
> is already in a tight race with Rust (post-v4.144.0 baseline, it hovers
> near 1.1×–1.2× of Rust). Any remaining gap here is calling-convention
> hygiene: missing `nsw` on arithmetic, missing `readnone` / `speculatable`
> on pure functions, or absent tail-call metadata. E2 is the smallest
> experiment in the arc and the cheapest proof that the IR-diff discipline
> catches genuine bugs, not just obvious ones.

**Status:** PLANNED
**Breaking:** No (perf patch, no API change)
**Prerequisite:** v4.145.0 shipped (E1 recorded as win or dead end)
**Estimated work:** 1–2 h
**Theme:** E2 — `fib_recursive` calling convention / pure-CPU

---

## Why this release, why now

`fib_recursive` is the cleanest possible CPU workload: pure integer
recursion, no allocation, no branches beyond the base case, no strings,
no state. Any observable gap to Rust on this workload is pure codegen
hygiene — the kind of thing v4.30.0 claimed to fix (`nsw` flags on
signed arithmetic) and the kind of thing reviewers routinely lose
sleep over.

At v4.144.0 baseline, `fib_recursive` runs ~1.1×–1.2× of Rust. The
remaining gap is small enough that a single missing IR flag could
account for all of it. The experiment is to *find which flag(s)*, not
to redesign anything.

The value of E2 isn't the benchmark delta — it's the audit. We will
read every emitted instruction for `fib` and compare against what
`rustc -O` produces, then patch exactly what's different. This is the
v4.30.0 claim's honest verification.

## Baseline (measure before touching code)

```bash
echo "4.146.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Target workload
python3 benchmarks/cross_language/run_benchmarks.py --only fib_recursive --runs 20 \
  --output benchmarks/cross_language/v4.146.0-baseline.json

# Full sweep for 5% rule floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.146.0-full-baseline.json
```

Write `docs/roadmap/v4/v4.146.0/BASELINE.md` with:
- `fib_recursive` median wall (Mapanare, Rust, C, Go, Python)
- Ratio to Rust (baseline target: get this below 1.1×)
- CPU, RSS (low interest for this workload but keep the discipline)
- `perf stat` instruction count + cycles (this is the diagnostic number)

## Hypothesis

One or more of the following IR-level omissions accounts for the
remaining 10–20 % gap to Rust:

- **`nsw` on integer arithmetic:** `fib(n-1) + fib(n-2)` should lower
  to `add nsw i64 ...` / `sub nsw i64 ...`. Missing `nsw` prevents
  some LLVM loop / induction-variable optimizations.
- **`readnone` / `speculatable` attributes on `fib` itself:** a pure
  function with no side effects, no memory access, should carry
  `attributes { readnone speculatable willreturn nounwind }`. Missing
  these blocks LLVM from CSE-ing repeated calls.
- **Tail-call hint:** `fib(n-1)` followed by `fib(n-2)` and an add
  cannot be tail-optimized (not tail positions), but the final add can
  be marked `tail` if the function returns it directly. Minor, but
  audit-worthy.
- **Opaque pointer cleanliness:** `fib` takes `i64`, returns `i64`,
  no pointers. But verify the function signature has no legacy `i64*`
  artifacts anywhere in the MIR → IR chain.

## Phase 1 — IR diff vs Rust

```bash
python3 -m mapanare emit-llvm benchmarks/optimizer/fib_recursive.mn -O3 \
  -o /tmp/fib.mn.ll

rustc -O --emit=llvm-ir \
  benchmarks/cross_language/rust/fib_recursive/src/main.rs \
  -o /tmp/fib.rs.ll

culebra extract /tmp/fib.mn.ll fib > /tmp/fib_mn.ll
# Extract the matching Rust fib function (check mangled name)
grep -E "^define .*fib" /tmp/fib.rs.ll | head -3
```

Write `docs/roadmap/v4/v4.146.0/IR_DIFF.md`:
- Full `fib` definition, Mapanare side (expect ~15 lines)
- Full `fib` definition, Rust side (expect ~15 lines)
- Line-by-line annotation of every flag / attribute difference

Specifically audit:
1. Function attribute set (Mapanare vs Rust: do we have
   `nofree nosync nounwind readnone speculatable willreturn`?)
2. `add` / `sub` instructions — do both carry `nsw`? `nuw`?
3. Call instructions — any `tail` / `musttail` markers?
4. Parameter attributes — `noundef` on `i64` arg?
5. Return value attributes — `noundef i64` on the ret?

## Phase 2 — Form hypothesis

Write `docs/roadmap/v4/v4.146.0/HYPOTHESIS.md` naming the *specific*
flag(s) missing and the expected per-flag contribution:

> *"Mapanare emits `add i64` and `sub i64` without `nsw`, and `fib`
> itself lacks `readnone` + `speculatable` function attributes. Adding
> all three is expected to close ≤ 10 % of the remaining Rust gap."*

If the IR diff shows the flags already present, the hypothesis shifts
to: *"Calling convention is clean; gap is in unrelated code (e.g.,
main driver loop). E2 is a dead end; close with no patch."*

## Phase 3 — Patch

Target files (in order of likelihood):

1. `mapanare/emit_llvm_text.py::emit_binop` — emit `nsw` / `nuw` flags
   on `add`/`sub`/`mul` when MIR operand types are signed integers
   (Mapanare's `Int` is `i64` signed). Verify v4.30.0's claim against
   actual emitted IR — this may already be correct.
2. `mapanare/emit_llvm_text.py::_RUNTIME_FN_ATTRS` (or equivalent) —
   extend the pure-function attribute set so user functions that pass
   semantic purity checks (no side effects, no allocations, no prints)
   get `readnone speculatable willreturn` in addition to `nounwind`.
3. `mapanare/semantic.py` or `mapanare/mir.py` — add a `is_pure` flag
   to function MIR nodes, populated during lowering. Emit attributes
   based on this flag. (Only if step 2 requires it — prefer to keep
   the patch in `emit_llvm_text.py` alone.)

Estimated diff: ~20–40 logic lines across 1–2 files.

## Phase 4 — Re-measure

```bash
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py --only fib_recursive --runs 20 \
  --output benchmarks/cross_language/v4.146.0-patched.json
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.146.0-full-patched.json
```

**5% rule:**
- `fib_recursive` median must improve ≥ 5 % vs baseline OR get within
  1.1× of Rust (whichever comes first is the "win" signal).
- No other cross-language workload may regress > 2 %.

If the IR diff showed no missing flags (i.e., v4.30.0's claim is fully
realized), E2 closes as a dead end with "gap is not in fib itself;
docket E2a to look at the driver loop." That's a legitimate result.

## Phase 5 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E2 | fib_recursive: nsw flags + pure-fn attrs | <win/dead-end> | +XX% vs baseline | emit_llvm_text.py::emit_binop | v4.146.0 |
```

Write `docs/roadmap/v4/v4.146.0/RESULTS.md` and
`docs/roadmap/v4/v4.146.0/SESSION_REPORT.md`.

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `BASELINE.md` written with pre-patch `fib_recursive` numbers + `perf stat` count | yes |
| 2 | `IR_DIFF.md` written (Mapanare `fib` vs Rust `fib`, full bodies) | yes |
| 3 | `HYPOTHESIS.md` names specific flag(s) expected to close the gap | yes |
| 4 | Patch applied OR documented absence of patch (E2 dead end) | yes |
| 5 | `RESULTS.md` written with before/after numbers | yes |
| 6 | `fib_recursive` within 1.1× of Rust OR improvement ≥ 5 % OR honest dead-end recorded | yes |
| 7 | No other cross-language workload regresses > 2 % | yes |
| 8 | `PERF_EXPERIMENTS.md` entry added (win or dead-end) | yes |
| 9 | Non-bootstrap pytest: ≥ 5,167 passed / 0 failed | yes |
| 10 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 11 | Native goldens: 54 / 66 | yes |
| 12 | Goldens `28_fib.mn` (or equivalent) byte-identical | yes |
| 13 | Valgrind: 0 ERRORS | yes |
| 14 | ASan: 0 ASAN_ERROR | yes |
| 15 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 16 | All 8 CI gates green | yes |
| 17 | SESSION_REPORT.md written | yes |
| 18 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 19 | Tag `v4.146.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Adding `nsw` triggers UB-sanitizer findings (signed overflow on large `fib(n)`) | low | medium | `fib(35)` fits in `i64` by 10 orders of magnitude; adding `nsw` is sound for this workload. Audit any other UB signals. |
| `readnone` added to a function that's actually impure (prints, allocates) | medium | medium | Gate attribute emission on MIR purity analysis; if purity tracking doesn't exist yet, scope the attribute to a whitelist of functions known to be pure (`fib`, `factorial`, `gcd`) |
| IR diff shows no missing flags — E2 is a no-op release | medium | low | That's a legitimate dead-end result; record it and continue to E3 |
| Pure-fn attributes accelerate `fib` but regress a non-target bench that shares the same codepath | low | low | 5 % rule catches this. Full sweep included in baseline + patched runs |

## What this release does NOT do

- Does not redesign the calling convention or function attribute system.
- Does not introduce a purity-tracking pass (defer to a later release
  if the patch requires it).
- Does not touch `lower.py` beyond exposing MIR purity info (if needed).
- Does not chase `fib_recursive` below 1.0× Rust — parity is the target,
  not outperformance.
- Does not mirror into `mapanare/self/emit_llvm.mn` (parity follow-up).

## Carry-forward after v4.146.0

- If win: new Cb.12 or similar opens for self-hosted parity, LOW.
- If dead end (flags already present): E2 closes cleanly, notes filed
  against v4.30.0's claim that they landed and held.
- If partial (some flags present, some missing): patch the missing
  ones, document the partial delta, proceed to E3.
- `fib_recursive` numbers republished at v4.153.0.
