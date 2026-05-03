# v5.24.1 — Wd.* — wider docs cleanup (arc closeout)

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.24.0 shipped (Hy.\* structural hygiene
gates; `make ci-gates` GREEN at HEAD).
**Estimated effort:** 1 session (~2–3 hours).
**Arc context:** Final release in v5.23–v5.24 recovery arc.
v5.27.0 panel arrives next at routine cadence.

---

## Why this exists

The "narrative + manifesto + SPEC drift" closeout. Three of
the eight items here are **3+ consecutive panel carries**:

1. **Wd.1 — Manifesto coherence (M2)**: `docs/manifesto.md:31`
   "Curly braces for blocks" untouched against
   brace-deprecated codebase. **Coral has flagged this at
   v5.7.1 / v5.11.0 / v5.22.0** — three panels.
2. **Wd.2 — SPEC corpus (M3)**: 26 of 36 block-openers in
   `docs/SPEC.md` are brace-style against §4.0 declaring
   colon-canonical. v5.21.1 hygiene closed prose but not
   examples.
3. **Wd.8 — Bo.27 audit cross-reference column** convention
   for the v5.27.0 audit (binds H.\* hygiene findings to
   prior-panel finding IDs). Closes the structural gap that
   produced Bo.18r persistence across 3 panels.

Plus 5 LOW polish items from Coral L1–L5 / TR1.

This release is the long-running-narrative-drift closeout.
v5.27.0 panel inherits **0 HIGH / 0 MEDIUM / ~5 LOW** open
docket.

---

## Goals

1. **Wd.1** Manifesto M2 closure.
2. **Wd.2** SPEC corpus M3 closure (`mnc fmt --to-terse` over
   `docs/SPEC.md`, preserving historical examples).
3. **Wd.3–Wd.7** Coral L1–L5 closures.
4. **Wd.8** Bo.27 audit cross-reference column convention.
5. Strict 3-stage fixed point preserved at v5.23.2's line
   count (zero compiler edits).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Wd.1** | MEDIUM | **Manifesto M2** — `docs/manifesto.md:31` "Curly braces for blocks" rewrite. Two-line edit per Coral M2's suggested fix: `"Indented blocks (with a brace-form legacy through v6.0), strong static typing with inference where it helps, no semicolons where they add nothing. If you have written Rust, Go, or TypeScript, you can read Mapanare immediately."` Or: drop "Curly braces for blocks" entirely and let SPEC be the canonical syntax description. The manifesto's job is to say *why*, not *how*. **3rd consecutive panel of manifesto drift.** | 5 min |
| **Wd.2** | MEDIUM | **SPEC corpus M3** — `mnc fmt --to-terse` over `docs/SPEC.md`. 26 of 36 block-openers are brace-style. The formatter handles markdown code blocks via `tests/test_format.py` corpus iteration (cross-checked at v5.13.0). Preserve any historical-artifact examples — Chapter 27 stability discussion's brace shape is intentional history; flag with `<!-- preserve-brace -->` opt-out marker if needed. Add a `tests/test_format.py` regression case. | 30 min |
| **Wd.3** | LOW | **Coral L1** — SPEC §27 deprecation crosslink. Add a one-paragraph note pointing at Te.3 as the v5.19.0 → v6.0 worked example: `"Te.3 ({}-block soft-deprecation, v5.19.0) demonstrates this cycle: parse-time warning starting v5.19.0 → 2-release soak → hard removal at v6.0. See §4.0 for the user-facing migration path."` | 5 min |
| **Wd.4** | LOW | **Coral L2** — broken-promise wording polish at SPEC:1009 area. The v5.21.1 H.7 closure rescoped single-line `if x: y` to v6.0; the wording can be tightened with a more honest acknowledgment of the v5.14.0 forward promise. | 10 min |
| **Wd.5** | LOW | **Coral L3** — `mnc fmt --keep-braces` flag mention in §4.0 Te.3 status block. The flag is documented in the H.6 SPEC §4.0 rewrite but the example invocation isn't shown; add it. | 5 min |
| **Wd.6** | LOW | **Coral L4** — generic-bound trait sketch. Coral has been asking for this since the v5.7.1 panel; SPEC currently has trait declarations but no worked example of bounded-generics with traits. Add a 10-line example to SPEC §6.x. | 30 min |
| **Wd.7** | LOW | **Coral L5** — examples directory micro-organization. `examples/` currently has Te.5/Te.6/etc. examples flat in the directory. Coral suggested grouping by feature category (`examples/terseness/`, `examples/struct_ergo/`, `examples/agents/`, etc.). Move-only edit; update README links. | 30 min |
| **Wd.8** | LOW | **Bo.27 audit cross-reference column** convention for v5.27.0 audit. Add to `.reviews/PANEL_AUDIT_TEMPLATE.md` (or create that template if missing): a "Closes prior-panel finding" column in the H.\* findings table that binds H.\* line items to prior-panel finding IDs. Same pattern as the v5.22.0 lesson: when the audit doesn't bind to panel-finding IDs, hygiene-release closures patch what the audit cites and walk past the panel-flagged shape. | 15 min |

---

## Phase plan

### Phase 0 — pre-flight verification

```bash
# Baseline must hold from v5.24.0
bash scripts/verify_fixed_point.sh --keep
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95
cat VERSION
# expected: 5.24.0

# Verify Hy.* items in place
make ci-gates
# expected: All gates GREEN (incl. cadence WARN if applicable)
```

If any gate is RED, abort.

### Phase 1 — Wd.1 + Wd.2 (the M2 + M3 closures)

1. **Wd.1** — open `docs/manifesto.md`. Locate line 31. Apply
   Coral's two-line edit:
   ```diff
   -The syntax is clean and direct. Curly braces for blocks, strong
   -static typing with inference where it helps, no semicolons where
   -they add nothing. If you have written Rust, Go, or TypeScript,
   -you can read Mapanare immediately.
   +The syntax is clean and direct. Indented blocks (with a brace-
   +form legacy through v6.0), strong static typing with inference
   +where it helps, no semicolons where they add nothing. If you
   +have written Rust, Go, or TypeScript, you can read Mapanare
   +immediately.
   ```

2. **Wd.2** — run `mnc fmt --to-terse docs/SPEC.md`. Verify
   the rewrite preserves prose layout (only code-block
   contents are touched). For any code block that should
   intentionally remain brace-style (Chapter 27 stability
   discussion of frozen syntax — historical context), add
   `<!-- preserve-brace -->` on the line above the fence and
   teach `mnc fmt --to-terse` to skip those.

   If `mnc fmt --to-terse` doesn't have the
   `<!-- preserve-brace -->` opt-out, add it (small change in
   `mapanare/format.py`); else handle the Chapter 27 cases
   manually (revert each one back to brace after the bulk
   pass).

   Add a regression case in `tests/test_format.py`:
   ```python
   def test_preserve_brace_marker_in_markdown():
       src = '''<!-- preserve-brace -->
       ```mn
       fn foo() { return 1 }
       ```'''
       result = format_to_terse(src)
       assert "{ return 1 }" in result
   ```

3. Run `python3 scripts/check_docs_drift.py` post-edit to
   verify no new violations. (The 26 → 0 brace-block reduction
   should not introduce parse failures.)

4. Run `pytest tests/test_format.py -v` post-edit. All green.

5. Run `make ci-gates`. All green (incl. new
   `check_doc_freshness` from Hy.2).

### Phase 2 — Wd.3 / Wd.4 / Wd.5 (Coral L1–L3 — SPEC text edits)

1. **Wd.3** — `docs/SPEC.md` §27.3 (deprecation cycle policy).
   Add a worked-example paragraph after the existing policy
   text per Coral L1's suggested phrasing.

2. **Wd.4** — `docs/SPEC.md:1009` area. Tighten the rescope
   wording. Coral L2's recommendation: acknowledge the v5.14.0
   forward promise more explicitly:
   ```diff
   -Single-line `if x: y` form is deferred to v6.0 (rescoped at v5.21.1).
   +Single-line `if x: y` form: v5.14.0 documented this as deferred
   +to v5.21.0; v5.21.0 instead shipped Te.6 chained comparisons.
   +The promise is now formally rescoped to v6.0 to coincide with
   +`{}` hard removal — single-line form will be unambiguous once
   +brace-style is no longer accepted at all.
   ```

3. **Wd.5** — §4.0 Te.3 status block. Add an example
   invocation:
   ```diff
    Migration: run `mnc fmt <path>` to auto-migrate to colon-style.
   +
   +Use `mnc fmt --keep-braces` if you want canonical formatting
   +applied while keeping brace syntax — useful as a soak-window
   +concession for codebases that prefer to migrate later.
   ```

### Phase 3 — Wd.6 (Coral L4 — generic-bound trait sketch)

1. Open `docs/SPEC.md` §6.x (generics + traits chapter). Find
   the trait declaration section.

2. Add a 10-line worked example for bounded-generics with
   traits:
   ```mn
   trait Comparable {
       fn compare(self, other: Self) -> Int
   }

   fn min<T: Comparable>(a: T, b: T) -> T:
       if a.compare(b) < 0:
           return a
       return b

   impl Comparable for Int:
       fn compare(self, other: Int) -> Int = self - other
   ```

3. Add to the `examples/` directory if it's small enough; update
   `examples/` index.

### Phase 4 — Wd.7 (Coral L5 — examples directory)

1. Audit `examples/`:
   ```bash
   ls examples/ | sort
   ```

2. Group by feature category. Suggested categories (~5):
   - `examples/terseness/` — Te.\* features (chained_cmp,
     interp, lambda, etc.)
   - `examples/struct_ergo/` — Te.5 (field shorthand, struct
     update, destructuring)
   - `examples/agents/` — agent + signal + stream demos
   - `examples/tensors/` — tensor / GPU examples
   - `examples/wasm/` — WebAssembly target examples

3. Move files (`git mv`) into appropriate categories. Top-
   level `examples/hello.mn` and `examples/README.md` stay
   at the root.

4. Update README links:
   - `README.md` (English + 3 localized)
   - Any SPEC references to `examples/` paths
   - `docs/guides/getting_started.md` if present

### Phase 5 — Wd.8 (Bo.27 audit cross-reference column)

1. Check if `.reviews/PANEL_AUDIT_TEMPLATE.md` exists.

2. If exists: edit to add the cross-reference column. If
   not: create it as the canonical template for v5.27.0+
   audits.

3. Template structure:
   ```markdown
   # vX.Y.Z Pre-Panel Audit

   ...

   ## Findings cleared in vX.Y.(Z-1) hygiene release

   ### Doc surface (Boa axis)

   | # | Severity | Finding | **Closes prior-panel ID** | Closed in vX.Y.(Z-1) |
   |---|---|---|---|---|
   | H.1 | HIGH | <description> | <prior-Bo.X / V.X / etc. ID, or "(none — fresh)"> | <evidence> |
   | ... |
   ```

4. Document the convention in
   `.reviews/REVIEW_CADENCE.md` if it has a section on audit
   structure (or add one).

### Phase 6 — closeout

1. SESSION_REPORT.md.
2. CHANGELOG `## [5.24.1]` entry.
3. CLAUDE.md release note.
4. Bump VERSION 5.24.0 → 5.24.1.
5. `python3 scripts/bump_version.py 5.24.1`.
6. CRLF restoration.
7. Final `make ci-gates` — must be GREEN.
8. CARRY_FORWARD.md update — mark all v5.22.0-panel items
   CLOSED. Note: only LOW polish + v6.0 carries remain.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `mnc fmt --to-terse docs/SPEC.md` corrupts code blocks (mishandling pseudo-code, output examples, etc.) | MEDIUM | Run on a copy first; diff carefully; iterate on `<!-- preserve-brace -->` markers. The formatter is conservative by design (v5.13.0 corpus assertions). |
| Examples directory reorganization breaks links | MEDIUM | Comprehensive grep for `examples/` references in README + SPEC + tests + docs/guides; update each in lockstep. Optional: add redirect-style symlinks (or `examples/INDEX.md`) at the top level pointing to the new locations |
| Hy.2 `check_doc_freshness.py` flags drift after the manifesto edit | LOW | The manifesto edit is content-specific; freshness checks are about version/goldens/line-count drift. Run `make ci-gates` post-edit to confirm |
| Bo.27 audit-template scope-creeps to deeper review-process work | LOW | The template is a single column addition + a one-paragraph convention note. Hold scope strictly |
| Generic-bound trait sketch (Wd.6) reveals SPEC inconsistency in trait/generic interaction | MEDIUM | If the example doesn't compile or contradicts §6.x prose, file as a separate v5.27.0 docket item; ship Wd.6 with a working example or skip if blocking |

---

## Success criteria

- [ ] Manifesto rewrite shipped (Wd.1)
- [ ] SPEC corpus migrated to colon-style with `<!-- preserve-brace -->` opt-outs for historical examples (Wd.2)
- [ ] Coral L1–L5 closures shipped (Wd.3–Wd.7)
- [ ] Bo.27 audit cross-reference column convention codified (Wd.8)
- [ ] Goldens 95/95 preserved
- [ ] Strict 3-stage fixed point preserved at v5.23.2's line count
- [ ] `make lint` clean
- [ ] `make ci-gates` GREEN at HEAD
- [ ] CARRY_FORWARD.md — all v5.22.0 panel items CLOSED
- [ ] SESSION_REPORT.md
- [ ] CHANGELOG `## [5.24.1]` entry
- [ ] CLAUDE.md release note
- [ ] VERSION bumped 5.24.0 → 5.24.1

---

## Out of scope (explicitly held)

- **Compiler / runtime / `mapanare/self/*.mn` edits.** None.
- **v5.27.0 panel.** Routine cadence; runs separately.
- **v6.0 carries** (Rt.04, Te.3 hard removal, etc.).

---

## What this release CANNOT do

- Re-grade the v5.22.0 panel.
- Touch v6.0 carry items.
- Ship anything beyond docs / examples / templates.

---

## Arc closure verification

After v5.24.1 ships, run `make ci-gates` + verify
CARRY_FORWARD.md state:

| Class | Count at v5.22.0 panel | Target at v5.24.1 closeout |
|---|---:|---:|
| HIGH | 4 | **0** |
| MEDIUM | 8 | **0** |
| LOW | ~12 | ~5 (only polish; LOW carries closed via Hy.\* / Mb.\* / Wd.\*) |
| v6.0 carry | 1 (Rt.04) | 1 (Rt.04) — unchanged |

If counts don't match, identify the missed item; close at
v5.24.x or document as deferred to v5.25.0+ (don't carry
silently — that's the failure mode this whole arc was
designed to prevent).

---

## v5.27.0 panel preview

Per the v5.22.0 V5_DECISION.md, the next routine cadence
panel runs at v5.27.0. By that release:

- v5.23.0 / v5.23.1 / v5.23.2 / v5.24.0 / v5.24.1 = 5
  recovery releases shipped.
- 4 HIGH closed, 8 MEDIUM closed, ~12 LOW closed.
- Strict 3-stage fixed point preserved (or new fixed-point
  documented post-Te.3.B).
- `make ci-gates` GREEN; `check_doc_freshness.py` GREEN;
  cadence enforcement WARN-only.

The panel target is **9.5+** (back above the 9.41 floor v5.22.0
hit). v5.7.1's 9.66 ceiling is reachable IF every HIGH closes
structurally and the prevention infrastructure is in place.
This arc is sized for that target.
