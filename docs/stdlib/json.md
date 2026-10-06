# `stdlib/encoding/json` — JSON parser, serializer, streaming

> Synced to v5.36.0 — Js.\* arc. Parser is now RFC 8259 strict;
> see "Strictness" below for inputs that previously parsed silently
> and now error.

## Quick reference

```mapanare
usa encoding::json

// Parse
let r: Result<JsonValue, JsonError> = parse(text)
let r: Result<JsonValue, JsonError> = decode(text)   // legacy alias

// Serialize
let s: String = to_json(value)                       // compact
let s: String = to_json_pretty(value, 2)             // 2-space indent

// Streaming (pull-based)
let mut p: JsonStreamParser = json_stream_open(text)
loop {
    let step: JsonStreamStep = json_stream_next(p)
    p = step.parser
    match step.event {
        Some(ev) => /* handle */,
        None     => break,
    }
}

// Typed serde (compile-time monomorphized)
let s: String = to_json::<MyStruct>(my_value)        // working
let r: Result<MyStruct, JsonError> = from_json::<MyStruct>(text)  // see "Js.4 status"
```

## Types

```mapanare
pub tipo JsonValue {
    | Null
    | Bool(Bool)
    | Int(Int)
    | Float(Float)
    | Str(String)
    | Array(List<JsonValue>)
    | Object(Map<String, JsonValue>)
}

pub tipo JsonError {
    message: String,
    line: Int,
    col: Int,
}

pub tipo JsonEvent {
    | StartObject | EndObject
    | StartArray  | EndArray
    | Key(String)
    | Value(JsonValue)
}

pub tipo JsonStreamParser { ... }
pub tipo JsonStreamStep { parser: JsonStreamParser, event: Option<JsonEvent> }
```

## Strictness

The v5.36.0 parser is RFC 8259 conformant on the
nst/JSONTestSuite corpus (283/283 CONFORM, 0 DEVIATE, 0 CRASH).
Inputs that previously parsed silently and now error:

- **Leading-zero numbers.** `01`, `-01`, `00.5` — all rejected.
  RFC 8259 §6 allows `0` standalone but not as a prefix to other
  digits in the integer part. To carry a value with a leading
  zero, encode it as a string: `"01"`.
- **Unescaped control characters in strings.** Bytes `U+0000`
  through `U+001F` inside a string literal must be escaped.
  Tab (`\t`), newline (`\n`), and carriage return (`\r`) all
  count — embed them via the corresponding `\x` escape.
- **Deep nesting.** Documents with more than 256 levels of
  nesting (arrays + objects combined) error with
  `Maximum nesting depth exceeded`. Pre-fix, deep nesting
  would crash the parser with a stack overflow.

The strictness changes are **not opt-out** in v5.36.0 — there
is no `JsonParseOpts { strict: false }` flag yet. If you have
a real-world corpus that needs the lenient pre-v5.36.0 behavior,
file an issue with the failing input.

## API

### `parse` / `decode` — full-document parser

```mapanare
pub fn parse(text: String) -> Result<JsonValue, JsonError>
pub fn decode(text: String) -> Result<JsonValue, JsonError>
```

`parse` is the v5.36.0 spelling; `decode` is the pre-v5.36.0
spelling preserved for backward compatibility. Identical
behavior. Returns `Ok(JsonValue)` on success or
`Err(JsonError)` with line/column.

### `to_json` / `encode` — compact serializer

```mapanare
pub fn to_json(value: JsonValue) -> String
pub fn encode(value: JsonValue) -> String
```

Same shape, same v5.36.0 / pre-v5.36.0 alias relationship as
`parse` / `decode`. Output has no whitespace between tokens.

### `to_json_pretty` / `encode_pretty` — indented serializer

```mapanare
pub fn to_json_pretty(value: JsonValue, indent: Int) -> String
pub fn encode_pretty(value: JsonValue, indent: Int) -> String
```

`indent` is the number of space characters per nesting level.
**`indent <= 0` falls through to `to_json` byte-for-byte** — no
trailing newline, no spaces between tokens. The recursive emitter
is only entered for `indent >= 1`.

### `json_stream_open` / `json_stream_next` — pull-based streaming

```mapanare
pub fn json_stream_open(text: String) -> JsonStreamParser
pub fn json_stream_next(p: JsonStreamParser) -> JsonStreamStep
pub fn json_stream_error(p: JsonStreamParser) -> Option<JsonError>
```

The pull API surfaces parser events one at a time. **Implementation
note:** v5.36.0 ships the API contract; under the hood the entire
document is parsed eagerly into an event list and `next` pops from
it. True chunked I/O with peak-RSS bounded smaller than document
size is deferred to a release that adds a native `Bytes` type and
a chunk-aware state machine.

Usage:

```mapanare
let mut p: JsonStreamParser = json_stream_open(text)
match json_stream_error(p) {
    Some(e) => print("parse error: " + e.message),
    None => {
        let mut done: Bool = false
        mien !done {
            let step: JsonStreamStep = json_stream_next(p)
            p = step.parser
            match step.event {
                Some(ev) => {
                    match ev {
                        StartObject => { /* { */ },
                        EndObject   => { /* } */ },
                        StartArray  => { /* [ */ },
                        EndArray    => { /* ] */ },
                        Key(k)      => { /* "key": */ },
                        Value(v)    => { /* atom or sub-tree */ }
                    }
                },
                None => { done = true }
            }
        }
    }
}
```

### `to_json::<T>` / `from_json::<T>` — typed serde

```mapanare
// Compile-time monomorphized; T must be a `tipo` struct.
let s: String = to_json::<T>(val)
let r: Result<T, JsonError> = from_json::<T>(text)
```

**`to_json::<T>` is fully working at v5.36.0.** Walks struct fields
at compile time, emits per-field encoding. Currently supports field
types: `Int`, `Float`, `Bool`, `String`, `Option<T>`. Field types
not yet supported: `List<T>`, `Map<String, T>`, nested struct,
enum variants. Calls on these types fall back to `str()` and
produce best-effort output.

**`from_json::<T>` ships compile-tested at v5.36.0; runtime is
deferred to v5.36.1.** The IR shape is correct and the build
links successfully, but the runtime path SEGVs in the field-
extraction step (a pre-existing v5.x drop-glue bug uncovered
by the v5.36.0 type-args propagation fix). The fix lands in
v5.36.1 — see Js.4.B in the v5.36.0 SESSION_REPORT for
investigation notes. Workaround for v5.36.0 callers: parse via
`decode(s)`, then construct the struct manually.

## Implementation notes

### Maximum nesting depth (Js.1.C)

Hardcoded constant `MAX_JSON_DEPTH = 256` in
`stdlib/encoding/json.mn`. Same default as sqlite, jansson, and
most production JSON parsers. Reachable inputs at depth 257+
return `Err(JsonError { message: "Maximum nesting depth exceeded",
... })`. Stack frames in the recursive descent path are
~200 bytes, so 256 levels uses ~50 KB of stack — well under
any reasonable thread stack budget.

### Cyclic struct serialization

`to_json::<T>` does not detect cycles. A struct that holds a
reference to itself (or a structurally cyclic graph) will run
the serializer until stack exhaustion. v5.36.0 leaves this as
undefined behavior; v5.40.0 may add a `JsonError::Cyclic` variant
with explicit visited-set tracking.

### Trailing data

`parse` rejects trailing non-whitespace after the JSON value:

```mapanare
parse("42 garbage")  // Err — "Unexpected trailing content"
parse("42  ")        // Ok — trailing whitespace is fine
```

## See also

- `stdlib/sql/sqlite.mn` — sqlite stdlib driver (v5.35.0).
  v5.36.0 plans to add `Value::Json(JsonValue)` for typed
  JSON column round-tripping; deferred to v5.36.1 with
  Js.4.B since it shares the runtime fix.
- `tests/stdlib/test_json.py` — 46 IR-level unit tests for
  the JSON module.
- `tests/stdlib/test_json_corpus_baseline.py` — v5.36.0 Js.5
  regression gate against the nst/JSONTestSuite corpus.
- `scripts/run_json_corpus.py` — corpus runner.
- `docs/roadmap/v5/v5.36.0/RFC_AUDIT.md` — per-fixture audit.
