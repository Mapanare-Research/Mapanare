# Mapanare v4.48.0 — Stdlib AI/LLM — Structured Output

> **Arc 4 release 2.** Typed structured output: given a struct type,
> extract a value of that type from an LLM response via JSON schema
> validation.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.47.0
**Delta review:** No (library-only)
**Full panel:** No (v4.51.0)
**Estimated work:** 1.5 sprints
**Theme:** `chat_structured<T>(messages, schema: T) -> Result<T, ParseError>` — type-parameterized LLM extraction.

---

## Scope

```mapanare
import stdlib::ai::llm
import stdlib::ai::structured

type Address = {
    street: String,
    city: String,
    zip: String,
    country: String,
}

let client = llm::Client::default()
let text = "John lives at 42 Main Street, Springfield 12345, USA."

let result: Result<Address, structured::ExtractError> =
    structured::extract<Address>(client, text)

match result {
    Ok(addr) => print(addr.city),  // "Springfield"
    Err(e) => print("extract failed: ", e),
}
```

### What's happening under the hood

1. `extract<T>` introspects the struct type `T` at compile time and generates a JSON schema.
2. It injects the schema into the LLM request as a system prompt or as a structured output directive (OpenAI's `response_format: json_schema`; Anthropic's `tool_use`; Ollama's `format: json`).
3. The LLM response is parsed as JSON and validated against the schema.
4. On parse failure, retry with a "please fix this parse error" message (bounded retries).
5. Returns a `Result<T, ExtractError>` or the validated struct.

### Generics + struct introspection

`extract<T>` is a generic function. At compile time, Mapanare's monomorphizer specializes `extract` for each concrete `T` used at a call site. The specialization has access to `T`'s struct layout — field names, field types — which lets it generate the JSON schema.

This requires **compile-time struct introspection**. Today, the semantic checker has this info internally (used for struct construction + destructuring). v4.48.0 exposes a small API for the stdlib to consume it.

---

## Phase 1 — Compile-time struct introspection API

### Phase 1.1: `@meta` reflection

- [ ] `mapanare/semantic.py` — add a compile-time builtin function: `__struct_meta<T>() -> StructMeta` that returns a struct describing `T`:

  ```mapanare
  type StructMeta = {
      name: String,
      fields: List<FieldMeta>,
  }

  type FieldMeta = {
      name: String,
      type_name: String,
      is_optional: Bool,
  }
  ```

- [ ] This is not runtime reflection — it's compile-time constant folding. The monomorphizer computes `StructMeta` at specialization time and inlines it as a literal.
- [ ] **Key constraint:** `__struct_meta<T>()` can only appear inside a generic function where `T` is a struct type. At non-struct instantiations, the call fails to compile.
- [ ] Alternative: a `@derive` decorator on struct definitions that generates a `T::meta() -> StructMeta` method. This is less magical and may be cleaner. Pick one in DESIGN.md.

### Phase 1.2: JSON schema generation

- [ ] `stdlib/encoding/jsonschema.mn` — new module (or extend the existing `stdlib/encoding/json.mn`).
- [ ] `schema_from_meta(meta: StructMeta) -> String` — builds a JSON schema string:
  ```json
  {
    "type": "object",
    "properties": {
      "street": { "type": "string" },
      "city": { "type": "string" },
      ...
    },
    "required": ["street", "city", "zip", "country"]
  }
  ```
- [ ] Handles nested types: `Option<T>` → not in `required`; `List<T>` → `{"type": "array", "items": ...}`; nested structs → recurse.

### Phase 1.3: Schema validator

- [ ] `stdlib/encoding/jsonschema.mn` — `validate(json: JsonValue, schema: String) -> Result<(), ValidateError>`:
  - Parse the schema.
  - Walk the JSON value, check each field against the expected type.
  - Return the first violation as a rustc-quality error.
- [ ] For v4.48.0, support a minimal JSON Schema subset: `type`, `properties`, `required`, `items`. Full JSON Schema is v5.x if demand.

## Phase 2 — Structured extraction

### Phase 2.1: `extract<T>`

- [ ] `stdlib/ai/structured.mn`:

  ```mapanare
  pub fn extract<T>(client: llm::Client, text: String) -> Result<T, ExtractError>
  where T: struct_shaped
  {
      let meta: StructMeta = __struct_meta<T>()
      let schema: String = jsonschema::schema_from_meta(meta)

      let prompt = build_extraction_prompt(text, schema)
      let response = client.chat([
          llm::Message::system("You extract structured data. Return only valid JSON matching the schema."),
          llm::Message::user(prompt),
      ])

      match response {
          Ok(r) => parse_and_validate<T>(r.message.content, schema),
          Err(e) => Err(ExtractError::LlmError(e)),
      }
  }
  ```

- [ ] `parse_and_validate<T>` — parse JSON, validate against schema, convert to `T` via struct construction.

### Phase 2.2: Retry logic

- [ ] If validation fails, retry with a feedback message that includes the parse error:
  ```
  "Your previous response failed to parse:  <error>. Please return valid JSON matching the schema."
  ```
- [ ] Bounded retries (default: 2).
- [ ] Configurable via `ExtractOptions` parameter (optional).

### Phase 2.3: Backend-native structured output

- [ ] If the backend supports native structured output (OpenAI's `response_format: json_schema`, Anthropic's `tool_use`), prefer it — more reliable than "please return JSON" in system prompts.
- [ ] Detect via `client.backend_capabilities()` — a new method that returns a struct with capability flags.
- [ ] Fall back to system-prompt JSON for backends that don't support native.

## Phase 3 — Tests

- [ ] `tests/stdlib/ai/test_structured_offline.py`:
  - `test_schema_from_meta_simple_struct` — Address → JSON schema
  - `test_schema_from_meta_nested_struct` — struct with a struct field
  - `test_schema_from_meta_optional_field` — Option<T> marked non-required
  - `test_schema_from_meta_list_field` — List<T> → array schema
  - `test_validate_valid_json_passes`
  - `test_validate_missing_required_field_fails`
  - `test_validate_wrong_type_fails`
  - `test_validate_extra_field_ok` — unknown extra fields ignored (lenient)
- [ ] `tests/stdlib/ai/test_structured_ollama.py` (integration, skip if Ollama missing):
  - `test_extract_simple_address_from_text`
  - `test_extract_retries_on_bad_json`
  - `test_extract_fails_after_max_retries`

## Phase 4 — Self-hosted mirror

- [ ] `__struct_meta<T>()` — implemented in both Python and self-hosted semantic passes
- [ ] The stdlib compiles through `mnc-stage1`
- [ ] Fixed-point still 0

## Phase 5 — LOW sweep

2 items.

## Phase 6 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.48.0
- [ ] `CHANGELOG.md [4.48.0]`
- [ ] Cookbook: structured extraction subsection
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `__struct_meta<T>()` returns correct metadata at compile time | unit tests |
| 2 | JSON schema generation for flat structs | `test_schema_from_meta_simple_struct` |
| 3 | JSON schema generation for nested structs | `test_schema_from_meta_nested_struct` |
| 4 | Optional fields handled | `test_schema_from_meta_optional_field` |
| 5 | Validator accepts valid JSON | `test_validate_valid_json_passes` |
| 6 | Validator rejects missing required fields | `test_validate_missing_required_field_fails` |
| 7 | `extract<T>` compiles for a concrete type | compile test |
| 8 | `extract<T>` returns correct struct for valid extraction | Ollama integration test |
| 9 | Retry logic fires on bad JSON | `test_extract_retries_on_bad_json` |
| 10 | Max retries honored | `test_extract_fails_after_max_retries` |
| 11 | Backend-native structured output preferred when available | integration test |
| 12 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 13 | Standard closeout clean | CI |

---

## What v4.48.0 does NOT do

- **Full JSON Schema support** — only a subset for v4.48.0
- **Recursive schemas** (a struct referring to itself) — v5.x
- **Enum-typed fields** — v4.49.0 or later
- **Non-struct output types** (`extract<List<Int>>` or `extract<String>`) — struct only
- **Runtime struct reflection** — no; compile-time only

---

## Reference

- OpenAI structured outputs — https://platform.openai.com/docs/guides/structured-outputs
- JSON Schema spec — https://json-schema.org/

---

## After v4.48.0

v4.49.0 adds embeddings and RAG helpers on top of the structured output infrastructure.
