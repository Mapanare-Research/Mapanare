# v5.53.0 — Sf.\* + Te.3.F — Windows struct-update overflow + nested stmt-block recursive migration

**Status:** PLANNING
**Type:** Patch release. Drains two carries from the v5.50.x docket:
(1) **Sf.\*** — the `82_struct_update` / `83_struct_update_partial`
integer-overflow surfaced during the Windows local-goldens sweep at
the v5.48.1 baseline. Pre-existing; unrelated to Wn.\*; filed as a
v5.49.x patch candidate in v5.49.0 SESSION_REPORT §Wn.2. (2) **Te.3.F**
— ~11 first-party nested-stmt-block predicates of shape
`if X { if Y { ... } }` (10 in `lexer.mn`, 1 in `lower.mn`) that
v5.50.0 Te.3.E's flat `_migrate_one_line_stmt_block` cannot reach
because of the line-363 nested-brace rejection. Both items are local
on Windows; STRICT preservation is the safety net.
**Breaking:** No. Bug fixes only; the formatter extension is
additive (more shapes migrate; existing migrations unchanged).
**Prerequisite:** v5.52.0 (Wn.8 — runtime archive locator) shipped.
Te.3.E grammar at v5.50.0 baseline. STRICT 3-stage fixed point at
246,347 lines / 0 diff (55-release streak from v5.7.1).
**Estimated effort:** 1 session. Both items are well-localized
single-class bugs; Phase 0 audit confirms sizing or splits per
the v5.46.0 sizing lesson.

---

## Why this exists

Two unrelated bugs, both surfaced during the v5.48.1 → v5.50.0
Windows-platform work, both filed as v5.50.x patch candidates,
both small enough to bundle into one release without the
v5.46.0-style sizing risk.

**Sf.\*** — v5.49.0 SESSION_REPORT.md:159 captured the symptom:

> Goldens (Windows local): 100/103. Pre-existing failures:
> `82_struct_update` and `83_struct_update_partial` fail with
> `integer overflow in 11 + 9223372036854775802` (a different
> codegen bug class — uninitialized memory read in struct update
> emission, surfaced on the Windows local build only; visible in
> the v5.48.1 baseline too — file as v5.49.x patch candidate
> unrelated to Wn.\*).

`9223372036854775802 == INT64_MAX - 5` — the high-bit pattern is
characteristic of an uninitialized stack-memory read. The Linux/macOS
goldens pass because their stack layouts coincidentally zero-init
the relevant slot; the Win64 layout exposes the latent bug. The
v5.20.0 Te.5.C struct-update lowerer at `mapanare/lower.py:5095`
(`_lower_struct_update`) synthesizes a base-temp via a recursive
`_lower_let` and emits per-field GEPs — the bug is likely in either
the synthesized-temp's element-type inference (the spread base's
fields may be read at a wrong-width offset) or in the
`__mn_dst_<idx>` tmp's allocation shape.

**Te.3.F** — v5.50.0 Te.3.E's `_migrate_one_line_stmt_block`
formatter rejects any single-line stmt-block whose body contains
nested braces:

```python
# mapanare/format.py:362-364
body_shadow = shadow[open_idx + 1 : close_idx]
if "{" in body_shadow or "}" in body_shadow:
    return None
```

This is correct for cases like `match x { ... }` where the inner
braces are comma-body openers with no colon form — but it also
rejects nested stmt-blocks like `if ch >= "a" { if ch <= "z" {
return true } }`, which v5.48.0 colon-form CAN represent as
`if ch >= "a": if ch <= "z": return true` (the body of the outer
`:` is a single statement which is itself a colon-form stmt-block,
and the grammar accepts this by composition).

Empirical residual count (`grep -c "if .* { if .* {" mapanare/self/*.mn`):

| File | Sites |
|---|---:|
| `lexer.mn` | 10 |
| `lower.mn` | 1 |
| **Total first-party** | **11** |

(`mnc_all.mn` registers 11 cascade matches from the same sources.)

CLAUDE.md's v5.50.0 note mentioned "17 lexer.mn predicates" — the
audit at Te.3.F.0 reconciles the count; the 17 likely included
multi-line stmt-block shapes that aren't `if X { if Y { ... } }`
single-line shape. Phase 0 enumerates by exact shape.

---

## Items in scope

### Sf.\* — struct-update integer-overflow (Windows)

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Sf.0** | HIGH (gate) | Phase 0 audit. Reproduce on Windows; capture the exact LLVM IR diff between `mapanare/lower.py` output and a known-good manual long-form lowering of the same struct-update source. Localize to either the base-temp synthesis (lines 1427-1497) or the per-field GEP emit in `_lower_struct_update` (lines 5095+). Decide whether the fix is Python-bootstrap-only (likely — self-host `lower.mn` may not have the bug if it already does the equivalent of v5.26.1 Eu.2's `current_fn.return_type` consultation) or needs a self-host mirror. Output: `PRE_PHASE_AUDIT.md`. | 1h |
| **Sf.1** | HIGH | Root-cause fix at the localized site. Likely shape — either initialize the synthesized base-temp's spread-source fields with the correct element width (avoiding the uninitialized read), or fix the GEP/load width on the spread base. ≤ 30 LOC predicted; if > 50 LOC, split to v5.53.x. | 1-2h |
| **Sf.2** | HIGH | Falsifiability test. New `tests/llvm/test_struct_update_init.py` with the exact 82/83 shape encoded as a Python-bootstrap IR-emission test that runs cross-platform (no Windows binary needed). Revert the Sf.1 fix → test fails with the recorded signature. Per the v5.46.0 Lf.\* pattern. | 0.5h |
| **Sf.3** | MEDIUM | Self-host mirror (conditional on Sf.0 finding). If self-host `lower.mn` has the same bug, port the fix. If self-host already handles correctly (matching v5.46.0 Lf.\* precedent where self-host had the v5.26.1 Eu.2 fix and Python didn't), no-op gate — STRICT preserved by construction. | 0-1h |

### Te.3.F — nested stmt-block recursive migration

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.F.0** | HIGH (gate) | Phase 0 audit. Re-enumerate `if X { if Y { ... } }` residuals per file by exact shape. Verify Te.3.E's `_indent_to_braces` already accepts the migrated output as input (the colon-form `if X: if Y: stmt` must round-trip to the brace form). If it doesn't, Te.3.F.1's recursion needs to migrate inside-out; if it does (likely — Te.3.E already accepts single-line continuations), top-down recursion suffices. Output: `PRE_PHASE_AUDIT.md`. | 1h |
| **Te.3.F.1** | HIGH | Formatter recursive migration. `mapanare/format.py::_migrate_one_line_stmt_block` extension: when `body_shadow` contains `{`/`}`, recursively try to migrate each nested brace block; re-check after recursion. The recursion bottoms out at the existing flat-body acceptance path. ~30 LOC + ~80 LOC tests. Idempotence locked. | 1-2h |
| **Te.3.F.2** | HIGH (gate) | Self-host source migration. Run `mnc fmt --to-terse` over `mapanare/self/{lexer,lower}.mn`. Regenerate `mnc_all.mn` via `scripts/concat_self.sh`. Stage1 rebuild + goldens 103/103 + STRICT 3-stage fixed point at the new baseline. ~11 sites migrate; brace surface drops from 25 → ~14. | 0.5h |
| **Te.3.F.3** | MEDIUM | Falsifiability test in `tests/test_single_line_colon_blocks.py` covering 3 nested shapes (depth 2, depth 3, mixed continuation). Revert the Te.3.F.1 recursion → tests fail with the recorded signature. | 0.5h |

**No C runtime mirror needed for Te.3.F.** The native `mnc fmt`
command shells out to Python `mapanare fmt` (`mapanare/self/main.mn:1186`,
`fmt_cmd = "mapanare fmt"`). The `__mn_indent_to_braces` C export
is parser-side (reads colon form, produces brace form for the LALR
parser); the formatter is `to_terse` direction, Python-only. v5.48.1
Te.3.D.4's C runtime mirror was for `__mn_indent_to_braces`, not
`_migrate_one_line_stmt_block`.

---

## Phase plan

- **Phase 0** — Sf.0 + Te.3.F.0 in parallel. Two `PRE_PHASE_AUDIT.md`
  outputs (one per docket) or combined in a single audit. Sizing
  decision: ≤ 50 LOC per fix = bundle into v5.53.0; > 50 LOC =
  split to v5.53.1 / v5.54.0.
- **Phase 1** — Sf.1 + Sf.2 (Python lowerer fix + falsifiability).
- **Phase 2** — Sf.3 (self-host mirror, conditional).
- **Phase 3** — Te.3.F.1 (formatter recursion).
- **Phase 4** — Te.3.F.2 (self-host migration + STRICT gate).
- **Phase 5** — Te.3.F.3 (falsifiability).
- **Phase 6** — Closeout: VERSION 5.52.0 → 5.53.0; CHANGELOG `### Fixed`
  for Sf.\* (with potentially-behavior-changing annotation per v5.46.0
  precedent — the Windows-only goldens go from FAIL → PASS); `### Added`
  for Te.3.F (formatter accepts more shapes); CLAUDE.md release-notes
  entry; SPEC.md header re-sync; SESSION_REPORT.md.

Each phase has a STRICT preservation gate. Goldens 103/103 at every
checkpoint per the v5.48.1 / v5.50.0 discipline. The v5.52.0 baseline
of **246,347 lines / 0 diff** is the floor; v5.53.0 preserves at the
new value after the self-host migration delta lands.

---

## Out of scope

- **Multi-line nested stmt-block migration.** Te.3.F is limited to
  single-line `if X { if Y { stmt } }` shape. Multi-line nested
  shapes (`if X { \n if Y { \n stmt \n } \n }`) already migrate via
  v5.50.0 Te.3.E.2 multi-line `:` form. Phase 0 audit confirms no
  multi-line residuals in the 17 originally tallied.
- **`mapanare/self/{ast,mir,parser,semantic,lower_state,mir_opt,emit_llvm,main}.mn`
  brace surface.** v5.50.0 closed the bulk; the v5.53.0 scope is
  the nested-shape residual only.
- **Stdlib / examples brace migration.** v5.50.0 scope was
  `mapanare/self/*.mn`; the v6.0 hard-removal cut handles the
  broader sweep.
- **Struct-update lowering refactor.** Sf.\* fixes the specific
  uninitialized-read bug, not the broader question of whether
  `_lower_struct_update`'s synthesized-base-temp approach should be
  replaced with destination-passing per v5.6.12 Lk.1 precedent.
  Refactor is v6.0 PLAN input.
- **Borrow checker.** v6.0 thesis.
- **macOS notarization (Nu.2).** v5.55.0 docket per the v5.x drain
  plan (needs Mac access + Apple Developer cert).
- **Cl.2 + Cl.3 (agent stdlib refactor + walk_dir).** v5.54.0 docket.

---

## Risk

1. **Sf.\* fix is wider than predicted.** If Phase 0 audit finds
   the uninitialized-read is in MIR-builder territory (not lowerer-
   only), the fix could touch `mir_builder.py` + the self-host mirror
   + multiple emit sites. Mitigation: Phase 0 sizing gate; if > 50
   LOC, split Sf.\* to v5.53.1 and ship Te.3.F alone in v5.53.0.
2. **Te.3.F recursion produces invalid output.** Recursive migration
   could collapse semantics — e.g., migrating
   `if X { if Y { stmt } else { stmt2 } }` to
   `if X: if Y: stmt else: stmt2` may bind the `else` to the wrong
   `if`. Mitigation: idempotence + AST-equivalence tests per v5.48.0
   precedent; Phase 0 audit prototypes the recursion and verifies
   parse equivalence on every residual shape before Te.3.F.1 lands.
3. **Self-host migration breaks STRICT.** v5.50.0's Phase 4
   rebuild-after-each-cluster surfaced two formatter bugs mid-
   implementation. Te.3.F.2 migrates 2 files (lexer.mn, lower.mn),
   so the discipline is light — but a per-file checkpoint rebuild
   is mandatory. If STRICT breaks, revert the migration and ship
   Te.3.F formatter alone (the formatter extension is value-add
   independent of the self-host source migration; migration can
   defer to v5.53.1).

---

## Success criteria

1. **Sf.\* — Windows goldens.** `82_struct_update` and
   `83_struct_update_partial` PASS on the Windows local build at
   `dist/mapanare/mnc.exe` (or the equivalent locally-built path).
   Cross-platform IR-emission test in `tests/llvm/test_struct_update_init.py`
   passes on Linux/macOS/Windows.
2. **Sf.\* — Linux/macOS preserved.** All 103 goldens preserve;
   no behavior change observable on platforms where the bug was
   masked.
3. **Te.3.F — formatter.** `mnc fmt --to-terse mapanare/self/lexer.mn`
   migrates all 10 nested-shape sites; output round-trips through
   `to_braces` to AST-equivalent MIR; idempotence on second run.
4. **Te.3.F — self-host migration.** `mapanare/self/lexer.mn` +
   `mapanare/self/lower.mn` migrated; `mnc_all.mn` regenerated;
   stage1 rebuilds; goldens 103/103; STRICT 3-stage fixed point
   preserved at the new line count.
5. **Brace surface.** First-party brace counter (v5.50.0 Te.3.E.X
   refinement) drops from the v5.50.0 baseline of 25 to ~14 (or
   the empirical Phase 0 count).
6. **No new MEDIUM / HIGH carries.** Sf.3 and Te.3.F's risk
   mitigations (the conditional self-host mirror and the formatter-
   only fallback) ensure the release ships clean or splits cleanly.

---

## Falsifiability lock

Per the v5.46.0 Lf.\* / v5.50.0 Te.3.E pattern, each fix gets a
falsifiability anchor in a test module docstring:

- **Sf.\*** — `tests/llvm/test_struct_update_init.py` module
  docstring: revert Sf.1 → IR-emission test asserts
  `i64 9223372036854775802` (or the exact uninitialized pattern
  Phase 0 captures) appears in the spread-source field read.
- **Te.3.F** — `tests/test_single_line_colon_blocks.py::TestNestedStmtBlock`
  module docstring: revert Te.3.F.1 → `to_terse` on
  `if X { if Y { stmt } }` returns the brace form unchanged.

---

## Carry-forward to v5.54.0

After v5.53.0:

- **Cl.2** (LOW) — agent stdlib ergonomic refactor (~400 LOC).
- **Cl.3** (LOW) — fs.mn `walk_dir` IR codegen.
- **websocket.mn `str(byte)`** (LOW) — decimal-stringification
  cleanup if not fully closed in v5.47.0 Cl.4.
- **Ai.1 `_specialize_fn`** (MEDIUM) — body-walk fix, carries to
  v5.55.0 by current drain plan but movable to v5.54.0 if Mac
  access is delayed.
- **Nu.2 macOS notarization** (MEDIUM) — v5.55.0 docket; needs
  Mac + Apple Developer cert.

Aggregate state entering v5.54.0: **0 HIGH** / **2 MEDIUM** (Ai.1,
Nu.2) / **~4 LOW** (Cl.2, Cl.3, websocket str(byte), Lf.4 variant-
name collision). v5.x drain on track for clean v6.0 entry.
