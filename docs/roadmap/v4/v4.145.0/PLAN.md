# Mapanare v4.145.0 — E1: `enum_match` codegen vs Rust

> **First experiment of the perf arc.** Close the 3.4× Rust gap on
> `benchmarks/system/enum_match.mn` (6-variant `Shape` enum, 100k
> iterations) to ≤ 2× by attacking the `match` lowering — Rust emits
> a niche-optimized tag extract + dense jump table, Mapanare emits a
> `switch i64` against a `{i64, i64}` inline slot with extra tag-extract
> branches. This is the canonical enum-dispatch story for the v5.1.0
> perf narrative; E1 proves the experiment loop works end-to-end.

**Status:** PLANNED
**Breaking:** No (perf patch, no API change)
**Prerequisite:** v4.144.0 shipped (baseline captured, panel outcome recorded)
**Estimated work:** 2–4 h
**Theme:** E1 — `enum_match` codegen vs Rust

---

## Why this release, why now

`benchmarks/system/enum_match.mn` is the most legible workload in the
cross-language corpus: pure enum dispatch, no allocation, no strings,
no async. It's also where the Rust gap is widest *and* where we have
the most headroom because v4.124.0 already delivered the `{i64, i64}`
unboxed payload (malloc count per run 83,333 → 0). The remaining gap
is purely match-lowering shape.

At v4.144.0 baseline, Mapanare `enum_match` is in the 1.4–1.5 ms range
for 100k iterations; Rust is in the 0.43–0.45 ms range; the observed
multiple is **~3.4×**. Inline-slot representation is correct and byte-
identical between the Python and self-hosted emitters (v4.140.0 Cb.5
verification, `%enum.Shape = type {i64, i64, i64}`). What differs is
the *decode path*: Mapanare's `match Shape { Circle(r) => ...,
Square(s) => ... }` lowers to a chain of tag-load + compare +
conditional branch + payload-extract, whereas `rustc -O` collapses
the same construct into one tag-load + one `switch` + sibling branch-
weight hints.

Closing this gap is a small, self-contained emitter edit in
`mapanare/emit_llvm_text.py::_emit_match` (or equivalent). The risk is
low: the workload has golden coverage (`07_enum_match`, `27_enum_payload`,
`65_enum_payload_mixed`), the IR diff is easy to read, and the 5%
rule guards against regressions on the other 5 cross-language benches.

## Baseline (measure before touching code)

```bash
# Refresh mnc-stage1 with 4.145.0 VERSION first (so artifact strings are honest)
echo "4.145.0" > VERSION
make build-rt
python3 scripts/build_stage1.py

# Target benchmark — 20 runs, median reported
python3 benchmarks/cross_language/run_benchmarks.py --only enum_match --runs 20 \
  --output benchmarks/cross_language/v4.145.0-baseline.json

# Also capture the 5 non-target workloads for the 5% rule floor
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.145.0-full-baseline.json
```

Record median wall, CPU, peak RSS, instruction count, and branch-miss
count (if perf available) in `docs/roadmap/v4/v4.145.0/BASELINE.md`.
Expected at v4.144.0 tag: `enum_match` median ≈ 1.45 ms, Rust ≈ 0.43 ms,
ratio ≈ 3.37×.

## Hypothesis

Rust collapses enum-match to a single tag-extract + dense `switch` with
branch weights; Mapanare emits an unnecessary chain of compare-and-
branch per variant, each re-loading the tag slot.

Expected concrete IR-level differences:

- **Tag load count:** Rust loads the tag once per match; Mapanare
  reloads it per arm (or per arm pair).
- **Switch vs cascaded br:** Rust uses `switch i64` → one terminator
  per match. Mapanare emits cascaded `icmp eq` / `br i1` — one per arm.
- **Branch weighting:** Rust emits `!prof !{!"branch_weights", i32 1, ...}`
  metadata on uneven-weight arms; Mapanare emits none, so LLVM lays
  out the jump table generically.

## Phase 1 — IR diff vs Rust

```bash
# Mapanare side (the benchmark's .mn)
python3 -m mapanare emit-llvm benchmarks/system/enum_match.mn -O3 \
  -o /tmp/enum_match.mn.ll

# Rust side (the benchmark's .rs — same algorithm)
rustc -O --emit=llvm-ir benchmarks/cross_language/rust/enum_match/src/main.rs \
  -o /tmp/enum_match.rs.ll

# Extract hot functions
culebra extract /tmp/enum_match.mn.ll area > /tmp/area_mn.ll
culebra extract /tmp/enum_match.mn.ll make_shape > /tmp/make_shape_mn.ll
# For Rust, grep the mangled name first
grep -E "^define .*area" /tmp/enum_match.rs.ll | head -1
# Extract by that name via culebra or llvm-extract
```

Write `docs/roadmap/v4/v4.145.0/IR_DIFF.md` with the side-by-side
`area()` and `make_shape()` diff (20-line blocks, annotated).

## Phase 2 — Form hypothesis

Write `docs/roadmap/v4/v4.145.0/HYPOTHESIS.md`:

> *"Rust emits one tag-load + one `switch i64` + branch-weight metadata
> per match; Mapanare emits one tag-load + N `icmp eq`/`br i1` pairs
> (N = variant count). Collapsing to a single `switch` plus canonical
> payload-extract should save ~60 % on the match loop."*

Include the precise Mapanare IR snippet to be replaced and the Rust
IR snippet it should resemble after the patch.

## Phase 3 — Patch

Target: `mapanare/emit_llvm_text.py::_emit_match` (or the function that
currently lowers `MIRMatch` to IR). Smallest possible change:

1. Emit one tag-load per match (cache in local SSA, not re-load per arm).
2. Emit `switch i64 %tag, label %default [ i64 0, label %arm0; i64 1, label %arm1; ... ]`
   when all arms are tag-dense and wildcard-terminated (else fallback to
   current chain).
3. Attach `!prof !{!"branch_weights", ...}` metadata using arm hit
   counts inferred from MIR (uniform if no profile info).
4. Keep payload-extract in the per-arm basic block so no regression
   on the unbox path.

**Do not change**: the enum ABI (byte-identical to v4.140.0), the
inline-slot layout, or the match MIR node shape. This is purely an
emitter-side lowering refactor.

Estimated diff: ~60–100 logic lines in `emit_llvm_text.py`.

## Phase 4 — Re-measure

```bash
make build-rt
python3 scripts/build_stage1.py

python3 benchmarks/cross_language/run_benchmarks.py --only enum_match --runs 20 \
  --output benchmarks/cross_language/v4.145.0-patched.json

python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.145.0-full-patched.json
```

**5% rule:**
- `enum_match` median must improve ≥ 5 % vs baseline (stretch: ≥ 40 %
  for the hypothesis to be called a "clean win").
- No other cross-language workload may regress > 2 %.

If target improves but another benchmark slips > 2 %, roll back and
document in `PERF_EXPERIMENTS.md` as a dead end.

## Phase 5 — Record

Append to `docs/roadmap/v4/PERF_EXPERIMENTS.md`:

```
| E1 | enum_match switch+branch-weights | win/dead-end | +XX% vs baseline | emit_llvm_text.py:~NNN-NNN | v4.145.0 |
```

Write `docs/roadmap/v4/v4.145.0/RESULTS.md` with before/after numbers,
and `docs/roadmap/v4/v4.145.0/SESSION_REPORT.md` narrating the
experiment (use v4.142.0 Ge.1 SESSION_REPORT as length template).

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | `docs/roadmap/v4/v4.145.0/BASELINE.md` written with pre-patch numbers | yes |
| 2 | `docs/roadmap/v4/v4.145.0/IR_DIFF.md` written (Mapanare vs Rust, `area` + `make_shape`) | yes |
| 3 | `docs/roadmap/v4/v4.145.0/HYPOTHESIS.md` written (one sentence + IR snippets) | yes |
| 4 | Patch applied to `mapanare/emit_llvm_text.py::_emit_match` (or equivalent) | yes |
| 5 | `docs/roadmap/v4/v4.145.0/RESULTS.md` written with post-patch numbers | yes |
| 6 | `enum_match` median improves ≥ 5 % (target: ≤ 2× Rust) | yes |
| 7 | No other cross-language workload regresses > 2 % | yes |
| 8 | `docs/roadmap/v4/PERF_EXPERIMENTS.md` entry added (win or dead-end) | yes |
| 9 | Golden `07_enum_match.mn` byte-identical through `mnc-stage1` | yes |
| 10 | Golden `27_enum_payload.mn` byte-identical | yes |
| 11 | Non-bootstrap pytest: ≥ 5,167 passed / 0 failed | yes |
| 12 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 13 | Native goldens: 54 / 66 | yes |
| 14 | Valgrind: 0 ERRORS | yes |
| 15 | ASan: 0 ASAN_ERROR | yes |
| 16 | Fixed-point: within `DIFF_THRESHOLD=100` | yes |
| 17 | All 8 CI gates green | yes |
| 18 | SESSION_REPORT.md written | yes |
| 19 | CHANGELOG + CLAUDE.md + ROADMAP.md updated | yes |
| 20 | Tag `v4.145.0` pushed to origin | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `switch` lowering regresses a golden that uses non-tag-dense arms (e.g., string arms, range arms) | medium | medium | Keep the cascaded-br path as fallback; only switch when arms are tag-dense + wildcard-terminated |
| LLVM's `switch` lowering at -O3 is already equivalent post-SimplifyCFG — patch yields <5 % improvement | medium | medium | 5% rule fires; log as dead end; still ship the branch-weight metadata piece if independently ≥ 5 % |
| Branch-weight metadata regresses a non-target bench (e.g., `fib_recursive`) | low | medium | Emit metadata only on match-lowering path, not on generic conditional brs |
| `make_shape` also shows a gap (constructor-side, not match-side) and the patch addresses only half | medium | low | Document in RESULTS.md; split the make-shape side to v4.145.1 or fold into v4.146.0 |

## What this release does NOT do

- Does not touch the enum ABI, inline-slot layout, or MIRMatch node.
- Does not add new benchmarks or modify the existing bench corpus.
- Does not mirror the change into the self-hosted `emit_llvm.mn` yet
  (that's a separate parity release after we confirm the Python fix wins).
- Does not chase `enum_match` beyond the ≤ 2× Rust target. If we hit
  1.9×, we ship. The next release is E2.
- Does not re-enable any dormant MIR passes (that's E8 / v4.152.0).

## Carry-forward after v4.145.0

- If E1 is a clean win: the patch is in the Python emitter only. A
  follow-up self-hosted parity docket (Cb.11 or similar) is opened with
  LOW severity, targeted at v4.152.0 or v4.153.0.
- If E1 is a dead end: hypothesis is falsified, `PERF_EXPERIMENTS.md`
  records the IR diff + why the expected delta didn't materialize, and
  v4.146.0 opens on E2 as planned.
- `enum_match` numbers are republished in the v4.153.0 pre-panel refresh.
