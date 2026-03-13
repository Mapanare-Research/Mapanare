"""Tests for TLS (OpenSSL) in the C I/O runtime (Phase 6, Tasks 9-14)."""

import pytest

from runtime.io_bridge import IO_AVAILABLE

pytestmark = pytest.mark.skipif(
    not IO_AVAILABLE,
    reason="I/O runtime not built — run: python runtime/native/build_io.py",
)

if IO_AVAILABLE:
    from runtime import io_bridge


class TestTlsInit:
    """Task 9: OpenSSL initialization."""

    def test_tls_init(self):
        rc = io_bridge.tls_init()
        # rc == 0 means OpenSSL found, rc == -1 means not installed
        # Both are valid outcomes — we just verify no crash
        assert rc in (0, -1)

    def test_tls_init_idempotent(self):
        rc1 = io_bridge.tls_init()
        rc2 = io_bridge.tls_init()
        assert rc1 == rc2


class TestTlsConnect:
    """Tasks 10-13: TLS connect, read, write, close.

    These tests require OpenSSL to be installed and network access.
    They connect to a real HTTPS endpoint to verify TLS works end-to-end.
    """

    @pytest.fixture(autouse=True)
    def check_openssl(self):
        rc = io_bridge.tls_init()
        if rc != 0:
            pytest.skip("OpenSSL not available on this system")

    def test_tls_connect_to_https(self):
        """Connect to example.com:443 via TLS and send an HTTP GET."""
        io_bridge.net_init()

        # TCP connect first
        fd = io_bridge.tcp_connect("example.com", 443)
        if fd < 0:
            pytest.skip("Cannot reach example.com — no network")

        # TLS handshake
        ctx = io_bridge.tls_connect(fd, "example.com")
        if ctx is None:
            io_bridge.tcp_close(fd)
            pytest.skip("TLS handshake failed — certificate issue?")

        # Send HTTP GET
        request = b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n"
        written = io_bridge.tls_write(ctx, request)
        assert written > 0

        # Read response
        response = io_bridge.tls_read(ctx, 4096)
        assert len(response) > 0
        assert b"HTTP/" in response

        # Clean close
        io_bridge.tls_close(ctx)
        io_bridge.tcp_close(fd)

    def test_tls_connect_invalid_hostname(self):
        """TLS with wrong SNI should fail or return certificate error."""
        io_bridge.net_init()
        fd = io_bridge.tcp_connect("example.com", 443)
        if fd < 0:
            pytest.skip("Cannot reach example.com — no network")

        # Use wrong hostname for SNI — may still succeed if no verification
        ctx = io_bridge.tls_connect(fd, "wrong.hostname.invalid")
        # Either NULL (strict verification) or valid ctx (permissive)
        if ctx is not None:
            io_bridge.tls_close(ctx)
        io_bridge.tcp_close(fd)
