# v5.39.6 — PLAN — typed-serde MAP encode + decode (string-key only)

> **Js.4.E.\* — MAP-typed field round-trip closure.** Sibling
> release to v5.39.5 (LIST decode), now bundling **encode + decode
> in one release** because Map's invariant decision is simpler than
> LIST's was, and both halves are mechanical mirrors of the LIST
> patterns shipped at v5.39.4 + v5.39.5. Adds **zero language
> features, zero new MIR ops, zero new IR shapes, zero new C
> runtime exports**.

## Invariant decision (locked at PLAN — no Phase 0 audit needed)

**`Map<K, V>` fields with non-String K → compile-time error.**

JSON object keys are strings (RFC 8259 §4 — "An object is an
unordered set of name/value pairs ... The names within an object
SHOULD be unique"). Mapanare's `Map<Int, X>` and `Map<Float, X>`
have no canonical JSON projection. Three choices were on the
table:

1. **Reject at compile time** ✓ — chosen. Zero runtime cost; user
   gets the diagnostic at `to_json::<T>` / `from_json::<T>` call
   site; forces the user to convert keys explicitly
   (`map.entries().map(\|(k,v)\| (str(k), v))` or similar) which
   is the right behavior for round-trip integrity.
2. Coerce keys to strings via `str()` — silent lossy round-trip
   (`Map<Int, X>` → `{"42": ...}` → decode produces `Map<String, X>`,
   not the original type). User has to catch this themselves.
3. Runtime error on first non-String key — surfaced too late;
   useful only for `Map<Any, X>` which Mapanare doesn't have.

Choice 1 is enforced in `_encode_field_to_json` MAP branch + the
`_decode_json_field` MAP branch. Diagnostic: `"to_json/from_json:
Map<K, V> requires K = String (got <kind>)"`.

## Scope

**Two bug-class fixes, two code paths, one release.** Mirror of
v5.39.4 (LIST encode) + v5.39.5 (LIST decode), applied to MAP.
Estimated session cost: ~150 LOC compiler + ~60 LOC tests.
3-4 hours.

### Js.4.E.1 — `to_json::<T>` MAP encode

**Bug.** `to_json::<T>(t)` for a struct with a `Map<String, V>`
field falls into the `str()` fallback, emitting `<?>`.

**Fix shape.** Add `TypeKind.MAP` branch in
`_encode_field_to_json` (just before the existing `LIST`
branch from v5.39.4):

```python
if kind == TypeKind.MAP:
    args = ftype.type_info.args
    key_kind = args[0].kind if args else TypeKind.UNKNOWN
    if key_kind != TypeKind.STRING:
        raise SemanticError(
            f"to_json: Map<K, V> requires K = String (got {key_kind.name})"
        )
    val_type = MIRType(args[1]) if len(args) > 1 else mir_unknown()
    return self._emit_map_json_body(field_val, val_type)
```

`_emit_map_json_body(map_val, val_type) -> Value` helper
(~80 LOC):

1. Init `result = "{"`.
2. Get `entries = map_val.entries()` — returns `List<(String, V)>`.
   (Phase 1: confirm `__mn_map_entries` runtime export exists; if
   not, use the per-key iteration via `__mn_map_keys` + per-key
   `__mn_map_get`.)
3. Loop `i = 0..len(entries)`:
   - First iter: append `"key": ` then encoded value.
   - Rest: append `, "key": ` then encoded value.
   - Encoded value = `_encode_field_to_json(val, val_type)` —
     recurses through STRUCT / LIST / primitive uniformly.
4. Append `"}"`.

Mirror v5.39.4's `_emit_list_json_body` mutable-Phi loop pattern.

### Js.4.E.2 — `from_json::<T>` MAP decode

**Bug.** `from_json::<T>` for a Map-typed field falls into the
raw-jval fallback, returning JsonValue Object enum.

**Fix shape.** Add `TypeKind.MAP` branch in `_decode_json_field`
(just before the v5.39.5 LIST branch):

```python
if kind == TypeKind.MAP:
    args = target_type.type_info.args
    key_kind = args[0].kind if args else TypeKind.UNKNOWN
    if key_kind != TypeKind.STRING:
        raise SemanticError(
            f"from_json: Map<K, V> requires K = String (got {key_kind.name})"
        )
    val_type = MIRType(args[1]) if len(args) > 1 else mir_unknown()
    return self._emit_map_decode_body(jval, val_type)
```

`_emit_map_decode_body(jval, val_type) -> Value` helper
(~80 LOC):

1. Extract inner `Map<String, JsonValue>` from
   `EnumPayload(variant="Object", payload_idx=0)`.
2. Init empty `mut acc: Map<String, V> = #{}` (uses the v5.39.2
   `_do_map_init` fix — sizes derive from declared `key_type` /
   `val_type`).
3. Loop over inner map keys (use `__mn_map_keys` runtime export
   returning `List<String>`).
4. For each key: `IndexGet` JsonValue from inner map, recurse
   via `_decode_json_field`, `IndexSet acc[key] = decoded_val`.
5. Return `acc`.

**Same in-place caveat as v5.39.5 LIST decode** — IndexSet
mutates. Phase 1 audit: confirm IndexSet inside loop body
preserves the phi-name pattern across the back-edge.

## Out of scope

- Non-String key support (rejected by invariant decision)
- Map ordering (JSON objects are unordered per RFC; no guarantee)
- ENUM encode/decode (deferred to v5.39.7)

## Phases

Same shape as v5.39.5:

- Phase 0 (~15min): pre-flight + repros (encode `<?>` for
  `Map<String,Int>` field; decode produces empty/wrong map)
- Phase 1 (~30min): runtime export audit
  (`__mn_map_entries`/`__mn_map_keys` availability), in-place
  IndexSet caveat audit
- Phase 2 (~2h): apply both fixes; verify with isolated repros
- Phase 3 (~5min): self-host grep — expected 0 matches → STRICT
  preserved by construction
- Phase 4 (~30min): 2 new `.mn` tests
  (`test_to_json_map_field.mn`, `test_from_json_map_field.mn`)
  + add to TEST_FILES; expect 13/13 GREEN (was 11+1 at v5.39.5
  HEAD; +2)
- Phase 5 (~30min): bump 5.39.6, CHANGELOG, SPEC sync, build-rt,
  stage1, fixed-point STRICT, ci-gates, lint, commit

## Risk

**Medium.** Two unknowns:

1. `__mn_map_entries` availability — if missing, fall back to
   `__mn_map_keys` + per-key `__mn_map_get`. ~10 LOC heavier but
   correct.
2. In-place IndexSet across loop boundary — same audit shape as
   v5.39.5's ListPush caveat. Fallback: copy-then-set.

Both fallbacks add ~10 LOC and runtime cost; neither changes
the surface contract.

## Aggregate state entering v5.39.7

After v5.39.6:

- **0 HIGH**
- **1 MEDIUM** — macOS notarization (carry, unchanged)
- **~6 LOW** — ENUM encode/decode (v5.39.7), prior carries

The Js.4.E.\* arc closes the MAP gap. ENUM remains the last
typed-serde surface piece before v5.40.0.
