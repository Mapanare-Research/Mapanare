# Coral — Language Design Review — v5.28.0

**Reviewer:** Coral (Language Designer. Dreamer. Languages as art.)
**Panel:** v5.28.0 RE-PANEL — v5.23.0–v5.27.0 arc graded
**Prior score:** 9.55 (v5.22.0)
**Verdict:** PASS WITH NOTES
**Score: 9.70 / 10**

---

## Executive Summary

The arc graded (v5.23.0–v5.27.0) is structural infrastructure, not language expression. Nine releases shipped: CI recovery, memory hygiene, brace-deprecation mirror, structural hygiene gates, docs cleanup, CI prevention, two codegen fixes, four LINK_FAIL closures, and formatter polish. None of these releases say anything new about what Mapanare *is*. That is the correct posture for a recovery arc.

The more important question — from a language-design lens — is whether this infrastructure *enables* the language to grow without needing recovery cycles. The answer is yes, and it is the first time that answer has been honestly earned:

- **`make ci-gates`** (9 sub-gates) structurally prevents the hollow-feature, struct-registry, docs-drift, changelog-honesty, and cadence failure modes that produced v5.22.0's -0.21 regression. Not by patching symptoms but by catching the failure class at the gate.
- **Te.3.B byte-identity contract** (11/11 tests) closes the 3-reviewer-flagged M1 hollow — Python and native now have a contractual obligation to agree on brace-deprecation behavior, enforced by a test suite that will fail the moment they diverge.
- **Eu.\* closures** fixed real language-semantic bugs in match dispatch (match on primitive subjects, or-pattern + guard dedup). These were correctness failures in the language's own control-flow semantics.
- **Bo.27 convention** (cross-reference column in PRE_PANEL_AUDIT.md) structurally prevents the v5.22.0 Bo.18r failure mode where hygiene releases patched the cited line but walked past the panel-flagged paragraph.

Infrastructure that prevents recovery cycles is infrastructure that serves the language. Score: **+0.15** from prior 9.55 → **9.70**. First time above the v5.7.1/v5.8.0 ceiling of 9.66 in the v5 series.

Two LOW findings (New.1, New.2) prevent higher. Neither affects language correctness or user experience.

---

## Score

| Category | Points | Notes |
|---|---|---:|
| M1 (Te.3 hollow) CLOSED | +0.025 | 11/11 test contract; single-line shape covered |
| M2 (manifesto coherence) CLOSED | +0.025 | Verbatim suggested fix applied at v5.24.1 Wd.1 |
| M3 (SPEC corpus brace-style) CLOSED | +0.025 | 26→0 brace block-openers; `<!-- preserve-brace -->` honored |
| L1–L5 / TR1 CLOSED | +0.025 | All Wd.3–Wd.7 closures verified at HEAD |
| Eu.* arc — language-semantic correctness | +0.025 | match-on-primitive, or-pattern+guard: real semantics fixed |
| Bo.27 + Hy.* prevention infrastructure | +0.025 | Structural prevention, not symptom-patching |
| Hygiene-via-release pattern continues | −0.025 | Mitigated by `check_doc_freshness.py` gate; not fully structural |
| New.1 (PLAN/PROMPT not amended post-Mc.8 pivot) | −0.005 | LOW; SESSION_REPORT corrects; no user-visible effect |
| New.2 (Mc.9 "sub-blocks" SESSION_REPORT imprecision) | −0.005 | LOW; behavior correct; documentation slightly loose |
| **Net from 9.55** | **+0.15** | |
| **Total** | | **9.70** |

---

## Progress Since Last Review

### M1 — Te.3 hollow / asymmetric closure (prior: MEDIUM, 3-reviewer-flagged)

**Status: FIXED (v5.23.2 Te.3.B)**

Prior state (v5.22.0): Python detector missed single-line `{...}` shapes; native `mnc-stage1` had zero brace-deprecation logic. Three independent reviewers flagged this (Coral M1, Anaconda §3, Rattler #1).

Verification at HEAD:
```
pytest tests/bootstrap/test_brace_deprecation_mirror.py -v
# 11/11 PASS — including case 'single_line' (fn main() { print("hi") })
```

The fix uses a C-runtime export (`__mn_count_user_brace_block_openers` + `__mn_emit_brace_deprecation_warning`) with the same algorithm for both Python and native — byte-identity by construction. This is the correct approach: a single source of truth in C, not two independent reimplementations that can diverge.

Synthetic-filename filter (`<...>`) prevents false-positives on the `_parse_interp_expr` recursive path. Sweep across goldens 06/81/82/84/85 confirms count=0 for colon-style code. The three test cases specifically covering edge cases (map literal `#{`, interpolation `${...}`, escaped brace) demonstrate the algorithm's precision.

**Verification commands run:**
- `pytest tests/bootstrap/test_brace_deprecation_mirror.py -v` → 11/11 PASS ✓

### M2 — Manifesto coherence (prior: MEDIUM, 3-consecutive-panel)

**Status: FIXED (v5.24.1 Wd.1)**

Prior state (v5.22.0): `docs/manifesto.md:31` read "Curly braces for blocks" for three consecutive panels. Coral's v5.22.0 report provided verbatim suggested fix.

Verification at HEAD:
```
grep -n "Indented blocks" docs/manifesto.md
# 31:  Indented blocks (with a brace-form legacy through v6.0)
```

The fix applied the verbatim Coral suggestion. The manifesto's first-impression syntax description now matches the Te.3 soft-deprecation posture. This is not cosmetic — the manifesto is a statement of the language's values. Having it say "curly braces" while the language was soft-deprecating them was a coherence failure that anyone reading the manifesto would notice.

**Verified:** `docs/manifesto.md` line 31 reads exactly "Indented blocks (with a brace-form legacy through v6.0)" ✓

### M3 — SPEC example corpus 72% brace-style (prior: MEDIUM)

**Status: FIXED (v5.24.1 Wd.2)**

Prior state (v5.22.0): 26 of 36 block-openers in SPEC.md used brace style against §4.0's colon-canonical declaration.

Verification at HEAD — the `<!-- preserve-brace -->` opt-out:
```
grep -n "preserve-brace" docs/SPEC.md
# 1069:<!-- preserve-brace -->
```

The 2 preserved brace openers are in the §4.0 "Brace style" demo block, which is exactly where they should be — showing what the deprecated form looks like. The `<!-- preserve-brace -->` opt-out mechanism is clean design: it makes the exemption explicit and machine-readable rather than relying on grep counts that could silently drift.

The `to_terse_markdown` function + `--to-terse` dispatch path on `.md` files creates a repeatable migration tool. Important: the dispatch requires explicit `--to-terse` (no auto-migration default on markdown). This is the right default — aggressive auto-migration on documentation would produce surprising diffs in CI.

**Verified:** `<!-- preserve-brace -->` present at line 1069; SPEC §4.0 uses colon-canonical style outside the preserved demo block ✓

### L1 — SPEC §27.3 Te.3 worked-example crosslink (prior: LOW)

**Status: FIXED (v5.24.1 Wd.3)**

SPEC §27.3 lines 2741-2748 contain the "Worked example (v5.19.0 → v6.0)" paragraph with crosslinks to §4.0 for migration commands. Verified at HEAD ✓

### L2 — SPEC §4.0 broken-promise wording (prior: LOW)

**Status: FIXED (v5.24.1 Wd.4)**

SPEC §4.0 now explicitly acknowledges the v5.14.0 forward promise and links the v6.0 rescope to the parser ambiguity that hard removal eliminates. Verified at HEAD (lines 1057-1063) ✓

### L3 — `mnc fmt --keep-braces` polish (prior: LOW)

**Status: FIXED (v5.24.1 Wd.5)**

SPEC §4.0 Te.3 status block gained example invocations of `mnc fmt` (auto-migrate + `--keep-braces`). Verified at HEAD ✓

### L4 — §7.4 generic-bound trait sketch (prior: LOW)

**Status: FIXED (v5.24.1 Wd.6)**

SPEC §7.4 (lines 1631+) contains the 10-line `Comparable` trait + `impl Comparable for Score` + generic `min<T: Comparable>(a: T, b: T) -> T` worked example. The Phase 0 finding (primitives aren't impl targets; `impl Comparable for Int` doesn't compile) was handled correctly by using a user-defined `Score` struct. This is honest: the example demonstrates what actually works in the language, not a speculative future that doesn't.

`examples/struct_ergo/generic_trait.mn` is present and runnable. Verified ✓

### L5 / TR1 — examples directory micro-organization (prior: LOW)

**Status: FIXED (v5.24.1 Wd.7)**

- `examples/terseness/chained_cmp.mn` (moved from root)
- `examples/struct_ergo/` (seeded by Wd.6)
- `examples/INDEX.md` (new)
- Async demos stay top-level (cited by path in cookbook/guides)

Verified at HEAD ✓

### Mc.* arc (prior: MEDIUM — 12-release carry from v5.13.0)

**Status: CLOSED (v5.27.0)**

Each item:

| Item | Status | Verification |
|---|---|---|
| Mc.1 LSP (v5.18.0) | CLOSED | `mapanare/lsp/` pygls package; 117/117 LSP tests |
| Mc.2 fmt (v5.13.0) | CLOSED | Idempotent, AST-preserving; 6 whitespace rules |
| Mc.3 init (v5.18.0) | CLOSED | Template-directory scaffolding; 15/15 init tests |
| Mc.4 check (v5.18.0) | CLOSED | `--all` recursive walk; 10/10 check tests |
| Mc.5 wasm-emit | CLOSED (rescoped v6.0) | No `emit-wasm` arm in `main.mn`; SESSION_REPORT line 259 documents rescope explicitly |
| Mc.6 Windows SDK split (v5.12.0) | CLOSED | Bundled SDK ZIP |
| Mc.7 hygiene (v5.21.1) | CLOSED | Pre-panel docs hygiene |
| Mc.8 line-length (v5.27.0) | CLOSED (detect-only pivot) | See §Mc.8 below |
| Mc.9 sort-imports (v5.27.0) | CLOSED | `sort_imports()` in `format.py`; alphabetical per block |

**Mc.5 rescope assessment:** Honest. SESSION_REPORT explicitly states "Mc.5 emit-wasm rescoped to v6.0" (line 259). The "Mc.* arc CLOSED" claim means "resolved (shipped or explicitly rescoped)," which is a defensible definition of closure.

### Mc.8 design pivot — detect-only (v5.27.0)

**Status: CLOSED (with pivot)**

**Assessment of pivot honesty: GOOD — with a minor documentation gap (→ New.1)**

The design pivot rationale is well-captured in SESSION_REPORT.md. The Phase 0 discovery that Mapanare's grammar is strictly single-line for all expressions (no implicit newline continuations inside `(`/`[`/`{`/`#{`) is real and consequential. An auto-wrap rewriter that cannot satisfy the Mc.2 AST-preservation invariant should not ship as "Mc.8 implemented" — that would be a worse kind of hollow feature. Shipping detect-only is the honest closure.

The `find_long_lines()` function is a pure read-only scan. `--check` causes non-zero exit for CI gates. `N=0` (default) disables the check. The design is clean.

**What the pivot is NOT:** It is not an admission of defeat. It is a recognition that auto-wrap requires a grammar change (newline-tolerant expressions inside grouping delimiters) that belongs in a dedicated release. The SESSION_REPORT says this explicitly. This is the correct framing.

**Minor gap:** `docs/roadmap/v5/v5.27.0/PLAN.md` Phase 2 (lines 88-95) still describes Mc.8 as conservative auto-wrapping. `PROMPT.md` line 51-52 still says "Mc.8 wraps only at clean break points." Neither was amended after Phase 0. SESSION_REPORT corrects this, but a reader of PLAN.md or PROMPT.md without SESSION_REPORT would have an incorrect mental model of what shipped. → **New.1 (LOW)**

### Tk.1 — empty `#{}` rewriter bug (prior: v5.24.1 Wd.2 carry)

**Status: FIXED (v5.27.0)**

The 6-LOC fix in `mapanare/format.py` applies the `_looks_like_stmt_block_opener` filter to the `endswith("{}")` branch, mirroring the existing filter on the `endswith(" {")` branch. `let m: Map<String, Int> = #{}` now survives `to_terse` verbatim.

The falsifiability round-trip (3 unit tests fail on pre-fix code, all pass after fix) is documented and verified. This is good engineering discipline: the tests prove the fix, not just that the fixed code happens to pass.

**Verified:** `mapanare/format.py` contains the Tk.1 fix; 3 named tests (`test_to_terse_preserves_empty_map_literal`, `test_to_terse_empty_map_literal_idempotent`, `test_to_terse_preserves_empty_struct_literal`) exist and pass ✓

### Eu.* arc (v5.26.1)

**Status: CLOSED**

Four language-semantic correctness bugs fixed:

- **Eu.1** (`emit_unwrap` on `Result<T, E>`): wrong extractvalue depth. `?` operator on Result now works correctly.
- **Eu.2** (standalone `Ok()`/`Err()` literals at call-arg sites): type width disagreement between wrapper and inner aggregate.
- **Eu.3** (match on primitive subjects): `EnumTag` extraction on `i64` was invalid LLVM. Primitive match now emits a sequential test cascade instead of a switch on a non-aggregate.
- **Eu.4** (or-pattern + guards): duplicate switch cases for same tag value. `build_match_arms` now deduplicates switch entries by tag value.

**From a language-design perspective:** Eu.3 and Eu.4 — match on primitives and or-pattern + guards — are patterns any Haskell/ML-trained programmer would use immediately. Having them silently produce invalid LLVM was a reliability failure that would have been discovered the moment someone tried to pattern-match an Int. The closures are real, correctness-critical, and regression-locked via `tests/llvm/test_async_link.py` (10/10 PASS, 0 XFAIL at HEAD).

### Te.3 deprecation cycle policy compliance

**Policy:** Soft-deprecation at v5.19.0 + 2-release soak window before v6.0 hard removal (SPEC §22).

**Status: COMPLIANT**

At v5.28.0, we are 9 releases past v5.19.0. The soak window policy (2 releases) is satisfied. v6.0 hard removal is still tracked at SPEC lines 1032, 1085, and 2744.

**Assessment:** The brace-deprecation cycle is Mapanare's first canonical worked example of its own stability policy (SPEC §22). That it now works correctly (Python ↔ native byte-identical, single-line shapes covered) and has a test contract gives developers confidence that future deprecation cycles will be handled with the same discipline. This is language credibility, not just correctness.

### Bo.27 convention — PRE_PANEL_AUDIT.md compliance

**Status: COMPLIANT**

Every H.* finding in PRE_PANEL_AUDIT.md binds to a prior-panel ID. Verified:

- H.1 (README.md:175 v5.21.0 stale) → Bo.18r-3
- H.2 (README.md:183 17 consecutive releases stale) → Bo.18r-3
- H.3 (README.md:196-197 14 consecutive releases stale) → Bo.18r-3
- H.4 (localized READMEs) → Bo.17r
- H.5 (docs/known_issues.md) → Bo.10-class
- H.6 (CARRY_FORWARD.md drift) → An.1-class
- H.7 (cadence acknowledgment) → An.1

No prior-panel HIGH or MEDIUM is silently dropped. Bo.27 convention working correctly ✓

### Cadence (6 minors since v5.22.0 — 1 minor late)

**Assessment: ACKNOWLEDGED. FRAMING IS HONEST.**

The rationale — formatter polish is the wrong scope to bundle with a panel review cycle — is documented in PROMPT.md (lines 38-45) and PRE_PANEL_AUDIT.md. The key question is whether the framing is honest or post-hoc rationalization. I judge it honest for three reasons: (1) SESSION_REPORT documents the rejection of bundling during PLAN drafting, not after the fact; (2) the Hy.3 gate itself was shipped by the same team — they built the gate that fired on them and did not disable it; (3) the trade-off is correct: a formatter polish release does not carry enough review surface to justify a full panel.

**Note:** This is the third consecutive panel where cadence has been a topic. The Hy.3 gate now makes future slips measurable and actionable. The infrastructure is correct.

### Coherence with the manifesto — does this arc enable growth?

The v5.23–v5.27 arc closes the failure modes that produced v5.22.0's -0.21 regression. From a language-design lens:

- **A language that needs recovery cycles cannot grow.** The v5.23–v5.24 recovery arc consumed 5 releases that could have been language features. The prevention infrastructure (Hy.*, Pv.*) makes future recovery cycles structurally less likely.
- **Correct semantics are table stakes.** The Eu.* closures fixed match dispatch on primitives and or-pattern + guards. A language that says "AI-native, first-class agents, signals, streams" but silently miscompiles `match n: 0 => ..., _ => ...` is not a language anyone can trust.
- **The deprecation cycle as a statement of values.** Te.3's brace-to-colon migration is Mapanare's first public commitment to "we will break things cleanly, with warnings, with migration tools, with documented timelines." Having the warning work correctly (byte-identical, all shapes) validates that commitment.

The arc does not express new language values. But it demonstrates the discipline that makes new language values trustworthy when they arrive. That is the correct use of a recovery arc.

---

## Issues Found

### New.1 — Mc.8 PLAN/PROMPT not amended after design pivot

**Severity: LOW**
**Prior-panel ID: (none — fresh)**
**Files:** `docs/roadmap/v5/v5.27.0/PLAN.md` (lines 88-95), `docs/roadmap/v5/v5.27.0/PROMPT.md` (lines 51-52)

PLAN.md Phase 2 still describes Mc.8 as a conservative auto-wrapper: "Pick two or three break points (comma, pipe, `&&`/`||`); refuse to wrap anything else." PROMPT.md line 51-52 still says "Mc.8 wraps only at clean break points." SESSION_REPORT correctly documents the Phase 0 pivot, but the planning artifacts were not amended.

**Impact:** None on language correctness or user experience. Planning documents are historical. The shipped code is correct.

**Why LOW and not MEDIUM:** The SESSION_REPORT is authoritative. The failure mode (future reader misunderstanding what Mc.8 shipped) is real but low-probability given SESSION_REPORT's clarity.

**Recommendation:** Future releases where Phase 0 pivots significantly should add a `## Phase 0 pivot` section to PLAN.md marking the pre-pivot sections as superseded.

### New.2 — Mc.9 SESSION_REPORT "sub-blocks" description imprecise

**Severity: LOW**
**Prior-panel ID: (none — fresh)**
**File:** `docs/roadmap/v5/v5.27.0/SESSION_REPORT.md` (Mc.9 section)

SESSION_REPORT: "Comments inside an import block split the surrounding block into sub-blocks — neither side reorders across the comment."

Live verification:
```python
>>> from mapanare.format import sort_imports
>>> sort_imports("import z\n// comment\nimport a\n")
'import z\n// comment\nimport a\n'
```

The mechanism is simpler: `_is_import_line()` returns False for any line not starting with "import " (including comments). A comment terminates the current block. There is no "sub-block" concept in the code. The "splits into sub-blocks" framing implies a two-pass algorithm that does not exist.

**Impact:** None on behavior. The sort is correct and idempotent.

**Recommendation:** SESSION_REPORT Mc.9 section should read: "Comments terminate the current import block; imports after the comment form a new independent block." More accurate and simpler.

---

## What is preserved

- **Strict 3-stage fixed point** at 241,842 lines / 0 diff (23-release streak) ✓
- **Goldens 95/95** (not regressed) ✓
- **Mc.2 AST-preservation invariant**: `find_long_lines()` is pure read-only; `sort_imports()` preserves all non-import content verbatim; `to_terse_markdown()` operates on fence bodies only ✓
- **Te.3 deprecation posture**: v5.19.0 → v6.0 timeline unchanged; three SPEC.md reference points intact ✓

---

## Recommendations

1. **(Low urgency)** Add `## Phase 0 pivot` amendment convention to PLAN.md template for future pivots. (New.1)
2. **(Low urgency)** Amend SESSION_REPORT Mc.9 section: "terminates the current block" not "splits into sub-blocks." (New.2)
3. **(v6.0 tracking)** Add a machine-readable Te.3 hard-removal sentinel to `check_cadence.py` or `check_doc_freshness.py` so the v6.0 timeline can't drift silently.
4. **(Language growth signal)** Mc.* and Eu.* arcs are closed. The next language-surface item: grammar lift for newline-tolerant expressions inside grouping delimiters. This unblocks Mc.8 auto-wrap and enables multi-line closures without escapes — the next step that would make Mapanare feel genuinely less constrained than Python, not just as terse.

---

## Post-Production Health Assessment

| Metric | v5.22.0 | v5.28.0 | Δ |
|---|---|---|---|
| Goldens passing | 95/95 | 95/95 | 0 |
| LINK_FAIL goldens | 4 (47,48,49,51) | 0 | -4 |
| Open HIGH | 4 | 0 | -4 |
| Open MEDIUM | 8 | 0 | -8 |
| Open LOW (non-v6.0) | ~12 | ~2 (New.1, New.2) | -10 |
| Fixed-point streak | 13 | 23 | +10 |
| CI sub-gates | 0 | 9 | +9 |
| brace-deprecation test coverage | 0 | 11/11 | +11 |
| Manifesto coherence | FAIL (line 31) | PASS | fixed |
| SPEC brace-style compliance | 72% brace | colon-canonical | fixed |

---

## Carry-Forward Status

**Watching for v5.29.0+:**

| Item | Status | Notes |
|---|---|---|
| Te.3 v6.0 hard removal | OPEN (v6.0) | Machine-readable sentinel recommended |
| Mc.8 auto-wrap (grammar lift required) | OPEN (future) | Correctly rescoped; grammar lift needed first |
| Single-line `if x: y` (v5.21.1 H.4 rescoped) | OPEN (v6.0) | Honest rescope |
| Mc.5 emit-wasm native dispatch | OPEN (v6.0) | Honestly rescoped |

All v5.22.0 Coral items (M1/M2/M3/L1-L5/TR1) CLOSED at v5.28.0 HEAD. Mc.* arc CLOSED. Eu.* arc CLOSED. Te.3 deprecation cycle policy COMPLIANT. Bo.27 convention COMPLIANT.

---

## Score Breakdown

```
Base (prior panel):     9.55
M1 Te.3 closed:        +0.025
M2 manifesto closed:   +0.025
M3 SPEC corpus closed: +0.025
L1-L5/TR1 closed:      +0.025
Eu.* correctness:      +0.025
Prevention infra:      +0.025
Hygiene-via-release:   −0.025
New.1 (LOW):           −0.005
New.2 (LOW):           −0.005
                        ─────
Final:                  9.70
```

---

## Special Note: Mc.8 Design Pivot Honesty

**Grade: B+ (HONEST, with minor documentation artifact)**

The pivot is documented in SESSION_REPORT with a table of 7 failed wrap attempts, the grammar constraint explanation, and an explicit rescope to a future release with grammar lift. The code shipped is correct. `--check` mode for CI gates is present. `N=0` default is right for a detect-only tool.

What prevents A: PLAN.md and PROMPT.md were not amended. A future session reading PLAN.md without SESSION_REPORT would have an incorrect model of what Mc.8 is. In a project with a structured review cadence and planning artifacts retained as historical record, leaving them unamended creates a gap between intent and outcome. The SESSION_REPORT is authoritative. The pivot rationale is honest. But documentation discipline is part of language-design discipline, and this is a minor lapse captured as New.1 (LOW).

---

## Verdict

**PASS WITH NOTES. Score: 9.70 / 10.**

The v5.23–v5.27 arc delivered exactly what a recovery arc should: structural prevention of the failure modes that caused the v5.22.0 regression, closure of the language-semantic correctness bugs that threatened Mapanare's match dispatch reliability, and an honest deprecation cycle that demonstrates v6.0 upgrade discipline. The arc does not express language values — but it enables them. That is the correct use of five infrastructure releases.

Two LOW findings (PLAN/PROMPT not amended post-Mc.8 pivot; Mc.9 SESSION_REPORT imprecision) prevent 9.80. Both are documentation artifacts with no user-visible effect. The language is cleaner, more correct, and better-guarded against process-discipline drift than it was at v5.22.0.

**Recommend: Option A.** No recovery cycle warranted.

---

*Coral / Language Design Reviewer / v5.28.0 panel*
