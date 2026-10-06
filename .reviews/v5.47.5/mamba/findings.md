# Mamba — v5.47.5 Closeout Panel Findings

**Reviewer axis:** Security + correctness under adversarial inputs
**Arc reviewed:** v5.31.0 → v5.47.0 (17 releases)
**Audit reference:** `.reviews/v5.47.5/PRE_PANEL_AUDIT.md`
**Prior-panel score:** 9.80 (v5.28.0 RE-PANEL)

---

## Summary

The arc shipped two security-load-bearing surfaces:
**v5.39.0 Cr.\* crypto baseline** (hashing additions,
streaming digest, HMAC-SHA512, constant_time_eq, random_u64
+ random_range with rejection sampling) and **v5.43.0 Da.\*
distributed agents wire-format** (length-prefixed
HMAC-SHA256-signed JSON over TCP/TLS, per-connection
last_seen replay watermark, 100MB DoS guard).

Both surfaces are well-engineered. The v5.43.0 wire-format
v1 in particular is the most security-conscious cross-
process contract in the project. The 1000-iteration
network-fuzz across 8 input variants (oversize length,
length=0, truncated, random body, sub-header, length-
without-body, all-random, immediate close) found 0 crashes /
0 hangs — that's substantive adversarial-input testing.

The v5.39.0 → v5.39.1 explicit deferral of AEAD + Ed25519/
X25519 + Argon2id was the **right correctness call**:
each has a known correctness trap (GCM nonce reuse,
Ed25519 key serialization, Argon2 OpenSSL major-version
skew), and bundling them with the easy hashing additions
raised the chance one ships subtly wrong. Structural
independence justified the split.

---

## Per-category grades

### Wire-format security model (v5.43.0)

**Grade: EXCEEDS**

`[u32 length BE][u8 v=1][u8 mt][u64 seq BE][16 b hmac][JSON]`:

- **HMAC-SHA256 truncation to 16 bytes** follows RFC 4868
  (secure for keys ≥ 32 raw bytes); `MAPANARE_NODE_KEY`
  env var explicit; documented in cookbook
- **Per-connection last_seen replay watermark** rejects
  out-of-order frames; replay-resistant
- **100MB DoS guard** caps single-frame allocation;
  prevents memory-exhaustion DoS
- **Length validation** before payload allocation;
  prevents undersize/oversize attacks
- **Version byte as escape hatch** for v2 frame format

The 1000-iteration randomized-input fuzz across 8
input-shape variants is the high watermark for v5
adversarial testing. **All 1001 accepts handled correctly;
0 crashes; 0 hangs.**

### Crypto baseline (v5.39.0)

**Grade: EXCEEDS**

Cr.\* additions:
- SHA-3-256 (FIPS 202; OpenSSL 1.1.1+)
- BLAKE2b (RFC 7693; 1.1.0+)
- Streaming `DigestCtx` (chunk-update-finalize)
- HMAC-SHA512
- `constant_time_eq` (prefers OpenSSL CRYPTO_memcmp;
  falls back to volatile-masked aggregation loop)
- `random_u64()` (8 bytes from `__mn_random_bytes_str`,
  packed BE)
- `random_range(low, high)` rejection sampling (avoids
  modulo bias)

RFC test corpus (RFC 6234 SHA-256/SHA-512, FIPS 202
SHA-3-256, RFC 7693 BLAKE2b-512, RFC 4231 HMAC tests
1/2/4/5) validates against published test vectors. **No
roll-your-own crypto.**

### Cr.0 emitter shortcut bypass discovery (LOAD-BEARING)

**Grade: EXCEEDS**

`mapanare/emit_llvm_text.py:3713-3776` had unconditional
builtin shortcuts for `sha256`, `hmac_sha256`, `base64_encode`,
etc. that called `__mn_*_str` C exports directly,
**bypassing user-defined wrappers** in `stdlib/crypto.mn`
that hex-encode output / wrap in Result types. When MIR
inlining failed (high call-site count or function-size
threshold), the shortcut won and silently changed the
return shape — `sha256(x)` returned 32 raw bytes instead
of 64 hex chars.

**Latent since v3.42.0** (when shortcuts were introduced).
Surfaced by v5.39.0 Cr.\* RFC corpus tests with 5
hmac_sha256 callsites; 4 returned raw, 1 (the only call
from inside `hmac_sha256`'s own user-defined chain)
inlined cleanly. Asymmetric-failure pattern was the
diagnostic. **Fix: gate each shortcut on `fn not in
self._sigs`**, deferring to user-defined wrapper when
present.

This is the **same bug-class as v5.36.0 Js.0 (`_san`
sanitizer over-stripping `%`) and v5.36.0 Js.0.B (Result
wrap-shape mismatch)** — emitter bugs surfaced by
extending stdlib in ways that exercise more code paths.

### Deferred-crypto discipline (v5.39.0 → v5.39.1)

**Grade: EXCEEDS**

AEAD (AES-GCM, ChaCha20-Poly1305) + Ed25519/X25519 +
PBKDF2/HKDF/Argon2id explicitly deferred to v5.39.1+.
Rationale documented: each has known correctness traps;
bundling with easy hashing additions raises subtle-bug
ship risk. **The deferral is the right correctness call.**
At v5.47.5 HEAD these are NOT v5.39.0 carry — they're
v5.40.0+ candidates that have not been picked up; that's
fine for v5.

### `MAPANARE_NODE_KEY` config surface

**Grade: MEETS**

v5.43.0 supervision.mn ships `node_key_from_env`,
`node_ping_interval_ms`, `node_ping_timeout_ms` env
config readers. **No baked-in keys.** The env-read
surface is documented in the cookbook + source preamble.

### Package-system security (v5.44.0 / v5.44.1)

**Grade: MEETS**

Reserved-source-literal contract (`mn_modules`, `path`,
`git`, `global-cache`) — only `mn_modules` shipped at
v5.44.0; **opportunistic global-cache scan explicitly
rejected** by `tests/packages/test_resolver_does_not_scan_global_cache.py`.
Forward-compat hygiene preserved.

Registry-side package signing **deferred** (v5.44.0 LOW
carry; v6.0+ candidate). At v5.47.5 HEAD, packages
install without signature verification — acceptable for
v5 but should not ship to a public registry without
signing in v6.0+.

---

## Findings

### Ma.0 — wire-format v1 is project security high watermark (LOW, positive)

v5.43.0 Da.\* wire format. The HMAC truncation rationale,
replay defense, DoS guard, and 1000-iteration fuzz are
all best-practice. **Recommend the shape as v6.0 model**
for any future cross-network contract.

### Ma.1 — Cr.0 emitter shortcut bypass class (LOW, positive)

Closed structurally at v5.39.0 by gating shortcuts on
`fn not in self._sigs`. The bug-class (emitter
shortcuts silently bypassing user-defined wrappers)
shares root with v5.36.0 Js.0/Js.0.B. **Recommend a
v6.0 audit pass:** sweep `emit_llvm_text.py` for
remaining unconditional shortcuts (regex_match,
regex_replace, http_get, etc.) that may exhibit the
same latent class.

### Ma.2 — deferred-crypto correctness discipline (LOW, positive)

AEAD + Ed25519/X25519 + Argon2id explicitly deferred at
v5.39.0 → v5.39.1. **The right call.** Each has known
trap; bundling raises subtle-bug ship risk. Should ship
in a dedicated future release (v5.39.x or v6.0+) with
its own RFC test corpus + adversarial-input gates.

### Ma.3 — registry-side package signing deferred (MEDIUM, fresh, v6.0 input)

v5.44.0 Ps.\* shipped install-from-mn_modules without
signature verification. **Recommend v6.0 PLAN explicit
elevation** before any public registry launch. Even with
sigstore-style signing optional, the contract must
support it.

### Ma.4 — RFC corpus discipline as v6.0 default (LOW, positive)

v5.39.0 Cr.\* shipped with RFC 6234 / FIPS 202 / RFC 7693
/ RFC 4231 test vectors. **The pattern should be the
default for any v6.0 cryptographic / security-load-
bearing surface.**

### Ma.New1 — adversarial-input testing as v6.0 default (LOW, positive)

v5.43.0 Da.\* 1000-iteration network fuzz is the model.
**Recommend v6.0 PLAN documents adversarial-input testing
as mandatory** for any cross-process / network-bound /
parser-bound surface.

### Ma.New2 — `EVP_MAC` migration carry (LOW, fresh)

v5.39.0 Cr.2 noted "HMAC over SHA-3 / BLAKE2 is v5.40.x+
via `EVP_MAC` migration". At v5.47.0 HEAD this is unshipped.
**Acceptable** — HMAC-SHA256/SHA-512 covers ~95% of HMAC
use; SHA-3/BLAKE2 HMAC is niche. Track as v6.0+ LOW.

---

## Carry-forward suggestions

For Cp.4 V5_TO_V6_CARRY.md:

- **(a) v6.0 PLAN input:** Registry-side package signing
  (Ma.3) — pre-registry-launch requirement
- **(a) v6.0 PLAN input:** v6.0 emitter-shortcut audit
  pass (Ma.1) — sweep for latent class
- **(retain process input for v6.0):** RFC corpus +
  adversarial-input testing as default for security-
  load-bearing surfaces (Ma.4 + Ma.New1)
- **(b) v5.47.x patch candidate:** AEAD + Ed25519/X25519
  + Argon2id ship release (Ma.2) — when ready, with
  RFC corpus
- **(b) v5.47.x patch candidate:** `EVP_MAC` migration
  for HMAC over SHA-3/BLAKE2 (Ma.New2) — niche; not
  blocker

---

## Score

**9.85 / 10**

Up 0.05 from v5.28.0's 9.80 — driven by the v5.43.0 wire-
format engineering and the v5.39.0 Cr.0 structural fix
class closure. The 0.15 gap is registry-side package
signing being a real v6.0 input that's not yet on the
PLAN draft, plus the deferred-crypto items being honest
deferrals not subtle holes.

## Recommendation

**PASS**

v5 ships clean from the security axis. v6.0 green-lit
conditional on Ma.3 (package signing) being explicit in
v6.0 PLAN before any public registry effort.
