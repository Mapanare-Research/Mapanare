# v4.136.0 / v5.0.0-rc1 — Session Report

> **THE PANEL — v5 gate attempt 3: Option C.** First v5 candidate in
> the project's history. Aggregate 8.80/10 with 0 NEEDS WORK.
> `v5.0.0-rc1` tagged at this commit.

## Summary

Seven-reviewer panel (Rattler, Viper, Anaconda, Cobra, Coral, Boa,
Mamba) graded the v4.121.0 → v4.135.0 15-release closeout arc against
`docs/roadmap/v4/v4.135.0/MEASUREMENTS.md` (the canonical evidence
document, 505 lines, FINAL at v4.135.0) and
`.reviews/v4.136.0/PRE_PANEL_AUDIT.md` (fact-check overlay, 0 material
discrepancies across 13 SESSION_REPORTs).

**Result: aggregate 8.80/10, grade distribution 1 EXCEEDS / 6 MEETS /
0 NEEDS WORK.** The mechanical rule from `PLAN.md` (8.5 ≤ aggregate <
9.0 AND 0 NEEDS WORK → Option C) fires cleanly — **tag `v5.0.0-rc1`.**

This is the third v5 gate attempt. Attempt 1 (v4.99.0) aggregated
6.59; attempt 2 (v4.120.0) aggregated 8.21 with Anaconda at 7.6 NEEDS
WORK (CI/testing hygiene). The 15-release v4.121.0 → v4.135.0 closeout
arc between attempts 2 and 3 addressed every named finding from both
prior panels and closed all three historical v5 blockers:

1. **Cobra's v4.99.0 fixed-point blocker** — CLOSED v4.134.0. Strict
   3-stage `stage2.ll == stage3.ll`, md5
   `0c00ad07fee94f98bb350b359395843b`, 108,397 lines. Cobra
   independently re-ran `scripts/verify_fixed_point.sh --keep` in this
   panel; md5 matches byte-for-byte.
2. **Anaconda's v4.120.0 NEEDS WORK (CI/testing)** — CLOSED v4.133.0.
   39 → 0 non-bootstrap pytest failures; 4 cumulative flaky audits /
   20 total sequential runs / 0 flaky findings. Anaconda's grade
   moved from NEEDS WORK (7.6) to MEETS (8.9) — +1.3, the biggest
   delta on the panel.
3. **Viper's memory-safety baseline (Sh.2 extracted-alias drop-glue)**
   — CLOSED v4.131.0 LIST + v4.132.0 STRING. 23 → 0 ASan findings;
   valgrind ERRORS 31 → 5 (all residuals Ge.1 generics-init class,
   out-of-scope v5.x track).

## Phase 1 — Pre-panel sanity

`VERSION`: 4.136.0 (bumped at v4.135.0 commit per v4.133.0 Dr.2
precedent). `HEAD` commit is f9ae9cd (v4.135.0 release commit). `git
diff v4.135.0..HEAD -- mapanare/ runtime/ mapanare/self/` — empty.
`libmapanare_rt.a` sha256 `d896c83ca6d35677de83bdacfa90189d95475eacac32056c0f5b5e66c33859b9`
(byte-identical to v4.135.0 build). `mnc-stage1` 3,480,720 bytes.
SESSION_REPORTs v4.121.0–v4.135.0 all present except v4.131.0
(intentionally absent per PRE_PANEL_AUDIT — panel deferred, release
shipped Sh.2 LIST fix without SR).

No drift to investigate. v4.135.0 evidence is the canonical reference.

## Phase 2 — Seven reviewers in parallel

All seven reviewer agents launched in parallel as background agents;
each received a self-contained brief with required reading list, their
v4.120.0 prior review as anchor, domain focus, and output contract.
**No reviewer saw another's draft.** No mid-panel coordination.

| Reviewer | Domain | Prior (v4.120.0) | This panel | Δ | Grade |
|---|---|---:|---:|---:|---|
| Rattler | LLVM IR correctness | 8.3 PASS | **8.9** | +0.6 | MEETS |
| Viper | Memory safety | 8.4 PASS | **9.0** | +0.6 | MEETS |
| Anaconda | CI / testing | 7.6 **NEEDS WORK** | **8.9** | **+1.3** | MEETS |
| Cobra | Bootstrap / self-hosted | 7.9 PASS | **8.7** | +0.8 | MEETS |
| Coral | Language design | 8.1 PASS | **8.7** | +0.6 | MEETS |
| Boa | Documentation | 8.7 PASS | **8.4** | −0.3 | MEETS |
| Mamba | C runtime / performance | 8.5 PASS | **9.0** | +0.5 | **EXCEEDS** |
| | **Aggregate** | **8.21** | **8.80** | **+0.59** | — |

**Score trajectory:** v4.99.0 6.59 → v4.106.0 7.87 → v4.114.0 8.21 →
v4.120.0 8.21 → **v4.136.0 8.80**. The 8.21 plateau broke.

**Notable reviewer observations:**

- **Rattler** (LLVM) — Sh.2 fix at `emit_llvm_text.py::_do_copy`
  (lines 2572-2591 LIST + 2600-2609 STR) structurally sound. Held
  back from 9.0+ because byte-identity proves determinism not
  correctness; Ge.1 leaves 5 valgrind ERRORS; Sh.2 fix narrow
  (LIST+STR only — MAP/SIGNAL/STREAM Copy paths still call
  `_track_container` unconditionally). Opens SE.1 / Sh.2-residual
  docket.
- **Viper** (memory) — Sh.2 closure verified for all four
  alias-source cases (field-get, enum-payload, param, closure
  capture). Held at 9.0 (not higher) explicitly because **Ch.1**
  (`mapanare_agent_destroy` UAF) gates all three TSan test classes.
  Considered blocking, landed on carry-forward because the bug
  requires explicit anti-pattern (skip stop), all in-tree callers are
  correct, and it's ~5-line fix.
- **Anaconda** (CI/testing) — Every named v4.120.0 finding closed at
  the level she asked for. Ran her own lint reproducer: 204 ruff + 65
  black + 36 mypy at HEAD (An.2 still open, honestly docketed in
  `tests/test_ci.py:120-129`). 18 SKIP-dockets at v4.133.0 judged
  legitimate (each names symptom + fix route). Moved to MEETS at 8.9.
  **NEEDS WORK on An.2 alone would have been punitive** — her
  reasoning.
- **Cobra** (bootstrap) — Re-ran `bash scripts/verify_fixed_point.sh
  --keep` this session; exit 0, md5 matches byte-for-byte, stage2/3
  both 108,397 lines. mnc-stage2 actually runs a user program. The
  v4.99.0 blocker is **genuinely** closed, not cosmetically. Opens
  Cb.3 (mnc-stage2 `ulimit -s 65536` precondition) and Cb.5 (ABI
  divergence — Rt.1 `_enum_inline` in Python emitter only).
- **Coral** (language) — SPEC currency strongest in any panel he's
  reviewed. All 11 v4.129.0 edits present. Gr.1/Gr.2/Sem.1 are
  parse-time diagnostics, not silent miscompilation — not v5 blockers.
  -0.25 for §0 stale "legacy Python transpiler" phrasing (one-line
  fix).
- **Boa** (docs) — Sole negative delta. README badge stale (4.129.0
  vs live 4.136.0); `mapanare --version` prints `2.0.1` (pkg metadata
  drift); FINAL_REPORT link references v4.130; roadmap table ends
  v4.131.0; getting_started §5 says "39/65 golden tests" (live 53/65).
  SPEC currency holds; error messages still Rust-grade; cookbook
  intact. Bo.4-Bo.7 opened. No regression makes a new user write
  incorrect code — honest MEETS at 8.4.
- **Mamba** (runtime/perf) — Only EXCEEDS grade. `libmapanare_rt.a`
  byte-identical (sha256 `d896c83c…3859b9`, source tree zero commits
  in v4.121.0–v4.135.0 window). Rt.1 delivered beyond promise:
  `enum_match` 0.98× of Rust (Mapanare faster). Benchmark methodology
  honest (polluted run disclosed). All v4.120.0 docks closed. Flagged
  Ch.1 as HIGH but ceded scoring weight to Viper's memory-safety
  lens.

## Phase 3 — Aggregate and decision

Per `.reviews/v4.136.0/V5_DECISION.md`:

```
Sum: 8.9 + 9.0 + 8.9 + 8.7 + 8.7 + 8.4 + 9.0 = 61.6
Aggregate: 61.6 / 7 = 8.80
NEEDS WORK: 0
EXCEEDS: 1 (Mamba)
MEETS: 6
```

**Mechanical rule (from PLAN.md):**

| Rule | Condition | Applied? |
|---|---|---|
| Option A | Aggregate ≥ 9.0 AND 0 NEEDS WORK | ❌ 8.80 < 9.0 |
| **Option C** | **8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK** | ✅ |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | ❌ |

**Applied: Option C. Tag `v5.0.0-rc1` at this commit.**

## Phase 4 — Execute decision

- `VERSION` → `5.0.0-rc1`
- `CHANGELOG.md` `[5.0.0-rc1] - 2026-04-15` entry (panel summary +
  carry-forward ledger)
- `README.md` updated: version badge 4.129.0 → 5.0.0-rc1, benchmark
  link FINAL_REPORT_v4.130.md → FINAL_REPORT_v4.136.md (2 occurrences),
  benchmark numbers refreshed (46× → 42.6× faster than Python, 1.00× →
  1.12× of Rust, 4.52× → 4.86× slower than C), status note v4.129.0
  → v5.0.0-rc1, roadmap table extended v4.129.0 → v5.0.0-rc1 (10 rows
  added). (Bo.4 closure — Boa's flagged doc drift.)
- `CLAUDE.md` current-version section: v5.0.0-rc1 entry added at top;
  v4.135.0 entry kept; v5.0.0 tag description updated with attempt
  history (6.59 / 8.21 / 8.80).
- `docs/roadmap/ROADMAP.md`: new `## Where We Are (v5.0.0-rc1 …)`
  section added above v4.135.0's.
- `.reviews/v4.136.0/V5_DECISION.md` — formal decision document.
- `.reviews/v4.136.0/README.md` — panel summary.
- Bo.5 (`mapanare --version` prints `2.0.1`) not closed in this release
  — requires `mapanare/cli.py` source change, out of scope for panel
  discipline. Tracked as v5.0.0-final item.

## Verification

Zero compiler or runtime source changes in this release. Panel
discipline per PLAN.md — VERSION bump + documentation only.

| Metric | v4.135.0 | v5.0.0-rc1 | Status |
|---|---|---|---|
| Goldens (stage1) | 53 / 65 | 53 / 65 | byte-identical |
| Non-bootstrap pytest | 5,116 / 0 / 121 / 7 | (unchanged) | byte-identical |
| Bootstrap pytest | 212 / 13 | (unchanged) | byte-identical |
| Valgrind | 0 / 60 / 5 | (unchanged) | byte-identical |
| ASan | 54 / 0 / 11 | (unchanged) | byte-identical |
| Strict fixed-point md5 | `0c00…43b` | (unchanged) | byte-identical |
| `libmapanare_rt.a` sha256 | `d896…9b9` | (unchanged) | byte-identical |
| `mnc-stage1` size | 3,480,720 | (unchanged) | byte-identical |

## Carry-forward to v5.0.0 final

Full ledger in `.reviews/v4.136.0/V5_DECISION.md`. Summary:

- **HIGH (1):** Ch.1 — `mapanare_agent_destroy` UAF before
  `pthread_join`. ~5-line fix. Consensus across Viper/Anaconda/Mamba/Coral.
  TSan gate on C runtime dark until closed.
- **MEDIUM (4):** Bo.4 (README fully synced this release; keep
  localized Spanish/Chinese/Portuguese READMEs in sync), Bo.5
  (`mapanare --version` reads pkg metadata not VERSION file), Cb.5
  (Rt.1 enum ABI divergence Python vs self-hosted), Gr.2 (qualified
  type refs blocks stdlib/gpu modules).
- **LOW (9):** Sh.2-residual/SE.1, Dr.1, Cb.3, An.2, Sem.1, §0 SPEC
  stale line, Bo.1/Bo.2/Bo.3 (carried from v4.120.0).
- **v5.x feature track:** Sh.4–Sh.7 (self-hosted async/const/tensor/
  closure-typed), ABI.1, Ge.1 (5 valgrind ERRORS), TR.1/Bn.1/Rt.2/Rt.3/
  Tm.1 (v4.133.0 SKIP-dockets).

## Panel artifacts

- `.reviews/v4.136.0/01-rattler.md` — 8.9 MEETS
- `.reviews/v4.136.0/02-viper.md` — 9.0 MEETS
- `.reviews/v4.136.0/03-anaconda.md` — 8.9 MEETS
- `.reviews/v4.136.0/04-cobra.md` — 8.7 MEETS
- `.reviews/v4.136.0/05-coral.md` — 8.7 MEETS
- `.reviews/v4.136.0/06-boa.md` — 8.4 MEETS
- `.reviews/v4.136.0/07-mamba.md` — 9.0 EXCEEDS
- `.reviews/v4.136.0/V5_DECISION.md` — formal decision
- `.reviews/v4.136.0/README.md` — panel summary
- `.reviews/v4.136.0/PRE_PANEL_AUDIT.md` — fact-check overlay (sealed
  at v4.135.0)

## What this release did NOT do

Per PLAN.md §"What this release does NOT do":

- Did not change compiler or runtime source (no edits under
  `mapanare/*.py`, `runtime/native/*.c`, `mapanare/self/*.mn`).
- Did not override the mechanical rule.
- Did not re-run measurements (v4.135.0 did that; evidence is
  canonical).
- Did not extend the panel indefinitely (7 reviewers, 1 decision).
- Did not retroactively edit SESSION_REPORTs.

## The lead's call

Per `CLAUDE.md`: "**v5.0.0** (when ready) — Major version tag. **The
lead's call.**" The mechanical rule mandates the `v5.0.0-rc1` tag at
this commit. The transition from `-rc1` to a clean `v5.0.0` is the
lead's prerogative, subject to Ch.1 closure (and ideally Bo.5 +
localized-README sync).

## Outcome

**First v5 candidate in the project's history.** The 136-release
v4.x arc closes at v4.135.0. `v5.0.0-rc1` is real.

Tag created: `v5.0.0-rc1`.
