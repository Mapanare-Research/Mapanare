# v5.39.6 — SESSION REPORT — typed-serde MAP encode + decode

**Status:** ready, not tagged.
**Scope:** Js.4.E.1 + Js.4.E.2 — close the MAP-typed field
round-trip gap. Bundles encode + decode in one release.

## Summary

Two compiler-side fixes in `mapanare/lower.py`, two helpers, two
new branches. Adds **zero language features, zero new MIR ops,
zero new IR shapes, zero new C runtime exports**. Strict 3-stage
fixed point preserved by construction at v5.39.5's **241,898
lines / 0 diff** (40-release strict streak from v5.7.1; zero
`mapanare/self/*.mn` source touches). Goldens **95/95**.
Regression suite **15/15** GREEN (was 11 at v5.39.5; +2 runtime
MAP cases + 2 parametrized rejection cases).

## Phases

### Phase 0 — pre-flight + repros (~10 min)

- `cat VERSION` → `5.39.5` ✓
- `pytest tests/stdlib/test_struct_json_runtime.py -q` → 11
  passed at HEAD ✓
- `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` → **0 matches** → mirror N/A by construction
- Encode repro `/tmp/tojson_map.mn`
  (`struct Bag { lookup: Map<String, Int> }`, two-entry map):
  pre-fix output `{"name": "box", "lookup": <?>}`. Confirmed.
- Decode repro `/tmp/fromjson_map.mn` (decode `Map<String, Int>`
  field): pre-fix exit code -11 (SEGV). Confirmed.

### Phase 1 — runtime + IndexSet audit (~15 min)

- `__mn_map_keys` exists at `runtime/native/mapanare_core.c:2441`,
  returns `MnList` (`List<String>`).
- `__mn_map_get` exists at `:2332`, `__mn_map_set` at `:2244`.
- **Map LLVM-IR representation: `PTR`** (single pointer), per
  `mapanare/emit_llvm_text.py::_rty` line 988
  (`if k == TypeKind.MAP: return PTR`).
- `IndexSet` on a Map calls `__mn_map_set(map_ptr, key_ptr,
  val_ptr)` at `_do_idx_set` line 4955 — **mutates bucket array
  in place; outer `MnMap*` pointer is invariant across
  iterations.**
- **Decision: no SSA-name-reuse trick required.** Unlike
  v5.39.5's LIST decode, where `ListPush` could grow the buffer
  and required reusing the phi alloca's name, MAP decode can use
  a single counter phi with the accumulator initialized once
  before the loop and IndexSet'd inside. Simpler than the LIST
  case.
- Auto-declaration of unknown `__mn_*` calls works via
  `_do_call`'s fallthrough at `mapanare/emit_llvm_text.py:4313`
  (`self._decl_fn(fn, ret_auto, pts_auto)`).
- Compile-time error pattern: `raise RuntimeError(...)` —
  matches the existing pattern at `mapanare/lower.py:1464` /
  `:1576` / `:1636` / `:4343`.

### Phase 2 — apply both fixes (~1.5 h)

#### Js.4.E.1 — `to_json::<T>` MAP encode

`mapanare/lower.py::_encode_field_to_json` had explicit branches
for `STRING` / `INT` / `FLOAT` / `BOOL` / `OPTION` / `STRUCT`
(v5.39.3) / `LIST` (v5.39.4) but no branch for `TypeKind.MAP`.
The fallback `Call(fn_name="str", args=[field_val])` emitted the
literal `<?>` placeholder via `_mkstr("<?>")`.

**Fix:** new `TypeKind.MAP` branch with String-key invariant
check; new `_emit_map_json_body(map_val, val_type) -> Value`
helper.

```
entry: keys = __mn_map_keys(map); len_v = len(keys); zero=0
       init = "{"; jump header
header: counter = phi(zero, new_counter)
        result  = phi(init, new_result)
        cmp = counter < len_v
        branch cmp -> body, exit
body:   key       = keys[counter]
        val       = map[key]                ; IndexGet on Map
        quoted_k  = "\"" + key + "\""
        val_str   = _encode_field_to_json(val, val_type)
        pair      = quoted_k + ": " + val_str
        if counter == 0: result_after = result + pair
        else:            result_after = result + ", " + pair
        new_counter = counter + 1
        new_result  = result_after
        jump header
exit:   final = result + "}"; return final
```

Mirrors v5.39.4's `_emit_list_json_body` mutable-Phi loop
pattern. Recursion through `_encode_field_to_json` per value
handles nested `Map<String, Struct>` / `Map<String, List>` /
`Map<String, Map>` uniformly through the existing branches.

**Empty `#{}` case:** `__mn_map_keys` on an empty map returns
`len=0`, the loop never enters body, exit emits
`init + "}" = "{}"` — correct.

**Falsifiability:** post-fix encode repro prints
`{"name": "box", "lookup": {"b": 2, "a": 1}}` (key order may
vary per RFC 8259 §4 — JSON objects are unordered). Confirmed
with `/tmp/encode_repro.py`.

#### Js.4.E.2 — `from_json::<T>` MAP decode

`mapanare/lower.py::_decode_json_field` had explicit branches
for primitives + `OPTION` + `STRUCT` (v5.39.4) + `LIST`
(v5.39.5) but no branch for `TypeKind.MAP`. The fallback
`return jval` returned the raw `JsonValue::Object` enum where
the consumer expected the typed `Map<String, V>` shape — silent
shape mismatch surfaced as either wrong values or a SEGV in
`__mn_map_get` (the consumer treated unrelated bytes as a
`MnMap*`).

**Fix:** new `TypeKind.MAP` branch with String-key invariant
check; new `_emit_map_decode_body(jval, val_type) -> Value`
helper.

```
entry: inner_map = EnumPayload(jval, "Object", 0)
       acc       = MapInit(empty, key=String, val=V)
       keys      = __mn_map_keys(inner_map)
       len_v     = len(keys); zero=0; jump header
header: counter = phi(zero, new_counter)
        cmp = counter < len_v
        branch cmp -> body, exit
body:   key      = keys[counter]
        elem_jv  = inner_map[key]
        decoded  = _decode_json_field(elem_jv, val_type)
        acc[key] = decoded                  ; IndexSet (in-place)
        new_counter = counter + 1; jump header
exit:   return acc
```

**Single counter phi only.** No phi for `acc` because the
Mapanare Map value is a single ptr to a heap MnMap; `IndexSet`
lowers to `__mn_map_set` which mutates the bucket array in
place without changing the outer pointer. `acc` is invariant
across iterations.

**Empty-literal `#{}` accumulator** depends on v5.39.2's
`_do_map_init` empty-branch fix (pre-v5.39.2 this would have
SEGV'd because the empty-literal map had hardcoded `(ksz=8,
vsz=8, ktag=0)` regardless of declared `key_type`/`val_type`).

**Falsifiability:** post-fix decode repro prints `2`
(`len(b.lookup) == 2`); round-trip repro
(`/tmp/roundtrip_map.mn`) prints `ROUNDTRIP_OK` with
`b2.lookup["a"] == 1 && b2.lookup["b"] == 2`. Confirmed.

#### Invariant decision (locked at PLAN)

`Map<K, V>` fields with non-String K → compile-time error.
Diagnostic shape:
- `to_json: Map<K, V> requires K = String (got <KIND>)`
- `from_json: Map<K, V> requires K = String (got <KIND>)`

Rationale: JSON object keys are strings (RFC 8259 §4).
`Map<Int, X>` and `Map<Float, X>` have no canonical JSON
projection. Three options on the table:

1. ✅ **Reject at compile time** — chosen. Zero runtime cost;
   user gets diagnostic at the call site; forces explicit key
   conversion which is the right behavior for round-trip
   integrity.
2. Coerce via `str()` — silent lossy round-trip
   (`Map<Int, X>` → `{"42": ...}` → decode produces
   `Map<String, X>`). Asymmetric.
3. Runtime error on first non-String key — surfaced too late.

Confirmed via `/tmp/intkey_repro.py` against
`struct Bad { lookup: Map<Int, String> }`: post-fix raises
`RuntimeError: to_json: Map<K, V> requires K = String (got
INT)`.

### Phase 3 — self-host mirror N/A (~5 min)

`grep -rn "from_json\|decode_to\|encode_struct\|to_json"
mapanare/self/` returned **0 matches**. The Js.4 typed-serde
surface shipped Python-bootstrap-only at v5.36.0 and has not
been mirrored. STRICT preserved trivially by construction;
v5.39.6 makes zero `mapanare/self/*.mn` source touches.

### Phase 4 — regression suite (~25 min)

Two new `.mn` test files appended to `TEST_FILES` in
`tests/stdlib/test_struct_json_runtime.py`:

- `stdlib/encoding/json/tests/test_to_json_map_field.mn`
  (Js.4.E.1, ~80 LOC, 3 sub-cases wrapped in helpers per the
  v5.39.5 caveat about bare `from_json_merge` block labels):
    1. `Map<String, Int>` two entries — assert `contains("\"a\": 1")`
       AND `contains("\"b\": 2")` (key order unspecified).
    2. Empty map — assert `contains("\"lookup\": {}")`.
    3. `Map<String, String>` value-side recursion — assert
       `contains("\"greeting\": \"hello\"")`.
- `stdlib/encoding/json/tests/test_from_json_map_field.mn`
  (Js.4.E.2, ~80 LOC, 3 sub-cases mirroring encode-side):
    1. Decode `{"lookup": {"a": 1, "b": 2}}` → `len == 2`,
       `lookup["a"] == 1`, `lookup["b"] == 2`.
    2. Empty: `{"lookup": {}}` → `len == 0`.
    3. `Map<String, String>` two entries with string values.

Plus 2 parametrized rejection cases in
`test_typed_serde_map_nonstring_key_rejected`:
- `Map<Int, String>` to_json → `RuntimeError` matching
  `to_json: Map<K, V> requires K = String`.
- `Map<Float, Int>` from_json → `RuntimeError` matching
  `from_json: Map<K, V> requires K = String`.

**13 runtime tests + 2 rejection tests = 15/15 GREEN** (was 11
at v5.39.5; +4 total).

**Falsifiability locked.** Disabling either MAP branch in
`lower.py` (replacing the kind-check with `if False:`) makes
the corresponding `test_*_map_field.mn` test fail; reapplying
restores GREEN. Verified.

### Phase 5 — closeout

- `bump_version.py 5.39.6` — VERSION + 4 README badges +
  CHANGELOG scaffold.
- CHANGELOG `### Changed` (invariant note — potentially
  breaking-ish but no production user has exercised this path
  pre-fix) + `### Fixed` (Js.4.E.1 + Js.4.E.2 + Phase 1 audit
  decision).
- `docs/SPEC.md` header re-synced from "v5.39.5 cut" to
  "v5.39.6 cut" with a new sync block summarizing
  Js.4.E.1+Js.4.E.2 and the invariant decision.
- `make build-rt` — runtime archive rebuilt with
  `MAPANARE_VERSION="5.39.6"`.
- `python3 scripts/build_stage1.py` — stage1 rebuilt so IR
  metadata embeds `!"5.39.6"` (recurring lesson from v5.31.0 —
  without this, `verify_fixed_point.sh` would show a 4-line
  VERSION-placeholder NEAR diff).
- `bash scripts/verify_fixed_point.sh --keep` →
  **STRICT 241,898 / 0 diff**.
- `python3 scripts/test_native.py --stage1
  mapanare/self/mnc-stage1` → **95/95** in 16.8s.
- `make ci-gates` → all 9 sub-gates GREEN (changelog_honesty +
  workflow_shapes + docs_drift + hollow_features +
  struct_registry + doc_freshness + cadence (REMINDER
  informational only — 11 minor versions since v5.28.0 panel,
  no enforcement) + clean-build-test).
- `make lint` → black formatting applied (2 files); re-run
  clean.

## Source delta

| File | LOC change | Purpose |
|---|---:|---|
| `mapanare/lower.py` | +185 | Js.4.E.1 helper + branch (~95 LOC); Js.4.E.2 helper + branch (~90 LOC) |
| `tests/stdlib/test_struct_json_runtime.py` | +44 | 2 new TEST_FILES entries; 2 parametrized rejection cases |
| `stdlib/encoding/json/tests/test_to_json_map_field.mn` | +80 | Encode-side regression |
| `stdlib/encoding/json/tests/test_from_json_map_field.mn` | +80 | Decode-side regression |
| `CHANGELOG.md` | +120 | v5.39.6 entry (`### Changed` + `### Fixed`) |
| `docs/SPEC.md` | +35 | Header bump + sync block |
| `CLAUDE.md` | +1 entry | Release notes |
| `VERSION`, README badges (4) | mechanical | bump_version.py |
| `docs/roadmap/v5/v5.39.6/SESSION_REPORT.md` | this file | |

Total ~545 LOC across compiler + tests + docs. Compiler edit
(~185 LOC) is comfortably above PLAN's ~150-LOC estimate but
within scope (the encode helper + the decode helper each
mirror their LIST counterparts plus the String-key
invariant check).

## Aggregate state entering v5.39.7

- **0 HIGH** — Js.4.E.\* closed; typed-serde round-trip closes
  for `Map<String, V>`-typed fields end-to-end.
- **1 MEDIUM** — macOS notarization (carry from v5.33.0 Nu.2,
  unchanged).
- **~6 LOW** — ENUM encode/decode (the last typed-serde piece;
  scoped for v5.39.7 with the tagged-union shape decision —
  `"VariantName"` vs `{"Variant": payload}` vs
  `{"tag": ..., "payload": ...}`). Prior carries unchanged.

**Js.4.E.\* arc CLOSED.** ENUM is the last typed-serde piece
before v5.40.0 manifesto-arc kickoff.

## Lessons captured

1. **Map-pointer invariance simplifies decode-side accumulation.**
   When the underlying type lowers to a single ptr (vs. LIST's
   fat pointer), in-place mutation through that ptr does not
   require the SSA-name-reuse trick. The accumulator becomes a
   straight `MapInit` once before the loop with `IndexSet`
   inside.
2. **Phase 1 audit on `_rty(MAP) → PTR` was load-bearing.** Had
   the audit not surfaced this, the decode helper would have
   carried the v5.39.5 ListPush-style phi pattern unnecessarily
   and added 30 LOC of complexity for no correctness gain.
3. **The String-key invariant rationale is a one-line addition
   to the diagnostic.** "got KIND_NAME" gives the user enough
   information to fix the call site without reading docs.
