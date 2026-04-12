# Post-Recovery Master Prompt — Execute v4.32.0 → v4.76.0

> **Read this BEFORE reading any individual vX.Y.Z/PROMPT.md.** This
> prompt supersedes `RECOVERY_MASTER_PROMPT.md` (which covered v4.27.0–
> v4.31.0). The recovery arc is over. v4.32.0 starts the post-recovery
> plan — 45 releases across 9 arcs ending at v4.76.0.
>
> **Each version has its own PLAN.md and PROMPT.md.** Read this master
> once per session. Read the release's own PROMPT.md + PLAN.md when
> starting work on a release. The PLAN.md has the tasks; the PROMPT.md
> has the release-specific context; this document has the persistent
> discipline.
>
> **You can execute one version at a time or multiple in a row.** The
> plan is sequenced — v4.X.0 cannot open until v4.(X-1).0's exit
> criteria are all green — but you can burn through a growth arc (e.g.,
> v4.37.0 → v4.41.0) in one working session if the scope permits, as
> long as each release closes cleanly before the next opens.

---

## Why this plan exists

The recovery arc closed at v4.31.0 with a 9.343/10 aggregate panel verdict
(up from ~8.2 at v4.26.0 — the largest single-cycle improvement in
project history). The recovery was a success. The question now is: what
discipline carries forward?

**Everything.** The anti-rush rules, the CI gates, the delta reviews,
the panel cadence, the `CARRY_FORWARD.md` ledger discipline — all of it.
The recovery arc wasn't a special one-time mode; it was the beginning
of how Mapanare ships releases.

v4.32.0 → v4.76.0 is the proof. 45 releases. 9 thematic arcs. 9
scheduled panels. 8 delta reviews on new-syntax releases. Every release
closes 2-3 LOW items from the running `CARRY_FORWARD.md` queue. Every
release passes all 8 CI gates. Every release has a pre-committed
`SESSION_REPORT.md` that is fact-checkable against file:line.

**The major-version bump is a labeling decision, not a scope decision.**
Everything the original roadmap scheduled for v5.0.0 — real async/await,
DWARF, Python emitter removal, llvmlite removal, real `const`, A7/A8/A9
drain — all of it ships in v4.x. The lead can tag v5.0.0 at any arc
close with no additional work.

---

## The 9 arcs at a glance

| Arc | Versions | Theme | Panel | Growth type |
|---|---|---|---|---|
| 1 | v4.32.0 → v4.36.0 | Error handling + pattern matching | **v4.36.0** | bug close + language core |
| 2 | v4.37.0 → v4.41.0 | LSP maturity | **v4.41.0** | developer experience |
| 3 | v4.42.0 → v4.46.0 | Tensor completeness | **v4.46.0** | language primitive finish |
| 4 | v4.47.0 → v4.51.0 | Stdlib AI/LLM | **v4.51.0** | library surface |
| 5 | v4.52.0 → v4.56.0 | Compiler debt drain (A7/A8/A9 + real `const`) | **v4.56.0** | debt drain |
| 6 | v4.57.0 → v4.61.0 | Deprecation + deletion (Python emitter + llvmlite) | **v4.61.0** | debt drain |
| 7 | v4.62.0 → v4.66.0 | DWARF debug info | **v4.66.0** | capability |
| 8 | v4.67.0 → v4.71.0 | Coroutine foundation | **v4.71.0** | capability prep |
| 9 | v4.72.0 → v4.76.0 | Coroutine completion (real async/await) | **v4.76.0** | capability finish |

Each arc is **3 feature/work releases + 1 consolidation release + 1 panel release** or **4 feature/work releases + 1 panel release**. The fifth release is always a scheduled panel per `.reviews/REVIEW_CADENCE.md`.

Full context: [`POST_RECOVERY_ROADMAP.md`](./POST_RECOVERY_ROADMAP.md).

---

## Anti-rush rules (these are permanent, not recovery-arc-specific)

The recovery arc rules are still the rules. The recovery arc wasn't
special — it was just the first time the rules were enforced.

1. **No scope creep.** If a task is not in the active version's
   PLAN.md exit criteria, it goes to the next version. Period. The
   v4.18.0–v4.26.0 regression died from "while I'm in here"
   improvements.

2. **Every CHANGELOG entry must point at a real test file.** Before
   committing, run `git ls-files tests/ | grep <claimed_test>` for
   every test mentioned in your draft entry. `scripts/check_changelog_honesty.py`
   (v4.31.0+) enforces this as a CI gate. Don't wait for CI to catch a
   claim you could have verified locally.

3. **`raise NotImplementedError` is a bug, not a feature.** If you
   write one, you have not shipped the feature. Either implement it or
   delete the syntax that gets you to the raise site. `scripts/check_no_hollow_features.py`
   (v4.31.0+) enforces this as a CI gate.

4. **Every claimed-as-working feature must have a green pytest.** Not
   "the parser accepts it." Not "the lowerer doesn't crash." A pytest
   that exercises the runtime behavior the CHANGELOG describes.

5. **Delta reviews are blocking.** Any release that adds a new keyword,
   a new `@decorator`, or a new MIR instruction kind gets a delta
   review at the PR that introduces it. Per `.reviews/REVIEW_CADENCE.md`.
   Non-passing delta reviews block merge.

6. **Panel releases are deliberately quiet.** v4.36.0, v4.41.0,
   v4.46.0, v4.51.0, v4.56.0, v4.61.0, v4.66.0, v4.71.0, v4.76.0 ship
   zero new features. The panel needs a stable target. If you're
   tempted to sneak a feature into a panel release, push it to the
   next growth release.

7. **Every growth release sweeps 2-3 LOW items from the carry-forward
   queue.** The LOW tail from the v4.31.0 panel gets distributed
   across v4.33.0-v4.35.0 + v4.36.0. New LOW items added by the
   v4.36.0 panel get swept in v4.37.0-v4.40.0 + v4.41.0. And so on.

8. **`CARRY_FORWARD.md` is the single source of truth.** Every
   `SESSION_REPORT.md` appends to it. Every closure has an evidence
   pointer (file:line, test name, commit). Every deferral has a named
   tracking version.

9. **Big features break into small releases.** Coroutines take 10
   releases (arcs 8+9). Tensors take 4. LSP takes 4. DWARF takes 4.
   Debt drain takes 4-5. None of it is compressed to hit a version-
   number milestone; all of it is shippable whenever the work is
   ready.

10. **The SESSION_REPORT.md is the lead's ledger.** Every claim is
    pre-verified against file:line or test name. The next panel
    fact-checks your reports.

11. **Run `.\dev.ps1` before every commit.** Not "after I'm done with
    this batch." Every commit. The recovery arc found regressions in
    tests that were currently failing locally — that meant commits
    were going in without running validation. This rule is permanent.

12. **The lead does not self-certify arcs.** Arc closure is the
    scheduled panel's call. If the panel returns NEEDS WORK, the next
    arc compresses into a recovery-style closeout. No shame; the
    cadence is working exactly as designed.

---

## Culebra discipline (this is new — the recovery arc set it up)

Culebra is the primary diagnostic for IR-level work. Use it.

### At session start (every release)

```bash
# Baseline snapshot — capture the state you're starting from
culebra summary mapanare/self/main.ll
culebra baseline save mapanare/self/main.ll -o .culebra/v4.X.Y.0-start.json
```

Record the function count, instruction count, type count in the
release's SESSION_REPORT.md header.

### After emitter changes

```bash
# Run the fast scan — tells you if you introduced a high-severity issue
culebra scan mapanare/self/main.ll --severity high

# Diff against the baseline — shows what changed
culebra baseline diff mapanare/self/main.ll -b .culebra/v4.X.Y.0-start.json
```

If new findings appear, triage:
```bash
culebra triage mapanare/self/main.ll --brief
```

### For specific investigations

| When you need... | Run... |
|---|---|
| List of typed-pointer regressions | `culebra scan --id typed-pointer-legacy main.ll` |
| "What could cause this symptom?" | `culebra map <symptom>` |
| IR for one function | `culebra extract main.ll <function_name>` |
| Valgrind offset → struct field | `python scripts/ir_doctor.py valgrind <test>` |
| Per-function metrics | `culebra table main.ll --top 20` |
| Comparison between stage outputs | `culebra compare stage2.ll stage3.ll` |
| Control flow walk through a function | `culebra inspect main.ll --function <name>` |
| Struct layout for a crash | `culebra crashmap main.ll --struct <name>` |
| List all struct layouts | `culebra structmap` |

### Before tagging

```bash
# Full scan, SARIF format — archive for the panel
culebra scan mapanare/self/main.ll --format sarif > .culebra/v4.X.Y.0-final.sarif

# Triage — compact view the next panel reads
culebra triage mapanare/self/main.ll --brief > .culebra/v4.X.Y.0-triage.txt

# Baseline for the next release to diff against
culebra baseline save mapanare/self/main.ll -o .culebra/v4.X.Y.0-final.json
```

Archive these in the release's roadmap directory:
```bash
cp .culebra/v4.X.Y.0-*.{json,sarif,txt} docs/roadmap/v4/v4.X.Y.0/
```

### Panel releases specifically

The 9 scheduled panel releases (v4.36.0, v4.41.0, ..., v4.76.0) need
**extra** Culebra output as panel input:

```bash
# The per-arc Culebra journal (append-only across the arc's 5 releases)
cat docs/roadmap/v4/v4.X.1.0/.culebra/*.jsonl \
    docs/roadmap/v4/v4.X.2.0/.culebra/*.jsonl \
    ... \
    > .reviews/v4.X.5.0/arc_journal.jsonl

# The current summary
culebra summary mapanare/self/main.ll > .reviews/v4.X.5.0/culebra_summary.md

# Per-template closure delta
culebra baseline diff mapanare/self/main.ll \
    -b .culebra/v4.X.0.0-start.json \  # the arc-start baseline
    > .reviews/v4.X.5.0/culebra_baseline_delta.md
```

These are the three files the panel's `prompt.md` specifically lists
as pre-populated receipts.

---

## Commit discipline

### When to commit

**Phase boundaries.** Every PLAN.md breaks a release into phases
(typically 1.1, 1.2, ..., 6.1 etc.). Commit at each phase boundary.
One commit per phase is the default; more is fine if the phase is big.

Don't commit in the middle of a phase unless you're parking work
overnight — partial commits are fine as long as the WIP is explicit in
the message.

**Never skip a commit between phases.** The recovery arc established
that the blast radius of a bad commit is bounded by how often you
commit. Commit often; revert cheap.

### Commit message format

```
v4.X.Y phase <N.M>: <concrete thing that shipped>

<optional body with details>

<co-author line if AI-assisted per project norms>
```

Examples:
- `v4.33.0 phase 1.1: add postfix_try production to mapanare.lark`
- `v4.33.0 phase 1.4: wire TryExpr through semantic + lowering`
- `v4.33.0 phase 2.1: self-hosted lexer recognizes ? token`
- `v4.33.0 phase 3.1: add 47_try_operator.mn golden`
- `v4.33.0 phase 4.1: fix mn_signal_propagate recursion depth limit`
- `v4.33.0 phase 7: tag release`

**No "wip" commits, no "fix typo" chains.** If a typo goes in, the
next commit fixes it as part of the next phase's work. Don't commit
tiny cleanups as standalone commits — they pollute git log.

### The "every commit runs validation" rule

Before `git commit`, run:

```bash
.\dev.ps1   # Windows — runs the full validate pipeline
# OR
make test lint  # Linux/WSL
```

If anything fails, the commit waits. This is non-negotiable. The
recovery arc found tests that had been silently red for 4 days because
commits were going in without local validation.

Shortcut for development iterations (not for final commits):

```bash
# Just the things that catch 90% of issues fast
pytest tests/relevant_subdir/ -q
black --check . && ruff check .
python scripts/check_no_hollow_features.py
```

Full `.\dev.ps1` is still required before the release-tag commit.

### The release-tag commit

The final commit of every release is the tag commit:

```bash
# After all phases green + SESSION_REPORT written:
git add VERSION CHANGELOG.md docs/roadmap/v4/v4.X.Y.0/SESSION_REPORT.md .reviews/CARRY_FORWARD.md
git commit -m "v4.X.Y.0: <one-line theme>

<short description>

Closes: <comma-separated list of CARRY_FORWARD.md row numbers>
"
git tag v4.X.Y.0
# git push origin dev --tags  (if/when ready to push)
```

Don't push the tag until:
1. All CI gates green on the tag commit
2. SESSION_REPORT.md fact-checked
3. `.reviews/CARRY_FORWARD.md` updated
4. The PLAN.md exit criteria are all checked
5. **Roadmap status updated** (see below)

### Roadmap status update (mandatory, every release)

After all exit criteria are green and before pushing, update the roadmap
docs so the next session (or any reader) can see the current state at a
glance:

1. **PLAN.md** — change `**Status:** PLANNED` to `**Status:** DONE (YYYY-MM-DD)`.
   Add the `**Session log:**` and `**Decisions taken:**` fields.
2. **v4/README.md versions table** — if the version's row says `(planned)`,
   remove the `(planned)` marker. Add a one-line summary of what actually
   shipped if it differs from the plan.
3. **ROADMAP.md release history** — same: remove `(planned)` marker from the
   version's row in the release history table. If the row doesn't exist yet
   (for v4.33.0+), add one.
4. **ROADMAP.md "Where We Are" header** — bump the version number in the
   section heading to the version you just tagged.
5. **CLAUDE.md** — update the `Current Version & Roadmap` line to reflect the
   new version and its theme.

This takes ~5 minutes and prevents the drift that caused the v4.18.0–v4.26.0
regression. The principle: **docs match code at every tag, not just at review
time.**

---

## CI gates (from v4.29.0 + v4.31.0 — permanent)

Every commit on the `dev` branch goes through these gates. A PR is not
mergeable until all 8 pass:

| # | Gate | Script | Purpose |
|---|---|---|---|
| 1 | `raise NotImplementedError` absent | `scripts/check_no_hollow_features.py` step 1 | Hollow-feature prevention |
| 2 | Every `pytest.mark.skip` / `xfail` has tracking version | `scripts/check_silent_skips.py` | Test honesty |
| 3 | `Makefile RUNTIME_SOURCES` matches `ls runtime/native/*.c` | `make check-runtime-sources` | Build drift |
| 4 | `verify_fixed_point.sh` exit code propagates | `scripts/verify_fixed_point.sh` | Fixed-point ratchet |
| 5 | CHANGELOG entries point at real files | `scripts/check_changelog_honesty.py` | Editorial honesty |
| 6 | Every doc code block parses | `scripts/check_docs_drift.py` | Docs-vs-code drift |
| 7 | AST class coverage (every expression has isinstance check in lower.py) | `scripts/check_no_hollow_features.py` step 3 | Structural hollow-feature prevention |
| 8 | Optimizer non-convergence ICE | `mir_opt.py` (runtime) | Silent-failure prevention |

Don't try to bypass any of these. If one fails, **fix the root cause**.
Disabling a gate is the exact opposite of the recovery-arc lesson.

---

## Delta review process

Required for releases that add new syntax or new `@decorator`. Per
`.reviews/REVIEW_CADENCE.md`.

### Which releases have delta reviews

| Release | Reviewer | Reason |
|---|---|---|
| v4.33.0 | Coral (primary) + Rattler (backup) | `?` operator |
| v4.35.0 | Coral (primary) + Rattler (cross-check on guard fall-through) | match guards + or-patterns |
| v4.42.0 | Rattler (primary) + Coral (secondary) | tensor literal syntax |
| v4.43.0 | Rattler (primary) | multi-index syntax |
| v4.45.0 | Rattler (primary) + Coral | tensor slicing + view semantics |
| v4.55.0 | Coral (primary) + Anaconda (type-system lens) | real `const` (Path A) |
| v4.68.0 | Rattler (primary) + Anaconda + Coral | `async`/`await` grammar |
| v4.74.0 | Rattler (primary) + Coral | `for await` |

### How to execute a delta review

1. **Pre-commit**: the release's feature is implemented + tested, but
   not merged. The lead creates a branch `delta-v4.X.Y.0-<feature>`.
2. **Prep the file**: `.reviews/deltas/v4.X.Y.0-<feature>.md` as a stub
   with:
   - PR diff summary (git range from previous version)
   - Links to new files (grammar, AST, tests, goldens)
   - Specific design questions the reviewer should validate
3. **Spawn the reviewer agent**: use the same pattern as full panels,
   but with a focused scope (1-hour lens vs 3-hour panel):
   ```
   Read docs/roadmap/v4/v4.X.Y.0/PLAN.md §<delta-review-phase>.
   Read the diff at <git range>.
   Read .reviews/deltas/v4.X.Y.0-<feature>.md for the questions.
   Return: PASS / PASS WITH NOTES / FAIL with specific findings.
   ```
4. **Reviewer fills in the file** with their verdict and findings.
5. **Handle the verdict**:
   - **PASS**: merge immediately
   - **PASS WITH NOTES**: merge; file the notes as v4.(Y+1).0 items
   - **FAIL**: fix the findings, re-review

### Never skip a delta review

The recovery arc's origin story: "we don't need a review for this
one." Every new syntax gets a delta review. No exceptions. Write it
into the release's commit history as proof.

---

## Full panel execution (for the 9 scheduled panel releases)

Panels run on v4.36.0, v4.41.0, v4.46.0, v4.51.0, v4.56.0, v4.61.0,
v4.66.0, v4.71.0, v4.76.0 per the 5-minor cadence.

### Panel release prep (Phase 6 in every panel release PLAN.md)

1. **Pre-panel sweep**: manual walkthrough of the arc's features;
   fix any bugs found before the panel runs. The lead is the first
   line of defense.
2. **Documentation polish**: cookbook chapters, SPEC sections,
   README updates. Every piece of user-facing documentation
   touching the arc's features gets audited.
3. **Measurement refresh**: fresh `culebra summary`, fresh benchmarks,
   fresh fixed-point diff. Record in `MEASUREMENTS.md`.
4. **LOW sweep**: final drain of the running carry-forward queue.
5. **Pre-panel audit**: fact-check every SESSION_REPORT.md claim from
   the arc's previous 4 releases against file:line. Write
   `PRE_PANEL_AUDIT.md`. If anything fails, fix before panel runs.
6. **Pre-populate `.reviews/v4.X.Y.0/`**:
   ```
   .reviews/v4.X.Y.0/
     culebra_summary.md
     culebra_baseline_delta.md
     arc_journal.jsonl
     MEASUREMENTS.md
     LEDGER_AUDIT.md
     PRE_PANEL_AUDIT.md
   ```
7. **Retarget `.reviews/prompt.md`** to the new version. Keep the
   recovery-arc framing: reviewers fact-check SESSION_REPORT claims.
8. **Spawn 7 reviewers in parallel** (Agent tool). Each reads:
   - Their previous-panel review file (`.reviews/v4.X-5.Y.0/NN-codename.md`)
   - The arc's SESSION_REPORTs
   - The relevant source files per their lens
   - The pre-populated files above
9. **Wait for all 7 to complete**, then write `.reviews/v4.X.Y.0/README.md`
   with the verdict table, consensus, action items.

### After panel: handling the verdict

**If PASS (aggregate ≥9.0, zero NEEDS WORK):**
- Arc closes. Next release opens.
- The panel's new action items go into `CARRY_FORWARD.md` as LOW/MEDIUM
  rows to be swept in the next arc.
- Update `docs/roadmap/v4/README.md` with the arc-close row.

**If PASS WITH NOTES (aggregate ≥9.0, zero NEEDS WORK, some notes):**
- Same as PASS. The notes go into `CARRY_FORWARD.md`.

**If NEEDS WORK (any reviewer gives NEEDS WORK, OR aggregate < 9.0):**
- Recovery protocol re-engages.
- The next release becomes a recovery-style closeout (like v4.27.0 was
  for the v4.26.0 panel).
- The next arc's theme slides by 1-2 versions.
- Write a new recovery PLAN.md for the closeout version.
- Continue panel runs on the same 5-minor cadence (the next arc still
  ends with a panel; it just might be grading more work than planned).

---

## Read-first list (every session, before you start coding)

1. This file (`POST_RECOVERY_MASTER_PROMPT.md`) — if it's been more
   than a week since you last read it
2. `docs/roadmap/v4/POST_RECOVERY_ROADMAP.md` — the 45-release overview
3. `docs/roadmap/v4/v4.X.Y.0/PROMPT.md` — the release you're about to
   execute
4. `docs/roadmap/v4/v4.X.Y.0/PLAN.md` — the release's task list
5. `docs/roadmap/v4/v4.(X-1).Y.0/SESSION_REPORT.md` — the previous
   release's report (for continuity)
6. `.reviews/CARRY_FORWARD.md` — the ledger (for the LOW sweep selection)

Plus (if applicable):
- The previous 7-reviewer panel's `README.md` if you're within 5
  releases of a panel run
- The arc's DESIGN.md if the release is part of a design-heavy arc
  (v4.34.0 for match, v4.55.0 for `const`, v4.62.0 for DWARF, v4.67.0
  for coroutines)

---

## Session Summary Protocol (every release)

Every release produces a `SESSION_REPORT.md` in its roadmap directory.
Template:

```markdown
# vX.Y.Z Session Report — <date>

## Verdict
- [self-graded aggregate — target ≥9.0 on the internal smoke check]
- [new `CARRY_FORWARD.md` rows closed this release]
- [new LOW items from the v4.31.0 panel still open after this release]

## Completed
- [list of completed phases with file paths + line numbers]

## Carry-forward closed
- [items from .reviews/CARRY_FORWARD.md that are now CLOSED]
- [each with evidence pointer: file:line, test name, commit]

## Carry-forward still open
- [items still OPEN with tracking version]

## Measurements
- [IR line count before/after]
- [Golden test count]
- [Stage2 module count]
- [Fixed-point diff line count]
- [Pytest pass count]
- [Culebra findings count]

## Decisions Made
- [every Path A/Path B or similar decision with rationale]

## Verification Results
- [output of key proof commands from PLAN exit criteria]
- [lint results]
- [golden/stage2 results]
- [delta review result if applicable]

## Tool discipline retrospective
- [what Culebra commands were run]
- [what raw commands were run]
- [ratio; notes for next session]

## Next Session Should Start With
- [Read POST_RECOVERY_MASTER_PROMPT.md if > 1 week]
- [Read docs/roadmap/v4/v(next).0/PLAN.md]
- [Read docs/roadmap/v4/v(next).0/PROMPT.md]
- [Specific blockers or context for the next phase]
```

Don't skip sections. Don't add sections. The panel reads these — they
need to be consistent across releases for fact-checking.

---

## What this plan does NOT do

- **Commit to dates.** Timing is not the plan's strong suit. Each
  release ships when its exit criteria are green.
- **Pre-decide v5.0.0.** The major-version bump is the lead's call at
  any arc close.
- **Require multi-release batches.** You can execute one release at a
  time or burn through a whole arc in one session. Both are fine as
  long as each release closes cleanly before the next opens.
- **Lock the post-v4.76.0 plan.** Whatever happens after arc 9 close
  is open. Could be more v4.x arcs. Could be v5.0.0. Could be both.

---

## After v4.76.0

**The 45-release plan ends.** The recovery-arc discipline has now
been the normal operating mode for 45 releases. Every feature shipped
had a delta review. Every 5 minors got a panel. Every carry-forward had
a tracking version. Eight CI gates caught regressions at PR time.

Whatever comes next — more growth, another major, a second recovery
arc, a multi-year stability release — the playbook is the same:

- Plan → Prompt → Session Report per release
- Delta review per new syntax
- Full panel per 5-minor cadence
- CARRY_FORWARD.md as the single source of truth
- Culebra as the primary IR diagnostic
- Validation before every commit
- SESSION_REPORT.md as the lead's ledger

The plan was never really about the features. It was about the
cadence. The cadence works.
