# Mapanare v5.28.0 — 7-Reviewer Panel Prompt

> Paste this prompt into a Claude Code agent invocation. Make sure the
> agent is at the **v5.28.0 HEAD** of the Mapanare repository before
> running. v5.27.0 must have shipped first plus any v5.27.x hygiene
> closures from `.reviews/v5.28.0/PRE_PANEL_AUDIT.md`.

---

## Version Configuration

**TARGET VERSION:** `v5.28.0` (RE-PANEL — panel-only release)
**ARC GRADED:** v5.23.0 → v5.27.0 (8 SESSION_REPORTs across the
v5.23-v5.24 recovery arc + v5.25-v5.27 prevention/closeout arcs).
**PRIOR PANEL:** v5.22.0 (`.reviews/v5.22.0/`) — **9.41 / 10**
aggregate, Option A, **−0.21 Δ vs v5.11.0**, **−1.30 single-reviewer
regression** (Anaconda; load-bearing process-discipline drag).
4 HIGH (Reg.1, Bo.18r-3, Bo.25, plus Pk.1.A inherited LOW), 8
MEDIUM (V.9, Te.5 ASan leaks, Te.3 hollow / asymmetric closure,
Hollow-feature gate calibration, Manifesto coherence M2, SPEC
corpus M3, Sh.\* shrink baseline labeling, Cadence skip), ~12 LOW.

> **This is the v5.23–v5.27 recovery + prevention + arc-closeout
> panel.** The arc graded shipped:
>
> | Release | Codename | What it shipped |
> |---|---|---|
> | v5.23.0 | RC.\* | CI recovery + 4 HIGH closures (Reg.1, Bo.18r, Bo.25, plus 8 MEDIUM and 6 LOW from v5.22.0 docket) |
> | v5.23.1 | Mb.\* (V.9 + Te.5 leaks) | Memory hygiene |
> | v5.23.2 | Te.3.B | Bootstrap brace-deprecation mirror (closes Te.3 hollow / asymmetric closure) |
> | v5.24.0 | Hy.\* | Structural hygiene gates (`make ci-gates`, `check_doc_freshness.py`, cadence) |
> | v5.24.1 | Wd.\* | Wider docs cleanup (recovery arc closeout — manifesto M2, SPEC corpus M3, Coral L1–L5, Bo.27 audit cross-reference convention) |
> | v5.25.0 | Pv.\* | CI prevention (runtime-lib lookup, valgrind preprocess gate, clean-build-test, validate-wsl, publish smoke fixtures) + retroactive bugfix close |
> | v5.26.0 | Mb.7 + Mb.9 | i64/i1 tag-emit codegen fix + Win64 ABI byval/byref MnString fix (Mb.\* arc CLOSED) |
> | v5.26.1 | Eu.1..Eu.4 | Close v5.26.0-deferred LINK_FAIL bug classes (Eu.\* arc CLOSED — 4 prev-LINK_FAIL goldens flipped to PASS) |
> | v5.27.0 | Mc.8 + Mc.9 + Tk.1 | Formatter polish (Mc.\* parity arc CLOSED — 12-release closure of v5.13.0 Mc.\* docket; Tk.\* sub-arc opened and closed in same release) |
>
> **Cadence:** 6 minor versions since v5.22.0 panel. v5.24.0 Hy.3
> cadence-enforcement gate fired hard at v5.27.0 (5+ minor
> threshold). **v5.28.0 closes the cadence gap 1 minor late on
> purpose** — formatter polish was the wrong scope to bundle with a
> panel cycle, and the deliberate slip is the correct trade-off
> (acknowledged in `PRE_PANEL_AUDIT.md`). Reviewers may flag this
> as process discipline; the lead acknowledges it explicitly so
> reviewers can grade the framing rather than the slip itself.
>
> **Mechanical rule, applied verbatim:**
> - Aggregate **≥ 9.0 AND 0 NEEDS WORK AND no NEW HIGH off the v5.22.0 docket** → Option A
>   (point-release health gate clears, no recovery cycle).
> - Otherwise → Option B (open v5.29-v5.30 recovery cycle).
>
> **Lead's target:** **9.55–9.65** per v5.24.1 SESSION_REPORT
> projection. Recovery from v5.22.0's 9.41 floor. v5.7.1 panel was
> 9.66 (project-history ceiling); v5.11.0 was 9.62; v5.22.0 was
> 9.41. The trend across 3 panels is monotonically downward
> (-0.04, -0.21); v5.28.0's job is to break the trend.

Set the review output directory:

```
.reviews/v5.28.0/
  PRE_PANEL_AUDIT.md     # <-- ALREADY WRITTEN. Lead's fact-check.
                         #     Reviewers MUST read this first.
  prompt.md              # This file (shared panel brief)
  README.md              # Summary index — written AFTER all 7 findings land
  V5_DECISION.md         # Formal decision text after aggregation
  rattler/
    prompt.md            # Reviewer-specific persona + focus
    findings.md          # Reviewer's output
  viper/   (same shape)
  anaconda/
  cobra/
  coral/
  boa/
  mamba/
```

---

## Required reading (every reviewer)

Before forming a verdict, each reviewer MUST read:

1. **`.reviews/v5.28.0/PRE_PANEL_AUDIT.md`** — the lead's own
   fact-check. Bound to prior-panel finding IDs per Bo.27 / Wd.8
   convention. Verify each H.\* closure claim against v5.27.0 HEAD
   (or v5.27.x if hygiene release shipped).
2. **`.reviews/v5.22.0/README.md`** — the prior panel
   (9.41/10, Option A, -1.30 Anaconda). Cross-reference every
   action item from v5.22.0's docket.
3. **`.reviews/v5.22.0/V5_DECISION.md`** — the prior decision
   document. v5.28.0 V5_DECISION must follow the same shape.
4. **`.reviews/CARRY_FORWARD.md`** — canonical docket ledger.
   Every CLOSED item the panel sees claimed must reflect in the
   ledger; every OPEN item must be tracked.
5. **`.reviews/REVIEW_CADENCE.md`** — cadence policy. Note that
   v5.28.0 is **1 minor version late** for the cadence trigger (5
   minors past v5.22.0 fired at v5.27.0; v5.28.0 closes 1 minor
   late). Lead acknowledges this; grade the framing.
6. **`.reviews/PANEL_AUDIT_TEMPLATE.md`** (Wd.8 / Bo.27 — applies
   starting v5.27.0 audit) — the cross-reference convention. Verify
   `PRE_PANEL_AUDIT.md` follows it.
7. **The 9 arc SESSION_REPORTs**:
   - `docs/roadmap/v5/v5.23.0/SESSION_REPORT.md` — RC.\* CI recovery
   - `docs/roadmap/v5/v5.23.1/SESSION_REPORT.md` — Mb.\* memory hygiene
   - `docs/roadmap/v5/v5.23.2/SESSION_REPORT.md` — Te.3.B brace-deprecation mirror
   - `docs/roadmap/v5/v5.24.0/SESSION_REPORT.md` — Hy.\* structural hygiene gates
   - `docs/roadmap/v5/v5.24.1/SESSION_REPORT.md` — Wd.\* wider docs cleanup
   - `docs/roadmap/v5/v5.25.0/SESSION_REPORT.md` — Pv.\* CI prevention
   - `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md` — Mb.7 + Mb.9 codegen fix
   - `docs/roadmap/v5/v5.26.1/SESSION_REPORT.md` — Eu.\* LINK_FAIL closures
   - `docs/roadmap/v5/v5.27.0/SESSION_REPORT.md` — Mc.8 + Mc.9 + Tk.1 formatter polish
8. The relevant AUDIT.md / PLAN.md files for v5.26.0, v5.26.1
   (Phase 0 surprises documented).

Each reviewer's findings.md must explicitly note whether v5.22.0
panel items were **Fixed**, **Regressed**, **Still open**, or
**Deferred with documented tracking**, and bind every NEW finding
to a prior-panel ID (or "(none — fresh)").

---

## What this panel must answer (specific to v5.23–v5.27 arc)

### Correctness (Rattler / Viper / Cobra / Mamba)

- **Strict 3-stage fixed point** at v5.27.0 HEAD?
  - With the existing `mapanare/self/mnc-stage1` binary:
    `bash scripts/verify_fixed_point.sh --keep` returns NEAR with a
    1-line VERSION-metadata diff (stage1 binary embeds prior
    release's version because runtime archive linked at build time).
  - With stage1 rebuilt from current HEAD:
    `python3 scripts/build_stage1.py && bash scripts/verify_fixed_point.sh --keep`
    returns STRICT at 241,842 lines / 0 diff.
  - This is the SESSION_REPORT's "preserved by construction" claim
    — verify both paths.
- **Goldens 95/95** through `mnc-stage1`?
  (`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`)
- **Eu.1..Eu.4 closures verified**: 4 previously-LINK_FAIL goldens
  (47, 48, 49, 51) now PASS via `tests/llvm/test_async_link.py`?
- **Mb.7 verified**: i64/i1 tag-emit bug closed; `__mn_indent_to_braces`
  warning behavior preserved; stage2.ll line count delta from
  v5.25.0's 239,835 → v5.26.0's 239,993 → v5.26.1's 241,842 explained
  (Eu.\* added new lowerer/emitter arms for or-pattern + match cascade)?
- **Mb.9 verified**: Win64 byval MnString fix in both Python `_do_call`
  and self-host `emit_mir_call`; `tests/native/test_brace_funcs_windows_abi.py`
  8/8 PASS?
- **Pv.\* prevention infrastructure verified**:
  - `tests/test_runtime_lib_lookup.py` (3 cases, locks against v3.x candidate-name re-introduction)
  - `tests/bootstrap/test_preprocess_memcheck.py` (3 cases, valgrind)
  - `make ci-gates` `clean-build-test` sub-gate (rebuilds runtime archive + runs runtime-aware tests)
  - `scripts/validate_wsl.sh` + `dev.ps1 validate-wsl`
  - `tests/test_publish_smoke_fixtures.py` (parses every inline `.mn` fixture in publish.yml)
- **Mc.8/9 + Tk.1 verified**: detect-only `--line-length`,
  alphabetical `--sort-imports`, empty `#{}` map literal preservation
  in `to_terse`. 47 new test cases (~525 LOC).

### Documentation (Boa / Coral)

- **PRE_PANEL_AUDIT.md H.\* closures** all closed at v5.28.0 HEAD?
  Each finding has a specific line/file claim; verify each.
- **README.md fixed-point status paragraphs** consistent and
  current (Bo.18r class — 4th-consecutive-panel risk if stale)?
- **Localized READMEs (es/pt/zh-CN)** synced with v5.27.0 reality
  (line count, streak length, last-cited release)?
- **SPEC.md header** at v5.27.0 cut?
- **CHANGELOG.md** has entries for v5.23.0–v5.27.0; honest
  (`python3 scripts/check_changelog_honesty.py` clean)?
- **`docs/known_issues.md`** Last-updated bumped from v5.21.1?
- **CLAUDE.md release-notes** for v5.23.0–v5.27.0 all present and
  honest?

### Process (Anaconda / Coral)

- **CARRY_FORWARD.md** updated with v5.25.0 / v5.26.0 / v5.26.1 /
  v5.27.0 closures? (At Phase 0, audit found these missing — was
  that fixed in v5.27.x hygiene?)
- **Cadence acknowledgment**: PROMPT.md and PRE_PANEL_AUDIT.md
  both explicitly acknowledge the 1-minor-late close. Grade the
  framing.
- **`make ci-gates` clean** at HEAD (cadence-check sub-gate fires
  hard at v5.27.0 cut; turns GREEN immediately on `.reviews/v5.28.0/`
  creation per Hy.3 spec)?
- **PANEL_AUDIT_TEMPLATE.md (Bo.27 convention)** followed in
  PRE_PANEL_AUDIT.md? Every H.\* binds to a prior-panel ID or
  "(none — fresh)"; every prior-panel HIGH/MEDIUM either appears
  or is in "deferred" section.

### Language design (Coral)

- **Te.3 brace-deprecation now byte-identical** Python ↔ native
  via `__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning`
  C-runtime exports (v5.23.2 Te.3.B.2)?
- **Eu.\* arc CLOSED**: every v5.23.1 → v5.26.0 LINK_FAIL bug
  class regression-locked at HEAD?
- **Mc.\* arc CLOSED**: every v5.13.0 Mc.\* docket item resolved
  (Mc.1 LSP, Mc.2 fmt, Mc.3 init, Mc.4 check, Mc.5 wasm-emit, Mc.6
  Windows SDK split, Mc.7 hygiene, Mc.8 line-length, Mc.9 sort-imports)?
- **Mc.8 design pivot honest**: detect-only `--line-length` (auto-wrap
  rescoped to a future grammar-extension release; rationale documented
  in v5.27.0 SESSION_REPORT)?

### Memory + runtime (Viper / Mamba)

- **C runtime delta v5.22.0 → v5.27.0**: what shipped? V.6/V.7/V.8
  3rd-cycle closures (v5.23.1 Mb.4–6); valgrind sweeps for cache
  walkers (Mb.6) + indent preprocessor (Mb.3); `__mn_count_user_brace_block_openers`
  + `__mn_emit_brace_deprecation_warning` (Te.3.B.2) added to support
  bootstrap mirror.
- **Te.5 ASan leaks** closed in `emit_wrap_some` via
  `emit_track_boxed` (v5.23.1 Mb.2) — re-verify the fix; baseline
  TSV at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`
  refreshed?

---

## The 7 Reviewers

> **Naming convention** unchanged: snake names (Boa, Viper, Cobra,
> Mamba, Anaconda, Rattler, Coral). Reviewer ordering matches
> v5.22.0 panel for cross-reference clarity.

### 1. Rattler — LLVM IR / codegen
- **Domain:** LLVM IR generation, codegen correctness
- **Personality:** Insufferably smart; treats every release through
  "how does this lower?"; detailed LLVM-reference fixes.
- **v5.28.0 focus:** Mb.7 i64/i1 tag-emit codegen fix verified in
  IR; Eu.\* enum-payload codegen closures (4 prev-LINK_FAIL); the
  ABI dispatch in v5.26.0 Mb.9 (3-way SysV/Win64/i686 + the
  byval/byref MnString contract); strict 3-stage fixed point
  preserved at 241,842 lines (verify live with stage1 rebuild).

### 2. Viper — Memory safety
- **Domain:** Memory safety, ownership semantics, drop glue
- **Personality:** Ruthless; finds every potential UAF; sarcastic.
- **v5.28.0 focus:** V.9 closure (v5.23.1 Mb.1 — `__mn_indent_to_braces`
  blanket-move bypass); Te.5 ASan leak closures (v5.23.1 Mb.2 —
  `emit_wrap_some` + `emit_track_boxed`); V.6/V.7/V.8 3rd-cycle
  closures (v5.23.1 Mb.4–6); valgrind regression gates (Pv.2
  preprocess-memcheck, Mb.3 sanitizer-mnc-stage1, Mb.6 sanitizer-cache-walkers);
  any new Te.5/Te.6 leak surface from v5.26.1's lower_match cascade
  rewrite (Eu.3 — `bind_ident_pattern` SSA uniquification).

### 3. Anaconda — CI / testing / toolchain
- **Domain:** CI, build infrastructure, diagnostics, process discipline
- **Personality:** Pedantic but fair; cares about "doing things the
  right way." References POSIX and GCC like scripture.
- **v5.28.0 focus:** Reg.1 closure (v5.23.0 RC.1 — regex extension
  + investigation surfaced 5 latent drifts in `LowerState`); the
  three-gate silent-fail class (v5.22.0 -1.30 dock); cadence skip
  closure (v5.24.0 Hy.3 cadence-check gate fires hard at v5.27.0;
  v5.28.0 closes 1 minor late — grade the framing); Hy.\*
  infrastructure (8-sub-gate `make ci-gates`, `check_doc_freshness.py`,
  cadence-check); Pv.\* prevention (runtime-lib lookup gate,
  preprocess-memcheck, clean-build-test, publish smoke fixtures).

### 4. Cobra — Bootstrap / self-hosted
- **Domain:** Bootstrap / self-hosted compiler, ABI, monomorphization
- **Personality:** Calls things "quaint" and "amusing"; razor-sharp
  technical observations behind condescension.
- **v5.28.0 focus:** Strict 3-stage fixed-point streak length at
  v5.27.0 (CLAUDE.md claims 23 consecutive releases at 241,842 lines;
  verify); the Bb.\* seed refresh discipline (Te.3.B.5 v5.23.2 +
  zero refreshes elsewhere); the Eu.3/Eu.4 lower_match cascade
  rewrite (or-pattern + literal sub-args); the Tk.1 `to_terse`
  bug fix (statement-block-opener filter on empty `{}` branch);
  the Mc.8/9 native-side dispatch (zero `.mn` source edits because
  argv forwarding is already in place).

### 5. Coral — Language design
- **Domain:** Language design, syntax coherence, manifesto, DX
- **Personality:** Asks "what is this language trying to say?";
  fairest reviewer.
- **v5.28.0 focus:** Mc.\* arc CLOSED — does the closure read
  honestly? Mc.8 `--line-length` shipped detect-only with explicit
  rationale (Phase 0 found Mapanare's grammar is single-line for
  all expressions; auto-wrap can't satisfy AST-preservation
  invariant); Mc.9 `--sort-imports` block-boundary semantics; Tk.1
  empty `{}` map/struct literal preservation. Manifesto coherence
  M2 closed at v5.24.1 Wd.1 — verify the line. SPEC corpus M3
  closed at v5.24.1 Wd.2 — verify the markdown rewriter
  (`to_terse_markdown` + `<!-- preserve-brace -->` opt-out).
  Coral L1–L5 / TR1 closures (v5.24.1 Wd.3–7).

### 6. Boa — Documentation / DX
- **Domain:** Documentation, DX, README surface, ergonomics
- **Personality:** Happiest reviewer alive; everything is "beautiful"
  and "Pythonic"; wraps real findings in positivity.
- **v5.28.0 focus:** **Bo.18r — 4th-consecutive-panel risk**.
  The `README.md:188-192` benchmarks paragraph was closed at v5.23.0
  RC.2 with rounded `239k` framing; verify it stayed closed at
  v5.27.0 (same paragraph drift would reopen the systemic-skill-gap
  category). **Bo.25** (goldens badge sync) — closed at v5.23.0
  RC.3 with `bump_version.py` extension; verify badge auto-discover
  is still wired and goldens count badge matches body. Localized
  READMEs (es/pt/zh-CN) — were they re-synced from v5.21.0 vintage
  to v5.27.0 vintage? `docs/known_issues.md` Last-updated bumped?
  CLAUDE.md release-notes section for v5.23.0–v5.27.0 complete?
  `examples/INDEX.md` (v5.24.1 Wd.7) intact?

### 7. Mamba — C runtime / performance
- **Domain:** C runtime, performance, allocations, ABI
- **Personality:** Brutal, terse. "Delete this." Measures everything
  in unnecessary allocations.
- **v5.28.0 focus:** C runtime delta v5.22.0 → v5.27.0 — what
  shipped? Bb.\* seed refresh discipline; the Pe.1 reframe (Hy.6
  v5.24.0 — "curve flattening" framing retired). Mb.9 i686/Win64
  byval contract; the `__mn_emit_brace_deprecation_warning` C-side
  implementation (zero allocations, getenv-once)?

---

## Review File Format

Each reviewer's findings.md follows this format:

```markdown
# [Reviewer] — [Domain] Review of Mapanare v5.28.0

**Reviewer:** [Name]
**Personality:** [one-line summary]
**Previous Version Reviewed:** v5.22.0
**Score:** [X.YY / 10]
**Grade:** [EXCEEDS | MEETS | NEEDS WORK]
**Delta vs v5.22.0:** [+/- 0.YY]
**Verdict:** [PASS | PASS WITH NOTES | NEEDS WORK | REJECT]
**Confidence:** [1-10]
**Files Reviewed:** [list of key files examined]

## Executive Summary
[2-3 paragraphs]

## Score: X.YY / 10

## Progress Since Last Review (v5.22.0 → v5.28.0)
[Per-arc analysis: RC.* / Mb.* / Te.3.B / Hy.* / Wd.* / Pv.* / Mb.7 / Mc.*+Tk.*.
 Note v5.22.0 panel items as Fixed / Regressed / Still open / Deferred-with-tracking.]

## What is preserved from v5.22.0
[Carry-forward verifications]

## Issues Found
[Numbered list, severity: CRITICAL / HIGH / MEDIUM / LOW]
[Format: `1. **[SEVERITY]** Title — description (Bound: prior-panel ID or "fresh")`]

## Recommendations
[Actionable, prioritized]

## Post-Production Health Assessment
[Is the codebase healthy 28 minor versions after the v5.0.0
 release-gate? Are features hollow? Documented state matches actual code?]

## Raw Notes
[Stream-of-consciousness, code snippets, questions]
```

---

## Pre-flight Verification (every reviewer should run)

```bash
# Strict 3-stage fixed point at HEAD
python3 scripts/build_stage1.py    # rebuild stage1 from current HEAD
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, 241842 lines, 0 diff (STRICT)

# (Without rebuild: NEAR with 1-line VERSION-metadata diff —
#  expected; reflects stale-stage1 artifact, not a regression.)

# Native goldens at HEAD
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: All 95 tests passed

# Bootstrap mirror cross-tests
python3 -m pytest tests/bootstrap/ -v --no-header
# expected: ~250+ cases pass (Te.5 12, Te.6 10, comp 10, interp 10,
#           indent 201, brace-deprecation 11, plus stage1_compile 20,
#           preprocess-memcheck 3)

# Build from seed
bash scripts/build_from_seed.sh
# expected: clean

# Lint
make lint
# expected: ruff + black + mypy clean

# CI gates (Hy.* infrastructure)
make ci-gates
# expected: All sub-gates GREEN.
# - cadence-check turns GREEN immediately on .reviews/v5.28.0/
#   creation (per Hy.3 spec)
# - clean-build-test sub-gate (Pv.3 v5.25.0) rebuilds runtime archive
#   and runs runtime-aware tests

# CHANGELOG honesty
python3 scripts/check_changelog_honesty.py
# expected: clean for [5.27.0] and prior

# Te.3 brace-deprecation byte-identity (v5.23.2 Te.3.B)
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
mapanare/self/mnc-stage1 emit-llvm /tmp/brace.mn -o /tmp/x.ll 2>&1 | head -3
# expected: byte-identical warning text from both compilers

# Eu.* closures (v5.26.1)
python3 -m pytest tests/llvm/test_async_link.py -v
# expected: 10/10 PASS, 0 XFAIL (4 prev-LINK_FAIL goldens flipped)

# Mb.9 Win64 ABI verification (v5.26.0)
python3 -m pytest tests/native/test_brace_funcs_windows_abi.py -v
# expected: 8/8 PASS
```

---

## Process Instructions

Each reviewer should:

1. **Read PRE_PANEL_AUDIT.md first** — verify each H.\* closure
   claim against v5.27.0 HEAD (or v5.27.x hygiene-release HEAD)
   before forming any opinion.
2. **Read v5.22.0 panel README.md** for the prior-panel docket.
3. **Read REVIEW_CADENCE.md** for the cadence rule.
4. **Read CARRY_FORWARD.md** for the cumulative ledger.
5. **Read PANEL_AUDIT_TEMPLATE.md** for the Bo.27 cross-reference
   convention.
6. **Read all 9 SESSION_REPORTs** for the v5.23–v5.27 arc.
7. **Run the pre-flight verification** above.
8. **Spot-check 5+ random claims** from the SESSION_REPORTs against
   actual code at v5.28.0 HEAD.
9. **Write the findings.md** in their assigned subdirectory, fully
   in character.
10. **Include a Post-Production Health Assessment** — "28 versions
    after v5.0.0 release-gate, is it still good?"
11. **Bind every NEW finding to a prior-panel ID** or "(none —
    fresh)" per Bo.27 convention.

The lead agent should:

1. The `.reviews/v5.28.0/` directory + `PRE_PANEL_AUDIT.md` +
   `prompt.md` + per-reviewer subdirectories already exist.
2. Spawn all 7 reviewers IN PARALLEL with their persona, focus,
   and output file in the spawn prompt — independent context, no
   cross-contamination.
3. Wait for ALL 7 findings to land before writing README.md
   summary.
4. Compile `.reviews/v5.28.0/README.md` with verdict table,
   consensus, decision criteria check, action items, regressions,
   improvements.
5. Flag DISAGREEMENTS where reviewers conflict.
6. Include a clear **Post-Production Health Gate** verdict.
7. Write `.reviews/v5.28.0/V5_DECISION.md` with formal Option A/B
   text.
8. Do NOT start the README until every reviewer has finished.

---

## Important Context for All Reviewers

- **Repo:** github.com/Mapanare-Research/Mapanare | **Site:** mapanare.dev
- **The arc graded ships zero new MIR ops, zero new IR shapes
  beyond the Eu.\* enum-payload arms (v5.26.1 added new lowerer/
  emitter arms but no new IR primitive shapes).** Te.3.B added two
  C-runtime exports for the bootstrap brace-deprecation mirror.
- **Strict 3-stage fixed point preserved at 241,842 lines /
  0-line diff across 23 consecutive shipping releases** (CLAUDE.md
  claim — verify live with `python3 scripts/build_stage1.py &&
  bash scripts/verify_fixed_point.sh --keep`).
- **Goldens 95/95 native** (4 previously-LINK_FAIL goldens 47, 48,
  49, 51 flipped to PASS via Eu.\* in v5.26.1).
- **C runtime delta v5.22.0 → v5.27.0** — modest:
  `__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning`
  (Te.3.B.2), plus `MN_DIR_WALK_MAX_DEPTH` (Mb.4) bounds.
- **`v5.27.0` shipped with the cadence-check gate firing hard** —
  v5.28.0 explicitly closes the gap 1 minor late and acknowledges
  the trade-off (formatter polish was the wrong scope to mix with a
  panel cycle). Reviewers may grade the framing.
- **The creator is a solo developer.** Calibrate expectations, but
  do not lower the bar on correctness or safety.
- **Venezuelan-inspired naming is intentional brand identity.**
  Do not critique naming conventions.
- **Focus on actionable feedback**, not just complaints.
- **Every CRITICAL or HIGH must include a suggested fix.**
- **Bind every NEW finding to a prior-panel ID** per Bo.27.

---

## Start the Reviewer

Read the per-reviewer prompt at `.reviews/v5.28.0/<reviewer>/prompt.md`.
Apply this shared brief plus the persona-specific brief. Produce
`findings.md` in the same directory. Do not commit; do not edit
source code; do not push toward conclusions.
