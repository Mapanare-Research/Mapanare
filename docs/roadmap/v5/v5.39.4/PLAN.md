# v5.39.4 — PLAN — typed-serde round-trip closure (LIST encode + nested-struct decode)

> Split-from-v5.39.3 follow-on. v5.39.3 closed the
> `to_json::<T>` nested-struct gap (Js.4.C) for the **STRUCT**
> kind only. PLAN's Phase 1 bundle review held LIST / MAP / ENUM
> for follow-on releases — LIST exceeded the ~20 LOC bundle
> threshold, MAP and ENUM raised invariant questions that
> deserved their own session. Symmetrically, `from_json::<T>`'s
> `_decode_json_field` only handles primitive field types at
> v5.39.3 HEAD — so the typed-serde round-trip
> (`to_json` ↔ `from_json`) does not yet work end-to-end for
> any shape more complex than a flat-primitive struct. v5.39.4
> closes the two highest-leverage gaps: **LIST encode** and
> **nested-struct decode**. Together they unlock a working
> `to_json::<T>` ↔ `from_json::<T>` round-trip for the shapes
> v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns. MAP / ENUM /
> nested-collection-decode held for v5.39.5+ with documented
> invariant decisions.

## Scope

**Two bug-class fixes, two code paths, one release.** Each fix
in isolation is ~30-50 LOC compiler + ~30 LOC tests; together
they're approximately 2× the size of v5.39.3 but still
significantly smaller than v5.39.2.

### Js.4.D.1 — `to_json::<T>` LIST nested encoding

**Bug.** `to_json::<T>(t)` for a struct with a List-typed field
emits the field as `<?>` instead of recursing element-by-
element. Repro at v5.39.4 HEAD:

```mn
struct Bag { name: String, items: List<Int> }
fn main() {
    let b: Bag = Bag("box", [1, 2, 3])
    print(to_json::<Bag>(b))
}
```

Actual:   `{"name": "box", "items": <?>}`
Expected: `{"name": "box", "items": [1, 2, 3]}`

**Root cause.** Same dispatch as v5.39.3:
`mapanare/lower.py::_encode_field_to_json` falls through to the
`str()` fallback for `TypeKind.LIST`, producing the placeholder
via `mapanare/emit_llvm_text.py:3465`.

**Fix shape.** Add a `TypeKind.LIST` branch that:
1. Allocates a `mut accumulator: String = "["`.
2. Calls `len(field_val)` to get count.
3. Loops `i = 0..count`:
   - If `i > 0`, appends `", "`.
   - `IndexGet` element at `i` (typed by `ftype.type_info.args[0]`).
   - Recursively calls `_encode_field_to_json(elem, inner_type)`.
   - Appends element string to accumulator.
4. Appends `"]"` and returns.

Need new `_emit_list_json_body(list_val, inner_type) -> Value`
helper to keep the dispatch table readable. ~40-50 LOC of MIR
emission (counter alloca, loop header / body / exit blocks,
`IndexGet`, `Phi` merge for accumulator across loop iterations).

**Reference shape:** look at how v3.x `for x in xs` lowering
produces the runtime loop in `mapanare/lower.py` (search for
`while` / `IndexGet` with a counter). The Js.4.D.1 emitter
mirrors that pattern but accumulates strings instead of running
arbitrary user code.

### Js.4.D.2 — `from_json::<T>` nested-struct decoding

**Bug.** `from_json::<Wrap>(s)` for a `struct Wrap { name:
String, inner: Inner }` succeeds at parse time but the inner
Struct field gets decoded as if it were a primitive — actual
behavior at HEAD: `from_json` returns `Err(...)` with
`TypeMismatch` on the inner field, OR the inner field is
silently zero-initialized depending on the path. Repro:

```mn
struct Inner { x: Int, y: String }
struct Wrap { name: String, inner: Inner }
fn main() {
    let s: String = "{\"name\": \"ok\", \"inner\": {\"x\": 42, \"y\": \"hi\"}}"
    let r: Result<Wrap, JsonError> = from_json::<Wrap>(s)
    match r {
        Ok(w) => print(w.inner.y),  // expect "hi"; actual: error or empty
        Err(e) => print("decode error")
    }
}
```

**Root cause.** `mapanare/lower.py::_decode_json_field` (same
file family as v5.39.3's fix point, around `lower.py:3002`)
dispatches on the field type but has explicit handlers only for
primitive kinds (`STRING` / `INT` / `FLOAT` / `BOOL`) plus
`OPTION`. For `STRUCT`, it falls through to a path that returns
a `TypeMismatch` JsonError or zero-initializes the struct via
its constructor.

**Fix shape.** Add a `TypeKind.STRUCT` branch in
`_decode_json_field` that:
1. Pulls the field's JSON sub-value (a `JsonValue::Object(...)`).
2. Calls a new shared helper
   `_decode_struct_from_json_value(json_val, struct_name) ->
   Value` that:
   - Iterates the struct's field list (from
     `self._module.structs[struct_name]`).
   - For each field, looks up the key in the
     `Map<String, JsonValue>` (the boxed payload).
   - Recursively calls `_decode_json_field` per field.
   - Constructs the struct via the v5.36.0 typed-decode
     pattern (mirror what `_lower_decode_to`'s top-level path
     does — extract a shared helper if clean, or duplicate
     the body if `_lower_decode_to` resists extraction;
     v5.39.3's `_emit_struct_json_body` extraction is the
     reference precedent).
3. Returns the constructed struct as the field value.

This is symmetric with v5.39.3's encode-side
`_emit_struct_json_body` extraction. Most likely shape: extract
`_decode_struct_body(json_val, struct_name) -> Value` from
`_lower_decode_to` and call it from both the top-level intrinsic
path and the new STRUCT field-recursion branch.

**Pair invariant: encode and decode must agree on the field
ordering.** v5.39.3's `_emit_struct_json_body` reads
`self._module.structs[struct_name]` in declaration order. The
decoder must read JSON keys *by name lookup*, not by position
— JSON objects are unordered. If the decoder reads keys
positionally, a struct re-ordering (or a JSON producer that
emits fields in a different order) silently breaks round-trip.
Phase 1 audit must confirm `_decode_json_field` looks fields up
by string key, not by index.

## Out of scope (held for v5.39.5+)

- **MAP encoding** (`to_json::<T>` for struct field of type
  `Map<K, V>`). Invariant question: JSON requires string keys.
  Mapanare's `Map<Int, V>`, `Map<Float, V>`, etc. are valid
  Mapanare types but not valid JSON. Three options:
  (a) reject non-string-keyed maps at typecheck (cleanest;
  potentially breaks existing code that uses
  `Map<Int, X>` for non-serialization purposes — has to be
  scoped narrowly to the `to_json` call site, not Map-in-
  general); (b) coerce keys via `str()` (lossy for Float;
  surprises on Int → `"42"`); (c) emit invalid JSON with
  numeric keys and let the caller deal. v5.39.5 PLAN should
  audit existing `Map<Int, V>` usage in stdlib + golden tests
  to see how breaking option (a) actually is. Tentative
  recommendation: option (a) but enforced only at the
  `_encode_field_to_json` MAP branch, not at typecheck — so
  the error surfaces at compile time when `to_json::<T>` is
  called on a struct with a non-string-keyed map field, but
  unrelated `Map<Int, V>` use is unaffected.

- **ENUM encoding** (user-defined enums beyond `Option` /
  `Result`). Invariant question: tagged-union JSON shape.
  Common conventions:
  - **Externally-tagged** (Rust serde default):
    `{"VariantName": payload}` for unit variants,
    `{"VariantName": {"field": ...}}` for struct variants.
    Pros: clean, parses unambiguously. Cons: variant names
    leak into JSON keys.
  - **Internally-tagged**: `{"type": "VariantName", "field":
    ...}`. Pros: variant name explicit and discoverable.
    Cons: payload's own fields collide with the tag key.
  - **Adjacently-tagged**: `{"type": "VariantName",
    "payload": {...}}`. Pros: no field collision. Cons:
    verbose for unit variants.
  - **Untagged**: just the payload. Cons: ambiguous for
    same-shape variants; unsafe for round-trip.

  v5.39.5 PLAN must pick one and document. Tentative
  recommendation: externally-tagged (Rust serde default) — it
  matches the most-cited reference implementation in this
  ecosystem. Decode side mirror is straightforward.

- **Decode for LIST / MAP / ENUM** (`from_json::<T>` for
  collection-typed or enum-typed fields). Pairs with the
  encode-side gaps above. v5.39.5 should bundle the
  encode and decode sides per shape so the round-trip stays
  testable.

- **Round-trip equality test infrastructure.** v5.39.4 ships
  encode + decode for nested structs separately. A
  comprehensive round-trip test
  (`assert from_json::<T>(to_json::<T>(t)) == t`) requires
  `==` on user-defined structs, which Mapanare does not
  expose at the surface level. v5.39.5+ may consider
  surfacing struct equality (via a derive-like attribute or a
  built-in `__eq__`); until then the round-trip test
  inspects field-by-field via accessors.

- **Self-host mirror.** Phase 0 grep verified the typed-serde
  surface is Python-bootstrap-only at v5.39.3 HEAD. Same
  expectation for v5.39.4. If verified, STRICT preserved by
  construction.

## Hard prerequisite

v5.39.3 shipped (Js.4.C closed for STRUCT encoding); the
shared `_emit_struct_json_body` helper exists at
`mapanare/lower.py:2589-2636`. v5.39.4 builds on the same
helper for Js.4.D.2's decode-side mirror.

## Phase plan

### Phase 0 — pre-flight + repro (~20 min)

```bash
cd /mnt/c/Users/Juan/Documents/GitHub/Mapanare
cat VERSION                                          # expected: 5.39.3
git status --short                                   # expected: clean
make ci-gates 2>&1 | tail -5                         # expected: GREEN
bash scripts/verify_fixed_point.sh 2>&1 | tail -3    # expected: STRICT
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 | tail -3
                                                     # expected: 95/95
python3 -m pytest tests/stdlib/test_struct_json_runtime.py \
                  tests/stdlib/test_struct_json_ir_shape.py \
                  tests/stdlib/test_struct_json_layout.py \
                  tests/stdlib/test_struct_json.py
                                                     # expected: 26 passed, 1 xfailed
```

Confirm both repros — see Js.4.D.1 and Js.4.D.2 sections above.

Self-host mirror grep:

```bash
grep -rn "from_json\|decode_to\|encode_struct\|to_json" mapanare/self/
                                                     # expected: 0 matches
```

### Phase 1 — diagnosis confirmation + invariant audits (~45 min)

For Js.4.D.1: read `_encode_field_to_json` confirm STRUCT
branch from v5.39.3 is intact, LIST falls through. Sketch the
loop MIR — confirm it fits in ~50 LOC.

For Js.4.D.2: read `_decode_json_field` (~`lower.py:3002`).
Confirm:
- Field lookup is by name (string key in Map<String, JsonValue>),
  not by position. **If positional, escalate scope** — that's a
  separate v5.x bug that has to be fixed before nested-struct
  decode is meaningful.
- Constructor invocation pattern: how does `_lower_decode_to`
  build the struct value from extracted fields? Mirror that
  for the new helper.

Look for an existing `_lower_decode_to` body to extract from,
analogous to v5.39.3's `_emit_struct_json_body` extraction
from `_lower_encode_struct`. If the body is too tangled with
its calling context, fall back to inline duplication.

### Phase 2 — apply fixes (~2-3h)

Order:

1. **Js.4.D.1 first.** LIST encode is a self-contained addition
   to the existing dispatch table. Doesn't touch decode side.
   Lower risk; quick to verify.
2. **Js.4.D.2 second.** Decode-side struct recursion. Builds
   on v5.39.3's encode-side extraction precedent.

After each fix, verify the repro and run the full JSON test
suite. Don't move to the second fix if the first regresses
existing cases.

### Phase 3 — self-host mirror verify (~5 min, expected N/A)

Same as v5.39.3. Expected 0 matches → STRICT preserved by
construction.

### Phase 4 — extend regression suite (~45 min)

Two new `.mn` test files under
`stdlib/encoding/json/tests/`:

1. **`test_to_json_list_field.mn`** (Js.4.D.1)
   — `struct Bag { name: String, items: List<Int> }` →
   `to_json::<Bag>` → contains-substring assertions for
   `[1, 2, 3]` and `"name": "box"`. Mirror v5.39.3's
   `test_to_json_nested_struct.mn` shape.

2. **`test_from_json_nested_struct.mn`** (Js.4.D.2)
   — same `struct Inner { x: Int, y: String }` /
   `struct Wrap { name: String, inner: Inner }` as v5.39.3.
   Decode `{"name": "ok", "inner": {"x": 42, "y": "hi"}}`.
   Assert `w.name == "ok"`, `w.inner.x == 42`,
   `w.inner.y == "hi"`. Failure modes: decode error → FAIL
   with the JsonError.message; field mismatch → FAIL with
   the specific field.

3. **(Optional but recommended)** `test_to_from_nested_roundtrip.mn`
   — chains v5.39.3 encode + v5.39.4 decode:
   `let w2 = from_json::<Wrap>(to_json::<Wrap>(w1)).unwrap()`
   then field-by-field compare. This is the load-bearing
   round-trip test the manifesto-arc work has been waiting
   for. Failure here is the most actionable diagnostic
   (encode-decode disagreement → which side is wrong is
   evident from the field that mismatches).

Append all three to `tests/stdlib/test_struct_json_runtime.py
::TEST_FILES`. Run pytest, expect 9/9 (or 10/10 with the
roundtrip case) GREEN.

Falsifiability:

- For Js.4.D.1: revert the LIST branch in
  `_encode_field_to_json` → `test_to_json_list_field.mn` fails
  with the `<?>` placeholder substring check.
- For Js.4.D.2: revert the STRUCT branch in
  `_decode_json_field` → `test_from_json_nested_struct.mn`
  fails on the inner-field assertion (or with a JsonError).

### Phase 5 — bump + closeout (~45 min)

```bash
python3 scripts/bump_version.py 5.39.4
$EDITOR CHANGELOG.md       # ### Fixed: LIST encode + struct decode
$EDITOR CLAUDE.md          # release-notes entry
$EDITOR docs/roadmap/v5/v5.39.4/SESSION_REPORT.md
$EDITOR docs/SPEC.md       # Hd-class header re-sync
python3 scripts/check_doc_freshness.py
python3 scripts/check_changelog_honesty.py
make build-rt              # rebuilds with new MAPANARE_VERSION
python3 scripts/build_stage1.py
bash scripts/verify_fixed_point.sh   # STRICT — load-bearing
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
make ci-gates && make lint
python3 -m pytest tests/stdlib/test_struct_json_runtime.py \
                  tests/stdlib/test_struct_json_ir_shape.py \
                  tests/stdlib/test_struct_json_layout.py \
                  tests/stdlib/test_struct_json.py
```

Commit (no tag — tag is the lead's call). GitNexus index
refresh (`npx gitnexus analyze --embeddings`).

## Success criteria

- [ ] **Js.4.D.1**: `to_json::<T>` for a struct with a
      `List<X>` field produces a real JSON array; pre-fix
      reproduces `<?>` substring; post-fix passes
      `test_to_json_list_field.mn`.
- [ ] **Js.4.D.2**: `from_json::<T>` for a struct with a
      struct-typed field constructs the inner struct
      correctly; pre-fix reproduces decode error;
      post-fix passes `test_from_json_nested_struct.mn`.
- [ ] **Round-trip**: `from_json::<Wrap>(to_json::<Wrap>(w))`
      reconstructs `w` field-by-field
      (`test_to_from_nested_roundtrip.mn`).
- [ ] STRICT 3-stage fixed point preserved at 241,898 lines /
      0 diff (38-release strict streak).
- [ ] Goldens 95/95.
- [ ] All v5.39.1+v5.39.2+v5.39.3 JSON tests still GREEN.
- [ ] Falsifiability locked for both new fixes.
- [ ] CHANGELOG / SPEC / CLAUDE.md / SESSION_REPORT.md
      complete.
- [ ] `check_doc_freshness.py` + `check_changelog_honesty.py`
      GREEN.

## Estimated session cost

**~150-200 LOC compiler edit** (LIST encode ~50 + struct decode
~80 + helper extractions ~50) **+ ~120 LOC tests** (3 new
`.mn` files + TEST_FILES updates) + closeout artifacts.

**~3-4 hours total**. Larger than v5.39.3 but smaller than
v5.39.2 (which had GDB-driven runtime SEGV diagnosis).

## What this unblocks

After v5.39.4 ships, the typed-serde surface
(`to_json::<T>` ↔ `from_json::<T>`) round-trips cleanly for
nested-struct shapes. v5.40.0 Ai.\* (`ask_typed::<T>`) can rely
on this round-trip for any user-defined struct whose fields are
primitive, optional-primitive, or nested-struct. List / Map /
Enum fields still hit the placeholder/decode-error path; users
of Ai.\* will know to keep their `ask_typed` shapes flat-or-
nested-struct until v5.39.5+ closes the rest.

## Aggregate state entering v5.39.5 (projected)

- **0 HIGH** if Js.4.D.1 + Js.4.D.2 ship clean.
- **1 MEDIUM:** macOS notarization (carry from v5.33.0 Nu.2).
- **~6 LOW:** to_json LIST/MAP/ENUM held for v5.39.5 (bumped
  from "candidates" to scoped LOW once v5.39.4 PLAN locks);
  from_json LIST/MAP/ENUM held; round-trip equality test
  infrastructure; native `Bytes` type carry; rest unchanged.
