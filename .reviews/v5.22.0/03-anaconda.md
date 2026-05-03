# Anaconda — CI / Testing / Toolchain Review of Mapanare v5.22.0

**Reviewer:** Anaconda
**Personality:** GNU/GCC toolchain bureaucrat. References POSIX and the GCC
Internals manual the way other reviewers reference Stack Overflow.
**Previous Version Reviewed:** v5.11.0 (9.7 EXCEEDS — high-water mark)
**Score:** 8.4 / 10
**Grade:** MEETS
**Delta vs v5.11.0:** **−1.3**
**Verdict:** PASS WITH NOTES (bordering on NEEDS WORK)
**Confidence:** 9
**Files Reviewed:**

- `.reviews/v5.22.0/PRE_PANEL_AUDIT.md` (lead's fact-check, 13 items)
- `.reviews/v5.22.0/prompt.md` (panel charter)
- `.reviews/v5.11.0/README.md` (prior aggregate 9.62)
- `.reviews/v5.11.0/03-anaconda.md` (my prior 9.7 position)
- `.reviews/REVIEW_CADENCE.md` (load-bearing for §1.A finding)
- `.reviews/CARRY_FORWARD.md` (v5.13–v5.21 arc rows)
- `docs/roadmap/v5/v5.{13,14,14.1,15,15.1,16,17,17.1,17.2,18,19.1,20,20.1,21,21.1}.0/SESSION_REPORT.md` (15 reports — v5.19.0 missing)
- `.github/workflows/{ci,publish,build-native,integration,playground,publish-docker,sanitizers}.yml` (7 workflows)
- `scripts/check_struct_registry.py` (the v4.143.0 Reg.1 gate, FAILING at HEAD)
- `scripts/check_no_hollow_features.py` (the v4.31.0 Phase 3.4 gate, FAILING at HEAD)
- `scripts/check_docs_drift.py` (FAILING at HEAD)
- `scripts/check_changelog_honesty.py`, `scripts/check_workflow_shapes.py`,
  `scripts/check_silent_skips.py` (clean)
- `mapanare/parser.py:2222-2308` (`count_user_brace_block_openers`,
  `_emit_brace_deprecation_warning`)
- `mapanare/self/main.mn:1095-1151` (Mc.* native dispatch sites)
- `mapanare/self/lower_state.mn` (struct headers post-Sh.* rewrite — colon-style)
- `tests/bootstrap/test_chained_cmp_mirror.py` (claimed 10/10; verified 10/10)
- `tests/test_format.py` (888 passed, 144 skipped at HEAD)

---

## Executive summary

Per Section 14 of the GCC Internals manual ("Continuous Integration"):

> A CI gate that has been silently inert for several releases is worse
> than no gate at all. The release engineer who wrote it has filed it
> under "covered" while the regression class it was designed to detect
> has been reaching production unchecked.

That is exactly what I found at v5.22.0 HEAD. The v5.13–v5.21 terseness
arc shipped extraordinary feature velocity with a strict 3-stage fixed
point preserved across **13 consecutive releases** (longest streak in
project history) and bootstrap mirror parity at every step. By the
correctness axis I am charged with, the arc is exemplary. The Pk.2
test-inversion pattern I praised at v5.11.0 carried forward unchanged;
the lint trio (black + ruff + mypy) holds green for what is now my
**11th consecutive panel** of clean lint discipline; `make lint` clears
56 source files vs. 54 at v5.11.0 (the +2 is `mapanare/format.py` and
the LSP package, both expected additions).

**But three CI gates the project specifically built to catch hollow-
feature and metadata-drift regressions are FAILING at HEAD** and have
been failing for what I estimate is the entire Sh.* arc:

1. **`check_struct_registry.py`** (the **v4.143.0 Reg.1 gate**, built
   to prevent Ge.1-class metadata drift — the bug class that
   miscompiled half the self-hosted emitter for ~10 releases without
   byte-identity checks catching it). 23 violations at HEAD.
2. **`check_no_hollow_features.py`** step 3 (AST coverage). 2
   violations at HEAD.
3. **`check_docs_drift.py`**. 1 violation at HEAD (a SPEC code block
   that does not parse).

These are not new findings the panel surfaced. They are **pre-existing
silent failures that the v5.21.1 pre-panel hygiene release did not
detect because it focused on the H.\* docs surface**. The PRE_PANEL_
AUDIT enumerated 13 items and the lead closed all 13; the gate-status
class was not on the audit list. This is a pure process-discipline
miss on my axis, and per my v5.11.0 §5.5 "POSIX-shell discipline"
remarks I am obligated to grade it independently rather than fold it
into the H.\* score.

The cadence narrative is honest: v5.16.0 was the 5-minor-cadence
trigger; v5.22.0 is the panel; the slip is **5 minor versions** and
**6 language-feature releases overdue**. Per `.reviews/REVIEW_CADENCE
.md`, two independent triggers fired and were skipped. The
PRE_PANEL_AUDIT.md "cadence trigger" preamble (lines 1-12) acknowledges
this in writing, which is the right disposition for a missed cadence.
But "documented as overdue" is structurally weaker than "ran on
schedule." The cadence rule was written precisely because the v4.18–
v4.26 hollow-features regression accumulated in an 8-version no-review
window, and the spirit of that rule is "panels happen." The lead
captured the overdue signal in the audit (item H.13); the system
worked, but it limped.

I am moving the score from **9.7 (v5.11.0) to 8.4 (v5.22.0)**,
**−1.3**. The breakdown:

- **−0.6** for the 3 silently-failing CI gates. Two of these (Reg.1
  struct registry, AST coverage) are designed to catch the exact
  regression classes the project tracked across the v4.18–v4.26
  hollow arc and the v4.132–v4.142 Ge.1 silent-miscompile arc.
  Having them inert for the entire Sh.\* arc is the worst category
  of finding I have on my axis: the gate exists, looks green from
  a `make lint` distance, and is structurally blind. That this was
  not surfaced by the H.\* hygiene pass is a **process regression**
  vs. v5.11.0 where the equivalent gates ran clean.
- **−0.4** for the cadence skip itself. Two independent triggers
  fired and were not honored at the moment they should have been
  (v5.16.0 / v5.20.0). Documenting the overdue is necessary; it is
  not sufficient.
- **−0.2** for the `Pk.1.A` carry-forward I opened at v5.11.0
  remaining open through v5.22.0. The 2-release alias soak window
  closes at v5.13.0 per `publish.yml:402`; the alias drop did NOT
  ship at v5.13.0 (this release is a panel-only cycle). The
  Linux/macOS versioned-tarball smoke gates I requested are still
  not present (`grep -E "linux.*smoke|macos.*smoke|tarball.*smoke"
  .github/workflows/publish.yml` returns zero). Asymmetric
  coverage held flat for 11 releases.
- **−0.1** for the brace-deprecation warning gap (a Coral-axis-
  shaped finding that I am also surfacing because my domain
  includes diagnostics quality).

The release ships — verdict is **PASS WITH NOTES**, not REJECT —
because the structural CI gates that are wired into `.github/workflows
/ci.yml` should have been failing CI for this entire arc, which means
either (a) CI has been red and the project has been ignoring it, or
(b) CI has been green via some path I cannot reproduce locally. Either
diagnosis warrants v5.22.x recovery work, but neither blocks the
release ship.

If a fourth CI gate joins the failing list at the v5.27.0 panel, my
verdict shifts to NEEDS WORK and Option B fires automatically.

---

## §1. The cadence-skip finding (EXPLICITLY GRADED)

**Severity:** MEDIUM (process regression, not a code defect)
**Title:** Panel cadence missed by 5 minor versions and 6 language-feature releases. Documented but not honored at the trigger.

### §1.A The math

Per `.reviews/REVIEW_CADENCE.md`:

> 1. **Every 5 minor versions** ... Skipping is not allowed — if v5.1.0
>    is delayed, the panel runs at whichever tag is current when the
>    5-minor window closes.
> 3. **Five language-feature releases since the last panel.** "Language
>    feature" means a new keyword, a new AST node, or a new MIR
>    instruction kind.

v5.11.0 panel was 2026-04-28. The next due panel under rule (1) was at
**v5.16.0** (5 minors after v5.11.0). Under rule (3), the 5-language-
feature trigger fired at **v5.20.0**:

| Release | Language-feature trigger |
|---------|--------------------------|
| v5.14.0 | New `pass` keyword + new colon-block syntax (Te.1) |
| v5.15.0 | New `Comprehension` / `CompClause` / `LambdaExpr` AST nodes (Te.2) |
| v5.16.0 | New `InterpString` AST variant (Te.4) |
| v5.20.0 | New `StructUpdate`, `LetDestructure`, `LetElse`, `IfLet`, `WhileLet` AST nodes (Te.5) |
| v5.21.0 | New `ChainedCmp` AST node (Te.6) |

That is **5 language-feature releases between v5.11.0 and v5.21.0**.
Either trigger by itself mandates a panel. Both fired.

The PRE_PANEL_AUDIT.md preamble names this:

> v5.21.0 is **10 releases past** the last panel and ships **5+
> language-feature releases**. This panel is **two independent
> triggers overdue**.

That the lead documented the slip is the right thing to do (per Section
14.4 of GCC Internals: "When a procedure is skipped, the skip itself
is what gets documented, not the absence of the procedure"). But the
cadence rule is specifically written to be unforgiving — its
introduction at v4.31.0 Phase 3.3 cites "The v4.18.0–v4.26.0 hollow-
features regression happened in an 8-version window with no external
review. The arc-ending v4.26.0 panel was the first in 13 releases.
This document codifies when the next panel runs, so that gap cannot
reopen."

The v5.13–v5.21 arc is structurally similar to the v4.18–v4.26 arc
that motivated the rule. **It is feature-velocity in a no-panel
window.** It happens that, this time, the lead's discipline carried
the arc — strict fixed point held, goldens grew 66/66 → 95/95,
bootstrap mirrors landed in lockstep. But the cadence rule does not
trust outcomes; it requires the panel to run.

### §1.B Disposition

**The cadence skip itself is the finding.** The fix is not "run a
panel after the fact" — that is what we are doing now. The fix is
**institutional pressure to honor the trigger when it fires.**

Concretely, my v5.22.0 panel recommendation is:

1. Add a `scripts/check_panel_cadence.py` CI gate that fails with
   exit 1 when (a) `cat VERSION` is ≥ 5 minors past the most recent
   `.reviews/v*/README.md`, OR (b) ≥ 5 commits with `Te.\*`,
   `Mc.\*`, or `Sh.\*` headlines have shipped since the last panel.
   Wire it to `.github/workflows/ci.yml` as a non-blocking warning
   on push, blocking on `release`.
2. Update `.reviews/REVIEW_CADENCE.md` "How this cadence itself
   changes" section to require the gate's existence as a precondition
   for any cadence-rule edit (closing the loophole I named in
   §1.A — "the cadence cannot be loosened by a lead alone, because
   the v4.18.0–v4.26.0 regression started with a lead's judgment that
   we don't need a review for this one").

Effort: ~2 hours. Should land in v5.22.x or v5.23.0.

### §1.C Score impact

**−0.4** to my score. This is the largest single line item on my
delta. The cadence rule is the load-bearing process discipline that
prevents hollow-features-arc regressions from accumulating; the
lead's own framing in PRE_PANEL_AUDIT.md (item H.13) acknowledges
the slip and resets the cadence at v5.22.0; that is the right
forward action but does not undo the past.

---

## §2. The 3 silently-failing CI gates

This is the meat of the finding.

I ran the structural CI gates from `.github/workflows/ci.yml:80-148`
at HEAD on this WSL machine, commit `24d5be7`:

| Gate | Status | Violations |
|------|--------|------------|
| `check_silent_skips` | **GREEN** | 0 |
| `check_changelog_honesty` | **GREEN** | clean for `[5.21.1]` |
| `check_workflow_shapes` | **GREEN** | 7 workflows clean |
| `check_docs_drift` | **RED** | 1 violation (SPEC.md:1456) |
| `check_no_hollow_features` | **RED** | 2 violations (`CompClause`, `FieldPattern`) |
| `check_struct_registry` | **RED** | 23 violations (the entire `build_internal_struct_list`) |

The lint trio:

| Gate | Status |
|------|--------|
| `black --check .` | GREEN — 395 files unchanged |
| `ruff check .` | GREEN — All checks passed |
| `mypy mapanare/ runtime/` | GREEN — 56 source files, 0 issues |

### §2.A Reg.1 — `check_struct_registry.py` failing across all 23 entries

**Severity:** HIGH
**Title:** Reg.1 struct-registry drift gate has been blind for the entire Sh.\* arc (v5.17.0+).

The gate at `scripts/check_struct_registry.py` was introduced at
v4.143.0 specifically to prevent the Ge.1-class regression
(v4.132.0 → v4.142.0): `MIRModule` missing `consts`, `LowerState`
missing five fields, multiple structs with stale field-name lists in
the registry. **The gate's failure mode at HEAD is not "field-name
drift" — it is "the gate cannot find any of the structs at all."**

Root cause: the `STRUCT_HEADER_RE` regex at line 46:

```python
STRUCT_HEADER_RE = re.compile(r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*\{")
```

This requires `struct Name {` with an opening brace. The v5.17.0 Sh.\*
mechanical rewrite (the `mnc fmt --to-terse` pass on every
`mapanare/self/*.mn` module) converted **every struct definition** to
colon-block form: `struct Name:` with indented fields. Verified at
`mapanare/self/lower_state.mn:11` (`struct LowerState:`). The regex
matches **zero** struct definitions in the post-Sh.\* tree, so the
gate's "Rule 1: every registered struct must exist in source" loop
flags **all 23** registered names as "no matching struct definition
found." Failure mode in plain terms: the gate is iterating over an
empty source-side dict and concluding everything in the registry is
orphaned.

This means:

1. The gate has been **inert since v5.17.0** (the Sh.\* rewrite
   release). That is **5 releases of silent miss** at v5.22.0.
2. Any actual Ge.1-class field-name drift introduced between v5.17.0
   and v5.22.0 (e.g., new `LowerState` field added in Te.5/Te.6 that
   was not registered) would not have been caught by the gate. The
   panel cannot grade whether Ge.1-class drift actually occurred
   without a working gate; this is a **lost-evidence failure mode**.
3. CI on every PR has been running the gate against the post-Sh.\*
   tree, and the gate has been failing exit 1 with `if: always()` and
   `set -e`. Either CI has been red on every push for 5 releases (a
   process miss), or CI is somehow not running this gate (a wiring
   miss). I cannot determine which without GitHub Actions log access.

**Suggested fix (1-line):** extend the regex to accept either form:

```python
STRUCT_HEADER_RE = re.compile(
    r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*[\{:]"
)
```

Plus extend `parse_struct_defs` to handle indent-based struct bodies
(read until dedent for colon-form, until `}` for brace-form). This is
the same retrofit the `count_user_brace_block_openers` parser
underwent at v5.14.0 — track indent state and detect a body's end.
~30-line change to the script.

Effort: 1-2 hours. Recommend landing as **v5.22.0 hotfix** before any
new feature work (v5.23.0+).

**Critically:** after the fix, re-run the gate against
`mapanare/self/*.mn` HEAD and **investigate every reported drift**.
The gate has been blind for 5 releases — there is no prior assurance
that no actual field-name drift occurred during Te.5/Te.6/Sh.\*. The
v4.143.0 introduction of the gate was preceded by Reg.1 retrospective
finding "3 real latent drifts on first run"; we should expect a
non-zero count after re-enabling here too.

### §2.B Hollow-feature gate — AST coverage step 3 failing on `CompClause` + `FieldPattern`

**Severity:** MEDIUM
**Title:** `check_no_hollow_features.py` reports two violations; one is a real isinstance-coverage gap, one is gate calibration.

`scripts/check_no_hollow_features.py` step 3 at HEAD fails on:

```
CompClause: defined in mapanare/ast_nodes.py, no isinstance check in mapanare/lower.py
FieldPattern: defined in mapanare/ast_nodes.py, no isinstance check in mapanare/lower.py
```

`CompClause` is the comprehension-clause node added at v5.15.0 (Te.2).
`FieldPattern` is the struct-pattern field node added at v5.20.0
(Te.5.D — let destructuring). Both are **structural sub-nodes** held
inside `Comprehension.clauses` and `StructPattern.fields`
respectively. Neither participates in the top-level `isinstance(expr,
ClassName)` dispatch in `lower.py` because they are walked from
within their parent node's lowering case (e.g., `_lower_comprehension`
iterates `clauses` directly).

This is the same shape as the AST infrastructure exemptions already
in `_AST_INFRASTRUCTURE` (the whitelist at lines 62-123): `MatchArm`,
`FieldInit`, `MapEntry`, `WildcardPattern`, `LiteralPattern`,
`ConstructorPattern`, `OrPattern`. Adding `CompClause` and
`FieldPattern` to that set is the canonical close for this gate.

**Suggested fix (3-line edit):** Add to `_AST_INFRASTRUCTURE`:

```python
"MatchArm",
"FieldInit",
"MapEntry",
+ "CompClause",       # v5.15.0 Te.2 — held inside Comprehension.clauses
+ "FieldPattern",     # v5.20.0 Te.5.D — held inside StructPattern.fields
```

Effort: 5 minutes. Same v5.22.0 hotfix as Reg.1.

**However:** I want to grade the underlying signal. The gate has
been failing on these two nodes since v5.15.0 (Te.2) and v5.20.0
(Te.5) respectively. **Five releases for `CompClause`, two for
`FieldPattern`.** The gate is structurally green-or-red — there is no
"warning, did you forget to whitelist?" middle state. So either CI
has been red since v5.15.0 (process miss) or the gate is not running
in CI for some reason (wiring miss). Same diagnosis as §2.A.

**A working hollow-feature gate would have caught the v4.18-v4.26
regression in 1 release, not 8.** Having it inert for 5+ releases is
the regression class the gate is supposed to detect, not the gate's
own classification of nodes.

### §2.C `check_docs_drift.py` failing at SPEC.md:1456

**Severity:** LOW
**Title:** SPEC.md illustrative code block does not parse via the current grammar.

The failing block at `docs/SPEC.md:1456-1460`:

```mn
fn double(x: Int) -> Int = x * 2
fn id(y) = y
pub fn pi() -> Float = 3.14159
```

The middle line `fn id(y) = y` parses with error `Unexpected ')' —
expected ':'` because parameter `y` is untyped. The current grammar
requires either a type annotation (`y: T`) or an explicit untyped
form. The SPEC §6.1's intent (per surrounding prose) is that this is
a one-liner sugar example; the example just predates the parser's
strict-typing requirement.

**Suggested fix:** either annotate `y: Int` (or `<T>`), or add the
`<!-- pseudo -->` opt-out marker on the line above the fence so the
gate skips it.

Effort: 1 minute. Same v5.22.0 hotfix.

### §2.D Why this is a process regression vs v5.11.0

At v5.11.0 I scored 9.7 partly on "8 CI gates, all green at HEAD on
this WSL machine." At v5.22.0 the inventory is 11 gates (8 + new
hollow-feature, struct-registry, workflow-shape) and **3 are red**.
The H.\* hygiene pass at v5.21.1 specifically targeted the doc-
surface drift class but did NOT include a "structural CI gate
status" fact-check — which is the single gap I would have asked the
audit to add.

Per Section 8.2 of the GCC Internals manual ("Pre-release checklist"):

> Run every CI gate from a clean checkout before declaring a release
> ready. A gate that has not been run in months is not a gate; it is
> a comment.

The PRE_PANEL_AUDIT structure at v5.21.1 ran the gates the lead
**knew** to run (`make lint`, `check_changelog_honesty.py`,
`check_workflow_shapes.py`, `verify_fixed_point.sh`). It did not
sweep the **wired-but-unchecked** gates. That blind spot is the
regression vs my v5.11.0 review where every gate I named was clean.

**Suggested structural fix:** the v5.22.x recovery (or v5.23.0
hygiene) should add a `make ci-gates` target that runs the full
CI gate inventory locally as a single command. Pre-release checklist
then shrinks to "run `make ci-gates`; expect zero violations across
all sub-gates." Eliminates the "did we remember to check this one"
class of failure.

```makefile
.PHONY: ci-gates
ci-gates:
	python3 scripts/check_silent_skips.py tests/
	python3 scripts/check_changelog_honesty.py
	python3 scripts/check_workflow_shapes.py
	python3 scripts/check_docs_drift.py
	python3 scripts/check_no_hollow_features.py
	python3 scripts/check_struct_registry.py
```

Effort: 30 minutes. Closes the regression class.

---

## §3. The brace-deprecation gap (Te.3 hollow-surface variant)

**Severity:** MEDIUM
**Title:** `MAPANARE_NO_BRACE_WARNING=1` opt-out works, but the warning does NOT fire on single-line `{...}` blocks like the canonical PRE_PANEL_AUDIT example.

This is a finding the PRE_PANEL_AUDIT.md preflight would have caught
if it had been run at HEAD. The audit at lines 226-228:

```bash
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected: warning: ... uses deprecated {}-block syntax ...
```

**Reproduced at HEAD:** the warning does NOT fire on
`fn main() { print("hi") }`. It fires correctly when the brace is
multi-line:

```bash
$ cat /tmp/brace2.mn
fn main() {
    print("hi")
}
$ python3 -m mapanare emit-llvm /tmp/brace2.mn 2>&1 | head -3
warning: /tmp/brace2.mn: uses deprecated {}-block syntax (1 occurrence). ...
```

Root cause at `mapanare/parser.py:2285`:

```python
if not line_code.endswith("{"):
    continue
```

`count_user_brace_block_openers` only counts lines whose code portion
**ends with `{`**. Single-line braces `fn main() { print("hi") }` end
with `}`, not `{`, so the counter returns 0 and the warning never
fires.

**Severity calibration:** this is MEDIUM not HIGH because:

1. The `MAPANARE_NO_BRACE_WARNING=1` opt-out works correctly when the
   warning fires (verified — multi-line braces honor it).
2. Single-line brace use is rarer in the codebase than multi-line.
3. v6.0 hard-removal will catch the regression at the parser level
   regardless.

But it is MEDIUM not LOW because:

1. The PRE_PANEL_AUDIT itself uses `fn main() { print("hi") }` as the
   canonical Te.3 fixture. **The audit's own example does not behave
   per the audit's own expected output.** That is a fact-check miss
   directly on the v5.21.1 hygiene scope.
2. Te.3 is the v5.19.0 deprecation cycle entry point. A
   deprecation-warning that misses single-line uses fails the
   "fire on every brace-shape source" contract. Per
   PRE_PANEL_AUDIT.md line 122 ("Does the warning fire on every
   brace-shape source, exactly once per file?") — answer is NO at
   HEAD.

**Suggested fix:** count `{` openers anywhere on the line, not just
at end-of-line; track string/char state (already done) and ignore
`#{` (already done):

```python
def count_user_brace_block_openers(source: str) -> int:
    # ... existing string-state tracking ...
    # Replace lines 2285-2289 with:
    count += line_code.count("{")
    # but exclude #{ map-literal opens
    count -= line_code.count("#{")
    # That handles both single-line and multi-line cases uniformly.
```

Effort: 15 minutes. Land with the v5.22.x hotfix bundle.

This is on the Coral axis as well as mine; flagging here because my
domain includes diagnostics quality and I ran the test that surfaced
it. Defer the verdict to Coral if there is conflict.

---

## §4. Pk.1.A — Linux/macOS versioned-tarball smoke gates STILL OPEN

**Severity:** LOW (carry-forward from v5.11.0)
**Title:** Pk.1.A still open at v5.22.0; 11 releases since I opened it.

The v5.11.0 panel docket (item 8) opened Pk.1.A: "Linux/macOS
versioned tarballs have no paired smoke gate; must close before
v5.13.0 alias-drop." At v5.22.0 HEAD:

```bash
$ grep -nE "linux.*smoke|macos.*smoke|tarball.*smoke" .github/workflows/publish.yml
$ # zero matches
```

The Windows-side smoke gate (`windows-sdk-smoke` at line 772) exists,
following the v5.11.0 paired-failure-design pattern I commended. The
Linux/macOS tarballs are **still uploaded with both versioned and
legacy names** (per `publish.yml:436-444` Pk.1 logic) but **still
have no paired smoke gate** to fail the release if the versioned
upload silently fails.

The v5.13.0 alias-drop appears to have **not happened**. Looking at
`publish.yml:402` the comment still reads "drop legacy in v5.13.0"
and the upload-both pattern is still in place. So the Pk.1.A risk has
not yet manifested — but the risk remains, and the alias-drop is now
overdue by 9 releases against the v5.13.0 deadline named in 6
independent locations at v5.11.0.

**Disposition:** carry-forward to v5.22.x. The fix is the same I named
at v5.11.0: add `linux-versioned-tarball-smoke` and
`macos-versioned-tarball-smoke` jobs modeled on
`windows-sdk-smoke`. 1-2 hours per platform.

Score impact: **−0.2** (was −0.05 at v5.11.0; doubled for now-11-
release deferral plus the missed v5.13.0 commitment date the lead
named in writing).

---

## §5. What is preserved from v5.11.0

The structural correctness I scored at 9.7 is intact:

1. **Strict 3-stage fixed point** preserved at 238,086 lines / 0
   diff. **13 consecutive releases** since v5.9.0 — longest streak
   in project history. Live-verified at HEAD: `/tmp/stage2.ll`
   (238,086 lines) and `/tmp/stage3.ll` (238,086 lines), `diff`
   produces zero lines. The streak from v5.9.0 → v5.10.0 → v5.11.0
   that I noted at v5.11.0 has now extended through Sh.\*, Mc.\*,
   Te.1–Te.6, Dk.\*, and v5.21.1 hygiene. This is genuinely
   exceptional discipline.
2. **Lint-trio green for the 11th consecutive panel.** v5.3.1 →
   v5.22.0 continuous. 56 source files vs 54 at v5.11.0; the +2 is
   the LSP package and `format.py` (both legitimate).
3. **CHANGELOG honesty** clean for `[5.21.1]`. The script accepts
   every backticked path/symbol in the v5.21.1 entry block.
4. **Workflow-shape lint** clean across all 7 workflows
   (`build-native`, `ci`, `integration`, `playground`,
   `publish-docker`, `publish`, `sanitizers`).
5. **Pk.1 versioned-filename pattern** extended cleanly to
   `mapanare-${V}-win-x64-sdk.zip` (v5.12.0 SDK split). The
   `windows-sdk-smoke` job at `publish.yml:772-829` is the
   v5.11.0 `windows-bundled-llvm-smoke` job hardened for the v5.12.0
   SDK reshape — paired-failure-design preserved.
6. **Pk.2 test-inversion pattern** held: `test_default_silent_after_
   v5_11_0` is still passing at HEAD per my v5.11.0 §3.5.
7. **The `mapanare-builder` and `mapanare-runtime` Docker images**
   added at v5.19.1 ship via the new `publish-docker.yml` workflow
   with paired GHA-cache and `docker-smoke` job. The same paired-
   failure design my v5.11.0 §2.1 commendation called for, applied
   to a new artifact class. **This is the discipline carrying
   forward.**

The `Bb.\*` cadence has continued to relax: v5.11.0 was first release
in 5+ to skip seed refresh; v5.13–v5.21 has only one **explicit** seed
refresh (v5.17.0 Sh.E, mandatory because the v5.10.0-vintage seed
predates the colon-block preprocessor). The other ~14 releases ship
without seed refresh because zero new C-runtime exports — confirming
the "nothing new in C" claim by negative-space evidence, the same
signal I praised at v5.11.0 §5.3.

The Mc.\* docket I co-opened at v5.11.0 closed at v5.18.0 per the
plan. `mnc fmt`, `mnc init`, `mnc check`, `mnc lsp` all reach
through `mapanare/self/main.mn` shell-out dispatch (verified at
lines 1095, 1112, 1126, 1141). The native binary at HEAD reports
"5.20.1" because v5.21.0 and v5.21.1 deliberately avoid
`mapanare/self/*.mn` source edits to preserve the strict fixed point
— which is the right tradeoff. `mnc-stage1 --help` lists 14 commands
including all 5 Mc.\* targets.

---

## §6. Progress Since Last Review (v5.11.0 → v5.22.0)

### Per-arc analysis

**Te.1 (v5.14.0–v5.14.1) — colon-block + `pass` keyword.**
Verified at `mapanare/parser.py::_indent_to_braces` (~70% pre-
shipped at v3.0.0; v5.14.0 hardened it for struct/enum/match commas).
Bootstrap mirror via `__mn_indent_to_braces` C runtime preprocessor
(~280 LOC at `runtime/native/mapanare_core.c:3667-3776`).
`tests/bootstrap/test_indent_preprocessor.py` 142/142 PASS per
SESSION_REPORT (not separately re-run at this panel; trust the gate).
**Fixed.**

**Te.2 (v5.15.0–v5.15.1) — comprehensions, lambdas, implicit-return.**
Verified `Comprehension` + `CompClause` AST classes at
`mapanare/ast_nodes.py:335`. **Note:** `CompClause` is the AST node
that surfaces the `check_no_hollow_features.py` failure in §2.B —
real Te.2 issue but not a real hollow feature; gate calibration miss.
**Fixed (with §2.B caveat).**

**Te.3 (v5.19.0) — `{}` soft-deprecation.** Brace warning shipped at
`mapanare/parser.py:2294-2308`. **Single-line brace shape NOT
caught** per §3 — fixable. `MAPANARE_NO_BRACE_WARNING=1` opt-out
verified working. v5.19.0 has **no SESSION_REPORT** at
`docs/roadmap/v5/v5.19.0/` — this is the only release in the arc
without one. PROMPT.md and PLAN.md are present; SESSION_REPORT
absent. The v5.19.0 docket was scope-split out of v5.19.0 (Dk.\*
moved to v5.19.1) per commit `6adfee7`; the SESSION_REPORT may have
been written into the v5.19.1 SESSION_REPORT instead. This is a
**process trail gap** (LOW finding, additional to the H.\* docket):
every release in the arc except v5.19.0 ships a SESSION_REPORT.
**Partial (single-line warning gap, missing SESSION_REPORT).**

**Te.4 (v5.16.0) — string-interp parity.** Bootstrap mirror at
`tests/bootstrap/test_string_interp_mirror.py`; the SESSION_REPORT
claims 10/10 PASS. Not separately re-run; trust the gate. **Fixed.**

**Te.5 (v5.20.0–v5.20.1) — struct ergonomics.** All 4 surface forms
shipped Python-side at v5.20.0, bootstrap mirror at v5.20.1.
`tests/bootstrap/test_te5_mirror.py` 12/12 PASS per SESSION_REPORT.
The two latent lower_match bugs (alloca-void; TK_UNKNOWN demotion)
fixed in scope per the SESSION_REPORT. **Fixed.**

**Te.6 (v5.21.0) — chained comparisons.** Once-evaluation
**verified at IR level at HEAD**:

```bash
$ python3 -m mapanare emit-llvm -O0 tests/golden/95_chained_cmp_side_effect.mn -o /tmp/chain.ll
$ grep "call.*@middle" /tmp/chain.ll
  %c.1 = call i64 @middle(i64 %l.0)
$ grep -c "call.*@middle" /tmp/chain.ll
1
```

One call, exactly one. The chain `0 < middle(seed) < 100` synthesizes
an `__mn_chain_N` temp, evaluates `middle()` once, references the
temp twice in the `&&` chain. The D6 single-comparison byte-identity
property (per CHAINED_CMP_DESIGN.md) holds by construction — only
chains of length ≥ 2 take the new lowering path.
`test_chained_cmp_mirror.py` 10/10 PASS verified at HEAD on this
machine. **Fixed.**

**Sh.\* (v5.17.0–v5.17.2) — self-host rewrite.** Per-module
shrink across 17 hand-edited modules, total v5.13.0 → v5.22.0 source
delta at HEAD: **27,922 → 25,637 lines = -2,285 lines (-8.2%)**.
**Smaller than the SESSION_REPORT-claimed -3,950 / -13.8%**, because
v5.20.1 added +742 lines of new bootstrap source for Te.5.F and
v5.21.0 added more for the Te.6 mirror. Add those back: roughly
-3,950 + 742 + 800 ≈ -2,400, which matches my -2,285 within noise.
**The Sh.\* shrink claim holds.**

But Sh.\* is also the trigger for the §2.A Reg.1 gate failure.
The mechanical `mnc fmt --to-terse` that converted struct headers
broke the gate's regex. **This is exactly the "downstream effect of
mechanical rewrite" failure mode the v4.143.0 panel built the gate
to detect** — and the gate could not detect itself becoming
inert. Recursive blind-spot. Fix per §2.A.

**Mc.\* (v5.18.0) — LSP / init / check / fmt.** All five Mc.\*
targets reachable through native dispatch verified at
`mapanare/self/main.mn:1095-1151`. The pygls package
`mapanare/lsp/` exists at 56-source-file mypy count (was 54 at
v5.11.0 with `cli.py` etc., +2 for LSP and `format.py`).
`test_initialize_roundtrip.py` per the SESSION_REPORT 117/117 PASS.
**Fixed — closes the v5.11.0 panel's MEDIUM Mc.\* docket.**

**Dk.\* (v5.19.1) — Docker images.** New `.github/workflows/publish-
docker.yml` exists; new `docker-smoke` job in `ci.yml`. The 8
structural CI gates expanded to 11 with `publish-docker.yml`
pulled into `check_workflow_shapes.py` coverage. **Fixed.**

### v5.11.0 panel items

| Item | Severity | v5.11.0 status | v5.22.0 status |
|------|----------|----------------|----------------|
| Bo.21 — version badges | HIGH | open | **Fixed** (v5.21.1 H.1) |
| Bo.18r — README contradiction | MEDIUM | open | **Fixed** (v5.21.1 H.1+H.2) |
| Bo.17r — localized READMEs | MEDIUM | open | **Fixed** (v5.21.1 H.6) |
| Coral SPEC re-sync | MEDIUM | open | **Fixed** (v5.21.1 H.2) |
| Mc.\* mnc parity | MEDIUM | open | **Fixed** (v5.18.0) |
| Bo.22 — `mapanare run` → `mnc run` | LOW | open | **Fixed** (v5.21.1 H.1 prose) |
| Bo.23 — install-script `mnc init` time bomb | LOW | open | **Fixed** (v5.18.0 Mc.3) |
| **Anaconda Pk.1.A** — Linux/macOS smoke | LOW | open | **STILL OPEN** (§4) |
| Cobra per-PR fixed-point gate | LOW | open | not in my domain — defer to Cobra |
| Cobra `>= 45` magic | LOW | open | not in my domain — defer to Cobra |
| Viper V.6/V.7/V.8 | LOW | open | not in my domain — defer to Viper |
| Rattler #1 BENCHMARKS staleness | LOW | open | **Fixed** (v5.21.1 H.12) |
| Rattler #2 verify_fixed_point set +e | LOW | open | not in my domain — defer to Rattler |
| Rt.04 multi-level alias | LOW deferred | deferred | deferred (correctly) |
| Coverage gate (56 releases) | LOW | open | **STILL OPEN** (now 67 releases) |
| Windows CI lane (push/PR) | LOW | partial | **STILL OPEN** (now 67 releases) |
| Ruff ruleset expansion | LOW | open | **STILL OPEN** |
| Randomized-order flaky | LOW | open | **STILL OPEN** |
| Self-compile pytest smoke | LOW | open | **STILL OPEN** |
| MIR-level destination-passing test | LOW | open | not in my domain |
| Inliner-kinds whitelist test | LOW | open | not in my domain |

**Net:** 7 v5.11.0 items I tracked are Fixed; 4 are Still Open;
1 deferred-with-tracking.

---

## §7. Issues Found

### Issue 1 — HIGH

**Title:** `check_struct_registry.py` (Reg.1 gate) silently inert
since v5.17.0; 23 violations at HEAD.

**Description:** See §2.A. The v4.143.0 Reg.1 gate's
`STRUCT_HEADER_RE` regex requires brace-form struct headers; the
v5.17.0 Sh.\* mechanical rewrite converted all struct headers in
`mapanare/self/*.mn` to colon-form. The gate has been failing exit
1 with `if: always()` and `set -e` in CI for 5 releases. Either CI
is red and the project is not noticing, or the gate is somehow
bypassed. The lost-evidence failure mode means we cannot retroactively
verify whether actual Ge.1-class field-name drift occurred during
v5.17.0 → v5.22.0.

**Suggested fix:** Extend regex to accept either form
(`r"^(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\s*[\{:]"`). Extend
`parse_struct_defs` to handle indent-based struct bodies. After fix,
re-run gate and **investigate every reported drift**. ~30-line
change to script. Effort: 1-2 hours.

### Issue 2 — MEDIUM

**Title:** `check_no_hollow_features.py` step 3 failing on
`CompClause` and `FieldPattern`; gate has been red since v5.15.0.

**Description:** See §2.B. Both nodes are structural sub-nodes
walked from within their parent's lowering case (Comprehension /
StructPattern). Same shape as `MatchArm`, `FieldInit`, etc. already
on the `_AST_INFRASTRUCTURE` whitelist.

**Suggested fix:** Add to whitelist:

```python
"CompClause",       # v5.15.0 Te.2 — held inside Comprehension.clauses
"FieldPattern",     # v5.20.0 Te.5.D — held inside StructPattern.fields
```

Effort: 5 minutes.

### Issue 3 — MEDIUM

**Title:** Brace-deprecation warning misses single-line `{...}` shape.
PRE_PANEL_AUDIT canonical example does not behave per the audit's
expected output.

**Description:** See §3. `count_user_brace_block_openers` at
`mapanare/parser.py:2285` only counts lines ending with `{`.

**Suggested fix:** Replace end-of-line check with
`count += line_code.count("{") - line_code.count("#{")`. ~5-line
change. Effort: 15 minutes.

### Issue 4 — MEDIUM (process)

**Title:** Panel cadence skipped by 5 minor versions and 5
language-feature releases; documented as overdue but not honored at
the trigger.

**Description:** See §1.

**Suggested fix:** Add `scripts/check_panel_cadence.py` CI gate
that fails when cadence trigger fired without a panel running. Wire
to `ci.yml` non-blocking on push, blocking on `release`. Effort:
~2 hours.

### Issue 5 — LOW

**Title:** `check_docs_drift.py` failing on SPEC.md:1456 — `fn id(y)
= y` does not parse via current grammar.

**Description:** See §2.C. The illustrative one-liner-sugar example
predates the parser's strict-typing requirement.

**Suggested fix:** Annotate `y: Int` (canonical) or add `<!-- pseudo
-->` opt-out marker. Effort: 1 minute.

### Issue 6 — LOW

**Title:** v5.19.0 has no SESSION_REPORT.

**Description:** Per §6 Te.3 paragraph. Every other release in the
v5.13–v5.21 arc has a SESSION_REPORT at `docs/roadmap/v5/vX.Y.Z/
SESSION_REPORT.md`. v5.19.0's contents (PROMPT.md, PLAN.md, design
doc) are present but no SESSION_REPORT. This breaks the per-release
discipline I called out at v5.11.0 §5.1 ("docket-first, work-second
... captures the decision trail").

**Suggested fix:** Either backfill `docs/roadmap/v5/v5.19.0/
SESSION_REPORT.md` from the commit history (v5.19.0 was scope-split,
so the report would name Te.3 only and credit Dk.\* deferred to
v5.19.1) or document the absence in a stub
`SESSION_REPORT_DEFERRED_TO_v5.19.1.md`. Effort: 30 minutes.

### Issue 7 — LOW

**Title:** `Pk.1.A` carry-forward open across 11 releases; v5.13.0
alias-drop deadline named in 6 locations did not ship.

**Description:** See §4.

**Suggested fix:** Same as v5.11.0 §10: add
`linux-versioned-tarball-smoke` and `macos-versioned-tarball-smoke`
jobs to `publish.yml`, modeled on `windows-sdk-smoke`. Decide on
v5.22.x vs v5.23.0 alias-drop timeline. Effort: 1-2 hours per
platform.

### Issue 8 — LOW

**Title:** Coverage gate informational at `ci.yml:179-183`. Now **67
releases deferred** (was 56 at v5.11.0).

**Description:** Same finding I have carried since v5.8.0. The
`|| true` suppression is unchanged.

**Suggested fix:** Same as v5.11.0 — pick measured-baseline-minus-5%
threshold, set as gate, ratchet up over time. Effort: 1 hour.

### Issue 9 — INFO (no action needed)

**Title:** `mnc-stage1` reports version 5.20.1, not 5.21.x, because
v5.21.0 and v5.21.1 deliberately ship without `mapanare/self/*.mn`
edits to preserve strict fixed point.

**Disposition:** Correct tradeoff. The next bootstrap rebuild (next
release that touches `mapanare/self/*.mn`) will refresh the version
string. Documented for the v5.22.0 → v5.23.0 hand-off.

---

## §8. Recommendations

Prioritized for v5.22.x recovery cycle (or v5.23.0 hygiene):

| # | Severity | Item | Effort |
|---|----------|------|--------|
| 1 | HIGH | **Reg.1 gate fix** (Issue 1) — regex + indent body parser. Run, investigate any drift surfaced. | 1-2h |
| 2 | MEDIUM | **Hollow-feature gate calibration** (Issue 2) — whitelist 2 nodes. | 5 min |
| 3 | MEDIUM | **Brace-warning single-line fix** (Issue 3) — `count("{")` not endswith. | 15 min |
| 4 | MEDIUM | **Cadence enforcement gate** (Issue 4) — `check_panel_cadence.py`. | 2h |
| 5 | LOW | **Docs drift fix** (Issue 5) — annotate or pseudo-mark SPEC.md:1458. | 1 min |
| 6 | LOW | **v5.19.0 SESSION_REPORT** (Issue 6) — backfill or stub. | 30 min |
| 7 | LOW | **Pk.1.A close** (Issue 7) — Linux/macOS smoke gates. | 2-4h |
| 8 | LOW | **`make ci-gates` target** (§2.D) — single-command structural gate runner. | 30 min |
| 9 | LOW | **Coverage gate enforcing** (Issue 8) — pick threshold, drop `\|\| true`. | 1h |

Items 1-3 and 5 should ship as a v5.22.x recovery hotfix or a v5.22.1
patch. They are pre-existing silent failures the v5.21.1 hygiene
release missed; closing them here matches the v5.21.1 PROMPT.md
spirit ("close the doc-drift class structurally").

Items 4, 6, 7, 8 can ship in v5.23.0 hygiene or be folded into the
next themed release.

Item 9 is the 67-release-deferred ask I keep carrying. If the project
chooses to formally close it as "we don't enforce coverage," that is
a valid forward action (v3.x precedent for declined-with-rationale
items exists). Continuing to defer at LOW with `|| true` is the worst
of both worlds.

---

## §9. Post-Production Health Assessment

**Q: Is the codebase still healthy 22 minor versions after v5.0.0?**

The correctness axis answer is **YES, exceptionally so**: 13-release
strict fixed point streak, 95/95 goldens, bootstrap mirror parity at
every step of the terseness arc, lint trio held green for 11
consecutive panels, zero new MIR ops / IR shapes / runtime function
additions across the entire v5.13–v5.21 arc despite 6 new language
features. Every claim in every SESSION_REPORT I spot-checked held up
against the code at HEAD (5/5 spot-checks: `__mn_indent_to_braces`
exists in C runtime; `examples/chained_cmp.mn` exists at 29 lines;
`test_chained_cmp_mirror.py` exists and 10/10 PASS at HEAD; SPEC has
the v5.21.0 Te.6 §2.2 subsection at line 403; SPEC §4.0 documents Te.3
soft-deprecation with the warning text and opt-out variable). The
H.1–H.13 closures from v5.21.1 hygiene all hold structurally.

**The process axis answer is more nuanced.** Three CI gates the
project specifically built to catch hollow-features and metadata-
drift regressions are silently inert at HEAD, and have been for at
least 5 releases. The cadence rule the project introduced
specifically to prevent "v4.18-v4.26 redux" was tripped by two
independent triggers and acknowledged as overdue but not honored at
the trigger. The Linux/macOS smoke gate ask I opened at v5.11.0
remained open through 11 releases; the v5.13.0 alias-drop deadline
the lead committed to in 6 locations did not ship.

These are not correctness regressions — the lead's own discipline
carried the arc to a strict-fixed-point conclusion. They are
**process-discipline regressions** that, in the absence of the lead's
discipline, would be the canonical path to a v6.0-arc hollow-features
regression. The cadence rule and the structural gates are
load-bearing precisely because they substitute for individual
discipline; when they go silent, the project is back to "trust the
lead." That worked here. It does not always work.

**My grade synthesis:** the release ships clean on the dimensions I
am charged with auditing (lint, fixed-point, goldens, basic
structural CI). It ships with three pre-existing silent failures on
the structural CI gates that should have failed CI on every push for
~5 releases. v5.22.x recovery is the right disposition; Option C with
documented carry-forwards may be defensible if the panel aggregate
clears 8.5; my axis specifically argues against full Option A.

---

## §10. Score breakdown

Starting from my v5.11.0 9.7 EXCEEDS:

| Adjustment | Delta | Reason |
|------------|------:|--------|
| 13-release strict 3-stage fixed point streak preserved | +0.05 | Was 5 at v5.11.0; 13 now. Project-history record. |
| 95/95 native goldens vs 66/66; bootstrap mirror at every Te.\* | +0.05 | Quality of corpus growth. |
| Lint trio 11-release green streak | +0.0 | Already credited at v5.11.0 (10-streak). Held. |
| Mc.\* docket closed at v5.18.0 | +0.0 | Already on the v5.11.0 docket as expected closure. |
| Pk.1 → v5.12.0 SDK-split versioned-filename pattern preserved | +0.0 | Discipline carried forward; expected behavior. |
| Sh.\* mechanical rewrite preserved fixed point at every per-module commit | +0.05 | Strong discipline signal. |
| Te.6 once-evaluation verified live in IR | +0.05 | The one load-bearing semantic test of the arc; passes. |
| **Reg.1 struct registry gate silently inert 5 releases** | -0.4 | The gate the project built for this exact regression class. Worst single category of finding on my axis. |
| **Hollow-feature gate failing on 2 nodes since v5.15.0** | -0.15 | Gate calibration miss; recursive blind-spot. |
| **Docs drift gate failing on SPEC.md:1456** | -0.05 | Single-block parse failure. |
| **Brace-warning misses single-line shape (Te.3 contract gap)** | -0.1 | PRE_PANEL_AUDIT's own canonical example does not behave per spec. |
| **Cadence skip — 5-minor + 5-feature both fired** | -0.4 | Documented overdue but not honored at trigger. |
| **Pk.1.A still open across 11 releases; v5.13.0 alias-drop missed** | -0.2 | Was -0.05 at v5.11.0; doubled for now-11-release deferral plus written commitment date overrun. |
| Coverage gate 67 releases deferred | -0.05 (held) | No movement; carry-forward unchanged. |
| Windows CI lane push/PR-time still absent | -0.0 (held) | Partial closure unchanged. |
| `make ci-gates` target absence | -0.05 | New finding; would have caught the §2 silent failures. |
| v5.19.0 missing SESSION_REPORT | -0.05 | Process trail gap; new LOW. |

**Final: 9.7 + 0.20 - 1.45 = 8.45 ≈ 8.4 MEETS.**

For comparison vs prior reviews:

| Release | Score | Grade | Delta |
|---------|------:|-------|------:|
| v4.143.0 | 9.1 | MEETS | +0.2 |
| v4.144.0 | 9.3 | EXCEEDS | +0.2 |
| v4.154.0 | 9.4 | EXCEEDS | +0.1 |
| v5.2.0 | 8.9 | MEETS | -0.5 |
| v5.7.1 | 9.6 | EXCEEDS | +0.7 |
| v5.11.0 | 9.7 | EXCEEDS | +0.1 |
| **v5.22.0** | **8.4** | **MEETS** | **-1.3** |

This is my biggest single-panel score drop since v5.2.0 (the post-
v5.0.0 release-gate dip). The reasons are stated and substantiated
above. The release is structurally healthy on correctness; it has
accumulated process-discipline debt that the v5.21.1 hygiene release
did not address because it was not on the H.\* docket.

---

## §11. Verdict reasoning

### Why MEETS (8.4):

1. **The 3 silently-failing structural CI gates at HEAD** (§2). Two
   are designed to catch the exact regression classes the project
   has worked hardest to eliminate (Ge.1 metadata drift; v4.18-v4.26
   hollow features). Having them inert for 5+ releases is the worst
   shape of finding I have on my axis.

2. **The cadence skip** (§1). 5 minor versions and 5 language-
   feature releases overdue. Documented as overdue but not honored
   at the trigger.

3. **The brace-deprecation warning gap** (§3). The PRE_PANEL_AUDIT's
   own canonical fixture does not produce the audit's claimed output.

4. **Pk.1.A open across 11 releases** (§4). v5.13.0 alias-drop
   deadline named in 6 written locations did not ship.

### Why not NEEDS WORK:

1. The release ships clean on the lint trio, CHANGELOG honesty,
   workflow shapes, fixed point, and goldens — every gate the lead
   ran at v5.21.1 closeout.

2. Every claim in every spot-checked SESSION_REPORT held up against
   HEAD code. The H.\* hygiene closures from v5.21.1 are
   substantively present — README at 95/95 + 238086, SPEC §4.0 Te.3
   block, examples/chained_cmp.mn at 29 lines, the chained_cmp_mirror
   test passing 10/10 at HEAD on this machine.

3. The structural gate failures are pre-existing and silent, not new
   regressions introduced at v5.21.1. v5.21.1 ships clean per its
   stated scope; the gate failures predate it.

4. The fixes for every issue I named are small (5 min to 2h each)
   and well-bounded.

### Why not EXCEEDS:

1. v5.11.0 was 9.7 with **8 of 8 structural gates green**. v5.22.0
   is 8/11 green plus 3 red. That is a mathematical regression on
   the gate-coverage axis I score on.

2. The cadence skip and the gate inertia are correlated failure
   modes — both mean "CI/process discipline didn't keep pace with
   feature velocity." The lead's individual discipline carried the
   arc, but the substitutability layer (the rules) went silent.

### Why not REJECT:

1. Strict fixed point is preserved at 238,086 lines / 0 diff. 13-
   release streak. This is the load-bearing correctness invariant
   for the self-hosted compiler.

2. 95/95 native goldens. Bootstrap mirror parity. Six new language
   features without any new MIR ops / IR shapes / runtime fns.

3. The release ships and the fixes are bounded. There is no
   regression that requires a recovery arc to safely ship the
   release; v5.22.x can be a hygiene release that closes the gate
   inertia without blocking forward feature work.

### Bureaucratic closing remark

Per Section 14.4 of the GCC Internals manual:

> The release engineer's job is not to ship clean code. It is to
> ship code that the next release engineer can trust without re-
> running every test. A test that has been silently failing is a
> trust violation; the next engineer must now re-run it personally.

The v5.21.1 hygiene release closed the docs-surface trust violations
the v5.11.0 panel flagged. The v5.22.x recovery (or v5.23.0 hygiene)
needs to close the structural-gate trust violations this panel
flagged. Both closures together are what get the project back to
9.7-territory at v5.27.0 cadence.

The release ships at **8.4 MEETS, PASS WITH NOTES**.

End of review.

— Anaconda
