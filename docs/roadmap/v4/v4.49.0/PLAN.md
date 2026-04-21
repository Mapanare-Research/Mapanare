# Mapanare v4.49.0 — Stdlib AI/LLM — Embeddings + RAG

> **Arc 4 release 3.** `stdlib/ai/embeddings.mn` and `stdlib/ai/rag.mn`
> provide the building blocks for retrieval-augmented generation:
> embedding a text corpus, computing similarity, top-k retrieval.

**Status:** DONE (2026-04-12)
**Breaking:** No
**Prerequisite:** v4.48.0
**Delta review:** No (library-only)
**Full panel:** No (v4.51.0)
**Estimated work:** 1.5 sprints
**Theme:** Make retrieval a first-class primitive in the AI stdlib.

---

## Scope

### Embeddings

```mapanare
import stdlib::ai::embeddings

let client = embeddings::Client::default()
let vec: List<Float> = client.embed("hello world")  // 1536-dim for OpenAI ada-002
```

Backend parity with the LLM client:
- `MAPANARE_EMBEDDING_BACKEND=openai|anthropic|ollama|llamacpp`
- `MAPANARE_EMBEDDING_MODEL=...`
- Falls back to Ollama's `nomic-embed-text` if no key

### RAG helpers

```mapanare
import stdlib::ai::rag

// Step 1: chunk a document
let chunks: List<String> = rag::chunk_text(document, chunk_size: 500, overlap: 50)

// Step 2: embed each chunk
let client = embeddings::Client::default()
let vectors: List<List<Float>> = chunks.map(|c| client.embed(c))

// Step 3: build an in-memory index
let index = rag::VectorIndex::new(chunks, vectors)

// Step 4: query
let query_vec = client.embed("what is the capital?")
let top_k: List<rag::SearchResult> = index.top_k(query_vec, k: 5)

for result in top_k {
    print(result.score, ": ", result.chunk)
}
```

### Types

```mapanare
type SearchResult = {
    chunk: String,
    score: Float,
    index: Int,
}

type VectorIndex = {
    chunks: List<String>,
    vectors: List<List<Float>>,
    // Methods: top_k, add, remove, len
}

enum EmbeddingError {
    NetworkError(String),
    AuthError(String),
    DimensionMismatch(Int, Int),  // expected, actual
    InvalidInput(String),
}
```

---

## Phase 1 — Embeddings module

### Phase 1.1: Client skeleton

- [ ] `stdlib/ai/embeddings.mn`:
  - `Client` struct + `default()` constructor reading env vars
  - `embed(text: String) -> Result<List<Float>, EmbeddingError>`
  - `embed_batch(texts: List<String>) -> Result<List<List<Float>>, EmbeddingError>` — parallel-friendly
- [ ] Backend adapters: OpenAI, Anthropic, Ollama, llama.cpp. Each implements the same interface.
- [ ] HTTP call via `stdlib::net::http` + JSON via `stdlib::encoding::json` — same pattern as v4.47.0.

### Phase 1.2: Backend adapters

- [ ] OpenAI: `POST /v1/embeddings` with `{model, input}`, parse `data[0].embedding`
- [ ] Anthropic: doesn't have an embedding API — raise `InvalidInput("Anthropic does not provide embeddings")`
- [ ] Ollama: `POST /api/embeddings` with `{model, prompt}`
- [ ] llama.cpp: shell out with `--embedding` flag; parse output
- [ ] Error mapping per backend

### Phase 1.3: Dimension consistency

- [ ] Every call to `embed` must return vectors of the **same dimension** for a given client. The client caches the dimension on first successful call.
- [ ] If a subsequent call returns a different dimension, raise `DimensionMismatch(expected, actual)` — indicates the backend switched models or something went wrong.

---

## Phase 2 — RAG helpers

### Phase 2.1: Chunking

- [ ] `stdlib/ai/rag.mn`:

  ```mapanare
  pub fn chunk_text(text: String, chunk_size: Int, overlap: Int) -> List<String>
  ```

- [ ] Chunk on sentence boundaries where possible (period + space); fall back to fixed-size chunks if sentences are too long.
- [ ] `overlap` parameter: consecutive chunks share `overlap` characters. Default 0.
- [ ] Handles edge cases: shorter than chunk_size (returns one chunk), multi-byte UTF-8 (do not split mid-character).

### Phase 2.2: Similarity

- [ ] `cosine_similarity(a: List<Float>, b: List<Float>) -> Float` — standard cosine similarity; dimension mismatch is an error
- [ ] `dot_product(a: List<Float>, b: List<Float>) -> Float` — for normalized vectors
- [ ] `euclidean_distance(a: List<Float>, b: List<Float>) -> Float` — for L2 distance
- [ ] All three: pure functions over `List<Float>`. Tensor versions if tensors prove more performant can wait for v5.x.

### Phase 2.3: Vector index

- [ ] `VectorIndex` struct:
  - `new(chunks: List<String>, vectors: List<List<Float>>) -> VectorIndex`
  - `top_k(query: List<Float>, k: Int) -> List<SearchResult>` — linear scan, cosine similarity, sort by score descending, take top k
  - `add(chunk: String, vector: List<Float>)` — append
  - `len() -> Int`
- [ ] Linear scan is fine for v4.49.0 scope. Anything smarter (HNSW, FAISS-style) is v5.x or a separate vector DB package.
- [ ] For chunks up to ~10k, linear scan with cosine similarity is sub-millisecond on modern CPUs.

---

## Phase 3 — Tests

- [ ] `tests/stdlib/ai/test_embeddings_offline.py`:
  - Parse OpenAI embedding response
  - Parse Ollama embedding response
  - Dimension caching
  - Dimension mismatch detection
- [ ] `tests/stdlib/ai/test_rag.py`:
  - `test_chunk_text_sentence_boundary`
  - `test_chunk_text_with_overlap`
  - `test_chunk_text_short_input`
  - `test_chunk_text_multi_byte_safe`
  - `test_cosine_similarity_orthogonal` — returns ~0
  - `test_cosine_similarity_identical` — returns 1.0
  - `test_cosine_similarity_dimension_mismatch` — error
  - `test_vector_index_top_k` — known fixture of 10 vectors with ground truth
  - `test_vector_index_add_grows_len`
- [ ] `tests/stdlib/ai/test_rag_ollama_integration.py`:
  - Embed 5 short texts, query one, verify the query retrieves itself as top result

---

## Phase 4 — Self-hosted mirror

- [ ] Both modules compile through `mnc-stage1`
- [ ] Fixed-point still 0

## Phase 5 — LOW sweep

2 items.

## Phase 6 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.49.0
- [ ] `CHANGELOG.md [4.49.0]`
- [ ] Cookbook: embeddings + RAG subsections
- [ ] SESSION_REPORT

---

## Exit criteria (12 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `embed` returns `List<Float>` of consistent dimension | offline test |
| 2 | `embed_batch` returns one vector per input | same |
| 3 | OpenAI backend parses response | `test_parse_openai_embedding` |
| 4 | Ollama backend parses response | `test_parse_ollama_embedding` |
| 5 | Dimension mismatch detected | `test_dimension_mismatch` |
| 6 | `chunk_text` respects sentence boundaries | `test_chunk_text_sentence_boundary` |
| 7 | `chunk_text` is multi-byte safe | `test_chunk_text_multi_byte_safe` |
| 8 | Similarity functions correct | unit tests |
| 9 | `VectorIndex.top_k` returns expected results on known fixture | `test_vector_index_top_k` |
| 10 | Ollama integration end-to-end | integration test |
| 11 | Fixed-point diff still 0 | `verify_fixed_point.sh` |
| 12 | Standard closeout clean | CI |

---

## What v4.49.0 does NOT do

- **Approximate nearest neighbor indices (HNSW, IVF, etc.)** — v5.x or separate package
- **Persistent vector storage** (SQLite, disk-backed) — v5.x
- **Reranking** (cross-encoder re-scoring top-k) — v5.x
- **Hybrid search** (keyword + vector) — v5.x
- **Multi-modal embeddings** (image, audio) — v5.x

---

## Reference

- Ollama embeddings — https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
- OpenAI embeddings — https://platform.openai.com/docs/guides/embeddings

---

## After v4.49.0

v4.50.0 builds end-to-end demos on top of the v4.47.0-v4.49.0 modules: a streaming chat agent and a RAG agent. Plus the full cookbook chapter.
