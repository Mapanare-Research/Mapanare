# v4.48.0 Session Report — Stdlib AI/LLM — Structured Output

**Date:** 2026-04-12
**Type:** Arc 4 release 2 (compiler + library)
**Self-Grade:** 9.3/10

---

## What This Release Did

Introduced compile-time struct reflection and typed structured output:

1. **`__struct_meta::<T>()` builtin** — new turbofish intrinsic that generates a JSON schema string for any struct type T at compile time. Zero runtime overhead.
2. **`extract_with_schema()`** — sends JSON schema to an LLM, validates the response, retries on malformed JSON.
3. **`ExtractError` type** — structured error handling for extraction failures.

## Compiler Changes

### `__struct_meta::<T>()` (semantic.py + lower.py)

Added as a turbofish intrinsic alongside `encode_struct::<T>()` and `decode_to::<T>()`:
- `semantic.py:_check_call` — validates 1 type arg, 0 value args, returns STRING_TYPE
- `lower.py:_lower_struct_meta` — iterates `self._module.structs[T]`, maps field types to JSON Schema (`String→string`, `Int→integer`, `Float→number`, `Bool→boolean`, `List→array`, `Option<T>→not required`), emits schema as a compile-time constant string

The schema is embedded as a literal `[N x i8]` constant in the LLVM IR module — no runtime computation.

## Library Changes

### stdlib/ai/llm.mn (+116 lines → 2025 lines total)

- `ExtractError` enum (LlmFailed, ParseFailed, ValidationFailed, RetriesExhausted)
- `extract_with_schema(config, schema, text, max_retries)` — core extraction function
- `extract_text(config, schema, text)` — convenience wrapper (2 retries default)
- `validate_json_shape(json_str)` — finds JSON object boundaries in LLM response
- `build_extraction_prompt()` / `build_retry_prompt()` — schema-guided prompts

### stdlib/ai/structured.mn (documentation wrapper)

Thin module with usage documentation; re-exports from llm.mn.

## Test Counts

- `test_struct_meta.py` — 10 new tests (5 compilation + 5 structure verification)
- `test_llm_offline.py` — 18 existing (unchanged)
- `test_llm_types.py` — 10 existing (unchanged)
- **38/38 tests pass**

## Key Decisions

1. **`__struct_meta::<T>()` returns String, not StructMeta object** — avoids defining new runtime types; the JSON schema string is what the LLM needs.
2. **Extraction logic in llm.mn, not separate module** — avoids cross-module import issues; keeps the API surface unified.
3. **Prompt-based extraction, not native response_format** — works across all backends (Ollama, OpenAI, Anthropic). Native structured output support noted but not required.
4. **2 retries default** — configurable via `extract_with_schema(..., max_retries)`.

## Files Changed

- `mapanare/semantic.py` — `__struct_meta` type checking in `_check_call`
- `mapanare/lower.py` — `_lower_struct_meta` method (JSON schema generation)
- `stdlib/ai/llm.mn` — ExtractError, extract_with_schema, validate_json_shape
- `stdlib/ai/structured.mn` — documentation wrapper (new)
- `tests/stdlib/ai/test_struct_meta.py` — 10 tests (new)

## Breaking Changes

None. Additive only.
