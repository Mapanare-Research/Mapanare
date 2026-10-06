# v5.39.0 Pre-Phase Audit — Cr.\* Crypto Stdlib

**Status:** AUDIT COMPLETE. Lead-approved staged scope.
**Audited at:** v5.38.0 HEAD (VERSION=5.38.0, fixed-point STRICT
241,898 / 0 diff, goldens 95/95).
**Decision:** stage Cr.\* across v5.39.0 + v5.39.1.

---

## Why this audit exists

PLAN.md described "net-new module at `stdlib/crypto/`, ~600 LOC"
backed by OpenSSL via `runtime/native/mapanare_tls.c`. **Both
premises are wrong at HEAD.** This audit captures the gap, the
existing surface that PLAN didn't account for, and the load-bearing
deviations driving v5.39.0 scope. Same Phase-0 pattern as v5.34.0
Dt.\*, v5.35.0 Sq.\*, v5.37.0 Ht.\*, v5.38.0 Re.\* — surface scope
correction *before* the implementation phase.

---

## Existing surface in `stdlib/crypto.mn` (283 LOC)

### Hashing
- ✅ `sha1`, `sha256`, `sha512` (hex digest) + `_raw` variants
- ❌ `sha3_256`, `blake2b` — NOT shipped
- ❌ Streaming API (e.g. `Sha256::new().update().finalize()`) — NOT shipped

### MAC
- ✅ `hmac_sha256` + `hmac_sha256_raw`
- ❌ `hmac_sha512` — NOT shipped
- ❌ `constant_time_eq` — NOT shipped (callers writing
  `sig_b64 != expected_b64` leak timing today; the JWT verify
  paths in this very module use byte-by-byte compare)

### Encoding
- ✅ `base64_encode/decode`, `base64url_encode/decode`,
  `hex_encode/decode`

### JWT (HS256)
- ✅ `jwt_encode`, `jwt_decode`, `jwt_verify`
- **Not in PLAN audit sketch.** Load-bearing for any v5.40.0+
  ask-flow that does API-key auth. Preserved unchanged.

### Random
- ✅ `random_bytes(n) -> List<Int>` + `random_hex(n) -> String`
- ❌ `random_u64`, `random_range` — NOT shipped

### Errors
- ✅ `CryptoError` enum: `InvalidInput`, `DecodeFailed`,
  `VerificationFailed`, `HashError` (4 variants)

### Constructor helpers
- ✅ `new_invalid_input`, `new_decode_failed`,
  `new_verification_failed`, `new_hash_error`

---

## Existing C-runtime exports (`mapanare_io.c`, NOT `mapanare_tls.c`)

PLAN refs `runtime/native/mapanare_tls.c` — **that file does not
exist.** OpenSSL dlopen plumbing lives in `mapanare_io.c`:

- libssl + libcrypto loaded with version fallback (so.3 → so.1.1
  → so → dylib).
- EVP MD context infrastructure: `EVP_MD_CTX_new/_free`,
  `EVP_DigestInit_ex`, `EVP_DigestUpdate`, `EVP_DigestFinal_ex`.
- Function pointers for: `EVP_sha1`, `EVP_sha256`, `EVP_sha512`,
  `HMAC`.
- Crypto exports already in place:
  - `__mn_sha1_str`, `__mn_sha256_str`, `__mn_sha512_str`
  - `__mn_hmac_sha256_str`
  - `__mn_hex_encode_str`, `__mn_hex_decode_str`
  - `__mn_base64_encode_str`, `__mn_base64_decode_str`
  - `__mn_random_bytes_str`

Cr.8 *extends* this file; it does not create a new
`mapanare_crypto.c`. Mirror v5.35.0 Sq.7's "wrap-don't-duplicate"
decision (the existing `mapanare_db.c` already had the dlopen
plumbing).

---

## Per-Cr.\* item state

| ID | State | v5.39.0 scope | v5.39.1 scope |
|---|---|---|---|
| **Cr.1** | PARTIAL | sha3_256, blake2b, streaming Sha256/Sha512/Sha3 ctx | — |
| **Cr.2** | PARTIAL | hmac_sha512, constant_time_eq, streaming Hmac ctx | — |
| **Cr.3** | NEW | — | AEAD (AES-256-GCM, ChaCha20-Poly1305, NonceCounter) |
| **Cr.4** | NEW | — | Ed25519 sign/verify, X25519 ECDH |
| **Cr.5** | PARTIAL | random_u64, random_range (no new C exports) | — |
| **Cr.6** | NEW | — | PBKDF2, HKDF, Argon2id (with fail-loudly fallback) |
| **Cr.7** | NEW | RFC 6234 SHA + RFC 4231 HMAC vectors | RFC 8439 + 8032 + 7748 + 6070 + 5869 + 9106 |
| **Cr.8** | NEW | ~5 new __mn_* exports in mapanare_io.c | ~10 more |
| **Cr.9** | NEW | docs/stdlib/crypto.md (Cr.1+Cr.2+Cr.5 surface) | extend for Cr.3+Cr.4+Cr.6 |

---

## Load-bearing deviations from PLAN

### D.1 — Layout: single-file, not directory
**PLAN:** `stdlib/crypto/{hash,hmac,aead,sig,kex,random,kdf}.mn`.
**v5.39.0:** keep extending `stdlib/crypto.mn`.
**Reason:** v5.34.0 Dt.\* (date/time), v5.35.0 Sq.\* (sqlite), and
v5.38.0 Re.\* (regex) all shipped single-file for the same reason —
cross-module mangling / extern-propagation limitations
(`time__date_new` mangled but call sites emit unprefixed forward
decls; reproduces with `python3 -m mapanare emit-llvm + clang link`).
Directory layout has to ride a separate cross-module-emitter fix.

### D.2 — C-runtime location: `mapanare_io.c`, not `mapanare_tls.c`
**PLAN:** "Extends the existing OpenSSL dlopen in `mapanare_tls.c`."
**Reality:** no `mapanare_tls.c` exists. OpenSSL plumbing lives in
`mapanare_io.c` (TLS sockets are bundled with general I/O).
**v5.39.0:** new exports appended at the end of the existing crypto
export block in `mapanare_io.c`. ABI-stable (stage1 binaries built
against pre-v5.39.0 runtime keep working).

### D.3 — Staged scope: Cr.1+Cr.2+Cr.5+Cr.7-partial+Cr.9-partial in v5.39.0
**PLAN:** all 9 items in one release.
**v5.39.0:** quick wins only (extending working primitives).
**v5.39.1:** AEAD, Ed25519/X25519, KDF.
**Reason:** AEAD nonce-handling, Ed25519 key serialization, and
Argon2 fallback each have correctness traps. Bundling them with
straightforward hashing additions raises the chance one ships
subtly wrong. Each is structurally independent — the staging
introduces no coupling debt.

### D.4 — Argon2id fallback policy: fail-loudly, not silent-PBKDF2
**PLAN:** "fall back to PBKDF2-SHA256 with a clear log message."
**v5.39.1:** return `Err(CryptoError::InvalidInput("argon2id
unavailable; install libargon2 or upgrade to OpenSSL 3.0+"))`.
**Reason:** silent fallback on a security primitive is the
bug-class the v5.34.0 Dt.6 named-tzdb decision was designed to
avoid. A user calling `argon2id` for password hashing has a
specific security profile in mind; quietly swapping in PBKDF2 with
defaults that may not match Argon2's parameters is worse than a
clear error. Documented as `Cr.6.B` for v5.39.1.

### D.5 — `Bytes` representation: `String` carrying raw bytes
**PLAN:** uses `Bytes` throughout.
**Reality:** Mapanare has no native `Bytes` type at v5.38.0.
**v5.39.0:** continue the existing module's pattern — `String`
carries raw bytes (lengths preserved through `MnString`,
embedded NULs roundtrip through the C runtime). `random_bytes`
keeps its `List<Int>` return for backwards compatibility.
Native `Bytes` type is a v6.0+ candidate.

### D.6 — JWT preservation
**Existing module ships JWT HS256.** Not in PLAN audit. Preserved
unchanged. v5.40.0 ask-flow (API-key handling) likely depends on
this surface.

---

## v5.39.0 deliverable summary

### .mn additions (~~150 LOC)
1. `extern "C" fn` declarations for 5 new exports.
2. Free functions: `sha3_256`, `blake2b`, `hmac_sha512`,
   `constant_time_eq`, `random_u64`, `random_range`.
3. Streaming digest contexts: `Sha256Ctx`, `Sha512Ctx`,
   `Sha3_256Ctx`, `Blake2bCtx`, `HmacSha256Ctx`, `HmacSha512Ctx`
   — wrapped around an `Int` handle pointing at a heap-allocated
   `EVP_MD_CTX*` / `HMAC_CTX*`.

### C-runtime additions (~~150 LOC, all in `mapanare_io.c`)
1. New EVP function pointers: `EVP_sha3_256`, `EVP_blake2b512`,
   `HMAC_CTX_new/_free/_Init_ex/_Update/_Final` (or modern
   `EVP_MAC_*` on OpenSSL 3.x).
2. New exports (appended at end of existing crypto block):
   - `__mn_sha3_256_str(MnString) -> MnString`
   - `__mn_blake2b_str(MnString) -> MnString`
   - `__mn_hmac_sha512_str(MnString, MnString) -> MnString`
   - `__mn_constant_time_eq(MnString, MnString) -> int64_t`
   - `__mn_md_ctx_new(int64_t algo_id) -> int64_t`
   - `__mn_md_ctx_update(int64_t handle, MnString) -> int64_t`
   - `__mn_md_ctx_finalize(int64_t handle) -> MnString`
   - `__mn_hmac_ctx_new(int64_t algo_id, MnString key) -> int64_t`
   - `__mn_hmac_ctx_update(int64_t handle, MnString) -> int64_t`
   - `__mn_hmac_ctx_finalize(int64_t handle) -> MnString`

### Tests (~~250 LOC + fixtures)
- `stdlib/crypto/tests/test_crypto_smoke.mn` — round-trips for
  every new function.
- `stdlib/crypto/tests/test_crypto_corpus.mn` — RFC 6234 SHA-256 /
  SHA-512 / SHA-3-256 vectors + RFC 4231 HMAC-SHA256 / SHA-512
  vectors (~12 cases).
- `tests/stdlib/test_crypto.py` — pytest harness mirroring the
  v5.38.0 Re.\* concatenation pattern.

### Docs (~~250 LOC)
- `docs/stdlib/crypto.md` — quick reference, type/API reference,
  cookbook recipes for shipped items, explicit "AEAD / Ed25519 /
  KDF coming in v5.39.1" note.

---

## Risk

1. **OpenSSL version skew:** SHA-3 added in OpenSSL 1.1.1.
   Mitigation: probe `EVP_sha3_256` at dlopen time; if NULL,
   `__mn_sha3_256_str` returns an empty string and `sha3_256`
   surfaces as `CryptoError::HashError("sha3_256 unavailable;
   requires OpenSSL 1.1.1+")`.
2. **HMAC API drift OpenSSL 1.1 vs 3.x:** `HMAC_CTX_*` deprecated
   in 3.0 favoring `EVP_MAC`. v5.39.0 uses the legacy `HMAC_CTX_*`
   path (still supported in 3.x with deprecation warning suppressed
   at compile time). Migrate to `EVP_MAC` in v5.40.x or v6.0.
3. **Streaming-context handle lifetime:** the `Int` handle wraps
   a heap-allocated `EVP_MD_CTX*` / `HMAC_CTX*`. Caller MUST call
   `_finalize` exactly once. Double-finalize and finalize-then-update
   both return error sentinels rather than crashing. Documented in
   crypto.md.
4. **Constant-time compare vs. compiler optimization:** GCC/Clang
   may optimize naïve `volatile`-marked loops. v5.39.0 uses the
   OpenSSL `CRYPTO_memcmp` symbol when available (constant-time
   guarantee from the upstream library) and falls back to a
   `volatile`-masked loop only when the symbol is absent.

---

## Falsifiability

Every Cr.\* test mirrors RFC test vectors verbatim. A typo in
the SHA-3 padding rule, an off-by-one in HMAC's ipad/opad XOR,
a misordered field in the streaming finalize would all surface
as a one-byte digest mismatch against the RFC expected output —
not as a soft "tests pass on roundtrip" green that masks a
silently broken cipher.

---

## Closeout gates (v5.39.0)

- [ ] Strict 3-stage fixed point preserved (zero
  `mapanare/self/*.mn` source touches; pure stdlib + C-runtime
  additions)
- [ ] Goldens 95/95
- [ ] RFC 6234 SHA + RFC 4231 HMAC vectors GREEN
- [ ] `make ci-gates` GREEN, `make lint` clean
- [ ] ASan + valgrind clean on new C code (streaming contexts;
  size-validation paths)
- [ ] SPEC header re-synced from "v5.38.0 cut" to "v5.39.0 cut"
- [ ] CLAUDE.md release-notes entry includes the staging note
  (Cr.3+Cr.4+Cr.6 explicitly named as v5.39.1)
