# v5.39.0 — Cr.\* — crypto primitives

**Status:** PLANNING
**Type:** Stdlib expansion. Net-new module at `stdlib/crypto/`,
backed by OpenSSL via the existing dlopen path already used for
TLS in `runtime/native/mapanare_tls.c`.
**Breaking:** No.
**Prerequisite:** v5.38.0 shipped (regex stdlib).
**Estimated effort:** 1 session. ~600 LOC `.mn` + ~200 LOC C
shim extending the existing OpenSSL dlopen path.

---

## Why this exists

Apps need to hash, sign, verify, encrypt. Today every Mapanare
app that needs even SHA-256 has to FFI to OpenSSL by hand. The
TLS path already proved the dlopen-OpenSSL pattern; v5.39.0 lifts
it into a clean stdlib API.

This is the final item in the **stdlib gap-close arc**. After
v5.39.0 the foundational gaps are closed and the manifesto arc
(v5.40.0+) can build on a complete stdlib.

---

## Goals

1. **Cr.1** — Hashing: SHA-256, SHA-512, SHA-3-256, BLAKE2b.
2. **Cr.2** — HMAC: HMAC-SHA256, HMAC-SHA512.
3. **Cr.3** — Symmetric encryption: AES-128-GCM, AES-256-GCM,
   ChaCha20-Poly1305.
4. **Cr.4** — Asymmetric: Ed25519 sign/verify, X25519 key
   exchange.
5. **Cr.5** — Random: cryptographically secure random bytes,
   random integer in range.
6. **Cr.6** — Key derivation: PBKDF2, Argon2id, HKDF.
7. **Cr.7** — Tests including known-answer tests against
   official RFC test vectors.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Cr.1** | HIGH | **Hashing in `stdlib/crypto/hash.mn`.** `sha256(data: Bytes) -> Bytes`, `sha512`, `sha3_256`, `blake2b`. Streaming API: `Sha256::new().update(chunk).finalize() -> Bytes`. Wraps OpenSSL `EVP_*` functions. | 2h |
| **Cr.2** | HIGH | **HMAC in `stdlib/crypto/hmac.mn`.** `hmac_sha256(key: Bytes, data: Bytes) -> Bytes`, `hmac_sha512`. Streaming via `Hmac::new(key).update(...).finalize()`. Constant-time comparison helper `crypto.constant_time_eq(a, b)` for verifying MACs without timing leaks. | 1h |
| **Cr.3** | HIGH | **AEAD in `stdlib/crypto/aead.mn`.** `aes_256_gcm_encrypt(key: Bytes, nonce: Bytes, plaintext: Bytes, aad: Bytes) -> Bytes` (returns ciphertext + tag concatenated). Decrypt returns `Result<Bytes, CryptoError>`. ChaCha20-Poly1305 with same shape. Reject reused nonce statically when the same `(key, nonce)` is detected via per-key nonce counter (best-effort safety net). | 3h |
| **Cr.4** | HIGH | **Ed25519 + X25519 in `stdlib/crypto/sig.mn` and `stdlib/crypto/kex.mn`.** `Ed25519::generate_keypair() -> (PublicKey, PrivateKey)`, `sign(priv, msg) -> Bytes`, `verify(pub, msg, sig) -> Bool`. X25519 for ECDH key agreement: `x25519(priv, pub) -> Bytes`. | 2h |
| **Cr.5** | MEDIUM | **Random in `stdlib/crypto/random.mn`.** `random_bytes(n: Int) -> Bytes`, `random_u64() -> Int`, `random_range(low: Int, high: Int) -> Int` (rejection-sampled to avoid modulo bias). Backed by `getrandom()` on Linux, `SecRandomCopyBytes` on macOS, `BCryptGenRandom` on Windows (via thin C shim — not OpenSSL). | 2h |
| **Cr.6** | MEDIUM | **KDF in `stdlib/crypto/kdf.mn`.** `pbkdf2_sha256(password, salt, iterations, len)`, `argon2id(password, salt, time, memory, parallelism, len)`, `hkdf_sha256(salt, ikm, info, len)`. Argon2id requires libargon2 (separate dlopen) OR fall back to OpenSSL 3.0+ EVP_KDF if available; document Argon2 as "available where libargon2 or OpenSSL 3.0+ is present" — degrade to PBKDF2 with clear message otherwise. | 2h |
| **Cr.7** | HIGH (gate) | **Tests in `stdlib/crypto/tests/`.** Known-answer tests from the relevant RFCs / NIST CAVP: `test_sha.mn`, `test_hmac.mn`, `test_aead.mn` (RFC 8439 ChaCha20-Poly1305 vectors; NIST AES-GCM CAVP), `test_ed25519.mn` (RFC 8032 vectors), `test_x25519.mn` (RFC 7748 vectors), `test_pbkdf2.mn` (RFC 6070), `test_random.mn` (chi-squared + monobit smoke; NOT a randomness quality test, just a sanity check). | 4h |
| **Cr.8** | LOW | **C shim** in `runtime/native/mapanare_crypto.c`. Extends the existing OpenSSL dlopen in `mapanare_tls.c`. Adds Ed25519 / X25519 / EVP_AEAD bindings; loads libargon2 separately if available. Random uses `getrandom`/`SecRandomCopyBytes`/`BCryptGenRandom` directly, not OpenSSL. ~200 LOC. | 3h |
| **Cr.9** | LOW | **Doc page** at `docs/stdlib/crypto.md`. Cookbook with secure-default examples ("hash a password" should mention Argon2id not SHA-256 raw; "encrypt a message" should reference AEAD not raw AES). | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.38.0 HEAD clean. Verify OpenSSL
  dlopen path in `mapanare_tls.c` is healthy.
- **Phase 1** — Cr.8 C shim foundation.
- **Phase 2** — Cr.1 + Cr.2 hashing + HMAC. Quickest wins.
- **Phase 3** — Cr.3 AEAD (most subtle; test vectors first).
- **Phase 4** — Cr.4 + Cr.5 + Cr.6.
- **Phase 5** — Cr.7 round out tests; Cr.9 docs.
- **Phase 6** — Bump + tag.

---

## Out of scope

- **Designing new crypto.** Stdlib wraps standard primitives. No
  custom protocols.
- **Post-quantum.** ML-KEM / ML-DSA can land in a v5.x patch
  release if OpenSSL 3.x exposure is straightforward; not v5.39.0.
- **JWT / JWE / COSE.** Higher-level token formats are downstream
  packages on top of v5.39.0 primitives.
- **Certificate parsing / X.509.** TLS already does cert
  verification internally; standalone X.509 parsing is downstream.
- **Bring-your-own crypto provider.** OpenSSL only for v5.x. If
  someone wants libsodium or BoringSSL backing they can fork.

---

## Risk

1. **OpenSSL version skew.** OpenSSL 1.1.x vs 3.x has different
   API surfaces (deprecations, EVP_KDF moves, etc.). Mitigation:
   Cr.8 shim probes `OPENSSL_VERSION_NUMBER` and dispatches; pin
   the minimum supported version (1.1.1, the LTS) and document.
2. **AEAD nonce reuse.** Catastrophic for GCM. Mitigation: Cr.3
   provides a per-key nonce counter helper that tracks issued
   nonces; user code that opts out gets a docs warning. Best
   effort — can't prevent at compile time without dependent
   types.
3. **Argon2id availability.** Some platforms may not ship
   libargon2 or OpenSSL 3.0+. Mitigation: Cr.6 falls back to
   PBKDF2-SHA256 with a clear log message; documented in Cr.9.
4. **Test vectors drift between standards revisions.** Mitigation:
   pin to specific RFC dates (RFC 8439, RFC 8032, etc.) in Cr.7
   test file headers; never silently update vectors.
5. **Constant-time HMAC compare.** A naive byte-by-byte compare
   leaks timing. Mitigation: Cr.2 ships `constant_time_eq` and
   uses it internally for verify paths.

---

## Success criteria

- ✅ All RFC / NIST test vectors pass.
- ✅ AEAD round-trip (encrypt → decrypt) preserves plaintext;
  truncated ciphertext fails decryption cleanly.
- ✅ Ed25519 sign-then-verify works; tampered signature is
  rejected.
- ✅ X25519 ECDH: both sides arrive at the same shared secret.
- ✅ `random_bytes(32)` produces non-trivially-different output
  on repeated calls (smoke test only).
- ✅ Argon2id available on Linux/macOS/Windows (or PBKDF2
  fallback with clear message).
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "no crypto stdlib" gap.
- **Stdlib gap-close arc CLOSED** — v5.34.0 through v5.39.0
  shipped: date/time, sqlite, JSON, HTTP, regex, crypto. The
  foundational stdlib is complete enough that the manifesto arc
  (v5.40.0+) has solid ground to build on.

**Inherits to v5.40.0:**
- Older carries (notarization, named-tzdb, Pg drivers, HTTP/2/3,
  PQ crypto, JWT/JWE).
- **Manifesto arc begins** — v5.40.0's `ask` primitive is the
  first item.
