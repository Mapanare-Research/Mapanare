# Mapanare v4.52.0 — Self-Hosted Semantic Wiring (A7)

> **Arc 5 release 1.** Closes `CARRY_FORWARD.md` A7. The self-hosted
> `semantic.mn` exists (1,729 lines at last count) but is not called
> from `self/main.mn:compile()`. The v4.5.0 CHANGELOG claimed it was
> wired; the v4.26.0 panel flagged the claim as false; the Python side
> was closed in v4.27.0; A7 is the self-hosted side. v4.52.0 finally
> closes it.

**Status:** DONE (2026-04-12)
**Session log:** Single session. Audit found 24 divergent items; 3 fixed (D1-D3), 21 deferred.
**Decisions taken:** Audit-first (default). Wiring already done (main.mn:297). Ported D1 (`?` operator), D2 (match guard Bool), D3 (while Bool). Deferred match exhaustiveness (needs Maranget port). No diagnostics.mn needed — format_error in main.mn adequate.
**Breaking:** No (the self-hosted compiler gains errors it used to silently accept, but existing correct programs are unaffected)
**Prerequisite:** v4.51.0 (arc 4 panel PASS)
**Delta review:** No (no new syntax — internal compiler wiring)
**Full panel:** No (v4.56.0)
**Estimated work:** 2 sprints (audit + wiring + the surprise-bug-fixup work the wiring surfaces)
**Theme:** The self-hosted compiler gains the semantic pass it always claimed to have.

---

## Why now

The v4.18.0–v4.26.0 regression taught the project that unfalsifiable CI is worse than no CI. A7 is the same lesson at the pipeline level: the self-hosted compiler has had a semantic pass sitting on disk for ~20 releases that the pipeline never actually runs. Compiling a broken `.mn` file through `mnc-stage1` produces whatever the lowerer emits — which may be garbage IR, may be an LLVM verification failure, may be a runtime crash. The semantic error messages the user should see never fire because the semantic pass is not on the code path.

**The cost of fixing this now vs in v5.0.0:** fixing in v4.52.0 means the v4.52.0-v4.55.0 work (self-hosted semantic, UNRESOLVED/ERROR split, emit_c.mn, const Path A) all gets validation from the v4.56.0 panel. Deferring to v5.0.0 bundles everything into one mega-release, which is the exact anti-pattern the recovery arc was built to prevent.

---

## Phase 0 — Audit

### Phase 0.1: Read the self-hosted semantic source

- [ ] `mapanare/self/semantic.mn` — read end-to-end. ~1,729 lines. Note:
  - What's the entry point? Probably `fn semantic_check(prog: Program) -> List<SemanticError>` or similar.
  - What's missing vs the Python `mapanare/semantic.py`?
  - What functions does it call that may themselves be stubs?
  - Does it reference any types / constants that don't exist yet?

### Phase 0.2: Side-by-side comparison

- [ ] For every public entry in `mapanare/semantic.py`, check the self-hosted equivalent:

  | Python `semantic.py` | Self-hosted `semantic.mn` | Status |
  |---|---|---|
  | `check_program(prog)` | `semantic_check(prog)` | ? |
  | `check_fn_def` | | ? |
  | `check_let_def` | | ? |
  | `check_struct_def` | | ? |
  | `check_enum_def` | | ? |
  | `check_trait_def` | | ? |
  | `check_impl_def` | | ? |
  | `check_expr` | | ? |
  | `check_stmt` | | ? |
  | `check_match_expr` | | ? |
  | `check_match_exhaustive` | | ? (v4.34.0 added this in self-hosted too; should be wired) |
  | `check_try_expr` | | ? (v4.33.0 added this) |
  | ... | ... | ... |

- [ ] Classify each row as:
  - **Parity**: Python and self-hosted behave equivalently
  - **Divergent-benign**: differ but not user-visible (different error messages, same error count)
  - **Divergent-breaking**: self-hosted misses a check the Python side catches — must be fixed in v4.52.0
  - **Missing**: self-hosted has no equivalent at all

- [ ] `docs/roadmap/v4/v4.52.0/AUDIT.md` — the audit table written out.

### Phase 0.3: Scope decision

- [ ] Reviewing the audit, decide which divergences are in scope for v4.52.0:
  - **In scope:** wire `semantic_check` into `compile()`. Fix any Divergent-breaking rows that would make the self-hosted compiler reject programs the Python compiler accepts, or accept programs the Python compiler rejects.
  - **Out of scope:** Divergent-benign rows. Missing rows that don't affect correctness. Those get tracked as v4.53.0+ follow-ups.

---

## Phase 1 — Diagnostic renderer (if missing)

The self-hosted side needs a rustc-quality diagnostic renderer. Check first:

- [ ] Does `mapanare/self/diagnostics.mn` exist? If yes, verify it matches `mapanare/diagnostics.py` in output shape.
- [ ] If no, create it. Port the rendering logic from Python:
  - `Span` → `(line, column, end_line, end_column)`
  - Colored output via ANSI codes (no-color fallback via env var)
  - `format_diagnostic(err: SemanticError) -> String` — builds the rendered message with file:line, caret underline, suggestion block
- [ ] Tests: take a fixture `SemanticError` and verify the rendered output byte-matches the Python side.

---

## Phase 2 — Wire `semantic_check` into `compile()`

- [ ] `mapanare/self/main.mn` — find the `compile()` function.
- [ ] After parse, before lower, insert:
  ```mapanare
  let errors: List<SemanticError> = semantic_check(prog)
  if errors.len() > 0 {
      for err in errors {
          mn_str_eprint(format_diagnostic(err))
      }
      mn_exit(1)
  }
  ```
- [ ] `mn_str_eprint` and `mn_exit` must exist as runtime externs. Check and add if missing.

---

## Phase 3 — Fix divergent-breaking rows

For each row classified as divergent-breaking in Phase 0.3:

- [ ] Port the Python-side check to the self-hosted side.
- [ ] This may require:
  - Extending `SemanticError` with new fields if the self-hosted version is sparser
  - Adding helper functions the self-hosted semantic doesn't have yet
  - Reconciling minor data-model differences (e.g., how scopes are represented)
- [ ] For each port, add a test: a `.mn` file that's rejected by Python and was previously accepted by self-hosted; verify v4.52.0 rejects it in both.

Expected divergent-breaking rows (preliminary guess — validated in Phase 0):
- `?` operator semantic check (v4.33.0 added it Python-side; self-hosted may still stub)
- Match exhaustiveness (v4.34.0 added error-level; self-hosted may still be warning-only or missing)
- Match guards type check (v4.35.0)
- Tensor shape compatibility (v4.42.0-v4.44.0)
- `__struct_meta<T>()` support (v4.48.0)

All of these were added in both pipelines during v4.33.0+, but were the self-hosted versions actually *invoked* if the semantic pass was never called? **Phase 0 audits this.**

---

## Phase 4 — Rebuild + validate

- [ ] `python scripts/build_stage1.py` — rebuild mnc-stage1 with the wired semantic pass
- [ ] Run all existing golden tests. Expect all 50+ to still pass — they're correct programs.
- [ ] Run the pytest test corpus through `mnc-stage1` via a test-runner shim. Any test fixtures that were deliberately broken ("file with type error") should now produce an error when compiled through `mnc-stage1`, not a crash or silent miscompile.
- [ ] **If any existing golden fails after wiring:** that's a case where the self-hosted compiler was silently accepting broken code. Fix the test (add the missing semantic check to catch it upstream) — this is the test honesty dividend.

---

## Phase 5 — Regression test

- [ ] `tests/self_hosted/test_semantic_wiring.py` — new test:
  ```python
  def test_compile_rejects_broken_file():
      # A file with a deliberate type error
      source = "fn main() { let x: Int = 'hello' }"
      result = subprocess.run(
          ["./mapanare/self/mnc-stage1", "-"],
          input=source,
          capture_output=True,
          text=True,
      )
      assert result.returncode == 1
      assert "type mismatch" in result.stderr
      assert "Int" in result.stderr
      assert "String" in result.stderr

  def test_compile_accepts_correct_file():
      source = "fn main() { let x: Int = 42 }"
      result = subprocess.run(
          ["./mapanare/self/mnc-stage1", "-"],
          input=source,
          capture_output=True,
          text=True,
      )
      assert result.returncode == 0
  ```

- [ ] Additional cases: undefined symbol, wrong arg count, non-exhaustive match, `?` in non-Result fn.

---

## Phase 6 — Fixed-point

- [ ] Run `bash scripts/verify_fixed_point.sh`. The semantic pass runs before lowering, so the lowered IR should be unchanged for correct programs. Fixed-point diff should remain 0.
- [ ] If it's not 0, something about the semantic check is mutating the AST in a way that affects lowering — investigate and fix.

---

## Phase 7 — LOW sweep

2 items.

---

## Phase 8 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.52.0
- [ ] `CHANGELOG.md [4.52.0]` — lists A7 closure and the semantic checks now wired
- [ ] `.reviews/CARRY_FORWARD.md` — A7 CLOSED with evidence (file:line of the `semantic_check` call site in `self/main.mn`)
- [ ] `AUDIT.md` committed alongside
- [ ] SESSION_REPORT written

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `AUDIT.md` written with side-by-side classification | file exists |
| 2 | `mapanare/self/diagnostics.mn` exists or is confirmed adequate | file check |
| 3 | `semantic_check` wired into `self/main.mn:compile()` | grep + line number in ledger |
| 4 | Broken `.mn` file compiled through mnc-stage1 produces exit code 1 + error | `test_compile_rejects_broken_file` |
| 5 | Correct `.mn` file compiles cleanly | `test_compile_accepts_correct_file` |
| 6 | All 50+ existing golden tests still pass | `test_native.py` |
| 7 | Any previously-passing golden that fails is because it had a real semantic error | audit log |
| 8 | Divergent-breaking rows ported from Phase 3 | AUDIT.md delta |
| 9 | Type mismatch example produces rustc-quality error | manual inspection |
| 10 | Undefined symbol example produces rustc-quality error | same |
| 11 | Non-exhaustive match produces error | same |
| 12 | `?` on non-Result fn produces error | same |
| 13 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 14 | A7 marked CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 15 | Standard closeout clean | CI |

---

## What v4.52.0 does NOT do

- **A8 UNRESOLVED/ERROR split** — v4.53.0
- **Full parity between Python and self-hosted** — only divergent-breaking rows are fixed. Benign divergences stay open.
- **Performance optimization** of the self-hosted semantic pass — it's now on the compile path; if it's slow, that's a v5.x investigation

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Wiring semantic_check breaks a bunch of "working" goldens because they had silent errors | **medium** | medium | Expected. Test honesty dividend — fix the tests (which is a win), not the semantic pass |
| Divergent-breaking rows are bigger than expected | medium | high | Phase 0 scopes it; if cascades, slip v4.52.0 and do a point release |
| The semantic pass is slow on `mnc_all.mn` (15k lines) | medium | medium | Profile; add caching if needed; worst case, the semantic pass takes an extra second on compile |
| Fixed-point diff moves because semantic check mutates the AST | low | medium | Shouldn't happen — semantic check is read-only — but verify explicitly |

---

## Reference

- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A7 — the carry-forward
- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 5

---

## After v4.52.0

v4.53.0 adds the UNRESOLVED/ERROR split (A8) on top of the now-wired self-hosted semantic pass.
