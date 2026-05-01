# Recovery Arc — v5.23.0 → v5.24.1

> **Status:** PLANNING
> **Trigger:** v5.22.0 panel (aggregate 9.41 / Option A) surfaced
> 4 HIGH + 8 MEDIUM + ~12 LOW findings; **CI has been quietly red
> since v5.20.0 → v5.21.1 on 8+ structural gates the v5.21.1
> hygiene release did not surface**.
> **Theme:** close the v5.22.0 panel docket + restore CI green +
> install structural prevention so the v5.27.0 panel inherits a
> clean docket. **This is not a v6.0-deferral arc** — every item
> in scope is closeable inside the v5.x line.

---

## Why this arc exists

The v5.22.0 panel was Option A (mechanical rule fired at 9.41 ≥
9.0; 0 NEEDS WORK). The release shipped. But **post-panel CI
analysis surfaced more failures than the panel saw**:

### CI surface — actual state at v5.21.1 / v5.22.0 HEAD

| Workflow / gate | Status | Surface | Panel-flagged? |
|---|---|---|---|
| `check_struct_registry.py` | **RED** since v5.17.0 | 23 violations | YES — Anaconda §2.A + Cobra #1 (Reg.1, HIGH) |
| `check_no_hollow_features.py` | **RED** since v5.15.0 / v5.20.0 | `CompClause` + `FieldPattern` calibration miss | YES — Anaconda §2.B (MEDIUM) |
| `check_docs_drift.py` | **RED** | SPEC.md:1456 untyped param | YES — Anaconda §2.C (MEDIUM) |
| `check_changelog_honesty.py` | **RED** at v5.21.1 entry | `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` not in CI git tree (`.reviews/` gitignored) | **NO — surfaced post-panel** |
| Docker Smoke | **RED** | `runtime/native/libmapanare_rt.a` missing in `docker-smoke` workflow (no build step before copy) | **NO — surfaced post-panel** |
| macOS & iOS Cross-Compile | **RED** | `__mn_str_eq` / `__mn_str_println` undefined for arm64 (Python bootstrap shells out to clang on macOS without linking `libmapanare_rt.a`) | **NO — surfaced post-panel** |
| Self-Hosted Compiler stage2 (`ir_doctor.py stage2`) | **RED** | `lower.mn` per-module compile fails on `Undefined function 'new_match_arm'` (cross-module ref to `parser.mn`) | **NO — tooling regression, not compiler** |
| LeakSanitizer (`run_asan_leak_goldens.sh`) | **RED** | 3 NEW LEAK regressions on Te.5 goldens (88_if_let, 90_while_let, 91_let_else; 1 leak / 8 bytes each) | **NO — separate from V.9** (Viper found V.9 in indent preprocessor; these are Te.5 lowering drop-glue leaks) |

**8 CI failures total. 4 panel-flagged. 4 NEW.** The
`check_struct_registry.py` failure has been silent for **5
releases**; the macOS/iOS one likely since v5.10.0+ (Bb.\* runtime
exports added `__mn_str_*` family); the Te.5 leaks landed at
v5.20.0 / v5.20.1.

### Panel docket entering recovery

Per `.reviews/CARRY_FORWARD.md` v5.22.0 panel section:
- **4 HIGH** open: Reg.1, Bo.18r (3rd panel), Bo.25, Pk.1.A (effectively HIGH given 11-release age — was LOW at v5.11.0)
- **8 MEDIUM** open: V.9, Te.3 hollow / asymmetric closure, hollow-feature gate, manifesto M2 (3rd panel), SPEC corpus M3, cadence skip, Sh.\* baseline labeling, `make ci-gates` / `check_doc_freshness.py` structural fixes
- **~12 LOW** open
- **1 v6.0-rescoped** (Rt.04)

This recovery arc closes everything **except** the v6.0
items (Rt.04, Te.3 hard removal of `{}`, stage2-teardown crash,
single-line `if x: y`).

---

## Arc shape

| Release | Theme | Severity ceiling | Compiler edits | Effort |
|---|---|---|---|---|
| **v5.23.0** | **RC.\*** — CI recovery + HIGH closures | HIGH | None (only `scripts/`, `.github/`, `mapanare/parser.py` for fmt; no MIR / IR / `mapanare/self/`) | 1 long session |
| **v5.23.1** | **Mb.\*** — memory hygiene | MEDIUM | `mapanare/lower.py` (Te.5 drop glue) + `mapanare/self/parser.mn` (V.9 tracked annotation) | 1 session |
| **v5.23.2** | **Te.3.B** — bootstrap brace-deprecation mirror | MEDIUM | `mapanare/parser.py` + `mapanare/self/parser.mn` (token-walker detector + native mirror) | 1 session |
| **v5.24.0** | **Hy.\*** — structural hygiene gates | MEDIUM (structural) | None (only `scripts/`, `.github/`, `Makefile`) | 1 session |
| **v5.24.1** | **Wd.\*** — wider docs cleanup | MEDIUM | None (only `docs/`, README, examples) | 1 session |

**Total scope:** 5 releases, ~5–8 sessions across ~1–2 weeks.
**Arc end (v5.24.1):** all 4 HIGH closed, all 8 MEDIUM closed,
~12 LOW closed, structural prevention installed.

**Cadence reset:** routine v5.27.0 panel still on schedule
(unchanged by this recovery — the v5.22.0 panel applied Option
A, not Option B; this arc is closure work, not recovery work in
the v4.27–v4.31 sense).

---

## Per-release summary

### v5.23.0 — RC.\* — CI recovery + HIGH closures

The "make CI green again" release. **15 items**, all closeable
in a single session because every fix is small and mechanical.

**HIGH** (must close):
- **RC.1** Reg.1 — extend `check_struct_registry.py` regex to
  accept colon-form headers + investigate the 5-release blind
  window for actual drift (per v4.143.0 retrospective precedent,
  expect non-zero count post-restore).
- **RC.2** Bo.18r — rewrite `README.md:188-192` benchmarks
  paragraph (closes Bo.18r + Bo.19 + Bo.20 in one keystroke).
- **RC.3** Bo.25 — bump goldens badge `66/66` → `95/95` across
  all 4 READMEs + extend `bump_version.py` to auto-discover
  `tests/golden/*.mn` count (structural fix).

**MEDIUM** (CI-blocking):
- **RC.4** Hollow-feature gate — add `CompClause` + `FieldPattern`
  to `_AST_INFRASTRUCTURE` whitelist.
- **RC.5** `check_docs_drift.py` — annotate `docs/SPEC.md:1456`
  with `<!-- pseudo -->` opt-out marker (or fix the example to
  parse).
- **RC.6** `check_changelog_honesty.py` — fix the v5.21.1 entry's
  `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` reference. Two options:
  (A) commit the `.reviews/v5.22.0/` tree to git with `git add
  -f` (matches the v5.11.0 / v5.7.1 precedent of tracked panel
  artifacts), or (B) add `<!-- no-check -->` markers in the
  CHANGELOG, or (C) extend `_SEARCH_ROOTS` in the script if the
  intent is to keep `.reviews/` ignored. **Recommendation: A
  (track panel artifacts)**, since the v5.11.0 README is
  currently tracked.
- **RC.7** Docker Smoke — `publish-docker.yml` needs a "build
  runtime first" step before copying `libmapanare_rt.a`.
- **RC.8** macOS/iOS cross-compile — Python bootstrap on macOS
  needs to link `libmapanare_rt.a` when shelling out to clang.
  Investigate `mapanare/cli.py` clang-shell-out path or the
  `link_with_runtime` helper for the Darwin-arm64 case.
- **RC.9** ir_doctor.py stage2 — make per-module compile pass
  cross-module symbols (build a single `mnc_all.mn` first or
  pass `--link-all` mode).

**LOW**:
- **RC.10** `__mn_indent_to_braces` declaration in `mapanare_core.h`.
- **RC.11** v5.19.0 SESSION_REPORT retroactive backfill.
- **RC.12** Sh.\* baseline labeling normalization across SR + CARRY_FORWARD + CLAUDE.md.
- **RC.13** `tests/bootstrap/test_indent_preprocessor.py` count refresh (142 → 201).
- **RC.14** Bo.22 — README Hello World `mapanare run` → `mnc run`.
- **RC.15** Bo.26 — link `docs/guides/{formatter,init}.md` from README.

**Out of scope**: V.9 leak (v5.23.1), Te.3 hollow (v5.23.2),
manifesto M2 (v5.24.1), SPEC corpus M3 (v5.24.1), cadence
enforcement gate (v5.24.0).

**Strict 3-stage fixed point preserved by construction** —
**zero edits to** `mapanare/{lower,emit_*,mir,*.lark}.py`,
`runtime/native/*.{c,h}`, `mapanare/self/*.mn`. Only
`scripts/`, `.github/workflows/`, `mapanare/parser.py` (for
detector polish), `Makefile`, `bump_version.py`, README +
docs prose.

### v5.23.1 — Mb.\* — memory hygiene

Three real memory bugs + the V.6/V.7/V.8 3-cycle carries +
prevention infrastructure.

**MEDIUM**:
- **Mb.1** V.9 — `__mn_indent_to_braces` MnString lifecycle
  leak. Add tracked-output-string annotation on the `extern
  "C" fn __mn_indent_to_braces` declaration in
  `mapanare/self/parser.mn`. Verify by re-running valgrind on
  a colon-syntax fixture; the 151-byte-per-parse leak should
  disappear.
- **Mb.2** Te.5 ASan leaks — 3 NEW LEAK regressions on
  `tests/golden/{88_if_let,90_while_let,91_let_else}.mn` (1
  leak / 8 bytes each). Almost certainly a missing
  drop-glue site in `_lower_let_else` /
  `_lower_while_let` / `_lower_if_let`. Investigate
  `mapanare/lower.py`'s let-else / while-let / if-let
  desugaring; the synthesized `__mn_chain_N` -style temps need
  to mirror v5.21.0's chain temps in tracking. Once-evaluation
  goldens (95) are leak-clean per Viper (Mb.1's Mb.2 sibling),
  so this is a Te.5-specific issue.
- **Mb.3** Valgrind regression CI gate — new
  `sanitizer-mnc-stage1` job at `.github/workflows/sanitizers.yml`
  running `valgrind --leak-check=full --error-exitcode=1
  mnc-stage1 emit-llvm <colon-syntax-golden>.mn`. Mandatory
  follow-up to V.9 because the byte-identical oracle
  (`test_indent_preprocessor.py`) cannot detect lifecycle
  issues.

**LOW** (3-cycle carries):
- **Mb.4** V.6 — `mn_dir_walk_*_` recursion → iterative
  work-queue.
- **Mb.5** V.7 — Win32 reparse-point skip.
- **Mb.6** V.8 — `sanitizer-cache-walkers` job at
  `sanitizers.yml`.

**ASan leak gate llc-aborts**: the 5 `Aborted (core dumped)`
messages from `llc -filetype=obj -relocation-model=pic` in the
sanitizers run are pre-existing — investigate but defer if the
8 LINK_FAILs are stable across baselines.

**Strict 3-stage fixed point**: must hold across Mb.\* —
v5.23.1 touches `mapanare/lower.py` (Mb.2 drop glue) but not
`mapanare/self/lower.mn`, which means stage2.ll output won't
change. **Verify post-Mb.2 that goldens 88, 90, 91 are still
PASS** (the leak fix should not change observable behavior;
it just runs the missing free).

### v5.23.2 — Te.3.B — bootstrap brace-deprecation mirror

Closes the asymmetric closure flagged by 3 independent panel
reviewers (Coral M1 + Anaconda §3 + Rattler #1):

- Python `count_user_brace_block_openers` misses single-line
  `{...}` shape (line-based detector — counts `{` only at
  end-of-line).
- Native `mnc-stage1` has **zero brace-deprecation logic**
  (`grep MAPANARE_NO_BRACE_WARNING mapanare/self/*.mn` →
  zero hits).

**MEDIUM**:
- **Te.3.B.1** — Python: rewrite `count_user_brace_block_openers`
  as token-walker (catches single-line `{...}` shape; correctly
  excludes `#{...}` map literals; comment- and string-aware).
- **Te.3.B.2** — Native: port the detector to
  `mapanare/self/parser.mn` (~50 LOC). Hook into `parse()`
  before `tokenize()`; print warning to stderr via
  `__mn_str_eprint`. Honor `MAPANARE_NO_BRACE_WARNING=1` env
  via `__mn_getenv`.
- **Te.3.B.3** — New `tests/bootstrap/test_brace_deprecation_mirror.py`
  cross-bootstrap test (10 cases asserting Python ↔ stage1
  byte-identical warning text).
- **Te.3.B.4** — Update PRE_PANEL_AUDIT.md template + ARC
  pre-flight test commands to actually demonstrate the warning.

**Strict 3-stage fixed point**: this release **edits
`mapanare/self/parser.mn`**, which means stage2.ll grows. Bb.\*
seed refresh required. Goldens 95/95 must hold.

### v5.24.0 — Hy.\* — structural hygiene gates

The "this should never have slipped" infrastructure release.
Coral and Anaconda both recommended `check_doc_freshness.py` +
`make ci-gates` as the structural fix for the H.\* / Bo.\*
drift class. Plus cadence enforcement.

**MEDIUM**:
- **Hy.1** `make ci-gates` Makefile target running the full
  CI gate inventory locally as a single command.
  `pre-release` checklist shrinks to "run `make ci-gates`,
  expect zero violations across all sub-gates."
- **Hy.2** `scripts/check_doc_freshness.py` — fail when
  README badges, fixed-point line count, goldens count,
  or version references in any tracked README/SPEC/manifesto
  file are stale. Closes the H.\* / Bo.\* drift class
  structurally.
- **Hy.3** Cadence enforcement gate — CI gate or pre-release
  script firing when ≥5 minor versions OR ≥5 language-feature
  releases have shipped without a panel. Prevents v5.16.0 /
  v5.20.0 silent-skip class.

**LOW** (long-running carries):
- **Hy.4** `>=45` magic-number → self-evident formula
  (Cobra 3rd-panel ask).
- **Hy.5** Pk.1.A — Linux/macOS versioned-tarball smoke gates
  in `publish.yml` (11-release carry; closes the asymmetric
  Windows-only smoke gate from v5.10.0).
- **Hy.6** Pe.1 framing retire ("curve flattening" → "growth
  proportional to bootstrap AST surface; not a v6.0 budget
  concern at current rate") in `CARRY_FORWARD.md` and
  v5.11.0 / v5.22.0 panel references.

**Out of scope**: tag-promotion automation, panel-spawning
automation. Both feel like Hy.\* shape but actually cost
multi-session integration.

**Strict 3-stage fixed point**: zero compiler edits.

### v5.24.1 — Wd.\* — wider docs cleanup

Long-running narrative + manifesto + SPEC drift. **3 of 8
items are 3+ consecutive panel carries** — manifesto M2,
Bo.27 audit cross-reference column convention, etc.

**MEDIUM**:
- **Wd.1** Manifesto M2 — `docs/manifesto.md:31` "Curly braces
  for blocks" rewrite (3rd consecutive panel of manifesto
  drift).
- **Wd.2** SPEC corpus M3 — `mnc fmt --to-terse` over
  `docs/SPEC.md` (preserve historical-artifact examples;
  Chapter 27 stability discussion's brace shape is intentional
  history).

**LOW**:
- **Wd.3** Coral L1 — SPEC §27 deprecation crosslink → Te.3 worked example.
- **Wd.4** Coral L2 — broken-promise wording polish at SPEC:1009 area.
- **Wd.5** Coral L3 — `mnc fmt --keep-braces` flag mention in §4.0.
- **Wd.6** Coral L4 — generic-bound trait sketch.
- **Wd.7** Coral L5 — examples directory micro-organization.
- **Wd.8** Bo.27 — PRE_PANEL_AUDIT cross-reference column convention. Add to the v5.27.0 audit template.

**Strict 3-stage fixed point**: zero compiler edits.

---

## Strict-fixed-point preservation

| Release | `mapanare/self/*.mn` edits | `mapanare/lower.py` edits | Other compiler edits | Fixed-point impact |
|---|---|---|---|---|
| v5.23.0 | None | None (parser.py only for detector polish, no lowering effect) | `mapanare/parser.py` (RC.6 if approach picked) | **Preserved** at 238,086 / 0 diff |
| v5.23.1 | None | Mb.2 (Te.5 drop glue — observable behavior unchanged) | None | **Preserved** at 238,086 / 0 diff (drop glue addition does not change emitted IR shape — it threads through existing tracking machinery) |
| v5.23.2 | Te.3.B.2 (`parser.mn` — brace detector port) | None | `mapanare/parser.py` (Te.3.B.1 — Python detector token-walker) | **Will grow stage2.ll**; Bb.\* seed refresh required; new fixed-point at ~239–240k expected |
| v5.24.0 | None | None | None | **Preserved** at v5.23.2 fixed-point |
| v5.24.1 | None | None | None | **Preserved** at v5.23.2 fixed-point |

**Across the arc**: the streak (now 13 releases at v5.21.1)
will continue at 14 (v5.23.0), 15 (v5.23.1), break + restart at
v5.23.2 (1 streak, expected — same as Te.\* feature releases),
then 16 (v5.24.0), 17 (v5.24.1).

---

## Cadence

The v5.22.0 panel cadence reset is **unchanged by this arc**.
Next routine panel: **v5.27.0** (5 minors past v5.22.0). With
v5.23.0 / v5.23.1 / v5.23.2 / v5.24.0 / v5.24.1 = 5 releases
in the recovery arc, the v5.27.0 panel will arrive having
received **two cadence-cycles** worth of work in one arc.

The v5.27.0 panel target is **9.5+** (back above the 9.41 floor
this panel hit). v5.7.1 ceiling at 9.66 is reachable IF every
HIGH closes structurally and the docs-freshness + ci-gates
prevention infrastructure is in place by v5.24.0. The arc is
sized for that target.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Reg.1 regex restoration surfaces real Ge.1-class drift hidden during 5-release blind window | HIGH | Investigate every flagged drift after restore; backport fixes to whichever release introduced the drift if possible; otherwise close at v5.23.0 with explicit closure comments per v4.143.0 retrospective precedent |
| Te.5 leak fix in v5.23.1 changes IR observable | LOW | The fix is drop-glue addition only — emitted IR shape stays identical; only `__mn_str_free` calls + their callsites change. Verify post-fix that goldens 88/90/91 still PASS and IR diff is in expected `__mn_*_free` insertions only |
| Te.3.B.2 native mirror (~50 LOC in `parser.mn`) breaks bootstrap | MEDIUM | Same risk shape as v5.14.0 → v5.14.1 (Te.1.B colon-block mirror); follow that release's testing flow (cross-bootstrap byte-identity test before commit; per-module commit + verify_fixed_point + goldens at every step) |
| `make ci-gates` reveals more silently-failing gates than the 4 the panel found | MEDIUM | Expected outcome. Each new finding either closes at v5.24.0 (if scope-compatible) or moves to v5.24.x as needed. The point is to surface the silent ones once and for all |
| `check_doc_freshness.py` is a v6.0-shape work item, not v5.x | LOW | The script's MVP is "compare README badges to VERSION + tests/golden/ count + git log streak"; that's ~150 LOC and ships at v5.24.0. Wider scope (every prose claim about every metric) is correctly v6.0+ |
| Pk.1.A (11-release carry) closure scope-creeps | MEDIUM | Pk.1.A is "add Linux + macOS smoke gate to `publish.yml` mirroring the Windows one"; it's 30 LOC of YAML and one test fixture. Hold scope strictly |
| macOS/iOS link fix exposes broader Darwin-ABI work | MEDIUM | If the fix is truly "Python bootstrap doesn't link `libmapanare_rt.a` on Darwin", that's a one-arg flag in `cli.py`. If it surfaces deeper Darwin Mach-O symbol-prefix issues (`___mn_str_*` vs `__mn_str_*`), open a separate v5.24.x docket and don't block v5.23.0 on it |

---

## What this arc CANNOT do

- **Re-grade the v5.22.0 panel.** The Option A decision is final;
  this arc is closure work, not panel-shifting work.
- **Loosen cadence.** v5.27.0 panel runs on schedule.
- **Open recovery cycle.** The v5.22.0 panel applied Option A,
  not Option B; recovery cycles only open under aggregate < 8.5
  OR any NEEDS WORK. This is closure work under the existing
  Option A.
- **Touch v6.0 carry items.** Rt.04 / Te.3 hard removal /
  stage2-teardown / single-line `if x: y` are all out of scope.

---

## Success criteria for the arc

- [ ] All 4 v5.22.0 HIGH items closed (Reg.1, Bo.18r, Bo.25, Pk.1.A)
- [ ] All 8 v5.22.0 MEDIUM items closed (V.9, Te.3 hollow, hollow-feature gate, manifesto M2, SPEC corpus M3, cadence skip enforcement, Sh.\* labeling, `make ci-gates` / `check_doc_freshness.py`)
- [ ] CI green on every workflow at v5.24.1 HEAD: ci, sanitizers, integration, publish, publish-docker, build-native, playground
- [ ] All 8 silent-fail gates documented + restored:
  - `check_struct_registry.py` (RC.1)
  - `check_no_hollow_features.py` step 3 (RC.4)
  - `check_docs_drift.py` (RC.5)
  - `check_changelog_honesty.py` v5.21.1 entry (RC.6)
  - Docker Smoke (RC.7)
  - macOS/iOS cross-compile (RC.8)
  - Self-Hosted Compiler stage2 ir_doctor (RC.9)
  - LeakSanitizer Te.5 leaks (Mb.2)
- [ ] Te.3 brace-deprecation surface symmetric across Python ↔ native (Te.3.B.1 + Te.3.B.2)
- [ ] Goldens 95/95 preserved at every per-release HEAD
- [ ] Strict 3-stage fixed point preserved at every per-release HEAD (with documented 1-release break at v5.23.2 for Te.3.B.2 bootstrap mirror)
- [ ] `make lint` clean at every per-release HEAD
- [ ] `make ci-gates` green at v5.24.0 HEAD (and after)
- [ ] CARRY_FORWARD.md updated at every per-release SESSION_REPORT
- [ ] v5.27.0 panel arrives with **0 HIGH / 0 MEDIUM open** (only LOW polish + v6.0 carries)

---

## Out-of-scope (explicitly held to v6.0 or post-v6.0)

- **Rt.04** — Multi-level alias analysis. v6.0 borrow checker.
- **Te.3 hard removal of `{}`** — v6.0 (after the 2-release soak window terminates).
- **Stage2-binary teardown crash (RC=3)** — papered over by `set +e`; 70+ releases stale; v6.0 cleanup window.
- **Single-line `if x: y`** — explicitly rescoped to v6.0 at v5.21.1 H.7.
- **Tag-promotion / panel-spawning automation** — feels like Hy.\* shape but multi-session integration; v6.0+ if at all.

---

## Filing convention for this arc

| Item | Owner |
|---|---|
| `docs/roadmap/v5/RECOVERY_ARC_v5.23-v5.24.md` | This file (overview, never updated post-write) |
| `docs/roadmap/v5/v5.{23.0,23.1,23.2,24.0,24.1}/PLAN.md` | Per-release planning |
| `docs/roadmap/v5/v5.{23.0,23.1,23.2,24.0,24.1}/PROMPT.md` | Per-release execution |
| `docs/roadmap/v5/v5.{23.0,23.1,23.2,24.0,24.1}/SESSION_REPORT.md` | Per-release post-mortem (written at closeout) |

Each PLAN follows the v5.21.1 / v5.22.0 PLAN format (status,
breaking, prerequisite, effort, why, goals, items table, phase
plan, risk register, success criteria, out of scope).

Each PROMPT follows the v5.22.0 PROMPT format (read-before-
starting, GitNexus pre-flight, phase plan with explicit Phase
0 verification, validation checklists, do-not list).

---

*Drafted 2026-05-01 from the v5.22.0 panel docket +
post-panel CI analysis. Estimated arc closure window: 1–2
weeks at the v5.13–v5.21 cadence.*
