# Mapanare v4.136.0 — THE PANEL: v5 gate attempt 3

> **The panel.** Seven reviewers grade v4.121.0 through v4.135.0
> holistically. Mechanical rule applies. 136 releases deep. The v4.120.0
> panel returned 8.21 with 1 NEEDS WORK (Anaconda). The 15-release
> closeout arc that followed addressed every finding, including the
> Sh.2 bug class that was deferred four times. The evidence lives in
> v4.135.0/MEASUREMENTS.md. Now the reviewers decide.

**Status:** PLANNED
**Breaking:** No (panel release — no code changes except VERSION)
**Prerequisite:** v4.135.0
**Full panel:** YES — 7 reviewers (Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba)
**Estimated work:** 1 sprint
**Theme:** The numbers are the numbers. The process is the process.

---

## The mechanical rule

- **Option A — tag v5.0.0**: aggregate ≥ 9.0 AND 0 NEEDS WORK
- **Option C — tag v5.0.0-rc1**: aggregate ≥ 8.5 AND < 9.0 AND 0 NEEDS WORK
- **Option B — continue v4.137.0+**: aggregate < 8.5 OR any NEEDS WORK

No overrides. No pleading. No "but this time we tried really hard."
The numbers are the numbers. If the panel is below 9.0, we keep shipping.

---

## What the closeout arc delivered (v4.121.0 - v4.135.0)

Evidence the panel reads lives at `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md`
(and supporting reports).

- v4.121.0 — Closed 22 v4.117.0 audit-subset pytest failures (test hygiene, DWARF warning, trait fix)
- v4.122.0 — Qs.1 (List<Int> indexing in argument position) closed
- v4.123.0 — Dead-code sweep: -1,963 net lines (optimizer.py + TBAA)
- v4.124.0 — Rt.1 (unboxed enum payloads) closed; enum_match 2.31× speedup
- v4.125.0 — Benchmark refresh; 5× flaky audit (0 flaky)
- v4.126.0 — Golden test push: 27/65 → 39/65
- v4.127.0 — Self-hosted cosmetic convergence: 9,971 → 9,535 divergence lines
- v4.128.0 — Sh.8 + divergence M bucket fully closed
- v4.129.0 — SPEC + cookbook + guides sync
- v4.130.0 — Pre-panel prep (3rd flaky audit, valgrind + ASan sweeps, pre-panel audit)
- v4.131.0 — **Sh.2 List fix**: goldens 39 → 53/65, valgrind ERRORS 31 → 14, ASan findings 23 → 9
- v4.132.0 — **Sh.2 String fix**: targets goldens ≥ 58/65, valgrind ERRORS ≤ 6, ASan findings 0
- v4.133.0 — **An.1 reduction**: 38 → ≤ 15 pytest failures (Anaconda's NEEDS WORK finding closed)
- v4.134.0 — **Sh.11 fix**: fixed-point blocker closed (or documented with minimal reproducer)
- v4.135.0 — Pre-panel refresh: fresh measurements for everything the panel reads

---

## Phase 1 — Pre-panel sanity

The v4.135.0 sweeps are the canonical evidence. Phase 1 just confirms
they're still true on the v4.136.0 HEAD (which differs from v4.135.0
only in VERSION bump):

- [ ] `python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no` — same failure set as v4.135.0
- [ ] `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — same golden count as v4.135.0
- [ ] `sha256sum runtime/native/libmapanare_rt.a` — byte-identical to v4.135.0
- [ ] `git diff v4.135.0..HEAD -- mapanare/ runtime/ mapanare/self/` — empty
- [ ] CI green on the commit

If any of these drift: investigate, fix, or descope before running the panel.

## Phase 2 — Reviewer panel (7 independent reviews)

Spawn 7 independent reviewer agents in parallel (v4.120.0 precedent).
Each reviewer gets the same brief:

- Read `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md`
- Read `.reviews/v4.136.0/PRE_PANEL_AUDIT.md`
- Read every SESSION_REPORT from v4.121.0 through v4.135.0
- Read `.reviews/v4.120.0/<their_reviewer>.md` for their prior position
- Write their independent review at `.reviews/v4.136.0/NN-<reviewer>.md`

### Rattler — LLVM IR correctness

- Is the IR correct at `-O2`? Does it survive `opt -O2 → llc → clang → run`?
- v4.131.0 + v4.132.0 fix: is the `_do_copy` shape correct? Any new incorrectness introduced?
- v4.124.0 Rt.1 enum unboxing: is the representation sound at all sizes?
- Fixed-point (v4.134.0): if stage2 runs, is stage2 IR correct (llvm-as valid)?
- **Compare to v4.120.0 score (8.3)**: delta and reasons

### Viper — Memory safety

- Sanitizers clean? Valgrind (v4.135.0 report) ERRORS count, ASan findings count
- v4.131.0 + v4.132.0 closed the Sh.2 class — is the fix sound?
- Any new memory safety issues introduced in v4.121.0-v4.135.0?
- v4.122.0 list indexing fix — correct and safe?
- **Compare to v4.120.0 score (8.4)**: delta and reasons

### Anaconda — CI / Testing (v4.120.0 NEEDS WORK)

- `make test` — An.1 closed? Full pytest failure count ≤ 15?
- Four flaky audits (v4.117.0, v4.125.0, v4.130.0, v4.135.0) — all consistent 0 flaky?
- CI gates — all passing? Sanitizer CI jobs (v4.105.0) green?
- **Compare to v4.120.0 score (7.6 NEEDS WORK)**: this is THE domain that must pass

### Cobra — Bootstrap / Self-hosted

- Fixed-point — measured? v4.134.0 outcome?
- Self-hosted goldens through mnc-stage1 — ≥ 58/65?
- ABI stable? Enum unboxing ABI compat (v4.124.0)?
- The v4.112.0 byref fix — still correct? Regression-free?
- **Compare to v4.120.0 score (7.9)**: delta and reasons

### Coral — Language design

- Qs.1 closed (v4.122.0)? Rt.1 closed (v4.124.0)?
- SPEC current (v4.129.0 sync)?
- Any language-level gaps that would embarrass a v5 label?
- `const` keyword — recognized by parser (v4.126.0 fix)?
- **Compare to v4.120.0 score (8.1)**: delta and reasons

### Boa — Documentation / DX

- Documentation current (v4.129.0 sync, v4.133.0 test cleanups)?
- README reflects current state (v4.131.0 + v4.132.0 + v4.133.0 updates)?
- Getting-started guide works end-to-end on post-v4.135.0?
- Error messages useful?
- **Compare to v4.120.0 score (8.7 PASS)**: must stay ≥ 8.5

### Mamba — C runtime / Performance

- Dead code removed (v4.123.0)?
- Benchmark numbers honest (v4.135.0 refresh)?
- v4.124.0 Rt.1 perf delta real?
- Runtime clean under sanitizers?
- `libmapanare_rt.a` unchanged since v4.129.0?
- **Compare to v4.120.0 score (8.5 PASS)**: must stay ≥ 8.5

Each reviewer provides:
- Score 1-10
- Grade: MEETS / NEEDS WORK / EXCEEDS
- Specific findings with file:line references
- Carry-forward items (if any) with proposed release target
- Comparison to v4.120.0 score (delta + reasons)

## Phase 3 — Aggregate + decision

- [ ] Compute aggregate score (mean of 7)
- [ ] Count NEEDS WORK grades
- [ ] Apply mechanical rule → Option A / B / C
- [ ] Write `.reviews/v4.136.0/V5_DECISION.md` with:
  - Mechanical rule application (aggregate, NEEDS WORK count)
  - Per-reviewer score table + delta vs v4.120.0
  - Decision (A, B, or C)
  - Rationale (the mechanical rule, not vibes)
  - Carry-forward items from each reviewer
- [ ] Write `.reviews/v4.136.0/README.md` with panel summary table

## Phase 4 — Execute decision

### Option A (tag v5.0.0)
- Update `VERSION` to `5.0.0`
- Update `README.md` with v5 announcement
- Write `CHANGELOG.md [5.0.0]` summarizing v4.x arc (v4.0.0 → v4.136.0, 136 releases)
- Create git tag `v5.0.0`
- Update `CLAUDE.md` current version
- Update `docs/roadmap/ROADMAP.md` with v5 entry

### Option C (tag v5.0.0-rc1)
- Update `VERSION` to `5.0.0-rc1`
- Document remaining items for v5.0.0 final
- Tag `v5.0.0-rc1`
- Plan v5.0.0 final as next release (or v4.137.0 if remaining items are substantial)

### Option B (continue v4.137.0)
- Update `VERSION` to `4.137.0`
- Document panel findings in `docs/roadmap/v4/v4.137.0/PLAN.md`
- Preliminary PLAN addressing highest-priority NEEDS WORK finding
- Update `docs/roadmap/ROADMAP.md` with continued v4.x plan

## Phase 5 — Closeout

- [ ] `SESSION_REPORT.md` with panel outcome
- [ ] `CHANGELOG.md [4.136.0]` entry (or `[5.0.0]` if Option A)
- [ ] All 7 reviewer files + V5_DECISION.md + README.md committed under `.reviews/v4.136.0/`
- [ ] Roadmap status updates

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Pre-panel sanity clean | yes |
| 2 | 7 individual reviews written | yes |
| 3 | Aggregate score computed | yes |
| 4 | NEEDS WORK grades counted | yes |
| 5 | Mechanical rule applied | yes |
| 6 | V5_DECISION.md written | yes |
| 7 | VERSION bumped per decision | yes |
| 8 | Git tag created per decision | yes (A or C only) |
| 9 | README + CHANGELOG + CLAUDE.md updated per decision | yes |
| 10 | `.reviews/v4.136.0/README.md` panel summary | yes |

---

## What this release does NOT do

- Change the compiler or runtime (no `mapanare/`, `runtime/`, `mapanare/self/` edits)
- Override the mechanical rule
- Re-run measurements (v4.135.0 did that)
- Extend the panel indefinitely (7 reviewers, 1 decision)
- Retroactively edit SESSION_REPORTs (honesty > optimism)

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel aggregate comes in at 8.5-8.9 (Option C territory) | medium | medium | Mechanical rule: tag v5.0.0-rc1, continue. Not a defeat. |
| Panel aggregate < 8.5 or any NEEDS WORK | medium | high | Mechanical rule: Option B. Document findings, v4.137.0 addresses. |
| A reviewer discovers a material discrepancy in evidence | low | high | v4.135.0 pre-panel audit caught known issues; panel is free to flag new ones — note + factor in |
| Panel scoring spread is wide (one outlier vs rest) | low | low | 7 independent reviews reduce outlier impact; mechanical rule uses aggregate |
| A new regression is discovered mid-panel | very low | high | Phase 1 verifies; if found, pause panel, fix, re-run Phase 1 |

---

## Score delta forecast (inform expectations, not the rule)

Using v4.120.0 per-reviewer baselines:

| Reviewer | v4.120.0 | Expected v4.136.0 | Rationale |
|---|---:|---:|---|
| Rattler | 8.3 | 8.8 | Sh.2 closed (was "reproduced fresh"); Rt.1 correctness confirmed |
| Viper | 8.4 | 9.0 | Valgrind ERRORS 31 → 6, ASan 23 → 0 (if v4.132.0 lands), Sh.2 class closed |
| Anaconda | 7.6 ❌ | 8.5 | An.1 38 → ≤ 15 (target); 4 flaky audits consistent; CI gates stable |
| Cobra | 7.9 | 8.5 | Fixed-point measured (v4.134.0); goldens 53/65 → ≥ 58/65 |
| Coral | 8.1 | 8.5 | Qs.1 closed; SPEC current; const parser fixed; no new language gaps |
| Boa | 8.7 | 8.8 | Docs stayed current; slight polish; unlikely to jump much |
| Mamba | 8.5 | 8.7 | Dead code gone; benchmarks refreshed; runtime sanitizer-clean |
| **Aggregate** | **8.21** | **~8.69** | — |

That forecast would land Option C (≥ 8.5, < 9.0, 0 NEEDS WORK).

**To land Option A (≥ 9.0)**, three of the above need to clear 9.0
and none fall below 8.8. That's a stretch — panels don't hand out 9s
easily. The honest expectation is Option C: v5.0.0-rc1.

That's still a huge deal. It's the first time in the project's history
a v5 candidate ships. If Option C lands, v4.137.0 or v5.0.0-final closes
the remaining items and v5.0.0 becomes real.

---

## After v4.136.0

### If Option A (v5.0.0)
- v4.x line closes at 136 releases
- v5.x opens (new era, new roadmap, new panel cadence)
- v5.0.0 shipped: Mapanare is v5

### If Option C (v5.0.0-rc1)
- Remaining items documented in V5_DECISION.md
- Next release (v4.137.0 or v5.0.0) closes remaining; full v5.0.0 soon after
- Release candidate signals "almost" — honest

### If Option B (continue)
- Specific gaps documented by panel become v4.137.0+ scope
- Same cadence: PLAN.md, PROMPT.md, SESSION_REPORT.md per release
- Panel again after 5-10 releases (v4.142.0 or v4.146.0)
- The process that built 136 releases can build 137. The numbers are the numbers.
