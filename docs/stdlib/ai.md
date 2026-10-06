# `ai` — `ask` and the AI-native ergonomic (v5.40.0+)

The `ai` cluster ships a provider-agnostic LLM client driver
(`ai::llm`), structured-output extraction (`ai::structured` →
`extract_with_schema`), embeddings (`ai::embedding`), and as of
**v5.40.0** an `ask`-shaped runtime adapter on top:

- `ai::ask` — env-driven config, `ask_text`, `ask_with_schema`,
  `AskError`, and the `map_extract_error` translation surface.
- `ai::ask_cache` — opt-in response cache keyed on
  `(provider, model, prompt, schema)` SHA-256.

`ask_text(prompt) -> Result<String, AskError>` and
`ask_with_schema(prompt, schema) -> Result<String, AskError>` are the
two load-bearing entry points. Typed-output is composed at the call
site by combining `__struct_meta::<T>()` with `from_json::<T>` (see
[Typed output](#typed-output)).

> **v5.40.0 deferral note.** The original `ask` proposal (the
> manifesto-arc kickoff) targeted `ask` as a reserved keyword with
> binding-context type inference, so that
> `let plan: Plan = ask("draft a 3-step plan")` would Just Work. That
> shape requires a structural change in the lowerer: substituting
> generic type parameters into `from_json::<T>` intrinsic call sites
> within a specialized function body. The Phase 0 audit at v5.39.7
> HEAD confirmed nested-generic intrinsic dispatch does not propagate
> the substituted type, so v5.40.0 ships the runtime adapter at
> function-syntax. The keyword `ask` and the `ask_typed::<T>`
> intrinsic are tracked for v5.41.0, on the back of a
> nested-generic-intrinsic-substitution fix in `mapanare/lower.py`'s
> `_specialize_fn`.

## Quick reference

```mn
import ai::llm
import ai::ask
import encoding::json

// 1. Free-form chat. Provider read from env.
pon r: Result<String, AskError> = ask_text("What is Mapanare?")

// 2. Structured extraction. Pair __struct_meta + from_json.
struct Greeting { greeting: String }
pon schema: String = __struct_meta::<Greeting>()
pon json_r: Result<String, AskError> = ask_with_schema(
    "Reply with JSON {greeting: \"hi\"}",
    schema
)
match json_r {
    Ok(json_text) => {
        pon parsed: Result<Greeting, JsonError> = from_json::<Greeting>(json_text)
        match parsed {
            Ok(g)  => print(g.greeting),
            Err(e) => print("parse: " + e.message)
        }
    },
    Err(e) => print(ask_error_message(e))
}
```

## Provider configuration

`build_config_from_env()` reads, in priority order:

| Env                        | Fallback              | Default                      |
|----------------------------|-----------------------|------------------------------|
| `MAPANARE_AI_PROVIDER`     | `MAPANARE_LLM_BACKEND` | `anthropic` if API key, else `ollama` |
| `MAPANARE_AI_API_KEY`      | `MAPANARE_LLM_API_KEY` | `""` (empty)                 |
| `MAPANARE_AI_MODEL`        | `MAPANARE_LLM_MODEL`   | per-provider sensible default |
| `MAPANARE_AI_LOCAL_URL`    | `MAPANARE_LLM_BASE_URL` | `localhost` for ollama      |

Recognised providers: `anthropic`, `openai`, `groq`, `ollama`,
`local` (alias for ollama). Unknown provider name falls back to the
ollama default.

Per-provider model defaults:

- `anthropic` → `claude-sonnet-4-20250514`
- `openai`    → `gpt-4o`
- `groq`      → `llama-3.3-70b-versatile`
- `ollama` / `local` → `llama3.2`

Hosted providers (`anthropic`, `openai`, `groq`) require an API key in
`MAPANARE_AI_API_KEY`. Local providers (`ollama`, `local`) typically
don't need one.

## Typed output

`__struct_meta::<T>()` is a compile-time intrinsic (shipped at
v4.48.0; CLOSED at v5.40.0 Phase 0 audit) that emits a JSON Schema
string from a struct definition. Combined with
`ask_with_schema` and `from_json::<T>`, the round-trip looks like:

```mn
struct Plan {
    goal: String,
    steps: List<String>,
    eta_days: Int
}

pon schema: String = __struct_meta::<Plan>()
pon json_r: Result<String, AskError> = ask_with_schema(prompt, schema)
match json_r {
    Ok(json_text) => {
        pon parsed: Result<Plan, JsonError> = from_json::<Plan>(json_text)
        match parsed {
            Ok(p)  => use_plan(p),
            Err(e) => report(DeserializeFailed(e.message))
        }
    },
    Err(e) => report(e)
}
```

The Js.4.\* arc (v5.36.0 → v5.39.7) closes the typed-serde
round-trip for every common LLM-response shape: primitives, structs,
nested structs, `List<X>`, `Map<String, V>`, and tagged-union enums
(externally-tagged shape).

## Errors

`AskError` covers the full surface area of failures that a typed-output
call can hit:

| Variant                   | When                                                   |
|---------------------------|--------------------------------------------------------|
| `Network(String)`         | TCP/TLS error, DNS failure, connection refused         |
| `RateLimit(Int)`          | provider returned 429; payload is retry-after seconds   |
| `SchemaMismatch(String)`  | response was JSON but didn't match the requested schema |
| `ContentFiltered(String)` | provider's safety / moderation filter blocked the output |
| `TimedOut`                | request exceeded the configured timeout                |
| `ProviderUnavailable(...)` | 5xx, transient provider outage                        |
| `MalformedResponse(...)`  | response was not parseable JSON                        |
| `DeserializeFailed(...)`  | response parsed but failed to fit the typed struct      |

The `LLMError` family (used by the lower-level `ai::llm` driver) is
translated to `AskError` via `map_extract_error(e: ExtractError)`.

## Caching

Opt-in via `MAPANARE_AI_CACHE_DIR`. When set, `ask_cache_lookup` /
`ask_cache_store` work; when unset, both no-op and return `None`/
`false`. Cache key is `SHA-256(provider || "|" || model || "|" ||
prompt || "|" || schema)`. Cache writes are atomic (temp + rename).

```mn
pon k: String = ask_cache_key(provider, model, prompt, schema)
match ask_cache_lookup(k) {
    Some(json_text) => use_directly(json_text),
    None => {
        pon r: Result<String, AskError> = ask_with_schema(prompt, schema)
        match r {
            Ok(json) => {
                pon _: Bool = ask_cache_store(k, json)
                use_directly(json)
            },
            Err(e) => report(e)
        }
    }
}
```

TTL default 86400 seconds (24h); override with
`MAPANARE_AI_CACHE_TTL_SECONDS=N`. `N=0` disables expiry checking.

The cache is **eager** — any prompt edit invalidates because the key
includes the prompt's SHA-256. A user reporting "ask isn't responding
to my updated prompt" usually has a stale cache; check the dir.

## Cookbook

### Recipe 1 — Plan generator (the manifesto demo)

See `examples/ai/plan_generator.mn`. Takes a goal string, returns a
typed `Plan { goal, steps, eta_days }`. Run with
`MAPANARE_AI_PROVIDER=anthropic MAPANARE_AI_API_KEY=sk-ant-...`.

### Recipe 2 — Code reviewer

```mn
struct Review {
    severity: String,
    line: Int,
    suggestion: String
}

fn review_diff(diff: String) -> Result<Review, AskError> {
    pon prompt: String = "Review this diff and produce a JSON review: " + diff
    pon schema: String = __struct_meta::<Review>()
    pon r: Result<String, AskError> = ask_with_schema(prompt, schema)
    match r {
        Ok(j) => {
            pon p: Result<Review, JsonError> = from_json::<Review>(j)
            match p {
                Ok(rv) => { da Ok(rv) },
                Err(e) => { da Err(DeserializeFailed(e.message)) }
            }
        },
        Err(e) => { da Err(e) }
    }
    da Err(Network("unreachable"))
}
```

### Recipe 3 — Free-form `ask_text` for chat

```mn
match ask_text("Tell me a one-line joke") {
    Ok(text) => print(text),
    Err(e)   => print(ask_error_message(e))
}
```

### Recipe 4 — Switching providers via env

```bash
# Hosted
export MAPANARE_AI_PROVIDER=openai
export MAPANARE_AI_API_KEY=sk-...
export MAPANARE_AI_MODEL=gpt-4o
mnc run myprog.mn

# Local
unset MAPANARE_AI_API_KEY
export MAPANARE_AI_PROVIDER=ollama
export MAPANARE_AI_MODEL=llama3.2
mnc run myprog.mn
```

The same source compiles and runs against any provider — only the
env changes.

### Recipe 5 — Cache for deterministic test runs

```bash
export MAPANARE_AI_CACHE_DIR=$(pwd)/.ask-cache
mnc test  # first run: hits provider, populates cache
mnc test  # second run: serves from cache, no network
```

Cached responses persist across runs as ordinary JSON files; commit
them if you want reproducible CI.

## What's not here yet (v5.40.0)

- **`ask` keyword.** `let plan: Plan = ask("...")` is the v5.41.0
  candidate; gated on a nested-generic-intrinsic-substitution fix.
- **Streaming `ask`.** `ask_stream(prompt)` returning a `Stream<String>`
  of token chunks.
- **Tool / function calling.** Critical for agentic workflows; needs
  its own surface.
- **Multi-turn conversations.** Use `ai::llm::Conversation` for now.
- **Vision / image inputs.** Type-system extension; not v5.40.0.
- **Provider-specific features** (Anthropic prompt caching, OpenAI
  assistant API, etc.). v5.40.0 is the lowest common denominator.

## Migration / coexistence

`ai::llm::ask(config: LLMConfig, prompt: String) -> Result<String,
LLMError>` (the explicit-config form) is preserved unchanged. The
new env-driven `ai::ask::ask_text(prompt)` and
`ai::ask::ask_with_schema(prompt, schema)` are additive.

`extract_with_schema(config, schema, text, max_retries)` continues to
ship in `ai::llm` and is the underlying retry-on-malformed-JSON
engine for `ask_with_schema`.
