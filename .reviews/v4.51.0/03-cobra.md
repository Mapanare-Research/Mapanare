# Cobra -- C++/ABI Review of Mapanare v4.51.0 (Arc 4 Panel)

**Reviewer:** Cobra
**Personality:** The Grumpy C++ Veteran -- condescending, encyclopedic, razor sharp
**Previous Version Reviewed:** v4.46.0 (score: 9.45, PASS -- tensor arc, scalar-tensor sub/div bug found)
**Verdict:** PASS
**Confidence:** 9/10
**Score:** 9.30/10
**Arc Reviewed:** Arc 4 (Stdlib AI/LLM), v4.47.0 through v4.50.0
**Primary Reviewer:** No -- this is a library arc, but I was asked to audit the HTTP/JSON/TLS internals and the `__struct_meta` reflection primitive, which are firmly in my domain

**Files Reviewed:**
- `stdlib/ai/llm.mn` (2,029 lines -- HTTP internals at 614+, JSON parser, structured extraction, streaming, full API surface)
- `stdlib/ai/embedding.mn` (933 lines -- HTTP calls, JSON parser, vector math, vector store)
- `stdlib/ai/structured.mn` (36 lines -- documentation wrapper, `usa ai::llm`)
- `stdlib/net/http.mn` (lines 1-900 -- the *real* HTTP client module, for comparison)
- `mapanare/lower.py` (lines 1945-1989 -- `_lower_struct_meta` implementation)
- `mapanare/semantic.py` (lines 889-894 -- `__struct_meta` type checking)
- `runtime/native/mapanare_io.c` (lines 324-487 -- TLS lifecycle: `ssl_load_library`, `__mn_tls_connect`, `__mn_tls_close`)
- `.reviews/CARRY_FORWARD.md`

---

## Executive Summary

Arc 4 delivers a four-release AI/LLM stdlib: chat completions across five backends (v4.47.0), compile-time struct reflection for structured extraction (v4.48.0), embeddings with a vector store (v4.49.0), and integration demos closing a 3-cycle carry-forward (v4.50.0). The panel asked me to focus on the HTTP/JSON plumbing underneath the AI surface, the TLS lifecycle correctness, and the `__struct_meta::<T>()` reflection primitive.

The honest assessment: the AI stdlib API surface is excellent. The five-provider abstraction (OpenAI, Anthropic, Groq, Ollama, Custom) with immutable config modifiers, Result-based error handling, conversation state, retry/fallback cascades, sequential chains, and consensus voting -- this is a well-designed SDK. If I saw this surface in a C++ library I would nod approvingly. The Prompture heritage shows: someone who has built LLM SDKs before designed this, and it shows in the small details (non-retryable error classification in `chat_with_retry`, the `has_system` flag avoiding a string comparison on every call, the temperature-zero extraction config).

Beneath that surface, however, the HTTP layer is a hand-rolled `POST`-only HTTP/1.1 client with no chunked transfer-encoding support, no redirect following, no connection reuse, and a per-element `char_at()` JSON parser. And it is copy-pasted wholesale between `llm.mn` and `embedding.mn`. There exists, in the same stdlib tree, a proper HTTP client (`stdlib/net/http.mn`) with URL parsing, header parsing, chunked decoding, redirect following, and a `Result<HttpResponse, HttpError>` return type. The AI modules do not use it. They vendor their own.

In C++ this would be the equivalent of writing a REST client by doing `send(fd, "POST /v1/chat/completions HTTP/1.1\r\n...")` with `std::string` concatenation instead of using `libcurl` or Boost.Beast. It works. I have done it myself, at 2 AM, in a prototype that was never supposed to ship. The difference is that I deleted it the next morning.

---

## 1. HTTP Request Building: Raw String Concatenation vs. a Proper HTTP Client

### What the AI Modules Do

At `llm.mn:716-726` (and the identical copy at `embedding.mn:567-571`):

```mapanare
pon mut raw: String = "POST " + path + " HTTP/1.1\r\n"
raw = raw + "Host: " + host + "\r\n"
raw = raw + "Content-Length: " + str(len(body)) + "\r\n"
cada key en headers { raw = raw + key + ": " + headers[key] + "\r\n" }
raw = raw + "Connection: close\r\n\r\n" + body
```

This is a POST-only, HTTP/1.1, Connection: close, no-redirect, no-chunked-encoding HTTP client. Every request opens a new TCP connection, performs a TLS handshake, sends one request, reads the full response, and closes. There is no connection pooling, no Keep-Alive, no pipelining.

### What `stdlib/net/http.mn` Does (Same Codebase)

The `http.mn` module, 900 lines away in the same stdlib tree, provides:

- URL parsing (`parse_url`) with scheme, host, port, path, query decomposition
- All HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Proper header construction with non-standard port handling
- Chunked transfer-encoding decoding (`decode_chunked_body`)
- Content-Length-based body extraction
- Redirect following (up to `max_redirects`)
- `Result<HttpResponse, HttpError>` with structured error types
- URL percent-encoding/decoding

The AI modules reinvent all of this except redirects and chunked decoding, which they simply *do not support*.

### The Chunked Transfer-Encoding Problem

This is not theoretical. OpenAI's API returns responses with `Transfer-Encoding: chunked` when the response body exceeds a threshold. The `llm.mn` `extract_http_body()` function at line 677-701 looks for `\r\n\r\n` (the header/body separator) and returns everything after it as the body. If the server sends chunked encoding, the "body" will contain chunk size headers interleaved with actual data:

```
4\r\n
Wiki\r\n
6\r\n
pedia \r\n
0\r\n
\r\n
```

The `jget()` JSON parser will then attempt to parse `"4\r\nWiki\r\n6\r\n..."` as JSON and return an empty string (the initial `{` is missing). The user gets a `ParseError("No choices en response")` with no indication that the real issue is chunked encoding.

In practice, the `Connection: close` header *usually* prevents chunked responses from OpenAI (the server knows the connection will close and may choose to send the body unchunked). But "usually" is not "always," and Anthropic's API has been observed to send chunked responses even with `Connection: close`. This is a latent correctness issue.

### The Duplication

The following functions are copy-pasted between `llm.mn` and `embedding.mn`:

| Function | llm.mn line | embedding.mn line |
|----------|------------|-------------------|
| `escape_json` | 308 | 309 |
| `skip_json_value` | 340 | 330 |
| `skip_ws` | 428 | 321 |
| `jget` | 448 | 372 |
| `jget_str` | 517 | 417 |
| `jget_int` | 553 | 433 |
| `jget_first` | 560 | 439 |
| `HttpResult` | 617 | 496 |
| `recv_full_tls` | 632 | 511 |
| `recv_full_tcp` | 644 | 523 |
| `parse_http_status` | 656 | 535 |
| `extract_http_body` | 677 | 546 |
| `https_post` | 703 | 561 |

That is 13 copy-pasted functions. In C++ I would call this a code smell. In a systems language stdlib, I call it a defect. These should be factored into a shared internal module (`stdlib/internal/http_post.mn` or similar) or, better, the AI modules should import and use `stdlib/net/http.mn`. The argument "we didn't want cross-module imports" (from the v4.48.0 session report, Key Decision #2) is understandable for a prototype but not acceptable for a stdlib that users will read as reference code.

### In C++ Terms

In the C++ ecosystem, this is the equivalent of:
- You have Boost.Beast in your dependency tree
- You hand-roll HTTP/1.1 requests with `sprintf` into a `char[]` buffer
- You copy-paste the `sprintf` code into both your OpenAI client and your embedding client
- You do not handle chunked encoding because "the server usually doesn't do it"

The C++ community would rightly ridicule this in a code review.

---

## 2. TLS Lifecycle: Is It Correct?

### The C Runtime Side

The TLS implementation in `mapanare_io.c` is well-structured:

1. **Init:** `ssl_load_library()` uses `pthread_once`/`InitOnceExecuteOnce` (fixed in v4.35.0, closing the carry-forward). Thread-safe.
2. **Connect:** `__mn_tls_connect()` allocates an `SSL_CTX` per connection (via `SSL_CTX_new`), creates an `SSL` session, calls `SSL_connect`, wraps both in a heap-allocated `MnTlsCtx`. The SNI hostname is set via `SSL_ctrl(ssl, SSL_CTRL_SET_TLSEXT_HOSTNAME, 0, hostname)`. Correct.
3. **Read/Write:** `__mn_tls_read`/`__mn_tls_write` dereference the `MnTlsCtx*`, call `SSL_read`/`SSL_write`. NULL checks present. Correct.
4. **Close:** `__mn_tls_close` calls `SSL_shutdown`, `SSL_free`, `SSL_CTX_free`, `free(tctx)`. In that order. Correct.

**One concern:** Every connection creates a new `SSL_CTX`. In OpenSSL, `SSL_CTX` holds the trust store, loaded via `SSL_CTX_set_default_verify_paths`. For repeated API calls to the same host (e.g., 10 consecutive `chat()` calls in a conversation loop), this means 10 `SSL_CTX` allocations, 10 trust-store loads from disk, 10 TLS handshakes, and 10 connection setups. In C++ with `boost::asio::ssl::context`, you would create one `ssl::context`, load the trust store once, and reuse it across connections. The per-connection `SSL_CTX` is not *wrong* -- it is thread-safe and leak-free -- but it is the most expensive possible correct implementation.

For the current usage pattern (one API call per `chat()` invocation, `Connection: close`), this overhead is dominated by the LLM's response latency. For embedding batches (hundreds of calls in a loop), the repeated TLS handshake overhead would become measurable. Not blocking, but worth noting for v5.x when connection pooling arrives.

### The Mapanare Side

At `llm.mn:728-744`:

```mapanare
si port == 443 {
    pon tls_init: Int = __mn_tls_init()
    pon tls_ctx: Int = __mn_tls_connect_str(fd, host)
    si tls_ctx == 0 {
        pon close_r: Int = __mn_tcp_close_fd(fd)
        da new_http_err("TLS handshake failed cada " + host)
    }
    pon sent: Int = __mn_tls_write_str(tls_ctx, raw)
    si sent < 0 {
        pon close_r: Int = __mn_tls_close_fd(tls_ctx, fd)
        da new_http_err("Failed to send request")
    }
    pon response: String = recv_full_tls(tls_ctx)
    pon close_r: Int = __mn_tls_close_fd(tls_ctx, fd)
    ...
}
```

The lifecycle is: init -> connect -> write -> read -> close. Error paths close resources correctly (the `si tls_ctx == 0` branch closes the TCP fd; the `si sent < 0` branch closes both TLS and TCP). The happy path closes both after reading.

**One issue:** The `tls_init` return value is captured but never checked. If `__mn_tls_init()` returns -1 (OpenSSL not found on the system), the code proceeds to `__mn_tls_connect_str()`, which will also fail (the `s_ssl.available` check inside `__mn_tls_connect` catches it). So the failure is caught, but the error message will be "TLS handshake failed" instead of the more informative "OpenSSL library not available." Minor usability issue.

**Another issue:** The TLS/plaintext decision is `si port == 443`. This is the port-sniffing heuristic. If someone runs an OpenAI-compatible API on port 8443 with TLS, the code will attempt plaintext HTTP. The `http.mn` module avoids this by using the URL scheme (`https://`). The AI modules do not parse URLs -- they take `host` and `port` separately -- so the port heuristic is all they have. For the five supported providers (OpenAI, Anthropic, Groq on 443; Ollama on 11434; Custom on user-specified), this works. For custom HTTPS endpoints on non-443 ports, it silently breaks.

### Verdict on TLS

The C runtime implementation is correct and thread-safe. The Mapanare-side lifecycle is correct but has two rough edges (unchecked init return, port-based TLS detection). Neither is a security vulnerability -- the worst case is a confusing error message or a plaintext connection to a server expecting TLS, which will fail at the protocol level anyway. But these are the kinds of paper cuts that a proper HTTP client abstraction would eliminate.

---

## 3. The JSON Parser: Character-by-Character `jget()`

The `jget()` family of functions (`jget`, `jget_str`, `jget_int`, `jget_first`, `jget_array_elements`) is a hand-rolled JSON object field extractor. It does not parse JSON into a tree; it does not validate JSON; it does not handle Unicode escape sequences (`\uXXXX`). It is a cursor-based scanner that finds a key in a JSON object and returns the raw value substring.

### Is It Correct?

For the JSON that LLM APIs return: yes, with one exception. The `jget_str()` unescape at `llm.mn:528-548` handles `\"`, `\\`, `\n`, `\t`, `\r` but does NOT handle `\uXXXX` Unicode escapes. If an LLM returns content containing `\u00e9` (the Unicode escape for "e"), the parser will treat the `u` as the escaped character and produce the literal string `u00e9`. In practice, OpenAI and Anthropic do not return `\uXXXX` escapes in the `content` field (they return raw UTF-8). Ollama does the same. So this is a theoretical issue with current providers but a real bug for any provider that follows RFC 8259 strictly.

The `embedding.mn` copy of `jget_str()` at line 427 has a simpler unescape that does not even handle `\n`/`\t`/`\r` -- it just passes through the escaped character verbatim. This divergence between the two copies is the predictable consequence of copy-paste maintenance.

### Performance

Every `jget()` call scans from the beginning of the JSON string, character by character via `text.char_at(i)`. For a typical OpenAI response (~2KB), this means ~2000 `char_at()` calls per field extraction. The `parse_openai_response()` function calls `jget` or `jget_str` approximately 8 times, meaning ~16,000 `char_at()` calls per response. Since `char_at()` on Mapanare strings is O(1) (pointer + offset into the `{ptr, i64}` representation), this is not catastrophic. But it is O(n*k) where n is response size and k is the number of fields extracted. A single-pass parser would be O(n).

For LLM responses, the JSON parsing time is approximately 0.001% of the wall-clock time (dominated by network + inference). For embedding responses with large float arrays, the `parse_float_array()` function at `embedding.mn:457-490` does its own character-by-character number parsing, which for a 1536-dimension embedding vector means ~30,000 `char_at()` calls. Still dominated by network latency, but getting into "noticeable if you batch 1000 calls" territory.

### In C++ Terms

In C++ you would use `nlohmann::json`, `simdjson`, or `rapidjson`. Even the most minimal JSON parsing library in the C++ ecosystem handles `\uXXXX` escapes and does single-pass parsing. The hand-rolled approach here is the kind of thing I wrote in 1998 when parsing a config file and I did not want to add a dependency. In a language stdlib, it should be replaced by an import of `stdlib/encoding/json.mn` (which exists! It has `escape_json_string()` at line 611!) or, at minimum, factored into a shared JSON utility module.

---

## 4. `__struct_meta::<T>()` -- Compile-Time Reflection

### The Implementation

At `lower.py:1945-1989`, `_lower_struct_meta` does exactly what it says:

1. Look up the struct name in `self._module.structs` (a dict of `{name: [(field_name, MIRType), ...]}`)
2. Map each field's `MIRType` to a JSON Schema type (`String->string`, `Int->integer`, `Float->number`, `Bool->boolean`, `List->array`, `Option<T>->inner type`)
3. Build a JSON Schema string: `{"type": "object", "properties": {...}, "required": [...]}`
4. Emit the string as a compile-time constant (`Const` MIR instruction)
5. The string becomes a `[N x i8]` constant in the LLVM IR module

This is compile-time-only. Zero runtime overhead. No RTTI tables, no type_info objects, no vtables. The struct's metadata is a string literal baked into the binary.

### Comparison to C++ RTTI / Reflection Proposals

In C++, `typeid(T)` returns a `std::type_info` reference with a mangled name and comparison operators. It requires the program to be compiled with RTTI enabled (`-frtti`), which adds vtable pointers and typeinfo records to every polymorphic class. It does NOT give you field names, field types, or any structural information.

The C++26 static reflection proposal (P2996) is far more ambitious: it gives compile-time access to the names, types, and attributes of every member of a class, accessible via `^T` (the reflection operator) and consteval functions. It is roughly 200 pages of standardese and has been in committee since 2022.

Mapanare's `__struct_meta::<T>()` is somewhere between these two extremes. It gives you structural information (field names and types) but only as a JSON string, not as a compile-time data structure you can operate on. You cannot write a generic `serialize<T>(val: T)` that iterates over fields -- you get a schema string and must use prompt engineering to make an LLM fill it in.

### Is This the Right Design?

For the specific use case (structured LLM extraction): absolutely yes. The LLM needs a JSON schema string. Generating that string at compile time from the struct definition is the exact right thing to do. No runtime cost, no RTTI overhead, and the schema is guaranteed to be consistent with the struct definition because it is generated from the same source of truth.

For general-purpose reflection: no. The JSON-string-only output means you cannot programmatically iterate over fields, cannot build generic serializers, and cannot implement traits like `Serialize` or `Debug` via reflection. But the roadmap does not claim `__struct_meta` is a general reflection system -- it is a compile-time schema generator for the AI stdlib. The scope is appropriate.

### The JSON Schema Subset

The generated schema supports:

| Mapanare Type | JSON Schema Type | Notes |
|---------------|------------------|-------|
| String | "string" | |
| Int | "integer" | |
| Float | "number" | |
| Bool | "boolean" | |
| List<T> | "array" | No `items` constraint -- the LLM does not know the element type |
| Option<T> | inner type, not in `required` | Correct -- optional fields are nullable |
| Everything else | "string" | Fallback -- structs, enums, maps all become "string" |

**Missing:** `Map<K,V>` should map to `"object"` (or `"object"` with `additionalProperties`). Nested structs should recursively expand. Enums should map to `"string"` with an `"enum"` constraint listing the variant names. `List<T>` should include `"items": {"type": "..."}` for the element type.

The current subset is sufficient for flat structs with primitive fields, which covers the v4.48.0 use case (address extraction). For nested structs (`struct Order { items: List<LineItem>, customer: Customer }`), the schema will say `"items": {"type": "array"}, "customer": {"type": "string"}`, which gives the LLM no structural guidance for the nested types. The extraction will still work in practice -- LLMs are remarkably good at inferring nested structure from field names -- but the schema is technically insufficient.

---

## 5. The recv_full Loop: Correctness Under Partial Reads

At `llm.mn:632-641`:

```mapanare
fn recv_full_tls(tls_ctx: Int) -> String {
    pon mut response: String = ""
    pon mut iterations: Int = 0
    mien iterations < 100000 {
        iterations = iterations + 1
        pon chunk: String = __mn_tls_read_str(tls_ctx, 8192)
        si len(chunk) == 0 { sal }
        response = response + chunk
    }
    da response
}
```

This reads 8KB chunks until `__mn_tls_read_str` returns an empty string (indicating EOF or error), concatenating into a growing `response` string. The 100,000 iteration cap is a safety valve -- at 8KB per chunk, this allows up to ~800MB of response data.

**The concatenation cost:** Each `response = response + chunk` allocates a new string of length `len(response) + len(chunk)`, copies the old response, copies the chunk, and (implicitly, via drop glue) frees the old response. For a 50KB API response received in seven 8KB chunks, this is seven allocations with sizes 8K, 16K, 24K, 32K, 40K, 48K, and 50K. Total memory allocated: ~218KB for a 50KB response. Total bytes copied: ~168KB. This is the classic Schlemiel the Painter's algorithm for string concatenation.

In C++ you would use a `std::string` with `reserve()` and `append()`, or a `std::vector<char>` with `push_back` and amortized growth. In Mapanare, the string type is `{ptr, i64}` (pointer + length) with no capacity field, so every concatenation must allocate. The fix would be a `StringBuilder` or `StringBuffer` type with exponential growth, which does not exist in the current stdlib.

For LLM API responses (1-50KB), this overhead is negligible compared to network latency. For embedding responses with large float arrays (potentially hundreds of KB), the quadratic concatenation cost could become measurable. Not blocking for v4.x.

---

## 6. The Streaming Implementation: Post-Hoc Chunking

The v4.47.0 `chat_stream()` function at `llm.mn:1741-1783` is refreshingly honest about what it does:

```
// Note: v4.47.0 streaming is post-hoc (receives full body then splits).
// Real per-chunk streaming requires async I/O (v4.74.0).
```

It calls the same `https_post()` that `chat()` uses, receives the full response body, then splits it into `ChatChunk` records by parsing SSE (`data: {...}`) or NDJSON (Ollama) lines. The chunks are returned as a `List<ChatChunk>`.

This is not streaming. This is "I received the entire response and then I chopped it into pieces." The user gets no benefit from the chunking -- the full response was already in memory. The only utility is if the user wants to iterate over the chunks for display purposes, simulating a streaming UI without actual streaming.

The session report acknowledges this explicitly and defers real streaming to v4.74.0 with coroutines. I respect the honesty. But I note that the function is named `chat_stream`, which implies streaming behavior to the caller. A name like `chat_chunked` or `chat_with_chunks` would be more accurate for the current implementation.

In C++ with Boost.Beast, you would use `async_read_some()` on the TLS stream and yield each chunk to a callback or coroutine. The Mapanare C runtime already supports partial reads via `__mn_tls_read` (which returns whatever SSL_read gives it, potentially a partial frame). The infrastructure for real streaming exists; the language lacks the async primitives to expose it.

---

## Issues Found

### CRITICAL: None

### HIGH: None

### MEDIUM

1. **[MEDIUM] HTTP client code copy-pasted between llm.mn and embedding.mn -- 13 identical functions, one with divergent unescape behavior.**

   `llm.mn` and `embedding.mn` each contain their own independent copies of: `escape_json`, `skip_json_value`, `skip_ws`, `jget`, `jget_str`, `jget_int`, `jget_first`, `HttpResult`, `recv_full_tls`, `recv_full_tcp`, `parse_http_status`, `extract_http_body`, `https_post`. This is ~250 lines of duplicated code with no shared module.

   Worse, the two copies have already diverged: `llm.mn:jget_str` at lines 528-548 handles `\n`, `\t`, `\r` unescaping; `embedding.mn:jget_str` at line 427 does not -- it passes through the character after `\` verbatim. This is the first symptom of copy-paste rot. It will get worse.

   A proper `stdlib/net/http.mn` module already exists with URL parsing, header parsing, chunked decoding, and redirect following. The AI modules should import and use it, or at minimum, the shared JSON/HTTP primitives should be extracted into a shared internal module.

2. **[MEDIUM] No chunked transfer-encoding support in the AI module HTTP client.**

   `extract_http_body()` in both `llm.mn` and `embedding.mn` naively splits on `\r\n\r\n` and returns everything after as the body. If the server sends `Transfer-Encoding: chunked`, the body will contain chunk size headers that will cause JSON parsing to fail silently (returning empty strings from `jget`). The `Connection: close` header usually inhibits chunked responses, but this is not guaranteed by the HTTP spec. The `stdlib/net/http.mn` module already handles chunked encoding correctly.

### LOW

3. **[LOW] `__struct_meta::<T>()` does not generate `items` constraint for List fields or recursive schemas for nested structs.**

   For `List<Float>`, the schema emits `"type": "array"` without `"items": {"type": "number"}`. For nested structs, the schema emits `"type": "string"`. Both reduce schema guidance quality for LLM extraction. Not blocking -- LLMs infer structure from field names -- but the schema is less useful than it could be.

4. **[LOW] `jget_str()` does not handle `\uXXXX` Unicode escapes.**

   RFC 8259 requires JSON parsers to handle `\uXXXX` and `\uXXXX\uXXXX` (surrogate pairs). The hand-rolled `jget_str` treats `\uXXXX` as `u` followed by four literal characters. Current LLM providers return raw UTF-8, not Unicode escapes, so this is not triggered in practice. But it violates the JSON spec.

5. **[LOW] TLS init return value unchecked in `https_post()`.**

   `llm.mn:730`: `pon tls_init: Int = __mn_tls_init()` -- the return value is captured but never tested. If OpenSSL is not installed, the error is caught later by `__mn_tls_connect_str` returning 0, but the error message says "TLS handshake failed" instead of the more informative "SSL library not available."

6. **[LOW] Port-based TLS detection (`si port == 443`) instead of scheme-based.**

   Custom HTTPS endpoints on non-443 ports (e.g., `custom("myserver", 8443, "/v1/chat", ...)`) will use plaintext HTTP. The `LLMConfig` struct has no `is_tls` field. Adding a `use_tls: Bool` field (defaulting to `port == 443`) with a `with_tls(config, true)` modifier would fix this without breaking existing API.

7. **[LOW] `recv_full_tls` / `recv_full_tcp` use quadratic string concatenation.**

   Each iteration appends to a growing string via `response = response + chunk`, which copies the entire accumulated response on every chunk. For a 50KB response in 7 chunks, this copies ~168KB total instead of ~50KB. A `StringBuilder` pattern would eliminate this overhead. Not measurable for typical LLM responses; potentially measurable for large embedding batches.

8. **[LOW] Dead arena code, 14th cycle.**

   Carrying forward from v4.46.0 Issue #7. Untouched in Arc 4. **14th cycle.** I am now seriously considering filing a UNESCO World Heritage nomination. The dead arena code has outlived three major arcs, two complete ABI redesigns, and the entire self-hosted compiler bootstrapping saga. It is the Ship of Theseus of dead code -- every other line of the emitter has been rewritten around it, and it remains, unmoved, a monument to the human capacity for procrastination.

9. **[LOW] Stale carry-forward tracking -- P3 and A10 unchanged for 4th cycle.**

   P3 (self-hosted guard fall-through divergence) still targets v4.37.0, which shipped in Arc 2 without the fix. A10 (bounded-for sentinels) still targets "v4.37.0+ if grammar adds `loop { }`". Fourth consecutive cycle I have flagged this. These tracking versions need to be updated to reflect reality.

---

## Carry-Forward Status

| # | Item | v4.46.0 | v4.51.0 | Note |
|---|------|---------|---------|------|
| P3 | Guard fall-through (MEDIUM) | OPEN (cycle 3) | **OPEN (cycle 4)** | Untouched in Arc 4. |
| A10 | Bounded-for sentinels (LOW) | OPEN (cycle 11) | **OPEN (cycle 12)** | 442+ sites, still no `loop { }` grammar change. |
| 49 | Drop-glue skip-struct-ret (LOW) | 8th cycle | **9th cycle** | Untouched. |
| 50 | Agent destroy in-flight message leak (LOW) | 2nd cycle | **3rd cycle** | Untouched. |
| Dead arena | Dead arena code | 13th cycle | **14th cycle** | Geological timescales. |
| BYREF_BYTES | BYREF_BYTES asymmetry | 5th cycle | **6th cycle** | Untouched. |
| NEW | HTTP code duplication (MEDIUM) | -- | **NEW** | 13 functions copy-pasted between llm.mn and embedding.mn. |
| NEW | No chunked transfer-encoding (MEDIUM) | -- | **NEW** | AI modules ignore chunked encoding; stdlib/net/http.mn handles it. |
| CLOSED | Scalar-tensor sub/div swap (MEDIUM) | NEW at v4.46.0 | **CLOSED** | v4.47.0 -- `rsub`/`rdiv` runtime functions. |
| CLOSED | P5 examples showcase gap (MEDIUM) | 3rd cycle | **CLOSED** | v4.50.0 -- 4 AI demos + cookbook chapter. |

---

## Recommendations

### Priority 1: Factor out shared HTTP/JSON code (Issue #1, MEDIUM)

Either have `llm.mn` and `embedding.mn` import `stdlib/net/http.mn` for HTTP operations, or extract the 13 duplicated functions into a shared internal module (`stdlib/internal/json_utils.mn` + `stdlib/internal/http_post.mn`). The divergent `jget_str` unescape behavior must be reconciled -- the `llm.mn` version is correct; the `embedding.mn` version is not.

### Priority 2: Add chunked transfer-encoding support or import http.mn (Issue #2, MEDIUM)

The simplest fix is to use `http.mn`'s `request()` function, which already handles chunked decoding. If the inline `https_post` is retained, add chunked decoding (the `decode_chunked_body` function from `http.mn` can be imported directly).

### Priority 3: Add `use_tls: Bool` to LLMConfig / EmbedConfig (Issue #6, LOW)

One-field addition. Set `true` when `port == 443`, add `with_tls(config, true)` modifier. Fixes custom HTTPS endpoints on non-standard ports.

---

## Top 3

1. **HTTP code duplication is a maintenance liability.** Thirteen copy-pasted functions between two modules in the same directory, already diverging in behavior. This is the number one issue I want fixed before v4.52.0.

2. **The `__struct_meta::<T>()` design is correct for its scope.** Compile-time-only, zero runtime overhead, schema generation from struct definitions. It is not C++ P2996 static reflection, but it does not need to be. For LLM structured extraction, a JSON schema string is exactly the right abstraction. The schema subset should be extended (nested structs, List item types) but the foundation is sound.

3. **The TLS lifecycle is correct.** The C runtime implementation is thread-safe, the Mapanare-side error handling closes resources on all paths, and the per-connection `SSL_CTX` pattern -- while expensive -- is safe. The two paper cuts (unchecked init return, port-based TLS detection) are usability issues, not security issues.

---

## Arc 4 Assessment

Arc 4 delivered a competent AI/LLM stdlib with a clean API surface, five-provider support, and a novel compile-time reflection primitive. The Prompture heritage is visible in the design patterns -- conversation state, retry cascades, consensus voting, sequential chains -- and the integration demos close a multi-cycle carry-forward gap.

The infrastructure beneath the API is the weak point. The hand-rolled HTTP client is POST-only with no chunked encoding support. The JSON parser is a character-by-character scanner with incomplete RFC 8259 compliance. Both are copy-pasted between modules. A proper HTTP client module exists in the same stdlib tree and is not used. This is the kind of technical debt that accumulates interest.

I am deducting 0.15 from the previous 9.45 for:
- **-0.05** for the HTTP code duplication (Issue #1, MEDIUM -- 13 functions, already diverging).
- **-0.04** for the missing chunked encoding support (Issue #2, MEDIUM -- latent correctness issue).
- **-0.02** for the `__struct_meta` schema subset limitations (Issue #3 -- incomplete but functional).
- **-0.01** for the `\uXXXX` unescape omission (Issue #4 -- theoretical with current providers).
- **-0.01** for the port-based TLS detection (Issue #6 -- affects custom HTTPS endpoints).
- **-0.01** for the dead arena code, now officially a teenager (Issue #8, 14th cycle).
- **-0.01** for stale carry-forward tracking, 4th consecutive flagging (Issue #9).

**Score: 9.30/10, PASS.** The drop from 9.45 is driven by the HTTP layer duplication and the missed opportunity to use the existing `http.mn` module. The API surface is excellent -- this is the best-designed module in the stdlib, with clear error types, immutable config modifiers, and a clean provider abstraction. The infrastructure needs to catch up to the interface. When the shared HTTP layer is factored out and chunked encoding is handled, this score goes back up.

The `__struct_meta::<T>()` primitive is a genuine language-level contribution. Compile-time struct reflection with zero runtime cost, targeted at a specific use case (LLM extraction), implemented as a turbofish intrinsic that fits naturally into the existing generic function call syntax. It is not C++ P2996, but it is the right tool for the job. I approve it.

PASS with high confidence. The AI stdlib works. It just needs to stop reinventing its own HTTP client.
