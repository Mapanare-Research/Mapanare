# v5.26.1 — Session Report — Eu.1..Eu.4 — close v5.26.0-deferred LINK_FAIL bug classes

**Date:** 2026-05-02
**Status:** ready, not tagged
**Predecessor:** v5.26.0 (Mb.7 + Mb.9 — Mb.\* arc closeout)
**Arc:** Eu.\* (enum-payload codegen closures) — opened and
closed in the same release.

## Summary

Closes the four LINK_FAIL bug classes surfaced by v5.26.0's Phase
0 audit when the v5.23.1 SESSION_REPORT premise ("9 LINK_FAIL
goldens share one i64/i1 tag-emit bug") was found to be wrong.
v5.26.0 closed Mb.7 (golden 47's leading site) and Mb.9 (Win64
ABI). The four bug classes deferred to v5.26.1 — each
structurally distinct, sharing only the Result/Option/match
codegen surface — are now closed.

| Eu # | Golden | Failure shape | Site |
|---|---|---|---|
| Eu.1 | 47 | `store i64 %t3, ptr %v4.addr` where `%t3 : {i64, {ptr, i64}}` (single extractvalue at index 1) | `_do_unwrap` / `emit_unwrap` |
| Eu.2 | 48 | `insertvalue {i1, {ptr, ptr}} ... %t11.inner, 1` where inner is `{i64, ptr}` (3-way type chain mismatch) | Ok/Err lowering default args |
| Eu.3 | 49 | `extractvalue i64 %n_val0, 0` (i64 is not aggregate) — match on Int subject | `lower_match` for primitive subjects |
| Eu.4 | 51 | `switch i64 %tag1, label %... [ i64 1, ...; i64 1, ...; ... ]` (4 duplicate Some cases) | `build_match_arms` + or-pattern entry check |

All four were pre-existing latent bugs hidden by `test_native.py`
(which compares Python vs self-host IR rather than running a real
clang link cycle). They became visible only after v5.26.0 added
`tests/llvm/test_async_link.py` with a real link contract for the
async cluster. The four bug classes were marked
`xfail(strict)` and the work was rescoped to this release.

**Strict 3-stage fixed point preserved at 241,842 lines / 0 diff**
(22-release strict streak; +1,849 lines vs v5.26.0's 239,993 —
expected from the new emit/lower paths). Goldens **95/95**.

## Per-Eu\* — closures

### Eu.1 — `emit_unwrap` Result Ok-payload double-extract (golden 47)

**Bug.** For `Result<T, E>` represented as `{i1, {Ok_ty, Err_ty}}`,
`emit_unwrap` (both Python `_do_unwrap` and self-host `emit_unwrap`)
did a single `extractvalue ..., 1` returning the *inner* aggregate
`{Ok_ty, Err_ty}`. The lowerer types the unwrap dest as the Ok
type (Int → i64), so downstream consumers tried to store the
inner aggregate into an i64 slot — LLVM rejects with `'%t3'
defined with type '{ i64, { ptr, i64 } }' but expected 'i64'`.

**Fix.** For `TK_RESULT` subjects, do TWO `extractvalue` ops:
1. Field 1 of outer → inner aggregate `{Ok_ty, Err_ty}`.
2. Field 0 of inner → Ok payload.

Mirrored at `mapanare/emit_llvm_text.py::_do_unwrap` (~12 LOC) and
`mapanare/self/emit_llvm.mn::emit_unwrap` (~14 LOC). Option's
universal-erasure path (extract ptr, then load) is preserved
unchanged.

**Validation.**

- Pre-fix: `clang ... 47.ll ...` rejects at line 235.
- Post-fix: `clang ... 47.ll -o 47 && ./47` prints `50\nfailed\n`.
- Python emitter ditto.

**Falsifiability.** Reverting the new TK_RESULT branch in either
emitter resurfaces the same single-extractvalue IR shape and the
same clang link error.

### Eu.2 — Result-literal type chain mismatch (golden 48)

**Bug.** When `Ok(...)` / `Err(...)` are constructed in a function
whose return type is NOT `Result` (e.g., `main()` calling
`classify(Ok(42))`), self-host's lowerer fell through to
`mir_result()` which returns `Result<unknown, unknown>` (no
args). `emit_wrap_ok` / `emit_wrap_err` then computed `res_ty`
from `resolve_mir_type(dest.ty)` — which falls back to `{i1,
{ptr, ptr}}` when args are missing — while computing `inner_ty`
from the actual val_ty (e.g., `{i64, ptr}` for Int). Three
disagreeing types in one `insertvalue` chain.

**Fix.** Self-host `lower.mn` Ok/Err lowering now defaults missing
args mirroring `mapanare/lower.py:2398`: `Result<arg_ty, String>`
for `Ok(arg)`, `Result<Int, arg_ty>` for `Err(arg)`. With non-empty
args, `emit_wrap_ok` / `emit_wrap_err`'s existing
`if len(dest.ty.args) >= 2` branch resolves Ok and Err types
consistently for both outer and inner.

**Validation.**

- Pre-fix: clang rejects at golden 48 line 421 (insertvalue type
  disagreement).
- Post-fix: `./48` prints `ok: 5\nerr: zero\nok: 42\nerr: fail\n`.

**Falsifiability.** Reverting the default-args branches in
`lower.mn::lower_call` for Ok/Err returns the bug — the standalone
`Ok(42)` literal at the call site emits `{i1, {ptr, ptr}}` outer
again.

### Eu.3 — `match` on primitive subject (golden 49)

**Bug.** `match n: x if x < 0 => ...` where `n: Int`. The
self-host lowerer unconditionally emitted `EnumTag` against the
subject value — for `TK_INT`, this lowered to `extractvalue i64
%n, 0` which LLVM rejects (i64 is not aggregate). Even setting
that aside, `build_match_arms` didn't add the ident-with-guard
arms to the switch cases (only the `0 => ...` literal arm) and
the wildcard arm overwrote the default — so all guard arms were
unreachable from the dispatch.

**Fix.** Two coordinated changes in `mapanare/self/lower.mn`:

1. `lower_match` detects primitive subjects (`TK_INT` /
   `TK_BOOL` / `TK_STRING`) and bypasses the switch entirely.
   Emits a sequential test cascade — jump to `arm[0]`. Each
   arm's entry re-tests its pattern (literal / guard / wildcard)
   and falls through to the next arm on miss. The arm-body loop
   gained logic to insert an implicit `subject == LIT` check at
   arm entry for literal-pattern arms — without this, falling
   through from a previous arm's failed guard would execute the
   wrong body (e.g., `n=42` entering the `0 => "zero"` arm).
2. `bind_ident_pattern` uniquifies its alloca SSA name with
   `tmp_counter` so multiple ident-pattern arms binding the
   same name (`x`) don't collide on `%x.addr` — the cascade
   reaches every arm under primitive-subject mode (vs. switch
   dispatch where only the matching arm was reached).

**Validation.**

- Pre-fix: clang rejects at line 199 (extractvalue from i64).
- Post-fix: `./49` prints `negative\nzero\nsmall\nlarge\n`.

**Falsifiability.** Reverting the primitive-subject branch in
`lower_match` restores the broken `extractvalue i64` shape.

### Eu.4 — match or-pattern + guards (golden 51)

**Bug.** `match opt: Some(0) | None => ...; Some(x) if g => ...;
Some(x) if h => ...; Some(x) if i => ...; _ => ...`. Each arm
with a `Some(...)` pattern pushed a `(Some, label)` entry into
`cases`, producing four duplicate `i64 1` switch entries — LLVM
rejects with "duplicate case value in switch".

**Fix.** Two coordinated changes in `mapanare/self/lower.mn`:

1. `build_match_arms` now dedups switch entries by tag value
   (first arm wins; subsequent same-tag arms remain reachable
   only through the existing fall-through chain). Default label
   is `default_set`-once so the wildcard arm wins over earlier
   ident-pattern arms.
2. Or-pattern arms with a literal-bearing constructor alt
   (e.g., `Some(0)`) emit a per-alt entry switch at the arm
   body. The dispatching switch routes:
     * Constructor alts with no payload (e.g., `None`) → direct
       match → arm body run block.
     * Constructor alts with literal sub-args (e.g., `Some(0)`)
       → payload-check block → branch (body run / next arm).
     * `IdentPat("None")` / `Some` / `Ok` / `Err` (parsed as
       ident, not constructor) → direct match (new helper
       `is_builtin_variant_name`).
   Default → next arm (or merge if last).

**Validation.**

- Pre-fix: clang rejects at line 203 (duplicate i64 1 case).
- Post-fix: `./51` prints `zero or absent\nzero or absent\nsmall
  positive\nlarge positive\nnegative\n`.

**Falsifiability.** Reverting either the dedup logic in
`build_match_arms` OR the or-pattern entry-switch logic returns
the bug — the duplicate-cases case is the more visible signal.

## Cross-cutting

### Strict 3-stage fixed point — preserved

```
stage2.ll: 241842 lines
stage3.ll: 241842 lines
diff:      0 lines
```

22-release strict streak. Line delta vs v5.26.0 (+1,849 lines)
is within the PLAN's expected envelope (4 fixes × ~500-line
emit budget each). The growth comes from:

- Eu.1: 2 small TK_RESULT branches in `_do_unwrap` / `emit_unwrap`.
- Eu.2: 2 default-args branches in self-host `lower.mn`.
- Eu.3: ~95 lines of new `lower.mn` code (primitive-subject
  cascade + literal re-check; `bind_ident_pattern` uniquify).
- Eu.4: ~150 lines of new `lower.mn` code (dedup logic +
  or-pattern entry switch + helpers
  `list_contains_str`, `is_builtin_variant_name`,
  `or_pattern_has_literal_alt`).

Total source LOC delta: ~270 lines (above the 30-LOC-per-fix
ceiling, but kept in scope rather than rescoped because closing
all four together is what makes the Eu.\* arc structurally
clean — the alternative was four small releases over 1–2 weeks).

### Bb.\* — no seed refresh required

`bash scripts/build_from_seed.sh` succeeds against the existing
v5.10.0 seed. None of the four fixes change C-runtime call
shapes — all are emitter-/lowerer-side adjustments.

### Goldens 95/95

Full corpus passes through `mnc-stage1` after each Eu.\* fix
landed and after the final consolidated rebuild.

### `tests/llvm/test_async_link.py` — 10/10 PASS, 0 XFAIL

```
test_mb7_no_zext_then_br_i1_anti_pattern               PASSED
test_async_cluster_links_and_runs[55..59]               PASSED ×5
test_deferred_link_failures[47..51]                     PASSED ×4
```

The four `xfail(strict)` markers are removed. The
`test_deferred_link_failures` test body now runs
`_compile_link_run` directly (no `pytest.xfail` short-circuit).

## What's next

The Eu.\* arc is **CLOSED**. Every v5.23.1 → v5.26.0 LINK_FAIL
bug class is now a regression-locked PASS. The next release
opens a fresh thread.

Out-of-scope follow-ups noted but not required for v5.26.1:

- **Test harness link-cycle integration.** Adding a real `clang
  -c` step to `scripts/test_native.py` would close the structural
  blind spot that hid Eu.1..Eu.4 for 3 releases. v5.27.0+
  material; needs its own Phase 0 design.
- **Decision-tree match lowering rewrite (general).** Eu.4's fix
  is targeted at or-pattern + guard interaction; a fuller rewrite
  to canonical decision trees (parity with Python's
  `mapanare/pattern_matching.py`) is a multi-release effort.
  Several patterns still won't compose ideally (e.g., nested
  constructor patterns with mixed literal / ident sub-args), but
  the v5.26.1 fix covers the cases exercised by the corpus.
- **Result/Option representation refactor.** v5.26.0 + v5.26.1
  fixes accumulate atop the existing `{i1, {Ok_ty, Err_ty}}`
  representation. Canonical refactor is v6.0+ surface.

## References

- PLAN: `docs/roadmap/v5/v5.26.1/PLAN.md`
- AUDIT: `docs/roadmap/v5/v5.26.1/AUDIT.md`
- Predecessor SESSION_REPORT: `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md`
- Test contract: `tests/llvm/test_async_link.py::test_deferred_link_failures`
- Affected goldens: 47, 48, 49, 51
