# Mapanare v5.22.0 — 7-Reviewer Panel Prompt

> Paste this entire prompt into Claude Code with agent teams enabled.
> Make sure you are at the **v5.22.0 HEAD** of the Mapanare repository
> before running. v5.21.1 hygiene must have shipped first; if not,
> stop and run the v5.21.1 hygiene PLAN before this panel.

---

## Version Configuration

**TARGET VERSION:** `v5.22.0`
**ARC GRADED:** v5.11.0 → v5.21.0 (10 releases — entire terseness
arc Te.1–Te.6, plus Mc.* tooling, Sh.* self-host rewrite, v5.18.0
LSP, v5.19.0/.1 Docker, v5.20.0 struct ergonomics).
**PRIOR PANEL:** v5.11.0 (`.reviews/v5.11.0/`) — 9.62/10
aggregate, Option A, 1 HIGH (Bo.21 version badges), 3 MEDIUM
(Bo.18r README contradiction, Bo.17r localized READMEs, Coral
SPEC re-sync), ~12 LOW.

> **This is the v5.13–v5.21 terseness-arc gate panel.** The
> arc shipped six additive language features (Te.1 colon-block,
> Te.2 comprehensions/lambda/implicit-return, Te.4 string-interp
> parity, Te.3 `{}` soft-deprecation, Te.5 struct ergonomics,
> Te.6 chained comparisons) and the Sh.\* mechanical self-host
> rewrite (-3,950 lines, -13.8%) — without a single new MIR op,
> new IR shape, or runtime function. Strict 3-stage fixed point
> held across all 10 releases (longest streak in project history,
> ~228k → ~238k lines, 0-line diff at every release). Goldens
> 66/66 → 95/95.
>
> **Mechanical rule, applied verbatim:**
> - Aggregate **≥ 9.0 AND 0 NEEDS WORK** → Option A
>   (point-release health gate clears, no recovery cycle).
> - Aggregate **8.5 ≤ x < 9.0 AND 0 NEEDS WORK** → Option C
>   (release ships with documented carry-forwards).
> - Aggregate **< 8.5 OR any NEEDS WORK** → Option B (open a
>   v5.22.x recovery cycle).
>
> **Lead's target:** 9.5+. v5.7.1 panel was 9.66 (highest
> project-history aggregate); v5.11.0 was 9.62 (-0.04, driven
> entirely by docs-surface drift). The lead has shipped a
> **v5.21.1 pre-panel hygiene release** to clear the docs-drift
> class before this panel runs. The panel should fact-check
> whether v5.21.1 actually closed the class or whether the
> drift re-emerges in different shape.

Set the review output directory:

```
.reviews/v5.22.0/
  PRE_PANEL_AUDIT.md     # <-- ALREADY WRITTEN. Lead's fact-check.
                         #     Reviewers MUST read this first.
  README.md              # Summary index — written AFTER all 7 reviews land
  01-rattler.md          # LLVM IR / codegen
  02-viper.md            # Memory safety
  03-anaconda.md         # CI / testing / toolchain
  04-cobra.md            # Bootstrap / self-hosted
  05-coral.md            # Language design
  06-boa.md              # Documentation / DX
  07-mamba.md            # C runtime / performance
  V5_DECISION.md         # Formal decision text if Option A fires
```

---

## Required reading (every reviewer)

Before forming a verdict, each reviewer MUST read:

1. **`.reviews/v5.22.0/PRE_PANEL_AUDIT.md`** — the lead's own
   fact-check, listing 13 items (H.1–H.13) the lead identified
   and closed in v5.21.1 hygiene. Verify each one's claimed
   closure against the v5.22.0 HEAD.
2. **`.reviews/v5.11.0/README.md`** — the previous panel
   (9.62/10, Option A). Cross-reference every action item:
   - Bo.21 (HIGH) — version badge drift across 4 READMEs
   - Bo.18r (MEDIUM) — README internal contradiction
   - Bo.17r (MEDIUM) — localized README content drift
   - Coral SPEC re-sync (MEDIUM) — SPEC.md staleness
   - Mc.\* mnc parity (MEDIUM) — closed at v5.18.0
   - Anaconda Pk.1.A, Cobra per-PR fixed-point gate, Cobra
     `>= 45` magic, Viper V.6/V.7/V.8, Rattler #1/#2 (LOW)
3. **`.reviews/CARRY_FORWARD.md`** — the canonical docket.
   Every CLOSED item the panel sees claimed must reflect in
   the ledger; every OPEN item must be tracked.
4. **`.reviews/REVIEW_CADENCE.md`** — the cadence policy. Note
   that v5.22.0 is **5 minor versions overdue** for a routine
   cadence panel (last was v5.11.0; next due was v5.16.0).
5. **The 10 arc SESSION_REPORTs**:
   - `docs/roadmap/v5/v5.13.0/SESSION_REPORT.md` — Mc.2 mnc fmt
   - `docs/roadmap/v5/v5.14.0/SESSION_REPORT.md` — Te.1 colon
   - `docs/roadmap/v5/v5.14.1/SESSION_REPORT.md` — Te.1 mirror
   - `docs/roadmap/v5/v5.15.0/SESSION_REPORT.md` — Te.2
   - `docs/roadmap/v5/v5.15.1/SESSION_REPORT.md` — Te.2 mirror
   - `docs/roadmap/v5/v5.16.0/SESSION_REPORT.md` — Te.4 interp
   - `docs/roadmap/v5/v5.17.0/SESSION_REPORT.md` — Sh.* rewrite
   - `docs/roadmap/v5/v5.17.1/SESSION_REPORT.md` — Sh.* polish
   - `docs/roadmap/v5/v5.17.2/SESSION_REPORT.md` — Sh.H loops
   - `docs/roadmap/v5/v5.18.0/SESSION_REPORT.md` — Mc.* tooling
   - `docs/roadmap/v5/v5.19.0/SESSION_REPORT.md` — Te.3 `{}`
   - `docs/roadmap/v5/v5.19.1/SESSION_REPORT.md` — Dk.* Docker
   - `docs/roadmap/v5/v5.20.0/SESSION_REPORT.md` — Te.5 ergon
   - `docs/roadmap/v5/v5.20.1/SESSION_REPORT.md` — Te.5 mirror
   - `docs/roadmap/v5/v5.21.0/SESSION_REPORT.md` — Te.6 chained
   - `docs/roadmap/v5/v5.21.1/SESSION_REPORT.md` — Mc.7 hygiene
   - `docs/roadmap/v5/v5.22.0/SESSION_REPORT.md` — panel cycle
6. **The 6 design docs**:
   - `docs/roadmap/v5/v5.14.0/COLON_BLOCK_DESIGN.md`
   - `docs/roadmap/v5/v5.15.0/TERSENESS_DESIGN.md`
   - `docs/roadmap/v5/v5.16.0/INTERP_SPEC.md`
   - `docs/roadmap/v5/v5.18.0/MC_TOOLING_DESIGN.md`
   - `docs/roadmap/v5/v5.20.0/STRUCT_ERGO_DESIGN.md`
   - `docs/roadmap/v5/v5.21.0/CHAINED_CMP_DESIGN.md`

Each reviewer's review must explicitly note whether v5.11.0
panel items were **Fixed**, **Regressed**, **Still open**, or
**Deferred with documented tracking**.

---

## What this panel must answer (specific to v5.13–v5.21 arc)

### Correctness (Rattler / Viper / Cobra / Mamba)

- **Strict 3-stage fixed point at 238,086 lines / 0-line diff
  on v5.22.0 HEAD?** (`bash scripts/verify_fixed_point.sh --keep`)
  Held continuously since v5.9.0 — 13 releases is the longest
  streak in project history.
- **`bash scripts/build_from_seed.sh` clean** at v5.22.0 HEAD
  with the v5.17.0 Sh.E refreshed seed?
- **Goldens 95/95** through `mnc-stage1`?
  (`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`)
- **Bootstrap mirror cross-tests**: Te.5 mirror (12/12), Te.6
  mirror (added v5.21.1, 10/10), string-interp mirror (10/10),
  comprehension mirror (10/10), indent-preprocessor (142/142)?
- **Te.6 once-evaluation** verified in IR — `0 < f() < 10`
  emits exactly one `call ... @f` per chain instance?
- **Te.3 `{}` deprecation** — does the warning fire on every
  parser entry path? Once per file? `MAPANARE_NO_BRACE_WARNING=1`
  suppresses cleanly? `mnc fmt` (no flag) auto-migrates?
- **Self-hosted source shrink** verified — v5.13.0 baseline
  vs v5.17.0/v5.17.1/v5.17.2 cumulative -3,950 lines (-13.8%)
  matches `git diff --stat`?
- **Te.5 latent bugs surfaced + fixed in v5.20.1 scope**
  (lower_match alloca-void, TK_UNKNOWN demotion). Re-verify
  the fixes against the bug shapes the SESSION_REPORT
  describes.
- **No new MIR ops, no new IR shapes, no runtime fn additions**
  across the 10-release arc — verify via diff of
  `mapanare/mir.py`, `runtime/native/mapanare_core.h`, and
  `mapanare/self/mir.mn`.

### Documentation (Boa / Coral)

- **PRE_PANEL_AUDIT items H.1–H.13** all closed at v5.22.0
  HEAD? Each finding has a specific line-number / file claim
  in the audit; verify each.
- **SPEC.md header** reads "Live — synced to the v5.22.0
  cut" (not v5.7.1)?
- **SPEC.md §4.0 Block Syntax** documents the v5.19.0 Te.3
  soft-deprecation, the parser warning shape, the `mnc fmt`
  default behavior, and the `MAPANARE_NO_BRACE_WARNING=1`
  opt-out?
- **SPEC.md broken `if x: y` promise** at line 1009 either
  shipped (single-line colon-block parses) or explicitly
  rescoped to v6.0?
- **Localized READMEs (es/pt/zh-CN)** — three native-compiler
  subsections written, badge bumped, fixed-point status,
  goldens count, terseness-arc note (Te.1–Te.6 in summary)?
- **`examples/chained_cmp.mn`** present, exercises 3-/4-
  element chains + side-effect once-eval, runs through
  `mnc run` clean?
- **CHANGELOG** v5.13.0–v5.21.1 entries all honest? Run
  `python3 scripts/check_changelog_honesty.py` — every
  backticked path/symbol must exist in the v5.22.0 tree.

### Process (Anaconda / Coral)

- **Carry-forward ledger** appended for the 10-release arc?
  Every item the SESSION_REPORTs claim CLOSED matches the
  ledger?
- **Panel cadence** — was v5.16.0 (the 5-minor cadence
  trigger) skipped? If yes, was the skip documented? If
  not documented, that's a process regression Anaconda
  should grade independently.
- **CI gates** — `check_changelog_honesty.py`,
  `check_workflow_shapes.py`,
  `check_struct_registry.py` — all green at HEAD?
- **`make lint`** — black + ruff + mypy all clean? 56 source
  files at v5.21.0; verify count + clean status at v5.22.0.
- **Mc.\* mnc parity** — closed at v5.18.0 per the
  v5.11.0 panel's MEDIUM. Re-verify: `mnc lsp`,
  `mnc fmt`, `mnc init`, `mnc check`, `mnc emit-wasm` all
  reachable through native dispatch?

### Language design (Coral)

- **Te.6 chained comparisons** — Python-like semantics
  preserved? Triviality predicate matches Python verbatim
  in both compilers?
- **Te.3 deprecation cycle posture** — soft-deprecation at
  v5.19.0 plus 2-release soak window before v6.0 hard
  removal is Mapanare's documented stability policy
  (SPEC §22). Verify the policy is followed.
- **Te.1–Te.6 absorbed without grammar churn** beyond the
  documented additive surface? `git log v5.11.0..HEAD --
  mapanare/mapanare.lark` should show only additive changes
  (new keywords, new rules, no removals beyond `eq_expr`
  precedence merge in v5.21.0).
- **Coherence with the manifesto** — v5.13–v5.21 cluster
  is "small wins for the working programmer." Do the 6
  features compose? Do the SPEC examples hang together?

### Memory + runtime (Viper / Mamba)

- **Drop glue across new AST nodes** — StructUpdate,
  LetDestructure, LetElse, IfLet, WhileLet, ChainedCompare,
  Comprehension. Each desugars to existing primitives; verify
  no new leak surface.
- **`__mn_chain_N` synthesized temps** in v5.21.0 — bound
  via existing `let` machinery; re-verify drop glue runs
  cleanly under valgrind on
  `tests/golden/95_chained_cmp_side_effect.mn`.
- **C runtime delta** — `git diff v5.11.0..HEAD --
  runtime/native/` — what shipped? Just the
  `__mn_indent_to_braces` preprocessor (~280 LOC, v5.14.1)?
  Any other C additions across the arc?

---

## Mission

Create an agent team of 7 reviewers to perform a deep,
comprehensive code review of the Mapanare programming language
codebase **at the v5.22.0 tag** (post-v5.21.1 hygiene). Mapanare
is an AI-native compiled programming language where agents,
signals, streams, and tensors are first-class primitives. It
compiles to native binaries via LLVM (primary), C (fallback via
gcc), and WebAssembly (browser/server).

Self-hosted compiler is **24,748 lines of `.mn` across 17
modules** in `mapanare/self/` (v5.17.1 post-Sh.* shrink), at
**strict 3-stage fixed point at 238,086 lines for stage2.ll ==
stage3.ll** (v5.20.1 milestone, held through v5.21.0/v5.22.0).

This is **the v5.13–v5.21 terseness-arc closeout panel.**
Reviewers should hold to **arc-end verification standards**: the
question is not "is this code healthy?" — it is **"does every
claim in every v5.13.0–v5.21.1 SESSION_REPORT.md hold up against
the code that shipped at v5.22.0?"** The lead has made ~150
claims across 16 SESSION_REPORTs. Your job is to fact-check them.

**Specifically look for:**

- **Re-regression**: any v5.11.0-panel item marked CLOSED in
  `.reviews/CARRY_FORWARD.md` that is actually still open or
  has re-emerged in different shape (Bo.18 → Bo.18r at v5.11.0
  panel is the canonical example).
- **Hygiene-via-release vs hygiene-at-source**: v5.21.1 closed
  H.1–H.13 in a dedicated release. The canonical Coral and Boa
  view is that hygiene-at-source (closing the drift in the same
  release that shipped the feature) is structurally healthier
  than hygiene-via-release. Grade accordingly — the v5.21.1
  closeout is good, but it's the cleanup, not the prevention.
- **Broken forward promises**: SPEC.md:1009 promised single-line
  `if x: y` for v5.21.0; v5.21.0 shipped Te.6 instead. Does
  v5.22.0 SPEC reflect the actual state, or is the promise still
  broken?
- **Hollow Te.3 surface**: v5.19.0 deprecated `{}`. Does the
  warning actually fire on every parser entry path? CLI emits it,
  but does `mapa check`, `mnc check`, the LSP `textDocument/
  diagnostics`?
- **Asymmetric closures**: per `.reviews/CARRY_FORWARD.md` dual-
  closure convention, does any item show `PY: closed | SH: open`
  that the lead claimed symmetric?

The previous panel (v5.11.0) docked **-0.5 from Boa** for
docs-surface drift. The v5.21.1 hygiene release closes the
specific instances; the panel must judge whether the drift CLASS
has been closed structurally or just patched.

---

## The 7 Reviewers

> **Naming convention:** the panel uses snake names (Boa, Viper,
> Cobra, Mamba, Anaconda, Rattler, Coral) — established at v3.0
> and held across 14+ panels. Reviewer numbering starts at 01;
> ordering matches the v5.11.0 panel for cross-reference clarity.

### 1. "Rattler" — The LLVM Wizard
- **Domain:** LLVM IR generation, codegen, lowering correctness
- **Personality:** Insufferably smart, casually mentions LLVM
  contributions. Treats every release through "how does this
  lower?" Detailed LLVM-reference fixes when he flags issues.
- **v5.22.0 focus:** Te.6 once-evaluation in IR; the
  `__mn_chain_N` synthesized temps; the strict 3-stage fixed
  point at 238,086 lines (verify live); no new IR shapes
  introduced across Te.1–Te.6; the v5.17.0 Sh.* mechanical
  rewrite preserved IR by construction.
- **Output:** `.reviews/v5.22.0/01-rattler.md`

### 2. "Viper" — The Rust Purist
- **Domain:** Memory safety, ownership semantics, drop glue
- **Personality:** Ruthless. Every non-Rust language is a toy.
  Sarcastic, blunt, finds every potential UAF. Begrudgingly
  admits good work with "fine, that doesn't suck."
- **v5.22.0 focus:** Drop glue across new AST nodes (Te.5
  StructUpdate / LetDestructure / LetElse / IfLet / WhileLet,
  Te.6 ChainedCompare); the Te.6 `__mn_chain_N` temps under
  valgrind on the side-effect golden; v5.20.1 Te.5.F.E latent
  bugs (alloca-void, TK_UNKNOWN demotion) actually fixed; the
  `__mn_indent_to_braces` C preprocessor (~280 LOC, the only
  v5.13–v5.21 C runtime addition) is leak-clean.
- **Output:** `.reviews/v5.22.0/02-viper.md`

### 3. "Anaconda" — The GNU/GCC Toolchain Bureaucrat
- **Domain:** CI, build infrastructure, diagnostics quality,
  compiler pipeline architecture
- **Personality:** Cares about process, standards, and "doing
  things the right way." Pedantic but fair. References POSIX
  and GCC like scripture.
- **v5.22.0 focus:** Panel cadence — was v5.16.0 (5-minor
  trigger) skipped on purpose or by accident? CI gates green
  at HEAD; `check_changelog_honesty.py` clean for v5.13.0–
  v5.21.1; `check_struct_registry.py` clean; `make lint`
  green; the v5.18.0 Mc.\* tooling pack delivers what the
  v5.11.0 panel asked for.
- **Output:** `.reviews/v5.22.0/03-anaconda.md`

### 4. "Cobra" — The C++ Veteran
- **Domain:** Bootstrap / self-hosted compiler, generics,
  monomorphization, ABI
- **Personality:** Has seen every trend. Calls things "quaint"
  and "amusing." Compares everything to C++. Razor-sharp
  technical observations behind the condescension.
- **v5.22.0 focus:** Self-hosted compiler shrink (-13.8% over
  Sh.\*) — actually held? Strict fixed-point streak (13
  releases — longest project-history) live-verified.
  Bootstrap mirror cross-tests: Te.5 (12/12), Te.6 (10/10),
  comprehension (10/10), string-interp (10/10), indent-
  preprocessor (142/142) all green. Per-PR fixed-point gate —
  third-time ask at v5.11.0; status?
- **Output:** `.reviews/v5.22.0/04-cobra.md`

### 5. "Coral" — The Language Designer
- **Domain:** Language design, syntax coherence, manifesto,
  developer experience
- **Personality:** Dreamer. Languages as art. Asks "what is
  this language trying to say?" Compares to Haskell, Erlang,
  Go, Zig, Mojo. Fairest reviewer; criticism stings because
  she clearly understood the goal.
- **v5.22.0 focus:** Six features (Te.1 colon-block, Te.2
  comprehensions/lambda/implicit-return, Te.3 `{}` soft-
  deprecation, Te.4 string-interp, Te.5 struct ergonomics,
  Te.6 chained comparisons) absorbed without grammar churn?
  Coherent terseness story?  SPEC re-sync at v5.21.1 — closed
  the Coral SPEC-staleness MEDIUM from v5.11.0 structurally
  or by patch? The v5.14.0 `if x: y` broken promise — closed
  cleanly? Te.3 deprecation policy (SPEC §22 deprecation cycle
  rules) followed verbatim?
- **Output:** `.reviews/v5.22.0/05-coral.md`

### 6. "Boa" — The Python Evangelist
- **Domain:** Documentation, DX, README surface, ergonomics
- **Personality:** Happiest reviewer alive. Everything is
  "beautiful" and "Pythonic." Wraps real findings in so much
  positivity you almost miss the severity. 🐍✨ Generous with
  exclamations.
- **v5.22.0 focus:** Bo.18r (README internal contradiction) +
  Bo.21 (version badges) + Bo.17r (localized READMEs) from
  v5.11.0 — closed at v5.21.1 hygiene. Are they STAYING
  closed? Do the localized READMEs (es/pt/zh-CN) tell the
  Te.1–Te.6 story or just bump badges? `examples/
  chained_cmp.mn` present and idiomatic? CHANGELOG entries
  v5.13.0 → v5.21.1 honest? Hello-world on the front page
  uses the right invocation (`mnc run` per v5.9.1 BREAKING
  + v5.11.0 Pk.2 deprecation-note removal)?
- **Output:** `.reviews/v5.22.0/06-boa.md`

### 7. "Mamba" — The C Minimalist
- **Domain:** C runtime, performance, allocations, ABI
- **Personality:** Brutal, terse. "Delete this." Measures
  everything in unnecessary allocations. Respects simplicity.
- **v5.22.0 focus:** C runtime delta v5.11.0 → v5.22.0 —
  basically just `__mn_indent_to_braces` (~280 LOC). No
  bloat. No new allocations on the chained-compare path.
  Te.6 desugar emits zero new runtime calls. `runtime/
  native/` byte-count delta over the 10 releases?
- **Output:** `.reviews/v5.22.0/07-mamba.md`

---

## Review File Format

Each review file follows this exact format:

```markdown
# [Reviewer Name] — [Domain] Review of Mapanare v5.22.0

**Reviewer:** [Name]
**Personality:** [one-line summary]
**Previous Version Reviewed:** v5.11.0 (or "first review" if N/A)
**Score:** [X.Y / 10]
**Grade:** [EXCEEDS | MEETS | NEEDS WORK]
**Delta vs v5.11.0:** [+/- 0.X]
**Verdict:** [PASS | PASS WITH NOTES | NEEDS WORK | REJECT]
**Confidence:** [1-10]
**Files Reviewed:** [list of key files examined]

## Executive Summary
[2-3 paragraphs]

## Score: X.Y / 10

## Progress Since Last Review (v5.11.0 → v5.22.0)
[Per-arc analysis covering Te.1, Te.2, Te.3, Te.4, Te.5, Te.6,
 Sh.*, Mc.*, Dk.*. Note v5.11.0 panel items as Fixed / Regressed
 / Still open / Deferred-with-tracking.]

## What is preserved from v5.11.0
[Carry-forward verifications]

## Issues Found
[Numbered list, severity: CRITICAL / HIGH / MEDIUM / LOW]
[Format: `1. **[SEVERITY]** Title -- description`]

## Recommendations
[Actionable, prioritized]

## Post-Production Health Assessment
[Is the codebase still healthy 22 minor versions after the v5.0.0
 release-gate? Are features hollow? Does documented state match
 actual code?]

## Raw Notes
[Stream-of-consciousness, code snippets, questions]
```

---

## README.md (panel summary) format

After all 7 reviews are written, compile `.reviews/v5.22.0/
README.md`:

```markdown
# v5.22.0 Panel — v5.13–v5.21 Terseness-Arc Health Gate

> Seven-reviewer panel reviewing the **v5.11.0 → v5.21.0** arc
> (10 releases: Te.1–Te.6 + Sh.* + Mc.* + Dk.*). v5.21.1 is the
> pre-panel hygiene release; v5.22.0 is the panel-only release.
>
> **Aggregate: X.YZ / 10. Decision: Option [A|B|C].**
> Δ vs prior panel (v5.11.0): [+/- 0.YZ] (9.62 → X.YZ)

**Panel date:** [today]
**Aggregate: X.YZ / 10**
**Grade distribution: N EXCEEDS / N MEETS / N NEEDS WORK**
**Decision rule applied:** [statement]

---

## Verdict Table

| # | Reviewer | Domain | Verdict | Score | Δ vs v5.11.0 | Top findings |
|---|---|---|---|---:|---:|---|
| 1 | [Rattler](01-rattler.md) | LLVM IR / codegen | EXCEEDS | X.X | +0.0 | ... |
| ... |
| | **Aggregate** | — | — | **X.YZ** | **+/- 0.YZ** | — |

Score trajectory (last 11 panels):
6.59 → 7.87 → 8.21 → 8.21 → 8.80 → 8.86 → 9.21 → 9.37 → 9.30 →
9.66 → 9.62 → **X.YZ**.

---

## Overall Team Consensus
[Synthesized verdict]

## Post-Production Health Gate
[YES / NO / CONDITIONAL]

## Prioritized Action Items (deduplicated)
| # | Severity | Item | Reported by | Effort |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

## Disagreements
[Spread across reviewers]

## Improvements Since v5.11.0 Panel
[Axis-by-axis comparison]

## Regressions Since v5.11.0 Panel
[Anything worse]

## Decision
[Option A / B / C with formal rationale]

## Evidence
[Files / commits / commands]
```

---

## Important Context for All Reviewers

- **Repo:** github.com/Mapanare-Research/Mapanare | **Site:** mapanare.dev
- **The arc graded ships six additive language features** with
  zero new MIR ops, zero new IR shapes, zero runtime function
  additions. Every desugaring routes through existing primitives.
- **Strict 3-stage fixed point preserved across 10 consecutive
  releases.** First 13-release streak in project history at
  v5.22.0.
- **Self-hosted compiler is now 24,748 LOC** (v5.17.1 post-Sh.\*
  shrink, -13.8% off the v5.13.0 baseline). Compiles itself.
- **Goldens 95/95 native** (66 + 29 new across Te.\*).
- **C runtime delta v5.11.0 → v5.22.0 is essentially flat** —
  one new export (`__mn_indent_to_braces`, ~280 LOC, v5.14.1).
  Pe.1 budget held.
- **`v5.21.1` is the pre-panel hygiene release** — closes
  PRE_PANEL_AUDIT.md items H.1–H.13. The panel grades whether
  the closure was structural or cosmetic.
- **The creator is a solo developer.** Calibrate expectations,
  but do not lower the bar on correctness or safety.
- **Venezuelan-inspired naming is intentional brand identity.**
  Do not critique naming conventions.
- **Focus on actionable feedback**, not just complaints.
- **Every CRITICAL or HIGH must include a suggested fix.**
- The codebase is no longer trying to prove "this works" — it
  is trying to prove **"this is still healthy after 22 minor
  versions of post-v5.0.0 evolution."**

---

## Pre-flight Verification (every reviewer should run)

```bash
# Fixed-point at HEAD
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll, 238086 lines, 0 diff

# Goldens at HEAD
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: All 95 tests passed

# Bootstrap mirror cross-tests
python3 -m pytest tests/bootstrap/ -v --no-header
# expected: ~190 cases pass (Te.5 12, Te.6 10, comp 10, interp 10,
#           indent 142, plus stage1_compile 20)

# Build from seed
bash scripts/build_from_seed.sh
# expected: clean

# Lint
make lint
# expected: ruff + black + mypy clean

# CHANGELOG honesty
python3 scripts/check_changelog_honesty.py
# expected: clean for [5.22.0] and [5.21.1] sections

# Te.3 brace-deprecation flow
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: warning: ... uses deprecated {}-block syntax ...

MAPANARE_NO_BRACE_WARNING=1 python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: no warning

# Te.6 once-evaluation (load-bearing semantic test)
python3 -m mapanare emit-llvm -O0 tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
grep -c "@middle(" /tmp/chain.ll
# expected: small finite count, exactly one per chain in source
```

---

## Process Instructions

Each reviewer should:

1. **Read PRE_PANEL_AUDIT.md first** — verify each H.1–H.13
   closure claim against v5.22.0 HEAD before forming any opinion
2. **Read v5.11.0 panel README.md** for the prior-panel docket
3. **Read REVIEW_CADENCE.md** for the cadence rule
4. **Read CARRY_FORWARD.md** for the cumulative ledger
5. **Read all 16 SESSION_REPORTs** for the v5.13–v5.21.1 arc
6. **Run the pre-flight verification** above
7. **Spot-check 5+ random claims** from the SESSION_REPORTs
   against actual code at v5.22.0 HEAD
8. **Write the review** in their assigned file, fully in character
9. **Include a Post-Production Health Assessment** — "22 versions
   after v5.0.0 release-gate, is it still good?"

The lead agent should:

1. The `.reviews/v5.22.0/` directory + `PRE_PANEL_AUDIT.md`
   already exist
2. Spawn all 7 reviewers in parallel with their personality,
   focus, and output file in the spawn prompt
3. Wait for ALL 7 reviews to land before writing the README.md
   summary
4. Compile `.reviews/v5.22.0/README.md` with the verdict table,
   consensus, decision, action items, regressions, improvements
5. Flag DISAGREEMENTS where reviewers conflict
6. Include a clear **Post-Production Health Gate** verdict
7. Include a **Regressions Since v5.11.0 Panel** section
8. Do NOT start the README until every reviewer has finished
9. Do NOT clean up the team until the user confirms read

---

## Start the Team

Spawn the 7 reviewers now. Assign each their character, focus,
and output file. Let them work in parallel. Once all 7 reviews
are written, compile the `README.md` summary and the
`V5_DECISION.md` if Option A fires. Do not clean up the team
until the user confirms.
