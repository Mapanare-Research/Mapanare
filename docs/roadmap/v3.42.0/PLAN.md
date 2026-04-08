# Mapanare v3.42.0 — "Cascabel" (Network Native)

> A native binary can fetch data from the internet.
> TCP, TLS, HTTP, crypto, regex — all from .mn code.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v3.41.0 (mapanare_io.c linked)

---

## The Problem

After v3.41.0, mapanare_io.c is linked but the functions aren't usable from
Mapanare code because:
1. No stdlib wrappers expose them as ergonomic functions
2. The HTTP client requires composing TCP + TLS + HTTP protocol manually
3. Crypto/regex functions need Mapanare-side wrappers

---

## Checklist

### 1. HTTP Client

- [ ] Add `__mn_http_get(url)` to `mapanare_io.c` — convenience wrapper:
  - Parse URL (host, port, path)
  - TCP connect (or TLS for https)
  - Send `GET {path} HTTP/1.1\r\nHost: {host}\r\n\r\n`
  - Read response, extract body after `\r\n\r\n`
  - Return body as `MnString`
- [ ] `stdlib/net/http.mn` — `get(url: String) -> Result<String, String>`
- [ ] Verify: `http_get("http://httpbin.org/get")` returns JSON response

### 2. TCP Client Wrappers

- [ ] `stdlib/net/tcp.mn` — verify extern C declarations match mapanare_io.h
- [ ] `connect(host: String, port: Int) -> Result<Int, String>`
- [ ] `send(fd: Int, data: String) -> Result<Int, String>`
- [ ] `recv(fd: Int) -> Result<String, String>`
- [ ] `close(fd: Int)`

### 3. Crypto Wrappers

- [ ] `stdlib/crypto.mn` — verify extern C declarations work natively
- [ ] `sha256(data: String) -> String` (hex digest)
- [ ] `hmac_sha256(key: String, data: String) -> String`
- [ ] `base64_encode(data: String) -> String`
- [ ] `base64_decode(data: String) -> String`
- [ ] `random_bytes(n: Int) -> String`

### 4. Regex Wrappers

- [ ] `stdlib/text/regex.mn` or add to `stdlib/text.mn`
- [ ] `regex_match(pattern: String, subject: String) -> Bool`
- [ ] `regex_find(pattern: String, subject: String) -> Option<String>`
- [ ] `regex_replace(pattern: String, subject: String, replacement: String) -> String`
- [ ] Graceful fallback when PCRE2 not available (return empty/false)

### 5. Golden Tests

- [ ] `37_http_get.mn` — fetch a URL, print response length (skip if offline)
- [ ] `38_crypto.mn` — SHA-256 hash, base64 encode/decode, HMAC
- [ ] `39_regex.mn` — match, find, replace patterns

### 6. Culebra Validation

- [ ] `culebra scan` on all new IR — zero critical
- [ ] `culebra abi` — verify all IO function signatures match C headers

---

## Exit Criteria

```mn
import net::http
import crypto

fn main() {
    let response = http::get("http://httpbin.org/ip")
    match response {
        Ok(body) => {
            print("Response: " + body)
            let hash = crypto::sha256(body)
            print("SHA-256: " + hash)
        }
        Err(e) => print("Error: " + e)
    }
}
```
