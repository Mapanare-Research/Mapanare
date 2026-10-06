# v5.39.5 — PLAN — typed-serde LIST decode (round-trip closure for List-typed fields)

> **Final session in the Js.4.D.\* arc** before v5.40.0 manifesto
> kickoff. v5.39.4 closed nested-struct decode (Js.4.D.2) and
> LIST encode (Js.4.D.1) but **deferred the symmetric LIST decode
> branch** in `_decode_json_field`, so the round-trip
> `to_json::<T>` ↔ `from_json::<T>` does not yet close for
> structs with `List<T>` fields. v5.39.5 closes that hole. Adds
> **zero language features, zero new MIR ops, zero new IR
> shapes, zero new C runtime exports**. Bundle scope locked:
> **LIST decode only**. MAP encoding (string-key invariant
> question), ENUM encoding (tagged-union shape question), and
> MAP/ENUM decoding all remain held — each deserves its own
> Phase 0 invariant audit, but **none are load-bearing for
> v5.40.0 Ai.\*** (LLM JSON responses overwhelmingly use struct +
> string + int + float + bool + nested-struct + list — MAP and
> ENUM are < 5% of the corpus). v5.40.0 unblocks after v5.39.5
> ships.

## Why this is the last v5.39.x

After v5.39.5, the typed-serde round-trip is **load-bearing
complete** for the shapes v5.40.0 Ai.\* (`ask_typed::<T>`)
actually returns from LLM providers:

- ✓ Primitive-field structs (v5.39.2)
- ✓ Multi-field mixed-type structs (v5.39.2)
- ✓ Nested-struct fields encode (v5.39.3) + decode (v5.39.4)
- ✓ `List<Primitive>` and `List<Struct>` encode (v5.39.4)
- ✓ `List<Primitive>` and `List<Struct>` decode (v5.39.5 — this release)
- ⊘ Map-typed fields (deferred — has invariant question; rare in LLM JSON)
- ⊘ Enum-typed fields (deferred — has tagged-union shape question; rare in LLM JSON)
- ⊘ Nested `Map<...>` and `Enum<...>` decoding (paired with above)

The deferred shapes don't appear in the v5.40.0 PROMPT's
`ask_typed::<T>` examples, so v5.40.0 can ship without them.
Each is a v5.40.x or v5.41+ candidate when motivated by a real
caller.

## Scope

**One bug-class fix, one code path, one release.** Mirror of
v5.39.4 Js.4.D.1's encode loop, applied to the decode side.
Estimated session cost: ~80-100 LOC compiler edit + ~50 LOC
tests. Plan 2-3 hours.

### Js.4.D.3 — `from_json::<T>` LIST nested decoding

**Bug.** `from_json::<T>(s)` for a struct with a `List<X>`
field falls into the `_decode_json_field` raw-jval fallback,
returning the JsonValue Array enum where the consumer expects
a `List<X>` value — silent shape mismatch surfaced as wrong
list contents (or a downstream segfault when the consumer
treats the enum payload as a list pointer).

Repro at v5.39.5 HEAD:

```mn
struct Bag { items: List<Int> }
fn main() -> Int {
    pon s: String = "{\"items\": [1, 2, 3]}"
    pon r: Result<Bag, JsonError> = from_json::<Bag>(s)
    match r {
        Ok(b) => print(str(len(b.items))),  // expected: 3
        Err(e) => print("FAIL"),
    }
    return 0
}
```

Actual: prints `0` or segfaults; round-trip via
`test_to_from_nested_roundtrip.mn` (which has `ints: List<Int>`)
fails on the list-equality check post-decode.

**Root cause.** `mapanare/lower.py:3019::_decode_json_field` has
explicit handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
(the latter from v5.39.4) but no branch for `TypeKind.LIST`. The
fallback returns the raw JsonValue.

**Fix shape.** Add a `TypeKind.LIST` branch that:

1. Asserts/extracts the JsonValue's `Array` variant payload to
   get the `List<JsonValue>` (call it `arr`).
2. Allocates an empty `mut acc: List<X> = []` (where `X` is the
   declared inner type).
3. Loops `i = 0..len(arr)`:
   - `IndexGet` the JsonValue at `arr[i]`.
   - Recursively calls `_decode_json_field(elem_jval, inner_type)`.
   - Pushes the converted value onto `acc`.
4. Returns `acc`.

Need a new `_emit_list_decode_body(arr_val, inner_type) -> Value`
helper. Mirror the v5.39.4 `_emit_list_json_body` helper's
mutable-Phi loop pattern — counter + accumulator phis at the
header, body branches between first / rest sep handling.

**MIR sketch (~80 LOC):**

```python
def _emit_list_decode_body(self, arr_val: Value, inner_type: MIRType) -> Value:
    """Emit MIR converting JsonValue::Array(List<JsonValue>) to List<inner>.

    Mirror of v5.39.4 Js.4.D.1's _emit_list_json_body shape but on the
    decode side: extract the inner List<JsonValue> from the Array variant,
    iterate, recursively decode each element, accumulate into typed list.
    """
    assert self._block is not None
    entry_label = self._block.label
    list_ty = MIRType(TypeInfo(kind=TypeKind.LIST, args=[inner_type.type_info]))

    # Extract inner List<JsonValue> from Array variant
    inner_arr = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
    self._emit(EnumPayload(dest=inner_arr, enum_val=arr_val, variant="Array", payload_idx=0))

    # Initialize accumulator
    acc_init = self._make_value(ty=list_ty)
    self._emit(ListInit(dest=acc_init, elem_type=inner_type, elements=[]))

    # len(inner_arr)
    len_val = self._make_value(ty=mir_int())
    self._emit(Call(dest=len_val, fn_name="len", args=[inner_arr]))

    zero = self._make_value(ty=mir_int())
    self._emit(Const(dest=zero, ty=mir_int(), value=0))

    header_bb = self._new_block(self._fresh_block("list_dec_header"))
    body_bb = self._new_block(self._fresh_block("list_dec_body"))
    exit_bb = self._new_block(self._fresh_block("list_dec_exit"))
    self._emit(Jump(target=header_bb.label))

    # Header: phi counter + acc; cmp; branch
    self._set_block(header_bb)
    counter_phi_dest = self._make_value(ty=mir_int())
    counter_phi = Phi(dest=counter_phi_dest, incoming=[])
    self._emit(counter_phi)
    acc_phi_dest = self._make_value(ty=list_ty)
    acc_phi = Phi(dest=acc_phi_dest, incoming=[])
    self._emit(acc_phi)
    cmp = self._make_value(ty=mir_bool())
    self._emit(BinOp(dest=cmp, op=BinOpKind.LT, lhs=counter_phi_dest, rhs=len_val))
    self._emit(Branch(cond=cmp, true_block=body_bb.label, false_block=exit_bb.label))

    # Body: extract elem JsonValue, recurse-decode, push
    self._set_block(body_bb)
    elem_jval = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.ENUM, name="JsonValue")))
    self._emit(IndexGet(dest=elem_jval, obj=inner_arr, index=counter_phi_dest))
    decoded = self._decode_json_field(elem_jval, inner_type)

    new_acc = Value(name=acc_phi_dest.name, ty=list_ty)  # in-place push pattern
    self._emit(ListPush(dest=new_acc, list_val=acc_phi_dest, element=decoded))
    self._emit(Move(value=decoded))

    one = self._make_value(ty=mir_int())
    self._emit(Const(dest=one, ty=mir_int(), value=1))
    new_counter = self._make_value(ty=mir_int())
    self._emit(BinOp(dest=new_counter, op=BinOpKind.ADD, lhs=counter_phi_dest, rhs=one))

    body_exit_label = self._block.label
    self._emit(Jump(target=header_bb.label))

    counter_phi.incoming = [(entry_label, zero), (body_exit_label, new_counter)]
    acc_phi.incoming = [(entry_label, acc_init), (body_exit_label, new_acc)]

    self._set_block(exit_bb)
    return acc_phi_dest
```

**Caveat: in-place push pattern.** v5.39.4's encode loop used
string accumulator phis cleanly because string concat is
functional. List push is in-place: `ListPush` mutates the list
buffer. The `new_acc = Value(name=acc_phi_dest.name, ty=list_ty)`
trick mirrors `_lower_method_call`'s `.push()` pattern at
`mapanare/lower.py:3144` — same SSA name reused so the emitter
sees a single list slot. **Phase 1 audit must verify this works
across the loop boundary** — if the SSA renaming + phi
predecessor matching breaks, fall back to `Copy`-then-`ListPush`
on each iteration (slower, but correct).

**Plug-in point.** In `_decode_json_field`, add immediately
before the fallback `return jval`:

```python
if kind == TypeKind.LIST:
    inner_type = (
        MIRType(target_type.type_info.args[0])
        if target_type.type_info.args
        else mir_unknown()
    )
    return self._emit_list_decode_body(jval, inner_type)
```

## Out of scope (deferred to v5.39.6+ / v5.40.x)

| Item | Why deferred | Open question |
|---|---|---|
| MAP encode | LLM JSON rarely has Map fields | String-key invariant: reject? coerce ints? runtime-error on non-string keys? |
| ENUM encode | LLM JSON rarely has Enum fields | Tagged-union shape: `"VariantName"` vs `{"Variant": payload}` vs `{"tag": ..., "payload": ...}`? |
| MAP decode | Paired with MAP encode | Same as encode |
| ENUM decode | Paired with ENUM encode | Same as encode |

Each carries forward as a LOW into v5.39.6+. None block v5.40.0.

## Phases

### Phase 0 — pre-flight + repro (~15 min)

- Confirm VERSION=5.39.4, ci-gates GREEN, fixed point STRICT
- Confirm goldens 95/95
- Confirm JSON suite 29 passed + 1 xfailed at HEAD
- Capture pre-fix repro for `Bag { items: List<Int> }` decode
- Self-host grep for `from_json|decode_to|encode_struct|to_json`
  in `mapanare/self/` — expect 0 matches → mirror N/A

### Phase 1 — diagnosis + caveat audit (~30 min)

- Re-read `_decode_json_field`; confirm v5.39.4 STRUCT branch intact
- Verify `JsonValue::Array(List<JsonValue>)` ABI: confirm `EnumPayload(variant="Array", payload_idx=0)` returns `List<JsonValue>` shape
- Audit the in-place ListPush-in-loop pattern: read
  `mapanare/lower.py:3144::_lower_method_call .push() handling` and
  the `for` loop's `_list_push_vars` tracking at line 1701.
  Decide: in-place vs Copy-then-push.
- Sketch the LIST decode loop MIR; confirm ~80 LOC budget holds.

### Phase 2 — apply fix (~1.5h)

- Add `_emit_list_decode_body` helper (~80 LOC)
- Add `TypeKind.LIST` branch in `_decode_json_field` (~10 LOC)
- Verify with `/tmp/fromjson_list.mn` standalone repro
- Verify with `test_to_from_nested_roundtrip.mn` — the `ints: List<Int>`
  field should now round-trip with full equality (currently
  passes only because the assertion doesn't check `ints`)

### Phase 3 — self-host mirror verify (~5 min, expected N/A)

```bash
grep -rn "from_json\|decode_to\|encode_struct\|to_json" mapanare/self/
```

Expected 0 matches → STRICT preserved by construction.

### Phase 4 — extend regression suite (~30 min)

Two new `.mn` test files under `stdlib/encoding/json/tests/`:

1. `test_from_json_list_field.mn` — Js.4.D.3 single-direction:
   - Decode `{"items": [1, 2, 3]}` → assert `len(b.items) == 3`,
     `b.items[0] == 1`, `b.items[2] == 3`.
   - Edge: empty list `{"items": []}` → assert `len(b.items) == 0`.
   - Edge: list of strings `{"tags": ["a", "b"]}` → assert
     `b.tags[1] == "b"`.

2. **Strengthen** `test_to_from_nested_roundtrip.mn` to also
   check `decoded.inner.ints[0] == 10 && decoded.inner.ints[2] == 30`
   — currently the v5.39.4 test only asserts outer fields and
   inner.x/y; once Js.4.D.3 lands, the full embedded list also
   round-trips.

Falsifiability: revert the LIST decode branch → `test_from_json_list_field.mn`
fails on the length / element check; reapply → passes.

### Phase 5 — bump + closeout (~30 min)

Same shape as v5.39.4:

- `bump_version.py 5.39.5`
- CHANGELOG `### Fixed` entry — be explicit that this is the
  symmetric pair to v5.39.4 Js.4.D.1; bundle scope locked LIST
  only; MAP/ENUM still held with the open invariant questions
- CLAUDE.md release-notes entry
- SPEC.md sync block re-bumped to "v5.39.5 cut"
- `check_doc_freshness.py` + `check_changelog_honesty.py` GREEN
- `make build-rt` → `python3 scripts/build_stage1.py` →
  `bash scripts/verify_fixed_point.sh` (STRICT preserved)
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  (95/95)
- `make ci-gates` GREEN; `make lint` clean
- JSON tests: 31 passed + 1 xfailed (was 29+1; +2 new)
- `gitnexus_detect_changes` matches expected scope

## Risk

**Low-to-medium.** The encode-side mirror was straightforward;
the decode side has the in-place ListPush caveat. If Phase 1
audit determines the in-place pattern doesn't survive the loop
boundary, the Copy-then-push fallback adds ~10 LOC and runtime
cost but doesn't change the surface contract.

**Falsifiability anchor:** revert-and-restore round-trip on the
new test case is the load-bearing verification.

## Aggregate state entering v5.40.0

After v5.39.5:

- **0 HIGH** — typed-serde round-trip closed for the v5.40.0
  Ai.\* call shapes
- **1 MEDIUM** — macOS notarization (carry from v5.33.0 Nu.2,
  unchanged across the v5.39.x arc)
- **~10 LOW** — MAP encode/decode (paired with invariant
  decision), ENUM encode/decode (paired with shape decision),
  plus prior carries

**Js.4.\* arc CLOSED for v5.40.0 dependencies.** Manifesto-arc
kickoff (v5.40.0 Ai.\* — `ask`/`ask_typed::<T>`) unblocked for
all common LLM response shapes.
