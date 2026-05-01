# v5.22.0 — RE-PANEL — terseness-arc closeout

**Status:** PLANNING
**Breaking:** No. Zero compiler / runtime / dispatch edits.
**Prerequisite:** v5.21.1 shipped (Mc.7 — pre-panel docs
hygiene; PRE_PANEL_AUDIT.md H.1–H.13 all closed).
**Estimated effort:** 1 session for the panel run + 0.5h for
the V5_DECISION + bump. Reviewers run in parallel.

---

## Why this exists

`.reviews/REVIEW_CADENCE.md` mandates a full 7-reviewer panel
**every 5 minor versions**. The last panel was v5.11.0
(2026-04-28). Counting from there:

- Routine cadence trigger fired at **v5.16.0** (5 minors past
  v5.11.0). Skipped — first cadence skip in project history.
- Cadence trigger fired again at **v5.21.0** (10 minors past
  v5.11.0). v5.22.0 closes the skip.

By the alternative trigger ("five language-feature releases
since the last panel"), the panel was due even earlier:

- **Te.1** (v5.14.0) — new keyword `pass`, new colon-block
  preprocessor
- **Te.2** (v5.15.0) — new AST nodes (Comprehension, terse
  lambdas, implicit-return shape)
- **Te.4** (v5.16.0) — `InterpString` AST changes
- **Te.5** (v5.20.0) — 5 new AST nodes (StructUpdate,
  LetDestructure, LetElse, IfLet, WhileLet)
- **Te.6** (v5.21.0) — `ChainedCompare` AST node, eq/cmp
  precedence merge

That's **5 language-feature releases**, the alternate cadence
threshold, hit by v5.20.0. v5.22.0 is **two independent triggers
overdue**.

This release is the panel cycle. **No compiler edits ship in
v5.22.0** — what the panel grades is the v5.11.0 → v5.21.1 arc
(which now includes the v5.21.1 hygiene work), so any new code
edits at this stage would shift the surface the panel measures.
Same posture as v5.8.0 (which graded v5.3.1 → v5.7.1, scored
9.66).

---

## Goals

1. Run the 7-reviewer panel against the v5.21.1 → v5.22.0
   surface using `.reviews/v5.22.0/prompt.md`.
2. Score the v5.13–v5.21 terseness arc.
3. Apply the mechanical decision rule:
   - Aggregate **≥ 9.0 AND 0 NEEDS WORK** → Option A (clean
     point release, ledger empty)
   - Aggregate **8.5 ≤ x < 9.0 AND 0 NEEDS WORK** → Option C
     (release ships with documented carry-forwards)
   - Aggregate **< 8.5 OR any NEEDS WORK** → Option B (open a
     v5.22.x recovery cycle)
4. Update `.reviews/CARRY_FORWARD.md` with the panel's findings
   delta from v5.11.0.
5. Reset cadence counter: next routine panel due at v5.27.0
   (5 minors past v5.22.0).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Pa.1** | HIGH | `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` already drafted at v5.21.0 close. Re-verify each H.1–H.13 closure against v5.21.1 HEAD; if any item is still open, hold the panel until v5.21.1 ships. | 30 min |
| **Pa.2** | HIGH | Spawn 7 reviewers per `.reviews/v5.22.0/prompt.md`. Parallel execution; reviewers do NOT see each other's output during review. | 1 session |
| **Pa.3** | HIGH | After all 7 reviews land, write `.reviews/v5.22.0/README.md` panel summary: verdict table, score trajectory (last 12 panels), per-axis improvement/regression vs v5.11.0, prioritized action items, disagreements, decision. | 1h |
| **Pa.4** | HIGH | If aggregate ≥ 9.0: write `.reviews/v5.22.0/V5_DECISION.md` Option A formal text. If 8.5–9.0: V5_DECISION.md Option C. If < 8.5 or any NEEDS WORK: skip V5_DECISION, queue the recovery PLAN as v5.22.1. | 30 min |
| **Pa.5** | MEDIUM | Update `.reviews/CARRY_FORWARD.md`: mark v5.11.0-panel items closed (Bo.18r, Bo.21, Bo.17r, Coral SPEC re-sync, Mc.\*, Pk.1.A, etc.); append new v5.22.0-panel items (if any). | 30 min |
| **Pa.6** | MEDIUM | `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md` documents the panel cycle: aggregate, per-reviewer scores + deltas, decision applied, carry-forward delta, cadence reset to v5.27.0. | 30 min |
| **Pa.7** | LOW | Bump VERSION 5.21.1 → 5.22.0; run `python3 scripts/bump_version.py 5.22.0`; CHANGELOG entry; CLAUDE.md release note. | 15 min |

---

## Phase plan

### Phase 0 — pre-panel verification

Before spawning reviewers, run the verification at v5.21.1 HEAD:

```bash
bash scripts/verify_fixed_point.sh --keep
# expected: 238,086 lines / 0 diff (preserved by v5.21.1's
# zero-compiler-edit posture)

python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95 (or 96+/96+ if v5.21.1 took Decision-1 Path A)

bash scripts/build_from_seed.sh
make lint
python3 scripts/check_changelog_honesty.py
```

Then re-verify each `PRE_PANEL_AUDIT.md` H.1–H.13 closure:

```bash
# H.1, H.2 — README staleness
grep -n "v5\.7\.1\|231,957\|80/80.*v5\.17" README.md docs/SPEC.md
# expected: NO hits

# H.3 — SPEC §4.0 mentions Te.3
grep -n "MAPANARE_NO_BRACE_WARNING\|soft.deprecat\|v5\.19" docs/SPEC.md
# expected: hits

# H.4 — broken promise closed
grep -n "deferred to v5\.21\.0" docs/SPEC.md
# expected: NO hits (replaced with v6.0 deferral or shipped)

# H.6 — localized READMEs body content
grep -n "v5\.7\.0 corpus\|66/66" docs/README.es.md docs/README.pt.md docs/README.zh-CN.md
# expected: NO hits (replaced with v5.21.0 status)

# H.7 — example present
ls examples/chained_cmp.mn
# expected: file exists

# H.9 — cross-bootstrap test present
ls tests/bootstrap/test_chained_cmp_mirror.py
# expected: file exists; 10/10 pass
```

If **any** check fails, **hold the panel** and finish v5.21.1
hygiene first.

### Phase 1 — spawn reviewers (parallel)

Per `.reviews/v5.22.0/prompt.md`:

| # | Reviewer | Output file | Domain |
|---|----------|-------------|--------|
| 1 | Rattler | `01-rattler.md` | LLVM IR / codegen |
| 2 | Viper | `02-viper.md` | Memory safety |
| 3 | Anaconda | `03-anaconda.md` | CI / testing / toolchain |
| 4 | Cobra | `04-cobra.md` | Bootstrap / self-hosted |
| 5 | Coral | `05-coral.md` | Language design |
| 6 | Boa | `06-boa.md` | Documentation / DX |
| 7 | Mamba | `07-mamba.md` | C runtime / performance |

All 7 spawn in parallel. They do not see each other's output
during review. Each must read `PRE_PANEL_AUDIT.md`,
v5.11.0 panel README, REVIEW_CADENCE.md, CARRY_FORWARD.md,
the 16 SESSION_REPORTs, and the 6 design docs before forming a
verdict.

### Phase 2 — panel summary

After all 7 review files land:

- Compile the verdict table (per-reviewer score, delta vs
  v5.11.0)
- Calculate aggregate (mean of 7 scores, 2 decimal places)
- Identify disagreements (any 0.3+ spread on the same axis)
- Surface the panel's prioritized action items
- Apply the mechanical decision rule
- Write `README.md` summary mirroring `.reviews/v5.11.0/README.md`
  format (verdict table, consensus, health gate, prioritized
  action items, disagreements, improvements, regressions,
  decision)

### Phase 3 — V5_DECISION (if applicable)

If aggregate ≥ 9.0: `.reviews/v5.22.0/V5_DECISION.md` carries
the Option A formal text. Format mirrors
`.reviews/v5.7.1/V5_DECISION.md`.

If 8.5 ≤ aggregate < 9.0: V5_DECISION.md carries Option C
(release ships with documented carry-forwards).

If aggregate < 8.5 OR any NEEDS WORK: skip V5_DECISION; queue
recovery cycle as `docs/roadmap/v5/v5.22.1/PLAN.md`.

### Phase 4 — ledger update

`.reviews/CARRY_FORWARD.md` gets:

- v5.11.0 panel items marked CLOSED with resolving release
  (Bo.18r → v5.21.1 H.1/H.2; Bo.21 → v5.21.0 bump_version
  sweep; Bo.17r → v5.21.1 H.6; Coral SPEC re-sync → v5.21.1
  H.2/H.3/H.5; Mc.\* → v5.18.0; Pk.1.A → status check)
- New v5.22.0-panel items appended, if any

### Phase 5 — closeout

- `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md`
- CHANGELOG `## [5.22.0]` entry summarizing the panel decision
- CLAUDE.md release note at top
- VERSION bumped 5.21.1 → 5.22.0
- bump_version sweep (badges + CHANGELOG comparison links)

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Aggregate < 9.0 — recovery cycle opens | LOW | v5.21.1 hygiene closes the docs-surface drift class that drove v5.11.0's -0.5; arc is structurally healthy on every metric |
| Reviewer returns NEEDS WORK on a v5.13–v5.21 claim that doesn't hold up | MEDIUM | PRE_PANEL_AUDIT.md is the lead's fact-check; reviewers verify, don't rediscover. Run a sanity pass before spawning |
| v5.21.1 doesn't ship before v5.22.0 panel — drift items show in panel | HIGH if v5.21.1 skipped | Hard prerequisite: v5.21.1 ships first or the panel is held |
| Disagreement between Boa (-0.5 risk on docs) and Coral (-0.1 risk on SPEC) creates a 0.5+ spread | LOW | Both axes converge on H.* items; v5.21.1 closes both; review prompt explicitly cross-references the spread to weight |
| Single-line `if x: y` Decision-1 chosen as Path A but ships with bugs | LOW | Path A scope is one Lark rule + one transformer line + one Self parser line; goldens verify; if buggy, take Path B at v5.21.1 |
| Cadence-skip pattern repeats — v5.27.0 panel also gets skipped | MEDIUM | Anaconda's review will explicitly grade the v5.16.0 skip; her recommendation should be a CI gate enforcing cadence |

---

## Success criteria

- All 7 review files land in `.reviews/v5.22.0/`
- Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A fires
- `.reviews/v5.22.0/README.md` summary written
- `.reviews/v5.22.0/V5_DECISION.md` (if Option A or C)
- `.reviews/CARRY_FORWARD.md` updated
- `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md` documents the
  cycle
- VERSION bumped to 5.22.0
- CHANGELOG + CLAUDE.md updated
- Strict 3-stage fixed point still 238,086 / 0 diff (preserved
  by zero-edit posture)
- Goldens 95+/95+ (preserved)
- Cadence counter reset for v5.27.0

---

## Out of scope (explicitly)

- **Compiler / runtime / dispatch edits.** Zero. v5.22.0 is the
  panel surface; any code edit shifts what the panel grades.
- **New language features.** Te.6 was v5.21.0; the next batch
  (if any) ships v5.23.0+.
- **Recovery work.** Only fires if the panel returns Option B.
  In that case, recovery PLAN lands at v5.22.1.
- **Tagging or pushing.** Awaits user approval per v5.20.1
  precedent.
- **v6.0 work.** Borrow checker / Rt.04 multi-level alias /
  `{}` hard removal — all v6.0 scope.

---

## What this panel CANNOT do

Per `.reviews/REVIEW_CADENCE.md` §"When this cadence itself
changes": panel CANNOT loosen the cadence. It can only:

- Pass: cadence resets to v5.27.0
- Pass-with-notes (Option C): cadence resets, but action items
  feed v5.22.1+ work
- Recovery (Option B): cadence shifts; next panel runs at the
  recovery-arc terminator

The lead cannot override.

---

## Score trajectory entering this panel

```
6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 → 9.37 → 9.30 →
9.66 → 9.62 → ?
```

Last 11 panels. v5.7.1 (9.66) is the project ceiling; v5.11.0
(9.62) is the most recent. The lead's stated target is **9.5+**.
Surpassing 9.66 is possible — every drift class Boa/Coral docked
at v5.11.0 is now closed at the source via v5.21.1 hygiene; the
strict-fixed-point streak is the longest in project history; the
self-host shrink (-13.8%) is unprecedented; the C runtime delta
is essentially flat. But the panel is not a coronation — Cobra's
per-PR fixed-point gate (3rd-time ask), Anaconda's cadence-skip
finding, and any new shapes the panel surfaces all push down.

A 9.65–9.70 result is the realistic best case. A 9.55–9.65
result is the expected case. Anything below 9.5 means a finding
the lead missed.

---

## After v5.22.0 ships

Next panel: **v5.27.0** (5 minors past v5.22.0). Routine
cadence; no special triggers expected unless v5.23.0–v5.26.0
adds 5+ language features.

Pending v6.0 work continues outside the panel cycle:
- Rt.04 multi-level alias analysis (borrow checker scope)
- `{}` hard removal (Te.3 v5.19.0 deprecation cycle terminus)
- Single-line `if x: y` if Decision-1 = Path B at v5.21.1
- Anything the v5.22.0 panel adds to the v6.0 list
