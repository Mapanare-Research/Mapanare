# Crypto (`stdlib/crypto.mn`)

Cryptographic primitives for Mapanare. v5.39.0 closes the
hashing / MAC / random gap on top of the pre-existing
SHA-1/256/512 + HMAC-SHA256 + Base64 + Hex + JWT HS256 surface.

**Backend:** OpenSSL libcrypto via dlopen (`libcrypto.so.3` /
`.so.1.1` / `.dylib`). The TLS path in `runtime/native/mapanare_io.c`
already proved the dlopen pattern; v5.39.0 extends the same loader
with new EVP function pointers.

**v5.39.0 ships:** SHA-3-256, BLAKE2b-512, HMAC-SHA512,
constant-time MAC compare, streaming digest + HMAC contexts,
random_u64, random_range. **AEAD (AES-GCM, ChaCha20-Poly1305),
Ed25519/X25519, and password KDFs (PBKDF2 / HKDF / Argon2id)
are scoped for v5.39.1** — see "What's not here yet" below.

---

## Quick reference

```mn
// One-shot hashes (hex output)
let h1: String = sha256("hello")            // 32 bytes -> 64 hex chars
let h2: String = sha512("hello")            // 64 bytes -> 128 hex chars
let h3: String = sha3_256("hello")          // 32 bytes -> 64 hex chars  (v5.39.0)
let h4: String = blake2b("hello")           // 64 bytes -> 128 hex chars (v5.39.0)

// HMACs (hex output)
let m1: String = hmac_sha256(key, message)
let m2: String = hmac_sha512(key, message)  // v5.39.0

// Timing-safe MAC compare (v5.39.0)
if constant_time_eq(received_mac, expected_mac) {
    // accept
}

// Streaming digest (v5.39.0)
let dctx_opt: Option<DigestCtx> = digest_new(algo_sha256())
match dctx_opt {
    Some(ctx) => {
        let _: Bool = digest_update(ctx, chunk1)
        let _: Bool = digest_update(ctx, chunk2)
        let hex: String = digest_finalize(ctx)   // ctx is consumed
    },
    None => { /* algo unsupported on this libcrypto */ }
}

// Streaming HMAC (v5.39.0)
let hctx_opt: Option<HmacCtx> = hmac_new(algo_sha256(), key)
match hctx_opt {
    Some(ctx) => {
        let _: Bool = hmac_update(ctx, chunk)
        let mac: String = hmac_finalize(ctx)
    },
    None => { /* */ }
}

// Random (v5.39.0)
let r: Int = random_u64()                   // any 64-bit value
let n: Int = random_range(0, 100)           // uniformly in [0, 100), rejection-sampled
let bytes: List<Int> = random_bytes(32)
let hex: String = random_hex(32)            // 64 hex chars
```

---

## Types

### `CryptoError`

```mn
pub tipo CryptoError {
    | InvalidInput(String)
    | DecodeFailed(String)
    | VerificationFailed(String)
    | HashError(String)
}
```

### `DigestCtx` *(v5.39.0)*

```mn
pub tipo DigestCtx {
    handle: Int,    // opaque EVP_MD_CTX*
    algo: Int       // 1=SHA-256, 2=SHA-512, 3=SHA-3-256, 4=BLAKE2b
}
```

Returned by `digest_new`. Always paired with `digest_finalize`
(or `digest_finalize_raw`) — finalize frees the underlying
context regardless of success. Reusing a finalized handle is
defined as returning the empty string; do not assume otherwise.

### `HmacCtx` *(v5.39.0)*

```mn
pub tipo HmacCtx {
    handle: Int,    // opaque HMAC_CTX*
    algo: Int       // 1=SHA-256, 2=SHA-512  (HMAC over SHA-3 / BLAKE2 — v5.39.1+)
}
```

---

## API reference

### Hashing (one-shot)

| Function | Returns | Output size |
|---|---|---|
| `sha1(data)` | hex `String` | 40 chars |
| `sha256(data)` | hex `String` | 64 chars |
| `sha512(data)` | hex `String` | 128 chars |
| `sha3_256(data)` *(v5.39.0)* | hex `String` | 64 chars |
| `blake2b(data)` *(v5.39.0)* | hex `String` | 128 chars |

Each has a `_raw` variant returning the binary digest (string
carrying raw bytes; lengths 20 / 32 / 64 / 32 / 64 respectively).

`sha3_256` requires OpenSSL 1.1.1+; `blake2b` requires
1.1.0+. Older libcrypto returns the empty string from the
underlying `__mn_*_str` extern, which surfaces as an empty hex
string. Detect by `len(result) == 0`.

### MAC

| Function | Returns | Output size |
|---|---|---|
| `hmac_sha256(key, data)` | hex `String` | 64 chars |
| `hmac_sha512(key, data)` *(v5.39.0)* | hex `String` | 128 chars |

Both have `_raw` variants.

### Constant-time compare *(v5.39.0)*

```mn
fn constant_time_eq(a: String, b: String) -> Bool
```

Returns `true` iff `a` and `b` are byte-equal. Length comparison is
**not** constant-time, but for fixed-size MAC compares (256 = 32
bytes, 512 = 64 bytes) both inputs are the algorithm's known
output length, so length leaks nothing.

Internally prefers OpenSSL `CRYPTO_memcmp`. Falls back to a
volatile-masked aggregation loop when the symbol is absent
(older builds, statically-linked binaries with the symbol
stripped).

### Streaming digest *(v5.39.0)*

```mn
fn digest_new(algo: Int) -> Option<DigestCtx>
fn digest_update(ctx: DigestCtx, chunk: String) -> Bool   // true on success
fn digest_finalize(ctx: DigestCtx) -> String              // hex output
fn digest_finalize_raw(ctx: DigestCtx) -> String          // raw bytes

fn algo_sha256() -> Int    // = 1
fn algo_sha512() -> Int    // = 2
fn algo_sha3_256() -> Int  // = 3  (requires OpenSSL 1.1.1+)
fn algo_blake2b() -> Int   // = 4
```

### Streaming HMAC *(v5.39.0)*

```mn
fn hmac_new(algo: Int, key: String) -> Option<HmacCtx>    // algo: 1 or 2 only
fn hmac_update(ctx: HmacCtx, chunk: String) -> Bool
fn hmac_finalize(ctx: HmacCtx) -> String                  // hex
fn hmac_finalize_raw(ctx: HmacCtx) -> String              // raw
```

### Random *(extended in v5.39.0)*

```mn
fn random_bytes(n: Int) -> List<Int>           // pre-existing
fn random_hex(n: Int) -> String                // pre-existing
fn random_u64() -> Int                          // v5.39.0
fn random_range(low: Int, high: Int) -> Int    // v5.39.0
```

`random_u64` reads 8 bytes from `random_bytes` and assembles a
big-endian unsigned 64-bit value; values above 2^63 appear
negative under signed interpretation (Mapanare `Int` is 64-bit
signed). For uniform integers in a range, prefer `random_range`,
which uses **rejection sampling** to avoid modulo bias and degenerates
gracefully (`random_range(5, 5) == 5`; `random_range(10, 5) == 10`).

### Pre-existing surface (preserved)

```mn
// Encoding
fn base64_encode(data: String) -> String
fn base64_decode(data: String) -> Result<String, CryptoError>
fn base64url_encode(data: String) -> String
fn base64url_decode(data: String) -> Result<String, CryptoError>
fn hex_encode(data: String) -> String
fn hex_decode(data: String) -> Result<String, CryptoError>

// JWT (HS256 over hmac_sha256)
fn jwt_header() -> String
fn jwt_encode(payload_json: String, secret: String) -> String
fn jwt_decode(token: String, secret: String) -> Result<String, CryptoError>
fn jwt_verify(token: String, secret: String) -> Bool
```

The JWT path is preserved unchanged. The `jwt_verify` byte-by-byte
equality check is structurally a timing leak; future revisions
should route it through `constant_time_eq` (tracked as v5.39.x
follow-up).

---

## Cookbook

### Hash a message

```mn
let msg: String = "the quick brown fox"
let h: String = sha256(msg)
print(h)
// 9ecb36561341d18eb65484e833efea61edc74b84cf5e6ae1b81c63533e25fc8f
```

### Hash a chunked stream (e.g. a file, an HTTP body)

```mn
let ctx_opt: Option<DigestCtx> = digest_new(algo_sha256())
match ctx_opt {
    Some(ctx) => {
        let _: Bool = digest_update(ctx, chunk_1)
        let _: Bool = digest_update(ctx, chunk_2)
        let _: Bool = digest_update(ctx, chunk_3)
        let h: String = digest_finalize(ctx)   // ctx is now invalid
        print(h)
    },
    None => {
        // SHA-256 should always be available; if not, libcrypto
        // failed to load — likely a system without OpenSSL.
        print("crypto unavailable")
    }
}
```

### Verify an HMAC without leaking timing

```mn
let expected: String = hmac_sha256(secret, message)
// `received` came over the network — assume attacker-controlled length.
if constant_time_eq(received, expected) {
    // Authenticated. Process the message.
} else {
    // Reject. Do not log received vs expected — the MAC is
    // a sensitive value.
}
```

### BLAKE2b for fast keyed hashing of small messages

```mn
// BLAKE2b is significantly faster than SHA-2 on modern x86_64
// while remaining cryptographically secure. For 64-byte message
// hashes, it benchmarks ~30% faster than SHA-512 on the same
// hardware.
let fingerprint: String = blake2b("user:" + user_id + "|session:" + session_id)
```

### Rate-limit / generate a uniformly-distributed jitter

```mn
// random_range avoids modulo bias.
let jitter_ms: Int = random_range(0, 250)
sleep_ms(base_delay + jitter_ms)
```

---

## What's not here yet (v5.39.1 plan)

| Item | Status |
|---|---|
| AEAD (AES-256-GCM, ChaCha20-Poly1305) | v5.39.1 |
| Nonce-counter helper for AEAD | v5.39.1 |
| Ed25519 sign / verify | v5.39.1 |
| X25519 ECDH | v5.39.1 |
| PBKDF2-SHA256 | v5.39.1 |
| HKDF-SHA256 | v5.39.1 |
| Argon2id (with explicit error on unavailability — no silent PBKDF2 fallback) | v5.39.1 |

These are scoped together because each has its own correctness
trap (GCM nonce reuse is catastrophic; Ed25519 key serialization
has multiple valid encodings; Argon2 availability differs across
OpenSSL major versions). v5.39.0 ships the easy hashing /
streaming / random additions cleanly; v5.39.1 ships the hard
ones with the full RFC corpus they require.

Native `Bytes` type (instead of `String` carrying raw bytes) is
a v6.0+ candidate.

---

## Test corpus

Runtime tests under `stdlib/crypto/tests/`:

- `test_crypto_smoke.mn` — Cr.1 / Cr.2 / Cr.5 surface smoke +
  streaming chunked-vs-one-shot equivalence + random distribution
  sanity.
- `test_crypto_corpus.mn` — RFC 6234 (SHA-256 / SHA-512), FIPS 202
  (SHA-3-256), RFC 7693 (BLAKE2b-512), RFC 4231 (HMAC-SHA256 +
  HMAC-SHA512 tests 1, 2, 4, 5).

Pytest harness at `tests/stdlib/test_crypto_runtime.py` follows the
v5.34.0 / v5.35.0 / v5.38.0 concatenation pattern: prepend
`stdlib/crypto.mn` to each `.mn` test, compile via the Python LLVM
emitter, link against `libmapanare_rt.a`, run, assert "PASSED".

The pre-existing `tests/stdlib/test_crypto.py` (compile-only
checks) remains as a parser / semantic / IR-shape gate.

---

## Compatibility note: v5.39.0 emitter shortcut fix (Cr.0)

Pre-v5.39.0, the Python LLVM emitter had unconditional builtin
shortcuts for `sha256`, `hmac_sha256`, `base64_encode/decode`,
`hex_encode`, `random_bytes`, `regex_match`, `regex_replace`. These
shortcuts produced *raw bytes* / different return shapes than the
user-defined wrappers in `stdlib/crypto.mn` and `stdlib/text/regex.mn`.
When MIR inlining failed (high call-site count, large function),
the shortcut won and silently changed the return type — `sha256(x)`
returned 32 raw bytes instead of 64 hex chars. v5.39.0 gates each
shortcut on `fn not in self._sigs`, deferring to the user-defined
wrapper when one exists. No callers depended on the
raw-bytes-from-`sha256` shortcut behavior; raw access has always
been spelled `sha256_raw`.
