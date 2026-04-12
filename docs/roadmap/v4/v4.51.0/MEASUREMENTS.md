# v4.51.0 Measurements

**Date:** 2026-04-12

## AI Stdlib Module Sizes

| Module | Lines | Functions (pub) | Types (pub) |
|--------|-------|-----------------|-------------|
| llm.mn | 2,029 | 35+ | 12 (Provider, Role, LLMError, ChatMessage, TokenUsage, LLMResponse, ToolDef, ToolCall, LLMConfig, ChatChunk, ExtractError, etc.) |
| embedding.mn | 933 | 20+ | 6 (EmbeddingError, EmbedProvider, EmbedConfig, EmbeddingResult, BatchEmbeddingResult, VectorStore) |
| rag.mn | 484 | 15+ | 4 (Chunk, RetrievalContext, Document) |
| structured.mn | 36 | 0 (docs only) | 0 |
| **Total** | **3,482** | **70+** | **22** |

## Test Coverage

| Test File | Tests | Scope |
|-----------|-------|-------|
| test_llm_types.py | 10 | Module compilation, type verification, env vars |
| test_llm_offline.py | 18 | Provider types, error mapping, streaming, conversation, tools, retry, chain, consensus, cost |
| test_struct_meta.py | 10 | __struct_meta compilation, optional fields, type mapping, extraction functions |
| test_embeddings_offline.py | 22 | Compilation, types, API surface, vector math, vector store |
| test_rag.py | 15 | Compilation, chunking strategies, context building, UTF-8 safety |
| test_ai_demos.py | 12 | Demo existence, cookbook structure, README content, Ollama integration (skip) |
| **Total** | **87** | |

## Arc 4 vs Pre-Arc 4 Comparison

| Metric | v4.46.0 (pre-arc) | v4.50.0 (post-arc) | Delta |
|--------|-------------------|-------------------|-------|
| AI stdlib modules | 3 (pre-existing) | 4 (+ structured.mn) | +1 |
| AI stdlib total lines | ~3,100 | 3,482 | +382 |
| AI stdlib tests | 0 | 87 | +87 |
| AI examples | 0 | 4 | +4 |
| Cookbook AI recipes | 0 | 4 (recipes 15-18 + chapter) | +4 |
| Compiler builtins | encode_struct, decode_to | + __struct_meta | +1 |
| P5 carry-forward | OPEN (3 cycles) | CLOSED | resolved |

## Compiler Changes (minimal)

| File | Change | Lines |
|------|--------|-------|
| semantic.py | __struct_meta type checking | +6 |
| lower.py | _lower_struct_meta + JSON schema gen | +42 |
| emit_llvm_text.py | Slicing stack array fix + reverse scalar handlers | +30 |
| mapanare_gpu_builtins.c | 4 reverse scalar + rscalar macro | +27 |
| **Total compiler delta** | | **+105** |
