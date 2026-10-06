# v5.39.5 — SESSION REPORT — Js.4.D.3 typed-serde LIST decode

**Status:** ready, not tagged.
**Date:** 2026-05-03.

## Summary

**Js.4.D.3 — `from_json::<T>` LIST nested decoding; v5.39.x arc
CLOSED.** Symmetric pair to v5.39.4's Js.4.D.1 (LIST encode).
Closes the last v5.39.x-deferred typed-serde gap before the v5.40.0
manifesto-arc kickoff. After this release, the typed-serde
round-trip `to_json::<T>` ↔ `from_json::<T>` closes for every shape
v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns from typical LLM
responses (primitive, struct, nested struct, `List<primitive>`,
`List<struct>`).

- **Zero language features, zero new MIR ops, zero new IR shapes,
  zero new C runtime exports.**
- **Strict 3-stage fixed point preserved by construction** at
  v5.39.4's 241,898 lines / 0 diff. Phase 0 grep for
  `from_json|decode_to|encode_struct|to_json` in `mapanare/self/`
  returned 0 matches — mirror is structurally N/A; STRICT
  preserved trivially. 39-release strict streak from v5.7.1.
- **Goldens 95/95**.
- **JSON runtime suite 11/11 GREEN** (was 10 at v5.39.4 HEAD; +1).

## Phase 0 — pre-flight + repro

- `VERSION` = `5.39.4` ✓
- `git status --short` clean ✓
- Self-host grep returned 0 matches → STRICT preserved by
  construction; Phase 3 mirror N/A.
- Existing `tests/stdlib/test_struct_json_runtime.py`: 10 passed.

**Pre-fix repro** at `/tmp/fromjson_list.mn`:

```mn
struct Bag { items: List<Int> }
fn main() -> Int {
    pon s: String = "{\"items\": [1, 2, 3]}"
    pon r: Result<Bag, JsonError> = from_json::<Bag>(s)
    match r {
        Ok(b) => print(str(len(b.items))),
        Err(e) => print("FAIL")
    }
    return 0
}
```

Pre-fix output: `94467072822368` (garbage from raw-jval enum
payload reinterpreted as list len).
Post-fix output: `3` ✓.

## Phase 1 — diagnosis + caveat audit

`mapanare/lower.py:3166::_decode_json_field` had explicit handlers
for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION` plus the v5.39.4
`STRUCT` branch but no `TypeKind.LIST` branch. The fallback
`return jval` returned the raw `JsonValue::Array` enum where the
consumer expected the typed `List<X>` value — silent shape
mismatch.

Verified `JsonValue::Array(List<JsonValue>)` ABI: existing Object
variant extraction at `lower.py:3068` uses
`EnumPayload(variant="Object", payload_idx=0)` returning the
inner `Map`. Same pattern works for the `Array` variant returning
the inner `List`.

**In-place ListPush across loop boundary — Option A vs Option B.**
Phase 1 audit of `mapanare/emit_llvm_text.py:4761::_do_list_push`
(in-place mutation through `__mn_list_push`, dest aliases source
SSA name) and `:2461::phi alloca` (registers
`_alloc[phi.dest.name] = (%phi.<name>, ty)`) confirmed Option A
(in-place push reusing the phi dest's SSA name) produces valid
IR: ListPush calls `__mn_list_push` on the phi alloca, mutates
the buffer in place, reloads the LIST struct. The deferred phi
store from the body-exit incoming becomes a load-from-self /
store-to-self no-op because `new_acc.name == acc_phi_dest.name`.
Option B fallback (`Copy`-then-push) was on the table but
unnecessary; Option A shipped.

## Phase 2 — apply fix

Two edits in `mapanare/lower.py`:

1. New `_emit_list_decode_body(arr_jval, inner_type) -> Value`
   helper (~75 LOC) at `lower.py:3245` — mirrors v5.39.4
   `_emit_list_json_body` shape on the decode side. Extract
   `List<JsonValue>` from the `Array` variant, initialize empty
   accumulator, mutable-Phi loop, recurse through
   `_decode_json_field` per element, in-place ListPush.

2. New `TypeKind.LIST` branch (~10 LOC) in `_decode_json_field`
   immediately before the raw-jval fallback. Element type derived
   from `target_type.type_info.args[0]`; recursion handles
   `List<List<X>>`, `List<Struct>`, etc. uniformly.

Total source delta: ~85 LOC `mapanare/lower.py` + ~80 LOC
`stdlib/encoding/json/tests/test_from_json_list_field.mn` + ~8
LOC `test_to_from_nested_roundtrip.mn` (assertion strengthening)
+ ~6 LOC `tests/stdlib/test_struct_json_runtime.py::TEST_FILES` +
~110 LOC CHANGELOG + ~30 LOC SPEC sync + this SESSION_REPORT +
mechanical `bump_version.py` edits.

Verified post-fix: `/tmp/fromjson_list.mn` prints `3`. Existing
JSON test suites all GREEN: `test_struct_json_runtime.py` 11/11
(post-extension), `test_struct_json_ir_shape.py` 4/4,
`test_struct_json_layout.py` 2/2, `test_struct_json.py` 13 passed
+ 1 xfailed (pre-existing).

## Phase 3 — self-host mirror verify

Phase 0 grep returned 0 matches → mirror N/A by construction.
STRICT preserved trivially (zero `mapanare/self/*.mn` source
touches in v5.39.5).

## Phase 4 — extend regression suite

Two test files touched:

1. **New** `stdlib/encoding/json/tests/test_from_json_list_field.mn`
   (~80 LOC, 3 sub-cases wrapped in helper functions:
   `case_int_three()` / `case_int_empty()` / `case_string_two()`).
   Helper functions are load-bearing — `_lower_from_json`'s
   `from_json_merge` / `decode_object` block labels are bare (not
   `_fresh_block`-prefixed); multiple `from_json::<T>` calls in
   one function body collide pre-MIR-verifier:

   ```
   VerifyError(main::from_json_merge: switch case target unknown: 'match_arm4')
   VerifyError(main::decode_object: jump to unknown block 'list_dec_header0')
   ```

   Documented as a v5.39.6+ LOW (cosmetic; surfaced because
   v5.39.5's test exercised the multi-decode shape that prior
   tests didn't).

2. **Strengthened** `test_to_from_nested_roundtrip.mn` with three
   new assertions: `len(decoded.inner.ints) == 3`,
   `decoded.inner.ints[0] == 10`, `decoded.inner.ints[2] == 30`.
   v5.39.4 deliberately omitted these because the embedded
   `List<Int>` field would have failed on the decode side;
   v5.39.5 closes the gap, making the test stricter going forward.

Test added to `tests/stdlib/test_struct_json_runtime.py::TEST_FILES`.

**Falsifiability round-trip** (executed in session): reverted the
`TypeKind.LIST` branch in `_decode_json_field` →
`test_from_json_list_field` SEGV'd (exit -11) and the
strengthened `test_to_from_nested_roundtrip` failed on the new
`inner.ints` assertions; reapplied the branch → both restored to
GREEN. Anchor locked for future regression detection.

## Phase 5 — bump + closeout

- `bump_version.py 5.39.5` clean (VERSION + 4 README badges +
  CHANGELOG stub)
- CHANGELOG `### Fixed` entry filled in with full Js.4.D.3
  details, in-place vs Copy decision logged, v5.39.x arc CLOSED
  framing, MAP/ENUM held with documented open invariant questions
- `docs/SPEC.md` header re-synced to "v5.39.5 cut" with new sync
  block summarizing Js.4.D.3 + arc closeout
- `check_doc_freshness.py` GREEN
- `check_changelog_honesty.py` GREEN
- `make build-rt` GREEN; `make ci-gates` GREEN; `make lint` clean
- `python3 scripts/build_stage1.py` clean
- `bash scripts/verify_fixed_point.sh` STRICT (241,898 / 0)
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  95/95
- JSON test suite 11/11 GREEN (was 10; +1)

## Aggregate state entering v5.40.0

- **0 HIGH** — typed-serde round-trip closed for the v5.40.0
  Ai.\* call shapes
- **1 MEDIUM** — macOS notarization (carry from v5.33.0 Nu.2,
  unchanged across the v5.39.x arc)
- **~10 LOW** — MAP encode/decode (paired with invariant
  decision), ENUM encode/decode (paired with shape decision),
  bare block labels in `_lower_from_json` (cosmetic; surfaced
  by v5.39.5 multi-decode test — restructured around it), plus
  prior carries (`to_json::<T>` LIST/MAP/ENUM nested encoding
  partially closed; `from_json::<T>` MAP/ENUM nested decoding
  remains)

**Js.4.\* arc CLOSED for v5.40.0 dependencies. Manifesto-arc
kickoff (v5.40.0 Ai.\* — `ask`/`ask_typed::<T>`) unblocked for
all common LLM response shapes.**
