# Mapanare v4.142.0 — Ge.1 close + pre-panel refresh (attempt 4)

> Close the Ge.1 generics-initialization bug class (5 residual
> valgrind ERRORS) and finalize MEASUREMENTS.md for the v4.143.0
> panel (v5 gate attempt 4).

**Status:** PLANNED
**Breaking:** No (compiler internal — lowerer initializes stack
structs it was relying on zero-fill for)
**Prerequisite:** v4.141.0 (lint clean, 5th flaky audit)
**Estimated work:** 1 sprint — half code (Ge.1), half evidence
**Theme:** Empty the valgrind ledger. Prep the desk for the panel.

---

## Why this release

At v4.136.0 the valgrind + ASan results were:
- Valgrind: 0 CLEAN / 60 WARNINGS_ONLY / **5 ERRORS** (all Ge.1)
- ASan: 54 CLEAN / **0 ASAN_ERROR** / 11 CRASH_NO_ASAN (feature gaps)

The 5 Ge.1 ERRORS are silent UB in the generics-monomorphization
path (no miscompile observed today, but stacks of uninitialized
bytes propagate through code that reads them conditionally). Closing
Ge.1 takes valgrind to **0 ERRORS** (from 36 at the v4.105.0 baseline,
a −100% close). That's the final evidence Rattler and Viper need to
move from 8.9-9.0 to 9.2+ at the panel.

Plus, the v4.143.0 panel needs a fresh MEASUREMENTS.md mirroring
what v4.135.0 did for the v4.136.0 panel.

---

## Scope

### Ge.1 — generics-init class (5 valgrind ERRORS)

**Source**: `docs/roadmap/v4/v4.135.0/VALGRIND_REPORT.md`.

Top frames (per v4.135.0 sweep):
- `lower_state__fresh_tmp` 4× (Ge.1 uninit-reads)
- `lower__try_monomorphize_struct` 4×
- `lower__monomorphize_impl_methods` 2×
- `emit_llvm__resolve_variant_index` 1× (32_generic_enum only)

Tests affected:
- `26_generics.mn`
- `29_generic_impl.mn`
- `30_nested_generics.mn`
- `31_generic_multi.mn`
- `32_generic_enum.mn`

All 5 programs exit 0 with correct output under the plain harness
(the uninit bytes don't influence control flow today, but a future
optimizer pass could turn them into miscompiles).

**Root cause hypothesis**: `fresh_tmp(...)` in `lower_state.mn`
allocates a struct on the stack without zero-initializing its
fields. For generics, some fields are computed lazily during
monomorphization (`try_monomorphize_struct`, `monomorphize_impl_methods`),
and the read happens before the lazy write. Zero-filling the struct
at alloca would close all 5 cases.

**Fix options**:

1. **Option A (precise)**: audit `fresh_tmp` and every
   `lower_state.mn` struct-creator to identify which fields are
   written unconditionally vs lazily; add an explicit init for the
   lazy ones.
2. **Option B (broad)**: emit `memset 0, sizeof(T)` after every
   `fresh_tmp` alloca that returns a non-POD struct. Solves the
   whole class with one intervention; ~1% perf cost on monomorphization
   paths (negligible).
3. **Option C**: align the self-hosted with Python's pattern where
   `lower.py` zero-inits on creation. Usually (B) in practice.

Recommend **Option B** — one-place fix, solves all 5 valgrind
ERRORS, low perf cost. Document the decision in SESSION_REPORT so
the self-hosted mirror knows why.

### Pre-panel: MEASUREMENTS.md v4.142.0 FINAL

Mirror `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md`. Refresh:
- Test counts live at v4.142.0
- Golden count via mnc-stage1 (expect ≥ 54/65)
- Self-hosted LOC
- Benchmark geomean (cross-language + async — refresh runs)
- Fixed-point md5 (new md5 from v4.140.0 or v4.139.0 emitter change)
- Sanitizer classes (Ge.1 now 0 ERRORS)
- Flaky audit (5 audits, 25 runs total)
- Dead-code line counts (unchanged)
- Docket ledger (Ch.1, Bo.*, Gr.2, Sem.1, §0, Co.1, Dr.1, Cb.5, SE.1,
  Cb.3, An.2, Ge.1 all CLOSED; running total)
- Panel score history + v4.143.0 forecast

### Pre-panel: PRE_PANEL_AUDIT.md overlay

Fact-check 13 SESSION_REPORTs (v4.121.0 through v4.134.0 previously;
extend to v4.137.0–v4.141.0 for this cycle — that's 6 new + 13 old =
19 total, but the 13 old are already sealed and don't need
re-auditing). New scope: v4.137.0 through v4.141.0.

---

## Phase 1 — Ge.1 fix

```bash
echo "4.142.0" > VERSION
git checkout -b v4.142.0 dev

# Reproduce current state
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -3
# Expected: 0 CLEAN / 60 WARNINGS / 5 ERRORS
```

**Option B implementation** — audit `mapanare/self/lower_state.mn::fresh_tmp`:

```mapanare
fn fresh_tmp(st: LowerState, ty: Type) -> (Value, LowerState):
  let name = new_temp_name(st)
  let v = make_value(name, ty)
  let s = emit_instr(st, Instruction::Alloca(v.value, ty))
  # NEW: zero-init the alloca for non-POD types
  let s = emit_instr(s, Instruction::MemsetZero(v.value, size_of_type(ty)))
  return (v, s)
```

And corresponding `emit_llvm.mn` codegen for the new
`Instruction::MemsetZero` case — `call void @llvm.memset.p0.i64(ptr
%x, i8 0, i64 N, i1 false)`.

Python emitter mirror: `mapanare/lower.py` — same pattern where it
creates fresh temporaries for generics monomorphization.

Verify after each file edit:

```bash
python3 scripts/build_stage1.py
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -5
# Expected after: 0 CLEAN / ≤60 WARNINGS / 0 ERRORS
```

## Phase 2 — Verify Ge.1 closure

```bash
# Run each of the 5 affected goldens under valgrind individually
for t in 26_generics 29_generic_impl 30_nested_generics 31_generic_multi 32_generic_enum; do
  echo "=== $t ==="
  valgrind --error-exitcode=99 ./mapanare/self/mnc-stage1 tests/golden/${t}.mn >/dev/null
  echo "exit: $?"
done
# Expected: each exits 0 (valgrind --error-exitcode=99 would fire on any error)

# Full sweep
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh 2>&1 | tail -3
# Expected: 0 CLEAN / 60+ WARNINGS / 0 ERRORS

# ASan confirms no new findings
bash scripts/run_asan_goldens.sh 2>&1 | tail -3
# Expected: 54+ CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN

# Fixed-point holds
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll
```

## Phase 3 — Benchmark refresh

```bash
python3 benchmarks/cross_language/run_benchmarks.py --runs 10 \
  > benchmarks/cross_language/v4.142.0-results.json
python3 benchmarks/async/run_async.py --runs 10 --cross-language \
  > benchmarks/async/v4.142.0-async.json

# Generate FINAL_REPORT_v4.143.md (mirrors v4.136.md structure)
python3 benchmarks/generate_report.py --version 4.142.0 \
  > benchmarks/FINAL_REPORT_v4.143.md
```

## Phase 4 — Sanitizer sweeps (fresh)

```bash
VG_OUTDIR=docs/roadmap/v4/v4.142.0/valgrind-logs bash scripts/valgrind_all_goldens.sh
bash scripts/run_asan_goldens.sh 2>&1 | tee docs/roadmap/v4/v4.142.0/asan-run.log

# Summary tables
python3 scripts/summarize_sanitizer_logs.py valgrind > docs/roadmap/v4/v4.142.0/valgrind-summary.tsv
python3 scripts/summarize_sanitizer_logs.py asan > docs/roadmap/v4/v4.142.0/asan-summary.tsv

# Write VALGRIND_REPORT.md + ASAN_REPORT.md mirroring v4.135.0 structure
```

## Phase 5 — MEASUREMENTS.md FINAL

Copy `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md` as template. Update
every section:
- Refresh all numbers live at v4.142.0 HEAD
- Mark Ge.1 as CLOSED in §8 carry-forward
- Update fixed-point md5 section with v4.140.0-era md5
- Update flaky audit §6 to include v4.141.0 5th audit
- Update Section 9 panel score history with v4.136.0 result + v4.143.0 forecast

## Phase 6 — PRE_PANEL_AUDIT.md

Fact-check v4.137.0 – v4.141.0 SESSION_REPORTs (5 new ones). Mirror
the v4.135.0 overlay structure. Target: 0 material discrepancies.

## Phase 7 — V5_READINESS.md

Revisit the 8 "would embarrass v5" items list from v4.119.0. By
v4.142.0, expect 8/8 closed (was 7/8 at v4.135.0 — package manager
the one open item, which is v5.x ecosystem scope).

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Ge.1 fix in `lower_state.mn::fresh_tmp` (or equivalent) | yes |
| 2 | Python emitter mirror | yes |
| 3 | 5 Ge.1 tests: 0 valgrind ERRORS each | yes |
| 4 | Full valgrind sweep: 0 ERRORS | yes |
| 5 | ASan sweep: 0 ASAN_ERROR (unchanged) | yes |
| 6 | Fixed-point md5 stable (record new if self-hosted changed) | yes |
| 7 | Goldens ≥ 54/65 | yes |
| 8 | Pytest baseline hold | yes |
| 9 | Benchmarks refreshed (cross-language + async) | yes |
| 10 | MEASUREMENTS.md v4.142.0 FINAL | yes |
| 11 | VALGRIND_REPORT.md + ASAN_REPORT.md written | yes |
| 12 | PRE_PANEL_AUDIT.md covers v4.137.0 – v4.141.0 | yes |
| 13 | V5_READINESS.md updated | yes |
| 14 | Ge.1 CLOSED in DOCKET_LEDGER | yes |

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| `memset 0` on every fresh_tmp materially slows compile | low | low | Benchmark compile time before/after; allow ≤5% regression |
| Option B misses a Ge.1 case that doesn't go through `fresh_tmp` | medium | medium | Re-run valgrind sweep; if residual, audit remaining stack-allocators case-by-case (Option A fallback) |
| Fixed-point break from zero-init emission change | medium | high | Gate sub-commits through verify_fixed_point.sh; record new reference md5 in FIXEDPOINT_STATUS.md |
| Benchmark numbers drift > ±15% | low | medium | Run 3 times; publish median; note environmental in report |

## What this release does NOT do

- Does not change the panel rule (v4.143.0 uses the same mechanical
  rule).
- Does not re-run the panel (that's v4.143.0).
- Does not close Sh.4-Sh.7 (self-hosted feature gaps; v5.x).
- Does not close ABI.1 (24-byte struct return; v5.x calling
  convention).
- Does not add new package-manager functionality.

## Score-impact forecast

At v4.143.0 panel:
- **Rattler 8.9 → 9.2**: Ge.1 closed removes the "silent compiler UB"
  objection; fresh sanitizer sweeps show 0 ERRORS.
- **Viper 9.0 → 9.5**: valgrind ERRORS 5 → 0 is her explicit want;
  Ch.1 already closed in v4.137.0.
- **Mamba +0.05**: one more benchmark refresh.

Combined with prior releases:

| Reviewer | v4.136.0 | v4.142.0 (forecast) | Driver |
|---|---:|---:|---|
| Rattler | 8.9 | 9.2 | SE.1 (v4.140), Ge.1 (v4.142) |
| Viper | 9.0 | 9.5 | Ch.1 (v4.137), Ge.1 (v4.142) |
| Anaconda | 8.9 | 9.2 | An.2 (v4.141) |
| Cobra | 8.7 | 9.2 | Cb.5 (v4.140) |
| Coral | 8.7 | 9.1 | v4.139 |
| Boa | 8.4 | 9.0 | v4.138 |
| Mamba | 9.0 | 9.1 | v4.142 refresh |
| **Aggregate** | **8.80** | **~9.18** | → Option A territory |

All seven reviewers ≥ 9.0 would put the aggregate at ~9.2. The rule
gate (≥ 9.0 AND 0 NEEDS WORK) is reachable.
