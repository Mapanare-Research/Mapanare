# v5.39.4 SESSION REPORT — Js.4.D.1 + Js.4.D.2 — typed-serde round-trip closure

**Status:** ready, not tagged.
**Date:** 2026-05-03.
**Predecessor:** v5.39.3 (Js.4.C — STRUCT field encoding).
**Successor target:** v5.39.5 (MAP/ENUM encode + LIST/MAP/ENUM decode candidates).

## Scope

Two siblings to v5.39.3, bundled in one release:

1. **Js.4.D.1** — `to_json::<T>` LIST nested encoding. The next missing
   `TypeKind` branch in `mapanare/lower.py::_encode_field_to_json`
   after v5.39.3's STRUCT branch.
2. **Js.4.D.2** — `from_json::<T>` nested-struct decoding. Round-trip
   pair to v5.39.3's encode side.

Bundling rationale: together they unlock the full nested-struct
round-trip (`to_json::<T>` ↔ `from_json::<T>`) for the shapes
v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns. Each is small,
self-contained, and structurally similar to v5.39.3.

**Out of scope (deferred to v5.39.5+, all noted in CHANGELOG):**

- MAP encoding (string-key invariant question: reject vs coerce vs
  runtime-error)
- ENUM encoding (tagged-union shape question: `"VariantName"` vs
  `{"Variant": payload}` vs `{"tag": ..., "payload": ...}`)
- LIST/MAP/ENUM decoding (mirror of the encode-side questions)

## Phase 0 — pre-flight + repro confirmation

- VERSION baseline: 5.39.3
- `make ci-gates`: GREEN (9 sub-gates)
- JSON test baseline: 26 passed + 1 xfailed
- Self-host grep `from_json|decode_to|encode_struct|to_json` in
  `mapanare/self/`: **0 matches** → Phase 3 mirror N/A by construction.

**Pre-fix repros captured:**

- Js.4.D.1: `Bag("box", [1, 2, 3])` → `{"name": "box", "items": <?>}`
- Js.4.D.2: nested round-trip → `FAIL roundtrip wrong values`
  (encode succeeds via v5.39.3 STRUCT branch; decode silently
  produces wrong inner fields)

## Phase 1 — diagnosis

**Encode side (Js.4.D.1):** `_encode_field_to_json` had branches for
`STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT` (the latter at
v5.39.3) but no `LIST`. Fallback `Call(fn_name="str", args=[...])`
emitted the literal `<?>` placeholder via `_mkstr("<?>")` in the
LLVM emitter.

**Decode side (Js.4.D.2):** `_decode_json_field` had branches for
`STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION` but no `STRUCT`. Fallback
returned the raw `JsonValue` enum where the consumer expected the
struct shape. Failure mode: silent shape mismatch (no link error,
no SEGV — just garbage data).

**Field lookup audit (load-bearing):** confirmed at
`mapanare/lower.py:2912` that `_lower_decode_to` uses by-name
lookup (`Const(key=fname)` → `IndexGet(entries, key)`) — not
positional — so the round-trip works for any JSON producer
regardless of field-declaration order.

## Phase 2a — Js.4.D.1 implementation

New helper `_emit_list_json_body(list_val, inner_type) -> Value`
(~100 LOC including comments) using mutable-Phi loop pattern:

- entry: zero=0; len_v=len(list); init="["; jump header
- header: counter=phi(zero, new_counter); result=phi(init, new_result);
  cmp = counter < len_v; branch body|exit
- body: elem = list[counter]; elem_str = _encode_field_to_json(elem,
  inner_type); separator branch (counter==0 ? "" : ", "); append;
  counter++; jump header
- exit: append "]"; return

Mutable-Phi pattern: emit Phi instructions at header with empty
incoming, fill incoming after body's exit label is known
(`Phi.incoming` is a mutable list — pattern is safe).

Plugged into `_encode_field_to_json` LIST branch immediately before
the `str()` fallback.

**Verification:**

- `Bag("box", [1, 2, 3])` → `{"name": "box", "items": [1, 2, 3]}` ✓
- `EmptyBag([])` → `{"items": []}` ✓ (loop never enters body)
- `StrBag(["foo", "bar"])` → `{"tags": ["foo", "bar"]}` ✓
  (recursing through STRING branch)
- `NestedBag([NestedItem(1, "a"), NestedItem(2, "b")])` →
  `{"items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}` ✓
  (recursing through STRUCT branch from v5.39.3)

JSON test suite 26 passed + 1 xfailed (unchanged from baseline).

## Phase 2b — Js.4.D.2 implementation

Extracted `_emit_decode_struct_inline(json_val, struct_name) -> Value`
helper (~30 LOC) from `_lower_decode_to`'s Object-branch body:

- Extract entries map from JsonValue Object payload
- For each declared field: `Const(key=fname)` → `IndexGet(entries, key)`
  → `_decode_json_field(jval, ftype)` (recursive)
- StructInit + Move drains
- Return bare struct (no Result wrap)

`_lower_decode_to`'s Object branch now calls the helper inline (one
line replacing ~25 LOC of inlined body); behavior unchanged. The
new STRUCT branch in `_decode_json_field` calls the same helper —
trusts the JsonValue is an Object variant (consistent with the
no-tag-check behavior of the primitive branches; on mismatch
produces wrong-shape data, same failure mode as a primitive variant
mismatch).

**Verification:**

- `from_json::<Wrap>("{\"name\":\"ok\",\"inner\":{\"x\":42,\"y\":\"hi\"}}")`
  → `Ok(Wrap{name:"ok", inner:{x:42, y:"hi"}})` ✓
- Round-trip `Wrap("ok", Inner(42, "hi", [10, 20, 30]))` →
  encode → decode → field-by-field equality holds for outer name,
  inner.x, inner.y ✓

JSON test suite 26 passed + 1 xfailed (unchanged from baseline).

## Phase 3 — self-host mirror

**N/A by construction.** Phase 0 verified
`grep -rn "from_json\|decode_to\|encode_struct\|to_json" mapanare/self/`
returned 0 matches. The Js.4 typed-serde surface shipped Python-
bootstrap-only at v5.36.0 and has not been mirrored. STRICT
preserved by construction; v5.39.4 makes zero `mapanare/self/*.mn`
source touches.

## Phase 4 — regression suite

Three new `.mn` files under `stdlib/encoding/json/tests/`:

1. `test_to_json_list_field.mn` — Js.4.D.1 single-direction encode.
   Asserts `encoded.contains("[1, 2, 3]")` AND
   `!encoded.contains("<?>")`.
2. `test_from_json_nested_struct.mn` — Js.4.D.2 single-direction
   decode. Asserts `w.name=="ok" && w.inner.x==42 && w.inner.y=="hi"`.
3. `test_to_from_nested_roundtrip.mn` — load-bearing round-trip with
   embedded `List<Int>` field exercising both fixes; failure mode
   dispatches on the specific diverging field.

`tests/stdlib/test_struct_json_runtime.py::TEST_FILES` extended
with all three. **10/10 GREEN** (was 7 at v5.39.3 HEAD; +3).

**Falsifiability locked:**

- Revert `_encode_field_to_json` LIST branch → `test_to_json_list_field.mn`
  fails on `<?>`-substring check; reapply → passes.
- Revert `_decode_json_field` STRUCT branch → `test_from_json_nested_struct.mn`
  fails on inner-field assertion; reapply → passes.
- Revert both → `test_to_from_nested_roundtrip.mn` fails with
  "FAIL test_to_from_nested_roundtrip: wrong inner.x"; reapply
  both → passes.

## Phase 5 — closeout

- `bump_version.py 5.39.4` clean
- CHANGELOG `### Fixed` entry: bundle scope explicit; v5.39.5
  candidates listed (MAP encode, ENUM encode, LIST/MAP/ENUM decode)
- SPEC.md header re-synced from "v5.39.3 cut" to "v5.39.4 cut" with
  new sync block summarizing what v5.39.4 ships
- CLAUDE.md release-notes entry added at top of "Most recent releases"
- `check_doc_freshness.py`: GREEN
- `check_changelog_honesty.py`: GREEN
- `make build-rt && python3 scripts/build_stage1.py &&
  bash scripts/verify_fixed_point.sh`: STRICT preserved at
  241,898 lines / 0 diff
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`:
  95/95
- `make ci-gates`: GREEN; `make lint`: clean
- JSON test suite: 29 passed + 1 xfailed (was 26+1; +3 new)

## Source delta

- `mapanare/lower.py` ~165 LOC (Js.4.D.1 helper + branch ~115 LOC;
  Js.4.D.2 helper extraction + branch ~50 LOC net — `_lower_decode_to`
  body shrank by ~25 LOC, helper added ~30 LOC, STRUCT branch added
  ~10 LOC)
- `stdlib/encoding/json/tests/test_to_json_list_field.mn` ~25 LOC
- `stdlib/encoding/json/tests/test_from_json_nested_struct.mn` ~25 LOC
- `stdlib/encoding/json/tests/test_to_from_nested_roundtrip.mn` ~30 LOC
- `tests/stdlib/test_struct_json_runtime.py` ~10 LOC (TEST_FILES extension)
- `CHANGELOG.md` ~85 LOC (Js.4.D.1 + Js.4.D.2 + Changed notes)
- `docs/SPEC.md` ~30 LOC (sync block)
- `CLAUDE.md` ~80 LOC (release-notes entry)

## Aggregate state entering v5.39.5

- **0 HIGH** — Js.4.D.1 + Js.4.D.2 closed; nested-struct round-trip
  works end-to-end.
- **1 MEDIUM** — macOS notarization (carry from v5.33.0 Nu.2,
  unchanged).
- **~10 LOW** — `to_json::<T>` MAP nested encoding (string-key
  invariant decision), `to_json::<T>` ENUM nested encoding
  (tagged-union shape decision), `from_json::<T>` LIST nested
  decoding, `from_json::<T>` MAP nested decoding, `from_json::<T>`
  ENUM nested decoding, plus prior carries (PV.7 LIST iteration MIR
  generalization candidate, etc).

Manifesto-arc kickoff (v5.40.0 Ai.\* — `ask`/`ask_typed::<T>`)
unblocked for nested-struct typed responses; collection-typed
responses await v5.39.5+.
