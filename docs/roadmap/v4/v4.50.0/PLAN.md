# Mapanare v4.50.0 — AI/LLM End-to-End Demos + Cookbook Chapter

> **Arc 4 release 4.** Integration-layer release. Takes the
> v4.47.0-v4.49.0 library surface and builds real end-to-end demos:
> a streaming chat agent, a RAG agent. Plus the full cookbook chapter
> walking through each.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.49.0
**Delta review:** No
**Full panel:** No (v4.51.0)
**Estimated work:** 1 sprint
**Theme:** Ship the "Building an AI agent in Mapanare" demo that the v4.26.0 panel flagged as missing. Close Coral's LOW item 20 (examples/ light on agents/signals/streams demos).

---

## Scope

### Demo 1: Streaming chat agent

```mapanare
@agent
struct Chatbot {
    client: llm::Client,
    history: List<llm::Message>,
}

@handler(Chatbot, String)
fn handle_user_message(self: Chatbot, msg: String) -> String {
    self.history.push(llm::Message::user(msg))

    let stream = self.client.chat_stream(self.history)
    let mut response = String::new()
    for chunk in stream {
        response.push_str(chunk.content)
        emit(chunk.content)  // forward to observer via signal or log
    }

    self.history.push(llm::Message::assistant(response))
    return response
}

fn main() {
    let client = llm::Client::default()
    let bot = spawn Chatbot { client, history: [] }

    let reply = sync bot.handle_user_message("hello!")
    print("bot: ", reply)
}
```

### Demo 2: RAG agent

```mapanare
@agent
struct RagAssistant {
    llm_client: llm::Client,
    embed_client: embeddings::Client,
    index: rag::VectorIndex,
}

fn build_index(docs: List<String>) -> rag::VectorIndex {
    let embed_client = embeddings::Client::default()
    let chunks = docs.flat_map(|d| rag::chunk_text(d, chunk_size: 500, overlap: 50))
    let vectors = chunks.map(|c| embed_client.embed(c).unwrap())
    return rag::VectorIndex::new(chunks, vectors)
}

@handler(RagAssistant, String)
fn answer(self: RagAssistant, query: String) -> String {
    let query_vec = self.embed_client.embed(query).unwrap()
    let top: List<rag::SearchResult> = self.index.top_k(query_vec, k: 5)

    let context = top.map(|r| r.chunk).join("\n\n")
    let prompt = "Context:\n" + context + "\n\nQuestion: " + query

    let response = self.llm_client.chat([
        llm::Message::system("Answer the question based on the provided context."),
        llm::Message::user(prompt),
    ])

    return response.unwrap().message.content
}

fn main() {
    let docs = load_document_corpus("./docs/")
    let index = build_index(docs)
    let assistant = spawn RagAssistant {
        llm_client: llm::Client::default(),
        embed_client: embeddings::Client::default(),
        index,
    }

    let answer = sync assistant.answer("How do I configure the LSP?")
    print(answer)
}
```

---

## Phase 1 — Demo 1: Streaming chat agent

- [ ] `examples/ai/chat_agent.mn` — full worked example
- [ ] Handle cases: empty history, API error, stream interruption
- [ ] Makes the v4.47.0 streaming real in an end-to-end context
- [ ] Integration test: run against Ollama, verify agent responds; skip if Ollama absent

## Phase 2 — Demo 2: RAG agent

- [ ] `examples/ai/rag_agent.mn` — full worked example
- [ ] Ships with a small document corpus under `examples/ai/sample_docs/` — a dozen short text files about Mapanare itself (dogfooding)
- [ ] Integration test: run against Ollama, verify the agent retrieves relevant chunks for a few known queries; skip if Ollama absent

## Phase 3 — Cookbook chapter

- [ ] `docs/cookbook.md` §Building an AI Agent in Mapanare — full tutorial:
  1. Why Mapanare for AI: agents + signals + streams as first-class primitives
  2. Installing a backend: Ollama setup walkthrough
  3. Your first LLM call: the v4.47.0 `client.chat` example
  4. Structured output: the v4.48.0 `extract<T>` example
  5. Streaming responses: the v4.47.0 `chat_stream` example
  6. Building an agent: the v4.50.0 `@agent Chatbot` demo
  7. RAG with embeddings: the v4.49.0 + v4.50.0 `RagAssistant` demo
  8. Going to production: auth, rate limiting, observability
- [ ] 2000-3000 words, 6-8 code blocks (all parseable by `check_docs_drift.py`)
- [ ] Cross-references to §Agents, §Signals, §Streams in the SPEC

## Phase 4 — README update

- [ ] `README.md` — the front page still has a pre-recovery-arc narrative. Update the "What is Mapanare?" paragraph to mention:
  - Agents + signals + streams as first-class primitives (held since v1.x)
  - LLM stdlib (v4.47.0)
  - Tensor primitives (v4.42.0-v4.45.0)
  - LSP maturity (v4.37.0-v4.40.0)
- [ ] Add a "Hello AI" code snippet to the README — the 10-line chat demo from v4.47.0
- [ ] Close Coral v4.31.0 LOW item "examples/ light on demos" — mark CLOSED in `CARRY_FORWARD.md`

## Phase 5 — Tests

- [ ] `tests/examples/test_chat_agent_runs.py` — runs the demo against Ollama if present
- [ ] `tests/examples/test_rag_agent_runs.py` — runs the RAG demo with the sample corpus against Ollama
- [ ] Both skip honestly if Ollama is unavailable, with tracking comment `v4.50.0-ollama-missing`

## Phase 6 — LOW sweep

Final LOW sweep before the arc 4 panel. 2-3 items. Coral's "examples/" carry-forward closes here.

## Phase 7 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.50.0
- [ ] `CHANGELOG.md [4.50.0]`
- [ ] SESSION_REPORT

---

## Exit criteria (13 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `examples/ai/chat_agent.mn` compiles and runs | runtime log |
| 2 | `examples/ai/rag_agent.mn` compiles and runs | runtime log |
| 3 | Sample document corpus committed | `ls examples/ai/sample_docs/` |
| 4 | Chat agent streams correctly via `@agent` + `for chunk in stream` | integration test |
| 5 | RAG agent retrieves relevant chunks for known queries | integration test |
| 6 | Cookbook chapter written (2000+ words) | file exists, word count |
| 7 | All cookbook code blocks parse via `check_docs_drift.py` | CI gate |
| 8 | README.md updated with AI narrative + snippet | diff |
| 9 | Coral LOW item 20 (examples/ demos) CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 10 | Fixed-point still 0 | `verify_fixed_point.sh` |
| 11 | Integration tests skip honestly when Ollama absent | tracking comments |
| 12 | Self-hosted mirror compiles (no compiler changes, should be trivial) | build log |
| 13 | Standard closeout clean | CI |

---

## What v4.50.0 does NOT do

- **New library modules** — v4.47.0-v4.49.0 was the library work
- **Compiler changes** — no
- **New @agent semantics** — agents work as specified in v4.30.0+
- **Persistent agent state** — v5.x backlog if ever

---

## Reference

- [`v4.47.0/PLAN.md`](../v4.47.0/PLAN.md), [`v4.48.0/PLAN.md`](../v4.48.0/PLAN.md), [`v4.49.0/PLAN.md`](../v4.49.0/PLAN.md) — the library releases this integrates

---

## After v4.50.0

v4.51.0 is the **arc 4 panel release** — 5-minor cadence panel runs against the stdlib AI/LLM arc.
