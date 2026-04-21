# Mamba -- C/Runtime Review of Mapanare v4.51.0 (Arc 4 Panel)

**Reviewer:** Mamba
**Personality:** The C Minimalist -- terse, brutal, "delete this"
**Previous Version Reviewed:** v4.46.0 (PASS, 8.5/10, confidence 9/10)
**Verdict:** PASS
**Score:** 7.5 / 10
**Confidence:** 9 / 10

**Scope:** Arc 4 (v4.47.0-v4.50.0) -- AI stdlib. Four releases that
shipped the full `stdlib/ai/` package: LLM driver (2,029 lines),
embedding + vector store (933 lines), RAG chunking (484 lines),
structured extraction (36 lines). Plus 4 reverse scalar runtime
functions in `mapanare_gpu_builtins.c` (+32 lines).

**Files reviewed:**
- `stdlib/ai/llm.mn` (2,029 lines -- **NEW**)
- `stdlib/ai/embedding.mn` (933 lines -- **NEW**)
- `stdlib/ai/rag.mn` (484 lines -- **NEW**)
- `stdlib/ai/structured.mn` (36 lines -- **NEW**)
- `runtime/native/mapanare_gpu_builtins.c` (805 lines -- **+32** since v4.46.0)
- `mapanare/emit_llvm_text.py` (reverse scalar dispatch, lines 2797-2827)

## Executive Summary

3,482 lines of new Mapanare stdlib. 32 lines of new C. The C runtime
is essentially unchanged -- the 4 reverse scalar functions
(`rsub_scalar_f64`, `rdiv_scalar_f64`, `rsub_scalar_i64`,
`rdiv_scalar_i64`) are trivial one-liner delegates to the existing
macro-generated `tensor_rscalar_op_*` statics. No complaints there.

The problem is the stdlib. It is 3,482 lines of string concatenation.
Every JSON builder, every HTTP request, every response parser, every
vector store search -- all built on `result = result + ch`. Each `+`
calls `__mn_str_concat`, which `malloc`s a new buffer, copies both
sides, returns a new `MnString`. The AI stdlib is a malloc stress
test disguised as an HTTP client.

Score drops from 8.5 to 7.5. The C runtime is fine (+32 clean lines).
The stdlib ships allocation pathologies that will dominate runtime
cost in real AI workloads.

## 1. String Concatenation: How Many Allocations per `chat()` Call?

I counted the allocation sites in a single `chat()` call path for the
OpenAI provider with a 3-message conversation (system + user +
assistant history). Each `+` on a String is one `__mn_str_concat`
call = one `malloc`.

### Request building path:

| Function | Concatenations | Notes |
|----------|----------------|-------|
| `escape_json` per message (3x) | O(n) per message | Character-by-character: `result = result + ch` for every non-special char. A 500-char message = 500 mallocs. |
| `message_to_json` (3x) | 5 per message | Fixed template fragments |
| `messages_to_json` | 3 (separators) + 3 (message bodies) | |
| `build_openai_body` | ~10 | Model, messages, max_tokens, temperature, close brace |
| `https_post` header build | ~8 + 2*N_headers | "POST " + path + " HTTP/1.1\r\n" + Host + Content-Length + each header + Connection + body |

**Total request-build allocations for 3 messages averaging 500 chars:**

- `escape_json`: 3 * 500 = **1,500**
- `message_to_json`: 3 * 5 = **15**
- `messages_to_json`: **6**
- `build_openai_body`: **10**
- `https_post` headers: **~14**

**Conservative estimate: ~1,545 `malloc` calls just to build the HTTP
request.** Each one copies all preceding characters. Total bytes
copied: O(n^2) where n is the total message length. For a 3-message
conversation with 500 chars each, that is roughly 1500 * 750 = 1.1
million bytes of memcpy for a 1,500-byte payload.

### Response parsing path:

| Function | Concatenations | Notes |
|----------|----------------|-------|
| `recv_full_tls` | 1 per chunk | `response = response + chunk`. O(response_size / 8192) chunks. For a 4KB response: 1 concat. For 100KB: ~13. Acceptable. |
| `extract_http_body` | O(body_len) | `body = body + raw.char_at(pos)` -- **character by character from \r\n\r\n to end**. A 4KB response body = 4,096 mallocs. |
| `jget` (called ~6 times) | O(key_len) per call for `found_key` + O(value_len) for value extraction | Both built char-by-char. |
| `jget_str` | O(value_len) | Char-by-char unescape. |

**Total response-parse allocations for a 4KB response body:**

- `extract_http_body`: **~4,096**
- `jget` (6 calls, avg 20-char keys + 100-char values): 6 * 120 = **720**
- `jget_str` (3 calls, avg 200-char values): 3 * 200 = **600**

**Conservative estimate: ~5,416 `malloc` calls to parse the response.**

### Grand total per `chat()` call:

**~6,961 string allocations.** Nearly 7,000 `malloc` + `free` pairs.
For comparison, the equivalent in C would be: 1 allocation for the
request buffer, 1 for the response buffer, and a handful of pointer
arithmetic operations. Zero mallocs for JSON parsing (just index into
the response string).

**This is not a language limitation.** Mapanare has `List<T>` with
amortized O(1) push. A `StringBuilder` pattern -- accumulate chars
in a `List<Int>` (byte values), then convert to String once at the
end -- would reduce `escape_json` from 500 mallocs to ~10 list
pushes (amortized). The `extract_http_body` function could use
`String.substr(pos, slen)` instead of char-by-char concatenation --
the `substr` method exists and is used elsewhere in the same file
(line 1798).

**`extract_http_body` is the worst offender.** It finds the
`\r\n\r\n` boundary, then copies the rest of the response one
character at a time. This function exists identically in both
`llm.mn` (line 677) and `embedding.mn` (line 546). Both are O(n^2).
Both should be `da raw.substr(pos, slen)`. One line. Delete 7 lines.

### Duplicated code across llm.mn and embedding.mn:

The following functions are copy-pasted verbatim between the two
files:

- `escape_json` (19 lines each)
- `skip_ws` (~8 lines each)
- `skip_json_value` (~40 lines each)
- `jget` (~44 lines each)
- `jget_str` (~18 lines each)
- `jget_int` (~4 lines each)
- `HttpResult` struct + constructors (~8 lines each)
- `recv_full_tls` / `recv_full_tcp` (~10 lines each)
- `parse_http_status` (~8 lines each)
- `extract_http_body` (~12 lines each)
- `https_post` (~30 lines each)

That is approximately **200 lines** duplicated. Factor into a shared
`stdlib/ai/http_json.mn` or `stdlib/text/json.mn`. The language has
`usa` (import). Use it.

## 2. Vector Store: O(n) per Query, O(n*k) for Top-K

`embedding.mn:859-901`, `store_search`:

```
mien i < count {
    pon score: Float = cosine_similarity(query, store.entries[i].vector)
    // ... build SearchResult, push to scored ...
    i = i + 1
}
// Selection sort for top-K
mien k < top_k {
    mien j < scored_count {
        // linear scan for max
    }
}
```

**Complexity:** O(n * d) for similarity computation (n entries, d
dimensions) + O(n * k) for selection sort. Total: O(n * (d + k)).

For a RAG store with 10,000 documents, 1536-dimension embeddings,
and k=5: 10,000 * 1,536 = 15.36 million float multiplications +
10,000 * 5 = 50,000 comparisons. The similarity dominates. The
selection sort is noise.

**The linear scan is not the problem.** For n < 100,000 with
float-dimension vectors, brute-force cosine similarity on CPU is
competitive with approximate nearest-neighbor indices (which have
build-time overhead). The stdlib comment says "fine for small
stores" -- correct.

**The real problem is allocation inside the loop.** Each iteration
creates a `SearchResult` struct (4 fields including String copies
and Map copies), pushes it to a `List<SearchResult>`. For 10,000
entries, that is 10,000 struct allocations to score every document,
then only k=5 are kept. The other 9,995 are garbage.

**Fix:** Score first into a `List<Float>`, do the top-k selection on
scores only, then build `SearchResult` structs for the k winners
only. Reduces struct allocations from n to k.

**The `cosine_similarity` function itself is clean.** Three passes
over the vectors (dot product, magnitude a, magnitude b). No
unnecessary allocation. The `sqrt_approx` uses 50-iteration Newton's
method which converges in ~6 iterations for typical inputs -- the
early-exit check at `diff < 0.0000001` handles this. Fine.

**Missing:** No batch search. If the user wants to search for 100
queries against the same store, they compute 100 * n similarities.
A precomputed normalized store would reduce each query to a single
dot product (skip the two magnitude calls). `normalize` exists as a
public function but is not used internally. The store should
normalize on insert and dot-product on search.

## 3. Reverse Scalar Runtime Functions: Necessary or Delete?

Four new functions in `mapanare_gpu_builtins.c` (lines 620-637):

```c
__mn_tensor_rsub_scalar_f64(double s, const mapanare_tensor_t *a)  // s - a[i]
__mn_tensor_rdiv_scalar_f64(double s, const mapanare_tensor_t *a)  // s / a[i]
__mn_tensor_rsub_scalar_i64(int64_t s, const mapanare_tensor_t *a) // s - a[i]
__mn_tensor_rdiv_scalar_i64(int64_t s, const mapanare_tensor_t *a) // s / a[i]
```

**Question: could `negate + add` replace `rsub`?**

`s - t` = `(-1 * t) + s` = `tensor_mul_scalar(t, -1)` then
`tensor_add_scalar(result, s)`.

That is 2 allocations (one for the negate, one for the add) + 2
passes over the data. The `rsub` function does it in 1 allocation +
1 pass. For a 10,000-element tensor: 80KB allocated vs 160KB, 10K
ops vs 20K.

**The reverse functions are necessary.** Non-commutative ops (sub,
div) with scalar-on-left cannot be decomposed without doubling the
work. The 4 functions are 16 lines of code (each is a one-liner
delegate to the macro-generated `tensor_rscalar_op_*`). The
alternative costs 2x memory and 2x compute. Keep them.

**One nit:** `rsub` and `rdiv` are sufficient because `radd` and
`rmul` are just `add` and `mul` (commutative). The function set is
minimal. Correct.

## 4. HTTP Implementation: Connection Per Request

`https_post` in both `llm.mn` and `embedding.mn` opens a new TCP
connection, does a TLS handshake, sends one request, reads the full
response, and closes everything. Every. Single. Call.

For a multi-turn conversation with 10 turns: 10 TCP connections, 10
TLS handshakes. A TLS 1.3 handshake is 1 RTT minimum. At 50ms RTT
to `api.openai.com`, that is 500ms of pure handshake overhead for a
10-turn chat.

The fix is connection pooling or at minimum HTTP keep-alive, but the
current C runtime `__mn_tcp_close_fd` / `__mn_tls_close_fd` API does
not support connection reuse. This is a runtime limitation, not a
stdlib bug. The stdlib correctly sends `Connection: close` because
that is all the runtime supports.

**Not blocking.** The handshake overhead is dwarfed by LLM inference
latency (seconds). But for embedding batch operations (where you
might call `embed` 100 times in a loop), this adds up. The
`embed_batch` function mitigates by sending multiple texts in one
request. Good.

## 5. `rag.mn`: Character-by-Character Chunking

`chunk_text` at `rag.mn:60-89`:

```
mien i < end {
    chunk_text = chunk_text + text.char_at(i)
    i = i + 1
}
```

For a 10,000-character document chunked into 512-char chunks with
64-char overlap: ~22 chunks, each built character by character.
Total: 22 * 512 = 11,264 string allocations. Could be 22
`text.substr(pos, end)` calls. Zero intermediate allocations.

Same pattern in `chunk_by_sentences` and `chunk_by_paragraphs`. The
entire RAG module builds every output string one character at a time.

## Carry-Forward Queue (Mamba-owned)

| # | Item | Severity | Cycles | Status | Notes |
|---|------|----------|--------|--------|-------|
| M1 | `__mn_signal_get` lockless read | MEDIUM | 6 | OPEN | No change. |
| M2 | `mn_signal_propagate` recursive | MEDIUM | 10 | OPEN | No change. |
| M3 | Tensor variadic N-D ABI | MEDIUM | 2 | OPEN | No change. |
| M4 | Tensor slice stride recomputation in inner loop | MEDIUM | 2 | OPEN | No change. |
| M5 | Tensor alloc uses raw malloc, not arena | MEDIUM | 2 | OPEN | No change. |
| **M6** | **AI stdlib O(n^2) string building** | **HIGH** | **1** | **NEW** | `escape_json`, `extract_http_body`, `jget`, all char-by-char concat. ~7,000 mallocs per `chat()`. Use `substr` and accumulator patterns. |
| **M7** | **200 lines duplicated between llm.mn and embedding.mn** | **MEDIUM** | **1** | **NEW** | Factor JSON/HTTP helpers into shared module. |
| **M8** | **`store_search` allocates n structs, keeps k** | **LOW** | **1** | **NEW** | Score into float list first, build structs for winners only. |
| L1 | `mn_arena_block_new` malloc+memset | LOW | 11 | OPEN | Eternal. |
| L2 | db/html handle tables unguarded | LOW | 6 | OPEN | No change. |
| L3 | `g_argc`/`g_argv` non-atomic | LOW | 6 | OPEN | Benign. |
| L4 | Tensor slice byte-by-byte copy | LOW | 2 | OPEN | No change. |
| L5 | 9 dead/redundant tensor dispatch+same-shape functions | LOW | 2 | OPEN | No change. |
| L6 | `DEFINE_TENSOR_BROADCAST_OPS` unused PROMOTE param | LOW | 2 | OPEN | No change. |
| L7 | No tensor struct strides/flags fields for future views | LOW | 2 | OPEN | No change. |
| 49 | Drop-glue skip-struct-ret | LOW | 12 | OPEN | Emitter, not runtime. |
| 50 | Agent destroy drain-under-contention | LOW | 6 | OPEN | No change. |

## Runtime Size Delta

| File | v4.46.0 lines | v4.51.0 lines | Delta |
|------|---------------|---------------|-------|
| `mapanare_core.c` | 3,009 | 3,009 | 0 |
| `mapanare_io.c` | 1,717 | 1,717 | 0 |
| `mapanare_runtime.c` | 1,369 | 1,369 | 0 |
| `mapanare_gpu.c` | 2,029 | 2,029 | 0 |
| `mapanare_gpu_builtins.c` | 773 | 805 | **+32** |
| `mapanare_db.c` | 877 | 877 | 0 |
| `mapanare_html.c` | 799 | 799 | 0 |
| `mapanare_internal.h` | 63 | 63 | 0 |
| **Total C runtime** | **10,636** | **10,668** | **+32** |

32 lines. Four one-liner functions and their doc comments. The C
runtime is clean. The problem is above it.

| File | Lines | Status |
|------|-------|--------|
| `stdlib/ai/llm.mn` | 2,029 | **NEW** |
| `stdlib/ai/embedding.mn` | 933 | **NEW** |
| `stdlib/ai/rag.mn` | 484 | **NEW** |
| `stdlib/ai/structured.mn` | 36 | **NEW** |
| **Total AI stdlib** | **3,482** | **NEW** |

## Strengths

1. **The reverse scalar functions are correct and minimal.** 4
   functions, 4 lines of delegate code, zero new complexity. The
   macro template does the work. The emitter dispatch at
   `emit_llvm_text.py:2821-2827` correctly swaps the argument order
   (scalar first, tensor second). No ABI issues.

2. **The LLM driver API surface is well-designed.** `chat()` takes
   config + messages, returns `Result<LLMResponse, LLMError>`.
   Provider-specific logic is confined to body builders and response
   parsers. Adding a new provider is one `build_*_body` + one
   `parse_*_response` + one match arm. Clean separation.

3. **Error handling is thorough.** HTTP status codes map to typed
   errors (AuthError, RateLimited, InvalidRequest). The JSON parser
   returns empty strings on failure instead of crashing. The
   `check_http_status` function handles every range. No panics in
   the stdlib.

## Top 3

1. **M6: ~7,000 string allocations per `chat()` call.** The entire
   AI stdlib builds strings character by character. `escape_json`,
   `extract_http_body`, `jget`, `jget_str`, and every RAG chunker
   use `result = result + ch` in a loop. This is O(n^2) time and
   O(n) allocations per string. The fix exists in the language
   already: `substr` for extraction, accumulator lists for building.
   This is the only HIGH item on the queue.

2. **M7: 200 lines of copy-pasted code.** JSON parsing, HTTP
   helpers, and `escape_json` are duplicated verbatim between
   `llm.mn` and `embedding.mn`. Factor into a shared module. This
   is maintenance debt that will triple when the next AI module
   (e.g., `ai/agents.mn`) ships.

3. **The 4 reverse scalar functions are the right call.** They avoid
   2x allocation and 2x compute versus the negate+add decomposition.
   Minimal code, correct semantics. The one bright spot in this arc
   from a C perspective.

## Verdict

**PASS.** The C runtime delta is +32 lines of clean, trivially
correct code. No memory safety issues. No ABI problems. The reverse
scalar functions are necessary and minimal.

The score drops from 8.5 to 7.5 because the AI stdlib -- which is
the entire point of this arc -- ships with O(n^2) string building
as its dominant runtime characteristic. The ~7,000 mallocs per
`chat()` call is not a theoretical concern; it is the hot path of
every AI application built on this stdlib. The C runtime underneath
is fast. The stdlib above it throws that away one `malloc` at a
time.

**-0.5** for M6 (string allocation pathology -- HIGH, pervasive,
fixable today).
**-0.5** for M7 (200 lines duplicated -- MEDIUM, maintenance bomb).

Previous docks (M1-M5 from v4.46.0) remain. The carry-forward
queue has 17 items, 3 new. None are blockers. The language works.
The AI stdlib works. It just works harder than it needs to.
