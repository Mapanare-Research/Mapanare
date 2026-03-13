"""Phase 6 — crypto.mn — Cryptographic Primitives tests.

Tests verify that the crypto stdlib module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation (Phase 8) is not yet
ready, tests inline the crypto module source code within test programs.

Covers:
  - CryptoError enum variants
  - SHA-256, SHA-512 hex digest wrappers
  - HMAC-SHA256
  - Base64 encode/decode + URL-safe variants
  - Hex encode/decode
  - JWT encode/decode/verify (HS256)
  - Random bytes and random hex
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CRYPTO_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "crypto.mn").read_text(
    encoding="utf-8"
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_crypto.mn", use_mir=True)


def _crypto_source_with_main(main_body: str) -> str:
    """Prepend the crypto module source and wrap main_body in fn main()."""
    return _CRYPTO_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Task 18: CryptoError enum
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCryptoError:
    def test_invalid_input_compiles(self) -> None:
        """CryptoError::InvalidInput variant compiles."""
        src = _crypto_source_with_main('let e: CryptoError = InvalidInput("bad")\nprintln("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_failed_compiles(self) -> None:
        """CryptoError::DecodeFailed variant compiles."""
        src = _crypto_source_with_main('let e: CryptoError = DecodeFailed("fail")\nprintln("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_verification_failed_compiles(self) -> None:
        """CryptoError::VerificationFailed variant compiles."""
        src = _crypto_source_with_main(
            'let e: CryptoError = VerificationFailed("sig")\nprintln("ok")'
        )
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hash_error_compiles(self) -> None:
        """CryptoError::HashError variant compiles."""
        src = _crypto_source_with_main('let e: CryptoError = HashError("err")\nprintln("ok")')
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 1-5: Hashing (SHA-256, SHA-512 hex digests)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHashing:
    def test_sha1_compiles(self) -> None:
        """sha1() hex digest compiles."""
        src = _crypto_source_with_main("""\
            let h: String = sha1("hello")
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_sha1_str" in ir_out

    def test_sha256_compiles(self) -> None:
        """sha256() hex digest compiles."""
        src = _crypto_source_with_main("""\
            let h: String = sha256("hello")
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_sha256_str" in ir_out

    def test_sha512_compiles(self) -> None:
        """sha512() hex digest compiles."""
        src = _crypto_source_with_main("""\
            let h: String = sha512("hello")
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_sha512_str" in ir_out

    def test_sha256_raw_compiles(self) -> None:
        """sha256_raw() returns binary hash."""
        src = _crypto_source_with_main("""\
            let h: String = sha256_raw("test")
            println("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sha512_raw_compiles(self) -> None:
        """sha512_raw() returns binary hash."""
        src = _crypto_source_with_main("""\
            let h: String = sha512_raw("test")
            println("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sha256_extern_declared(self) -> None:
        """SHA-256 extern declaration present in compiled IR."""
        src = _crypto_source_with_main('println("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_sha256_str" in ir_out

    def test_sha512_extern_declared(self) -> None:
        """SHA-512 extern declaration present in compiled IR."""
        src = _crypto_source_with_main('println("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_sha512_str" in ir_out

    def test_hex_encode_extern_declared(self) -> None:
        """Hex encode extern declaration present (used by hash wrappers)."""
        src = _crypto_source_with_main('println("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_hex_encode_str" in ir_out


# ---------------------------------------------------------------------------
# Tasks 6-7: HMAC-SHA256
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHMAC:
    def test_hmac_sha256_compiles(self) -> None:
        """hmac_sha256() hex digest compiles."""
        src = _crypto_source_with_main("""\
            let h: String = hmac_sha256("secret-key", "message")
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_hmac_sha256_str" in ir_out

    def test_hmac_sha256_raw_compiles(self) -> None:
        """hmac_sha256_raw() returns binary HMAC."""
        src = _crypto_source_with_main("""\
            let h: String = hmac_sha256_raw("key", "data")
            println("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 8-9: Base64 encode/decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBase64:
    def test_base64_encode_compiles(self) -> None:
        """base64_encode() compiles."""
        src = _crypto_source_with_main("""\
            let encoded: String = base64_encode("hello world")
            println(encoded)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_base64_encode_str" in ir_out

    def test_base64_decode_compiles(self) -> None:
        """base64_decode() returns Result compiles."""
        src = _crypto_source_with_main("""\
            let r: Result<String, CryptoError> = base64_decode("aGVsbG8=")
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_base64url_encode_compiles(self) -> None:
        """base64url_encode() (URL-safe, no padding) compiles."""
        src = _crypto_source_with_main("""\
            let encoded: String = base64url_encode("hello world!")
            println(encoded)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_base64url_decode_compiles(self) -> None:
        """base64url_decode() returns Result compiles."""
        src = _crypto_source_with_main("""\
            let r: Result<String, CryptoError> = base64url_decode("aGVsbG8")
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_base64_round_trip_compiles(self) -> None:
        """Base64 encode then decode compiles."""
        src = _crypto_source_with_main("""\
            let encoded: String = base64_encode("round trip test")
            let r: Result<String, CryptoError> = base64_decode(encoded)
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("decode error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 10-11: Hex encode/decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestHex:
    def test_hex_encode_compiles(self) -> None:
        """hex_encode() compiles."""
        src = _crypto_source_with_main("""\
            let h: String = hex_encode("abc")
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hex_decode_compiles(self) -> None:
        """hex_decode() returns Result compiles."""
        src = _crypto_source_with_main("""\
            let r: Result<String, CryptoError> = hex_decode("616263")
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hex_decode_odd_length_compiles(self) -> None:
        """hex_decode with odd length returns Err."""
        src = _crypto_source_with_main("""\
            let r: Result<String, CryptoError> = hex_decode("abc")
            match r {
                Ok(decoded) => { println("should not happen") },
                Err(e) => { println("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hex_round_trip_compiles(self) -> None:
        """Hex encode then decode compiles."""
        src = _crypto_source_with_main("""\
            let encoded: String = hex_encode("hello")
            let r: Result<String, CryptoError> = hex_decode(encoded)
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 12-14: JWT (HS256)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestJWT:
    def test_jwt_encode_compiles(self) -> None:
        """jwt_encode() with JSON payload string compiles."""
        src = _crypto_source_with_main("""\
            let token: String = jwt_encode("{\\\"sub\\\":\\\"1234\\\"}", "secret")
            println(token)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_decode_compiles(self) -> None:
        """jwt_decode() returns Result<String, CryptoError> compiles."""
        src = _crypto_source_with_main("""\
            let token: String = jwt_encode("{\\\"user\\\":\\\"alice\\\"}", "mykey")
            let r: Result<String, CryptoError> = jwt_decode(token, "mykey")
            match r {
                Ok(payload) => { println(payload) },
                Err(e) => { println("error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_verify_compiles(self) -> None:
        """jwt_verify() returns Bool compiles."""
        src = _crypto_source_with_main("""\
            let token: String = jwt_encode("{\\\"data\\\":\\\"test\\\"}", "key123")
            let valid: Bool = jwt_verify(token, "key123")
            if valid {
                println("verified")
            } else {
                println("invalid")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_verify_wrong_key_compiles(self) -> None:
        """jwt_verify with wrong key returns false (compiles)."""
        src = _crypto_source_with_main("""\
            let token: String = jwt_encode("{\\\"x\\\":\\\"y\\\"}", "correct-key")
            let valid: Bool = jwt_verify(token, "wrong-key")
            if valid {
                println("should not verify")
            } else {
                println("correctly rejected")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_decode_invalid_token_compiles(self) -> None:
        """jwt_decode with malformed token compiles."""
        src = _crypto_source_with_main("""\
            let r: Result<String, CryptoError> = jwt_decode("not.a.valid.jwt", "key")
            match r {
                Ok(payload) => { println(payload) },
                Err(e) => { println("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_round_trip_compiles(self) -> None:
        """JWT encode → decode round-trip compiles."""
        src = _crypto_source_with_main("""\
            let payload: String = "{\\\"sub\\\":\\\"user1\\\",\\\"iat\\\":1234}"
            let secret: String = "super-secret"
            let token: String = jwt_encode(payload, secret)
            let verified: Bool = jwt_verify(token, secret)
            let r: Result<String, CryptoError> = jwt_decode(token, secret)
            match r {
                Ok(decoded) => { println(decoded) },
                Err(e) => { println("decode error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 15-17: Random bytes
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRandom:
    def test_random_bytes_compiles(self) -> None:
        """random_bytes() returns List<Int> compiles."""
        src = _crypto_source_with_main("""\
            let bytes: List<Int> = random_bytes(16)
            println(str(len(bytes)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_random_bytes_str" in ir_out

    def test_random_hex_compiles(self) -> None:
        """random_hex() returns hex string compiles."""
        src = _crypto_source_with_main("""\
            let h: String = random_hex(16)
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_random_bytes_extern_declared(self) -> None:
        """Random bytes extern declaration present in compiled IR."""
        src = _crypto_source_with_main('println("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_random_bytes_str" in ir_out


# ---------------------------------------------------------------------------
# Integration patterns
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCryptoIntegration:
    def test_hash_and_encode_pipeline_compiles(self) -> None:
        """Hash → hex encode → base64 encode pipeline compiles."""
        src = _crypto_source_with_main("""\
            let h: String = sha256("input data")
            let b64: String = base64_encode(h)
            println(b64)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_hmac_then_hex_compiles(self) -> None:
        """HMAC → hex digest pipeline compiles."""
        src = _crypto_source_with_main("""\
            let mac: String = hmac_sha256("key", "message")
            println(mac)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_all_hash_functions_compile(self) -> None:
        """All hash functions used together compile."""
        src = _crypto_source_with_main("""\
            let h1: String = sha1("test")
            let h2: String = sha256("test")
            let h3: String = sha512("test")
            println(h1)
            println(h2)
            println(h3)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_random_and_hash_compiles(self) -> None:
        """Random hex → hash pipeline compiles."""
        src = _crypto_source_with_main("""\
            let nonce: String = random_hex(32)
            let h: String = sha256(nonce)
            println(h)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jwt_full_flow_compiles(self) -> None:
        """Full JWT flow: encode → verify → decode compiles."""
        src = _crypto_source_with_main("""\
            let payload: String = "{\\\"role\\\":\\\"admin\\\"}"
            let secret: String = "jwt-secret-key"
            let token: String = jwt_encode(payload, secret)
            let ok: Bool = jwt_verify(token, secret)
            if ok {
                let r: Result<String, CryptoError> = jwt_decode(token, secret)
                match r {
                    Ok(p) => { println(p) },
                    Err(e) => { println("err") }
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
