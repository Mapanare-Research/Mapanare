# v5 Gate Decision — v4.136.0

> **v5 gate attempt 3.** Panel aggregate 8.80/10, 0 NEEDS WORK.
> Mechanical rule → **Option C — tag v5.0.0-rc1.**

## Score

**Aggregate: 8.80 / 10**
**Grade distribution: 1 EXCEEDS (Mamba) / 6 MEETS / 0 NEEDS WORK**

## Decision Rule

From `docs/roadmap/v4/v4.136.0/PLAN.md` §"The mechanical rule":

| Rule | Condition | Outcome | Applied? |
|---|---|---|---|
| Option A | Aggregate ≥ 9.0 AND 0 NEEDS WORK | Tag `v5.0.0` | ❌ 8.80 < 9.0 |
| **Option C** | **8.5 ≤ Aggregate < 9.0 AND 0 NEEDS WORK** | **Tag `v5.0.0-rc1`** | ✅ **8.80 ∈ [8.5, 9.0), 0 NEEDS WORK** |
| Option B | Aggregate < 8.5 OR any NEEDS WORK | Continue v4.137.0 | ❌ both gates clear |

**Applied: Option C.** Tag `v5.0.0-rc1`.

This is the first v5 candidate in the project's history. Attempt 1
(v4.99.0) aggregated 6.59; attempt 2 (v4.120.0) aggregated 8.21
with 1 NEEDS WORK (Anaconda, CI/testing hygiene). The 15-release
v4.121.0 → v4.135.0 closeout arc addressed every named finding from
both prior panels and closed all three historical v5 blockers:

1. **Cobra's v4.99.0 fixed-point blocker** — CLOSED v4.134.0
   (strict 3-stage stage2.ll == stage3.ll, md5
   `0c00ad07fee94f98bb350b359395843b`, independently re-verified
   in this panel by Cobra).
2. **Anaconda's v4.120.0 NEEDS WORK (CI/testing)** — CLOSED v4.133.0
   (39 → 0 non-bootstrap pytest failures + 4 cumulative flaky
   audits, 20 total sequential runs, 0 flaky findings).
3. **Viper's memory-safety baseline (Sh.2 extracted-alias)** —
   CLOSED v4.131.0 (LIST) + v4.132.0 (STRING) (23 → 0 ASan
   findings; valgrind ERRORS 31 → 5, all residual in Ge.1 class).

## Per-reviewer scores

| Reviewer | Domain | v4.120.0 | v4.136.0 | Δ | Grade |
|---|---|---:|---:|---:|---|
| [Rattler](01-rattler.md) | LLVM IR correctness | 8.3 | **8.9** | +0.6 | MEETS |
| [Viper](02-viper.md) | Memory safety | 8.4 | **9.0** | +0.6 | MEETS |
| [Anaconda](03-anaconda.md) | CI / testing | 7.6 ❌ | **8.9** | **+1.3** | MEETS |
| [Cobra](04-cobra.md) | Bootstrap / self-hosted | 7.9 | **8.7** | +0.8 | MEETS |
| [Coral](05-coral.md) | Language design | 8.1 | **8.7** | +0.6 | MEETS |
| [Boa](06-boa.md) | Documentation | 8.7 | **8.4** | −0.3 | MEETS |
| [Mamba](07-mamba.md) | C runtime / performance | 8.5 | **9.0** | +0.5 | **EXCEEDS** |
| | **Aggregate** | **8.21** | **8.80** | **+0.59** | — |

**Score trajectory** v4.99.0 → v4.106.0 → v4.114.0 → v4.120.0 →
v4.136.0: **6.59 → 7.87 → 8.21 → 8.21 → 8.80.**

The v4.121.0 → v4.135.0 closeout arc broke the 8.21 plateau with a
+0.59-point move in 15 releases. Anaconda (+1.3) and Cobra (+0.8)
carried the delta. Boa's −0.3 is the sole regression (README
version badge drift: 4.129.0 badge vs live 4.136.0 VERSION — Bo.4
carry-forward, ~30 min effort).

## What Option C Means

- `v5.0.0-rc1` tag is created at this commit.
- `VERSION` bumps to `5.0.0-rc1`.
- v5.0.0 final becomes the next release target (or v4.137.0 if the
  lead chooses to continue the v4.x cadence for one more release to
  close the Ch.1 HIGH + Bo.4 README items before final).
- The mechanical rule applies again at the next gate: aggregate
  ≥ 9.0 AND 0 NEEDS WORK for a clean v5.0.0 tag.
- Panel's carry-forward items (listed below) become v5.0.0-final /
  v5.0.x scope, not v4.137.0+ sprawl.

## What must close before v5.0.0 final

Items the panel agreed on, ordered by severity + consensus:

### HIGH — should close before v5.0.0 final

1. **Ch.1** — `mapanare_agent_destroy` UAF before `pthread_join`
   (Viper, Anaconda, Mamba, Coral all flagged).
   `runtime/native/mapanare_runtime.c::mapanare_agent_destroy`
   (lines 693-715) is missing the thread-join step. All three
   sanitizer test classes (`TestCRuntimePlain`,
   `TestCRuntimeASan`, `TestCRuntimeTSan`) in
   `tests/native/test_c_hardening.py:99,113,134` are currently
   skipped behind one shared `_CH1_REASON`. TSan gate on the C
   runtime is dark until this closes. Estimated effort: ~5-line
   fix + state guard. **This is the single HIGH item on the
   ledger.**

### MEDIUM — strongly recommended before v5.0.0 final

2. **Bo.4** — README version badge drift (4.129.0 → 4.136.0;
   FINAL_REPORT link stale; roadmap table ends at v4.131.0; §5
   getting-started still says "39/65 golden tests" — live is
   53/65). Day-1 visible. ~30 min effort.
3. **Bo.5** — `mapanare --version` prints `2.0.1` (reads stale
   `pkg_resources` metadata rather than the `VERSION` file).
   Day-1 visible papercut. ~10 min effort.
4. **Cb.5** — ABI divergence: `_enum_inline` machinery exists in
   Python emitter (`mapanare/emit_llvm_text.py`, 10 grep hits) but
   is absent from `mapanare/self/emit_llvm.mn` (0 hits).
   Fixed-point holds because both stages use the same self-hosted
   source + boxed representation; but stage1-compiled and
   stage2-compiled binaries have incompatible enum ABI.
   Not a fixed-point blocker. v5.0.x.
5. **Gr.2** — qualified type refs in type position
   (`stdlib/gpu/tensor.mn:90`, `stdlib/gpu/kernel.mn:63` blocked).
   Grammar extension or stdlib bare-import workaround. v4.137.0
   or v5.0.x.

### LOW — pre-v5.0.0-final polish (nice-to-have, not blocking)

- **Sh.2-residual / SE.1** (Rattler) — MAP / SIGNAL / STREAM `_do_copy`
  branches still call `_track_container` unconditionally. Apply
  alias-vs-owner shape to match LIST+STR. Defensive; no current
  failing test case.
- **Dr.1** — self-hosted `!0 = !{!"4.127.0"}` hardcoded version
  string in `mapanare/self/emit_llvm.mn:3523`. Cosmetic; does not
  invalidate fixed-point md5 (constant in both stages).
- **Cb.3** — mnc-stage2 needs `ulimit -s 65536` to run on
  `mnc_all.mn`. Document precondition or set internally.
- **An.2** — lint debt (204 ruff + 65 black + 36 mypy). Honestly
  docketed in `tests/test_ci.py:120-129` skip. Not blocking.
- **Sem.1** — module-level `let mut` scoping: pick SPEC direction
  (add or reject). Coral wants this closed before v5.0.0 syntax
  freeze.
- **§0 SPEC stale phrasing** — `docs/SPEC.md:6` still says
  "A legacy Python transpiler backend exists" (Appendix B already
  documents the v4.58.0 deletion). One-line fix.
- **Bo.1 / Bo.2 / Bo.3** — `docs/known_issues.md`,
  getting-started native-mode prerequisites, STATISTICS.md merge.
  Carried from v4.120.0. Non-blocking.

### Deferred to v5.x feature track

- **Sh.4 / Sh.5 / Sh.6 / Sh.7** — self-hosted async / const /
  tensor / closure-typed emitter gaps (12 goldens).
- **Gr.1** — multi-line list/tensor literal grammar.
- **ABI.1** — 24-byte struct return ABI (residual 2.3× vs C gcc on
  `enum_match`).
- **Ge.1** — generics-init class (5 valgrind ERRORS in
  `lower__try_monomorphize_struct` / `fresh_tmp` chain). Silent
  UB; no miscompile.
- **TR.1 / Bn.1 / Rt.2 / Rt.3 / Tm.1** — v4.133.0 An.1 reduction
  SKIP-dockets.

## The lead's call

`CLAUDE.md` reserves the v5.0.0 tag itself to the lead:

> "**v5.0.0** (when ready) — Major version tag. **The lead's call.**"

The mechanical rule mandates the `v5.0.0-rc1` tag at this commit.
The transition from `-rc1` to a clean `v5.0.0` is the lead's
prerogative, subject to Ch.1 closure and (ideally) Bo.4/Bo.5
README hygiene.

## Next steps

- `VERSION` → `5.0.0-rc1`
- Git tag `v5.0.0-rc1` at this commit
- `CHANGELOG.md` [5.0.0-rc1] entry summarizing the 136-release v4.x
  arc + listing carry-forward items for v5.0.0 final
- `CLAUDE.md` current version → v5.0.0-rc1
- `docs/roadmap/ROADMAP.md` → v5.0.0-rc1 entry
- **v5.0.0 final** planning (v4.137.0 bridge release or direct v5.0.0
  — lead's call)

---

## Panel evidence index

For the v5.0.0-final reviewers:

- This file — `.reviews/v4.136.0/V5_DECISION.md`
- Panel summary — `.reviews/v4.136.0/README.md`
- Per-reviewer files — `.reviews/v4.136.0/{01-07}-*.md`
- Measurements — `docs/roadmap/v4/v4.135.0/MEASUREMENTS.md`
- Fixed-point status — `docs/roadmap/v4/v4.135.0/FIXEDPOINT_STATUS.md`
- Valgrind + ASan reports — `docs/roadmap/v4/v4.135.0/VALGRIND_REPORT.md`, `ASAN_REPORT.md`
- Flaky audit — `docs/roadmap/v4/v4.135.0/FLAKY_AUDIT.md`
- Docket ledger — `docs/roadmap/v4/v4.135.0/DOCKET_LEDGER.md`
- V5 readiness matrix — `docs/roadmap/v4/v4.135.0/V5_READINESS.md`
- Pre-panel audit — `.reviews/v4.136.0/PRE_PANEL_AUDIT.md`
- Benchmark report — `benchmarks/FINAL_REPORT_v4.136.md`
- Prior panels — `.reviews/v4.99.0/`, `v4.106.0/`, `v4.114.0/`, `v4.120.0/`

**Attempt 3 passes the rc1 gate. The rule is the rule. The numbers
are the numbers. v5.0.0-rc1 is real.**
