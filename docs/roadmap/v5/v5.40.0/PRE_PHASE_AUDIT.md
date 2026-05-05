# v5.40.0 — Pre-Phase Audit (Ai.\* — `ask` as a language primitive)

**Status: PROCEED.** v5.39.7 HEAD is clean and the hard prerequisite —
the entire Js.4.\* arc — closed across v5.39.1 → v5.39.7. Each minor
in the arc closed one `TypeKind` branch in the
`_encode_field_to_json` / `_decode_json_field` dispatch tables; at
v5.39.7 HEAD the typed-serde round-trip
`to_json::<T>` ↔ `from_json::<T>` works end-to-end for every common
LLM JSON response shape (primitive, struct, nested struct, `List<X>`,
`Map<String, V>`, externally-tagged enums).

The original v5.40.0 PRE_PHASE_AUDIT (drafted at v5.39.0 HEAD)
recommended Path A — defer v5.40.0; ship a multi-session Js.4.B fix
arc. **Path A was taken**: v5.39.1 → v5.39.7 closed the arc, item
by item, with regression-locked link-and-run tests. v5.40.0 picks
back up cleanly.

## Gate results at v5.39.7 HEAD

| Gate                                    | Result | Notes                                     |
|-----------------------------------------|--------|-------------------------------------------|
| Baseline VERSION = 5.39.7               | ✅     | Pre-bump state; v5.39.7 ready/not-tagged  |
| `make ci-gates`                         | ✅     | All 9 sub-gates GREEN                     |
| `bash scripts/verify_fixed_point.sh`    | ✅     | STRICT — 241,898 lines / 0 diff           |
| `python3 scripts/test_native.py`        | ✅     | 95/95 goldens                             |
| `tests/stdlib/test_struct_json_runtime` | ✅     | 18/18 GREEN — full Js.4 round-trip locked |
| `__struct_meta::<T>()` exists           | ✅     | `mapanare/lower.py:2646` + `semantic.py:1010` |
| `extract_with_schema` exists            | ✅     | `stdlib/ai/llm.mn:1987` — retry-on-malformed-JSON |
| `ExtractError` exists                   | ✅     | `stdlib/ai/llm.mn:1930` — 4 variants      |
| `default_config()` from env             | ✅     | `stdlib/ai/llm.mn:1845` — reads `MAPANARE_LLM_*` |
| `to_json::<T>` end-to-end               | ✅     | Js.4.D.1 (LIST), Js.4.E.1 (MAP), Js.4.F.1 (ENUM) |
| `from_json::<T>` end-to-end             | ✅     | Js.4.D.3, Js.4.E.2, Js.4.F.2 — round-trip closed |
| `crypto.sha256(s)` for cache keying     | ✅     | `stdlib/crypto.mn:70` — Cr.\* @ v5.39.0   |
| `fs.read_file / write_file / rename`    | ✅     | `stdlib/fs.mn` — atomic-write building blocks |
| `__mn_env_get` for env reads            | ✅     | `runtime/native/mapanare_html.c:662`      |

## PLAN items — current state

| ID    | PLAN claim                          | Reality at v5.39.7 HEAD               | Status      |
|-------|-------------------------------------|---------------------------------------|-------------|
| Ai.1  | Add `ask` keyword                   | NEW. Grammar / parser / AST work.     | NEW         |
| Ai.2  | Lowering with binding-context inference | NEW. Most subtle compiler change. | NEW         |
| Ai.3  | Compile-time JSON schema generation | **CLOSED.** `__struct_meta::<T>()` already emits a JSON Schema string at compile time. v5.40.0 lifts and reuses. | CLOSED      |
| Ai.4  | Runtime in `stdlib/ai/ask.mn`       | PARTIAL. `extract_with_schema` is the load-bearing pipeline; provider-agnostic env wrapper + `from_json::<T>` deserialization is NEW (~80 LOC). | PARTIAL     |
| Ai.5  | `AskError` enum                     | PARTIAL. `ExtractError` covers ~half of the variants. Reuse + extend, or wrap. | PARTIAL     |
| Ai.6  | Optional cache                      | NEW. `crypto.sha256` + `fs` primitives are in place; ~120 LOC `.mn`. | NEW         |
| Ai.7  | Tests                               | NEW. Mock-provider deterministic + live-gated. | NEW         |
| Ai.8  | Compile-time schema embedding       | **CLOSED.** Already what `__struct_meta` does. | CLOSED      |
| Ai.9  | Examples (`plan_generator.mn`)       | NEW.                                  | NEW         |
| Ai.10 | Docs (`docs/stdlib/ai.md`)          | NEW.                                  | NEW         |

## Compiler-edit budget

**Hard cap: ~50 LOC total** across grammar / parser / lower /
semantic in **both** Python and self-hosted compilers. Rationale:
compiler edits perturb IR; STRICT must hold across the
self-host's stage2 ↔ stage3 fixed point. If the keyword cannot be
landed in budget, **fall back to function-syntax shape** —
`ask_typed::<T>(prompt)` works without grammar edits — and ship the
keyword in v5.41.0 once the lowering shape is proven.

**Decision strategy:**

1. **Phase 1 (load-bearing)** — ship `ask_typed::<T>(prompt)` +
   `ask_text(prompt)` as ordinary `pub fn`s in `stdlib/ai/ask.mn`
   using existing turbofish syntax. Zero compiler edits. This is the
   manifesto-level deliverable. If Phase 2 (keyword sugar) defers,
   v5.40.0 still ships the runtime end-to-end.
2. **Phase 2 (sugar, optional)** — add `ask` as a primary
   expression. Lowers to `Call("ask_typed", [prompt],
   type_args=[T])` where T is the binding-context expected type.
   Surface to the lead if compiler-edit count exceeds 80 LOC across
   both compilers.

## Naming collision: existing `pub fn ask(config, prompt)`

`stdlib/ai/llm.mn:1114` already defines `pub fn ask(config:
LLMConfig, prompt: String) -> Result<String, LLMError>`. v5.40.0's
new function-style entry points are **distinct names**:

- `ask_typed::<T>(prompt)` — generic, env-driven config. (NEW)
- `ask_text(prompt)` — env-driven config, returns `Result<String, AskError>`. (NEW)

Existing `llm.ask(config, prompt)` is preserved unchanged — explicit
config form. Different module, different signature, no collision.

If Phase 2 adds `ask` as a keyword, the existing 2-arg `ask(config,
prompt)` form would become a parse-time conflict. Mitigation: the
keyword-form `ask` only matches `ask "(" expr ")"` (one arg);
explicit calls with two args route through the existing
`postfix_expr LPAREN arg_list RPAREN` path (resolved later via
identifier lookup in semantic). If the keyword reservation conflict
surfaces, defer Phase 2.

## Env-var naming

**Decision: `MAPANARE_AI_*`** (PROMPT) takes precedence; fall back
to `MAPANARE_LLM_*` (existing `default_config()`) for compatibility.

`build_config_from_env()` in `stdlib/ai/ask.mn` reads:

- `MAPANARE_AI_PROVIDER` (else `MAPANARE_LLM_BACKEND`, else
  `"anthropic"` if API key present, else `"ollama"`)
- `MAPANARE_AI_MODEL` (else `MAPANARE_LLM_MODEL`, else
  per-provider default)
- `MAPANARE_AI_API_KEY` (else `MAPANARE_LLM_API_KEY`, else `""`)
- `MAPANARE_AI_LOCAL_URL` (else `MAPANARE_LLM_BASE_URL`, else
  `"http://localhost"` for ollama)
- `MAPANARE_AI_CACHE_DIR` (cache opt-in; absent disables)
- `MAPANARE_AI_CACHE_TTL_SECONDS` (default 86400 — 24h)

## AskError shape

Strategy: **extend `ExtractError`** with the missing variants;
introduce `AskError` as an alias / wrapper. Smaller surface area
than a parallel hierarchy. Conversion is mechanical via
`map_extract_error`.

`ExtractError` variants today: `LlmFailed(String)`,
`ParseFailed(String)`, `ValidationFailed(String)`,
`RetriesExhausted(String)`.

PLAN's `AskError` adds: `Network(String)`,
`RateLimit { retry_after_seconds: Int }`,
`SchemaMismatch(String)`, `ContentFiltered(String)`, `Timeout`,
`ProviderUnavailable(String)`, `MalformedResponse(String)`,
`DeserializeFailed(String)`.

**Decision: define `AskError` as its own enum in
`stdlib/ai/ask.mn`** (Js.4.F closed enum encode/decode at v5.39.7,
so the error type round-trips through JSON cleanly if a caller wants
to log it). Map `ExtractError::*` → `AskError::*` in
`map_extract_error`.

## Diagnosis artifacts (preserved from v5.39.0 audit)

The original v5.39.0-vintage Js.4.B repro at `/tmp/jsdt.mn` no longer
SEGVs. v5.39.2 closed the runtime SEGV in `__mn_map_get` by deriving
the Map handle's key/val sizes from `MapInit.key_type`/
`MapInit.val_type` instead of the hardcoded `(8, 8, 0)` defaults.

## Decision

**Proceed with Phase 1 (function-syntax runtime adapter, zero
compiler edits) load-bearing. Phase 2 (keyword sugar) is best-effort
within compiler-edit budget; if STRICT regresses, defer to v5.41.0
with an honest CHANGELOG note.**
