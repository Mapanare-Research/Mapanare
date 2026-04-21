# Mapanare v4.143.0 — THE PANEL (v5 gate attempt 4)

> Seven-reviewer panel. v5 gate attempt 4. The v4.137.0–v4.142.0
> six-release closeout arc is the surface graded. Target: aggregate
> ≥ 9.0 AND 0 NEEDS WORK → **Option A → tag `v5.0.0`** (clean, not
> rc).

**Status:** PLANNED
**Breaking:** No (panel release — no code changes except VERSION)
**Prerequisite:** v4.142.0 (Ge.1 closed, MEASUREMENTS.md FINAL)
**Full panel:** YES — 7 reviewers
**Estimated work:** 1 sprint
**Theme:** The arc earned its shot.

---

## The mechanical rule (unchanged from v4.136.0)

- **Option A — tag `v5.0.0`**: aggregate ≥ 9.0 AND 0 NEEDS WORK
- **Option C — tag `v5.0.0-rc2`**: 8.5 ≤ aggregate < 9.0 AND 0 NEEDS WORK
- **Option B — continue v4.144.0+**: aggregate < 8.5 OR any NEEDS WORK

No overrides. The numbers are the numbers.

Note: v5.0.0-rc1 is already tagged (v4.136.0). A second rc (rc2) is
still a net forward move — it tightens the remaining punch list — but
the v4.137.0–v4.142.0 arc specifically targeted the rc1 carry-forward,
so rc2 would mean the plan under-delivered. Aim for Option A.

---

## What the closeout arc delivered (v4.137.0 – v4.142.0)

Evidence the panel reads lives at `docs/roadmap/v4/v4.142.0/MEASUREMENTS.md`
(sealed FINAL at v4.142.0).

| Release | Delivered | Reviewer lifted |
|---|---|---|
| v4.137.0 | Ch.1 closed (runtime UAF, 3 TSan tests un-skipped) | Viper +0.3 |
| v4.138.0 | Bo.1–Bo.7 closed (docs sweep, `--version` fix) | Boa +0.5 |
| v4.139.0 | Gr.2 / Sem.1 / §0 / Co.1 / Dr.1 closed | Coral +0.4 |
| v4.140.0 | Cb.5 + SE.1 + Cb.3 closed (self-hosted parity) | Cobra +0.4, Rattler +0.2 |
| v4.141.0 | An.2 closed (lint 305→0); 5th flaky audit | Anaconda +0.3 |
| v4.142.0 | Ge.1 closed (valgrind 5→0); MEASUREMENTS.md FINAL | Rattler +0.1, Viper +0.2 |

---

## Phase 1 — Pre-panel sanity

```bash
echo "4.143.0" > VERSION
git log --oneline -10

# v4.142.0 is the reference; no code drift expected
git diff v4.142.0..HEAD -- mapanare/ runtime/ mapanare/self/
# Expected: empty

python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 2>&1 | tail -3
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
sha256sum runtime/native/libmapanare_rt.a
bash scripts/verify_fixed_point.sh --keep
md5sum /tmp/stage2.ll /tmp/stage3.ll

# Compare to v4.142.0 MEASUREMENTS.md — any drift? Pause panel, investigate.
```

## Phase 2 — Spawn 7 reviewers in parallel

Mirror v4.136.0 PROMPT.md Phase 2 structure. Seven reviewer agents in
parallel, each gets a self-contained brief:

- Read `docs/roadmap/v4/v4.142.0/MEASUREMENTS.md`
- Read `.reviews/v4.143.0/PRE_PANEL_AUDIT.md`
- Read their v4.136.0 prior review
- Read SESSION_REPORTs v4.137.0 – v4.142.0 (6 releases)
- No access to other reviewers' drafts during scoring

Per-reviewer focus:

### Rattler (LLVM IR)
- SE.1 (Sh.2-residual) fix shape in `_do_copy` for MAP/SIGNAL/STREAM
- Cb.5 (enum ABI parity Python vs self-hosted) — culebra diff 0
- Ge.1 (stack-init zero-fill) soundness
- Fixed-point still holds at new md5
- **Prior: 8.9. Target: ≥ 9.2.**

### Viper (memory safety)
- Ch.1 closure — `pthread_join` before free; 3 TSan classes pass
- Ge.1 closure — valgrind 5 → 0 ERRORS
- No new memory safety issues in the arc
- **Prior: 9.0. Target: ≥ 9.4.**

### Anaconda (CI / testing)
- An.2 (lint debt) — `make lint` exits 0
- 5th flaky audit — 25 cumulative runs, 0 flaky
- CI gate re-enabled (`tests/test_ci.py::test_lint_clean` passes)
- **Prior: 8.9. Target: ≥ 9.2.**

### Cobra (bootstrap / self-hosted)
- Cb.5 (Rt.1 port to self-hosted emitter) — culebra diff 0
- Cb.3 (ulimit precondition documented)
- Dr.1 (version string parameterized)
- Fixed-point still holds at new md5
- Self-hosted goldens ≥ 54/65 (or ≥ 58 if Sh.4 partially closed)
- **Prior: 8.7. Target: ≥ 9.0.**

### Coral (language)
- Gr.2 — qualified type refs (stdlib/gpu compiles clean)
- Sem.1 — module-level `let mut` diagnostic
- §0 SPEC stale line removed
- Co.1 — "compiles itself" wording precision
- **Prior: 8.7. Target: ≥ 9.0.**

### Boa (docs / DX)
- Bo.1–Bo.7 all closed
- `mapanare --version` prints live version
- Localized READMEs synced
- getting_started native prereqs + golden counts current
- docs/known_issues.md present
- **Prior: 8.4. Target: ≥ 8.9.**

### Mamba (C runtime / performance)
- `libmapanare_rt.a` byte-identical (still) — stable runtime surface
- Benchmarks refreshed at v4.142.0
- Fresh sanitizer sweeps pass
- Ch.1 fix validated (runtime-adjacent)
- **Prior: 9.0. Target: ≥ 9.0 (hold).**

## Phase 3 — Aggregate + decision

```bash
for f in .reviews/v4.143.0/NN-*.md; do
  grep -oE "Score: [0-9]+\.[0-9]+" "$f" | head -1
done | awk -F: '{s+=$2; n+=1} END {printf "Aggregate: %.2f/%d = %.2f\n", s, n, s/n}'

grep -l "Grade: NEEDS WORK" .reviews/v4.143.0/NN-*.md | wc -l
```

Apply mechanical rule:

```python
if aggregate >= 9.0 and needs_work_count == 0:
    decision = "A"     # v5.0.0 — CLEAN TAG
elif 8.5 <= aggregate < 9.0 and needs_work_count == 0:
    decision = "C"     # v5.0.0-rc2
else:
    decision = "B"     # continue v4.144.0+
```

Write `.reviews/v4.143.0/V5_DECISION.md` + `README.md` mirroring
v4.136.0 structure.

## Phase 4 — Execute decision

### Option A — v5.0.0 (clean tag)

```bash
echo "5.0.0" > VERSION

# README: v5.0.0 announcement block at top
# CHANGELOG: [5.0.0] entry summarizing the full v4.x arc (137 releases)
# CLAUDE.md: v5.0.0 entry
# ROADMAP.md: v5.x era opens

git add -A
git commit -m "v5.0.0: tagged after panel aggregate N.NN/10, 0 NEEDS WORK"
git tag v5.0.0
```

### Option C — v5.0.0-rc2

```bash
echo "5.0.0-rc2" > VERSION
# Document remaining items; tag rc2; plan v5.0.0 final
git commit -m "v5.0.0-rc2: panel aggregate N.NN/10, remaining punch list for v5.0.0"
git tag v5.0.0-rc2
```

### Option B — v4.144.0

```bash
echo "4.144.0" > VERSION
# Write docs/roadmap/v4/v4.144.0/PLAN.md addressing highest-priority finding
git commit -m "Bump VERSION to 4.144.0 (panel Option B, continue)"
```

## Phase 5 — Final commit

```bash
# Archive Culebra baseline + journal
culebra baseline save mapanare/self/main.ll
cp .culebra-journal.jsonl docs/roadmap/v4/v4.143.0/culebra-journal.jsonl
cp .culebra-baseline.json docs/roadmap/v4/v4.143.0/culebra-baseline.json

culebra journal add "v4.143.0 panel: [decision]" --action milestone --tags v4.143.0,panel,v5-gate
```

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Phase 1 sanity clean (no drift from v4.142.0) | yes |
| 2 | 7 reviews written and committed | yes |
| 3 | Aggregate score computed and recorded | yes |
| 4 | NEEDS WORK grades counted | yes |
| 5 | Mechanical rule applied (A/B/C) | yes |
| 6 | V5_DECISION.md + README.md at `.reviews/v4.143.0/` | yes |
| 7 | VERSION bumped per decision | yes |
| 8 | Git tag created (A: v5.0.0; C: v5.0.0-rc2; B: no tag) | yes |
| 9 | README + CHANGELOG + CLAUDE.md + ROADMAP.md updated per decision | yes |
| 10 | Culebra baseline + journal archived | yes |

---

## Forecast (for expectations, not the rule)

Per-reviewer at v4.143.0:

| Reviewer | v4.136.0 | Forecast | Driver |
|---|---:|---:|---|
| Rattler | 8.9 | **9.2** | SE.1 (v4.140), Ge.1 (v4.142) |
| Viper | 9.0 | **9.4** | Ch.1 (v4.137), Ge.1 (v4.142) |
| Anaconda | 8.9 | **9.2** | An.2 (v4.141) |
| Cobra | 8.7 | **9.1** | Cb.5 (v4.140), Dr.1 (v4.139) |
| Coral | 8.7 | **9.0** | Gr.2 + Sem.1 (v4.139) |
| Boa | 8.4 | **8.9** | Bo.1–Bo.7 (v4.138) |
| Mamba | 9.0 | **9.1** | Benchmark refresh (v4.142) |
| **Aggregate** | **8.80** | **~9.13** | → **Option A** |

That forecast lands Option A. Risk of slippage:
- **Boa target 8.9**: the Bo.* sweep covers all her items but she is
  demanding; realistic floor 8.7, ceiling 9.1. An 8.7 would drag
  aggregate to 9.1 (still Option A).
- **Cobra 9.1**: if Cb.5 self-hosted port is cosmetic rather than
  full ABI parity, could stay at 8.9, pulling aggregate to 9.1
  (still Option A).
- **Surprise finding**: a reviewer flags something not on the ledger.
  This is what PRE_PANEL_AUDIT.md mitigates; still possible.

**Realistic aggregate band: 9.0 – 9.2.** All within Option A.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Aggregate lands 8.95 (Option C again) | low | medium | Accept; rc2 is still a win; plan v5.0.0 final from rc2 punch list |
| One reviewer grades NEEDS WORK | low | **high** | PRE_PANEL_AUDIT catches known issues; reviewers briefed to be rigorous not punitive — honest ledger |
| Code drift since v4.142.0 | very low | high | Phase 1 verifies; pause panel if found, fix on a v4.143.0.1 branch, re-run Phase 1 |
| Reviewers miss the v4.137.0–v4.142.0 deltas | low | medium | Per-reviewer prompts list the exact SESSION_REPORTs + evidence files to read |
| v5.0.0 tag ships but lead wanted to defer | very low | low | Per CLAUDE.md, `v5.0.0` is "the lead's call." If lead says defer, ship Option A as `v5.0.0-rc2` instead and hold the clean tag. No panel override — decision stays above the rule. |

---

## What this release does NOT do

- Change the compiler or runtime (panel release).
- Override the mechanical rule.
- Re-run measurements (v4.142.0 is canonical).
- Retroactively edit any SESSION_REPORT.
- Extend the panel beyond 7 reviewers.

---

## Three shipping scenarios

### Option A — v5.0.0 ships
The v4.x line closes at 142 releases of code + v4.143.0 panel. 22
release closeout arc from v4.121.0 through v4.142.0 delivered every
named item from v4.99.0 + v4.120.0 + v4.136.0 panels. Largest
disciplined recovery in the project's history. Mapanare is v5.

### Option C — v5.0.0-rc2 ships
Rc2 narrows the ledger to ≤ 3 items. v5.0.0 final is one targeted
release away. The rc tag signals honest "almost" — it doesn't claim
what isn't there.

### Option B — v4.144.0 opens
Panel found a material gap the arc missed. Same cadence — PLAN,
PROMPT, SESSION_REPORT per release. The process that built 142
releases can build 143. The numbers are the numbers.

---

## After v4.143.0

### If Option A (v5.0.0)
- v4.x line closes
- v5.x opens (new era, new roadmap, new panel cadence)
- v5.0.0 shipped. Mapanare is v5.

### If Option C (v5.0.0-rc2)
- Punch list documented in V5_DECISION.md
- v5.0.0 final is the next release target (or one bridge release + v5.0.0)

### If Option B (continue)
- Gaps become v4.144.0+ scope
- Panel again after 5–10 releases
- Cadence preserved
