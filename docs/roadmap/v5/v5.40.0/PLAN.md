# v5.40.0 — Ai.\* — `ask` as a language primitive

**Status:** PLANNING
**Type:** Manifesto delivery. The single highest-leverage release
in v5.x — first time the AI-native pitch shows up at the syntax
level rather than as a library API.
**Breaking:** No. `ask` is a new keyword; existing identifiers
named `ask` would shadow the keyword and trigger a deprecation
warning, but the keyword is grammar-level new.
**Prerequisite:** v5.39.0 shipped (full stdlib gap-close arc).
Specifically requires: Js.4 reflection serde (v5.36.0) for
typed-output deserialization, Ht.\* (v5.37.0) for HTTP transport
to provider, Cr.\* (v5.39.0) for HMAC-signed API key handling.
**Estimated effort:** 2 sessions. ~800 LOC `.mn` for the runtime
+ grammar/lower changes + ~400 LOC tests. Compiler edits are
small but load-bearing.

---

## Why this exists

Mapanare's manifesto says "AI-native compiled language with
first-class agents, signals, streams, and tensors." Today,
calling an LLM is a library API like in any other language —
import, configure, call, parse JSON. There's nothing
*language-level* about it.

`ask` makes the LLM call a first-class language construct:

```mn
let plan: Plan = ask("draft a 3-step plan to migrate from sqlite to postgres")
```

The compiler:

1. Sees the assignment target type `Plan` (a user struct).
2. Generates a JSON schema from `Plan` at compile time.
3. Lowers the call to `__mn_ask_runtime(prompt, schema, ResultType)`.
4. The runtime dispatches to a configured provider (Anthropic,
   OpenAI, local llama.cpp, etc.), passes the schema as
   structured-output constraint, parses the response back into
   the typed struct via Js.4 serde.
5. Returns `Result<Plan, AskError>` (or unwraps inline if the
   user wrote `ask` rather than `try ask`).

This is the *qualitative* win — every other language has to
write a function called `ask_for_plan`, hand-write the prompt
template, hand-write the JSON schema, and hand-write the
deserializer. Mapanare ships all of that as keyword-level sugar
backed by the type system.

---

## Goals

1. **Ai.1** — Grammar: `ask` keyword; expression form
   `ask(prompt: String) -> InferredFromContext`.
2. **Ai.2** — Type inference: target type drives the JSON schema
   and the result type; binding-context-driven.
3. **Ai.3** — Compile-time JSON schema generation from any user
   struct (lifts Js.4 type metadata).
4. **Ai.4** — Runtime: provider-agnostic dispatch via env-config
   (`MAPANARE_AI_PROVIDER`, `MAPANARE_AI_MODEL`,
   `MAPANARE_AI_API_KEY`). Built-in providers: Anthropic
   (Claude), OpenAI, local OpenAI-compatible (llama.cpp /
   ollama).
5. **Ai.5** — Error surface: structured `AskError` enum (network,
   rate-limit, schema-mismatch, content-filter, timeout).
6. **Ai.6** — Caching: optional response cache via env
   (`MAPANARE_AI_CACHE_DIR`). Same prompt + schema + provider +
   model = cache hit. Useful for tests and repeated runs.
7. **Ai.7** — Tests: deterministic unit tests via mock provider;
   live integration tests gated on env presence (skip if no API
   key set).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ai.1** | HIGH | **Grammar.** Add `ask` to `mapanare/mapanare.lark` as a primary expression: `ask_expr: "ask" "(" expr ")"`. Reserved keyword; existing `ask` identifiers in user code emit a deprecation warning (auto-renamable via `mnc fmt --rename-deprecated`). | 1h |
| **Ai.2** | HIGH | **Lowering.** `mapanare/lower.py` and `mapanare/self/lower.mn`: at the call site, use the binding context's expected type as the target type. If unbound (`let x = ask("...")`), default to `String`. Call site lowers to `__mn_ask_runtime(prompt: MnString, schema: MnString, type_id: i64) -> {ok: i1, payload: ptr | error: ptr}` shape. | 3h |
| **Ai.3** | HIGH | **Compile-time JSON schema generation.** New module `mapanare/schema_gen.py` (and `.mn` mirror): walk a `Type` and produce JSON Schema (Draft 2020-12). Maps `Int → integer`, `Float → number`, `String → string`, `Bool → boolean`, `List<T> → array`, `Map<String, T> → object with additionalProperties`, user struct → `object` with required + properties from fields, `enum E { A, B(Int) } → oneOf` representation. | 3h |
| **Ai.4** | HIGH | **Runtime in `stdlib/ai/ask.mn`.** `__mn_ask_runtime(prompt, schema, type_id)` reads `MAPANARE_AI_PROVIDER` env: `"anthropic"` → call Claude API; `"openai"` → call OpenAI; `"local"` → call configurable OpenAI-compatible endpoint. Each provider does HTTP POST (via Ht.\*), passes prompt + structured output schema, parses response, validates against schema, returns typed `Result<T, AskError>`. Streams not supported in v5.40.0 (sync only — see Out of Scope). | 5h |
| **Ai.5** | HIGH | **Error type and surface.** `enum AskError { Network(String), RateLimit { retry_after_seconds: Int }, SchemaMismatch(String), ContentFiltered(String), Timeout, ProviderUnavailable(String), MalformedResponse(String) }`. The `ask` expression desugars to `ask(...)?` style — propagates errors via `Result<T, AskError>`. User can opt into try-or-default with the `?` operator: `let plan: Plan = ask("...")?`. | 1h |
| **Ai.6** | MEDIUM | **Caching.** Optional cache when `MAPANARE_AI_CACHE_DIR` is set: hash `(provider, model, prompt, schema)` with SHA-256, look up file in cache dir, return cached response if present + valid (TTL configurable, default 24h). Cache writes are atomic (temp-file + rename). Disabled by default. | 2h |
| **Ai.7** | HIGH (gate) | **Tests in `stdlib/ai/tests/`.** `test_ask_unit.mn` uses a mock provider that responds with canned JSON — deterministic. `test_ask_schema.mn` validates schema generation for 15 distinct type shapes. `test_ask_error_paths.mn` simulates rate-limit, network, schema-mismatch errors. `test_ask_live.mn` is gated on `MAPANARE_AI_API_KEY` env presence — skipped in CI's `pytest -n auto` run, exercised in a separate manual `pytest -m live` invocation. | 4h |
| **Ai.8** | LOW | **Compiler emit-time JSON schema embedding.** Schemas are computed at compile time per `ask` site and emitted as static strings in the binary. Keeps runtime overhead to "send the prompt + a string" rather than "introspect the type system at runtime." | 2h |
| **Ai.9** | LOW | **Examples + manifesto demo.** `examples/ai/plan_generator.mn`: takes a goal string, returns a structured `Plan { steps: List<Step>, eta_days: Int }`. Demos the keyword-level ergonomic that no other language has. | 1h |
| **Ai.10** | LOW | **Doc page** at `docs/stdlib/ai.md`. Provider configuration, error handling, caching, schema generation rules, examples. Plus `docs/manifesto.md` gets a section pointing at `ask` as the first manifesto item delivered at syntax level. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.39.0 HEAD clean; entire stdlib
  gap-close arc shipped.
- **Phase 1** — Ai.3 schema generation; build standalone, test
  against many type shapes before hooking to grammar.
- **Phase 2** — Ai.1 grammar + Ai.2 lowering; thread through
  type inference.
- **Phase 3** — Ai.4 runtime with mock provider only (ignore
  network for now).
- **Phase 4** — Ai.5 error surface + Ai.4 real provider
  implementations (Anthropic first, OpenAI second, local third).
- **Phase 5** — Ai.6 caching, Ai.7 tests, Ai.8 compile-time
  schema embedding.
- **Phase 6** — Ai.9 examples + Ai.10 docs.
- **Phase 7** — Bump + tag.

---

## Out of scope

- **Streaming responses.** `ask` returns a single typed value;
  streaming requires a different shape (`stream_ask` or
  similar). v5.40.x or later release.
- **Tool / function calling.** Critical for agentic workflows
  but a separate language feature; defer to its own release.
- **Multi-turn conversations.** `ask` is one-shot; multi-turn
  is `Conversation` API in stdlib. Defer.
- **Vision / image inputs.** Type system can extend but not in
  v5.40.0.
- **Embedding generation.** Different shape (`embed(text)`); a
  natural follow-up release.
- **Provider-specific features** (Anthropic prompt caching,
  OpenAI assistant API, etc.). v5.40.0 is the lowest common
  denominator.
- **Cost accounting.** Useful but separate; downstream package.

---

## Risk

1. **The "AI-native" pitch is loud — implementation has to
   match.** If `ask` works on `String` only, or schema
   generation flakes on common struct shapes, the demo falls
   flat. Mitigation: Ai.3's 15-shape test suite is the bar; if
   any common shape (nested struct, optional fields, lists of
   structs, sum types) doesn't generate clean schema, block the
   release.
2. **Provider API drift.** Anthropic / OpenAI ship breaking API
   changes. Mitigation: pin specific API versions; abstract
   behind `Provider` trait; if a provider breaks, ship a
   v5.40.x patch with the new wire format. Don't promise
   forward compat.
3. **Structured-output guarantees vary by provider.** Anthropic's
   structured output is strict; OpenAI's `response_format:
   json_schema` is strict for newer models, lenient for older
   ones; local llama.cpp depends on the model. Mitigation:
   v5.40.0 validates the response against the schema in Mapanare
   *after* receiving it, regardless of provider; report
   `SchemaMismatch` if the response doesn't fit. User can retry.
4. **Live tests are flaky and expensive.** Mitigation: live
   tests are gated on env, never run in CI by default. Mock
   provider tests cover deterministic paths.
5. **Caching can mask bugs.** A cached response from a buggy
   prompt persists. Mitigation: cache key includes prompt hash;
   any prompt edit invalidates. Document the gotcha.

---

## Success criteria

- ✅ `let plan: Plan = ask("draft a 3-step plan").unwrap()`
  compiles, runs against Anthropic, returns a typed `Plan`.
- ✅ Schema generation produces valid JSON Schema for 15+
  struct shapes including nested structs, `Option<T>`, `List<T>`,
  `Map<String, T>`, sum types.
- ✅ Mock-provider unit tests are 100% deterministic.
- ✅ Live test against Anthropic + OpenAI + local both succeed
  (manual run).
- ✅ Cache hit returns identical result with no network call.
- ✅ All known error paths surface as typed `AskError` variants.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.
- ✅ `examples/ai/plan_generator.mn` demoable end-to-end.

---

## Carry-forward delta

**Closes:**
- "no language-level AI primitive" gap.
- **First manifesto arc release** — `ask` is the first item the
  manifesto promises that ships at syntax level rather than via
  library API.

**Inherits to v5.41.0:**
- Streaming `ask`, tool calling, multi-turn (new MEDIUMs;
  natural follow-ups).
- Older carries.
