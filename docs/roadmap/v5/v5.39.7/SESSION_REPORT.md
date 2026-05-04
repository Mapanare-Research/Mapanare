# v5.39.7 — SESSION_REPORT — typed-serde ENUM encode + decode (v5.39.x arc CLOSEOUT)

**Date:** 2026-05-04
**Tag:** v5.39.7 (ready, not tagged — lead's call)
**Arc:** Js.4.F (final piece of the v5.39.x typed-serde arc; **Js.4.\* arc CLOSED**)

## Summary

Two structurally distinct fixes shipping together as a sibling pair:

| Fix | Site | Bug |
|---|---|---|
| Js.4.F.1 | `mapanare/lower.py::_encode_field_to_json` | enum-typed struct fields fell into the `str()` fallback, emitting the literal `<?>` placeholder |
| Js.4.F.2 | `mapanare/lower.py::_decode_json_field` | enum-typed struct fields fell into the raw-jval return, producing silent shape mismatch (consumer received the JsonValue enum where a typed enum was expected) |

Both fixes are routed inside the existing STRUCT branch because
`_resolve_type_expr` cannot distinguish enum from struct at parse time.
The skip list `{Option, Result, JsonValue}` keeps compiler-internal
enums on their existing paths.

## Invariant decision (locked at PLAN)

**Externally tagged JSON shape**:

- No-payload variants encode as the bare string `"VariantName"`.
- Single-payload variants encode as `{"VariantName": <encoded>}`.
- Multi-payload variants encode as `{"VariantName": [<p0>, <p1>, ...]}`.

Rationale: most common shape in JSON-RPC, OpenAI / Anthropic
function-calling schemas, and Rust serde's default derive output;
round-trips trivially through the existing `_emit_list_decode_body`
for multi-payload variants. Bare-string for unit variants matches
Rust serde's `untagged()` for unit variants and is what most LLMs
produce in function-call responses.

Internally tagged (`{"tag": "V", ...}`) and adjacently tagged
(`{"tag": "V", "payload": ...}`) explicitly out of scope; tracked
as v5.40+ LOW.

## Phases

| Phase | Time | Outcome |
|---|---|---|
| 0 | ~10 min | Baseline 15/15 GREEN; encode `<?>` repro confirmed; self-host grep 0 matches |
| 1 | ~30 min | Audited `self._module.enums` shape (`[(variant_name, [payload_types])]`); confirmed skip list exhaustive; verified BinOpKind.EQ works for strings; sketched encode Switch + decode string-cascade |
| 2 | ~2 h | Implemented `_emit_enum_json_body` (encode, ~120 LOC); routed inside STRUCT encode branch with enum/struct disambiguation; tested encode end-to-end; implemented `_emit_enum_decode_body` (decode, ~190 LOC); routed inside STRUCT decode branch; tested all three variant shapes end-to-end |
| 3 | <1 min | Self-host grep returned 0 matches; STRICT preserved by construction |
| 4 | ~30 min | Wrote three new `.mn` regression tests; hit parser limitation `=> return EXPR` not supported (rewrote to block-form `=> { ok = ... }`); 18/18 GREEN; falsifiability locked per fix |
| 5 | ~45 min | bump 5.39.7; CHANGELOG `### Fixed` + `### Changed` (arc-closeout language); CLAUDE.md release-notes entry; SPEC sync to v5.39.7 cut; ci-gates GREEN; STRICT verified; goldens 95/95 |

## Arc retrospective (v5.39.0 → v5.39.7)

The v5.39.x arc was scoped at v5.39.0 as "JSON completeness +
typed-serde foundation." Actual delivery:

| Release | Tag | Surface |
|---|---|---|
| v5.39.0 | Cr.\* | Crypto stdlib (separate arc, ran first) |
| v5.39.1 | Js.4.B.1 | from_json IR-emission shape (no-import case) |
| v5.39.2 | Js.4.B.2 | from_json runtime SEGV closeout + harness |
| v5.39.3 | Js.4.C | to_json STRUCT field encoding |
| v5.39.4 | Js.4.D.1+2 | to_json LIST encode + from_json STRUCT decode |
| v5.39.5 | Js.4.D.3 | from_json LIST decode |
| v5.39.6 | Js.4.E.1+2 | Map<String,V> encode + decode |
| v5.39.7 | Js.4.F.1+2 | Enum encode + decode |

**Why 7 minor releases.** The Js.4 typed-serde surface shipped
Python-bootstrap-only at v5.36.0 and was compile-only-tested.
v5.40.0's Phase 0 audit surfaced that the surface was
**structurally incomplete** — only flat-primitive structs worked
end-to-end. Each subsequent release closed one TypeKind branch
in the encode + decode dispatch. The bundling discipline (one
TypeKind per release, with documented invariant decisions for
the harder cases) traded release count for falsifiability rigor
— every fix has a revert-and-restore test pair locked in the
regression suite.

**Pattern that emerged.** Both `_encode_field_to_json` and
`_decode_json_field` are dispatch tables on `TypeKind`. Each
v5.39.x minor adds one matching pair of branches + a helper
mirroring the encode-side mutable-Phi loop pattern (or the
multi-variant Switch for ENUM). The pattern is now battle-tested
for any future TypeKind extension.

**v5.40.0 Ai.\* unblocked.** The manifesto-arc `ask` /
`ask_typed::<T>` ergonomics layer can now assume any user-defined
struct + List + Map<String, _> + Enum combination round-trips
through JSON cleanly.

## Test infrastructure

Three new `.mn` test files under `stdlib/encoding/json/tests/`:

- `test_to_json_enum_field.mn` — encode all three variant payload
  shapes (no-payload "Active", single-payload "Pending(42)",
  multi-payload "Failed(\"oops\", 500)")
- `test_from_json_enum_field.mn` — decode all three shapes
- `test_to_from_enum_roundtrip.mn` — load-bearing round-trip

Each sub-case wrapped in its own helper function per the v5.39.5
caveat (multi-decode block-label collision). Match arms use
block-form actions (`=> { ok = ... }`) because the parser does
not accept `=> return EXPR` directly — documented in each test
file preamble; tracked as v5.40+ parser-ergonomic LOW.

**Falsifiability:**

- Revert encode branch (`if struct_name in self._module.enums:
  return self._emit_enum_json_body(...)` deleted) →
  `test_to_json_enum_field` + `test_to_from_enum_roundtrip` fail;
  `test_from_json_enum_field` still passes (decode is independent).
- Revert decode branch → `test_from_json_enum_field` +
  `test_to_from_enum_roundtrip` fail; `test_to_json_enum_field`
  still passes.

Both round-trips verified pre-commit.

## Aggregate state entering v5.40.0

- **0 HIGH** — Js.4.F.\* closed; typed-serde round-trip closed
  for every common LLM JSON shape.
- **1 MEDIUM** — macOS notarization carry from v5.33.0 Nu.2.
- **~5 LOW** — hash-dispatched enum decode (linear cascade
  sufficient for typical enums), internally / adjacently tagged
  shapes (alternative serde modes), custom serde rename
  attributes, parser ergonomic `=> return EXPR` (block-form
  workaround used in tests), prior carries.

**Js.4.\* arc CLOSED.** v5.40.0 manifesto-arc kickoff
(`ask` / `ask_typed::<T>`) fully unblocked.

## Source delta

- `mapanare/lower.py` — ~310 LOC (Js.4.F.1 helper + branch ~120 LOC;
  Js.4.F.2 helper + branch ~190 LOC; both routed inside existing
  STRUCT branches with enum-vs-struct disambiguation)
- `stdlib/encoding/json/tests/test_to_json_enum_field.mn` — ~75 LOC
- `stdlib/encoding/json/tests/test_from_json_enum_field.mn` — ~80 LOC
- `stdlib/encoding/json/tests/test_to_from_enum_roundtrip.mn` — ~80 LOC
- `tests/stdlib/test_struct_json_runtime.py` — ~22 LOC TEST_FILES
  extension
- `CHANGELOG.md` — ~115 LOC (### Fixed + ### Changed with
  arc-closeout language)
- `docs/SPEC.md` — ~50 LOC sync block (v5.39.6 cut → v5.39.7 cut)
- `CLAUDE.md` — release-notes entry + arc retrospective
- `VERSION` — `5.39.6` → `5.39.7` (mechanical)
- `README.md` (badge) + 3 localized README badges (mechanical)

## Followups

- Hash-dispatched enum decode (v5.40+ LOW) — linear cascade is
  fine until benchmarks show need.
- Internally / adjacently tagged shapes (v5.40+ LOW) — alternative
  serde modes; would need PLAN-level invariant decision.
- Custom serde rename attributes (v5.40+ LOW) — analogous to Rust
  serde's `#[serde(rename = "...")]`.
- Parser ergonomic `=> return EXPR` (v5.40+ LOW) — current
  workaround is block-form `=> { ok = ... }`; tests document the
  pattern in their preambles.
