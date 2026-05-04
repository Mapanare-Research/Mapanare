# v5.39.7 — PLAN — typed-serde ENUM encode + decode (v5.39.x arc CLOSEOUT)

> **Js.4.F.\* — ENUM-typed field round-trip closure.** **Final
> release in the v5.39.x typed-serde arc.** Closes the last
> remaining shape (tagged unions / enum variants) so v5.40.0
> Ai.\* manifesto kickoff has full typed-serde coverage. Adds
> **zero language features, zero new MIR ops, zero new IR shapes,
> zero new C runtime exports**.

## Invariant decision (locked at PLAN — externally tagged)

**Tagged-union shape: `{"Variant": payload}`** (externally
tagged, the most common JSON convention).

Three shapes were on the table:

1. **Externally tagged: `{"VariantName": payload}`** ✓ — chosen.
   Most common in JSON RPC, most LLM frameworks, OpenAI function-
   calling examples; round-trips trivially; no payload wrapper
   needed.
2. Internally tagged: `{"tag": "VariantName", "field1": ...}` —
   collides with payload field names (`tag` reserved); only works
   for struct-payload variants.
3. Adjacently tagged: `{"tag": "VariantName", "payload": ...}` —
   verbose, two-level nesting; better for streaming protocols not
   JSON-as-config.

**Special cases:**

- **No-payload variants** (e.g., `Color::Red` from `enum Color
  { Red, Green, Blue }`) encode as the bare string `"Red"` (not
  `{"Red": null}`) — matches Rust serde's `untagged()` for unit
  variants and is what most LLMs produce.
- **Single-payload variants** (e.g., `Some(42)` from
  `Option<Int>`) — already handled by v5.39.3's OPTION branch
  (Some → bare value; None → `null`); v5.39.7 does NOT touch
  the OPTION case.
- **Result<T, E>** — already handled by `_lower_decode_to`'s
  Object-tag check; ENUM branch should NOT match Result either.
- **`JsonValue` itself** — recursive case; already handled via
  `_ensure_json_types_registered` — ENUM branch should detect
  and pass through.

The branch checks `enum_name not in {"Option", "Result", "JsonValue"}`
before applying the tagged-union shape.

## Scope

**Two bug-class fixes, two code paths, one release.** Mirror of
v5.39.4 + v5.39.5 + v5.39.6 patterns. Estimated session cost:
~180 LOC compiler + ~80 LOC tests. 4 hours (slightly larger than
MAP because the per-variant dispatch needs a Switch instead of a
linear loop).

### Js.4.F.1 — `to_json::<T>` ENUM encode

**Bug.** `to_json::<T>(t)` for a struct with an enum-typed field
falls into the `str()` fallback, emitting `<?>`.

**Fix shape.** Add `TypeKind.ENUM` branch in
`_encode_field_to_json` with the special-case skip list:

```python
if kind == TypeKind.ENUM:
    enum_name = ftype.type_info.name if ftype.type_info else ""
    if enum_name in {"Option", "Result", "JsonValue"}:
        # OPTION handled above; Result/JsonValue intentionally fall
        # through to the str() fallback (round-trip is undefined for
        # raw Result/JsonValue fields — user should unwrap first).
        pass  # falls through to str() fallback
    elif enum_name and enum_name in self._module.enums:
        return self._emit_enum_json_body(field_val, enum_name)
```

`_emit_enum_json_body(enum_val, enum_name) -> Value` helper
(~100 LOC):

1. Get `tag = EnumTag(enum_val)`.
2. Look up variants from `self._module.enums[enum_name]` →
   `[(variant_name, [payload_types])]`.
3. Switch on tag with one case per variant → branches to
   per-variant emitter blocks → merge to result phi.
4. Per-variant block:
   - **No payload:** result = `"\"VariantName\""` (bare string)
   - **Single payload:** result = `"{\"VariantName\": " + encoded_payload + "}"`
   - **Multiple payloads:** result = `"{\"VariantName\": [" + p0 + ", " + p1 + ", ...]}"`
     (payload tuple → JSON array; matches the encode-positional
     decode-positional symmetry)
5. Default case (unrecognized tag, shouldn't happen at runtime):
   emit `"\"<UNKNOWN>\""` placeholder.

### Js.4.F.2 — `from_json::<T>` ENUM decode

**Bug.** `from_json::<T>` for an enum-typed field falls into the
raw-jval fallback.

**Fix shape.** Add `TypeKind.ENUM` branch in `_decode_json_field`
with the same special-case skip list:

```python
if kind == TypeKind.ENUM:
    enum_name = target_type.type_info.name if target_type.type_info else ""
    if enum_name in {"Option", "Result", "JsonValue"}:
        pass  # OPTION handled above; Result/JsonValue fall through
    elif enum_name and enum_name in self._module.enums:
        return self._emit_enum_decode_body(jval, enum_name)
```

`_emit_enum_decode_body(jval, enum_name) -> Value` helper
(~120 LOC):

1. Switch on `EnumTag(jval)`:
   - `"Str"` (bare string variant — no-payload case):
     `EnumPayload(variant="Str", 0)` → string; switch on string
     value to construct the right variant.
   - `"Object"` (tagged-union with payload): extract entries map,
     iterate to find which variant key is present, decode payload
     accordingly.
   - default: error case (unrecognized JSON shape for enum) —
     same no-tag-check-no-error pattern as v5.39.4 STRUCT decode
     (return zero-init enum).
2. For each candidate variant, build the EnumInit with decoded
   payload(s) (positional list-decode for multi-payload variants).

This is the most complex decoder so far because the JSON
structure can be either `"VariantName"` (string) or
`{"VariantName": payload}` (object), and the variant name is
extracted at runtime — needs a string-comparison cascade or
hash-based dispatch. PLAN's MIR sketch: a linear cascade of
`if json_str == "Variant1" { EnumInit Variant1 } else if ...`
is correct and fast enough for typical enums (< 20 variants).

## Out of scope

- Internally tagged shape (`{"tag": ..., "field": ...}`)
- Adjacently tagged shape (`{"tag": ..., "payload": ...}`)
- Custom serde attributes (e.g., `#[serde(rename = "...")]`)
- Hash-dispatched decode (linear cascade is fine; revisit if
  benchmarks show need)

## Phases

Same shape as v5.39.6:

- Phase 0 (~15min): pre-flight + repros
- Phase 1 (~45min): variant dispatch sketch; payload-shape
  decision audit; in-place IndexGet/EnumPayload caveat audit
- Phase 2 (~2.5h): apply both fixes; ENUM is bigger than MAP
  because of multi-variant dispatch
- Phase 3 (~5min): self-host grep 0 matches → STRICT preserved
- Phase 4 (~30min): 3 new `.mn` tests:
  - `test_to_json_enum_field.mn` — encode no-payload, single,
    multi
  - `test_from_json_enum_field.mn` — decode all three shapes
  - `test_to_from_enum_roundtrip.mn` — load-bearing round-trip
- Phase 5 (~30min): bump 5.39.7, **explicit "v5.39.x arc CLOSED"
  framing in CHANGELOG + CLAUDE.md release notes**, full closeout

## Risk

**Medium-to-high.** ENUM is the most complex of the four typed-
serde shapes. Three sources of risk:

1. **Multi-variant dispatch** — Switch lowering for the encode
   side, string-cascade for the decode side. Both patterns exist
   in the codebase but the decode-side cascade is novel for the
   typed-serde path.
2. **Special-case skip list correctness** — must NOT match Option
   (handled separately), Result (parent context), or JsonValue
   (recursive). If the skip list misses a case, we get either an
   infinite recursion or a wrong-shape encode/decode.
3. **Payload type recursion** — multi-payload variants need
   positional list-decode; reuses v5.39.5's `_emit_list_decode_body`
   with a synthetic JSON array payload. Phase 1 must verify this
   composes cleanly.

If any of the three blocks: split ENUM encode and decode across
v5.39.7 + v5.39.8. **Document the split explicitly in
SESSION_REPORT** — better to ship a working subset than a buggy
bundle.

## Aggregate state entering v5.40.0

After v5.39.7:

- **0 HIGH**
- **1 MEDIUM** — macOS notarization (carry, unchanged across
  the entire v5.39.x arc)
- **~5 LOW** — typed-serde extensions (custom rename attributes,
  internally/adjacently tagged shapes, hash dispatch), prior
  carries

**Js.4.\* arc CLOSED.** Typed-serde round-trip works for every
shape v5.40.0 Ai.\* (`ask_typed::<T>`) returns:

- ✓ Primitives (v5.39.2)
- ✓ Multi-field structs (v5.39.2)
- ✓ Nested struct encode + decode (v5.39.3 + v5.39.4)
- ✓ List<X> encode + decode (v5.39.4 + v5.39.5)
- ✓ Map<String, V> encode + decode (v5.39.6)
- ✓ Enum / tagged union encode + decode (v5.39.7 — this release)

**Manifesto-arc kickoff (v5.40.0 Ai.\* — `ask` /
`ask_typed::<T>`) fully unblocked.**
