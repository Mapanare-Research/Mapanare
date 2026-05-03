# v5.36.0 — Js.\* — JSON completeness

**Status:** PLANNING
**Type:** Stdlib polish + new features. The existing `stdlib/json/`
covers the basics; v5.36.0 closes correctness gaps and adds the
features needed for the `ask` primitive (v5.40.0) to ship cleanly.
**Breaking:** No, except where the existing parser silently
accepted invalid input (those become hard errors — stricter, but
arguably bug-fix territory).
**Prerequisite:** v5.35.0 shipped (sqlite). v5.35.0 Sq.3.B has a
preview integration that v5.36.0 firms up.
**Estimated effort:** 1 session. ~600 LOC `.mn` polish + ~300 LOC
new code (streaming + reflection-based serde).

---

## Why this exists

The current JSON stdlib parses well-formed input and produces
canonical output, but has gaps:

1. Escape sequences are minimal — `\n \t \" \\` work but `é`
   sometimes mishandled in non-ASCII paths.
2. Number parsing accepts what JavaScript accepts, not what RFC
   8259 mandates (leading zeros, trailing dots).
3. No streaming parser — opening a 100 MB JSON file loads it
   all into memory first.
4. No pretty-print option.
5. Typed serialize/deserialize requires hand-written
   `to_json`/`from_json` per struct — no generic mechanism.

Item 5 is the load-bearing one: the v5.40.0 `ask` primitive
(`let plan: Plan = ask("...")`) needs *automatic* deserialization
from JSON to typed structs. Without it, `ask` requires a
boilerplate function per response type.

This is item #3 of the stdlib gap-close arc.

---

## Goals

1. **Js.1** — Parser correctness: full RFC 8259 compliance (escape
   sequences, number grammar, surrogate-pair unicode).
2. **Js.2** — Pretty-print: `to_json_pretty(value, indent: Int)
   -> String`.
3. **Js.3** — Streaming parser: `JsonStreamParser` reads from a
   `Stream<Bytes>`; emits events (`StartObject`, `Key`, `Value`,
   `EndObject`, `StartArray`, `EndArray`).
4. **Js.4** — Reflection-based serde. `to_json<T>(val: T) ->
   String` and `from_json<T>(s: String) -> Result<T, JsonError>`
   work for any user struct without `derive` annotations, by
   walking the type metadata at runtime.
5. **Js.5** — Tests: corpus of valid + invalid RFC 8259 cases;
   round-trip property tests for all primitive types and nested
   structures.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Js.1** | HIGH | **Parser correctness in `stdlib/json/parse.mn`.** Audit against the JSON test suite (jsoncheck / json-test-suite). Fix: surrogate-pair `😀` decoding; reject `01` and `.5` numbers; reject unescaped control chars in strings; reject trailing commas. List specific failures from the audit and fix one-by-one. | 3h |
| **Js.2** | LOW | **Pretty-print in `stdlib/json/format.mn`.** `to_json_pretty(v: JsonValue, indent: Int = 2) -> String`. Recursive formatter with indent stack. Default indent 2; `indent: 0` falls through to existing compact output. | 1h |
| **Js.3** | MEDIUM | **Streaming parser in `stdlib/json/stream.mn`.** Pull-based: `JsonStreamParser::from(reader: Stream<Bytes>) -> Self`; `parser.next() -> Option<JsonEvent>`. State machine with input buffer. Important for files / network responses where the value won't fit in RAM. ~250 LOC. | 4h |
| **Js.4** | HIGH (load-bearing for v5.40.0) | **Reflection-based serde in `stdlib/json/serde.mn`.** `to_json<T>(val: T) -> String` and `from_json<T>(s: String) -> Result<T, JsonError>`. Uses runtime type metadata (already present in `runtime/native/mapanare_typeinfo.c` for the existing `print` debug path; lift it). Field name → JSON key by default; `@json_field("name")` annotation for overrides. Handles nested structs, `Option<T>`, `List<T>`, `Map<String, T>`. **Required by v5.40.0 `ask` to map LLM JSON responses onto typed structs without per-type boilerplate.** | 5h |
| **Js.5** | HIGH (gate) | **Tests in `stdlib/json/tests/`.** `test_rfc8259.mn` runs the full RFC test corpus (commit list of fixtures into the repo at `stdlib/json/tests/fixtures/rfc8259/`). `test_streaming.mn` parses a 100-MB synthetic file and asserts memory ceiling. `test_serde_roundtrip.mn` round-trips 30 distinct struct shapes via Js.4. | 3h |
| **Js.6** | LOW | **JSON-column integration with sqlite.** Promote v5.35.0 Sq.3.B preview to first-class. `Value::Json(JsonValue)` variant; `Statement::bind` accepts `Value::Json`, stores as TEXT in sqlite (sqlite has `JSON1` extension, but for portability we store as TEXT and parse on read). | 1h |
| **Js.7** | LOW | **Doc page** at `docs/stdlib/json.md`. Examples for parse, pretty-print, streaming, typed serde. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.35.0 HEAD clean. Run JSON test
  corpus against current parser, log failures (Js.1 input).
- **Phase 1** — Js.1 parser fixes. Iterative — fix one failure,
  re-run corpus, repeat.
- **Phase 2** — Js.2 pretty-print (small).
- **Phase 3** — Js.3 streaming parser (the biggest single item).
- **Phase 4** — Js.4 reflection serde (the load-bearing one).
- **Phase 5** — Js.5 round out tests; Js.6 sqlite integration;
  Js.7 docs.
- **Phase 6** — Bump + tag.

---

## Out of scope

- **JSON5 / JSONC.** Variants with comments and trailing commas
  are downstream package territory.
- **JSONPath / JMESPath.** Query languages; downstream.
- **Canonical JSON / RFC 8785.** Niche; downstream if needed.
- **Schema validation.** JSON Schema is a separate library; not
  v5.x stdlib.
- **Tn.1** — **DEADLINE was v5.35.0**. If still open at
  v5.36.0, this release is gated on it landing first as v5.35.1.

---

## Risk

1. **Reflection-based serde performance.** Walking type metadata
   per call is slower than codegen'd serde (Rust serde, Go
   `json.Marshal`). Mitigation: it's good enough for v5.40.0's
   `ask` primitive (a 200ms LLM call dominates any 1-2ms serde
   overhead). Add a `@json_codegen` annotation in v5.x+ that
   monomorphizes the serde paths if profiling shows it matters.
2. **Streaming parser state-machine bugs.** Streaming parsers are
   notoriously tricky (incomplete input boundaries inside escape
   sequences, surrogate pairs split across reads). Mitigation:
   test against random splits of the same input — 100 random
   chunkings per fixture in Js.5 round-trip property tests.
3. **Backward compatibility.** Js.1 stricter parsing may reject
   inputs the old parser silently accepted. Mitigation: gate
   strictness behind `JsonParseOpts::strict` (default `true`,
   set to `false` for legacy callers); document the change in
   CHANGELOG `### Changed` section.
4. **Reflection runtime depends on TypeInfo metadata.** Currently
   only `print`'s debug path uses `mapanare_typeinfo`; serde
   would be the second consumer. Mitigation: confirm at Phase 0
   that all relevant struct shapes have full metadata in v5.36.0
   compiler output; file a Js.4.B item if any are missing.

---

## Success criteria

- ✅ Full RFC 8259 test corpus passes.
- ✅ `to_json_pretty(value, 2)` produces readable output.
- ✅ Streaming parser handles 100-MB file with bounded memory.
- ✅ `to_json` + `from_json<T>` round-trip on 30 different
  struct shapes.
- ✅ sqlite Js.6 integration: insert struct as JSON, retrieve
  + parse, struct equal to original.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- JSON correctness gaps.
- Reflection-based serde gap (the load-bearing one for `ask`).
- Sq.3.B preview promoted.

**Inherits to v5.37.0:**
- Tn.1 (assuming it landed at v5.35.x — confirm at Phase 0;
  if not, halt this release).
- macOS notarization, named-tzdb, Pg/MySQL drivers (LOW).
- Code-generated serde for hot paths (new LOW; v5.x+).
