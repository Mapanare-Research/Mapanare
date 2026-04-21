# Mapanare Review Cadence

> **v4.31.0 Phase 3.3.** The v4.18.0–v4.26.0 hollow-features regression
> happened in an 8-version window with no external review. The arc-
> ending v4.26.0 panel was the first in 13 releases. This document
> codifies when the next panel runs, so that gap cannot reopen.

---

## The three review types

| Type | Reviewers | Scope | Trigger |
|---|---|---|---|
| **Full panel** | 7 independent reviewers covering Rust/Memory, Python/DX, C++/ABI, C/Runtime, GCC/Toolchain, LLVM/Codegen, Language Design | Whole repo: code, docs, CHANGELOG, carry-forwards, CI, bench, process | See "Full-panel triggers" below |
| **Delta review** | 1 reviewer, focused lens | The diff that introduces the new syntax + any touched lowering / emit / doc path | See "Delta triggers" below |
| **Recovery review** | 7 reviewers, same format as full panel | Whole repo | Any non-unanimous full-panel verdict (≥ 1 NEEDS WORK or REJECT) automatically queues the next recovery review |

## Full-panel triggers

Run a full 7-reviewer panel when ANY of the following is true:

1. **Every 5 minor versions.** From v4.31.0, the next scheduled full
   panel is at v5.1.0 (5 minors after v4.31.0). Skipping is not
   allowed — if v5.1.0 is delayed, the panel runs at whichever tag is
   current when the 5-minor window closes.
2. **Before any release tagged `>=` a previous major.** `v5.0.0`
   requires a full panel on the immediately-prior v4.x tag as its
   release gate. No exceptions — the major bump is what the panel
   validates.
3. **Five language-feature releases since the last panel.** "Language
   feature" means a new keyword, a new AST node, or a new MIR
   instruction kind. Bug-fix and refactor releases don't count
   toward this threshold, even if they span many versions.
4. **Any reviewer on the most-recent panel gave a NEEDS WORK verdict
   (recovery-arc rule).** The next panel runs when the recovery arc
   closes — at the first "zero NEEDS WORK" shipping release. That is
   how v4.31.0 became the re-entry point after v4.26.0.

## Delta triggers

Run a focused 1-reviewer delta review when the diff meets EITHER of:

1. **Adds a new keyword to `mapanare.lark`.** The reviewer pulls the
   `culebra scan --severity high` output on the regenerated
   `main.ll`, plus the new keyword's lowering + emission path, plus
   the new golden test that exercises it. Verdict is pass/fail,
   not scored. Failing deltas block the merge.
2. **Adds a new `@decorator` that changes MIR.** Same lens as keyword
   additions.

## Why these numbers

- **5 minor versions** is roughly the velocity at which the
  v4.18.0-v4.26.0 regression accumulated: 6 hollow features in 8
  versions. A 5-minor cadence catches the next regression before it
  reaches 8. If the velocity changes, this number changes.
- **Before any major** is a hard rule because majors are when
  user-facing contracts change. A major with a silent hollow feature
  is a trust-destroying release.
- **Delta reviews on new syntax** are the cheap insurance: one
  reviewer, one lens, one hour. Most of the v4.18.0–v4.26.0 regression
  was hollow *syntax*; a per-syntax delta review catches it at the
  PR where it was introduced, not 8 versions later.

## How to run a full panel

1. Copy `.reviews/prompt.md` and substitute the target version
2. Create `.reviews/vX.Y.Z/` with one file per reviewer:
   `01-viper.md`, `02-boa.md`, `03-cobra.md`, `04-mamba.md`,
   `05-anaconda.md`, `06-rattler.md`, `07-coral.md`
3. Each reviewer gets the prompt + the repo state at the target tag.
   Reviewers do NOT see each other's output during review — the panel
   is parallel, not collaborative
4. After all 7 files are in, write `.reviews/vX.Y.Z/README.md` as the
   panel summary: verdict table, overall consensus, health gate,
   carry-forward deltas from the previous panel, disagreements,
   severity split
5. Update `.reviews/CARRY_FORWARD.md` with the new items the panel
   surfaced and the items the panel confirms closed

## How to run a delta review

1. Identify the reviewer whose lens most directly covers the change
   (e.g. Rattler for emitter changes, Anaconda for build/toolchain,
   Coral for language design)
2. Give the reviewer: the PR diff, the relevant golden test, the
   Culebra scan against the regenerated `main.ll`, and a two-line
   summary of intent
3. Reviewer returns a single file at `.reviews/deltas/vX.Y.Z-<topic>.md`
4. Non-passing deltas block the PR. The PR must either fix the issue
   or provide a justification that the delta reviewer re-reviews

## When this cadence itself changes

This document is versioned. Any change to the cadence requires a full
panel's blessing — the cadence cannot be loosened by a lead alone,
because the v4.18.0–v4.26.0 regression started with a lead's judgment
that "we don't need a review for this one."

---

## The next scheduled panel

| Scheduled | Trigger | Target |
|---|---|---|
| v4.31.0 | Recovery-arc terminator (every reviewer on v4.26.0 gave ≥ 1 NEEDS WORK) | **Run at v4.31.0 tag** — the recovery arc is incomplete until the panel signs off |
| v5.0.0 | Release-gate rule #2 (before any major) | Run at the last v4.x tag that precedes the v5.0.0 release |
| v5.1.0 | 5-minor cadence from v4.31.0 (assuming v4.31.0 passes) | Counted as a routine panel, not a recovery panel |

If the v4.31.0 panel returns NEEDS WORK, the recovery arc extends into
v4.32.0 and the above schedule shifts accordingly.
