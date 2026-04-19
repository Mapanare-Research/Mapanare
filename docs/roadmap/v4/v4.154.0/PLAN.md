# Mapanare v4.154.0 — THE PERF PANEL (v5.1.0 gate)

> **The perf panel.** Seven reviewers grade the v4.144.0 → v4.153.0
> arc holistically through a perf-focused lens. 10 releases of
> experiments, wins and dead ends recorded honestly, a trend graph
> spanning the arc, and the story defensibility this release lives
> or dies by. Mechanical rule applies verbatim. Aggregate ≥ 9.5 fires
> a clean `v5.1.0` tag (perf-version equivalent of v5.0.0's Option A);
> aggregate ≥ 9.0 AND 0 NEEDS WORK fires `v5.1.0` under the standard
> mechanical rule; below that, we ship what we have and continue.

**Status:** PLANNED
**Breaking:** No (panel release — no code changes except VERSION)
**Prerequisite:** v4.153.0 shipped (pre-panel refresh complete, 0 material discrepancies, MEASUREMENTS.md FINAL committed)
**Full panel:** YES — 7 reviewers (Rattler, Viper, Anaconda, Cobra, Coral, Boa, Mamba)
**Estimated work:** 1 day (panel execution) + pre-panel sanity (~1 hour)
**Theme:** The numbers are the numbers. The experiments are the experiments. The tag is whatever the rule says it is.

---

## The mechanical rule (perf-arc surface)

The project's v5-gate mechanical rule applies at this panel with one
added branch — a "strong perf story" tier for arc-wide aggregate ≥ 9.5:

| Rule | Condition | Outcome |
|---|---|---|
| **Option A′ (strong perf)** | Aggregate ≥ 9.5 AND 0 NEEDS WORK | Tag `v5.1.0` cleanly; publish arc-closeout blog post + marketing payload |
| **Option A (standard)** | 9.0 ≤ Aggregate < 9.5 AND 0 NEEDS WORK | Tag `v5.1.0` under the standard v5-gate rule; marketing payload framed honestly (not every experiment was a win) |
| **Option C** | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Tag `v5.1.0-rc1`; v4.155.0 closes remaining items before clean v5.1.0 |
| **Option B** | Aggregate < 8.5 OR any NEEDS WORK | No v5.1.0 tag; v4.155.0 opens as recovery cycle; perf arc's technical debt named in carry-forward |

No overrides. No "but the trend graph looks great." No "three EXCEEDS
reviewers override one NEEDS WORK." The aggregate is the aggregate;
the NEEDS WORK count is the NEEDS WORK count; the rule is the rule.

Precedent: `.reviews/v4.136.0/V5_DECISION.md` — the same rule fired
Option C at v4.136.0 (8.80, 0 NEEDS WORK → `v5.0.0-rc1`). We do the
same thing here, at the perf-arc gate.

## Score trajectory context (to inform expectations, not the rule)

| Panel | Aggregate | NEEDS WORK | Outcome |
|---|---:|---:|---|
| v4.99.0 | 6.59 | (recovery trigger) | Option B |
| v4.106.0 | 7.87 | 0 | Option B |
| v4.114.0 | 8.21 | 0 | Option B |
| v4.120.0 | 8.21 | 1 (Anaconda) | Option B |
| v4.136.0 | **8.80** | 0 | Option C (`v5.0.0-rc1`) |
| v4.143.0 | **8.86** | 0 | Option C (`v5.0.0-rc2` or similar; per that release's outcome) |
| **v4.154.0 forecast** | **~9.1** | **0 target** | **Option A (v5.1.0) target** |

The arc's +0.2 delta from v4.143.0 to v4.154.0 depends on:
- Mamba (+0.3 to 9.3 target): she's the C-runtime + perf reviewer.
  E6 async lever outcomes + E7 allocator outcomes land directly in
  her domain. If E6 closes to ≤ 1.2× Go and E7 delivers +30 %, she
  hits 9.3.
- Rattler (+0.2 to 9.1): IR correctness under E3 noalias + E8 MIR
  passes. Stable iff sanitizers stayed zero across all experiments.
- Cobra (+0.1 to 8.8): fixed-point held through all E-releases.
- Other four (Viper / Anaconda / Coral / Boa): ~flat, each in [8.8, 9.0].

Aggregate 9.1 is the honest forecast. 9.5 is a stretch goal that
requires three reviewers at 9.5+ and none below 8.8.

## What the arc delivered (v4.144.0 → v4.153.0)

Evidence the panel reads lives at
`docs/roadmap/v4/v4.153.0/MEASUREMENTS.md` (canonical) and
`docs/roadmap/v4/PERF_EXPERIMENTS.md` (experiment ledger).

| Release | Theme | Outcome (summary) |
|---|---|---|
| v4.144.0 | LOW polish + baseline + v5.0.0 panel | Bn.1 harness trustworthy, benchmark baseline captured, v5.0.0 gate attempt (Option A/C per that release) |
| v4.145.0 | E1 `enum_match` codegen vs Rust | Win / dead end / partial |
| v4.146.0 | E2 `fib_recursive` ABI | — |
| v4.147.0 | E3 parameter-level `noalias` | — |
| v4.148.0 | E4 `string_concat` vs Rust | — |
| v4.149.0 | E5 ABI.1 struct-return | — |
| v4.150.0 | E6 async agent pipeline vs Go | — |
| v4.151.0 | E7 allocator hot path | — |
| v4.152.0 | E8 dormant MIR pass re-evaluation | — |
| v4.153.0 | Pre-panel refresh (6th flaky audit, MEASUREMENTS.md FINAL, TREND_v4.144_v4.153.md) | 30 sequential runs / 0 flaky; 0 material discrepancies |

The panel reads all of these in sequence. Dead ends count as credible
negative results; wins count as credible positive results; partial
outcomes count as honestly-scoped engineering. What the panel *does
not* tolerate is a claim in SESSION_REPORT.md that Phase 5 pre-panel
audit found to be a material discrepancy — v4.153.0's audit target is
0, and the panel will flag any they find.

## Phase 1 — Pre-panel sanity (~1 hour)

The v4.153.0 sweeps are canonical evidence. Phase 1 confirms they're
still true on the v4.154.0 HEAD (which differs from v4.153.0 only
in VERSION bump):

- [ ] `python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no` — same failure set as v4.153.0 (expect 0 failures)
- [ ] `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — 54/66 goldens
- [ ] `sha256sum runtime/native/libmapanare_rt.a` — record (will change due to 4.154.0 VERSION embed, that's expected)
- [ ] `git diff v4.153.0..HEAD -- mapanare/ runtime/ mapanare/self/` — empty (no source changes, only VERSION)
- [ ] `md5sum /tmp/stage2.ll /tmp/stage3.ll` — fixed-point within `DIFF_THRESHOLD=100`
- [ ] All 8 CI gates green on the commit

If any drift: investigate, fix, or descope before running the panel.

## Phase 2 — Reviewer panel (7 independent reviews, ~0.5 day)

Spawn 7 independent reviewer agents in parallel. Each gets the same
brief + reads the same artifacts. Each writes
`.reviews/v4.154.0/NN-<reviewer>.md`.

### Each reviewer reads (common brief)

- `.reviews/prompt.md` (TARGET VERSION: `v4.154.0`, PERF FOCUS: yes)
- `.reviews/v4.143.0/<their-codename>.md` (their prior review at the
  last panel — establishes their delta baseline)
- `.reviews/v4.154.0/PRE_PANEL_AUDIT.md` (v4.153.0 output)
- `.reviews/CARRY_FORWARD.md` (current ledger)
- `docs/roadmap/v4/v4.153.0/MEASUREMENTS.md`
- `docs/roadmap/v4/v4.153.0/DOCKET_LEDGER.md`
- `benchmarks/FINAL_REPORT_v4.153.md`
- `benchmarks/TREND_v4.144_v4.153.md`
- `docs/roadmap/v4/PERF_EXPERIMENTS.md`
- `docs/roadmap/v4/PERF_ARC_PLAN.md` (arc-level framing)
- Every SESSION_REPORT v4.144.0 through v4.153.0

### Per-reviewer focus (perf-arc surface)

**Rattler — LLVM IR correctness (expected domain delta: +0.2)**
- Did E1–E4 IR-level experiments produce correct IR at -O0 through
  -O3? Any invalid IR introduced?
- E3 `noalias` metadata placement — safe? No mis-annotated aliasing?
- E8 MIR pass re-enables — any pass-interaction IR bug?
- Compare to v4.143.0 score

**Viper — Memory safety (expected domain delta: 0, hold)**
- Sanitizer state at v4.153.0: 0 ERRORS valgrind, 0 ASAN_ERROR
- E6 scheduler changes — any new race? Ch.1 TSan classes still green?
- E7 `realloc` lever — no UAF / double-free reintroduced?
- E8 MIR pass re-enables — no use-after-move?
- Compare to v4.143.0 score

**Anaconda — CI / testing (expected domain delta: 0, hold ≥ 8.8)**
- 30 cumulative sequential pytest runs, 0 flaky (6th audit)
- CI gates green across all E-releases
- Test coverage for new codegen paths (E1 enum_match, E3 noalias, E5 ABI.1)
- Compare to v4.143.0 score

**Cobra — Bootstrap / self-hosted (expected domain delta: +0.1)**
- Fixed-point held through all 10 arc releases?
- E8 MIR pass re-enables — bootstrap stage1/stage2 parity?
- Self-hosted goldens — still 54/66?
- ABI stability (E5 struct-return lowering — safe for self-hosted parity?)
- Compare to v4.143.0 score

**Coral — Language design (expected domain delta: 0, hold)**
- Any arc experiment broke a language promise? (SPEC compliance)
- E1 enum_match — Shape enum behavior preserved, no subtle semantic shift?
- E7 `realloc` value-type predicate — semantically sound?
- Compare to v4.143.0 score

**Boa — Documentation / DX (expected domain delta: +0.1)**
- Arc documentation quality — BASELINE.md / IR_DIFF.md / HYPOTHESIS.md
  / RESULTS.md / SESSION_REPORT.md present and honest for every
  E-release?
- `PERF_EXPERIMENTS.md` credibility — dead ends named honestly?
- `docs/PERF.md` landing page shipped? README perf section current?
- Compare to v4.143.0 score

**Mamba — C runtime / performance (expected domain delta: +0.3, the arc's lead scorer)**
- The arc's canonical reviewer. Reads TREND_v4.144_v4.153.md cover
  to cover
- Cross-language geomean — closed ≤ 1.5× Rust? (target)
- Async geomean — closed ≤ 1.2× Go? (target) Or ≤ 1.4× with honest
  narrative? (acceptable)
- E6 scheduler + E7 allocator — deltas real and defensible?
- `libmapanare_rt.a` still sanitizer-clean?
- Compare to v4.143.0 score

### Per-reviewer output format

Each reviewer writes their review in the same shape used at v4.136.0
and v4.143.0:

```markdown
# Panel v4.154.0 — <Codename> (<Domain>)

**Score:** X.Y / 10
**Grade:** EXCEEDS / MEETS / NEEDS WORK
**Delta vs v4.143.0:** +/- 0.N

## Summary
[2-3 sentences]

## What improved since v4.143.0
- [specific, cite file/line/benchmark]

## What held
- [specific]

## What concerns me
- [specific, with proposed docket ID + severity if any]

## Carry-forward (for v5.1.1 / v5.2.x)
- [docket ID] [severity] [one-line scope]
```

## Phase 3 — Aggregate + mechanical-rule decision (~0.5 hour)

- [ ] Compute aggregate (mean of 7)
- [ ] Count NEEDS WORK grades
- [ ] Apply the mechanical rule → Option A′ / A / B / C
- [ ] Write `.reviews/v4.154.0/V5_1_0_DECISION.md` (or `V5_DECISION.md`
      if preferred; naming mirrors v4.136.0's `V5_DECISION.md` precedent)
- [ ] Write `.reviews/v4.154.0/README.md` with the verdict table

The decision doc format mirrors `.reviews/v4.136.0/V5_DECISION.md`:
- Score (aggregate + distribution)
- Decision rule table (which option fires)
- Per-reviewer scores table (v4.143.0 → v4.154.0 delta)
- Score trajectory (v4.99.0 → v4.154.0)
- What the option means (tag / next release)
- Carry-forward items (severity-ranked)

## Phase 4 — Execute decision

### Option A′ (v5.1.0, strong perf)

- `echo "5.1.0" > VERSION`
- Write `CHANGELOG.md [5.1.0]` summarizing the arc: 8 experiments,
  wins, dead ends, benchmark deltas, sanitizer state
- Create git tag `v5.1.0`
- `README.md` v5.1.0 announcement + updated benchmark claims
- Update `CLAUDE.md` current version
- Update `docs/roadmap/ROADMAP.md` with v5.1.0 entry
- Write `docs/roadmap/v4/v4.154.0/PERF_ARC_CLOSEOUT.md` — the
  arc-closeout doc the marketing payload references
- Queue marketing payload: 4 blog posts, trend graph svg, `docs/PERF.md`

### Option A (v5.1.0, standard)

Same as Option A′ but the CHANGELOG + arc closeout honestly frame
outcomes ("8 experiments, N wins, M dead ends, honest story"). Tag
`v5.1.0`. Marketing payload ships with the honest framing.

### Option C (v5.1.0-rc1)

- `echo "5.1.0-rc1" > VERSION`
- Document remaining items in `V5_1_0_DECISION.md` "what must close"
  section
- Tag `v5.1.0-rc1`
- v4.155.0 opens as the closer release (mirrors v4.137.0 / v4.138.0
  pattern from the v5.0.0-rc1 arc)

### Option B (recovery)

- `echo "4.155.0" > VERSION`
- Document panel findings in `docs/roadmap/v4/v4.155.0/PLAN.md`
  (preliminary PLAN addresses highest-priority NEEDS WORK finding)
- Update `docs/roadmap/ROADMAP.md` with continued v4.x plan
- No v5.1.0 tag created

## Phase 5 — Closeout

- [ ] `SESSION_REPORT.md` with panel outcome + carry-forward + decision log
- [ ] `CHANGELOG.md` entry (`[4.154.0]` or `[5.1.0]` per outcome)
- [ ] All 7 reviewer files + V5_1_0_DECISION.md + README.md committed under `.reviews/v4.154.0/`
- [ ] `PERF_ARC_CLOSEOUT.md` written (Options A′ / A only)
- [ ] Marketing payload queued (A′ / A only)
- [ ] Roadmap status updates

---

## Exit criteria

| # | Check | Required |
|---|---|---|
| 1 | Pre-panel sanity clean | yes |
| 2 | 7 individual reviews written | yes |
| 3 | Aggregate score computed | yes |
| 4 | NEEDS WORK grades counted | yes |
| 5 | Mechanical rule applied verbatim | yes |
| 6 | Option named (A′ / A / B / C) | yes |
| 7 | `V5_1_0_DECISION.md` written | yes |
| 8 | VERSION bumped per decision | yes |
| 9 | Git tag created per decision | yes (A′ / A / C only) |
| 10 | README + CHANGELOG + CLAUDE.md updated per decision | yes |
| 11 | `.reviews/v4.154.0/README.md` panel summary committed | yes |
| 12 | If A′ / A: `PERF_ARC_CLOSEOUT.md` written | conditional |
| 13 | If A′ / A: `docs/PERF.md` landing page published | conditional |
| 14 | `SESSION_REPORT.md` written | yes |
| 15 | Non-bootstrap pytest 5,160+ / 0 | yes |
| 16 | Bootstrap pytest 212 / 13 byte-identical | yes |
| 17 | Goldens 54 / 66 | yes |
| 18 | Valgrind 0 ERRORS, ASan 0 ASAN_ERROR | yes |
| 19 | Fixed-point within `DIFF_THRESHOLD=100` | yes |
| 20 | All 8 CI gates green | yes |
| 21 | Tag pushed to origin | yes |

---

## What this release does NOT do

- Change the compiler or runtime (no `mapanare/`, `runtime/`,
  `mapanare/self/` edits — VERSION bump only)
- Override the mechanical rule
- Re-run measurements (v4.153.0 did that)
- Extend the panel indefinitely (7 reviewers, 1 decision, 1 day)
- Retroactively edit SESSION_REPORTs (honesty > optimism)
- Add new benchmarks mid-panel (the arc corpus is sealed)
- Promote a dead-end lever to a win post-hoc

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel aggregate comes in at 8.5–8.9 (Option C territory) | medium | medium | Mechanical rule fires `v5.1.0-rc1`; v4.155.0 closes remaining items. This is the v5.0.0-rc1 pattern — not a defeat, just honest RC framing |
| Panel aggregate < 8.5 or any NEEDS WORK | low | high | Mechanical rule fires Option B. Document findings; v4.155.0 opens as recovery; arc's marketing payload is held until the recovery cycle closes |
| Mamba grades the async gap (E6) as under-delivering — Option A blocked by her alone | medium | medium | Her grade is the arc's lead signal. If E6 didn't close, the honest story (documented in v4.150.0 RESULTS.md) is the defense — "1.4× Go is still Go-class," not "we failed." If she still scores < 9.0, accept Option C |
| A reviewer discovers a material discrepancy the pre-panel audit missed | low | high | v4.153.0 PRE_PANEL_AUDIT.md target was 0 material; if panel finds one, flag it, note the audit gap in README, continue to decision |
| Panel scoring spread is wide (one outlier 8.5, others 9.5) | low | low | 7 independent reviews reduce outlier impact; mechanical rule uses aggregate only |
| Ch.1 TSan class regressed during E6 and nobody noticed | very low | critical | Phase 1 sanity includes the Ch.1 canary — `python3 -m pytest tests/native/test_c_hardening.py`. If it's red, pause panel and fix before review |

---

## After v4.154.0

### If Option A′ (v5.1.0, strong perf)
- Arc marketing payload publishes: 4 blog posts (one per week),
  `docs/PERF.md` landing page, trend graph svg, HN submission
- `v5.1.0` carries the perf story; `v5.0.0` remains the engineering arc
- Next arc opens based on external signal (adoption → ecosystem,
  criticism → correctness, quiet → polish)

### If Option A (v5.1.0, standard)
- Same as A′ but marketing framing is "honest wins, named dead ends"
- Blog posts shipped with that framing
- Still a clean `v5.1.0` tag

### If Option C (v5.1.0-rc1)
- Remaining items documented in V5_1_0_DECISION.md
- v4.155.0 closes the named items (~1–2 releases estimated)
- Clean v5.1.0 tag shortly after

### If Option B (recovery)
- v4.155.0+ addresses highest-priority NEEDS WORK finding
- Panel re-runs after 3–5 releases when the finding is closed
- Arc marketing payload held pending clean gate

---

## The arc in one paragraph (for SESSION_REPORT framing)

The v4.144.0 → v4.153.0 arc executed 8 perf experiments with
documented hypotheses, IR diffs, and results per release. Wins and
dead ends were recorded in `PERF_EXPERIMENTS.md` as they landed. The
6th flaky audit confirmed 30 sequential runs with 0 flaky findings.
The benchmark trend closed the Rust gap toward ≤ 1.5× on the
cross-language geomean and — depending on E6 outcome — closed the Go
gap toward ≤ 1.2× on async. The panel reads this evidence and decides
whether the arc's artifact quality, delta magnitude, and narrative
defensibility merit a clean `v5.1.0` tag. Whatever the decision, the
project ships the honest number: that discipline is what made v5.0.0
a clean tag, and it's what makes v5.1.0 one too, whenever the rule
fires it.
