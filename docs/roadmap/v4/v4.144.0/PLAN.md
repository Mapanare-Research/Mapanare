# Mapanare v4.144.0 — LOW polish + perf baseline + THE PANEL (attempt 4)

> **First release of the perf arc, and the v5.0.0-gate attempt 4.** Close
> the five remaining LOW panel items from v4.143.0 (Cb.5-tests + Cb.6
> + Cb.7 + Cb.9 + Cb.10), refresh the benchmark evidence pack now that
> Bn.1 is closed, then run the 7-reviewer panel. If aggregate ≥ 9.0
> AND 0 NEEDS WORK → Option A fires → tag `v5.0.0`. Otherwise Option C
> advances `v5.0.0-rc1` to `v5.0.0-rc2`.

**Status:** PLANNED
**Breaking:** No (test additions + minor polish; no API change)
**Prerequisite:** v4.143.0 shipped and pushed to `origin/dev`
**Estimated work:** 1–2 days (polish 0.5 day + panel 1 day)
**Theme:** Tag `v5.0.0`. Close the v4.143.0 carry-forward. Open the perf arc baseline.

---

## Why this release, why now

v4.143.0 shipped with panel aggregate **8.86 / 10**, 0 NEEDS WORK,
3 EXCEEDS. Ledger: **0 CRITICAL / 0 HIGH / 0 MEDIUM / 5 LOW**. The
0.14-point gap to Option A's 9.0 threshold is polish-sized, not
feature-sized — the remaining dockets are a single-day bundle of
Cobra items + one Rattler-flagged test gap.

Closing Cb.5-tests + Cb.6–Cb.10 plausibly moves:
- **Cobra +0.2** (his named carry-forward closes cleanly)
- **Rattler +0.1** (dedicated enum_inline unit tests land)

That projects aggregate **≈ 9.06**, enough to clear Option A's 9.0
threshold. But panels open new findings at roughly the rate old ones
close, so this is not guaranteed. The plan explicitly allows for
Option C (rc2) as a successful outcome; only Option B (NEEDS WORK /
aggregate < 8.5) counts as failure.

This release also **establishes the perf-arc baseline**: now that Bn.1
is closed, the benchmark harness is trustworthy for the first time
since v4.125.0. Re-running the full 6 cross-language + 5 async benches
and publishing `FINAL_REPORT_v4.144.md` gives every subsequent perf
release (v4.145.0+) an honest starting line.

---

## What closes in this release

### From the v4.143.0 panel LOW queue

| Docket | Owner | Scope | Effort |
|---|---|---|---|
| **Cb.5-tests** | Rattler / Cobra | Dedicated unit tests for `_enum_inline` machinery: inline-slot eligibility (≤ 2 slots, ≤ 8-byte fields, no self-ref), `pack_to_i64` / `unpack_from_i64` helper round-trips, `compute_enum_inline_slots` eligibility check. | 2 h |
| **Cb.6** | Cobra | Document the trailing-`*` typed pointer asymmetry in `type_fits_inline_slot`; add a defensive assertion. | 30 min |
| **Cb.7** | Cobra | Extract the hand-maintained move-after-transfer idiom (6 sites in `lower.mn`) into a named helper. | 1 h |
| **Cb.9** | Cobra | Port `module_path` concept into self-hosted `semantic.mn` so qualified type refs resolve in both bootstrap and self-hosted checkers. | 2 h |
| **Cb.10** | Cobra | Rewrite `66_qualified_type_ref.mn` docstring to match what the test actually exercises. | 15 min |

### Benchmark evidence refresh (new work for the arc)

- Re-run `benchmarks/cross_language/run_benchmarks.py --runs 20`
  across all 6 workloads.
- Re-run async benches under the same harness.
- Publish `benchmarks/FINAL_REPORT_v4.144.md` with honest post-Bn.1
  numbers for Mapanare vs Rust, Go, C, Python.
- Update README benchmark section (`## Benchmarks`) with v4.144.0
  citation, retire the v4.136.0 reference.
- Establish per-workload baselines in `docs/roadmap/v4/v4.144.0/BASELINE.md`
  so v4.145.0–v4.152.0 have a trusted comparison point.

### Panel (attempt 4)

- 7-reviewer panel at `.reviews/v4.144.0/` — Rattler, Viper, Anaconda,
  Cobra, Coral, Boa, Mamba.
- Pre-panel audit at `.reviews/v4.144.0/PRE_PANEL_AUDIT.md`.
- Mechanical rule applies verbatim. See `docs/roadmap/v4/PERF_ARC_PLAN.md`.

---

## Mechanical rule (unchanged)

| Rule | Condition | Outcome |
|---|---|---|
| **Option A** | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Tag `v5.0.0` |
| **Option C** | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Advance to `v5.0.0-rc2` |
| **Option B** | Aggregate < 8.5 OR any NEEDS WORK | v4.145.0 opens as recovery cycle; perf arc deferred |

**All three options permit the perf arc to continue.** Option B is
the only one that pushes the perf arc past v4.144.0 — and even then,
only by delaying its start, not cancelling it. The v4.154.0 panel is
perf-focused regardless of whether v4.144.0 fires Option A or C.

---

## Phase 1 — LOW polish (0.5 day)

### Cb.5-tests

Create `tests/llvm/test_enum_inline.py`:
- `test_compute_enum_inline_slots_eligible` — enum with 2× `Int`
  payload is eligible
- `test_compute_enum_inline_slots_too_many_slots` — enum with 3
  payload fields is ineligible
- `test_compute_enum_inline_slots_large_field` — enum with a
  16-byte payload field is ineligible
- `test_compute_enum_inline_slots_self_reference` — enum referencing
  itself is ineligible
- `test_pack_to_i64_roundtrip` — `unpack(pack(x)) == x` for all slot
  sizes 1, 2, 4, 8
- `test_enum_match_ir_shape` — compiling the `Shape { Circle(Int),
  Square(Int), ... }` from the bench emits `{i64, i64, i64}` not
  `{i64, ptr}`
- `test_enum_ir_abi_parity_python_vs_self_hosted` — compile
  `benchmarks/system/enum_match.mn` via both emitters; assert the
  `%enum.Shape` type line is byte-identical

### Cb.6

`mapanare/self/emit_llvm.mn::type_fits_inline_slot` — add a guard
clause rejecting typed-pointer-legacy `i64*` / `void()*` forms. The
function should only accept inline-sized primitive or ptr-typed
fields. Add a one-line comment naming Cb.6.

### Cb.7

Extract the move-after-transfer idiom from its 6 call sites in
`mapanare/self/lower.mn` into a named helper
`clear_moved_owner_state(state: LowerState) -> LowerState` or similar.
All 6 sites call the new helper. Behavior unchanged. This is the
systemic pattern Viper named as Own.1 — Cb.7 makes it observable by
giving it a name.

### Cb.9

`mapanare/self/semantic.mn` — mirror the `module_path` resolution
from `mapanare/semantic.py:416-445`. When a named/generic type's
`module_path` is non-empty, look up the import in scope before
falling back to the local struct/enum registry.

### Cb.10

`tests/golden/66_qualified_type_ref.mn` — rewrite the docstring to
describe what the test actually exercises (qualified type reference
round-trip through the parser and type checker, not any runtime
behavior).

## Phase 2 — Benchmark evidence refresh (0.5 day)

```bash
# Rebuild mnc-stage1 so the VERSION is 4.144.0 in all artifacts
make build-rt
python3 scripts/build_stage1.py

# Full benchmark run
python3 benchmarks/cross_language/run_benchmarks.py --runs 20 \
  --output benchmarks/cross_language/v4.144.0-results.json

# Async benches
python3 benchmarks/async/run_async_benchmarks.py --runs 20 \
  --output benchmarks/async/v4.144.0-results.json

# Human-readable report
python3 benchmarks/cross_language/format_report.py \
  benchmarks/cross_language/v4.144.0-results.json \
  > benchmarks/FINAL_REPORT_v4.144.md
```

Write `docs/roadmap/v4/v4.144.0/BASELINE.md` with per-workload medians
+ CPU + RSS, formatted as the canonical baseline for E1–E8.

Update `README.md` benchmark section:
- Replace `benchmarks/FINAL_REPORT_v4.136.md` references with `FINAL_REPORT_v4.144.md`
- Update the one-line benchmark claim in the main blurb to match
  the honest v4.144.0 numbers
- Bump Tests badge if pytest count has moved since v4.143.0 (5,160+ → ?)

## Phase 3 — Pre-panel audit (0.25 day)

Write `.reviews/v4.144.0/PRE_PANEL_AUDIT.md` — fact-check every
v4.144.0 claim (Cb.5-tests landed, Cb.6–Cb.10 evidence, new
benchmark numbers reproducible) against live file:line references.
Format: mirror `.reviews/v4.143.0/PRE_PANEL_AUDIT.md`.

## Phase 4 — Panel (0.5 day)

- Update `.reviews/prompt.md` TARGET VERSION to `v4.144.0` (already
  done at v4.143.0 tag).
- Spawn 7 reviewers in parallel (Rattler, Viper, Anaconda, Cobra,
  Coral, Boa, Mamba). Each writes `.reviews/v4.144.0/{01-07}*.md`.
- Wait for all 7 to complete.
- Write `.reviews/v4.144.0/README.md` with the verdict table,
  mechanical-rule application, and decision.
- If Option A fires: write `.reviews/v4.144.0/V5_DECISION.md` and
  prepare the `v5.0.0` tag.

## Phase 5 — Tag + commit (0.25 day)

```bash
# VERSION bump (Option A: 5.0.0; Option C: 5.0.0-rc2)
echo "5.0.0" > VERSION   # or "5.0.0-rc2"

# Rebuild artifacts with new version
make build-rt
python3 scripts/build_stage1.py

# Verification sweep (full quality gate)
ruff check . && black --check . && mypy mapanare/ runtime/
python3 scripts/check_docs_drift.py
python3 scripts/check_silent_skips.py tests/
python3 scripts/check_struct_registry.py
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -5
bash scripts/verify_fixed_point.sh --keep

# Commit
git add VERSION CHANGELOG.md CLAUDE.md README.md docs/ tests/ benchmarks/
git commit -m "v4.144.0: v5.0.0 gate attempt 4 — <Option A/C outcome>"
git tag v5.0.0   # or v5.0.0-rc2

# Push
git push origin dev
git push origin v5.0.0   # or v5.0.0-rc2
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Cb.5-tests: 7 new unit tests land in `tests/llvm/test_enum_inline.py` and pass | yes |
| 2 | Cb.6: typed-pointer-legacy guard added with named comment | yes |
| 3 | Cb.7: `clear_moved_owner_state` helper extracted, 6 call sites updated | yes |
| 4 | Cb.9: `module_path` resolution in self-hosted `semantic.mn` | yes |
| 5 | Cb.10: `66_qualified_type_ref.mn` docstring rewritten | yes |
| 6 | `benchmarks/FINAL_REPORT_v4.144.md` published with honest post-Bn.1 numbers | yes |
| 7 | `docs/roadmap/v4/v4.144.0/BASELINE.md` written | yes |
| 8 | README benchmark section updated | yes |
| 9 | Pre-panel audit written | yes |
| 10 | 7 reviewer files written to `.reviews/v4.144.0/` | yes |
| 11 | `.reviews/v4.144.0/README.md` with verdict + decision | yes |
| 12 | Mechanical rule applied verbatim — Option A, B, or C named | yes |
| 13 | Non-bootstrap pytest: ≥ 5,167 passed / 0 failed (+7 Cb.5-tests) | yes |
| 14 | Bootstrap pytest: 212 / 13 byte-identical | yes |
| 15 | Goldens: 54 / 66 | yes |
| 16 | Valgrind: 0 ERRORS | yes |
| 17 | ASan: 0 ASAN_ERROR | yes |
| 18 | Fixed-point within `DIFF_THRESHOLD=100` | yes |
| 19 | All 8 CI gates green | yes |
| 20 | VERSION file reflects decision (5.0.0 or 5.0.0-rc2) | yes |
| 21 | Tag pushed to origin (`v5.0.0` or `v5.0.0-rc2`) | yes |

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel opens new findings that push aggregate below 9.0 | medium | medium | Accept Option C outcome; document rationale; continue perf arc unchanged |
| A reviewer returns NEEDS WORK on a surface we didn't anticipate (WASM, mobile, GPU stdlib) | low | high | Option B fires; open recovery cycle; perf arc delayed by 1–2 releases |
| Cb.9 (self-hosted `module_path`) turns out to require a deeper semantic rewrite | medium | medium | Carry Cb.9 as Cb.9a / Cb.9b in the new ledger; don't block the panel on it — it's LOW |
| Benchmark refresh surfaces a new MEDIUM regression (e.g., an arm that was fast before is now slow) | low | medium | Name the regression, docket it, ship the honest numbers anyway; the panel values honesty over hidden debt |
| v4.144.0 slips past its 1–2 day estimate | low | low | It's a polish + panel release. Low architectural risk. Slippage costs calendar, not quality |

---

## What this release does NOT do

- No new language features, no new syntax, no new SPEC sections.
- No perf experiments (those start at v4.145.0).
- No WASM, mobile, or GPU stdlib work.
- No discretionary v5 tag override — the mechanical rule applies.
- No re-scoping of Own.1 (v5.x refactor) or other deferred items.

## Carry-forward after v4.144.0

Expected state:
- **0 CRITICAL / 0 HIGH / 0 MEDIUM / 1 LOW** (Own.1 — v5.x refactor, accepted as such).
- Remaining v4.143.0 panel LOW queue: empty.
- New carry-forwards from v4.144.0 panel: to be determined by reviewers.

Next release: **v4.145.0** — opens the perf arc with E1 (`enum_match`
codegen vs Rust). See `docs/roadmap/v4/v4.145.0/PLAN.md`.
