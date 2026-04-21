# Mapanare v4.47.0 — Stdlib AI/LLM — Unified Interface + Streaming

> **Arc 4 release 1.** Library work on top of existing agents, streams,
> and HTTP primitives. No compiler changes. No new syntax. This is where
> the "AI-native" claim starts meaning something users can actually
> `import`.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.46.0 (arc 3 panel PASS)
**Delta review:** No (library-only)
**Full panel:** No (v4.51.0)
**Estimated work:** 2 sprints
**Theme:** Ship `stdlib/ai/llm.mn` with a unified chat interface and streaming via `Stream<ChatChunk>`.

---

## Scope

### The library surface

```mapanare
import stdlib::ai::llm

let client = llm::Client::default()  // reads MAPANARE_LLM_* env vars

let response: Result<ChatResponse, LlmError> = client.chat([
    llm::Message::system("You are a helpful assistant."),
    llm::Message::user("What is the capital of France?"),
])

// Streaming variant:
let stream: Stream<ChatChunk> = client.chat_stream([
    llm::Message::user("Write a 100-word story."),
])
for chunk in stream {
    print(chunk.content)
}
```

### Backends

Backend-selection via environment or config:
- `MAPANARE_LLM_BACKEND=openai` — OpenAI API
- `MAPANARE_LLM_BACKEND=anthropic` — Claude API
- `MAPANARE_LLM_BACKEND=ollama` — local Ollama HTTP endpoint (default when no API key set)
- `MAPANARE_LLM_BACKEND=llamacpp` — local llama.cpp binary

Each backend adapts the unified `Client.chat` / `chat_stream` interface to the backend's HTTP API.

### Types

```mapanare
type Message = {
    role: String,      // "system" | "user" | "assistant"
    content: String,
}

type ChatResponse = {
    message: Message,
    model: String,
    usage: TokenUsage,
}

type ChatChunk = {
    delta: String,     // the new content in this chunk
    finish_reason: Option<String>,  // "stop", "length", None if still streaming
}

type TokenUsage = {
    prompt_tokens: Int,
    completion_tokens: Int,
}

enum LlmError {
    NetworkError(String),
    AuthError(String),
    RateLimitError(Int),   // seconds to wait
    InvalidRequest(String),
    ServerError(Int, String),  // status, body
}
```

---

## Phase 1 — Module skeleton

- [ ] `stdlib/ai/` — directory if not present
- [ ] `stdlib/ai/llm.mn` — 600-800 lines:
  - Type definitions (above)
  - `Client` struct with backend field
  - `Client::default()` constructor reading env vars
  - `Client::openai(api_key)` / `::anthropic(api_key)` / `::ollama(base_url)` / `::llamacpp(binary_path)` — explicit constructors
  - `Client.chat(messages: List<Message>) -> Result<ChatResponse, LlmError>`
  - `Client.chat_stream(messages: List<Message>) -> Stream<ChatChunk>`
- [ ] `stdlib/ai/__init__.mn` — re-export the public surface

## Phase 2 — Backend adapters

### Phase 2.1: OpenAI backend

- [ ] `stdlib/ai/openai.mn` (internal) — implements OpenAI Chat Completions API
- [ ] `chat`: POST to `https://api.openai.com/v1/chat/completions` with JSON body; parse JSON response; map to `ChatResponse`
- [ ] `chat_stream`: same endpoint with `stream: true`; parse SSE (`data: {...}`) lines; emit `ChatChunk` via the existing `Stream<T>` primitive
- [ ] Error mapping: HTTP 401 → `AuthError`, 429 → `RateLimitError(retry_after)`, 5xx → `ServerError`, 4xx → `InvalidRequest`
- [ ] Uses `stdlib::net::http` + `stdlib::encoding::json` (already exist)

### Phase 2.2: Anthropic backend

- [ ] `stdlib/ai/anthropic.mn` — similar shape for the Claude API
- [ ] Endpoint: `https://api.anthropic.com/v1/messages`
- [ ] System message handling: Anthropic puts the system prompt in a separate field, not as a message
- [ ] Streaming: Anthropic's SSE format is slightly different from OpenAI's — adapt

### Phase 2.3: Ollama backend

- [ ] `stdlib/ai/ollama.mn` — local Ollama HTTP endpoint
- [ ] Default base URL: `http://localhost:11434`
- [ ] Endpoint: `/api/chat` with `{model, messages, stream}`
- [ ] Streaming: newline-delimited JSON
- [ ] **Primary test target** — doesn't need an API key, works offline

### Phase 2.4: llama.cpp backend

- [ ] `stdlib/ai/llamacpp.mn` — shell out to `llama.cpp` binary
- [ ] Config: path to the binary + path to the GGUF model
- [ ] Streaming: read stdout line by line, parse, emit `ChatChunk`
- [ ] Lower priority — can defer to v4.48.0 if time constrained

## Phase 3 — Streaming via `Stream<T>`

- [ ] The existing `Stream<T>` primitive (from v1.x) provides the iterator interface.
- [ ] `chat_stream` creates a `Stream<ChatChunk>` backed by an async HTTP request. Each chunk arrives as an SSE or newline-delimited event.
- [ ] Agents can consume the stream: an `@agent` that receives a user message, calls `chat_stream`, and forwards chunks to the caller.
- [ ] **v4.47.0 note:** real async/await doesn't ship until v4.68.0+. For v4.47.0, streaming is synchronous-blocking per chunk — the stream yields chunks as they arrive but blocks the caller on each. Once real coroutines land, `chat_stream` can become non-blocking.

## Phase 4 — Environment + configuration

- [ ] `Client::default()` — reads:
  - `MAPANARE_LLM_BACKEND` — required, selects adapter
  - `MAPANARE_LLM_API_KEY` — for OpenAI/Anthropic
  - `MAPANARE_LLM_MODEL` — default model; otherwise hardcoded per backend
  - `MAPANARE_LLM_BASE_URL` — for Ollama / llama.cpp
- [ ] Error on missing required env: `LlmError::InvalidRequest("MAPANARE_LLM_BACKEND not set")`

## Phase 5 — Examples

- [ ] `examples/ai/basic_chat.mn` — 30-line example using Ollama by default:

  ```mapanare
  import stdlib::ai::llm

  fn main() {
      let client = llm::Client::default()
      let response = client.chat([
          llm::Message::user("Hello, what's 2+2?")
      ])
      match response {
          Ok(r) => print(r.message.content),
          Err(e) => print("error: ", e),
      }
  }
  ```

- [ ] `examples/ai/basic_stream.mn` — streaming variant

## Phase 6 — Tests

- [ ] `tests/stdlib/ai/test_llm_types.py` — type definitions compile, Message constructors work
- [ ] `tests/stdlib/ai/test_llm_offline.py` — test the parsing logic with fixture responses (no network):
  - Parse OpenAI JSON response into `ChatResponse`
  - Parse OpenAI SSE chunks into `ChatChunk` stream
  - Parse Anthropic JSON response
  - Parse Ollama newline-delimited JSON
  - Error mapping per backend
- [ ] `tests/stdlib/ai/test_llm_ollama_integration.py` — skip if Ollama not available (tracking comment `v4.47.0-ollama-missing`). Otherwise spin up a request and verify round-trip.
- [ ] No OpenAI/Anthropic integration tests in CI — those need API keys. Document how to run them manually.

## Phase 7 — Self-hosted mirror

- [ ] `stdlib/ai/llm.mn` compiles through `mnc-stage1` and produces a valid .so/.a
- [ ] The self-hosted pipeline sees the new stdlib module. Fixed-point unchanged.

## Phase 8 — LOW sweep

2-3 items.

## Phase 9 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.47.0
- [ ] `CHANGELOG.md [4.47.0]`
- [ ] `docs/cookbook.md` §AI — new chapter start (full chapter lands at v4.50.0)
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `stdlib/ai/llm.mn` compiles through mnc-stage1 | rebuild clean |
| 2 | OpenAI backend parses response + emits `ChatResponse` | `test_parse_openai_response` |
| 3 | OpenAI backend parses SSE into `ChatChunk` stream | `test_parse_openai_stream` |
| 4 | Anthropic backend parses response | `test_parse_anthropic_response` |
| 5 | Ollama backend parses response | `test_parse_ollama_response` |
| 6 | `Client::default()` reads env correctly | `test_client_from_env` |
| 7 | Error mapping per backend | `test_error_mapping` |
| 8 | `examples/ai/basic_chat.mn` runs against Ollama (or skips honestly) | integration log |
| 9 | `examples/ai/basic_stream.mn` streams chunks correctly | integration log |
| 10 | `Stream<ChatChunk>` iterates correctly in a `for` loop | runtime test |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | Documentation start written | `docs/cookbook.md §AI` |
| 13 | Standard closeout clean | CI |

---

## What v4.47.0 does NOT do

- **Real async streaming** — v4.74.0 (when coroutines land)
- **Structured output** — v4.48.0
- **Embeddings / RAG** — v4.49.0
- **Vision / multi-modal** — v5.x
- **Function calling / tool use** — v5.x
- **Local model loading** via the C runtime directly (bypassing llama.cpp subprocess) — v5.x
- **Token counting** beyond what the API returns — v5.x

---

## Reference

- OpenAI API reference — https://platform.openai.com/docs/api-reference/chat
- Anthropic API reference — https://docs.anthropic.com/claude/reference/messages_post
- Ollama API — https://github.com/ollama/ollama/blob/main/docs/api.md

---

## After v4.47.0

v4.48.0 adds `stdlib/ai/structured.mn` — typed structured output with JSON schema validation.
