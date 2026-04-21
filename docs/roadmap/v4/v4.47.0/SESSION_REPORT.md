# v4.47.0 Session Report — Stdlib AI/LLM + Arc 3 Bug Fixes

**Date:** 2026-04-12
**Type:** Arc 4 release 1 (library) + Arc 3 bug fixes (compiler)
**Self-Grade:** 9.3/10

---

## What This Release Did

Two things:
1. **Fixed v4.46.0 panel bugs** (Arc 3 closure): slicing inttoptr + scalar-tensor sub/div
2. **Shipped stdlib/ai/llm.mn enhancements** (Arc 4 start): ChatChunk streaming + env-based defaults

## Arc 3 Bug Fixes

### Bug 1: Slicing inttoptr (CRITICAL → FIXED)
`emit_llvm_text.py` now allocates stack arrays for starts/ends via `alloca [N x i64]` + GEP + store. Passes array pointers to `__mn_tensor_slice` instead of raw i64 values via `inttoptr`. 5/5 tensor goldens compile + validate.

### Bug 2: Scalar-tensor sub/div operand swap (MEDIUM → FIXED)
Added 4 reverse scalar runtime functions (`__mn_tensor_rsub/rdiv_scalar_f64/i64`) to `mapanare_gpu_builtins.c`. Lowerer uses `rsub/rdiv` for non-commutative scalar-first ops. `5.0 - tensor` now correctly computes `5.0 - tensor[i]`.

## Stdlib AI/LLM Additions

The existing `stdlib/ai/llm.mn` (1710 lines, 3 backends, tool calling, retries, consensus, chaining) was extended with:

- **ChatChunk type** (`delta`, `finish_reason`, `is_done` fields)
- **chat_stream()** function with SSE (OpenAI/Anthropic) and NDJSON (Ollama) parsing
- **default_config()** reads `MAPANARE_LLM_BACKEND`, `MAPANARE_LLM_API_KEY`, `MAPANARE_LLM_MODEL`, `MAPANARE_LLM_BASE_URL` env vars; defaults to Ollama at localhost:11434
- **split_lines()** helper for streaming response parsing

Final module size: 1909 lines.

## Examples

- `examples/ai/basic_chat.mn` — Ollama chat demo (no API key)
- `examples/ai/basic_stream.mn` — streaming demo (post-hoc chunking)

## Tests

- `tests/stdlib/ai/test_llm_types.py` — module compilation + type verification (10 tests)
- `tests/stdlib/ai/test_llm_offline.py` — offline verification of all providers, error mapping, streaming types, conversation, tool calling, retry, fallback, chain, consensus, cost estimation (18 tests)
- **28/28 tests pass**

## Limitations

- Streaming is post-hoc (full response then split) — real per-chunk streaming requires async I/O (v4.74.0)
- llama.cpp backend deferred to v4.48.0+
- No Ollama integration test in CI (requires local Ollama running)

## Test Counts

- New AI stdlib tests: 28
- Tensor-specific tests: 100 (unchanged)
- Full pytest: 4911+ pass (estimated)
- Tensor goldens: 5/5 compile + validate via llvm-as

## Files Changed

### Compiler fixes
- `mapanare/emit_llvm_text.py` — slicing stack array allocation + reverse scalar function support
- `mapanare/lower.py` — non-commutative scalar-tensor dispatch to rsub/rdiv
- `runtime/native/mapanare_gpu_builtins.c` — 4 new reverse scalar functions + rscalar macro

### Library additions
- `stdlib/ai/llm.mn` — ChatChunk, chat_stream, default_config, split_lines (+199 lines)
- `examples/ai/basic_chat.mn` — new
- `examples/ai/basic_stream.mn` — new
- `tests/stdlib/ai/` — 2 test files, 28 tests
- `docs/cookbook.md` — recipe 16 (AI: Chat with an LLM)

## Breaking Changes

None.
