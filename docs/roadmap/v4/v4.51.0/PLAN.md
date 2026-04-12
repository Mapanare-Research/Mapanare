# Mapanare v4.51.0 — Arc 4 Panel Release (Stdlib AI/LLM Close)

> **Fourth 5-minor cadence panel.** Arc 4 closes. Panel grades the
> stdlib AI/LLM work from v4.47.0-v4.50.0.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.50.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** The "AI-native" claim goes from marketing to measurable.

---

## Arc scope the panel grades

- v4.47.0: `stdlib/ai/llm.mn` — unified chat + streaming
- v4.48.0: `stdlib/ai/structured.mn` — typed structured output
- v4.49.0: `stdlib/ai/embeddings.mn` + `stdlib/ai/rag.mn`
- v4.50.0: End-to-end demos + cookbook chapter + README update

Specific questions for the panel:
- Does `import stdlib::ai::llm; Client::default().chat(...)` work end-to-end for a new user on a fresh install?
- Does the RAG agent demo actually retrieve relevant context for queries about the Mapanare SPEC?
- Does the cookbook chapter read as a realistic AI-native developer experience?
- Is `__struct_meta<T>()` a design decision the panel is comfortable with, or does it invite future hollow-feature risk?

---

## Phase 1 — Pre-panel sweep

- [ ] Run both end-to-end demos against a fresh Ollama install. Verify they work start-to-finish.
- [ ] Cookbook walkthrough: open the cookbook chapter and copy-paste each snippet into a new file, compile, run. Any snippet that doesn't work is a bug.
- [ ] Run the offline test suite for the AI modules — all passing.
- [ ] Integration tests with Ollama — all passing or cleanly skipped.

## Phase 2 — Documentation polish

- [ ] `docs/cookbook.md` §Building an AI Agent — final read-through
- [ ] `docs/SPEC.md` — if any AI-related claims are made, ensure they match the stdlib
- [ ] `docs/reference.md` — stdlib AI module references
- [ ] README.md — AI snippet works as shown

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — likely near-identical to v4.46.0 (no compiler changes in arc 4)
- [ ] AI-specific metrics:
  - Chat latency (Ollama, local model, short prompt, short response)
  - Streaming first-chunk latency
  - Structured extraction success rate (10 fixtures × 3 backends = 30 trials)
  - Embedding latency (Ollama, single text)
  - RAG end-to-end query latency (embed + top-k over 1000 chunks)
- [ ] `MEASUREMENTS.md` written

## Phase 4 — LOW sweep + pre-panel audit

- [ ] Any remaining LOW items from v4.46.0 ledger state
- [ ] Fact-check every v4.47.0-v4.50.0 SESSION_REPORT claim
- [ ] `PRE_PANEL_AUDIT.md` written

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.51.0. Arc: Arc 4 (stdlib AI/LLM).
- [ ] `mkdir -p .reviews/v4.51.0/` + pre-populate
- [ ] Spawn 7 reviewers. Special focus:
  - **Boa (Python/DX)** — primary for the library surface. Would a Python dev find `import stdlib::ai::llm; Client::default().chat(...)` natural? Compare to OpenAI's Python SDK.
  - **Coral (language design)** — is `__struct_meta<T>()` sound? Does it invite misuse?
  - **Cobra (C++/ABI)** — the HTTP/JSON plumbing. Are there layering issues?
  - **Rattler (LLVM)** — the `extract<T>` monomorphization path. Is the specialized compile-time schema generation correct?

## Phase 6 — Closeout

- [ ] `.reviews/v4.51.0/README.md` written
- [ ] If PASS: arc 4 closes. v4.52.0 opens arc 5 (compiler debt drain).
- [ ] If NEEDS WORK: recovery protocol; arc 5 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Chat agent demo runs end-to-end against Ollama | integration log |
| 2 | RAG agent demo runs end-to-end | integration log |
| 3 | Cookbook chapter snippets all compile | manual + `check_docs_drift.py` |
| 4 | Documentation polish complete | CI gate |
| 5 | AI-specific metrics recorded | `MEASUREMENTS.md` |
| 6 | `LEDGER_AUDIT.md` written | file exists |
| 7 | `PRE_PANEL_AUDIT.md` written | file exists |
| 8 | `.reviews/prompt.md` retargeted | diff |
| 9 | 7 reviewer files + README.md | listed |
| 10 | Panel verdict ≥ 9.0 zero NEEDS WORK (target) | README.md |
| 11 | SESSION_REPORT written | file exists |

---

## What v4.51.0 does NOT do

- **New features.** Panel release.
- **Compiler changes.** Arc 4 was library-only.

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 4

---

## After v4.51.0

v4.52.0 opens **Arc 5 (compiler debt drain)** — the four long-standing `CARRY_FORWARD.md` A-items scheduled here: A7 (self-hosted semantic wiring), A8 (UNRESOLVED/ERROR split), A9 (emit_c.mn decision), const Path A.
