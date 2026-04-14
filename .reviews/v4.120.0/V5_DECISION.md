# v5 Gate Decision — v4.120.0

## Score

**Aggregate: 8.21/10**
**NEEDS WORK: 1 reviewer (Anaconda — CI / testing)**
**PASS WITH NOTES: 4 reviewers (Rattler, Viper, Cobra, Coral)**
**PASS: 2 reviewers (Boa — documentation, Mamba — performance)**

## Decision Rule

- Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A (tag v5.0.0)
- Aggregate 8.5 – 9.0 AND 0 NEEDS WORK → Option C (tag v5.0.0-rc1)
- Aggregate < 9.0 OR any NEEDS WORK → **Option B (continue v4.121.0+)**

**Applied: Option B.** Aggregate 8.21 < 9.0 AND 1 NEEDS WORK.

Option C is also blocked independently (aggregate below 8.5 *and*
Anaconda's NEEDS WORK verdict).

## Lead directive overlay

The session lead explicitly chose **Option B** independently of the
panel outcome:

> "ok can you run the prompt of 4.120.0? and well i just dont want
> to upgrade to v5 i will hjave another agent with the plans and
> well the rest i want you to do the swap and the reviews?"

The lead's authority to defer the v5 tag beyond what the
mechanical rule alone would allow is documented in `CLAUDE.md`:

> "**v5.0.0** (when ready) — Major version tag. **The lead's call.**"

Since the mechanical rule already produces Option B, the lead
directive does not override it — it confirms it. v5 is not tagged
at v4.120.0 by either channel.

## What Option B Means

- v5.0.0 is **NOT** tagged.
- v4.121.0 opens as the next release. `VERSION` bumps to `4.121.0`.
- The panel's 17 carry-forward items (listed below and in
  `.reviews/v4.120.0/README.md`) become v4.121.0+ scope.
- The cadence continues: one release per sprint, full PLAN + PROMPT
  + SESSION_REPORT + CHANGELOG + tests discipline.
- The next v5 gate will be scheduled when the blocking items close.
  The proposed roadmap (subject to lead approval) targets **v4.130.0**
  as the third v5 gate attempt, with v4.121.0–v4.129.0 closing the
  items below.

## What must close before the next v5 gate

From the panel's carry-forward ledger, ordered by severity and panel
consensus:

### Blockers (every reviewer would want these closed)

1. **Qs.1** — `List<Int>` indexing in argument position
   (`arr.push(42); print(str(arr[0]))` prints `<?>` through the
   native pipeline; Python bootstrap gives correct output). Reproduced
   fresh in this panel by Rattler, Viper, and Mamba. A silent
   wrong-output bug must close before v5.
2. **An.1 / An.2 / An.3** — test + lint hygiene:
   - 51 uncatalogued pytest failures outside the v4.117.0 audit scope
   - 64 black-reformat + 204 ruff + 34 mypy findings
   - `test_fibonacci_run` failure of unknown cause
3. **Sh.8** — self-hosted `semantic.mn` constructor registration
   (None/Some/Ok) — blocks `verify_fixed_point.sh`

### Strongly recommended

4. **Rt.1** — boxed-enum payload overhead (`enum_match` 24× slower
   than C gcc, 2× slower than Rust; 0.3 point dock from Mamba)
5. **Sh.2** — `__mn_str_starts_with` crash in self-hosted emitter
   (10 golden tests affected; 0.2 point dock from Viper)
6. **Cb.1 / Co.1** — README sentence "the compiler compiles itself"
   precision (self-hosted compiles user programs, fixed-point self-
   compile is v5.x)

### Pre-v5 polish (non-blocking but earn panel credit)

- **ASan.1** — `mn_list_rc` UAF baseline (12 findings, reviewed)
- **Cb.2 / Bo.3** — GOLDEN_FAILURES.md / STATISTICS.md documentation refreshes
- **Co.2 / Co.3 / Co.4** — struct-literal-syntax, const-keyword, contract-programming decisions
- **Bo.1 / Bo.2** — `docs/known_issues.md`, getting-started native-mode prerequisites
- **TBAA.1 / willreturn.1** — optimizer annotation decisions (wire or delete)
- **Instr.1** — Culebra scan over 854K-line main.ll (completes for Rattler today)

### Deferred to v5.x

- **Sh.4 / Sh.5 / Sh.6 / Sh.7** — self-hosted emitter feature gaps (async / const / tensor / closure type)
- **Sh.9a / Sh.9b / Sh.10** — Python-bootstrap async emitter workarounds

## The lead's assessment

The recovery arc was disciplined. The v4.100.0 → v4.119.0 twenty-
release sprint closed **every one of the eleven v4.99.0 docket items**
with line-reference evidence. The Phase A critical bugs are
structurally gone (`MnString` bitfield, `_move_resource` move-
semantics, `mn_coro_is_done` fix). The Phase C string_concat fix
delivered a 77× speedup. The Phase E async I/O demos shipped the
first user-runnable async programs. The Phase F benchmark report is
reproducible.

But the panel uncovered gaps this release could not paper over:

- The full pytest suite was never walked. 51 failures outside the
  v4.117.0 audit's declared scope surfaced when the panel ran
  `pytest tests/` directly.
- `make lint` is red. Cosmetic, auto-fixable, but panel-visible and
  unprofessional.
- `verify_fixed_point.sh` still fails at Stage 1. The byref fix is
  verified in isolation; full self-compilation is blocked on Sh.8.

These are **bounded** items. Anaconda's NEEDS WORK is on CI hygiene,
not on compiler correctness. A single release dedicated to closing
An.1 / An.2 / An.3 would move that verdict to PASS WITH NOTES. A
second release closing Qs.1 and Sh.8 would move the aggregate past
8.5. v5 earned via the mechanical rule — Option A or Option C —
then becomes reachable.

## The path to v5

### Short path (user pointed: "I'm fine with more versions")

- **v4.121.0** — test + lint hygiene sweep (close An.1 / An.2 / An.3 / Co.2 / Bo.2)
- **v4.122.0** — Qs.1 fix + DWARF warning (close Qs.1, 3 test failures)
- **v4.123.0** — Rt.1 (boxed-enum unboxing where pointer-fits)
- **v4.124.0** — Sh.8 fix (None/Some/Ok constructors in self-hosted semantic.mn)
- **v4.125.0** — benchmark refresh + updated panel-prep docs
- **v4.126.0** — dead-code sweep (optimizer.py, TBAA decision, Co.3)
- **v4.127.0 – v4.129.0** — buffer + Sh.2 if appetite
- **v4.130.0** — **v5 gate attempt 3**

Each release follows the same cadence discipline: PLAN + PROMPT +
SESSION_REPORT + CHANGELOG + tests. Nothing new.

### Long path

If the lead wants to close more of Sh.4 / Sh.5 / Sh.6 / Sh.7
(self-hosted feature parity) before v5, add 5-10 more releases.
This pushes v5 to ~v4.140.0 timeframe. The panel does not require
this, but Cobra and Coral would both welcome it.

## v5.0.0 Tag

**Not created at v4.120.0.**

The next v5 gate decision will be made by the next panel with
evidence from v4.121.0+. Whether that panel comes at v4.130.0
(short path) or later (long path) is the lead's call.

---

## Panel evidence index

For the next v5 gate reviewers:

- This file — `.reviews/v4.120.0/V5_DECISION.md`
- Panel summary — `.reviews/v4.120.0/README.md`
- Per-reviewer files — `.reviews/v4.120.0/{01-07}-*.md`
- Measurements — `docs/roadmap/v4/v4.120.0/MEASUREMENTS.md`
- Retrospective — `docs/roadmap/v4/v4.120.0/RETROSPECTIVE.md`
- Statistics — `docs/roadmap/v4/v4.120.0/STATISTICS.md`
- V5 readiness matrix — `docs/roadmap/v4/v4.120.0/V5_READINESS.md`
- Pre-panel audit — `docs/roadmap/v4/v4.120.0/AUDIT_NOTES.md`
- Benchmark report — `benchmarks/FINAL_REPORT_v4.120.md`
- Docket ledger — `.reviews/CARRY_FORWARD.md`
- Prior panels — `.reviews/v4.99.0/`, `v4.106.0/`, `v4.114.0/`
