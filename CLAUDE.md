# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Mapanare is an AI-native compiled language with first-class agents,
signals, streams, and tensors. Compiles to LLVM IR (primary) and C
(fallback via gcc). WebAssembly backend for browser/server targets.
Self-hosted compiler is 38,000+ lines of `.mn` across 10 modules in
`mapanare/self/`. The compiler compiles itself —
`bash scripts/build_from_seed.sh` builds from source with no Python.

**Current version:** see `VERSION` file.

## Current Version & Roadmap

Most recent releases. Full history at
`docs/roadmap/ROADMAP.md` and
`docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` per release:

- **v5.39.7** (ready, not tagged) — **Js.4.F.1 + Js.4.F.2 —
  typed-serde ENUM encode + decode; round-trip closure for
  enum-typed fields. Final release in the v5.39.x typed-serde
  arc; Js.4.\* arc CLOSED.** After v5.39.7 the typed-serde
  round-trip `to_json::<T>` ↔ `from_json::<T>` closes for
  **every common LLM JSON response shape** (primitive, struct,
  nested struct, `List<X>`, `Map<String, V>`, and tagged-union
  enums). Adds **zero language features, zero new MIR ops,
  zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.6's
  **241,898 lines / 0 diff** (41-release strict streak from
  v5.7.1; zero `mapanare/self/*.mn` source touches — Phase 0
  verified `grep -rn "from_json|decode_to|encode_struct|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.F.1 — ENUM encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (v5.39.3) + `LIST` (v5.39.4) + `MAP` (v5.39.6) but no branch
  for user-defined enum-typed fields. Pre-fix the fallback at
  `Call(fn_name="str", args=[field_val])` emitted the literal
  `<?>` placeholder. `Record(2, Pending(42))` encoded as
  `{"id": 2, "status": <?>}`; post-fix encodes as
  `{"id": 2, "status": {"Pending": 42}}`. Fix adds a new
  `_emit_enum_json_body(enum_val, enum_name) -> Value` helper
  (~120 LOC) that switches on `EnumTag(enum_val)` with one
  block per variant + a default block, merges the per-variant
  strings via a Phi. Per-variant payload shape: **no-payload →
  bare string `"VariantName"`; single-payload →
  `{"VariantName": <encoded>}`; multi-payload →
  `{"VariantName": [<p0>, <p1>, ...]}`** (positional tuple →
  JSON array). Recurses through `_encode_field_to_json` per
  payload type so nested struct / list / map / enum payloads
  fall through uniformly. **Js.4.F.2 — ENUM decode.**
  `mapanare/lower.py:3336::_decode_json_field` had explicit
  handlers for primitives + OPTION + STRUCT (v5.39.4) + LIST
  (v5.39.5) + MAP (v5.39.6) but no branch for user-defined
  enum-typed fields. Pre-fix the raw-jval fallback returned
  the JsonValue enum where the typed enum value was expected
  — silent shape mismatch on the consumer side. Fix adds a
  new `_emit_enum_decode_body(jval, enum_name) -> Value`
  helper (~190 LOC) that switches on the JsonValue tag (Str /
  Object / default), then runs a string-cascade compare
  against each variant name. **Str path:** each no-payload
  variant gets one
  `if jstr == "VariantName" { EnumInit(VariantName) }` arm.
  **Object path:** extract the `Map<String, JsonValue>`
  entries via `EnumPayload(variant="Object")`, pull the single
  variant key via `__mn_map_keys`+`keys[0]`, cascade-compare
  against each payload-bearing variant, decode the payload(s)
  positionally (1-tuple → recurse `_decode_json_field`;
  n-tuple → extract `JsonValue::Array`'s inner
  `List<JsonValue>` and decode each element by its declared
  payload type), then `EnumInit` with the decoded payloads.
  **Linear cascade** — fast enough for typical enums (< 20
  variants); hash-based dispatch is a v5.40+ candidate.
  **Js.4.F.0 — enum/struct disambiguation.**
  `_resolve_type_expr` cannot distinguish enum from struct at
  parse time — both come through as `TypeKind.STRUCT` with
  the user-supplied name. The Js.4.F.1 + Js.4.F.2 branches
  are routed inside the existing STRUCT branches: check
  `self._module.enums` first (with the skip list
  `{Option, Result, JsonValue}` keeping compiler-internal
  enums on their existing paths — OPTION is handled
  separately, Result is the parent context never reached as a
  struct field, JsonValue is the recursive case routed via
  `_ensure_json_types_registered`), fall through to the
  struct path only if the name is genuinely a struct.
  **Externally-tagged JSON shape locked at PLAN.** Three
  shapes were on the table (externally tagged
  `{"V": payload}`, internally tagged `{"tag": "V", ...}`,
  adjacently tagged `{"tag": "V", "payload": ...}`);
  externally tagged was chosen — most common in JSON-RPC,
  OpenAI / Anthropic function-calling schemas, and Rust
  serde's default derive output; round-trips trivially
  through the existing `_emit_list_decode_body` for
  multi-payload variants. Special case: no-payload variants
  encode as the bare string `"VariantName"` (not
  `{"VariantName": null}`) — matches Rust serde's
  `untagged()` for unit variants and is what most LLMs
  produce in function-call responses.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Three new `.mn` test
  files appended to `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`:
  `test_to_json_enum_field.mn` (Js.4.F.1 single-direction
  encode covering all three variant payload shapes),
  `test_from_json_enum_field.mn` (Js.4.F.2 single-direction
  decode covering all three shapes), and
  `test_to_from_enum_roundtrip.mn` (load-bearing round-trip
  ensuring encode and decode wire to the same JSON shape).
  **18/18 GREEN** at HEAD (was 15 at v5.39.6; +3).
  **Match arms use block-form actions** (`=> { ok = ... }`)
  because the parser does not accept `=> return EXPR` after a
  pattern — collect success into a mutable flag and return
  it. Documented in each test file preamble as a v5.40+
  parser-ergonomics candidate. Falsifiability locked per fix
  — reverting either branch fails the corresponding
  single-direction test plus the round-trip; reverting both
  fails all three new tests.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.6 cut" to "v5.39.7 cut" with new sync block
  documenting the externally-tagged invariant decision +
  Js.4.\* arc closeout. `check_doc_freshness.py` GREEN;
  `check_changelog_honesty.py` GREEN. Source delta: ~310 LOC
  `mapanare/lower.py` (Js.4.F.1 helper + branch ~120 LOC;
  Js.4.F.2 helper + branch ~190 LOC) + ~225 LOC `.mn` test
  cases (3 files) + ~22 LOC `test_struct_json_runtime.py`
  TEST_FILES + ~115 LOC CHANGELOG + ~50 LOC SPEC sync + this
  CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. **Arc retrospective:** v5.39.0 →
  v5.39.7 closed every `TypeKind` branch in
  `_encode_field_to_json` / `_decode_json_field` that
  v5.36.0's Phase-0 audit identified as structurally
  incomplete. Round-trip now works end-to-end for: primitives
  (v5.39.2), multi-field structs (v5.39.2), nested structs
  (v5.39.3 + v5.39.4), `List<X>` (v5.39.4 + v5.39.5),
  `Map<String, V>` (v5.39.6), and tagged-union enums
  (v5.39.7). The bundling discipline (one TypeKind per
  release, with documented invariant decisions for the harder
  cases) traded release count for falsifiability rigor —
  every fix has a revert-and-restore test pair locked in the
  regression suite. Aggregate state entering v5.40.0:
  **0 HIGH** (Js.4.F.\* closed; typed-serde round-trip closed
  for every common LLM JSON shape) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~5 LOW (hash-
  dispatched enum decode, internally/adjacently tagged shapes,
  custom serde rename attributes, parser ergonomic
  `=> return EXPR`, prior carries). **Js.4.\* arc CLOSED.
  v5.40.0 manifesto-arc kickoff (`ask` / `ask_typed::<T>`)
  fully unblocked.** See
  `docs/roadmap/v5/v5.39.7/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.6** (ready, not tagged) — **Js.4.E.1 + Js.4.E.2 —
  typed-serde MAP encode + decode; round-trip closure for
  `Map<String, V>`-typed fields.** Sibling release to v5.39.5
  (LIST decode); bundles encode + decode in one release because
  Map's invariant decision is simpler than LIST's was
  (string-key only — JSON object keys are strings per RFC 8259
  §4) and both halves are mechanical mirrors of v5.39.4 +
  v5.39.5 patterns. Adds **zero language features, zero new
  MIR ops, zero new IR shapes, zero new C runtime exports**.
  **Strict 3-stage fixed point preserved by construction** at
  v5.39.5's **241,898 lines / 0 diff** (40-release strict
  streak from v5.7.1; zero `mapanare/self/*.mn` source
  touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.E.1 — MAP encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (v5.39.3) and `LIST` (v5.39.4) but no branch for
  `TypeKind.MAP`. The fallback at
  `Call(fn_name="str", args=[field_val])` emitted the literal
  `<?>` placeholder. Pre-fix `Bag("box", #{"a": 1, "b": 2})`
  encoded as `{"name": "box", "lookup": <?>}`; post-fix encodes
  as `{"name": "box", "lookup": {"a": 1, "b": 2}}` (key order
  unspecified per RFC 8259). Fix adds a new
  `_emit_map_json_body(map_val, val_type) -> Value` helper
  mirroring v5.39.4's `_emit_list_json_body` shape: iterate via
  `__mn_map_keys` (returns `List<String>`) + per-key IndexGet
  on the map (lowered to `__mn_map_get`), emit
  `"key": value` pairs separated by `, `, recurse through
  `_encode_field_to_json` per value so nested
  `Map<String, Struct>` / `Map<String, List>` /
  `Map<String, Map>` fall through STRUCT / LIST / MAP /
  primitive branches uniformly. Mutable-Phi loop pattern
  matches v5.39.4. **Js.4.E.2 — MAP decode.**
  `mapanare/lower.py:3166::_decode_json_field` had explicit
  handlers for primitives + OPTION + STRUCT (v5.39.4) + LIST
  (v5.39.5) but no branch for `TypeKind.MAP`. Pre-fix
  `from_json::<Bag>("{\"lookup\": {\"a\": 1}}")` SEGV'd
  (consumer treated raw JsonValue::Object enum bytes as a
  `MnMap*`). Fix adds a new
  `_emit_map_decode_body(jval, val_type) -> Value` helper
  mirroring v5.39.5's `_emit_list_decode_body` decode-side
  shape: extract `Map<String, JsonValue>` from the `Object`
  variant via `EnumPayload(variant="Object", payload_idx=0)`,
  initialize an empty `Map<String, V>` accumulator (relies on
  v5.39.2's `_do_map_init` empty-literal type-derivation fix
  for correct bucket sizing), iterate keys, recurse-decode per
  value, accumulate via `IndexSet` (lowered to
  `__mn_map_set`).
  **No SSA-name-reuse trick needed (vs. v5.39.5 ListPush)** —
  Phase 1 audit confirmed `MAP` lowers to `PTR` in the IR
  (`emit_llvm_text._rty`), and `__mn_map_set` mutates the
  bucket array in place without changing the outer `MnMap*`.
  The accumulator value is invariant across loop iterations,
  so the decode helper uses a single counter phi (no acc phi).
  **Invariant decision (locked at PLAN — no Phase 0 audit)**:
  `Map<K, V>` fields with non-String K → compile-time error.
  Diagnostic shape: `to_json/from_json: Map<K, V> requires
  K = String (got <KIND>)`. Rationale: JSON object keys are
  strings per RFC 8259 §4; `Map<Int, X>` and `Map<Float, X>`
  have no canonical JSON projection. Rejected silent lossy
  coercion (`str(key)` → asymmetric round-trip) and runtime
  error (surfaced too late) in favor of compile-time
  rejection. Documented as `### Changed` (potentially
  breaking-ish but no production user has exercised this path
  pre-fix — encode emitted `<?>`, decode SEGV'd).
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Two new `.mn` test files
  (`test_to_json_map_field.mn`, `test_from_json_map_field.mn`,
  3 sub-cases each wrapped in helper functions per the v5.39.5
  caveat about bare `from_json_merge` block labels) appended
  to `TEST_FILES`. Plus 2 parametrized rejection cases
  (`test_typed_serde_map_nonstring_key_rejected`) asserting
  `RuntimeError` for `Map<Int, V>` and `Map<Float, V>` fields.
  **15/15 GREEN** at HEAD (was 11 at v5.39.5; +4 total).
  Falsifiability locked per fix — disabling either MAP branch
  in `lower.py` makes the corresponding test fail; reapplying
  restores GREEN.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.5 cut" to "v5.39.6 cut" with new sync block
  documenting the MAP invariant decision.
  `check_doc_freshness.py` GREEN; `check_changelog_honesty.py`
  GREEN. Source delta: ~185 LOC `mapanare/lower.py`
  (Js.4.E.1 helper + branch ~95 LOC; Js.4.E.2 helper + branch
  ~90 LOC) + ~160 LOC `.mn` test cases (2 files) + ~44 LOC
  `test_struct_json_runtime.py` (TEST_FILES + rejection
  parametrized cases) + ~120 LOC CHANGELOG + ~35 LOC SPEC sync
  + this CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. Aggregate state entering v5.39.7:
  **0 HIGH** (Js.4.E.\* closed) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~6 LOW (added ENUM
  encode/decode as v5.39.7 candidate — last typed-serde piece
  before v5.40.0 manifesto-arc kickoff). **Js.4.E.\* arc
  CLOSED.** See
  `docs/roadmap/v5/v5.39.6/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.5** (ready, not tagged) — **Js.4.D.3 — typed-serde
  LIST decode (round-trip closure for List-typed fields);
  v5.39.x arc CLOSED.** Symmetric pair to v5.39.4 Js.4.D.1
  (LIST encode). Closes the last v5.39.x-deferred typed-serde
  gap before the v5.40.0 manifesto-arc kickoff. After this
  release, the typed-serde round-trip
  `to_json::<T>` ↔ `from_json::<T>` closes for **every shape
  v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns** from
  typical LLM responses (primitive, struct, nested struct,
  `List<primitive>`, `List<struct>`). Adds **zero language
  features, zero new MIR ops, zero new IR shapes, zero new C
  runtime exports**. **Strict 3-stage fixed point preserved
  by construction** at v5.39.4's **241,898 lines / 0 diff**
  (39-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.D.3 — LIST decode.**
  `mapanare/lower.py:3166::_decode_json_field` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (the latter from v5.39.4) but no branch for
  `TypeKind.LIST`. The fallback `return jval` returned the
  raw `JsonValue::Array` enum where the consumer expected the
  typed `List<X>` value — silent shape mismatch surfaced as
  wrong list contents (or downstream segfault on element
  access). Pre-fix
  `from_json::<Bag>("{\"items\": [1, 2, 3]}")` printed
  garbage `94467072822368` for `len(b.items)`; post-fix
  prints `3`. Fix adds a new
  `_emit_list_decode_body(arr_jval, inner_type) -> Value`
  helper mirroring v5.39.4's `_emit_list_json_body` shape on
  the decode side: extract `List<JsonValue>` from the `Array`
  variant via `EnumPayload(variant="Array", payload_idx=0)`,
  initialize an empty `List<inner>` accumulator, mutable-Phi
  loop over the inner array length, recurse through
  `_decode_json_field` per element, accumulate via in-place
  `ListPush` (mirrors `_lower_method_call`'s `.push()` SSA
  name-reuse pattern at `mapanare/lower.py:3298` — the dest
  reuses `acc_phi_dest`'s name so the emitter's phi alloca
  acts as the single mutable list slot across iterations).
  Element type from `target_type.type_info.args[0]`;
  recursion handles nested `List<List<X>>`, `List<Struct>`,
  etc. uniformly through the existing dispatch.
  **In-place ListPush across the loop boundary** — Phase 1
  audit confirmed Option A (in-place push reusing the phi
  dest's SSA name) works. The phi alloca system at
  `mapanare/emit_llvm_text.py:2461-2473` registers
  `_alloc[acc_phi_dest.name] = (%phi.<name>, ty)`; ListPush
  at `:4761` finds the alloca via `_get_ptr`, calls
  `__mn_list_push` which mutates the buffer in place, then
  reloads. The deferred phi store from the body-exit
  incoming becomes a no-op load-from-self / store-to-self
  because `new_acc.name == acc_phi_dest.name`. Option B
  fallback (`Copy`-then-`ListPush`) was on the table but
  Phase 1 spike produced valid IR for Option A, so Option A
  shipped.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been
  mirrored. STRICT preserved trivially.
  **Test infrastructure extension.** New
  `stdlib/encoding/json/tests/test_from_json_list_field.mn`
  (~80 LOC, 3 sub-cases: `List<Int>` with 3 elements, empty
  list, `List<String>` with 2 elements) appended to
  `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`. Each sub-case
  is wrapped in its own helper function because
  `_lower_from_json`'s `from_json_merge` / `decode_object`
  block labels are bare (not `_fresh_block`-prefixed);
  multiple `from_json::<T>` calls in one function body
  collide pre-MIR-verifier. Documented as a v5.39.6+ LOW
  (cosmetic; surfaced because v5.39.5's test exercised the
  multi-decode shape that prior tests didn't). 11/11 GREEN
  at HEAD (was 10 at v5.39.4 HEAD; +1).
  **Strengthened `test_to_from_nested_roundtrip.mn`** with
  three new assertions
  (`len(decoded.inner.ints) == 3`,
  `decoded.inner.ints[0] == 10`,
  `decoded.inner.ints[2] == 30`). v5.39.4 deliberately
  omitted these because the embedded `List<Int>` field would
  have failed on the decode side; v5.39.5 closes the gap.
  Falsifiability locked per fix — reverting the
  `TypeKind.LIST` branch in `_decode_json_field` makes
  `test_from_json_list_field` SEGV (exit -11) and the
  strengthened nested round-trip fail on the new
  `inner.ints` assertions; reapplying restores both to
  GREEN.
  **Hd-class preventative** — `docs/SPEC.md` header
  re-synced from "v5.39.4 cut" to "v5.39.5 cut" with new
  sync block. `check_doc_freshness.py` GREEN;
  `check_changelog_honesty.py` GREEN. Source delta: ~85 LOC
  `mapanare/lower.py` (helper + branch) + ~80 LOC `.mn`
  test case + ~8 LOC nested-roundtrip strengthening + ~6
  LOC `test_struct_json_runtime.py` TEST_FILES update +
  ~110 LOC CHANGELOG + ~30 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.40.0: **0 HIGH** (Js.4.D.3
  closed; typed-serde round-trip closed for v5.40.0 Ai.\*
  call shapes) / **1 MEDIUM** (macOS notarization carry
  from v5.33.0 Nu.2) / ~10 LOW (added MAP encode/decode,
  ENUM encode/decode, bare block labels in
  `_lower_from_json` cosmetic). **Js.4.\* arc CLOSED for
  v5.40.0 dependencies.** v5.40.0 manifesto-arc kickoff
  (`ask`/`ask_typed::<T>`) unblocked. See
  `docs/roadmap/v5/v5.39.5/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.39.4** (ready, not tagged) — **Js.4.D.1 + Js.4.D.2 —
  typed-serde round-trip closure for nested-struct + List-typed
  fields.** Two siblings to v5.39.3's STRUCT field encoding
  (Js.4.C), bundled in one release because together they unlock
  the `to_json::<T>` ↔ `from_json::<T>` round-trip for the
  shapes v5.40.0 Ai.\* (`ask_typed::<T>`) actually returns. After
  this release, the typed-serde round-trip handles
  `struct Wrap { name: String, inner: Inner }` end-to-end
  (encode → decode → field-by-field equality holds), and
  List-typed fields encode element-by-element. Adds **zero
  language features, zero new MIR ops, zero new IR shapes,
  zero new C runtime exports**. **Strict 3-stage fixed point
  preserved by construction** at v5.39.3's **241,898 lines / 0
  diff** (38-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **Js.4.D.1 — LIST encode.**
  `mapanare/lower.py:2689::_encode_field_to_json` had explicit
  handlers for `STRING`/`INT`/`FLOAT`/`BOOL`/`OPTION`/`STRUCT`
  (the latter from v5.39.3) but no branch for `TypeKind.LIST`.
  The fallback `Call(fn_name="str", args=[field_val])` emitted
  the literal `<?>` placeholder via `_mkstr("<?>")`. Pre-fix
  `Bag("box", [1, 2, 3])` encoded as
  `{"name": "box", "items": <?>}`. Fix adds a new
  `_emit_list_json_body(list_val, inner_type) -> Value` helper
  emitting a counter+phi loop that calls `_encode_field_to_json`
  per element, recursing through STRUCT / LIST / primitive
  branches uniformly. Empty `[]`, `["foo", "bar"]`, and
  `[{"id": 1, "name": "a"}, ...]` all encode correctly post-fix.
  Mutable-Phi loop pattern: emit Phi instructions at header with
  empty incoming, fill incoming after body's exit label is known
  (`Phi.incoming` is a mutable list — pattern is safe).
  **Js.4.D.2 — STRUCT decode.**
  `mapanare/lower.py:3019::_decode_json_field` had explicit
  handlers for primitives + OPTION but no branch for
  `TypeKind.STRUCT`. The fallback returned the raw `JsonValue`
  enum where the consumer expected the struct shape — silent
  shape mismatch surfaced as wrong field values after decode
  (no link error, no SEGV — just garbage data). Pre-fix nested
  `from_json::<Wrap>(s)` returned a Wrap with `inner.x=0` /
  `inner.y=""`. Fix mirrors v5.39.3's encode-side helper-extract
  pattern: extracted
  `_emit_decode_struct_inline(json_val, struct_name) -> Value`
  from `_lower_decode_to`'s Object branch (the field-extraction
  + StructInit body, ~30 LOC); the helper is shared between the
  top-level `decode_to::<T>` / `from_json::<T>` Ok-path
  (replacing the inlined body) and the new STRUCT branch in
  `_decode_json_field` (which trusts the JsonValue is an Object
  variant, consistent with the no-tag-check behavior of the
  primitive branches).
  **Field lookup audit (load-bearing):** confirmed at
  `mapanare/lower.py:2912` that `_lower_decode_to` uses
  by-name lookup (`Const(key=fname)` → `IndexGet(entries, key)`)
  — not positional — so the round-trip works for any JSON
  producer regardless of field-declaration order.
  **Bundle scope: STRUCT decode + LIST encode only.** MAP
  encoding has the JSON-string-key invariant question (reject
  vs coerce vs runtime-error); ENUM encoding has the tagged-
  union shape question (`"VariantName"` vs `{"Variant":
  payload}` vs `{"tag": ..., "payload": ...}`); LIST/MAP/ENUM
  decoding mirrors the same questions on the parse side. Each
  deserves its own Phase 0 audit and lead-approved invariant
  decision. v5.39.5+ picks them up.
  **Self-host mirror N/A by construction**: Phase 0 grep
  returned 0 matches. The Js.4 typed-serde surface shipped
  Python-bootstrap-only at v5.36.0 and has not been mirrored.
  STRICT preserved trivially.
  **Test infrastructure extension.** Three new `.mn` test
  files appended to `TEST_FILES` in
  `tests/stdlib/test_struct_json_runtime.py`:
  `test_to_json_list_field.mn` (Js.4.D.1 single-direction encode),
  `test_from_json_nested_struct.mn` (Js.4.D.2 single-direction
  decode), and `test_to_from_nested_roundtrip.mn` (load-bearing
  round-trip with embedded `List<Int>` field exercising both
  fixes). 10/10 GREEN at HEAD (was 7 at v5.39.3 HEAD; +3).
  **Falsifiability locked per fix** — reverting either branch
  fails the corresponding single-direction test; reverting
  both fails the round-trip with the diverging-field signature.
  **Hd-class preventative** — `docs/SPEC.md` header re-synced
  from "v5.39.3 cut" to "v5.39.4 cut" with new sync block.
  `check_doc_freshness.py` GREEN; `check_changelog_honesty.py`
  GREEN. Source delta: ~165 LOC `mapanare/lower.py` (Js.4.D.1
  helper + branch ~115 LOC; Js.4.D.2 helper extraction + branch
  ~50 LOC net) + ~80 LOC `.mn` test cases (3 files) + ~10 LOC
  `test_struct_json_runtime.py` TEST_FILES update + ~85 LOC
  CHANGELOG + ~30 LOC SPEC sync + this CLAUDE.md release-notes
  entry + mechanical bump_version.py edits. Aggregate state
  entering v5.39.5: **0 HIGH** (Js.4.D.1 + Js.4.D.2 closed) /
  **1 MEDIUM** (macOS notarization carry from v5.33.0 Nu.2) /
  ~10 LOW (added MAP encode, ENUM encode, LIST/MAP/ENUM decode
  as v5.39.5+ candidates). See
  `docs/roadmap/v5/v5.39.4/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.3** (ready, not tagged) — **Js.4.C — `to_json::<T>`
  nested-struct recursion.** Split-from-v5.39.2 follow-on.
  v5.39.2 closed the runtime SEGV in `from_json::<T>` (Js.4.B.2)
  but explicitly held back the `to_json::<T>` nested-struct fix
  because it lives in a different code path. v5.39.3 closes that
  hole. After this release, the typed-serde encode path
  (`to_json::<T>`) handles nested struct fields end-to-end; the
  manifesto-arc ergonomic v5.40.0 Ai.\* will exercise via
  `ask_typed::<T>`. Adds **zero language features, zero new MIR
  ops, zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.2's
  **241,898 lines / 0 diff** (37-release strict streak from v5.7.1;
  zero `mapanare/self/*.mn` source touches — Phase 0 verified
  `grep -rn "from_json\|decode_to\|encode_struct\|to_json"
  mapanare/self/` returned 0 matches). Goldens **95/95**.
  **The bug.** `mapanare/lower.py:2681::_encode_field_to_json`
  had explicit handlers for `STRING` / `INT` / `FLOAT` / `BOOL` /
  `OPTION` (the latter recursing on the inner type) but no branch
  for `TypeKind.STRUCT`. The fallback at line 2762
  (`Call(fn_name="str", args=[field_val])`) emitted the literal
  `<?>` placeholder via `mapanare/emit_llvm_text.py:3465`'s
  `r, _ = self._mkstr("<?>")`. Latent since v5.36.0 Js.4 ship;
  the v5.36.0 `tests/stdlib/test_struct_json.py` was compile-only
  — the placeholder text was syntactically present in IR but
  never link-tested. **Fix.** Refactored `_lower_encode_struct`
  to delegate to a new shared `_emit_struct_json_body(struct_val,
  struct_name) -> Value` helper. Added the missing `TypeKind.STRUCT`
  branch in `_encode_field_to_json` that recurses through the
  same helper, guarded on
  `struct_name in self._module.structs`. The two call sites (the
  top-level `encode_struct::<T>` / `to_json::<T>` intrinsic and
  the new STRUCT-typed-field recursion) now share one load-bearing
  emitter. ~70 LOC change. **Bundle scope: STRUCT only.** Phase 1
  review of the LIST iteration MIR sketch put it at ~30-50 LOC
  (counter alloca + `len()` runtime call + comparison + IndexGet
  + accumulator) — exceeded PLAN's ~20 LOC bundle threshold.
  MAP and ENUM also held: MAP has the JSON-string-key invariant
  question (reject vs coerce vs runtime-error); ENUM has the
  tagged-union shape question (`"VariantName"` vs `{"Variant":
  payload}` vs `{"tag": ..., "payload": ...}`). v5.39.4 will
  pick these up together once the ENUM shape decision aligns
  with `from_json::<T>` round-trip semantics. **Self-host
  mirror N/A**: Phase 0 grep returned 0 matches. The Js.4
  typed-serde surface shipped Python-bootstrap-only at v5.36.0
  and has not been mirrored. STRICT preserved trivially by
  construction. **Test.** New
  `stdlib/encoding/json/tests/test_to_json_nested_struct.mn`
  (~30 LOC) appended to v5.39.2's
  `tests/stdlib/test_struct_json_runtime.py::TEST_FILES`.
  Single-direction encode-and-inspect (`to_json::<Wrap>(w)` then
  `String.contains` checks). Single-direction on purpose: the
  `from_json::<T>` decoder
  (`mapanare/lower.py::_decode_json_field`) only handles
  primitive field types at v5.39.3 HEAD — a round-trip equality
  test would fail on the decode side, not the v5.39.3 fix. Round-
  trip for nested structs is a v5.39.4 candidate. Falsifiability
  locked: reverting the new STRUCT branch reproduces the `<?>`
  placeholder; the new test fails with the recorded
  `FAIL test_to_json_nested_struct: still emits <?> placeholder`
  signature. One Edit-and-pytest cycle. **Hd-class preventative**
  — `docs/SPEC.md` header re-synced from "v5.39.2 cut" to
  "v5.39.3 cut" with new sync block. `check_doc_freshness.py`
  GREEN; `check_changelog_honesty.py` GREEN. Source delta:
  ~70 LOC `mapanare/lower.py` (helper extraction + STRUCT branch)
  + ~30 LOC `.mn` test case + ~2 LOC `test_struct_json_runtime.py`
  TEST_FILES update + ~75 LOC CHANGELOG + ~30 LOC SPEC sync +
  this CLAUDE.md release-notes entry + mechanical bump_version.py
  edits. Aggregate state entering v5.39.4: **0 HIGH** (Js.4.C
  closed for STRUCT) / **1 MEDIUM** (macOS notarization carry
  from v5.33.0 Nu.2) / ~8 LOW (added `to_json::<T>` LIST/MAP/ENUM
  nested encoding + `from_json::<T>` nested-struct decoding as
  v5.39.4 candidates). See
  `docs/roadmap/v5/v5.39.3/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.2** (ready, not tagged) — **Js.4.B.2 — `from_json::<T>`
  runtime SEGV closeout + link-and-run regression suite.
  v5.39.1+v5.39.2 arc CLOSED.** Second of two release sessions on
  Js.4.B; together they close the v5.36.0-deferred typed-serde
  defect surfaced at v5.40.0 Phase 0 audit. v5.39.1 closed the
  IR-emission shape (no-import case); v5.39.2 closes the runtime
  SEGV in `__mn_map_get` (with-import case). After v5.39.2 ships,
  v5.40.0 (Ai.\* — `ask` keyword, manifesto-arc kickoff) picks up
  cleanly with the typed-output ergonomic intact. Adds **zero
  language features, zero new MIR ops, zero new IR shapes, zero
  new C runtime exports**. **Strict 3-stage fixed point preserved
  by construction** at v5.39.1's **241,898 lines / 0 diff**
  (36-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **The bug.** PROMPT/PLAN's leading hypothesis was that
  `_is_self_ref` doesn't recurse through `LIST` / `MAP` / `OPTION`
  / `RESULT` type args, so `JsonValue::Object(Map<String,
  JsonValue>)` and `Array(List<JsonValue>)` weren't marked boxed
  at registration time. **Phase 1 instrumentation confirmed
  `boxed=set()` for JsonValue but the side-by-side IR audit of
  the construction (`malloc(8); store ptr %map`) vs extraction
  (`extractvalue, 1; gep {ptr}, 0; load ptr`) showed both sides
  agreed on the unboxed `{ptr}` layout.** The audit's hypothesis
  was wrong about the load-bearing root cause. The actual bug
  was one level deeper: **the Map handle itself was created with
  the wrong sizes/key-type.** GDB pinpointed the SEGV not inside
  `__mn_map_get` but two instructions past its return — at
  `load {i64, ptr} from NULL` in main, because
  `__mn_map_get` returned NULL (key not found). Inspecting the
  Map struct showed `key_size=8, val_size=8, key_type=0/INT` for
  what should have been a `Map<String, JsonValue>` (16/16/1).
  **Root cause:** `mapanare/emit_llvm_text.py::_do_map_init`
  empty-literal branch (`if i.pairs: ... else: ksz, vsz, ktag =
  8, 8, 0`) hardcoded `(8, 8, 0)` defaults instead of deriving
  from the declared `MapInit.key_type` / `MapInit.val_type`.
  **Any** `Map<String, X> = #{}` or `Map<Float, X> = #{}` was
  silently miscompiled. `decode_object_inner`'s
  `pon mut entries: Map<String, JsonValue> = #{}` was the
  load-bearing instance. Latent since the multi-typed map
  literal surface landed; never surfaced because the original
  `tests/stdlib/test_struct_json.py` was compile-only. **Fix:**
  derive `ksz` / `ktag` from `i.key_type` and `vsz` from
  `i.val_type` unconditionally. ~25 LOC change. Defensive
  symmetry fix in `_do_enum_init`: Map values consumed as enum
  payloads now also drain from `_map_vars` (was: only
  `_list_vars`) — doesn't fire in the v5.39.2 repro but the
  asymmetry was a latent footgun. **Self-host mirror N/A**:
  Phase 0 verified `mapanare/self/emit_llvm.mn:3106-3169::
  emit_map_init` already derives `key_size`/`val_size` from
  `key_ty`/`val_ty` regardless of pair count (sensible defaults
  16 / 64 for STRUCT/ENUM). The Python bug was a latent drift
  between Python and self-host that the self-host already had
  right. STRICT preserved trivially; v5.39.2 makes zero
  `mapanare/self/*.mn` source touches. **Link-and-run
  regression suite** — new `tests/stdlib/test_struct_json_runtime.py`
  + 6 `.mn` test cases under `stdlib/encoding/json/tests/`
  mirrors v5.34/v5.35/v5.39.0 concat pattern. This is the test
  infrastructure that should have existed since v5.36.0 — the
  compile-only `test_struct_json.py` (preserved unchanged) is
  exactly why Js.4.B stayed latent for 4 releases. All 6
  GREEN; v5.39.1's `test_struct_json_ir_shape.py` (4) +
  `test_struct_json_layout.py` (2) preserved GREEN.
  **Falsifiability round-trip locked as the test suite
  itself** — revert `_do_map_init`, all 6 cases fail with the
  recorded SEGV signature; reapply, all 6 pass. One
  Edit-and-pytest cycle. **`to_json::<T>` nested-struct split
  to v5.39.3** — `to_json::<Wrap>(w)` with struct-typed field
  still emits `<?>`; different code path
  (`_emit_struct_to_json`), out of v5.39.2's scope. **Hd-class
  preventative** — `docs/SPEC.md` header re-synced from
  "v5.39.1 cut" to "v5.39.2 cut". `check_doc_freshness.py`
  GREEN. Source delta: ~25 LOC `mapanare/emit_llvm_text.py`
  (`_do_map_init` + `_do_enum_init` defensive map-vars
  removal) + ~120 LOC pytest harness + ~120 LOC `.mn` test
  cases (6 files) + ~125 LOC CHANGELOG + ~30 LOC SPEC sync +
  this CLAUDE.md release-notes entry + mechanical
  bump_version.py edits. Aggregate state entering v5.39.3:
  **0 HIGH** (Js.4.B fully closed) / **1 MEDIUM** (macOS
  notarization carry from v5.33.0 Nu.2) / ~7 LOW (added
  `to_json::<T>` nested-struct as v5.39.3 candidate). **Js.4.B
  arc CLOSED.** v5.40.0 manifesto-arc kickoff unblocked. See
  `docs/roadmap/v5/v5.39.2/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.39.1** (ready, not tagged) — **Js.4.B.1 — `from_json::<T>`
  IR-emission shape fix (no-import case).** First of two release
  sessions dedicated to closing **Js.4.B** (the v5.36.0-deferred
  typed-serde defect that v5.40.0 Phase 0 audit
  (`docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md`) re-diagnosed as
  significantly worse than the original SESSION_REPORT
  documented — actually two structurally distinct failure modes,
  not one). v5.39.1 closes the **IR-emission shape mismatch**
  in the no-import case; v5.39.2 will close the **runtime SEGV
  in `__mn_map_get`** in the with-import case. After v5.39.2
  ships, v5.40.0 (Ai.\* — `ask` manifesto-arc kickoff) picks up
  cleanly. Adds **zero language features, zero new MIR ops,
  zero new IR shapes, zero new C runtime exports**. **Strict
  3-stage fixed point preserved by construction** at v5.39.0's
  **241,898 lines / 0 diff** (35-release strict streak from
  v5.7.1; zero `mapanare/self/*.mn` source touches). Goldens
  **95/95**.
  **The bug.** When user code calls `from_json::<T>(s)` without
  `import stdlib::encoding::json`, the lowerer emits
  `EnumPayload(variant="Object", ...)` for the `JsonValue`
  subject. The emitter at `_do_enum_payload`
  (`mapanare/emit_llvm_text.py:5187`) checks `if en in
  self._enums` — false because `JsonValue` was never
  registered. Falls into the Result/Option fallback's `else`
  branch which emits `extractvalue {i64, ptr} %enum, 1` — this
  yields a `ptr` (the boxed payload pointer) but `_put` tags
  the value with `dt = self._rty(i.dest.ty)` which is `i64`
  for an Int field. The next consumer fails IR validation:
  `'%pl.48' defined with type 'ptr' but expected 'i64'`.
  Latent since v5.36.0 Js.4 ship; the v5.36.0
  `tests/stdlib/test_struct_json.py` was compile-only
  (validated IR text generation, never linked) so the
  validation-time failure stayed hidden through v5.36.0 →
  v5.39.0.
  **Strategy A (audit-recommended) chosen.** New
  `_ensure_json_types_registered(self) -> None` helper at
  `mapanare/lower.py:2767` injects the canonical `JsonValue`
  (7 variants: Null, Bool(Bool), Int(Int), Float(Float),
  Str(String), Array(List<JsonValue>),
  Object(Map<String, JsonValue>)) and `JsonError` (3 fields:
  message: String, line: Int, col: Int) layouts into
  `self._module.enums` / `self._module.structs` when not
  already present. Idempotent — guarded with `if "JsonValue"
  not in self._module.enums`. Called at the top of
  `_lower_decode_to` AND `_lower_from_json` (the two
  Js.4-related entry points) so registration runs before any
  `EnumPayload` emission. Layout uses `MIRType(TypeInfo(...))`
  wrapping (matches the stored shape from
  `_register_declarations` at `lower.py:822-848`) and the
  `mir_int()` / `mir_string()` / `mir_bool()` factory helpers
  already imported at line 159-162 — no new imports needed.
  With `JsonValue` registered, the proper boxed-enum
  extraction path (`emit_llvm_text.py:5134-5185`) fires;
  downstream extraction is correct. Runtime SEGV in
  `__mn_map_get` remains — that's v5.39.2's whole release.
  **Strategy B (fix the emitter fallback)** held — narrower
  contract for the fallback path is the right invariant; the
  v5.39.2 runtime SEGV fix needs the Strategy A path anyway
  because `_is_self_ref` recursion only matters once
  `JsonValue` is properly registered.
  **Layout-drift guard** — `tests/stdlib/test_struct_json_layout.py`
  (2 cases) parses `stdlib/encoding/json.mn`, extracts the
  `JsonValue` enum + `JsonError` struct AST shape, asserts
  shape-for-shape match against the lower.py-injected canonical
  layout. If json.mn drifts (variant rename, field reorder,
  type change), the no-import path silently emits IR against
  the wrong shape — the with-import path keeps working,
  masking the divergence. The drift test fails loudly with a
  pointer to the lower.py update needed.
  **IR-shape regression test** —
  `tests/stdlib/test_struct_json_ir_shape.py` (4 cases):
  parametrized over Int / String / Bool single-field structs +
  one mixed Int+String case. Validates with `clang -c` (full
  IR validation, no link). Pre-fix all four fail with the exact
  `'%pl.NN' defined with type 'ptr' but expected ...` error
  shape; post-fix all four pass. The no-import case CANNOT
  link end-to-end (`decode` undefined without the json
  import) and that is correct, not a regression — runtime
  correctness for the with-import path is gated separately in
  v5.39.2's link-and-run suite. The pre-existing
  `tests/stdlib/test_struct_json.py` (20 compile-only cases)
  is preserved unchanged.
  **PROMPT/PLAN deviation (load-bearing) — Phase 2 self-host
  mirror N/A.** PROMPT/PLAN scoped a `mapanare/self/lower.mn`
  mirror as load-bearing for STRICT and budgeted ~1h.
  Phase 0 verification (`grep -rn "from_json\|decode_to"
  mapanare/self/`) returned zero matches: there is no
  `_lower_from_json` / `_lower_decode_to` in the self-host.
  The Js.4 surface (v5.36.0 Shape B — typed serde intrinsics)
  was Python-bootstrap-only and no self-host mirror has ever
  been shipped. STRICT preserved trivially by construction;
  v5.39.1 makes zero `mapanare/self/*.mn` source touches.
  Documented in `docs/roadmap/v5/v5.39.1/SESSION_REPORT.md`
  + CHANGELOG `### Changed`.
  **Falsifiability round-trip locked** — repro confirmed with
  `/tmp/serde_simple.mn` pre-fix; post-fix clean compile;
  reverted (`s/self._ensure_json_types_registered()/pass/g`),
  reproduced exact pre-fix error
  (`'%pl.48' defined with type 'ptr' but expected 'i64'`),
  reapplied, clean compile. v5.39.2 has the anchor when
  STRICT regressions surface from the deeper runtime fix.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.39.0 cut" to "v5.39.1 cut" with new sync block
  summarizing the Js.4.B.1 fix and the v5.39.1+v5.39.2 arc
  framing. `check_doc_freshness.py` GREEN.
  Source delta: ~50 LOC `mapanare/lower.py` (helper + 2 call
  sites) + ~165 LOC `tests/stdlib/test_struct_json_ir_shape.py`
  + ~115 LOC `tests/stdlib/test_struct_json_layout.py` +
  ~80 LOC CHANGELOG + ~25 LOC SPEC sync + this CLAUDE.md
  release-notes entry + mechanical bump_version.py edits.
  Aggregate state entering v5.39.2: **1 HIGH** (Js.4.B.2 —
  runtime SEGV in `__mn_map_get` when json import is present;
  arc continuation) / **1 MEDIUM** (macOS notarization;
  carry from v5.33.0 Nu.2) / ~6 LOW (carries unchanged from
  v5.39.0). See
  `docs/roadmap/v5/v5.39.1/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`
  and `docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md` for
  diagnosis artifacts.

- **v5.39.0** (ready, not tagged) — **Cr.\* — crypto stdlib
  hashing/MAC/random extensions; stdlib gap-close arc CLOSED.**
  Sixth and final release in the stdlib gap-close arc
  (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0, Ht.\* @
  v5.37.0, Re.\* @ v5.38.0, Cr.\* @ v5.39.0). **Staged scope
  (deviation from PLAN, lead-approved at Phase 0).** v5.39.0
  ships the easy hashing / streaming / random additions on top
  of the pre-existing `stdlib/crypto.mn` (283 LOC; SHA-1/256/512
  + HMAC-SHA256 + Base64 + Hex + JWT HS256 + random_bytes
  already shipped). AEAD (AES-GCM, ChaCha20-Poly1305 +
  NonceCounter helper), Ed25519 + X25519, and password KDFs
  (PBKDF2, HKDF, Argon2id with explicit-Err fallback) explicitly
  deferred to v5.39.1. Reason: each has its own correctness trap
  (GCM nonce reuse, Ed25519 key serialization, Argon2 OpenSSL
  major-version skew); bundling with the easy hashing additions
  raises the chance one ships subtly wrong, and they are
  structurally independent. **Strict 3-stage fixed point
  preserved by construction at v5.38.0's 241,898 lines / 0 diff**
  (35-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **Cr.1 hashing additions:** `sha3_256` (FIPS 202; OpenSSL
  1.1.1+), `blake2b` (RFC 7693; 1.1.0+) with `_raw` variants;
  optional symbols, return empty string on older libcrypto.
  **Cr.1 streaming digest:** `DigestCtx { handle, algo }` opaque
  struct + `digest_new(algo) -> Option<DigestCtx>`,
  `digest_update`, `digest_finalize` (hex / `_raw`). Algo IDs:
  1=SHA-256, 2=SHA-512, 3=SHA-3-256, 4=BLAKE2b. Helper functions
  `algo_sha256()` / `algo_sha512()` / `algo_sha3_256()` /
  `algo_blake2b()` (Mapanare does not yet support top-level
  `const` declarations as of v5.39.0 — minor parser ergonomics
  candidate for v5.40+). Caller MUST call `_finalize` exactly
  once; finalize frees the underlying EVP_MD_CTX* regardless of
  success. Handle = `(int64_t)(intptr_t)ctx` direct cast.
  **Cr.2 HMAC additions:** `hmac_sha512` + `_raw` variant.
  `constant_time_eq(a, b) -> Bool` for timing-safe MAC verify;
  prefers OpenSSL `CRYPTO_memcmp`, falls back to a
  volatile-masked aggregation loop. Streaming `HmacCtx` with
  algo 1 (SHA-256) or 2 (SHA-512); HMAC over SHA-3 / BLAKE2 is
  v5.40.x+ via `EVP_MAC` migration.
  **Cr.5 random extensions:** `random_u64()` reads 8 bytes from
  `random_bytes` packed big-endian; `random_range(low, high)`
  uses rejection sampling to avoid modulo bias. Degenerate
  `random_range(5, 5)` returns 5; `random_range(10, 5)` returns
  low. No new C-runtime exports — both derive from
  `__mn_random_bytes_str`.
  **Cr.7 RFC test corpus:** new
  `stdlib/crypto/tests/test_crypto_smoke.mn` (~190 LOC, surface
  smoke + streaming chunked-vs-one-shot equivalence + random
  distribution sanity) and `test_crypto_corpus.mn` (~110 LOC,
  RFC 6234 SHA-256 / SHA-512, FIPS 202 SHA-3-256, RFC 7693
  BLAKE2b-512, RFC 4231 HMAC tests 1, 2, 4, 5). Pytest harness
  `tests/stdlib/test_crypto_runtime.py` (~165 LOC) mirrors the
  v5.34 / v5.35 / v5.38 concatenation pattern: prepend
  `stdlib/crypto.mn`, compile via Python LLVM emitter, link
  against `libmapanare_rt.a`, run, assert "PASSED". **3/3 GREEN.**
  Pre-existing `tests/stdlib/test_crypto.py` (40 compile-only
  cases) preserved unchanged.
  **Cr.8 C runtime extensions** in `runtime/native/mapanare_io.c`
  (NOT a separate `mapanare_crypto.c` — PLAN's `mapanare_tls.c`
  reference is wrong; OpenSSL plumbing already lives in
  `mapanare_io.c`, same wrap-don't-duplicate decision as v5.35.0
  Sq.7 with `mapanare_db.c`). Ten new `__mn_*` exports appended
  at end of existing crypto block: `__mn_sha3_256_str`,
  `__mn_blake2b_str`, `__mn_hmac_sha512_str`,
  `__mn_constant_time_eq`, `__mn_md_ctx_new`,
  `__mn_md_ctx_update`, `__mn_md_ctx_finalize`,
  `__mn_hmac_ctx_new`, `__mn_hmac_ctx_update`,
  `__mn_hmac_ctx_finalize`. ABI-stable: appended, not inserted;
  stage1 binaries built against pre-v5.39.0 runtime keep working.
  Five new EVP function pointers (`EVP_sha3_256`,
  `EVP_blake2b512`, `CRYPTO_memcmp`, plus `HMAC_CTX_*` legacy
  set) wired into `s_evp` struct as **optional** (NULL is
  legitimate; callers gate at runtime). `evp_load()` resolution
  block extended; required-symbols gate unchanged.
  **Cr.9 docs** — new `docs/stdlib/crypto.md` (~290 LOC):
  quick reference, type/API reference, 5 cookbook recipes
  (one-shot hash, chunked stream hash, timing-safe MAC verify,
  BLAKE2b for keyed hashing, jitter via `random_range`),
  "what's not here yet" v5.39.1 plan, compatibility note for
  the Cr.0 emitter fix.
  **Cr.0 emitter shortcut fix (LOAD-BEARING)** —
  `mapanare/emit_llvm_text.py` had unconditional builtin
  shortcuts at lines 3713-3776 for `sha256`, `hmac_sha256`,
  `base64_encode`, `base64_decode`, `hex_encode`, `random_bytes`,
  `regex_match`, `regex_replace`, `http_get`. These shortcuts
  called the underlying `__mn_*_str` C exports directly,
  bypassing the user-defined wrappers in `stdlib/crypto.mn` /
  `stdlib/text/regex.mn` that hex-encode the output / wrap in
  Result types. When MIR inlining failed (high call-site count
  or function-size threshold), the shortcut won and silently
  changed the return shape — `sha256(x)` returned 32 raw bytes
  instead of 64 hex chars; `hmac_sha256(k, m)` returned 32 raw
  bytes instead of hex. Surfaced by the new RFC corpus tests
  with 5 `hmac_sha256` callsites: 4 returned raw, 1 (the only
  call from inside `hmac_sha256`'s own user-defined chain)
  inlined cleanly. The corresponding `hmac_sha512` callsites
  (no shortcut existed) returned hex correctly — the
  asymmetric-failure pattern was the diagnostic. Latent bug
  since v3.42.0 (when the shortcuts were introduced; user-defined
  `stdlib/crypto.mn` wrappers came later). **Fix:** gate each
  shortcut on `fn not in self._sigs`, deferring to the
  user-defined wrapper when one exists. ~10 LOC change. No
  callers depended on the shortcut's raw-bytes return — raw
  access has always been spelled `sha256_raw` / `hmac_sha256_raw`
  in the stdlib. Pre-existing `test_crypto.py` (40) +
  `test_regex.py` (32) all green; broader stdlib sweep 1001 PASS;
  goldens 95/95 preserved; STRICT fixed point preserved.
  **Cr.0 belongs to the same bug-class as v5.36.0 Js.0**
  (`emit_llvm_text.py` `_san` sanitizer over-stripping `%`)
  and v5.36.0 Js.0.B (Result wrap-shape mismatch) — emitter
  bugs surfaced by extending the stdlib in ways that exercise
  more code paths.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.38.0 cut" to "v5.39.0 cut" with new sync block
  summarizing Cr.\* additions (specifically enumerating the 10
  new C runtime exports and the Cr.0 emitter fix; runtime-additions
  count is the highest since v5.34.0 Dt.\*).
  `check_doc_freshness.py` GREEN. `check_changelog_honesty.py`
  GREEN. Source delta: ~165 LOC C in `mapanare_io.c` (Cr.1 + Cr.2
  + Cr.8) + ~235 LOC `stdlib/crypto.mn` extensions (Cr.1 + Cr.2 +
  Cr.5) + ~300 LOC `.mn` tests (Cr.7) + ~165 LOC pytest harness
  + ~290 LOC `docs/stdlib/crypto.md` (Cr.9) + ~10 LOC
  `mapanare/emit_llvm_text.py` (Cr.0) + ~85 LOC CHANGELOG +
  ~35 LOC SPEC sync + CLAUDE.md release-notes entry +
  mechanical bump_version.py edits.
  Aggregate state entering v5.39.1: **0 HIGH** (the hard items
  Cr.3 + Cr.4 + Cr.6 are explicitly named for v5.39.1, not
  carried forward as HIGH) / **1 MEDIUM** (macOS notarization,
  carry from v5.33.0 Nu.2) / ~6 LOW (EVP_MAC migration, native
  Bytes type, HMAC over SHA-3/BLAKE2, JWT verify routing through
  constant_time_eq, Pike VM regex rewrite candidate, regex_replace
  single-shot follow-up from v5.38.0). **Stdlib gap-close arc
  CLOSED.** Manifesto arc begins v5.40.0 with `ask` (the user's
  v5.40.0 PROMPT will reference Cr.\* surface for HMAC-signed
  API key handling). See
  `docs/roadmap/v5/v5.39.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
  SESSION_REPORT.md}`.

- **v5.38.0** (ready, not tagged) — **Re.\* — regex stdlib
  closeout.** Fifth release in the stdlib gap-close arc
  (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0, Ht.\* @
  v5.37.0, Re.\* @ v5.38.0). **Zero compiler edits. Zero new
  C runtime exports. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.37.0's **241,898 lines / 0 diff** (33-release strict
  streak from v5.7.1). Goldens **95/95**. v5.38.0 audited the
  pre-existing PCRE2-backed `stdlib/text/regex.mn` (271 LOC,
  shipped at v0.9.0), fixed two pre-existing parse / lowering
  bugs that had silently broken the module at HEAD, and
  extended the surface with a `Regex`-first compile-once API
  plus a `Captures` type with named-group lookup.
  **Phase 0 deviation from PLAN (load-bearing).** PLAN
  specified "net-new module at `stdlib/regex/`, ~600 LOC Pike
  VM"; Phase 0 audit established that a complete PCRE2 wrapper
  was already shipped. Audit committed at
  `docs/roadmap/v5/v5.38.0/PRE_PHASE_AUDIT.md`, surfaced to
  lead, **lead approved keeping PCRE2** (Pike VM rewrite is a
  v6.0+ candidate). Same pattern as v5.34.0 / v5.35.0 / v5.37.0
  — Phase-0-driven scope correction toward the right
  deliverable for the release window.
  **Re.1+Re.2 — Regex-first API**:
  `regex_is_match(r, s) -> Bool`,
  `regex_find(r, s) -> Option<Match>`,
  `regex_find_all(r, s) -> List<Match>`,
  `regex_replace(r, s, repl) -> String`,
  `regex_replace_all(r, s, repl) -> String`,
  `regex_free(r) -> Regex`. The pre-existing pattern-string-
  first free-function API (`regex_match`, `find_all`,
  `replace`, `replace_all`, `regex_split`, `is_match`) is
  **preserved unchanged**.
  **Re.3 — Captures + named groups**: new `NamePair` and
  `Captures` types; `regex_captures(r, s) -> Option<Captures>`;
  `regex_captures_iter(r, s) -> List<Captures>`;
  `captures_get(c, idx) -> Option<String>`;
  `captures_get_named(c, name) -> Option<String>`;
  `captures_count(c) -> Int`. Named groups parse
  `(?P<name>...)` and `(?<name>...)` in pattern source via the
  new `parse_named_groups` walker (Path A — no new C runtime
  exports). Walker handles escapes, character classes,
  non-capturing groups, lookarounds, atomic groups, inline
  flags, and comments. **`Captures` stores group state as
  parallel `List<String> + List<Bool>`** rather than
  `List<Option<String>>` to sidestep the v5.x drop-glue carry
  on `List<Option<X>>` appends (`snapshot_all_groups` hung in
  early testing); public `captures_get` surface preserves
  `Option<String>` so callers don't see the workaround.
  **Backref-bearing replacements work natively** — PCRE2's
  default `pcre2_substitute` recognizes `$0..$9`, `${name}`,
  and `$$` without `PCRE2_SUBSTITUTE_EXTENDED`; existing C
  wrapper at `runtime/native/mapanare_io.c` passes the right
  options. Pattern-side backreferences (`\1`) remain
  out-of-scope (NP-complete).
  **Re.4 — runtime test corpus**:
  `stdlib/text/tests/test_regex_smoke.mn` (10 sections,
  ~270 LOC) covers compile happy + error paths,
  `regex_is_match`, `regex_captures` named-group extraction,
  numbered-group access, unknown-name handling,
  `captures_count`, `captures_iter`, `regex_replace_all`
  with `$1`/`$2`, named backref via `${name}`, `$$` literal
  escape. `stdlib/text/tests/test_regex_corpus.mn` (~150 LOC,
  ~40 cases) covers literals + `.`, quantifiers, anchors,
  character classes, alternation, non-capturing groups,
  capture groups (numbered), inline flag `(?i)`, `find_all`
  count assertions, `replace_all` edge cases. Pytest harness
  `tests/stdlib/test_text_regex.py` mirrors v5.34/v5.35
  concatenation pattern (read regex module, prepend to test
  main body, compile via Python LLVM emitter, link against
  `libmapanare_rt.a`, run, assert "PASSED"). Gated on
  `libpcre2-8` dlopen target. **3/3 GREEN.**
  **Re.5 — `docs/stdlib/regex.md`** (~360 LOC): pattern
  syntax reference, type / API reference, 6 cookbook recipes
  (compile-once match-many; extract named fields; swap pairs
  via `$1`/`$2`; replace via named backref; iterate matches
  with groups; case-insensitive via `(?i)`), deviation notes,
  migration note from the pre-v5.38.0 surface.
  **Two pre-existing bugs fixed in v5.38.0** (both
  silently-broken-at-HEAD, would have failed the user's first
  attempt to use regex from a fresh clone): (1) 17 occurrences
  of `pon _: Int = ...` (the parser does not accept `_` as a
  binding name) — renamed to `pon _drop: Int = ...`; (2)
  `parse_named_groups` underlying `String.substr(start, count)`
  semantics — Mapanare's `substr` third arg is a **count**, not
  an exclusive end-index. The pre-existing `regex_split` at
  lines 235/242 has the same shape `text.substr(offset,
  text_len)` — over-reads past string end, mitigated by PCRE2
  capping bounds; latent silent over-read, not a visible crash.
  **Re.6 — new MEDIUM (deferred)**: `pon m: Option<Match> =
  regex_match(...)` allocates `m` as `i1` instead of as the
  `Option<Match>` aggregate (same bug class as v5.36.0 Js.0.B
  / v5.26.1 Eu.\*). Reproduces standalone with no v5.38.0
  additions involved. Out of scope — fix needed in
  `mapanare/lower.py` / `emit_llvm_text.py`, not in the regex
  module. The v5.38.0 Regex-first API does not trigger this
  bug because `Regex` (not `Option<Match>`) is the local type.
  **`regex_replace` (single-shot) returns subject unchanged**
  on multi-match input — underlying C wrapper without
  `PCRE2_SUBSTITUTE_GLOBAL` does not substitute under current
  testing. v5.38.x follow-up; `regex_replace_all` validated.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced
  from "v5.37.0 cut" to "v5.38.0 cut" with new sync block
  summarizing what v5.38.0 ships. `check_doc_freshness.py`
  GREEN. Source delta: ~461 LOC `stdlib/text/regex.mn` (Re.\*
  surface) + ~270 LOC `test_regex_smoke.mn` + ~150 LOC
  `test_regex_corpus.mn` + ~170 LOC pytest harness + ~360 LOC
  `docs/stdlib/regex.md` + CHANGELOG / CLAUDE.md / SPEC sync /
  mechanical bump_version.py edits. Aggregate state entering
  v5.39.0: **0 HIGH** / **3 MEDIUM** (Re.6 new, Ht.5 typed
  handler waits on Js.4.B, macOS notarization carry from
  v5.33.0 Nu.2) / ~9 LOW (Pike VM rewrite candidate added,
  `regex_replace` single-shot follow-up, Rust regex corpus
  port, plus v5.37.0 carries). See
  `docs/roadmap/v5/v5.38.0/{PLAN.md, PROMPT.md,
  PRE_PHASE_AUDIT.md, SESSION_REPORT.md}`.

- **v5.37.0** (ready, not tagged) — **Ht.\* — HTTP App / router /
  middleware / streaming encoders.** Fourth release in the stdlib
  gap-close arc (Dt.\* @ v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0,
  Ht.\* @ v5.37.0). New `stdlib/net/http/router.mn` ships an opt-in
  `App` container bundling a path-pattern router (`:name`
  parameters + `*name` wildcards alongside literals; method
  dispatch GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS) with a
  **registration-table middleware** list (Logger / Cors /
  BodyLimit / RequestId / Custom). New
  `stdlib/net/http/streaming.mn` ships RFC 7230 §4.1 chunked
  transfer encoding plus a Server-Sent Events encoder. **Zero
  compiler edits. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.36.0's **241,898 lines / 0 diff** (32-release strict streak
  from v5.7.1). Goldens **95/95**. Twenty-nine new pytest
  assertions across 3 `.mn` test files: 12 router + 6 middleware
  + 11 streaming, all GREEN; pytest harness
  `tests/stdlib/test_http_router.py` mirrors the v5.34/v5.35
  concatenation pattern. The legacy `stdlib/net/http/server.mn`
  `Router` (string-named handlers, `${name}` syntax) is
  **preserved unchanged** — existing pytest coverage in
  `tests/stdlib/test_http_server.py` keeps passing; the v5.37.0
  surface is opt-in via the new module. **Five PROMPT deviations,
  all load-bearing, all structurally driven, all surfaced in
  Phase 0.** **(1) Ht.2 — registration table, not closure
  chain.** PROMPT specified `type Middleware = fn(Request, Next)
  -> Response`. Phase-0 spike confirmed both backends fail on
  indirect calls through fn-typed parameters: native
  `mnc-stage1` produces invalid IR (`use of undefined value`);
  Python LLVM emitter links cleanly but **SEGVs at runtime**.
  Same root cause as v5.35.0's deferred
  `transaction<T>(f: fn() -> ...)` shape. v5.37.0 ships the
  registration-table form (Middleware enum variants); custom
  middleware via `Custom(name)` dispatched through a user-
  written `dispatch_custom_middleware_before` switch. Closure-
  chain shape is a v5.38.0+ candidate. **(2) Ht.1 — ordered
  list of compiled patterns, not recursive trie.** Functionally
  equivalent — same API surface, same priority rule (literal >
  parameter > wildcard, locked with explicit overlap tests),
  same big-O on small route counts. Removes a recursion risk
  in the MIR lowerer that the v5.37.0 release scope did not
  budget for. **(3) Ht.3 ships as documentation only.**
  `stdlib/net/websocket.mn` already had a complete RFC 6455
  client + server (`ws_accept_upgrade`, `ws_recv_full` with
  fragmentation, masking, control-frame size cap, UTF-8
  validation, `wss://` over TLS, `ws_echo_loop`). The PROMPT's
  `stdlib/net/http/ws.mn` would have been a redundant wrapper.
  Cookbook in `docs/stdlib/http.md` shows the integration path.
  Autobahn fixture corpus deferred to v5.38.0+ as **Ht.3.B**.
  **(4) Ht.4 — encoders, not bounded-RSS streamer.** Existing
  `__mn_tcp_send_str(fd, data: String)` C-runtime export takes
  a whole string; a real bounded-RSS streaming writer needs
  `__mn_tcp_send_bytes(fd, ptr, len)` plus a chunk-pump driver
  loop. v5.37.0 ships *encoders* (`chunked_encode`,
  `build_chunked_response`, `SseLite` + `sse_lite_encode_stream`)
  that produce wire-format strings; the wire format is identical
  to what the eventual streamer will write. Pump driver is
  **Ht.4.B** for v5.38.0+. **(5) Ht.5 deferred** pending Js.4.B
  drop-glue fix from v5.36.0 carry. `from_json::<T>` builds
  successfully but SEGVs at runtime in field extraction;
  without working `from_json::<T>` the typed-handler-shorthand
  auto-deserialization has no mechanism. v5.36.x will close
  Js.4.B; v5.38.0+ picks Ht.5 back up. **Headers stored as
  `List<String>` alternating-kv** (not `Map<String, String>`)
  in `Request`, `Response`, and middleware return shapes —
  same v5.x map-in-returned-payload drop-glue motivation as
  `MatchedRoute.params_kv`; helpers `hdr_get` / `hdr_set` /
  `hdr_has` provide the standard Map-style operations on top.
  Five v5.x carry-forward bug-classes documented in source-file
  preambles + CHANGELOG `### Changed`: multi-line struct literals
  not parsed (single-line workaround); `for x in some_list` not
  lowered (index-based `while i < len(xs)` workaround); string-
  aliasing on `xs = xs + [cur]; cur = mut` (snapshot via
  `let snap = cur + ""`); `Map<String, String>` drop-glue in
  returned struct/enum (replace with `List<String>` kv); fn-
  value parameter invocation broken (registration-table dispatch
  instead of closure chain). **Hd-class preventative** —
  `docs/SPEC.md` header re-synced from "v5.36.0 cut" to
  "v5.37.0 cut" with new sync block summarizing what v5.37.0
  ships. `check_doc_freshness.py` GREEN. Source delta: ~600
  LOC `stdlib/net/http/router.mn`, ~250 LOC
  `stdlib/net/http/streaming.mn`, ~400 LOC `.mn` tests, ~110
  LOC pytest harness, ~150 LOC walkthrough example, ~360 LOC
  `docs/stdlib/http.md`, plus CHANGELOG / CLAUDE.md / SPEC sync
  / mechanical bump_version.py edits. Aggregate state entering
  v5.38.0: **0 HIGH** / **2 MEDIUM** (Ht.5 typed handler waits
  on Js.4.B; macOS notarization carry from v5.33.0 Nu.2) / ~7
  LOW (Ht.3.B Autobahn corpus, Ht.4.B bounded-RSS streamer,
  closure-chain middleware, native `Bytes` type,
  `Map<String, String>` drop-glue, plus v5.36.0+ carries).
  See `docs/roadmap/v5/v5.37.0/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md}`.

- **v5.36.0** (ready, not tagged) — **Js.\* — JSON completeness
  arc.** Third release in the stdlib gap-close arc (Dt.\* @
  v5.34.0, Sq.\* @ v5.35.0, Js.\* @ v5.36.0); these three are the
  prerequisites named for v5.40.0 `ask`. **Strict 3-stage fixed
  point preserved by construction at v5.35.0's 241,898 lines / 0
  diff** (31-release strict streak from v5.7.1; zero
  `mapanare/self/*.mn` source touches). Goldens **95/95**.
  **Js.1 — JSON parser is now RFC 8259 strict.** Inputs that
  previously parsed silently and now error: leading-zero numbers
  (`01`, `-01`, `00.5`); unescaped control chars in strings (bytes
  U+0000..U+001F including embedded `\n`/`\t`/`\r`); documents
  nesting deeper than 256 levels (was a SEGV pre-fix on inputs
  like `[[[...]]]` × 100k). 8 nst/JSONTestSuite fixtures moved
  from broken to conformant; final corpus state **283 CONFORM /
  35 IMPL / 0 DEVIATE / 0 CRASH = 318**. Strict mode is **not
  opt-out** at this release — no `JsonParseOpts { strict: false }`
  flag yet. Documented in `### Changed` (potentially
  breaking-ish) per CHANGELOG honesty rule. **Js.2** —
  `to_json_pretty(value, indent)` configurable indent (was
  hardcoded 2 spaces); `indent <= 0` falls through to compact
  `to_json` byte-for-byte. New aliases `to_json` / `to_json_pretty`
  / `parse` mirror existing `encode` / `encode_pretty` / `decode`.
  **Js.3 (LITE)** — pull-based streaming API
  (`JsonStreamParser`, `JsonStreamStep`, `json_stream_open`,
  `json_stream_next`, `json_stream_error`) on top of the existing
  batch parser. Ships the API contract; true chunked I/O with
  peak-RSS-bounded streaming deferred to a release that adds a
  native `Bytes` type. **Js.4 (Shape B) — typed serde
  intrinsics `to_json::<T>` and `from_json::<T>`** as compile-time
  monomorphized aliases of existing `encode_struct::<T>` /
  `decode_to::<T>`. **`to_json::<T>` works end-to-end** at this
  release (verified `Point{3,4}` → `{"x": 3, "y": 4}`).
  **`from_json::<T>` builds successfully but SEGVs at runtime**
  in field-extraction (a pre-existing v5.x drop-glue bug
  uncovered by the Js.0.B fix). API surface is in place so
  v5.40.0 `ask` work can build against it; runtime fix tracked
  as **Js.4.B for v5.36.1**. **Phase 0 user decision**: Shape B
  (extend existing intrinsics) over Shape A (build runtime
  reflection from scratch — would have been 3-5 release
  sessions). PROMPT/PLAN claimed runtime type metadata existed at
  `runtime/native/mapanare_typeinfo.c` "or inlined in
  mapanare_core.c"; verified empirically that `print(struct)`
  literally just emits `printf("%lld\n", first_field)` with no
  field iteration — runtime metadata does not exist. **Js.5** —
  `tests/stdlib/test_json_corpus_baseline.py` regression gate
  asserting CONFORM ≥ 283 / DEVIATE ≤ 0 / CRASH ≤ 0. Marked
  `pytest.mark.slow`. **Js.7** — `docs/stdlib/json.md` user-
  facing reference. Documents strictness changes, every public
  API, the Js.3-LITE memory characteristic, and Js.4.B
  explicitly so callers know what they can rely on.
  **Js.6 sqlite integration deferred to v5.36.1** — was scoped
  to add `Value::Json(JsonValue)` variant requiring
  `from_json::<JsonValue>` runtime path, blocked by Js.4.B.
  **Two compiler bug-fixes uncovered during the work and shipped
  in-release.** **Js.0** (`mapanare/emit_llvm_text.py:1421`):
  `_san` sanitizer used `nm.lstrip("%")` (only leading) but
  callers interpolated names into compound IDs like
  `f"_map_iter_{value.name}"`; embedded `%` survived
  sanitization → invalid IR (`%_map_iter_%entries37.addr`).
  1-line fix: strip ALL `%`, not just leading. Goldens 95/95
  preserved. **Required for any end-to-end test of the existing
  json.mn module to work** (the bug surfaced as soon as Phase 0
  tried to build the corpus runner). **Js.0.B**
  (`mapanare/emit_llvm_text.py:5214` / `:5223`):
  `_do_wrap_ok` / `_do_wrap_err` hardcoded the unfilled side of
  the Result struct as `ptr`, producing `{i1, {ok_ty, ptr}}` when
  the consumer expected `{i1, {ok_ty, err_ty}}`. Mismatch invisible
  until Phi merge of two arms with full type info hit a size
  conflict. Fix uses dest's `Result.args` when available (kind
  == RESULT and len(args) ≥ 2); falls back to legacy shape
  otherwise. Required for Js.4 `from_json::<T>` to even build.
  **Bb.\*: NOT required** (no C-runtime export changes). **Hd-
  class preventative**: SPEC.md header re-synced from "v5.35.0
  cut" to "v5.36.0 cut" with new sync block summarizing what
  v5.36.0 ships (specifically calling out Js.1 as `### Changed`
  / potentially breaking-ish; Js.4.B as the load-bearing
  deferred fix for v5.40.0 `ask`). `check_doc_freshness.py`
  GREEN. **Vendored RFC 8259 corpus is gitignored** at
  `stdlib/json/tests/fixtures/rfc8259/`; `scripts/run_json_corpus.py`
  clones nst/JSONTestSuite on demand if missing. Aggregate state
  entering v5.37.0: **0 HIGH** / **1 MEDIUM** (Js.4.B
  `decode_to`/`from_json` runtime SEGV; macOS notarization carry
  from v5.33.0 Nu.2) / ~6 LOW (native `Bytes` type, Js.6 sqlite
  paired with Js.4.B, field-type coverage extension paired with
  Js.4.B, `JsonParseOpts` opt-out, multi-line struct literal
  syntax, v5.x match-cleanup SEGV, cyclic-struct detection).
  See `docs/roadmap/v5/v5.36.0/{PLAN.md, PROMPT.md,
  SESSION_REPORT.md, RFC_AUDIT.md}`.

- **v5.35.0** (ready, not tagged) — **Sq.\* — first-class SQLite3
  stdlib driver + Tn.1 closure.** Closes the persistence gap.
  Net-new `stdlib/sql/sqlite.mn` (~720 LOC) wraps the existing
  v5.34.x `mapanare_db.c` sqlite exports plus 8 new ones added at
  Sq.7 (`__mn_sqlite3_libversion`, `_bind_blob`, `_column_blob`,
  `_reset`, `_bind_parameter_index`, `_changes`,
  `_last_insert_rowid`, `_extended_errcode`). **Zero compiler
  edits. Zero `mapanare/self/*.mn` source touches.** Strict 3-stage
  fixed point preserved by construction at v5.34.0's **241,898
  lines / 0 diff** (30-release strict streak from the v5.7.1
  baseline). Goldens **95/95**. Surface: `Database`, `Statement`,
  `Value` (7 variants: Null/Int/Float/Text/Blob/Bool/DateTime),
  `SqlError` (8 variants with retry/recovery semantics —
  `LoadFail`, `VersionTooOld(String)`, `BadSql(String)`,
  `TypeMismatch(String)`, `Constraint(String)`, `Busy`, `Misuse`,
  `Closed`), `SavepointHandle` for nested transactions. Typed
  `column<T>` with mismatch detection; named parameter binding via
  `:name` / `@name` / `$name`; explicit transaction primitives
  (`database_begin / commit / rollback`) plus `SavepointHandle`-
  based nesting; blob support carrying raw bytes through `String`;
  `database_open` does a `>= 3.7.0` libsqlite3 version check via
  the new `sqlite3_libversion` export.
  **Sq.0 (formerly Tn.1) — closure of v5.28.0 RE-PANEL directive
  carried 6 releases.** New `tests/llvm/test_llvm_link_all.py`
  generalizes the v5.26.0 link-and-run pattern from 10 goldens
  (the async cluster + 4 v5.26.1 Eu.\* deferred goldens) to all
  95. 96/96 PASS at HEAD in 8s on 32 workers. Closes the structural
  test gap that hid Eu.1..Eu.4 LINK_FAIL bugs for 3 releases (v5.23.1
  → v5.26.0 Phase 0 audit).
  **Bundled-vs-staged-as-Sq.0 decision.** v5.35.0 PROMPT scoped
  Tn.1 as a hard-gate precondition that should ship as a v5.34.1
  hotfix. After surfacing this at Phase 0, the user directed
  bundle-into-v5.35.0 — preserves deadline integrity (Tn.1 was
  named DEADLINE-at-v5.35.0 in v5.33.0 directive) without spending
  a release slot. Tradeoff: substantive Sq.\* arc + tiny mechanical
  test ship together; honesty cost paid in this release-notes
  entry + SESSION_REPORT explicitly calling out Sq.0's prior
  Tn.1 identity.
  **Sq.6 tests.** 5 `.mn` test files under
  `stdlib/sql/sqlite/tests/` + new pytest harness
  `tests/stdlib/test_sq_sqlite.py` (mirrors the v5.34.0 Dt.\*
  concatenation pattern: read `stdlib/sql/sqlite.mn`, prepend to
  each `.mn` test main body, compile via Python LLVM emitter, link
  against `libmapanare_rt.a`, run, assert `"PASSED"` in stdout).
  7/7 GREEN at HEAD (5 .mn tests + parses-clean + typechecks-clean)
  in 3.98s. Tests cover: Sq.1 lifecycle (open / close idempotent
  / libversion non-empty); Sq.1+2 full CRUD with named-param
  binding; Sq.4 commit + rollback + nested SAVEPOINT (mid-tx
  count → post-commit count → savepoint rollback discards inner
  inserts but outer commit retains); Sq.2+5 manual prepared-stmt
  reuse via `reset+bind+step` over 200 iterations in a single
  transaction; Sq.1+2+3 SqlError variant coverage including
  Constraint extended-rc mapping (UNIQUE = 2067, PRIMARYKEY =
  1555 propagated through the message string).
  **Sq.7 C shim — extends, doesn't duplicate.** Phase 1
  discovery: `runtime/native/mapanare_db.c` already had complete
  sqlite3 dlopen plumbing (877 LOC, 18 function pointers, full
  `SQLITE_SYM(...)` resolution) — the PROMPT's "create net-new
  `mapanare_sqlite.c` (~150 LOC)" was based on incomplete reading
  of the existing runtime. User directed wrap-don't-duplicate;
  Sq.7 added 8 new function pointers + 8 new wrapper functions
  to the existing `s_sqlite` struct + `sqlite3_load()` resolver.
  ~80 LOC of new C, no new source files. Build path unchanged
  (`mapanare_db.c` already in `Makefile` `RUNTIME_SOURCES`). C
  smoke harness at `/tmp/sq7_smoke.c` (6 cases including blob
  round-trip with embedded NUL, named-param resolution,
  duplicate-INSERT extended errcode) PASS against system
  libsqlite3 3.45.1.
  **Sq.8 Windows DLL bundle.** `.github/workflows/publish.yml`
  Windows `build-cli` path now downloads pinned
  `https://www.sqlite.org/2024/sqlite-dll-win-x64-3460100.zip`
  (SQLite 3.46.1), extracts and stages
  `dist/mapanare/bin/sqlite3.dll`. Three guards: MZ-header check
  (catches HTML-error-as-DLL); 500 KB ≤ size ≤ 5 MB (catches
  partial download / wrong file); explicit version-string
  variable in the shell that future bumps must update with the
  URL. Linux + macOS use system libsqlite3 (Ubuntu 20.04+ ships
  3.31+; macOS 13+ ships 3.39+).
  **Sq.9 docs.** `docs/stdlib/sql.md` (~370 lines) — quick
  reference, types, 7 cookbook recipes (open + create + insert +
  read on `:memory:`; on-disk database; transaction-wrapped
  batch insert with the perf-explanation; manual prepared-stmt
  reuse with the Sq.5-deferred note; `match SqlError` for
  retry/recovery; blob handling; Sq.3.B JSON preview with
  forward link to v5.36.0 Js.\*); deviations explicitly listed;
  migration / coexistence note from existing `stdlib/db/sqlite.mn`;
  Sq.8 Windows DLL distribution policy.
  **Five PLAN deviations (all load-bearing, all structurally
  driven).** (1) Single-file module instead of directory layout
  — same lesson as v5.34.0 `stdlib/time.mn`, blocked on cross-
  module mangling/extern-propagation fix. (2) `Value::Blob(String)`
  not `Value::Blob(Bytes)` — Mapanare has no native `Bytes` type;
  v5.36.0 Js.\* arc may introduce one. (3) Explicit transaction
  primitives + `SavepointHandle` instead of `transaction<T>(\|\|
  ...)` closure wrapper — Mapanare stdlib has no precedent for
  generic-closure-arg functions. (4) Sq.5 statement cache deferred
  to v5.36.0 — without first-class state mutation across function
  calls + `Map<K,V>` ergonomics, the auto-cache API is uglier
  than the manual `prepare-once + reset+bind+step` path that
  produces the same 5-10× speedup. (5) Sq.7 wraps existing
  `mapanare_db.c` instead of new `mapanare_sqlite.c` — Phase 1
  scope discovery, surfaced to user, accepted.
  **Hd-class preventative.** `docs/SPEC.md` header re-synced from
  "synced to the v5.34.0 cut" to "synced to the v5.35.0 cut" with
  a new sync block summarizing what v5.35.0 ships (specifically
  enumerating the 8 new C runtime functions in `mapanare_db.c`).
  `check_doc_freshness.py` GREEN.
  Aggregate state entering v5.36.0: **0 HIGH** (Tn.1 closed) /
  **1 MEDIUM** (macOS notarization carry from v5.33.0 Nu.2) /
  ~9 LOW (Sq.5 cache deferred, native `Bytes` type, closure-arg
  transaction wrapper, PostgreSQL/MySQL typed wrappers, schema
  migrations + ORM, async sqlite, cross-module emitter fix,
  carry from v5.34.0). The existing v5.34.x `stdlib/db/sqlite.mn`
  is **untouched**; both drivers coexist (the older one routes
  through `Connection` / unified SQL URLs; the new
  `stdlib/sql/sqlite.mn` is the typed-`column<T>` + named-param
  surface).
  See `docs/roadmap/v5/v5.35.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.34.0** (ready, not tagged) — **Dt.\* — first-class date /
  time stdlib.** First stdlib expansion since v5.21.0. **Zero
  compiler edits. Zero `mapanare/self/*.mn` source touches.**
  Strict 3-stage fixed point preserved by construction at
  v5.33.x's **241,898 lines / 0 diff** (29-release strict streak
  from the v5.7.1 baseline). Goldens **95/95**. Net-new
  `stdlib/time.mn` (~723 LOC) shipping `Date`, `Time`, `DateTime`,
  `Duration`, `Timezone` types with construction-time validation
  (rejects `2026-13-03`, `1900-02-29`, year out of `[1, 9999]`);
  ISO 8601 + RFC 3339 parse/format with strftime specifier subset
  (`%Y %m %d %H %M %S %z %Z %%`); arithmetic with month/day
  rollover and leap-year handling; v0 timezone surface (UTC +
  system-local; `tz_named("America/Lima")` returns explicit
  `Err("named tzdb not yet supported: ...")` — non-negotiable
  defer per PLAN, silent fallback to UTC is the bug-class that
  bites real users). All v5.33.x flat-file surface (`Stopwatch`,
  `now_ns`, `format_duration_ms`, etc.) preserved unchanged at
  the top of the file. Built on a new ~340 LOC portable C shim
  at `runtime/native/mapanare_time.c` (POSIX default + `#ifdef
  _WIN32` for `GetSystemTimePreciseAsFileTime` / `localtime_s` /
  `gmtime_s` / `_mkgmtime`). Six new runtime exports:
  `__mn_now_realtime_ns`, `__mn_utc_pack`, `__mn_local_pack`,
  `__mn_local_offset_minutes`, `__mn_timegm`,
  `__mn_normalize_pack`. Wired into `runtime/native/Makefile`
  `RUNTIME_SOURCES` (`libmapanare_rt.a` now contains 9 modules +
  Metal on Darwin).
  **Phase 0 spike result.** PROMPT scoped Dt.5 with operator
  overloads (`dt + dur`). Spike (`/tmp/op_spike.mn`) confirmed
  `impl Add for Dur` does NOT lower through `mnc-stage1` —
  semantic checker reports `Undefined trait 'Add'` and `Operator
  '+' not supported for types Dur and Dur`. Operator-overload
  infrastructure (`trait Add`, etc.) does not exist in the
  current toolchain. Per PROMPT mitigation, Dt.5 fell back to
  free-function method form: `datetime_add_duration(dt, dur)`,
  `duration_add(a, b)`, `duration_mul(d, n)`, etc. Same surface
  semantics, less ergonomic, no syntax change.
  **PLAN deviation (load-bearing) — single-file vs. directory
  module.** PROMPT specified `stdlib/time/{types,construct,parse,
  format,arith,tz}.mn`. Phase 2 dev surfaced two cross-module
  limitations: (1) native `mnc-stage1` does not propagate
  `extern_fn_def` declarations across module imports — every
  consumer would have to re-declare every extern; (2) the Python
  LLVM emitter mangles defined function names with the module
  prefix (`time__date_new`) but emits unprefixed forward
  declarations at call sites, producing link failures
  (reproduced via `python3 -m mapanare emit-llvm + clang link`;
  same root cause as the `examples/ai/basic_chat.mn` v4.129.0
  known-issue note). Both blocked the multi-file design. Every
  existing stdlib module (`math`, `crypto`, `fs`, `ai/llm`,
  `db/*`) is single-file with self-contained tests for the same
  reason — v5.34.0 follows that proven pattern. Cross-module
  fixes tracked separately and explicitly **outside v5.34.0
  scope** (the PROMPT itself warned "If you find yourself
  opening `mapanare/self/lower.mn` or `emit_llvm.mn`, you have
  gone outside scope"). The directory-module shape remains the
  right structural goal; it has to ride a separate
  cross-module-emitter fix.
  **Dt.7 tests.** 7 `.mn` test files under `stdlib/time/tests/`
  + new pytest harness `tests/stdlib/test_time_dt.py` (mirrors
  the v3.x `test_crypto.py` concatenation pattern: read
  `stdlib/time.mn`, prepend to each `.mn` test main body,
  compile via Python LLVM emitter, link against
  `libmapanare_rt.a`, run, assert `"PASSED"` in stdout). 9/9
  GREEN at HEAD. Tests cover: Dt.1 leap-year boundaries
  (1900/2000/2024/2100/2400 — the bug-class behind every "Feb
  29 1900" mishap); Dt.2 epoch round-trip across 0 (1970) →
  2000000000 (2033); Dt.3 22 parse cases including
  `2026-05-03T14:32:00.123Z` (fractional secs) and
  `+05:30`/`-05:00` offset variants; Dt.4 strftime specifier
  coverage; Dt.5 month/day rollover (Jan 31 + 1d → Feb 1; Dec
  31 23:59:59 + 1s → next year; Feb 29 leap + 365d → Feb 28
  non-leap); Dt.6 `tz_named` explicit-defer assertion; Dt.7
  three property-style tests (parse-then-format round-trip,
  epoch round-trip, arithmetic associativity) on a fixed
  deterministic table of boundary fixtures.
  **Dt.8 C shim.** ~340 LOC. Adapted PROMPT signatures from
  out-pointer form to scalar returns with packed-int64
  representation (`packed = y*10^10 + mo*10^8 + d*10^6 +
  h*10^4 + mi*10^2 + s`) — Mapanare `extern "C" fn` exposes only
  Int / String / List<X> returns, no out-pointer surface. C
  smoke (`/tmp/time_shim_smoke.c`, 20 cases): leap-year
  boundaries, normalization forward/backward, year overflow,
  out-of-range rejection. 20/20 PASS. Valgrind clean.
  **Dt.9 docs.** `docs/stdlib/time.md` — quick reference, type
  definitions with year-range/leap-year/tz-sign conventions
  documented, strftime specifier table, four required cookbook
  recipes (parse-then-format round-trip; "1 week from now"; "is
  this date in the past?"; "format as ISO 8601 in local
  timezone"), migration note from the v5.33.x flat
  `stdlib/time.mn` (every existing surface preserved).
  **Closeout: caught one bug at Phase 6.** ISO parser
  fractional-seconds skip had off-by-one between loop-exit
  sentinel (`p = n`) and post-loop fallback
  (`if p == n { tz_pos = p }`). Symptom:
  `2026-05-03T14:32:00.123Z` failed parse with empty
  diagnostic. Fix: track `found_pos` separately from loop-exit
  sentinel; only fall back to `tz_pos = n` when `found_pos < 0`.
  Pinned in `test_parse_iso.mn` case 17 — round-trip parse →
  format → parse.
  **Hd-class preventative.** SPEC.md header re-synced from
  v5.33.1's "synced to the v5.33.1 cut" to "synced to the
  v5.34.0 cut" with a new 14-line block summarizing what
  v5.34.0 adds (specifically enumerating the 6 new runtime
  functions — the first SPEC-scoped runtime additions since
  v5.21.0). `check_doc_freshness.py` GREEN.
  Aggregate state entering v5.35.0: **1 HIGH** (Tn.1 — DEADLINE
  per v5.33.0 escalation, 6-release overdue carry-forward) /
  **2 MEDIUM** (macOS notarization; carry) / ~7 LOW (added
  named-tzdb, cross-module mangling, operator-overload
  infrastructure, full strftime expansion, sub-second precision
  in broken-down forms). See
  `docs/roadmap/v5/v5.34.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.33.2** (ready, not tagged) — **Cd.\* — relax panel-cadence
  enforcement to informational-only.** Tooling-policy hotfix.
  **Zero compiler edits. Zero runtime edits. Zero
  `mapanare/self/*.mn` source edits.** Strict 3-stage fixed point
  preserved by construction at v5.33.1's 241,898 lines / 0 diff
  (30-release strict streak from the v5.7.1 baseline). Goldens
  **95/95**. Closes the v5.33.1-push CI failures: the
  "Cadence enforcement (warn-only)" job in `.github/workflows/ci.yml`
  reported a red ❌ even though `continue-on-error: true` made it
  non-blocking, and `tests/test_cadence.py::test_cadence_within_window_at_head`
  asserted exit 0 at HEAD which was impossible at 5 minors past
  v5.28.0 panel. **Cd.1**: `scripts/check_cadence.py` rewritten —
  `main()` always returns 0; `OVERDUE` renamed to `REMINDER` +
  clarifying "Informational only — lead drives review timing.";
  docstring updated with the v5.24.0 Hy.3 → v5.33.2 Cd.1 history
  + the artifact-correctness-vs-human-scheduling distinction.
  **Cd.2**: `tests/test_cadence.py` updated — fixture cases that
  previously asserted exit 1 on overdue now assert exit 0 +
  REMINDER message printed. Doc-drift / changelog-honesty /
  fixed-point line-count gates remain hard — those enforce
  *artifact correctness*; this one tracked a *human scheduling
  decision*, which is the lead's call. User-memory entry
  `feedback_no_forced_cadence_gates` recorded so the rule survives
  across sessions: visibility/REMINDER OK, CI-blocking enforcement
  not OK; same rule applies if a future arc proposes the same
  shape under a different name. Source delta: ~50 LOC in
  `scripts/check_cadence.py` (full rewrite), ~30 LOC in
  `tests/test_cadence.py` (fixture-case updates), CHANGELOG
  one-paragraph entry, this CLAUDE.md entry, plus the mechanical
  Vb.\* files. Stage1 + `libmapanare_rt.a` rebuilt post-bump per
  the v5.31.0 + v5.33.1 lessons. Aggregate state entering v5.34.0:
  **1 HIGH** (Tn.1 — 6-release overdue carry; panel cadence
  demoted from HIGH to LOW since the gate is no longer enforcing)
  / **2 MEDIUM** (macOS notarization; carry) / ~6 LOW. See
  `docs/roadmap/v5/v5.33.2/{PLAN.md, SESSION_REPORT.md}`.

- **v5.33.1** (ready, not tagged) — **Hd.\* — SPEC header drift
  hotfix.** Docs-surface-only hotfix. **Zero compiler edits.
  Zero runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.33.0's 241,898 lines / 0 diff (29-release strict streak
  from the v5.7.1 baseline). Goldens **95/95**. Closes
  `check_doc_freshness.py` SPEC-header lag violation (3 minors
  stale, max tolerated 2). `docs/SPEC.md` header re-synced from
  `synced to the v5.30.0 cut` to `synced to the v5.33.1 cut`;
  new sync block at the top summarizes v5.31.0 (Bn.\* banner
  hotfix), v5.32.0 (Nw.\* Windows native `mnc.exe` in SDK ZIP),
  v5.33.0 (Nu.\* Linux x86_64 + macOS arm64 native `mnc` in
  release tarballs; Linux aarch64 + macOS x86_64 deferred to
  v5.34.0+), and v5.33.1 (this re-sync) — declarative,
  cross-checked against each release's SESSION_REPORT.
  v5.31–v5.33.1 together added **zero language features, zero
  new MIR ops, zero new IR shapes, zero new runtime functions**
  — packaging / hotfix releases only. The structural gate
  (`check_doc_freshness.py`'s `check_spec_header()`, landed at
  v5.24.0 Hy.2 with a 2-minor lag tolerance) fired exactly as
  designed: SPEC stayed unsynced for 3 minor releases, gate
  flipped hard at v5.33.0 HEAD, hotfix re-syncs and the gate
  closes the next recurrence in CI rather than at the panel.
  Source delta: ~14 LOC in `docs/SPEC.md` (Hd.1 header bump +
  Hd.2 sync block), ~12 LOC in `CHANGELOG.md` (one-paragraph
  hotfix entry, no fake `### Added`/`### Changed`/`### Fixed`
  subsection content), this CLAUDE.md entry, plus the
  mechanical files `bump_version.py` touched (VERSION + 4
  README badges en/es/pt/zh-CN). Stage1 rebuilt post-bump so
  IR-metadata embeds `!"5.33.1"` in stage2 + stage3 (the
  v5.31.0 SESSION_REPORT documented lesson — without the
  rebuild, `verify_fixed_point.sh` would show a 4-line
  VERSION-placeholder NEAR diff). **Panel cadence note:**
  `check_cadence.py` warn-only OVERDUE — 5 minor versions since
  v5.28.0 panel; full 7-reviewer panel deliberately not picked
  up here (multi-day cycle, exceeds hotfix scope). Escalated to
  v5.34.0 as HIGH carry-forward. Aggregate state entering
  v5.34.0: **2 HIGH** (panel cadence escalated; Tn.1 5-release
  overdue carrying forward) / **2 MEDIUM** (macOS notarization;
  carry) / ~6 LOW. See
  `docs/roadmap/v5/v5.33.1/{PLAN.md, SESSION_REPORT.md}`.

- **v5.33.0** (ready, not tagged) — **Nu.1 + Nu.2 + Nu.3 + Nu.4
  + Nu.5 + Nu.6 — ship native `mnc` in the Linux x86_64 and
  macOS arm64 release tarballs.** Mirror of v5.32.0 Nw.\*
  applied to the two existing Unix tarballs. Closes the
  asymmetry where Windows had the fix and Unix didn't —
  release-tarball users on Linux x86_64 and macOS arm64
  no longer hit the Python bootstrap on `mnc --version`,
  `mnc run`, or `mnc build`. **Zero compiler edits. Zero
  runtime edits. Zero `mapanare/self/*.mn` source edits.**
  Strict 3-stage fixed point preserved by construction at
  v5.32.0's **241,898 lines / 0 diff** (28-release strict
  streak from the v5.7.1 baseline). Goldens **95/95**.
  **Nu.1 + Nu.2 deviation from PROMPT.** PROMPT scoped
  four arches: Linux x86_64 + Linux aarch64 + macOS x86_64
  + macOS arm64. v5.33.0 ships only the two arches that
  already build natively in `build-native` (Linux x86_64
  on `ubuntu-latest`, macOS arm64 on `macos-latest`).
  Linux aarch64 and macOS x86_64 are **deferred to v5.34.0**.
  Reasons: (a) `scripts/build_stage1.py` has no `--target`
  / `--output` flags — it always builds for the host;
  cross-compile would need new infrastructure that exceeds
  v5.32.0's "lift the proven path" precedent; (b) Linux
  aarch64 needs a cross-compile + qemu smoke pipeline that
  doesn't exist; (c) macOS x86_64 needs a separate
  `macos-13` runner and a brand-new tarball name in the
  release matrix. Mirrors v5.32.0's own "deviation from
  PROMPT" (build-native reuse vs. PROMPT's cross-compile
  recipe — same logic: prefer the validated path; preserve
  the more ambitious recipe for the next minor when it's
  motivated). **Nu.1 + Nu.2 plumbing**: `build-native`
  Linux + macOS jobs upload `mnc-linux-x64` /
  `mnc-darwin-arm64` as workflow artifacts (mirrors the
  `mnc-windows-x64-native` Nw.2 upload, single-day
  retention, `if-no-files-found: error`). `build-cli`
  Linux + macOS paths download the matching artifact, run
  three guards before staging — ELF / Mach-O magic
  (`7f454c46` for ELF; `cffaedfe` for Mach-O 64-bit
  little-endian) + 20 MB size ceiling (native is ~3-4 MB;
  PyInstaller-copy regression would be ~30 MB) +
  non-zero-bytes check — then copy to
  `dist/mapanare/mnc` (sibling of the existing
  `dist/mapanare/mapanare` PyInstaller binary; bundle-root
  layout matching the v5.32.0 Nw.2 decision rather than
  the PROMPT's `bin/mnc` shape). macOS path also runs
  ad-hoc `codesign -s -` so Gatekeeper doesn't quarantine
  the binary on first run after tar extraction; proper
  Developer ID notarization is a v5.34.0+ LOW.
  **Nu.4** smoke gates: two layers, both load-bearing.
  **Layer 1 in-job** (`build-cli` "Clean Linux/macOS native
  mnc smoke before archiving"): on the staging directory,
  asserts `dist/mapanare/mnc --version` (a) contains the
  expected version string from `VERSION`, (b) does not
  spawn a new Python interpreter (snapshots `pgrep -fl
  python` count before / after — same anti-pattern Windows
  Nw.4 closes). **Layer 2 published** (extends existing
  `linux-tarball-smoke` + `macos-tarball-smoke` jobs which
  already gate on `windows-sdk-smoke`'s shape): downloads
  the published tarball from the GitHub Release, runs the
  same magic / size / version-string / no-Python-spawn
  checks. Per-platform stat flag (`stat -c%s` Linux vs.
  `stat -f%z` macOS). The no-Python assertion is the
  load-bearing one — that's the specific anti-pattern
  v5.33.0 closes for the Unix release tarballs.
  **Nu.5** fallback-wrapper audit: `mapanare/__main__.py`
  refactored to extract `_native_binary_name(os_name=...)`
  (4 LOC). Pre-v5.33.0 the suffix-selection logic
  (`"mnc.exe" if os.name == "nt" else "mnc"`) was inlined
  in `_native_binary` and only host-OS-testable —
  monkeypatching `os.name` globally to test the *other*
  branch crashes pathlib (`NotImplementedError: cannot
  instantiate 'WindowsPath' on your system`). The new
  helper takes `os_name` as a parameter so tests can pin
  the value without touching pathlib. New
  `tests/test_native_fallback.py::test_native_binary_suffix_per_platform`
  parametrizes over (`posix` → `mnc`, `nt` → `mnc.exe`)
  so a Linux CI worker validates the Windows lookup and
  vice versa. 5/5 GREEN. Falsifiability: hardcoding the
  wrong suffix flips one of the two parametrized cases.
  **Nu.6** docs: README.md install section gains a
  paragraph noting v5.33.0+ ships native `mnc` on Linux
  x86_64 + macOS arm64; macOS-quarantine workaround
  (`xattr -d com.apple.quarantine`) documented inline.
  CLAUDE.md "Native-First Philosophy" updated; this
  release-notes entry added. **Localized READMEs
  (es/pt/zh-CN) deliberately not updated** — v5.32.0
  followed the same pattern (English README only); the
  v5.28.0 panel H.4 finding tracks localized README
  updates as a bookkeeping cycle, not per-release work.
  Source delta: ~120 LOC YAML in `.github/workflows/publish.yml`
  (Nu.1+Nu.2 + Nu.3 staging + Nu.4 in-job smoke + extended
  `linux-tarball-smoke` / `macos-tarball-smoke`); ~10 LOC
  Python in `mapanare/__main__.py` (Nu.5 refactor); ~25 LOC
  test in `tests/test_native_fallback.py` (Nu.5 parametrized
  case); ~15 LOC docs (README + CLAUDE). Aggregate state
  entering v5.34.0: 0 HIGH / 2 MEDIUM (Tn.1 — 5-release
  overdue, escalates to HIGH per v5.32.0 directive; macOS
  notarization, new from Nu.2 ad-hoc-signing shortcut) /
  ~6 LOW (deferred Linux aarch64 + macOS x86_64 tarballs
  added). Cadence unchanged: next routine panel still due
  v5.33.0 cadence-gap-acknowledged at v5.34.0 if not
  bundled. See
  `docs/roadmap/v5/v5.33.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.32.0** (ready, not tagged) — **Nw.2 + Nw.3 + Nw.4 + Nw.5
  + Nw.6 — ship native `mnc.exe` in the Windows SDK ZIP.**
  Closes the structural "Python is the front door on Windows
  release installs" problem that v5.31.0 only papered over.
  v5.12.0 shipped the *toolchain* bundle (`sdk\bin\clang.exe` —
  LLVM-MinGW). v5.32.0 ships the *frontend* bundle: `mnc.exe`
  in `mapanare-${V}-win-x64-sdk.zip` and `-minimal.zip` is now
  the native compiler binary, not a PyInstaller copy of
  `mapanare.exe`. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.31.0's **241,898
  lines / 0 diff** (27-release strict streak from the v5.7.1
  baseline). Goldens **95/95**. After this release a fresh
  Windows SDK install never invokes Python for `mnc --version`,
  `mnc run`, or `mnc build`. **Nw.1 deviation from PROMPT:**
  PROMPT recommended approach (a) cross-compile from Linux CI
  via `clang --target=x86_64-w64-mingw32`. v5.32.0 uses
  approach (b) — reuses the existing `build-native` Windows
  job's `mnc-win-x64.exe` artifact (full stage1 → stage2
  self-compile cycle on a `windows-latest` runner via w64devkit
  MinGW). Reasons: PROMPT explicitly allows fallback to (b)
  "if cross-compile produces ABI mismatches" — doing (b)
  directly avoids a discovery cycle; existing path is validated
  across 30+ releases and runs the full self-compile cycle
  (stronger Win64-ABI validation than cross-compile);
  smaller diff — no third Windows-build code path. Trade-off:
  ~5-10 min of serial CI on the Windows publish path
  (`build-cli` now `needs: [release, build-native]`).
  Cross-compile remains available for v5.33.0+ when Linux /
  macOS native-frontend bundling motivates a unified job.
  **Nw.2** publish.yml wiring: `build-native` Windows path
  uploads `mnc-win-x64.exe` as the `mnc-windows-x64-native`
  workflow artifact (in addition to the existing GitHub
  Release upload). `build-cli` Windows path downloads it and
  stages as `dist/mapanare/mnc.exe` with two guards:
  MZ-header check (PE32+ DOS-stub `0x4D 0x5A`) and 20 MB size
  ceiling (native is ~3-4 MB; PyInstaller copy is ~30 MB —
  20 MB reliably distinguishes). Replaces the pre-v5.32.0
  `Copy-Item dist/mapanare/mapanare.exe dist/mapanare/mnc.exe`
  alias-shape. **Nw.3** native-binary fallback wrapper:
  `mapanare/__main__.py` rewritten with a 25-LOC preamble
  that detects a sibling `bin/mnc[.exe]` and `os.execv`s to
  it. `MAPANARE_FORCE_PYTHON=1` opts out for dev/debug. Also
  fixes a pre-v5.32.0 bug where `cli.main()` ran at module-
  import time (no `if __name__ == "__main__":` guard) — pytest
  collection of the new fallback tests would have hit
  argparse `SystemExit` otherwise. New
  `tests/test_native_fallback.py` (3 cases) locks the
  detection logic and the env-var bypass. **Nw.4** smoke gate:
  augmented existing `Clean Windows SDK smoke before archiving`
  (in build-cli) and `windows-sdk-smoke` (post-publish, on
  the published ZIP) with three new gates — MZ-header +
  size-ceiling check on `mnc.exe`; version-string match
  against `VERSION`; no-new-Python-process assertion across
  the `--version` call (snapshots `Get-Process | Where-Object
  { $_.Name -match '^python' }` count before / after). The
  no-Python assertion is the load-bearing one — that's the
  specific anti-pattern v5.32.0 closes. **Nw.5** minimal ZIP
  also ships native `mnc.exe` automatically — minimal-ZIP
  staging archives `dist/mapanare/` *after* Nw.2 staging has
  swapped the binary, so no separate code path needed.
  **Nw.6** docs: CLAUDE.md Native-First Philosophy section
  gains a paragraph; README.md install section calls out the
  v5.32.0+ native shipping; CHANGELOG.md `## [5.32.0]` filled
  in with full Nw.\* details + the deviation note;
  `check_changelog_honesty.py` GREEN. **Layout decision:**
  PROMPT specified `bin\mnc.exe`; v5.32.0 keeps `mnc.exe`
  at the bundle root because the bundled SDK lives at
  `sdk/bin/clang.exe` (not `bin/sdk/bin/clang.exe`) — PROMPT's
  layout assumption didn't match v5.12.0's existing structure.
  Aggregate state entering v5.33.0: 0 HIGH / 1 MEDIUM (Tn.1,
  4-release overdue; v5.32.0 deferred to keep scope tight;
  escalates to HIGH at v5.33.0 per v5.31.0 cadence note) /
  ~5 LOW. Cadence unchanged: next routine panel still due
  v5.33.0. See
  `docs/roadmap/v5/v5.32.0/{PLAN.md, PROMPT.md, SESSION_REPORT.md}`.

- **v5.31.0** (ready, not tagged) — **Bn.1 + Bn.2 + Bn.3 +
  Bn.4 + Bn.5 — banner hotfix; kill the "[dev mode]" lie.**
  Pure UX hotfix. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage
  fixed point preserved by construction at v5.30.0's
  **241,898 lines / 0 diff** (26-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Closes the
  publish-run-#50-shaped report where a fresh Windows SDK
  install ran `mnc --version` and got `[dev mode] Using
  Python bootstrap compiler. For native speed: mnc run
  <file.mn>` printed before the version string — three
  things wrong: "[dev mode]" was a lie on a release install,
  "for native speed: mnc run <file.mn>" was incoherent on a
  metadata command, and the banner fired unconditionally
  before argparse ran. The Python bootstrap was fine — it
  just announced itself wrong. **Bn.1**: new
  `_should_show_dev_banner(argv)` argv-peek in
  `mapanare/cli.py::main` skips the banner when the first
  non-flag token is in `NO_BANNER_COMMANDS = frozenset({
  "--version", "--help", "-h", "init", "list"})`; honest-
  default policy is "when in doubt, don't fire". **Bn.2**:
  new `_is_release_install()` helper (`@lru_cache(1)`):
  primary signal is `MAPANARE_RELEASE=1` env var; fallback
  is the absence of `pyproject.toml` + `.git` directory at
  the repo root (the parent of `mapanare/`). Release
  installs never see the banner. **Bn.3**: dev-clone
  banner reworded to honestly describe the situation:
  `[mapanare dev] running from source clone (.../mapanare/
  cli.py). Set MAPANARE_RELEASE=1 or install via the SDK to
  silence.` Path embedded so a developer with multiple
  checkouts can tell which one they're hitting. Misleading
  "for native speed: mnc run <file.mn>" suggestion removed.
  **Bn.4**: new `tests/test_cli_banner.py` (5 cases) locks
  all four matrix cells {dev clone, release install} ×
  {metadata cmd, compile cmd} plus the new wording.
  Falsifiability: removing either gate in `cli.py`
  reproduces the publish-run-#50 anti-pattern. **Bn.5**:
  `packaging/pyinstaller-entry.py::main()` calls
  `os.environ.setdefault("MAPANARE_RELEASE", "1")` before
  importing `mapanare.cli`. Single edit covers Linux
  tarball, macOS bundle, and Windows SDK ZIP — every
  release platform ships via the PyInstaller bundle so all
  inherit the env var. The Bash shim
  (`packaging/mapanare-shim.sh`) `exec`s the bundled
  binary directly so the env var set inside the entry
  point is the process's own env. `setdefault` (not
  unconditional set) means a user who explicitly unsets
  `MAPANARE_RELEASE` for testing can still trigger the
  path-heuristic fallback. **v5.31.0 ≠ v5.32.0** — the
  native `mnc.exe` shipping work (which makes the Python
  path *unused* on release installs, not just *quiet*)
  is v5.32.0. Source delta: ~115 LOC of behavior change
  across 3 files (`cli.py` +37/-5, new
  `test_cli_banner.py` +75, `pyinstaller-entry.py` +9/-1)
  — well under PLAN's 50–80 LOC target with the test file
  the bulk of the new code. **Lesson captured for future
  bump-only releases**: rebuild stage1 via
  `python3 scripts/build_stage1.py` between
  `bump_version.py` and `verify_fixed_point.sh` — first
  fixed-point run after the bump showed a spurious 4-line
  VERSION-placeholder NEAR diff (`!0 = !{!"5.30.0"}` vs
  `!0 = !{!"5.31.0"}`) because cached stage1 still
  embedded pre-bump VERSION; rebuild restored STRICT.
  Aggregate state entering v5.32.0: 0 HIGH / 1 MEDIUM
  (Tn.1 still 3-release overdue; bumped from "overdue"
  toward "escalate to HIGH at v5.33.0 if not landed";
  deliberately deferred to keep v5.31.0 scope tight) /
  ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See
  `docs/roadmap/v5/v5.31.0/{PLAN.md, SESSION_REPORT.md}`.

- **v5.30.0** (ready, not tagged) — **Vb.\* — packaging-only
  release: version bump.** **Zero compiler edits. Zero runtime
  edits. Zero `mapanare/self/*.mn` source edits.** Strict
  3-stage fixed point preserved by construction at v5.29.0's
  **241,898 lines / 0 diff** (25-release strict streak from
  the v5.7.1 baseline). Goldens **95/95**. Advances the
  published version surface (VERSION, README badges in
  en/es/pt/zh-CN, CHANGELOG.md) so the next `dev` → `main`
  merge carries a clean v5.30.0 number; the substantive
  deliverable is the refreshed PR description covering
  v5.13.0 → v5.30.0 cumulative scope (currently `main` is
  stuck at v5.13.0). All real fix / feature work shipped at
  v5.29.0 (Mb.10 self-host emitter routing for
  `__mn_indent_to_braces` Win64 ABI; Pv.7 / Pv.8 already on
  `dev` pre-v5.29.0). NO seed refresh required (no C-runtime
  export changes — no `.mn` source touches the C side at
  all). `make ci-gates` GREEN (9 sub-gates); `make lint`
  clean. See `docs/roadmap/v5/v5.30.0/{PLAN.md,
  SESSION_REPORT.md, PR_BODY.md}`.

- **v5.29.0** (ready, not tagged) — **Mb.10 + Pv.7 + Pv.8 —
  Win64 ABI closeout + CI race prevention.** Three findings,
  three fixes, one release. Reopens the **Mb.\*** arc (declared
  closed at v5.26.1) for one residual Win64 ABI gap and closes
  it **structurally** this time. **Strict 3-stage fixed point
  preserved by construction at 241,898 lines / 0 diff** (24-
  release strict streak; restored from v5.28.0's NEAR — the
  prior NEAR was a v5.9.0 DX.2 artifact from a stale stage1
  binary linked against a v5.27.0-vintage runtime, not actual
  divergence). Goldens **95/95**. **Mb.10**: closes
  publish-run-#50 Windows SIGSEGV in `__mn_indent_to_braces`.
  Sister fix to v5.26.0 Mb.9 (which routed the brace-deprecation
  siblings `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning` but missed the parent
  function with the same Win64 ABI shape). Pre-fix mechanism:
  `emit_mir_call`'s user-call fallthrough uses the 64-byte
  `is_byref_type_st` threshold for arg classification; `MnString`
  is 16 bytes, so on Win64 the call site emitted the struct by
  value while `declare_runtime_fn` already declared the function
  with `ptr` parameter via `win64_rewrite_decl_params` (8-byte
  threshold). gcc lowered `MnString source` per Win64 ABI as
  pass-by-hidden-pointer with rcx pointing into the struct's
  data buffer instead of into a valid `MnString` — SIGSEGV on
  the first `source.len` read. The Python emitter has had this
  routing since v5.23.1 Mb.1 (`emit_llvm_text.py:3632`); the
  self-host side was missed. The Mb.9 Python comment at
  `mapanare/self/emit_llvm.mn:3778` even names the missing
  routing as the pattern Mb.9 mirrored — but Mb.9's author only
  added the routing for the brace-deprecation pair, not for the
  parent function. Bug stayed latent because Linux/macOS publish
  jobs hide the mismatch via SysV register-passing, and Windows
  publish wasn't reaching the stage2-self-compile step for
  v5.23.1 → v5.27.0 (failing earlier on other things). v5.28.0
  RE-PANEL did not surface Mb.10 (test gap; covered by Tn.1
  panel rec). 3-LOC fix in `mapanare/self/emit_llvm.mn` (12-line
  block including explanatory comment) inserted after the Mb.9
  brace-deprecation routing at line 3786, mirroring the same
  shape — only the return type differs (`llvm_string()` i.e.
  `{ptr, i64}` MnString here, vs `"i64"` for the counter).
  `emit_rt_call` uses `win64_sarg_rewrite_args` (8-byte
  threshold matching `win64_rewrite_decl_params`), producing
  the correct `sret+sarg` shape on Win64 and a no-op on Linux
  SysV. **Mb.10.C** new
  `tests/llvm/test_indent_to_braces_win64_abi.py` (6 cases
  mirrors v5.26.0 Mb.9.C's `test_brace_funcs_windows_abi.py`):
  3 IR-shape gates under Win64 triple via the Python emitter
  (load-bearing); 1 SysV negative gate pinning the by-value
  shape so future emitter refactors don't accidentally rewrite
  it; 3 ctypes contract cases against
  `runtime/native/mapanare_core.c` for runtime-side correctness.
  Falsifiability round-trip verified — reverting the v5.23.1
  Python handler triggers the IR-shape gate failure exactly
  matching the publish-run-#50 anti-pattern (`call ... ({ptr,
  i64} %l.0)`). **Bb.\* seed refresh: NOT required** (no
  C-runtime export changes; the v5.10.0-vintage seed has no
  view of how `mnc-stage1` emits the call). **Pv.7**: closes
  `clean-build-test` race against parallel `pytest -n auto`
  workers. Pre-fix, the `rm -f libmapanare_rt.a && make
  build-rt` sequence in `clean-build-test` left a 1-3 second
  window where the canonical archive was missing; surfaced as
  flake on `tests/bootstrap/test_chained_cmp_mirror.py`
  (gw0 hit the race window). **Already shipped on dev as
  commit `bc3bc7b`** between v5.28.0 and v5.29.0. Fix
  parameterizes `build-rt` with `RT_OUTPUT ?=
  runtime/native/libmapanare_rt.a`, rebuilds into a sandbox
  path on the same filesystem (`runtime/native/.libmapanare_rt
  .cbt-tmp.a`), then atomic `mv -f` into the canonical path.
  Race-window evidence captured in v5.29.0 SESSION_REPORT:
  200-poll watcher at 20 ms cadence over the full 4-second
  rebuild produced **0 MISSING reports**. **Pv.8**: closes
  agent-state timing races in `tests/native/test_c_runtime.c`'s
  `test_agent_pause_resume` (`:712`) and
  `test_agent_failing_handler` (`:738`). `mapanare_agent_pause()`
  is a guarded transition that silently no-ops if the agent
  isn't yet RUNNING; the worker thread sets state=RUNNING only
  after the OS schedules the new thread, and the test's fixed
  `usleep(50000)` was sometimes insufficient under CI load.
  **Already shipped on dev as commit `f119c43`** between
  v5.28.0 and v5.29.0 (the PROMPT/PLAN were drafted assuming
  the fix was uncommitted; verified at Phase 0 that it had
  landed cleanly). Fix adds 4 polling helpers
  (`wait_for_agent_state`, `wait_for_messages_processed`,
  `wait_for_agent_recv`, `wait_for_counter` + `test_sleep_ms`)
  plus 7 fixed-delay sleeps converted to bounded polls
  (`test_agent_lifecycle`, `test_agent_send_recv`,
  `test_agent_pause_resume`, `test_agent_failing_handler`,
  `test_agent_metrics`, `test_shutdown_with_agents`,
  `test_pool_basic` + `test_pool_saturation`). Generous
  timeouts (1000 ms for state, 2000 ms for FAILED /
  messages-processed, 5000 ms for 500-task pool stress) —
  returns on first match; only consumes the full budget if the
  worker is genuinely stuck. Plain + ASan + TSan all green
  (3/3); `gcc -O2 -g -pthread -Wall -Wextra -Werror` clean.
  Pv.8.B (preemptive sweep of 11 same-shape sites in
  `tests/native/test_agent_scheduler.py`) **deferred** to
  v5.30.0+ if a flake materializes; reactive-only fix
  discipline preserved. **Mb.\* arc CLOSED structurally** —
  v5.26.0's "Mb.\* arc CLOSED" claim was strictly correct for
  Mb.7+Mb.9 but missed `__mn_indent_to_braces`; v5.29.0 closes
  the arc for real. Aggregate state entering v5.30.0: 0 HIGH /
  1 MEDIUM (Tn.1 escalated per v5.28.0 panel directive — not
  picked up here, deliberately deferred to keep Mb.10 scope
  tight) / ~5 LOW. Cadence unchanged: next routine panel still
  due v5.33.0. See `docs/roadmap/v5/v5.29.0/{SESSION_REPORT.md,
  PLAN.md, AUDIT.md}`.

- **v5.28.0** (ready, not tagged) — **RE-PANEL — v5.23.0 →
  v5.27.0 recovery + prevention + arc-closeout arc graded.**
  Panel-only release. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at v5.27.0's 241,842 lines / 0
  diff. 7 reviewers graded the v5.23.0 → v5.27.0 arc (8 releases,
  9 SESSION_REPORTs) using the v5-gate mechanical decision rule.
  **Aggregate: 9.72 / 10. Decision: Option A.** Fourth
  consecutive Option A under the v5-gate framework, **largest
  single-arc recovery in v5 history (+0.31 vs v5.22.0's 9.41
  floor)**, and **first panel above the v5.7.1 / v5.8.0 9.66
  ceiling in the v5 series**. Score trajectory: 9.66 → 9.62 →
  9.41 → **9.72** — 3-consecutive-panel downward trend (-0.04,
  -0.21) broken with +0.31. **Per-reviewer:** Rattler 9.90
  (+0.05), Viper 9.80 (+0.10), **Anaconda 9.60 (+1.20 — load-
  bearing recovery; the v5.22.0 -1.30 dock was driven by 3
  silently-RED CI gates that v5.23.0 RC.\* + v5.24.0 Hy.\* +
  v5.25.0 Pv.\* closed structurally, not symptomatically)**,
  Cobra 9.70 (+0.15), Coral 9.70 (+0.15), **Boa 9.55 (+0.55 —
  largest single-panel Boa improvement in project history;
  Bo.18r 3-consecutive-panel persistence finally structurally
  closed)**, Mamba 9.80 (-0.05). 7 EXCEEDS / 0 MEETS / 0 NEEDS
  WORK; 7 PASS WITH NOTES. **0 NEW HIGH, 0 NEW MEDIUM, ~14 NEW
  LOW** (mostly process polish). **v5.22.0 docket: 25/25 items
  CLOSED at v5.28.0 HEAD** (highest closure rate in v5 history
  across a single recovery arc). Mb.\* / Mc.\* / Eu.\* arcs all
  CLOSED entering this panel; 4 prev-LINK_FAIL goldens
  (47/48/49/51) flipped to PASS via Eu.1..Eu.4. **Phase 2 H.\*
  hygiene closures** (committed `069ff24` ahead of panel cut,
  per Bo.27 / Wd.8 cross-reference convention codified at
  `.reviews/PANEL_AUDIT_TEMPLATE.md`): H.1/H.2/H.3 (Bo.18r-class)
  README.md fixed-point status paragraphs at lines 175 / 183 /
  196-197 bumped to v5.27.0 / 241k / 23 consecutive releases;
  H.4 (Bo.17r-class) 3 localized READMEs (es/pt/zh-CN) native-
  compiler subsection rewritten with v5.23-v5.27 arc summary;
  H.5 (Bo.10-class) `docs/known_issues.md` Last-updated bumped;
  H.6 (An.1-class) `.reviews/CARRY_FORWARD.md` v5.25-v5.27
  closure rows appended (4-release update-protocol drift caught
  + fixed); H.7 cadence-gap acknowledgment in PROMPT.md +
  PRE_PANEL_AUDIT.md preambles. **Cadence-gap closure 1 minor
  late on purpose** — v5.24.0 Hy.3 cadence-enforcement gate
  fired hard at v5.27.0 (5+ minor threshold); v5.28.0 closes
  the gap because bundling formatter polish (Mc.8+Mc.9+Tk.1)
  with a panel cycle was rejected during v5.27.0 PLAN drafting.
  Two reviewers (Anaconda, Coral) independently judged the
  framing honest. **Convergent recommendation (Cobra Cb.New1 +
  Rattler Ra.Inf1 — independent reviewers, same finding shape)**:
  extend `tests/llvm/test_async_link.py` link-and-run pattern
  to all 95 goldens via new `test_llvm_link_all.py` (Tn.\*
  generalization). Closes the structural gap that hid Eu.1..Eu.4
  for 3 releases. **Escalate to MEDIUM at v5.29.0 if not picked
  up in a Pv.\* follow-on.** Other LOW recommendations: M.1
  (Mamba — `.h` vs `.c` header asymmetry recurrence; Pv.7-style
  structural gate); A.1 (Anaconda — new
  `check_carry_forward_freshness.py` gate); Ra.New1 (Rattler —
  Stage2 teardown narrowed to stdout-redirect-specific SIGSEGV;
  investigation tractable, consider closing in v5.29.0 rather
  than v6.0). **Cadence reset:** next routine panel due v5.33.0.
  See `.reviews/v5.28.0/{README.md, V5_DECISION.md, PRE_PANEL_AUDIT.md}`,
  7× `<reviewer>/findings.md`, and
  `docs/roadmap/v5/v5.28.0/SESSION_REPORT.md`.

- **v5.27.0** (ready, not tagged) — **Mc.8 + Mc.9 + Tk.1 —
  formatter polish; Mc.\* parity arc CLOSED.** Three formatter /
  rewriter polish items shipping together because they all live
  in `mapanare/format.py` and ship without compiler edits. Closes
  the v5.13.0 Mc.\* parity gap docket (Mc.8 + Mc.9, 12-release
  carry each) and the v5.24.1 Wd.2 latent rewriter bug (Tk.1,
  3-release carry). **Strict 3-stage fixed point preserved by
  construction at 241,842 lines / 0 diff** (23-release strict
  streak — same line count as v5.26.1 because zero
  `mapanare/self/*.mn` source edits in v5.27.0; the existing
  argv-forwarding loop in `main.mn` carries the new flags through
  the native dispatch unchanged). Goldens **95/95**. **Mc.8**
  (`mapanare fmt --line-length N`): **detect-only** long-line
  reporter. Phase 0 surfaced that Mapanare's grammar is strictly
  single-line for all expressions — newlines are not implicit
  continuations inside `(`/`[`/`{`/`#{` — so an auto-wrap
  rewriter cannot satisfy the v5.13.0 Mc.2 AST-preservation
  invariant. Pure read-only scan; never modifies source; default
  mode reports overlong lines on stderr; under `--check` causes a
  non-zero exit so CI gates can enforce the ceiling; `N=0` (the
  default) disables the check. Auto-wrap rescoped to a future
  release that also adds newline-tolerant grammar inside grouping
  delimiters. **Mc.9** (`mapanare fmt --sort-imports`): sorts
  contiguous top-level `import` blocks alphabetically. Block
  boundaries are any non-import line (blank, comment, or other
  statement), so the user's existing groupings (e.g. stdlib /
  third-party / local separated by blanks) function as the
  de-facto group structure: each group sorts independently.
  Comments inside an import block split the surrounding block
  into sub-blocks — neither side reorders across the comment.
  Idempotent. AST-preserving up to `ImportDecl` declaration
  order; load-bearing corpus check sorts the 8-import block in
  `mapanare/self/main.mn` and asserts `ImportDecl` multiset
  preservation. **Tk.1** (`to_terse` empty `#{}` rewriter bug):
  surgical 6-LOC fix in `mapanare/format.py::to_terse` —
  `endswith("{}")` branch now applies the same
  `_looks_like_stmt_block_opener` filter the `endswith(" {")`
  branch relies on via `_find_match_verbatim_lines`, so
  expression-context empty literals (`let m: Map<String, Int> =
  #{}`, `let p = Point {}`) survive verbatim instead of
  collapsing to grammatically invalid `... = #:` + indented
  `pass`. v5.24.1 Wd.2 sidestepped this latent bug by leaving
  SPEC §17.1 unrewritten; with Tk.1 fixed, `to_terse_markdown
  (SPEC.md)` is now safe to run end-to-end. Falsifiability
  round-trip verified: 3 unit tests (`test_to_terse_preserves_
  empty_map_literal`, `test_to_terse_empty_map_literal_idempotent`,
  `test_to_terse_preserves_empty_struct_literal`) all fail on
  pre-fix `format.py` with the exact pre-fix bug shape; all 3
  pass after the fix. **Source delta:** Python only —
  `mapanare/format.py` ~95 LOC (Tk.1 ~6 + `find_long_lines` ~30
  + `sort_imports` ~50 + `__all__`); `mapanare/cli.py` ~30 LOC
  (argparse + per-file detector wiring); 4 new test files /
  extensions (~525 LOC tests, 47 new test cases); ~90 LOC docs
  in `docs/guides/formatter.md`. **Cadence-gate hard fire**:
  `scripts/check_cadence.py` fires hard at v5.27.0 HEAD (5+
  minor versions since v5.22.0 panel). **Acknowledged and
  informational** — the v5.28.0 RE-PANEL closes the cadence gap
  one minor late on purpose; bundling formatter polish with a
  panel cycle was rejected during PLAN drafting (formatter work
  is the wrong scope to mix with a panel review cycle).
  **Mc.\* parity arc CLOSED** — every Mc.\* item from the
  v5.13.0 parity gap docket is now resolved. See
  `docs/roadmap/v5/v5.27.0/SESSION_REPORT.md` and `PLAN.md`.

- **v5.26.1** (ready, not tagged) — **Eu.1..Eu.4 — close
  v5.26.0-deferred LINK_FAIL bug classes; Eu.\* arc closeout.**
  Four small-but-distinct codegen / lowering fixes that move
  goldens 47, 48, 49, 51 from LINK_FAIL → PASS. Each was a
  pre-existing latent bug surfaced by v5.26.0's Phase 0 audit
  and tracked as `xfail(strict)` in
  `tests/llvm/test_async_link.py`. Per-bug Phase 0 investigations
  honored — bundled in one release for efficiency, not conflated
  (mirrors v5.26.0 Mb.7/Mb.9 split discipline). **Strict 3-stage
  fixed point preserved at 241,842 lines / 0 diff** (22-release
  strict streak; +1,849 lines vs v5.26.0's 239,993 from the new
  lowerer/emitter arms). Goldens **95/95**.
  `tests/llvm/test_async_link.py` 10/10 PASS, 0 XFAIL.
  **Eu.1**: `emit_unwrap` on `Result<T, E>` did one
  `extractvalue ..., 1` returning the inner aggregate `{Ok_ty,
  Err_ty}` rather than the Ok payload at field 0 of that inner
  aggregate. Fixed at both `mapanare/emit_llvm_text.py::_do_unwrap`
  and `mapanare/self/emit_llvm.mn::emit_unwrap` — for `TK_RESULT`
  subjects, do TWO `extractvalue` ops. Closes golden 47 (`?`
  operator on Result). **Eu.2**: standalone `Ok(...)` / `Err(...)`
  literals at call-arg sites (e.g., `classify(Ok(42))` from
  `main`) lowered with empty `dest.ty.args` because the caller
  wasn't a Result-returning fn — `emit_wrap_ok` then derived the
  outer wrapper type from `resolve_mir_type` (fallback `{i1, {ptr,
  ptr}}`) while the inner aggregate used real Ok/Err widths
  (`{i64, ptr}`) — three disagreeing `insertvalue` widths in one
  chain. Fixed at `mapanare/self/lower.mn` Ok/Err lowering to
  default missing args mirroring `mapanare/lower.py:2398`
  (`Result<T, String>` for `Ok(T)` and `Result<Int, T>` for
  `Err(T)`). Closes golden 48. **Eu.3**: `match` on a primitive
  (Int / Bool / String) subject emitted `EnumTag` which lowered
  to `extractvalue i64 %v, 0` — LLVM rejects (i64 is not
  aggregate). Fixed at `mapanare/self/lower.mn::lower_match`:
  primitive subjects bypass the switch entirely and emit a
  sequential test cascade — jump to `arm[0]`; arms with literal
  patterns gain an implicit `subject == LIT` check at entry; the
  existing v4.79.0 P3 guard fall-through is preserved. Also
  `bind_ident_pattern` uniquifies its alloca SSA name with
  `tmp_counter` (mirrors `bind_one_pattern_field`'s pattern) so
  multiple `Some(x) if guard` arms don't collide on `%x.addr`
  under cascade dispatch. Closes golden 49. **Eu.4**: `match`
  with or-pattern + guards (e.g., `Some(0) | None | Some(x) if g
  | ...`) emitted N duplicate `i64 1` switch cases — LLVM rejects
  "duplicate case value in switch". Fixed via two coordinated
  changes in `mapanare/self/lower.mn`: (1) `build_match_arms`
  dedups switch entries by tag value (first arm wins; subsequent
  same-tag arms remain reachable through fall-through), default
  label set once (wildcard wins over earlier ident-non-enum); and
  (2) or-pattern arms with a literal-bearing alt emit a per-alt
  entry switch at the arm body — constructor alts with no payload
  (e.g., `None`) → direct match; constructor alts with literal
  sub-args (e.g., `Some(0)`) → payload-check block; default →
  next arm. New helper `is_builtin_variant_name` recognises
  `None`/`Some`/`Ok`/`Err` as variants when they appear as
  `IdentPat` (the parser does not wrap them in `ConstructorPat`).
  Closes golden 51. **Bb.\* — no seed refresh** (no C-runtime
  call shape changes). **Eu.\* arc CLOSED** — every v5.23.1 →
  v5.26.0 LINK_FAIL bug class is now a regression-locked PASS
  via `tests/llvm/test_async_link.py::test_deferred_link_failures`
  (10/10 PASS at HEAD; the four `pytest.xfail` short-circuits
  were removed). Source delta: ~17 LOC Python + ~14 LOC self-host
  (Eu.1) + ~10 LOC self-host (Eu.2) + ~95 LOC self-host (Eu.3) +
  ~150 LOC self-host (Eu.4) = ~286 LOC total (above the per-fix
  30-LOC ceiling but kept in scope to close the arc structurally;
  alternative was four small releases over 1–2 weeks).
  See `docs/roadmap/v5/v5.26.1/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.26.0** (ready, not tagged) — **Mb.7 + Mb.9 — codegen +
  Win64 ABI fixes; Mb.\* arc closeout.** Two real codegen fixes
  in the same release. Mb.7 closes the 3-release carry (v5.23.1
  → v5.24.0 → v5.25.0) of the i64/i1 tag-emit bug in
  `mapanare/self/emit_llvm.mn::emit_enum_tag`: the function
  zexted Result/Option i1 tags to i64 unconditionally, but the
  try-operator path declared its dest as `mir_bool()` (i1) and
  consumed it in `Branch`, producing invalid `br i1 %i64_val`.
  Surgical 5-LOC fix — honors `dest.ty.kind`: emit i1 directly
  for `TK_BOOL` consumers (try-op), keep zext for `TK_RESULT`/
  `TK_OPTION`/`TK_ENUM` (match → `switch i64`). Mb.9 closes the
  publish-run-#48 Windows OOM in the v5.23.2 Te.3.B.2 functions
  `__mn_count_user_brace_block_openers` and
  `__mn_emit_brace_deprecation_warning`: Python's `_do_call`
  uses a 64-byte byref threshold but `_decl_fn` uses 8 bytes on
  Win64 — the 16-byte `MnString` was passed by-value at the
  call site while the declaration said `ptr`, and gcc's Win64
  pass-by-hidden-pointer semantics for `MnString source` then
  read the data buffer's bytes 8..16 as the length. For
  `mnc_all.mn` (`// Auto-generated:`) those bytes are
  `g e n e r a t e` → `0x65746172656e6567` → `malloc(7e+18)` →
  OOM. Fixed via explicit handlers in Python's `_do_call` AND
  self-host's `emit_mir_call` routing both functions through
  the runtime-call path (mirrors the v5.23.1 Mb.1 pattern for
  `__mn_indent_to_braces`). **No C-runtime edits**; the C side
  was always correct. **No Bb.\* seed refresh** (no call shapes
  change); this corrects the PLAN. **Phase 0 disclosure** — the
  v5.23.1 SESSION_REPORT premise ("9 LINK_FAIL goldens share
  one bug") was wrong: only golden 47 had Mb.7's bug; goldens
  55-59 (the async cluster) never had it (always linked); 47/48/
  49/51 fail for distinct reasons (Eu.1..Eu.4 rescoped to
  v5.26.1). **Strict 3-stage fixed point preserved by
  construction at 239,993 lines / 0 diff** (21-release strict
  streak; +158 lines vs v5.25.0's 239,835 from the new dispatch
  arms). Goldens **95/95**. New `tests/llvm/test_async_link.py`
  (10 tests: 6 PASS + 4 documented xfail) — IR-invariant gate
  for the i64/i1 anti-pattern, link-and-run sanity for the async
  cluster, xfail markers documenting the four v5.26.1-rescoped
  bug classes (XPASS-strict so future fixes auto-flip them).
  New `tests/native/test_brace_funcs_windows_abi.py` (8 PASS)
  — IR-shape gate under forced Win64 triple plus Linux ctypes
  contract proving the C side is correct on SysV. **Mb.\* arc
  CLOSED** — every memory- and ABI-related panel finding
  through v5.22.0 + v5.23.2's Te.3.B.2 follow-on closed. See
  `docs/roadmap/v5/v5.26.0/SESSION_REPORT.md` and `AUDIT.md`.

- **v5.25.0** (ready, not tagged) — **Pv.\* — CI prevention
  infrastructure.** First release in the new **Pv.\*** sub-arc
  (structural pattern parallel to v5.24.0's **Hy.\***). Closes
  the class of failure where a CI-only test path catches a bug
  that could have been caught locally — typically because (a) a
  stale local artifact masks the bug on the developer machine,
  (b) a feature ships without an end-to-end test exercising it
  through the .mn-caller side, or (c) a test asset only runs on a
  non-Windows CI job. **Zero compiler edits. Zero runtime edits.
  Zero `mapanare/self/*.mn` source edits.** Strict 3-stage fixed
  point preserved by construction at **239,835 lines / 0 diff**
  (20-release strict streak; same line count as v5.24.1 because
  no source under `mapanare/self/` changed). Goldens **95/95**.
  **Pv.1**: new `tests/test_runtime_lib_lookup.py` (3 cases)
  locks `mapanare.test_runner._find_runtime_lib()` against
  re-introduction of v3.x-era `libmapanare_core.*` candidate
  names; sweeps stale shadows, asserts canonical name resolution,
  end-to-end links a tiny IR fragment that references
  `__mn_str_eq` against whatever archive the lookup returned.
  Pre-fix (commit `9dcbbb5` shipped on `dev` between v5.24.1 and
  v5.25.0) the lookup silently returned `None` because the
  candidate list still mentioned the v3.x names; a stale local
  `libmapanare_core.so` masked the regression on developer
  machines for 11+ releases. **Pv.2**: new
  `tests/bootstrap/test_preprocess_memcheck.py` (3 parameterized
  cases — brace-only, colon-only, mixed) runs `mnc-stage1
  preprocess` under valgrind. Locks the
  `__mn_indent_to_braces` brace-only fast-path against
  MnString-aliasing regressions; pre-fix the fast path returned
  the input MnString aliased and produced a double-free at
  function-end drop glue. Mirrors v5.23.1 Mb.3's grep-for-symbol
  pattern rather than `--error-exitcode=1` because `mnc-stage1`
  has a pre-existing single-shot leak from `__mn_argv` (~71 bytes,
  known and tracked since v5.23.1) that would otherwise produce a
  100% noise floor. **Pv.3**: extended `make ci-gates` (v5.24.0
  Hy.1) with new `clean-build-test` sub-gate — 9 sub-gates total,
  up from 8. Removes
  `runtime/native/libmapanare_*.{a,so,dylib,dll}` (the explicit
  `rm -f` is what makes the rebuild meaningful — `make clean`
  alone does not touch the archive), runs `make build-rt`, then
  runs `pytest tests/test_at_test_runtime.py
  tests/test_runtime_lib_lookup.py`. Catches the runtime-archive
  rename / relocation class structurally before any PR lands.
  **Pv.4**: new `scripts/validate_wsl.sh` runs the Linux pytest
  path end-to-end (`make build-rt` + `python3
  scripts/build_stage1.py` + `pytest tests/ -x -n auto`) from any
  CWD by resolving the repo root from the script's own location.
  New `dev.ps1 validate-wsl` mode shells out via `wsl -d Ubuntu`
  so a Windows host can produce the Linux pytest signal without
  leaving the dev loop. Optional pre-push hook at
  `scripts/hooks/pre-push.sample` (commented opt-in; not enabled
  by default — forcing the full suite on every push kills the dev
  loop and produces resentment, not safety). **Pv.5**: removed
  the v5.13.1 entry from CLAUDE.md "Planned / in-progress"
  section. The runtime-lib wiring (At.1's only remaining open
  item) shipped on `dev` between v5.24.1 and v5.25.0; the `@test`
  runtime is fully functional end-to-end. **Pv.6**: closes
  publish run #48 Linux + macOS tarball-smoke job failures.
  `.github/workflows/publish.yml` Linux + macOS smoke fixtures
  rewritten from `echo 'fn main(): print("...")' > /tmp/hello.mn`
  (single-line `fn x(): y` was the v5.14.0 SPEC §1009 forward
  promise that v5.21.1 H.4 explicitly rescoped to v6.0 — fixture
  authored against an unshipped feature) to multi-line colon via
  `printf 'fn main():\n    print(...)\n'`. New
  `tests/test_publish_smoke_fixtures.py` (2 cases) extracts every
  inline `.mn` fixture across four shapes (bash echo, bash
  printf, PowerShell here-string, bash heredoc) and parses each
  through `mapanare.parser.parse`; first test guards against a
  regex update silently dropping every fixture. **5 fixtures
  locked at v5.25.0 HEAD**. **Falsifiability**: every Pv.\* test
  documents a revert-and-restore round-trip in its module
  docstring; verified red-then-green for Pv.1 / Pv.2 / Pv.6 in
  the release session. **Out of scope** (held): Mb.7 (i64/i1
  tag-emit, 9 LINK_FAIL goldens) — v5.26.0; `to_terse` empty
  `#{}` rewriter bug — v5.27.0; `mnc fmt` long-line wrap +
  import sort — v5.27.0. See
  `docs/roadmap/v5/v5.25.0/SESSION_REPORT.md` and `PLAN.md`.

> Older release notes elided. See `docs/roadmap/ROADMAP.md` for the
> full ledger and `docs/roadmap/v5/v5.X.Y/SESSION_REPORT.md` for any
> specific release.

### Planned / in-progress

- **v5.12.0** — **Mc.6 / Wk.* — Windows SDK split.** Default
  Windows installs move to `mapanare-${V}-win-x64-sdk.zip`, which
  bundles one curated LLVM-MinGW/UCRT x86_64 SDK under `sdk/` so
  clean-machine `mnc run` / `mnc build` keep working. The opt-in
  `mapanare-${V}-win-x64-minimal.zip` is app-only and requires a
  user/system compiler. `MAPANARE_NO_BUNDLED_TOOLCHAIN=1` and legacy
  `MAPANARE_NO_BUNDLED_LLVM=1` select minimal. `toolchain/` must not
  appear in v5.12.0 Windows release ZIPs. See
  `docs/roadmap/v5/v5.12.0/WINDOWS_TOOLCHAIN_AUDIT.md`.

**Terseness arc — v5.13–v5.21 (shipped).** All terseness arc
releases (v5.13.0 → v5.21.0, plus the Sh.\* self-host rewrite at
v5.17.0 → v5.17.2) have shipped. See per-release SESSION_REPORTs
under `docs/roadmap/v5/v5.13.0/` through `docs/roadmap/v5/v5.21.0/`
for details, or `CHANGELOG.md` for summaries. The terseness thesis
is now visible in real code: cumulative source shrink of −13.8%
across `mapanare/self/` from v5.13.0 baseline.

- **v5.19.0** — **Te.3 + Dk.* — closeout.** Soft-deprecate
  `{}` (still parses, emits warning); hard removal scheduled
  for v6.0. Ship `mapanare/builder` + `mapanare/runtime`
  Docker images. See `docs/roadmap/v5/v5.19.0/PLAN.md`.
- **v6.0** — Borrow checker / multi-level alias analysis. Hard
  removal of `{}` (Te.3 from v5.19.0 was soft deprecation only).
  Closes Rt.04 (multi-level drop-glue alias analysis, rescoped
  v5.6.6 — struct→list→string depth-2). The only remaining
  v5.6.x v6.0 carry now that v5.6.12 closed Lk.1 at the
  source via destination passing.

See `docs/roadmap/v5/CLOSEOUT_ARC.md` and
`docs/roadmap/v5/PARITY_GAPS.md`.

## Pre-Push Validation (MANDATORY)

Run the full validation suite before any commit/push. Mirrors CI.
Writes results to `error.log`.

```powershell
.\dev.ps1                  # Full validate: black + ruff + mypy + gcc + pytest + WAT
.\dev.ps1 validate -Watch  # Validate then watch
.\dev.ps1 test             # pytest only
.\dev.ps1 lint             # Linters only
.\dev.ps1 fmt              # Auto-format
.\dev.ps1 e2e              # End-to-end tests
.\dev.ps1 bench            # Benchmarks
```

The validate step includes **WAT emission** for `examples/wasm/*.mn`
— catches WASM CI failures locally. `pytest` alone is NOT sufficient.

Quick partial checks:

```bash
python -m mapanare emit-wasm examples/wasm/hello.mn -o /dev/null
black --check . && ruff check . && mypy mapanare/ runtime/
pytest tests/semantic/test_types.py -v
pytest tests/parser/ -v
```

## Commands

```bash
make install          # pip install -e ".[dev]"
make build            # pip install -e .
make test             # pytest tests/ -v  (add -n auto for parallel)
make lint             # ruff + black + mypy
make fmt              # black + ruff --fix
make benchmark        # python -m benchmarks.run_all
make clean            # Remove caches + egg-info
```

### Core workflows

```bash
# Golden test harness (WSL for stage1)
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Full rebuild cycle (WSL)
bash scripts/rebuild.sh              # concat + build + goldens

# Self-hosted fixed-point (WSL)
python scripts/build_stage1.py
bash scripts/verify_fixed_point.sh --keep
```

### Debug tooling

Full command reference: **`docs/guides/tools_reference.md`**.

- `python scripts/ir_doctor.py <cmd>` — per-function IR diagnostics,
  baselines, valgrind mapping, stage2 pipeline
- `python scripts/mir_trace.py <file.mn> <fn>` — trace type inference
  in the Python lowerer
- `culebra <cmd>` — 49+ templates for IR + C diagnostics (Rust binary,
  WSL)

## Testing the Native Compiler

Golden corpus at `tests/golden/*.mn` (66 programs). Reference IR at
`tests/golden/*.ref.ll`.

Workflow:
1. Edit `mapanare/self/*.mn` or `mapanare/emit_llvm_text.py`
2. `python scripts/build_stage1.py`
3. `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
4. Harness compares mnc-stage1 output against Python bootstrap —
   shows which functions are missing or different.

Every run updates `tests/golden/BENCHMARKS.md`. Commit to track
regressions.

**Current baseline (v5.7.1):** **66/66 — preserved.** Sh.7
(closure-typed parameters) and B (or-pattern + identifier `None`
resolution) both closed in v5.7.0; v5.7.1 is a docs/polish release
with no compiler edits. The closure arc is closed; every test in
the corpus that defines "self-hosting" now passes through
`mnc-stage1`.

## Code Style

- **Black** (line length 100), **Ruff** (E, F, W, I), **MyPy** strict
- Target Python 3.11+ (bootstrap compiler)
- Dataclasses for AST nodes; type hints throughout

## Compiler Pipeline

```
.mn source
  → Lark LALR parser → AST (dataclasses)
  → Semantic checker
  → MIR lowering
  → MIR optimizer (O0–O3)
  → Emitter:
      ├→ emit_llvm_text.py  → LLVM IR (text)
      ├→ emit_c.py          → C source
      └→ emit_wasm.py       → WebAssembly (WAT/WASM)
```

Key modules in `mapanare/`:

| File | Role |
|---|---|
| `cli.py` | Entry point — command dispatch |
| `parser.py` | Lark transformer: parse tree → AST |
| `ast_nodes.py` | AST node definitions |
| `semantic.py` | Two-pass type checker + scope resolver |
| `mir.py` / `mir_builder.py` | MIR data + builder |
| `lower.py` | AST → MIR lowering |
| `mir_opt.py` | MIR optimizer passes |
| `emit_llvm_text.py` | LLVM IR generation |
| `emit_c.py` | C source generation |
| `emit_wasm.py` | WebAssembly (WAT) generation |
| `wasm_linker.py` | wasm-ld multi-module linking |
| `types.py` | **Single source of truth** for type system |
| `mapanare.lark` | LALR grammar, 13-level precedence |
| `tracing.py` | OpenTelemetry-compatible tracing |
| `diagnostics.py` | Rust-style structured error output |

## Runtime System

**Python runtime** (`runtime/`): `agent.py`, `signal.py`, `stream.py`,
`result.py`, `deploy.py`. **Legacy — being replaced by native .mn
stdlib.**

**Native C runtime** (`runtime/native/`): arena memory (no GC),
lock-free SPSC ring buffers, thread pool with work-stealing, coop
scheduler (mobile), agent lifecycle, TCP sockets, TLS (OpenSSL via
dlopen), file I/O, event loop (epoll/select), string interning,
memory profiling. Used by the LLVM backend.

## LLVM Backend Status

**Working:** functions, structs, enums, pattern matching, control
flow, type inference, generics, Result/Option, print, builtins, lists,
maps (Robin Hood), agents, signals (full reactivity), streams,
closures (env struct capture), traits, module imports, pipes,
multi-agent pipe definitions, string methods, GPU kernel dispatch.

**Not yet on LLVM:** tensor reshape, mutable views, stepped slices
(v5.x). Tensor surface stable since v4.45.0.

New LLVM features target `emit_llvm_text.py` (sole LLVM emitter).

## Type System (`mapanare/types.py`)

Single source of truth:
- `TypeKind` enum (25 kinds: INT, FLOAT, BOOL, STRING, LIST, MAP,
  OPTION, RESULT, SIGNAL, STREAM, AGENT, TENSOR, FN, etc.)
- `BUILTIN_FUNCTIONS`: print, println (deprecated), len, str, int,
  float, Some, Ok, Err, signal, stream
- `BUILTIN_CALL_MAP`: Mapanare → Python name mapping for emitters
- `PYTHON_TYPE_MAP`: Type → Python type mapping

## Self-Hosted Compiler (`mapanare/self/`)

10 modules, ~14,000 lines of Mapanare. Mirrors the Python bootstrap:

| Module | ~LOC | Role |
|---|---:|---|
| `ast.mn` | 781 | AST node definitions |
| `lexer.mn` | 575 | Tokenizer |
| `parser.mn` | 2,249 | Recursive descent parser |
| `semantic.mn` | 1,729 | Type checker + scope resolver |
| `mir.mn` | 791 | MIR data structures |
| `lower_state.mn` | 587 | Lowerer state |
| `lower.mn` | 3,602 | AST → MIR lowering |
| `emit_llvm_ir.mn` | 258 | LLVM type constants + IR builders |
| `emit_llvm.mn` | 3,206 | MIR → LLVM IR emitter |
| `main.mn` | 537 | Compiler driver |

**Patterns:** constructor functions (`let r: T = first_field; return
r`), state-threading, no struct literal syntax in grammar yet.

**Fixed-point:** NEAR (stage2.ll == stage3.ll except VERSION
placeholder). Strict hit at v4.134.0; currently NEAR per v5.3.2.

## Key Conventions

- Grammar: `mapanare/mapanare.lark` (bootstrap copy at `bootstrap/`)
- Emitters detect used features (agents/signals/streams) and import
  only as needed
- Builtins dispatched via `BUILTIN_CALL_MAP` in both emitters
- Self-hosted sources: `mapanare/self/*.mn`
- Language spec: `docs/SPEC.md` | Manifesto: `docs/manifesto.md` |
  RFCs: `docs/rfcs/`
- Roadmap: `docs/roadmap/ROADMAP.md` | Era READMEs:
  `docs/roadmap/v0/` → `docs/roadmap/v5/`
- Version: `VERSION` file
- Bootstrap frozen at v0.6.0 in `bootstrap/`

## Native-First Philosophy (v0.8.0+)

- **Stdlib in .mn:** new stdlib modules are `.mn`, compiled via LLVM.
  No more Python `.py` stdlib files.
- **C runtime as foundation:** OS primitives (sockets, TLS, file I/O)
  in C. Everything above (HTTP, JSON, routing) in Mapanare.
- **Test on LLVM:** every test runs on the LLVM backend.
- **Python entrypoint is bootstrap-only on release installs (v5.32.0+).**
  Windows SDK ZIPs ship a real native `mnc.exe` (built from
  `mapanare/self/` via the stage1 → stage2 self-compile cycle).
  **v5.33.0 extends this to Linux x86_64 and macOS arm64 release
  tarballs** — both ship `dist/mapanare/mnc` (native ELF / Mach-O)
  alongside the existing PyInstaller `mapanare` binary. The native
  `mnc` is invoked directly; no Python interpreter starts on
  `mnc --version`, `mnc run`, or `mnc build`. Linux aarch64 + macOS
  x86_64 tarballs are deferred to v5.34.0+ (no native runner /
  cross-compile infrastructure yet). The Python `mapanare`/`mnc`
  console-script remains for clean clones, pip-installs without
  the SDK, and the `bash scripts/build_from_seed.sh` bootstrap
  path. `mapanare/__main__.py` detects a sibling `bin/mnc[.exe]`
  and `os.execv`s to it; `MAPANARE_FORCE_PYTHON=1` opts out for
  dev/debug.

## GPU / WASM / Mobile (v2.0.0)

- **GPU** — CUDA + Vulkan via dlopen; `@gpu`/`@cuda`/`@vulkan`
  annotations; PTX/SPIR-V codegen; `stdlib/gpu/`.
- **WASM** — `mapanare/emit_wasm.py` → WAT, `wasm_linker.py` for
  wasm-ld. Targets: `wasm32-unknown-unknown`, `wasm32-wasi`.
- **Mobile** — `aarch64-apple-ios`, `aarch64-linux-android`,
  `x86_64-linux-android`. Coop scheduler + smaller defaults (4 KB
  arenas, 256-slot rings, 4 K string intern cap).

## Ecosystem Packages

- **Dato** (`github.com/Mapanare-Research/dato`) — DataFrame package
  (pandas+numpy replacement), in .mn
- `net/crawl`, `security/scan`, `security/fuzz` — agents-based
- AI/LLM drivers: `stdlib/ai/` (LLM, embeddings, RAG)

## CI

GitHub Actions on push/PR to `dev`:
- **ci** — black → ruff → mypy → pytest. Matrix: Python 3.11/3.12
- **native** — C runtime: gcc, ASan, TSan
- **wasm** — WAT emit → wat2wasm → wasmtime WASI examples
- **android** — NDK cross-compile: ARM64 + x86_64 `.o` + ELF verify

5,400+ tests across the full pipeline.

## Skills (slash commands)

| Skill | Description |
|---|---|
| `/golden` | 15/15 golden suite through mnc-stage1 + llvm-as |
| `/stage2` | Compile self-hosted modules + validate stage2 IR |
| `/rebuild` | concat + build mnc-stage1 + run goldens |
| `/ir-audit` | LLVM IR pathology audit with baselines |
| `/valgrind-map` | Valgrind + auto-map offsets to struct fields |
| `/bump-version` | Bump VERSION, README, CHANGELOG, localized docs |
| `/code-review` | 7-reviewer panel review |
| `/create-pr` | PR title + description from commits |
| `/simplify` | Review + fix changed code |
| `/autoresearch` | Autonomous experiment loop |
| `/culebra-scan` | Culebra v2.4.0 — 49+ templates (ABI / IR / Binary / Bootstrap / C). Workflow guide: `docs/guides/culebra.md` |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Mapanare** (31941 symbols, 67020 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Mapanare/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Mapanare/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Mapanare/clusters` | All functional areas |
| `gitnexus://repo/Mapanare/processes` | All execution flows |
| `gitnexus://repo/Mapanare/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
