# v5.39.1 — SESSION_REPORT — Js.4.B.1: `from_json::<T>` IR-emission shape fix

**Status:** Ready, not tagged.
**Date:** 2026-05-03.
**Scope:** First of two release sessions dedicated to closing
**Js.4.B** (v5.36.0-deferred typed-serde defect; v5.40.0 Phase 0
audit re-diagnosed it as two distinct bugs, not one). v5.39.1
closes the IR-emission shape mismatch in the no-import case;
**v5.39.2** will close the runtime SEGV in `__mn_map_get` in the
with-import case.

---

## Headline

- **Strict 3-stage fixed point preserved by construction** at
  v5.39.0's 241,898 lines / 0 diff (35-release strict streak from
  v5.7.1). **Zero `mapanare/self/*.mn` source touches** — the
  Phase 0 audit established that `mapanare/self/lower.mn` has no
  `_lower_from_json` / `_lower_decode_to` mirror. The Js.4 surface
  (v5.36.0 Shape B) was Python-bootstrap-only. STRICT preserved
  trivially.
- **Goldens 95/95** preserved.
- **Compiler edit footprint: ~50 LOC Python, all in
  `mapanare/lower.py`** — under the PROMPT's 30-50 LOC ceiling.
  No emitter edits. No semantic edits. No grammar edits.
- **Falsifiability round-trip locked** — see "Falsifiability"
  below.
- **Test additions: 2 new files, 6 new test cases.**
- Bumped `VERSION` 5.39.0 → 5.39.1, `CHANGELOG.md`, `CLAUDE.md`,
  `docs/SPEC.md` header.

## Aggregate state entering v5.39.2

- **1 HIGH:** Js.4.B.2 — runtime SEGV in `__mn_map_get` when user
  imports `stdlib/encoding/json` and calls `from_json::<T>(s)`.
  v5.39.1 fixed the no-import IR-shape side; this remains open.
  See `docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md` for
  diagnosis artifacts (`/tmp/jsdt.mn`, `/tmp/jsbug2.mn`,
  `/tmp/diag.py`).
- **1 MEDIUM:** macOS notarization (carry from v5.33.0 Nu.2).
- **~6 LOW:** unchanged from v5.39.0 carries.

## Diagnosis recap (from v5.40.0 Phase 0 audit)

Two distinct failure modes at v5.39.0 HEAD when user calls
`from_json::<T>(s)`:

1. **No-import case (v5.39.1's scope):**
   `_lower_from_json` → `_lower_decode_to` → emits
   `EnumPayload(variant="Object", ...)` for the `JsonValue`
   subject. Emitter `_do_enum_payload` checks
   `if en in self._enums` — false (JsonValue not registered
   because the user didn't import json). Falls into the
   Result/Option fallback (`emit_llvm_text.py:5187`):
   ```
   else:  # variant != Ok / Err / Some
       r = self._f("pl")
       self._L(f"{r} = extractvalue {et} {ev}, 1")
       dt = self._rty(i.dest.ty)
       self._put(i.dest, r, dt)
   ```
   `extractvalue {i64, ptr} %enum, 1` yields `ptr` (the boxed
   payload pointer), but `_put` tags with `dt = i64` (the dest
   type for an Int field). The next consumer fails IR
   validation:
   ```
   /tmp/serde_simple.ll:142:13: error: '%pl.48' defined with type 'ptr'
                                         but expected 'i64'
     store i64 %pl.48, ptr %t13.a.49
   ```

2. **With-import case (v5.39.2's scope):** valid IR, runtime
   SEGV in `__mn_map_get`. Different bug, different fix.
   **Out of scope for v5.39.1.**

## Strategy A — register canonical layouts at lowering time

The PROMPT/PLAN's audit recommendation. Same shape as
`__struct_meta`'s known set of primitive type encodings.
Hardcoded layout in lower.py is brittle but bounded; the
layout-drift guard test (`test_struct_json_layout.py`) catches
divergence loudly.

Strategy B (fix the emitter fallback) was held — narrower
contract for the fallback path is the right invariant; the
runtime SEGV in v5.39.2 will need the Strategy A path anyway
because `_is_self_ref` recursion only matters once `JsonValue`
is properly registered.

## What changed

### `mapanare/lower.py` (~50 LOC Python edit, only file)

New helper `_ensure_json_types_registered(self) -> None` (45
LOC including layout literal). Registers canonical `JsonValue`
(7 variants — Null, Bool, Int, Float, Str, Array, Object) and
`JsonError` (3 fields — message, line, col) into
`self._module.enums` / `self._module.structs` when not already
present. Idempotent: guarded with
`if "JsonValue" not in self._module.enums`. Layout mirrors
`stdlib/encoding/json.mn:15-29` exactly — verified by
`tests/stdlib/test_struct_json_layout.py`.

Called at the top of `_lower_decode_to` (line 2768) and
`_lower_from_json` (line 2872+1 for the new helper insertion
shift). Both are the entry points for typed-serde lowering;
either path triggers registration before any `EnumPayload` op
is emitted.

Layout uses `MIRType(TypeInfo(...))` wrapping (matches the
stored shape from `_register_declarations` at line 822-848) and
the `mir_int()` / `mir_string()` / `mir_bool()` factory helpers
already imported at line 159-162. No new imports needed.

### Tests added

- `tests/stdlib/test_struct_json_ir_shape.py` (4 cases):
  parametrized over Int / String / Bool single-field structs +
  one mixed Int+String case. Validates with `clang -c` (full IR
  validation, no link). Pre-fix all four fail with the exact
  `'%pl.NN' defined with type 'ptr' but expected ...` error
  shape; post-fix all four pass.
- `tests/stdlib/test_struct_json_layout.py` (2 cases): parses
  `stdlib/encoding/json.mn`, extracts `JsonValue` enum and
  `JsonError` struct AST, asserts shape-for-shape match against
  the lower.py-injected canonical layout. If json.mn drifts
  (variant rename, field reorder, type change), the no-import
  path silently emits IR against the wrong shape — these tests
  fail loudly with a pointer to the lower.py update needed.

### Out of scope (held for v5.39.2 / later)

- Runtime SEGV in `__mn_map_get` when json IS imported.
  v5.39.2's whole release.
- `_is_self_ref` audit for MAP/LIST type-arg recursion. v5.39.2.
- `_decode_json_field` rework. v5.39.2.
- `to_json::<T>` nested-struct recursion (the `<?>` placeholder).
  Same family, separate fix. v5.39.2 or v5.39.3.
- Full link-and-run rewrite of `tests/stdlib/test_struct_json.py`.
  v5.39.2 alongside the runtime fix.
- Self-host mirror — N/A (see deviation below).

## Deviation from PROMPT/PLAN

**Phase 2 (self-host mirror) is structurally N/A.** PROMPT/PLAN
scoped a `mapanare/self/lower.mn` mirror as load-bearing for
STRICT and budgeted ~1h for it. Phase 0 verification:

```bash
$ grep -rn "from_json\|decode_to" mapanare/self/
$ # (zero matches)
```

There is no `_lower_from_json` / `_lower_decode_to` in the
self-host. The Js.4 surface (v5.36.0 Shape B — typed serde
intrinsics `to_json::<T>` / `from_json::<T>`) was added to
Python lower.py only; no self-host mirror has ever been
shipped because mnc-stage1 doesn't compile user-level
`from_json::<T>` calls (none exist in `mapanare/self/`).

Implication: STRICT is preserved trivially by construction.
v5.39.1 makes zero `mapanare/self/*.mn` source touches.
The 35-release strict streak from v5.7.1 continues by
definition.

## Falsifiability round-trip

Before applying the fix, repro confirmed with `/tmp/serde_simple.mn`:

```
struct P { x: Int }
fn main() {
    let s: String = "{\"x\": 42}"
    let r: Result<P, JsonError> = from_json::<P>(s)
    match r {
        Ok(p2) => { print("ok") },
        Err(e) => { print("err") }
    }
}
```

```
$ python3 -m mapanare emit-llvm /tmp/serde_simple.mn -o /tmp/serde_simple.ll
$ clang -c /tmp/serde_simple.ll -o /tmp/serde_simple.o
/tmp/serde_simple.ll:142:13: error: '%pl.48' defined with type 'ptr'
                                      but expected 'i64'
  store i64 %pl.48, ptr %t13.a.49
```

After applying the fix:

```
$ clang -c /tmp/serde_simple.ll -o /tmp/serde_simple.o
$ ls -la /tmp/serde_simple.o
-rw-r--r-- 1 uan uan 3512 ... /tmp/serde_simple.o
```

Round-trip locked: temporarily disabled the helper call (replaced
both `self._ensure_json_types_registered()` lines with
`pass  # disabled for falsifiability check`); reproduced the
exact pre-fix error; reapplied; clean compile. Run-by-run
documented inline so v5.39.2 has the anchor when STRICT
regressions surface.

The falsifiability round-trip is also encoded as the
`test_from_json_no_import_ir_validates` parametrize matrix —
revert the `_ensure_json_types_registered` calls, re-run the
test file, see all parametrized cases fail with the same
pre-fix error shape.

## What didn't fit

Nothing. The fix landed under budget (~50 LOC vs. the PROMPT's
~30-50 LOC target — at the upper end because the layout literal
itself is ~35 LOC). No emitter edits required. No grammar /
semantic / mir.py / mir_opt.py changes. No new C runtime
exports. No stage1 rebuild required to verify the Python fix
(stage1 doesn't lower `from_json` calls).

The bump did require rebuilding stage1 per the v5.31.0 lesson
(VERSION metadata embeds in IR), but the stage1 rebuild itself
is mechanical post-bump.

## Closing

- Compiler edit: ~50 LOC, single file, surgical.
- STRICT preserved by construction at v5.39.0's 241,898 / 0.
- Goldens 95/95.
- Tests added: 6 new cases across 2 files, falsifiability locked.
- CHANGELOG honest about arc framing (v5.39.1 closes IR-shape;
  v5.39.2 will close runtime SEGV).
- SPEC header re-synced to v5.39.1 cut.
- Deviation from PLAN (Phase 2 self-host mirror N/A) documented
  here and in CHANGELOG.
- v5.40.0 (`ask` keyword) still blocked on Js.4.B.2 (runtime
  SEGV) — picks up after v5.39.2.

See `PLAN.md` for the original scope and `PROMPT.md` for the
execution prompt.
