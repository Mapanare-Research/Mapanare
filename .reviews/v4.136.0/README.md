# v4.136.0 Panel — v5 Gate Attempt 3 — RC1

> Seven-reviewer panel. The v4.121.0 → v4.135.0 15-release closeout
> arc is the surface graded. First v5 candidate in the project's
> history.

**Panel date:** 2026-04-15
**Aggregate: 8.80 / 10**
**Grade distribution: 1 EXCEEDS / 6 MEETS / 0 NEEDS WORK**
**Decision rule applied: Option C — tag `v5.0.0-rc1`**

---

## Individual scores

| Reviewer | Domain | Score | Grade | Δ vs v4.120.0 |
|---|---|---:|---|---:|
| [Rattler](01-rattler.md) | LLVM IR correctness | **8.9** | MEETS | +0.6 |
| [Viper](02-viper.md) | Memory safety | **9.0** | MEETS | +0.6 |
| [Anaconda](03-anaconda.md) | CI / testing | **8.9** | MEETS | **+1.3** |
| [Cobra](04-cobra.md) | Bootstrap / self-hosted | **8.7** | MEETS | +0.8 |
| [Coral](05-coral.md) | Language design | **8.7** | MEETS | +0.6 |
| [Boa](06-boa.md) | Documentation | **8.4** | MEETS | −0.3 |
| [Mamba](07-mamba.md) | C runtime / performance | **9.0** | **EXCEEDS** | +0.5 |
| | **Aggregate** | **8.80** | — | **+0.59** |

Score trajectory v4.99.0 → v4.106.0 → v4.114.0 → v4.120.0 →
v4.136.0: **6.59 → 7.87 → 8.21 → 8.21 → 8.80**.

The v4.121.0 → v4.135.0 closeout arc broke the 8.21 plateau with a
+0.59-point move across 15 releases. Anaconda carried the biggest
delta (+1.3 — from NEEDS WORK at 7.6 to MEETS at 8.9) after her
named findings (An.1 pytest hygiene, An.5 flaky detection) closed
at v4.133.0. Cobra carried +0.8 after the strict 3-stage fixed
point reached at v4.134.0 — the blocker he named at v4.99.0 —
closed.

## Mechanical decision rule

From `docs/roadmap/v4/v4.136.0/PLAN.md`:

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Tag `v5.0.0` | ❌ 8.80 < 9.0 |
| **Option C** | **8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK** | **Tag `v5.0.0-rc1`** | ✅ |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Continue v4.137.0 | ❌ both gates clear |

**Applied: Option C.** Aggregate 8.80 ∈ [8.5, 9.0) AND 0 NEEDS WORK
→ `v5.0.0-rc1` is tagged at this commit.

See [V5_DECISION.md](V5_DECISION.md) for the formal decision text.

## What the closeout arc delivered

Three historical v5 blockers closed in the v4.121.0 → v4.134.0 arc:

1. **Cobra's v4.99.0 fixed-point blocker** — CLOSED v4.134.0.
   Strict 3-stage `stage2.ll == stage3.ll`, md5
   `0c00ad07fee94f98bb350b359395843b`, 108,397 lines.
   Independently re-verified by Cobra in this panel.
2. **Anaconda's v4.120.0 NEEDS WORK** — CLOSED v4.133.0. 39 → 0
   non-bootstrap pytest failures; 4 cumulative flaky audits, 20
   total sequential runs, 0 flaky findings.
3. **Viper's memory-safety baseline** — CLOSED v4.131.0 (LIST) +
   v4.132.0 (STRING). 23 → 0 ASan findings; valgrind ERRORS 31 →
   5 (all residual in Ge.1 generics-init class).

Quality deltas:
- Golden tests through mnc-stage1: 21 → 53 (+32).
- Valgrind ERRORS: 31 → 5 (−26, −84%).
- ASan ASAN_ERROR: 23 → 0 (−23, stretch goal).
- Non-bootstrap pytest failures: 39 → 0 (−39).
- Flaky audit cumulative: 20 sequential runs, 0 flaky findings.
- Dead-code removed: −1,963 lines (v4.123.0 sweep).
- `enum_match` benchmark: 3.026 → 1.468 ms (2.06× speedup;
  Mapanare now 0.98× of Rust).

## What panels agreed on

**Ch.1 is the single HIGH carry-forward.** Viper, Anaconda, Mamba,
and Coral all flagged `mapanare_agent_destroy` UAF before
`pthread_join` (`runtime/native/mapanare_runtime.c:693-715`). All
three sanitizer test classes in
`tests/native/test_c_hardening.py` are currently skipped behind
`_CH1_REASON`. TSan gate on the C runtime is dark until this
closes. Estimated effort: ~5-line fix.

**Secondary consensus (MEDIUM):**

- **Bo.4** — README version badge drift (4.129.0 → 4.136.0);
  day-1 visible. ~30 min effort.
- **Bo.5** — `mapanare --version` prints stale `2.0.1` (metadata
  drift). Day-1 papercut. ~10 min effort.
- **Cb.5** — ABI divergence: Rt.1 `_enum_inline` lives only in the
  Python emitter, not in `mapanare/self/emit_llvm.mn`.
  Stage1-compiled and stage2-compiled binaries have incompatible
  enum ABI. Does not block the fixed-point (both stages use the
  same source).
- **Gr.2** — qualified type refs in type position blocks
  `stdlib/gpu/tensor.mn:90` and `stdlib/gpu/kernel.mn:63`.

## What panels disagreed on

- **Boa** was the sole negative delta (8.7 → 8.4). The docs
  regressions (README badge, getting-started stale golden count,
  `--version` flag drift) were honest but specific to her domain.
  Other reviewers consumed docs without friction.
- **Cobra** flagged an ABI-divergence concern (Cb.5) that did not
  surface in Rattler's LLVM review — because the fixed-point
  `md5` identity masks it (both stages have the same boxed
  representation). Rattler acknowledges Cb.5 as a latent v5.0.x
  item.
- **Mamba** EXCEEDS (9.0) is the only above-MEETS grade. He
  assessed runtime perf wins (Rt.1) delivered beyond promise;
  other reviewers' grades reflect their domains still having LOW
  open items that would pull toward polish, not push toward
  excellence.

## Carry-forward opened by this panel

Full ledger in [V5_DECISION.md](V5_DECISION.md). Summary:

### HIGH

- **Ch.1** — `mapanare_agent_destroy` UAF before thread join
  (consensus across Viper / Anaconda / Mamba / Coral).

### MEDIUM

- **Bo.4** — README version/roadmap drift.
- **Bo.5** — `mapanare --version` reads stale pkg metadata.
- **Cb.5** — Rt.1 enum ABI divergence Python vs self-hosted.
- **Gr.2** — qualified type refs in type position (blocks stdlib/gpu).

### LOW (polish)

- **Sh.2-residual / SE.1** — apply alias-vs-owner shape to
  MAP / SIGNAL / STREAM / boxed-enum-payload Copy paths.
- **Dr.1** — self-hosted hardcoded `!0 = !{!"4.127.0"}`.
- **Cb.3** — mnc-stage2 `ulimit -s 65536` precondition.
- **An.2** — repo-wide lint debt (304 findings; honestly docketed).
- **Sem.1** — SPEC direction for module-level `let mut`.
- **§0 SPEC stale "legacy Python transpiler" line**.
- **Bo.1 / Bo.2 / Bo.3** — carried from v4.120.0 (known_issues,
  native-mode prerequisites, STATISTICS merge).
- **Gr.1** — multi-line list/tensor literal grammar.

### Deferred to v5.x feature track

- **Sh.4 / Sh.5 / Sh.6 / Sh.7** — self-hosted async / const /
  tensor / closure-typed emitter gaps.
- **ABI.1** — 24-byte struct return ABI.
- **Ge.1** — generics-init class (5 valgrind ERRORS, silent UB).
- **TR.1 / Bn.1 / Rt.2 / Rt.3 / Tm.1** — v4.133.0 SKIP-dockets.

## Per-reviewer files

- [01-rattler.md](01-rattler.md) — LLVM IR correctness — **8.9 MEETS**
- [02-viper.md](02-viper.md) — Memory safety — **9.0 MEETS**
- [03-anaconda.md](03-anaconda.md) — CI / testing — **8.9 MEETS**
- [04-cobra.md](04-cobra.md) — Bootstrap / self-hosted — **8.7 MEETS**
- [05-coral.md](05-coral.md) — Language design — **8.7 MEETS**
- [06-boa.md](06-boa.md) — Documentation — **8.4 MEETS**
- [07-mamba.md](07-mamba.md) — C runtime / performance — **9.0 EXCEEDS**

## Outcome

- **`v5.0.0-rc1` tagged at this commit.** First v5 candidate in
  the project's history.
- `VERSION` bumps to `5.0.0-rc1`.
- v5.0.0 final becomes the next target (via v4.137.0 bridge or
  direct v5.0.0 — the lead's call).
- Panel's carry-forward items become v5.0.0-final / v5.0.0.x
  scope.
- The mechanical rule applies again at the v5.0.0 gate: aggregate
  ≥ 9.0 AND 0 NEEDS WORK for the clean tag.

See [V5_DECISION.md](V5_DECISION.md) for the formal decision text.
See `docs/roadmap/v4/v4.136.0/SESSION_REPORT.md` for the release
narrative.
