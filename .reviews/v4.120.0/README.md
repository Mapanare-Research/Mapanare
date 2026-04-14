# v4.120.0 Panel — Final Panel of the v4.x Extended Line

> Seven-reviewer panel. v5 gate attempt 2. The v4.100.0 – v4.119.0
> recovery arc (20 releases across six phases) is the surface
> graded.

**Panel date:** 2026-04-14
**Aggregate: 8.21 / 10**
**Verdict breakdown: 2 PASS / 4 PASS WITH NOTES / 1 NEEDS WORK**
**Decision rule applied: Option B — continue v4.121.0+**

---

## Individual scores

| Reviewer | Domain | Score | Verdict | Δ vs v4.114.0 |
|---|---|---:|---|---:|
| [Rattler](01-rattler.md) | LLVM / codegen | **8.3** | PASS WITH NOTES | +0.1 |
| [Viper](02-viper.md) | Memory safety | **8.4** | PASS WITH NOTES | +0.1 |
| [Anaconda](03-anaconda.md) | CI / testing | **7.6** | **NEEDS WORK** | −0.2 |
| [Cobra](04-cobra.md) | Bootstrap / self-hosted | **7.9** | PASS WITH NOTES | −0.1 |
| [Coral](05-coral.md) | Language design | **8.1** | PASS WITH NOTES | −0.2 |
| [Boa](06-boa.md) | Documentation | **8.7** | **PASS** | +0.2 |
| [Mamba](07-mamba.md) | C runtime / performance | **8.5** | **PASS** | +0.3 |
| | **Aggregate** | **8.21** | — | 0.00 |

Score trajectory v4.99.0 → v4.106.0 → v4.114.0 → v4.120.0:
**6.59 → 7.87 → 8.21 → 8.21**

The recovery arc closes at the same aggregate as the Phase D panel.
Phase E + F's work (async I/O demos, documentation batch, testing
sweep, final benchmark, retrospective) **held the line** against
the additional scrutiny this panel brought (full pytest run,
`make lint` status, `verify_fixed_point.sh` blocker). The two PASS
verdicts (Boa documentation, Mamba performance) reflect new work
landing well; the one NEEDS WORK (Anaconda CI / testing) reflects
scope gaps in the v4.117.0 flaky audit that this panel uncovered.

## Mechanical decision rule

From `.reviews/v4.99.0/V5_DECISION.md` and `POST_RECOVERY_MASTER_
PROMPT.md`:

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Tag `v5.0.0` | ❌ 8.21 < 9.0 |
| Option C | 8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK | Tag `v5.0.0-rc1` | ❌ Aggregate below 8.5 AND 1 NEEDS WORK |
| **Option B** | **Aggregate < 9.0 OR any NEEDS WORK** | **Continue v4.121.0+** | ✅ **both conditions match** |

**Applied: Option B.** v5.0.0 is **not** tagged at v4.120.0.

### Lead directive overlay (not in conflict)

Per the session lead's explicit directive at this release: v5 would
not be tagged at v4.120.0 regardless of panel outcome. The
mechanical rule independently produced Option B; the lead directive
produced the same outcome. No override was needed.

The lead's authority to defer the v5 tag beyond what the mechanical
rule alone recommends is documented in `CLAUDE.md`:

> "**v5.0.0** (when ready) — Major version tag. **The lead's call.**
> Zero additional work required — v4.76.0 is release-gate quality."

"The lead's call" encompasses "not tagged even if the rule would
have allowed it." That clause is exercised here.

## What panels agreed on

**Every reviewer flagged the same three items for v4.121.0+:**

1. **Qs.1 — `List<Int>` indexing** in argument position (Rattler,
   Viper, Mamba all reproduced today; Coral referenced)
2. **`make lint` red** on dev (Rattler: −0.2 points; Anaconda:
   −0.2 points; Boa implicitly)
3. **README precision on self-hosted wording** (Cobra, Coral
   explicitly; Boa would accept as polish)

Secondary consensus:

- **Sh.8 fixed-point blocker** (Cobra, Rattler) is documented but
  should close before the next v5 gate
- **Rt.1 boxed-enum overhead** (Mamba primary, Rattler secondary)
  is the biggest performance lift available

## What panels disagreed on

- **Anaconda** is the only NEEDS WORK: cites 51 uncatalogued pytest
  failures plus lint debt. Other reviewers acknowledge the lint debt
  but absorbed it into small deductions rather than verdict-change.
- **Cobra** and **Coral** both want README precision on
  self-hosting; **Boa** accepts it as polish, not blocker.
- **Viper** opens a new docket (**ASan.1** — `mn_list_rc` UAF
  bucket of 12 findings); other reviewers' scorecards do not reference
  this.

## Aggregate-gap analysis (v4.114.0 → v4.120.0)

The aggregate held at 8.21, but the composition changed:

- **+0.3 Mamba** (async I/O demos + benchmark report)
- **+0.2 Boa** (six documents shipped in Phase E/F)
- **+0.1 Rattler** (Phase E polish without IR regression)
- **+0.1 Viper** (TSan extension to async demos)
- **−0.1 Cobra** (Anaconda's finding about uncatalogued failures crosses domains)
- **−0.2 Coral** (docs precision items surfaced)
- **−0.2 Anaconda** (full pytest suite reveals 51 extra failures outside the v4.117.0 audit scope)

Net: **+0.2** from Boa + Mamba gains, **−0.2** from Anaconda +
Coral drops. Aggregate unchanged.

This is a **stable panel**. The recovery arc has reached a quality
ceiling that the remaining open items (Rt.1, Qs.1, Sh.8, Sh.2,
lint, An.1 flaky-scope) must close before the score moves.

## Carry-forward items opened by this panel

From per-reviewer carry-forwards:

### HIGH / MEDIUM (block the next v5 gate)

- **Qs.1** (existed; now reproduced by panel) — `List<Int>` indexing in argument position
- **An.1** (new) — 51 uncatalogued pytest failures outside v4.117.0 audit scope
- **An.2** (new) — lint debt (64 black, 204 ruff, 34 mypy)
- **An.3** (new) — `test_fibonacci_run` regression (cause unknown)
- **Sh.8** (existed) — self-hosted `semantic.mn` None/Some/Ok ctor registration blocks fixed-point
- **Rt.1** (existed) — boxed-enum payload overhead, `enum_match` 2× slower than Rust

### LOW / polish

- **ASan.1** (new, Viper) — `mn_list_rc` UAF baseline bucket review
- **Cb.1** (new, Cobra) — README + SPEC precision on "self-hosted"
- **Cb.2** (new, Cobra) — GOLDEN_FAILURES.md refresh footer
- **Co.1** (new, Coral) — README precision on "compiler compiles itself"
- **Co.2** (new, Coral) — struct-literal-syntax decision (grammar or delete tests)
- **Co.3** (new, Coral) — `const` keyword direction (implement or remove)
- **Co.4** (new, Coral) — SPEC §29 + contract programming precision
- **Bo.1** (new, Boa) — `docs/known_issues.md` user-facing limitations
- **Bo.2** (new, Boa) — getting-started "prerequisites for native mode"
- **Bo.3** (new, Boa) — STATISTICS.md pre-v3.33.0 panel footnote
- **Instr.1** (existed) — Culebra scan over 854K-line main.ll (Rattler observed it completes today)

## Per-reviewer files

- [01-rattler.md](01-rattler.md) — LLVM / codegen — 8.3 PASS WITH NOTES
- [02-viper.md](02-viper.md) — Memory safety — 8.4 PASS WITH NOTES
- [03-anaconda.md](03-anaconda.md) — CI / testing — **7.6 NEEDS WORK**
- [04-cobra.md](04-cobra.md) — Bootstrap / self-hosted — 7.9 PASS WITH NOTES
- [05-coral.md](05-coral.md) — Language design — 8.1 PASS WITH NOTES
- [06-boa.md](06-boa.md) — Documentation — **8.7 PASS**
- [07-mamba.md](07-mamba.md) — C runtime / performance — **8.5 PASS**

## Outcome

- **v5.0.0 NOT tagged.** Option B applies (mechanical rule) and is
  independently confirmed by lead directive.
- **v4.121.0 opens** as the next release.
- The panel's carry-forward items (17 tracked above) become v4.121.0+
  scope.
- The next v5 gate is v4.130.0 per the proposed roadmap. Until then,
  the cadence continues: one release per sprint, PLAN + PROMPT +
  SESSION_REPORT + CHANGELOG + tests.

See [V5_DECISION.md](V5_DECISION.md) for the formal decision text.
See [docs/roadmap/v4/v4.121.0/PLAN.md](../../docs/roadmap/v4/v4.121.0/PLAN.md)
for the next release's scope.
