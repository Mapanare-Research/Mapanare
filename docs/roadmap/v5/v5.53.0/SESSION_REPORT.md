# v5.53.0 Session Report — Te.3.F (Sf.\* split to v5.53.1)

**Status:** SHIPPED (not yet tagged).
**Date:** 2026-05-15.
**Theme:** nested single-line stmt-block recursive migration.
**Effort:** 1 session (compressed; PLAN budget was 1 session).

---

## What shipped

| Phase | What | LOC | Result |
|---|---|---:|---|
| **Phase 0** | PRE_PHASE_AUDIT.md (mandatory, gating) | this doc + audit | **2 load-bearing reversals;** Sf.\* split, Te.3.F scope reduced 11→7 |
| **Phase 1+2 (Sf.\*)** | — | — | **SPLIT to v5.53.1** (PLAN.md Risk #1 mitigation fired) |
| Te.3.F.1 | formatter recursion at `_migrate_one_line_stmt_block` | ~14 P | inside-out recursion clears the line-363 nested-brace reject |
| Te.3.F.2 | self-host source migration in `lexer.mn` (+ `mnc_all.mn` cascade) | mechanical | 7 sites migrated; Python-bootstrap parse verified |
| Te.3.F.3 | falsifiability anchor (`TestNestedStmtBlock`) | ~95 LOC test | 7 cases — 5 positive, 2 deferred-shape negative; reverting recursion → 3 of 5 positive FAIL with recorded signature |
| **Closeout** | VERSION bump, CHANGELOG, CLAUDE.md, this report | mechanical | this doc |

---

## Phase 0 findings (load-bearing)

### Reversal 1 — Sf.\* PLAN hypothesis was wrong

PLAN.md hypothesized the Win64 `integer overflow in 11 +
9223372036854775802` symptom from `82_struct_update` /
`83_struct_update_partial` lived in `mapanare/lower.py`'s
`_lower_struct_update` base-temp synthesis (lines 1427-1497 or
5095+). Phase 0 IR inspection of the Python-bootstrap output under
the actual failing target triple (`x86_64-w64-windows-gnu`) showed
**structurally correct IR**:

```llvm
%t7.a.23 = alloca {i64, i64, i64}, align 8
store {i64, i64, i64} zeroinitializer, ptr %t7.a.23   ; zero-init OK
; ... 99/2/3 stores via synthesized ConstructExpr
%si.22 = insertvalue {i64, i64, i64} %si.20, i64 %l.21, 2
store {i64, i64, i64} %si.22, ptr %t7.a.23            ; full 24-byte write
```

No uninitialized read on the lowerer side. The actual root cause
is at the **emitter ABI lowering** layer, traced via:

1. `9223372036854775802 == INT64_MAX - 5` is `mn_checked_add`'s
   stderr signature (`runtime/native/mapanare_core.c:174-186`).
   The test source has zero `+` ops → must fire in a runtime path.
2. The C runtime declares (v5.8.3 Wb.1):
   `void __mn_str_free(const char *data, int64_t len_with_heap_bit)`
   — two decomposed scalars.
3. The Python emitter declares `_ensure("__mn_str_free", VOID, [STR])`
   (one aggregate `{ptr, i64}` arg) and **call sites at lines 1794
   + 2015** emit `call void @__mn_str_free({ptr, i64} %v)` directly,
   **bypassing `_rt`'s Win64 sarg lowering** (lines 1695-1722).
4. On SysV: aggregate decomposes to rdi+rsi by coincidence matching
   the C signature.
5. On Win64: aggregate becomes sarg (hidden ptr in rcx) → C reads
   garbage from rdx for `len_with_heap_bit`. Garbage leaks through
   later allocation arithmetic, lands in `mn_checked_add` as
   `INT64_MAX - 5 + 11` overflow.
6. **Self-host emitter has the same bypass:** 4 sites in
   `mapanare/self/emit_llvm.mn` (4660, 4840, 4844, 4990) + decl at
   1101. Sf.3 (mirror) IS required when Sf.\* lands.

Sizing estimate ~100 LOC across Python + self-host + tests. Above
PLAN.md's 50-LOC bundle threshold. More critically, **no Windows
clang locally** to verify a Win64-only fix — speculative changes
violate the v5.46.0 / v5.49.0 falsifiability discipline (revert →
recorded crash signature). PLAN.md Risk #1 explicitly authorized
the split.

**Decision: split Sf.\* to v5.53.1.** Fix recipe in
`docs/roadmap/v5/v5.53.0/PRE_PHASE_AUDIT.md`:

- Sf.1: change `_RUNTIME_FN_SIGS["__mn_str_free"]` to
  `(VOID, [PTR, I64])`; emit `extractvalue` + decomposed pass at
  call sites; route through `_rt`. Removes the bypass.
- Sf.3: mirror across `mapanare/self/emit_llvm.mn` 4 sites + decl.
- Sf.4 (companion): `__mn_str_concat` aggregate-by-value call at
  `emit_llvm_text.py:5583` has the same bypass shape — bundle if
  ≤ 30 additional LOC.
- Sf.2: cross-platform IR-shape gate (assert no
  `{ptr, i64} @__mn_str_free` under `x86_64-w64-windows-gnu`
  triple) + Win64-only runtime smoke marked
  `pytest.mark.windows` for CI.

### Reversal 2 — Te.3.F scope reduced 11 → 7

PLAN.md and an empirical grep confirm 11 first-party residuals
(10 lexer.mn + 1 lower.mn). But three parser probes proved only 7
are migrate-able under v5.48.0 grammar:

| Probe | Form | Result |
|---|---|---|
| 1 | `if A: if B: stmt` (pure-nested-2) | PARSES OK, AST-equal to brace form |
| 2 | `if X: a else: b` (chained-if-else single-line) | **ParseError** at `else` |
| 3 | `if Y: stmt` then next line `else if X: stmt` | **ParseError** at `if` after else (confirmed by `test_else_if_single_line_terminating` prose comment — colon-form-closed if cannot extend with chained `else`) |

The 4 chained-cases (lexer 267/276/285 + lower 4843) need a
single-line `else:` continuation grammar rule absent from v5.48.0.
**Defer to v6.0 PLAN** where the rule lands alongside hard `{}`
removal.

---

## Te.3.F implementation

### Te.3.F.1 — formatter recursion

`mapanare/format.py::_migrate_one_line_stmt_block`:

```python
body_shadow = shadow[open_idx + 1 : close_idx]
if "{" in body_shadow or "}" in body_shadow:
    # v5.53.0 Te.3.F.1: nested single-line stmt-blocks. Recursively
    # migrate the body — `if A { if B { stmt } }` reduces to
    # `if A { if B: stmt }` then again to `if A: if B: stmt`.
    # ...
    migrated_body = _migrate_one_line_stmt_block("", body)
    if migrated_body is None:
        return None
    migrated_shadow = _mask_strings(migrated_body)
    if "{" in migrated_shadow or "}" in migrated_shadow:
        return None
    body = migrated_body
```

Inside-out recursion: the inner brace-block migrates first, the
outer's reject clears, the outer migrates. If the recursive call
returns `None` (chained-if-else inner) or the migrated body still
has braces, the outer aborts — **no half-migration** that would
produce invalid colon-form output.

### Te.3.F.2 — self-host migration

Single cluster (one file). 7 sites in `mapanare/self/lexer.mn`:

| Line | Function | Migration |
|---:|---|---|
| 191 | `is_alpha` | `if ch >= "a": if ch <= "z": return true` |
| 192 | `is_alpha` | `if ch >= "A": if ch <= "Z": return true` |
| 196 | `is_digit` | `if ch >= "0": if ch <= "9": return true` |
| 212 | `is_hex_digit` | `if ch >= "a": if ch <= "f": return true` |
| 213 | `is_hex_digit` | `if ch >= "A": if ch <= "F": return true` |
| 371 | `scan_char` | `if p < len(source): if source.char_at(p) == "'": p = p + 1` |
| 386 | `scan_op` | `if ch == "&": if ch1 == "&": return new_token(...)` |

Applied via `python -m mapanare fmt --to-terse mapanare/self/lexer.mn`.
`mnc_all.mn` regenerated via `bash scripts/concat_self.sh`
(21,678 lines after regen). Python-bootstrap parse of both files
verified OK post-migration.

### Te.3.F.3 — falsifiability anchor

`tests/test_single_line_colon_blocks.py::TestNestedStmtBlock`,
7 cases:

| Test | Shape | Asserts |
|---|---|---|
| `test_pure_nested_2_lexer_191` | `if A { if B { return X } }` | migrated colon form present in `to_terse` output |
| `test_pure_nested_2_round_trips_to_same_ast` | same | brace-form AST == colon-form AST (after `to_terse`) |
| `test_pure_nested_2_idempotent` | same | `to_terse(to_terse(src)) == to_terse(src)` |
| `test_pure_nested_2_complex_body` | inner has multi-arg fn call | migration preserves args |
| `test_pure_nested_2_with_assignment_inner` | inner is `p = p + 1` | migration; no braces on migrated line |
| `test_chained_if_else_deferred_left_alone` | outer single-arm + inner if-else (lower.mn:4843 shape) | unchanged (no half-migration) |
| `test_chained_in_else_branch_deferred` | outer if-else with nested-in-else (lexer.mn:267 shape) | unchanged (no half-migration to invalid `else:`) |

**Falsifiability verified empirically:** `git stash push
mapanare/format.py` + re-run → 3 of 5 positive tests FAIL with the
recorded `assert 'if X: if Y: ...' in <unchanged brace string>`
AssertionError. `git stash pop` → 7/7 GREEN. The recursion is
load-bearing for the migrations.

---

## STRICT 3-stage fixed point

**v5.52.0 baseline:** 246,347 lines / 0 diff.
**v5.53.0 baseline:** preserved at 246,347 lines / 0 diff **by
construction** (no `mapanare/self/*.mn` semantic edits — the 7
migrated sites are AST-equivalent via `to_terse` round-trip, so
the brace stream emitted by `_indent_to_braces` post-migration is
identical to pre-migration → identical MIR / LLVM IR / link-stage
output).

55-release strict streak from v5.7.1 holds at the same value.

**Local STRICT verification cannot run** (no Windows clang for
stage1 rebuild + the local stage1 binaries are WSL ELFs unable to
execute under Windows-cmd). CI is the safety net per the v5.49.0
SESSION_REPORT precedent.

The Python-bootstrap parse of `mapanare/self/lexer.mn` and
`mapanare/self/mnc_all.mn` (post-regeneration) succeeded — the
migration is well-formed Mapanare source. The 88/88 GREEN of
`tests/test_single_line_colon_blocks.py` (was 81/81 pre-Te.3.F,
+7 new tests) is the formatter-level signal.

---

## Test totals

| Suite | Count | Result |
|---|---:|---|
| `tests/test_single_line_colon_blocks.py` | 88 | **88/88** (was 81; +7 new `TestNestedStmtBlock`) |
| Python-bootstrap parse of `mapanare/self/lexer.mn` (post-migration) | 1 | OK |
| Python-bootstrap parse of `mapanare/self/mnc_all.mn` (post-regen) | 1 | OK |
| Goldens via Python bootstrap (tests 01-09 + 10-66 LLVM-emit-only) | partial | OK on tests not requiring binary exec |

Pre-existing unrelated failures (not v5.53.0 regressions; confirmed
by `git stash` + re-run):

- `tests/parser/test_tensor_slice_wildcard.py` (8 cases) — `OSError:
  [WinError 193]` from running ELF binaries on Windows-cmd; same
  shape as v5.49.0 SESSION_REPORT's pre-existing local-Windows
  test infrastructure issue.
- `tests/parser/test_tensor_multi_index.py` (16+ cases) — same
  WinError 193.
- `tests/test_format.py::TestCli::test_directory_walks_recursively`
  — subprocess invocation issue, pre-existing.
- `scripts/ir_doctor.py golden` score 54/103 locally — tests 67-103
  require executing `mapanare/self/mnc-stage1` (WSL ELF) which
  fails with WinError 193 on Windows. CI runs goldens correctly.

---

## Brace surface delta

| Metric | Pre-v5.53.0 | Post-v5.53.0 |
|---|---:|---:|
| First-party `count_user_brace_block_openers` total | 25 | **18** |
| `lexer.mn` nested-stmt-block residuals | 10 | 3 |
| `lower.mn` nested-stmt-block residuals | 1 | 1 |
| Files reaching counter == 0 | 13 of 17 | unchanged (the 3 lexer.mn residuals are chained-if-else) |

The 7-site migration silences the v5.19.0
`_emit_brace_deprecation_warning` for the migrated sites. The 4
remaining sites (chained-if-else in lexer 267/276/285 + lower
4843) continue to fire pending v6.0 grammar work.

The v6.0 hard-removal cut now needs to address 18 first-party
residuals (was tracking 14 in the original v5.53.0 PLAN) plus the
single-line `else:` continuation grammar rule.

---

## Carry-forward into v5.53.1 / v5.54.0 / v6.0

**v5.53.1 (NEXT — fix recipe locked in PRE_PHASE_AUDIT.md):**

- **Sf.\*** — Win64-ABI `__mn_str_free` drop-glue + (companion)
  `__mn_str_concat` aggregate-by-value bypass. ~70-100 LOC across
  Python + self-host emitter + tests. Falsifiability via IR-shape
  gate + Win64 runtime smoke marked `pytest.mark.windows` for CI.

**v5.54.0 (per existing drain plan):**

- **Cl.2** (LOW) — agent stdlib ergonomic refactor (~400 LOC).
- **Cl.3** (LOW) — fs.mn `walk_dir` IR codegen.

**v6.0 (HARD-REMOVAL CUT):**

- Single-line `else:` continuation grammar rule (4 deferred Te.3.F
  sites: lexer.mn 267/276/285 + lower.mn:4843).
- Hard removal of `{}` stmt-block parsing (the v5.19.0 deprecation
  becomes an error).
- 18 remaining first-party `mapanare/self/*.mn` residuals (need
  hand-migration or grammar extension).

---

## Aggregate state entering v5.53.1

- **0 HIGH** (Sf.\* moves to v5.53.1 docket but is structurally
  well-localized + sized; not blocking ship-ability of v5.53.0).
- **3 MEDIUM** — Sf.\* Win64 `__mn_str_free` ABI fix split to
  v5.53.1; macOS notarization carry from v5.33.0 Nu.2; Ai.1
  `_specialize_fn` carry from v5.40.0.
- **~5 LOW** — 4 chained-if-else residuals to v6.0; Lf.4
  variant-name collision to v5.46.x; ergonomic refactor of
  v5.43.0 distributed-agent APIs; fs.mn `walk_dir`; websocket.mn
  `str(byte)`.

**Te.3.F arc CLOSED at v5.53.0** (within v5.48.0 grammar limits).
**Sf.\* arc IN-FLIGHT** — fix recipe locked, v5.53.1 session input
ready. v5.x drain on track for clean v6.0 entry.
