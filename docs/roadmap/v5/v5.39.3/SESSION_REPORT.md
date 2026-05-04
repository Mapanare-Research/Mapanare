# v5.39.3 — SESSION_REPORT — Js.4.C: `to_json::<T>` nested-struct recursion

**Status:** Ready, not tagged.
**Date:** 2026-05-03.
**Scope:** Split-from-v5.39.2 follow-on. v5.39.2 closed the runtime
SEGV in `from_json::<T>` (Js.4.B.2) but explicitly held back the
`to_json::<T>` nested-struct fix — different code path, bundling
would have inflated v5.39.2's scope. v5.39.3 closes that hole.

---

## Headline

- **Strict 3-stage fixed point preserved by construction** at
  v5.39.2's 241,898 lines / 0 diff (**37-release strict streak from
  v5.7.1**). Phase 0 grep
  (`grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/`) returned **0 matches** — the typed-serde surface
  remains Python-bootstrap-only, so the PROMPT-scoped self-host
  mirror is structurally N/A. Zero `mapanare/self/*.mn` source
  touches.
- **Goldens 95/95** preserved.
- **Compiler edit footprint:** ~70 LOC Python in
  `mapanare/lower.py`:
  - `_lower_encode_struct` reduced to a 4-line wrapper
    delegating to the new shared helper.
  - New `_emit_struct_json_body(struct_val, struct_name) -> Value`
    helper (~50 LOC) — moved from the body of the previous
    `_lower_encode_struct` with no semantic change.
  - New `TypeKind.STRUCT` branch in `_encode_field_to_json`
    (~9 LOC) — recurses through `_emit_struct_json_body`, guarded
    on `struct_name in self._module.structs`.
- **Test additions:** 1 new `.mn` test case
  (`stdlib/encoding/json/tests/test_to_json_nested_struct.mn`,
  ~30 LOC) appended to v5.39.2's
  `tests/stdlib/test_struct_json_runtime.py::TEST_FILES`. No new
  `.py` test infrastructure.
- **Bundle scope:** STRUCT only. Phase 1 review of the LIST
  iteration MIR sketch put it at ~30-50 LOC (counter alloca +
  `len()` runtime call + comparison + IndexGet + accumulator) —
  exceeded the ~20 LOC bundle threshold from PLAN. MAP and ENUM
  also held: MAP has the JSON-string-key invariant question
  (reject vs coerce vs runtime-error); ENUM has the tagged-union
  shape question (`"VariantName"` vs `{"Variant": payload}` vs
  `{"tag": ..., "payload": ...}`). v5.39.4 will pick these up
  together.
- **Falsifiability locked.** Reverted the new STRUCT branch in
  `_encode_field_to_json`; ran the new pytest case;
  `FAIL test_to_json_nested_struct: still emits <?> placeholder`
  reproduced the recorded pre-fix signature. Reapplied; case
  passed. Verified once.
- **Bumped** `VERSION` 5.39.2 → 5.39.3, `CHANGELOG.md`,
  `CLAUDE.md`, `docs/SPEC.md` header.

## Aggregate state entering v5.39.4

- **0 HIGH** — Js.4.C closed for STRUCT.
- **1 MEDIUM:** macOS notarization (carry from v5.33.0 Nu.2).
- **~8 LOW:** added `to_json::<T>` LIST/MAP/ENUM nested encoding
  as v5.39.4 candidates (split per Phase 1 bundle decision); also
  added `from_json::<T>` nested-struct decoding as a v5.39.4
  candidate (the round-trip-equality gap surfaced when sketching
  test scope; v5.39.3 ships single-direction encode-and-inspect
  only). Rest unchanged from v5.39.2 carries.

---

## Phase 1 — diagnosis confirmed

PLAN's hypothesis matched HEAD exactly:
`mapanare/lower.py:2681::_encode_field_to_json` had explicit
handlers for `STRING` / `INT` / `FLOAT` / `BOOL` / `OPTION` but no
branch for `TypeKind.STRUCT`. The fallback at line 2762
(`Call(fn_name="str", args=[field_val])`) emitted the literal
`<?>` placeholder via `mapanare/emit_llvm_text.py:3465`'s
`r, _ = self._mkstr("<?>")`.

Pre-fix repro `/tmp/tojson_nested.mn`:

```
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }
fn main() {
    let w: Wrap = Wrap("ok", Inner(42, "hi"))
    print(to_json::<Wrap>(w))
}
```

Pre-fix output: `{"name": "ok", "inner": <?>}`
Post-fix output: `{"name": "ok", "inner": {"x": 42, "y": "hi"}}`

Falsifiability anchor captured.

## Phase 2 — fix applied

Refactor + new branch as PLAN's preferred shape:

```python
def _lower_encode_struct(self, expr: CallExpr, struct_val: Value) -> Value:
    type_arg = expr.type_args[0]
    struct_name = type_arg.name if hasattr(type_arg, "name") else ""
    return self._emit_struct_json_body(struct_val, struct_name)

def _emit_struct_json_body(self, struct_val: Value, struct_name: str) -> Value:
    """Emit MIR producing a JSON `{...}` string for struct_val."""
    fields = self._module.structs.get(struct_name, [])
    # ... (the body that was previously inline in _lower_encode_struct)
```

And in `_encode_field_to_json`, just before the `str()` fallback:

```python
if kind == TypeKind.STRUCT:
    struct_name = ftype.type_info.name if ftype.type_info else ""
    if struct_name and struct_name in self._module.structs:
        return self._emit_struct_json_body(field_val, struct_name)
```

The `struct_name in self._module.structs` guard is defense-in-
depth: any reachable struct definition is registered, but if a
caller hands in a struct type that isn't, the fallback `str()`
keeps the prior behavior rather than crashing in field iteration.

## Phase 3 — self-host mirror N/A (verified)

```
$ grep -rn "from_json\|decode_to\|encode_struct\|to_json" mapanare/self/
(no output)
```

Same pattern as v5.39.1 + v5.39.2 — the Js.4 typed-serde surface
shipped Python-bootstrap-only at v5.36.0 and has not been
self-host-mirrored. STRICT preserved by construction at v5.39.2's
241,898 lines / 0 diff.

## Phase 4 — regression test extended

`stdlib/encoding/json/tests/test_to_json_nested_struct.mn`:

```mn
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }

fn main() -> Int {
    pon w: Wrap = Wrap("ok", Inner(42, "hi"))
    pon encoded: String = to_json::<Wrap>(w)
    si encoded.contains("<?>") {
        print("FAIL test_to_json_nested_struct: still emits <?> placeholder")
    } sino si encoded.contains("\"x\": 42") {
        si encoded.contains("\"y\": \"hi\"") {
            si encoded.contains("\"name\": \"ok\"") {
                print("PASSED test_to_json_nested_struct")
            } sino { print("FAIL ... missing outer name field") }
        } sino { print("FAIL ... missing inner.y field") }
    } sino { print("FAIL ... missing inner.x field") }
    return 0
}
```

Single-direction (encode + inspect) on purpose: the
`from_json::<T>` decoder (`mapanare/lower.py::_decode_json_field`)
only handles primitive field types at v5.39.3 HEAD — a round-trip
equality test would fail on the decode side, not the v5.39.3
fix. Round-trip for nested structs tracked as v5.39.4 candidate.

`tests/stdlib/test_struct_json_runtime.py::TEST_FILES` extended;
7/7 pytest GREEN at HEAD (was 6/6 at v5.39.2 HEAD).

Falsifiability:
- Reverted `_encode_field_to_json`'s STRUCT branch → new case
  fails with the pre-fix `<?>` signature.
- Reapplied → 7/7 GREEN.

## Phase 5 — closeout

- `bump_version.py 5.39.3` clean (VERSION + 4 README badges +
  CHANGELOG section scaffolded).
- CHANGELOG `### Fixed` + `### Changed` + `### Added` filled in
  per PLAN; bundle-scope decision explicit.
- `check_doc_freshness.py` clean.
- `check_changelog_honesty.py` clean.
- SPEC header re-synced from "v5.39.2 cut" to "v5.39.3 cut" with
  new sync block.
- Full test suite: 26 passed + 1 xfailed across the four JSON
  test files (was 25 + 1 at v5.39.2 HEAD; +1 from
  `test_to_json_nested_struct.mn`).

## Why no LIST bundle

PLAN's bundle decision rubric specified LIST bundles "if and only
if the runtime list-iteration MIR is straightforward (sketch fits
in ~20 LOC)." Sketch:

```
i = 0; out = "["
while i < len(xs):
    if i > 0: out = out + ", "
    elem = xs[i]
    elem_str = _encode_field_to_json(elem, inner_type)
    out = out + elem_str
    i = i + 1
out = out + "]"
```

Translated to MIR ops: alloca for `i` and `out`, `Const` for
initial values, `Call` to `len`, `BinOp` comparison, `Branch`,
loop body block with `BinOp` (i > 0 check) + `Branch` + comma
append + `IndexGet` + recursion + accumulation, `BinOp` increment,
`Jump` back to header, exit block with closing bracket append.
Conservative sketch: ~35-50 LOC of new helper code in
`_encode_field_to_json` (or a new
`_emit_list_json_body(list_val, inner_type) -> Value` helper).
Above the bundle threshold. Held for v5.39.4.

## Why no MAP / ENUM bundle

Both have invariant questions that deserve session-level alignment
with the `from_json::<T>` decode side:

- **MAP**: JSON requires string keys. `Map<Int, String>` and
  `Map<Float, String>` are valid Mapanare types. Encoding options:
  (a) reject non-string-keyed maps at typecheck (cleanest, breaks
  existing code if any), (b) coerce keys via `str()` (lossy for
  Float, surprises on Int), (c) emit invalid JSON and let the
  decoder's typecheck catch it (worst). v5.39.4 should pick one
  and align both directions.

- **ENUM**: Tagged-union JSON shapes vary across ecosystems —
  `"VariantName"` for unit, `{"Variant": payload}` (Rust serde
  default), `{"tag": "Variant", "payload": ...}` (TypeScript-ish),
  internally-tagged, externally-tagged. The shape decision is
  load-bearing for round-trip — both `to_json::<T>` and
  `from_json::<T>` need to agree.

v5.39.4 PLAN should bundle LIST + MAP + ENUM with the matching
`from_json::<T>` decode-side recursion so the typed-serde round-
trip is end-to-end testable.

---

## Files touched

```
M  mapanare/lower.py                                        (~70 LOC)
A  stdlib/encoding/json/tests/test_to_json_nested_struct.mn (~30 LOC)
M  tests/stdlib/test_struct_json_runtime.py                 (+2 LOC)
M  CHANGELOG.md                                             (~75 LOC)
M  docs/SPEC.md                                             (~30 LOC)
M  CLAUDE.md                                                (~release-notes entry)
A  docs/roadmap/v5/v5.39.3/SESSION_REPORT.md                (this file)
M  VERSION                                                  (5.39.2 → 5.39.3)
M  README.md                                                (badge bump)
M  docs/README.es.md                                        (badge bump)
M  docs/README.pt.md                                        (badge bump)
M  docs/README.zh-CN.md                                     (badge bump)
```
