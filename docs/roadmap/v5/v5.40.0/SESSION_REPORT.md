# v5.40.0 — Session Report — Ai.\* — `ask` runtime adapter

**Status:** Ready (not tagged).
**Manifesto-arc kickoff release.**

## Summary

Closed: **Ai.4 / Ai.5 / Ai.6 / Ai.7 / Ai.9 / Ai.10**.
Deferred to v5.41.0: **Ai.1 / Ai.2 / Ai.8** (`ask` keyword + typed
intrinsic).

The v5.40.0 PROMPT framed the release as "wrap an existing pipeline
behind a keyword, not build a runtime from scratch" — Phase 0 audit
confirmed this framing is exactly right. `__struct_meta::<T>()`,
`extract_with_schema`, `from_json::<T>`, `to_json::<T>`, `default_config()`,
`ExtractError`, `LLMConfig`, the full hosted-and-local provider
matrix — every load-bearing piece of the typed-output ergonomic
already exists at v5.39.7 HEAD. v5.40.0's substantive deliverable is
the runtime adapter that exposes them under one provider-agnostic
surface (`AskError`, `ask_text`, `ask_with_schema`,
`build_config_from_env`) plus an opt-in cache.

The keyword sugar — `let plan: Plan = ask("...")` — is the
manifesto-level ergonomic that justifies the release framing, but
shipping it cleanly requires either (a) a structural change in
`mapanare/lower.py::_specialize_fn` to rewrite nested `type_args`
through generic-function bodies, or (b) a new compile-time intrinsic
that emits ~80 LOC of Result-chaining MIR per call site. Either
threatens the 42-release STRICT streak; the PROMPT explicitly named
this trade-off and authorized fall-back to function-syntax. v5.40.0
takes the function-syntax path and tracks the keyword as v5.41.0
work.

## Pre-flight gates (Phase 0)

| Gate                                    | Result | Notes                                     |
|-----------------------------------------|--------|-------------------------------------------|
| `make ci-gates`                         | ✅     | All 9 sub-gates GREEN                     |
| `bash scripts/verify_fixed_point.sh`    | ✅     | STRICT — 241,898 lines / 0 diff           |
| `python3 scripts/test_native.py`        | ✅     | 95/95 goldens                             |
| `tests/stdlib/test_struct_json_runtime` | ✅     | 18/18 GREEN — Js.4.\* arc round-trip      |

## What shipped

### Ai.4 — Provider-agnostic env-driven config (Closed)

`stdlib/ai/ask.mn::build_config_from_env()` reads
`MAPANARE_AI_PROVIDER` / `MAPANARE_AI_MODEL` / `MAPANARE_AI_API_KEY` /
`MAPANARE_AI_LOCAL_URL` with fallback to `MAPANARE_LLM_*` (existing
`default_config()` env vars) for compatibility. Routes to the
appropriate `LLMConfig` constructor (`anthropic`, `openai`, `groq`,
`ollama`, `ollama_at`). Recognised provider names: `anthropic`,
`openai`, `groq`, `ollama`, `local` (alias for ollama). Defaults to
`anthropic` if API key is present, else `ollama` with `llama3.2`.

Per-provider model defaults match `default_config()`: anthropic →
`claude-sonnet-4-20250514`, openai → `gpt-4o`, groq →
`llama-3.3-70b-versatile`, ollama → `llama3.2`.

### Ai.5 — `AskError` (Closed)

8-variant enum: `Network(String)`, `RateLimit(Int)`,
`SchemaMismatch(String)`, `ContentFiltered(String)`, `TimedOut`,
`ProviderUnavailable(String)`, `MalformedResponse(String)`,
`DeserializeFailed(String)`. Round-trips through JSON via v5.39.7
ENUM serde if a caller wants to log it (externally-tagged shape:
bare `"TimedOut"` for unit variant, `{"Network": "msg"}` for
single-payload).

`map_extract_error(e: ExtractError) -> AskError` translates the
underlying retry-on-malformed-JSON engine's failures:
`LlmFailed` → `Network`, `ParseFailed` → `MalformedResponse`,
`ValidationFailed` → `SchemaMismatch`, `RetriesExhausted` →
`MalformedResponse`.

**Naming gotcha (load-bearing):** `LLMError` already defines a
`Timeout(String)` variant. A unit `Timeout` in `AskError` collided in
match-pattern resolution under concatenation — the pattern-matcher
resolved to the *other* enum's variant. Caught in Phase 1 smoke;
renamed to `TimedOut`. Documented in CHANGELOG and source preamble.

### Ai.6 — Optional response cache (Closed)

`stdlib/ai/ask_cache.mn`. Cache key is SHA-256 over
`(provider || "|" || model || "|" || prompt || "|" || schema)`.
Cache files live at `${MAPANARE_AI_CACHE_DIR}/${key}.json`. TTL
default 86400s (24h); `MAPANARE_AI_CACHE_TTL_SECONDS=N` overrides;
`N=0` disables expiry checking. Atomic writes (temp + rename).

**Self-contained — direct C-runtime externs only**, no `stdlib/fs.mn`
dependency. Discovered during Phase 3 that `stdlib/fs.mn` carries a
pre-existing IR codegen issue: `walk_dir`'s match-on-`Result<List<String>,
FsError>` lowers to `extractvalue ptr ... 0` then `zext ptr to i64`,
which `clang` rejects ("invalid cast opcode for cast from 'ptr' to
'i64'"). Reproduces on `dev` HEAD with no v5.40.0 changes — verified
via `git stash` + standalone fs-only smoke. **Out of scope** per
PROMPT (the LLVM emitter / lowerer is the v5.40.0 third rail). Tracked
as v5.41.0+ LOW.

### Ai.7 — Tests (Closed)

5 deterministic `.mn` test cases under `stdlib/ai/tests/` plus a
live-gated case. New pytest harness at
`tests/stdlib/test_ai_ask.py` (concat-pattern mirrors v5.34/v5.35/
v5.39.x): 5/5 GREEN at HEAD in 8.92s, 1 SKIPPED (live).

| Test                                | Coverage                                            |
|-------------------------------------|-----------------------------------------------------|
| `test_ask_error_variants.mn`        | 8 AskError variants + 2 map_extract_error cases     |
| `test_ask_config_env.mn`            | default path (no env) → ollama / llama3.2           |
| `test_ask_config_env_anthropic.mn`  | env=anthropic + API key → api.anthropic.com:443     |
| `test_ask_cache_roundtrip.mn`       | store → hit → miss-on-different-key                 |
| `test_ask_schema_shapes.mn`         | 7 struct shapes through `__struct_meta::<T>()`      |
| `test_ai_ask_live` (gated)          | end-to-end against real provider (skip without key) |

Live test only fires when `MAPANARE_AI_API_KEY` is set; never in CI.

### Ai.9 — Manifesto demo (Closed)

`examples/ai/plan_generator.mn`. Goal-string in, structured `Plan
{ goal: String, steps: List<Step>, eta_days: Int }` out. Renders the
steps with title + detail. Calls `ask_with_schema(prompt,
__struct_meta::<Plan>())` then `from_json::<Plan>(json_text)`.

### Ai.10 — Docs (Closed)

`docs/stdlib/ai.md` (~340 LOC) — quick reference, provider config
matrix, typed-output pattern, AskError table, cache configuration,
5 cookbook recipes, explicit "what's not here yet" list, migration
note. `docs/manifesto.md` gains the "first manifesto item shipped at
syntax level" section.

## What was deferred to v5.41.0

### Ai.1 / Ai.2 / Ai.8 — `ask` keyword + typed intrinsic + compile-time schema embedding

PROMPT scoped a reserved `ask` keyword with binding-context type
inference and an `ask_typed::<T>(prompt)` intrinsic. Phase 0 surfaced
two structural blockers:

1. **Naming collision.** `stdlib/ai/llm.mn:1114` already defines `pub
   fn ask(config: LLMConfig, prompt: String) -> Result<String,
   LLMError>`. A reserved keyword `ask` would shadow this across the
   entire ecosystem.

2. **Nested-generic intrinsic substitution does not propagate.**
   `mapanare/lower.py::_specialize_fn` substitutes parameter and
   return types when monomorphizing a generic function, but does not
   walk the body to rewrite nested `CallExpr.type_args`. Confirmed
   empirically: a user-level
   `fn parse_typed<T>(s: String) -> Result<T, JsonError> { da
   from_json::<T>(s) }` called as `parse_typed::<P>("{\"x\": 42}")`
   with `P { x: Int }` returns 0 (default-init) instead of 42.
   The inner `from_json::<T>` was lowered with the literal
   type-variable name "T" rather than the substituted "P", so the
   intrinsic dispatch in `_lower_from_json` resolved to an empty
   struct.

The compiler-edit budget required to close either was unsafe within
the v5.40.0 window — the PROMPT explicitly authorized fall-back:
"If the changes threaten STRICT, fall back to a function-syntax
shape … and revisit the keyword in v5.41.x. The strict streak is
more valuable than the keyword sugar."

v5.41.0 picks up the keyword work on the back of a `_specialize_fn`
body-walk fix that recursively rewrites `CallExpr.type_args` through
the substituted body.

Ai.8 (compile-time schema embedding) was already CLOSED at Phase 0
audit time — `__struct_meta::<T>()` (v4.48.0) does this. The keyword
sugar would have used it; without the sugar, callers compose
`__struct_meta::<T>()` at the call site explicitly.

## Compiler edits

**Zero.** No changes to `mapanare/lower.py`, `mapanare/semantic.py`,
`mapanare/parser.py`, `mapanare/mapanare.lark`,
`mapanare/emit_llvm_text.py`, or any `mapanare/self/*.mn`. STRICT
preserved by construction.

## Source delta

| File / area                           | Lines added | Notes                              |
|---------------------------------------|-------------|------------------------------------|
| `stdlib/ai/ask.mn`                    | ~155        | Ai.4 + Ai.5; new file              |
| `stdlib/ai/ask_cache.mn`              | ~110        | Ai.6; new file                     |
| `stdlib/ai/tests/*.mn`                | ~245        | 5 test files, new                  |
| `tests/stdlib/test_ai_ask.py`         | ~175        | Ai.7 harness, new                  |
| `examples/ai/plan_generator.mn`       | ~60         | Ai.9; new file                     |
| `docs/stdlib/ai.md`                   | ~340        | Ai.10; new file                    |
| `docs/manifesto.md`                   | ~6 LOC delta | manifesto-arc-kickoff section     |
| `docs/SPEC.md`                        | header re-sync block | v5.40.0 cut                |
| `CHANGELOG.md`                        | ~95         | Ai.\* entry                        |
| `CLAUDE.md`                           | release-notes entry | first manifesto-arc release |
| `docs/roadmap/v5/v5.40.0/PRE_PHASE_AUDIT.md` | re-written | Path A taken outcome           |
| `docs/roadmap/v5/v5.40.0/SESSION_REPORT.md` | this file | NEW                            |

## Closeout gates

- **STRICT 3-stage fixed point** — preserved by construction at
  v5.39.7's 241,898 lines / 0 diff (42-release strict streak).
- **Goldens 95/95** — preserved.
- **`make ci-gates`** — GREEN.
- **`tests/stdlib/test_ai_ask.py`** — 5 PASSED, 1 SKIPPED (live).
- **`tests/stdlib/test_struct_json_runtime.py`** — 18/18 GREEN
  (Js.4.\* arc round-trip preserved).
- **`check_doc_freshness.py`** — GREEN.
- **`check_changelog_honesty.py`** — GREEN.
- **No new C runtime exports.** `__mn_env_get` /
  `__mn_now_realtime_ns` / `__mn_sha256_str` / `__mn_hex_encode_str` /
  `__mn_file_*` are all preserved-from-prior-releases.

## Carry-forward delta

**Closed:**
- "no language-level AI primitive" gap (partial — runtime adapter
  shipped at function syntax; keyword sugar deferred).
- The manifesto-arc framing is now active.

**Inherits to v5.41.0:**
- Ai.1 / Ai.2 — `ask` keyword + binding-context type inference; gated
  on `_specialize_fn` body-walk fix.
- `_specialize_fn` body-walk fix itself (NEW MEDIUM): substitute
  nested `CallExpr.type_args` through specialized function bodies.
  Affects every user-level generic that calls a generic intrinsic.
- `stdlib/fs.mn::walk_dir` IR codegen issue (NEW LOW): match on
  `Result<List<String>, FsError>` produces `zext ptr to i64`. Pre-
  existing on dev HEAD; surfaced during Phase 3 cache-module work.
- Live-provider integration test against real Anthropic / OpenAI /
  ollama (Ai.7 follow-on; gated on env, skipped in CI).
- Streaming `ask_stream(prompt) -> Stream<String>` (PLAN out-of-scope
  carry).
- Tool / function calling (PLAN out-of-scope carry).
- Multi-turn `Conversation` ergonomic (PLAN out-of-scope carry).
- Older carries from v5.39.7.

## Aggregate state entering v5.41.0

- **0 HIGH**
- **2 MEDIUM** — `_specialize_fn` body-walk fix (gates Ai.1+Ai.2);
  macOS notarization (carry from v5.33.0 Nu.2).
- **~6 LOW** — `stdlib/fs.mn::walk_dir` IR codegen issue (NEW),
  streaming `ask`, tool calling, multi-turn, plus prior carries.

## Decision log

- **Phase 0 audit findings carry the release.** The original v5.39.0-
  vintage audit recommended Path A (defer v5.40.0; ship a multi-
  session Js.4.B fix arc as v5.39.1 + v5.39.2). Path A was taken;
  v5.39.1 → v5.39.7 closed the Js.4.\* arc item-by-item. v5.40.0 picks
  back up cleanly with the runtime adapter on top.
- **Function-syntax over keyword sugar.** Per PROMPT authorization;
  STRICT streak is more valuable than the manifesto headline. The
  manifesto demo is in `examples/ai/plan_generator.mn` regardless.
- **Self-contained cache module over fs.mn dependency.** Phase 3
  surfaced a pre-existing IR codegen issue in fs.mn's `walk_dir`. Two
  options: (a) fix fs.mn (out of scope per PROMPT), (b) rewrite cache
  to use direct C-runtime externs. Took (b); ~10 extra LOC, fully
  within the v5.40.0 deliverable surface.
- **TimedOut over Timeout.** Naming collision with `LLMError::Timeout(String)`
  was caught in Phase 1 smoke. Match-pattern resolution under
  concatenation silently picked the wrong enum. Renaming was the
  smaller fix vs. namespacing match patterns.
