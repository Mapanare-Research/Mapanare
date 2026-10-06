# v5.47.0 — Cl.* — pre-panel hygiene cleanup; SESSION_REPORT

**Status:** ready, not tagged.
**Theme:** Cl.* — pre-panel hygiene cleanup. Mirrors v5.28.0
hygiene-before-panel precedent (the +0.31 panel recovery there came
specifically from H.* hygiene closures landing ahead of panel cut).
v5.47.0 substantively closes Lf.4 + websocket str(byte) cleanup;
two Phase-0-driven scope splits (Cl.2 + Cl.3) keep the
hygiene-release scope tight and re-target both for v5.47.1.

---

## Headline numbers

- **STRICT 3-stage fixed point preserved at 244,654 lines / 0 diff.**
  50-release strict streak from the v5.7.1 baseline. +889 lines vs
  v5.46.0's 243,749 from new self-host paths (semantic.mn +
  lower.mn + lower_state.mn).
- **Goldens 103/103.** v5.46.0's 102 + new
  `103_variant_name_collision.mn` (Cl.6).
- **Tests:** `tests/llvm/test_lowerer_fixes.py` 8/8 GREEN
  (was 5; +3 new Lf.4 cases). `tests/stdlib/test_websocket.py`
  61/61 GREEN. `tests/semantic/` + `tests/parser/` 567/567 GREEN.
- **Source delta:** ~80 LOC compiler (semantic.py + self-host
  semantic.mn + lower.mn + lower_state.mn) + ~30 LOC stdlib
  (websocket.mn) + ~85 LOC golden + ~80 LOC test_lowerer_fixes.py
  extension + ~200 LOC PRE_PHASE_AUDIT.md + ~250 LOC SESSION_REPORT
  + ~140 LOC CHANGELOG `### Fixed` (Cl.1, Cl.4) + `### Changed`
  (Cl.2/Cl.3 splits) + ~30 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical `bump_version.py` edits.

---

## What shipped

### Cl.0 — Phase 0 audit (`PRE_PHASE_AUDIT.md`)

Reproduced each Cl.* item at v5.47.0 HEAD. Confirmed:

- **Cl.1 Lf.4 still open.** Both Python bootstrap and self-host
  stage1 reject `pon n: NetworkError = TransportLost("net")` with
  `Type mismatch: declared type NetworkError but initial value is
  ExitReason`. Self-host has the bug too; mirror is non-trivial.
- **Cl.3 still open.** v5.46.0 Lf.* did NOT close it as a
  side-effect; clang still rejects `extractvalue ptr ... 0` then
  `zext ptr to i64` in `stdlib/fs.mn` IR.
- **Cl.4 sites enumerated.** 11 `str(byte)` calls in
  `read_frame`, `build_send_frame`, chunked-send paths.

**Cl.1 LOC measurement:** ~80 LOC across `mapanare/semantic.py`
(~40) + `mapanare/self/semantic.mn` (~40 + 7-constructor field
addition + helper) + `mapanare/self/lower.mn` (~20 hint logic) +
`mapanare/self/lower_state.mn` (~25 field + helper). Above the
strict ≤60 LOC bundle threshold but in the tight bundle range.
Decision: bundle.

### Cl.1 (Lf.4) — variant-name collision fix

**Bug shape.** Variant lookup by unqualified name; the second
enum's `define()` call shadows the first. Constructor calls and
bare-variant references resolve to the last-registered enum's
variant, not the binding's expected enum.

**Python bootstrap fix** (`mapanare/semantic.py`):
- Added `_variant_alternatives: dict[str, list[(enum_name,
  type_info, has_payload)]]` field on `SemanticChecker`.
- Populated during `_register_definitions` enum-variant
  registration loop alongside the existing `global_scope.define()`
  call.
- Added `_expected_type: TypeInfo | None` context field.
- `_check_let` threads the binding's annotation as `_expected_type`
  before `_infer_expr(let.value)`; restores in `finally`.
- `_check_call` (constructor with payload) and the `Identifier`
  branch in `_infer_expr` (bare variant) consult
  `_variant_alternatives` when the name has multiple alternatives;
  return the alternative matching `_expected_type.name`.

**Self-host stage1 fix** (Cl.5 mirror):
- `mapanare/self/semantic.mn`: added `expected_type: TypeInfo` to
  `SemState`. Mechanical update of all 7 constructor sites
  (single-line struct literals — multi-line not parsed). New
  `set_expected_type` helper.
- `check_let_stmt` threads the annotation as `expected_type`
  before `infer_expr`; restores after.
- New post-inference helper `scope_has_variant_for_enum(scope,
  variant_name, enum_name)` walks `Scope.symbols` (which appends
  rather than replacing — both colliding variants ARE in the list,
  only differ in `scope_lookup` order). Walks parent scopes via
  recursion. Checks both `sym.type_info.name == enum_name`
  (bare-variant case) and `sym.type_info.return_type.name ==
  enum_name` (constructor case).
- Post-inference disambiguation in `check_let_stmt`: if
  `ann_type.name != value_ti.name` AND
  `scope_has_variant_for_enum(...)` returns true, override
  `value_ti = ann_type`.
- `mapanare/self/lower_state.mn`: added `expected_enum_name:
  String` to `LowerState`. New helper `enum_has_variant(st,
  enum_name, variant)`.
- `mapanare/self/lower.mn`: `lower_let` resolves type_ann; if
  TK_ENUM, sets `st.expected_enum_name = hint_ty.name` before
  `lower_expr`; restores after. `lower_call_by_name`'s
  enum-variant branch consults `st.expected_enum_name` and prefers
  it over `enum_name_for_variant`'s first-match result when
  `enum_has_variant` confirms the hinted enum has the variant.

**Falsifiability locked** in `tests/llvm/test_lowerer_fixes.py`
module docstring + per-test docstring. Reverting either layer
(semantic-checker resolver OR lowerer hint) breaks the
corresponding test:
- semantic-only revert → semantic check rejects the construction
  (no IR emitted; rc != 0)
- lowerer-only revert → wrong-shape IR (`store %enum.ExitReason
  %t4, ptr %x5.addr` into NetworkError-shaped slot)

### Cl.4 — websocket str(byte) cleanup

11 `str(byte0)` / `str(byte1)` / `str(0)` / `str(b4..b7)`
decimal-stringification calls in `stdlib/net/websocket.mn`
replaced with `__mn_str_chr(...)`. Added extern declaration
`__mn_str_chr(code: Int) -> String` (v5.43.0 Da.0 C runtime
export — already covers bytes 0..255 with byte 0x00
preservation). Pre-existing `tests/stdlib/test_websocket.py` 61
cases preserved GREEN (the websocket cases compile but do not
execute against a live socket; behavior was correct for ASCII
bytes before, correct for high bytes after).

### Cl.5 — self-host mirror

Non-trivial (unlike v5.46.0's no-op gate). Stage1 rebuilt cleanly
post-edit in 17 seconds; goldens 102/102 stayed GREEN throughout
each rebuild iteration. STRICT 3-stage fixed point preserved at
244,654 lines / 0 diff.

**Lesson captured:** initial `scope_has_variant_for_enum` helper
checked only `sym.type_info.name == enum_name`, missing the
constructor case where `sym.type_info` is the function-type with
`name = "<builtin>"` and the actual enum name lives in
`type_info.return_type`. Without checking both shapes, the
disambiguation didn't fire. Phase 1 re-verified by direct repro
on stage1 binary. Cost: one extra rebuild cycle.

**Lesson captured:** the Mapanare match arm with `=> { ... }`
block-form action does not accept a nested `match` with multi-line
arms in the same body. First version of `scope_has_variant_for_enum`
used `match sym.type_info.return_type:` with `Some(rt) => { if ... }`
and failed to parse. Second version used flag-based control flow
(`got_ret`, `have_ret`) and parsed cleanly. Documented as a v5.40+
parser-ergonomics candidate (already tracked from v5.39.5).

### Cl.6 — test corpus

- New `tests/golden/103_variant_name_collision.mn` (~85 LOC).
  Covers two enums sharing two variant names (TransportLost +
  third unique variant per enum). Tests construction +
  match-dispatch on both colliding and non-colliding variants.
- Extended `tests/llvm/test_lowerer_fixes.py` with
  `test_lf4_variant_name_collision` (asserts golden 103 stdout
  `["net=1", "exit=10", "net2=2", "exit2=20"]`) +
  `test_lf4_minimal_pair[0/1]` parametrized cases (minimal 2-enum
  shape with shared variant name).
- Bumped `tests/llvm/test_llvm_link_all.py::test_golden_corpus_count`
  from 102 to 103.

### Cl.7 — closeout

Standard mechanical bump + CHANGELOG fill + SPEC sync + README
golden-count bumps + this SESSION_REPORT.

---

## PROMPT/PLAN deviations surfaced

1. **Cl.2 — Agent stdlib ergonomic refactor SPLIT to v5.47.1.**
   PLAN/PROMPT scoped Cl.2 inside v5.47.0 (~4h). Phase 0 Cl.2
   surface enumeration found ~12 public functions across 4 files
   plus ~50+ internal callers and `tests/stdlib/test_distributed_
   agents.py` 4-case shape change. Estimated ~400 LOC across
   public-API surfaces. Honest assessment: this exceeds
   "hygiene release" scope without dedicated focus and risks
   subtle agent-stdlib regressions on a release timeline. The
   Cl.1 fix is the load-bearing structural enabler; v5.47.1
   ships the refactor with dedicated focus. Documented in
   CHANGELOG `### Changed`.
2. **Cl.3 — `stdlib/fs.mn::walk_dir` IR codegen SPLIT to v5.47.1.**
   PLAN listed this as 2h conditional ("if v5.46.0 closed it,
   skip"). Phase 0 verified still open with a wrong-IR-shape class
   different from Lf.1 (Result aggregate at the destructure site
   comes through as `{ptr, i64, i64, i64, i64}` with no leading
   tag — receiver-side wrong-shape, not constructor-side). The
   fix lives in `mapanare/lower.py::_lower_match` for
   `Result<NonTrivialOk, E>` patterns where the enclosing fn does
   NOT return Result; the diagnosis-to-fix path is non-trivial.
   Documented in CHANGELOG `### Changed`.
3. **Cl.5 self-host mirror is non-trivial.** PLAN noted "Cl.1
   requires mirror in `mapanare/self/semantic.mn` +
   `mapanare/self/lower.mn`." Phase 0 verified stage1 has the
   same Lf.4 bug AND the lowerer-side variant-name resolution
   uses first-match without context (different from v5.46.0
   where self-host already had Eu.2 fix). Cl.5 budget
   (~3h in PLAN) was accurate; mirror is real work, ~80 LOC.
4. **Bundle/split decision honored at Phase 0.** Per PROMPT:
   "≤ 60 LOC = bundle; > 60 LOC tight; > 100 LOC = re-split."
   Cl.1 measurement landed at ~80 LOC (tight bundle). Bundled
   per Phase 0 decision; STRICT preservation verified at Phase 6.
5. **No new C runtime exports.** Cl.4 used existing v5.43.0
   `__mn_str_chr` export; Cl.1 used existing string-comparison
   helpers. PROMPT guarded against new exports; Phase 6
   confirmed not needed.
6. **No drop-glue / aliasing edits.** Different bug class than
   v5.45.0; standard pytest gate sufficed.

---

## Aggregate state entering v5.47.5

- **0 HIGH carries.**
- **2 MEDIUM** (Cl.2 split — agent stdlib ergonomic refactor;
  Cl.3 split — fs.mn walk_dir IR codegen). Both were LOW pre-
  v5.47.0; the splits explicitly track them at v5.47.1
  rather than letting them age. macOS notarization carry from
  v5.33.0 Nu.2 still pending (paid Apple Developer cert
  dependency; v6.0+ when paid distribution makes it worthwhile)
  — held LOW.
- **~6 LOW** (Ai.1 `_specialize_fn` body-walk for generic stdlib
  calling generic intrinsics, carry from v5.40.0; pre-existing
  v5.44.1 `Tensor<Int>` parser bug; carries from v5.46.0).

**Tensor closeout arc CLOSED at v5.45.0.**
**Manifesto arc CLOSED at v5.43.0.**
**Package-system runway CLOSED at v5.44.0.**
**v5.43.0 lowerer-bug closeout CLOSED at v5.46.0.**
**Pre-panel hygiene cleanup CLOSED at v5.47.0** (with two scope
splits to v5.47.1).

The v5.47.5 closeout panel reviews a docket smaller than v5.47.0
HEAD because Cl.1 + Cl.4 are gone; Cl.2 + Cl.3 are explicitly
named for v5.47.1 (panel can defer-confirm rather than discover).

---

## Tag policy

Per project memory `feedback_v5_tag_timing.md`: never bump to
v5 or create v5 tags without explicit user approval. v5.47.0
ships ready, not tagged.
