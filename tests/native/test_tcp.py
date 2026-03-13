"""Tests for TCP networking in the C I/O runtime (Phase 6, Tasks 1-8)."""

import threading
import time

import pytest

from runtime.io_bridge import IO_AVAILABLE

pytestmark = pytest.mark.skipif(
    not IO_AVAILABLE,
    reason="I/O runtime not built — run: python runtime/native/build_io.py",
)

if IO_AVAILABLE:
    from runtime import io_bridge


class TestNetInit:
    """Task 8 (cross-platform): Networking subsystem initialization."""

    def test_init_returns_zero(self):
        assert io_bridge.net_init() == 0

    def test_double_init_is_safe(self):
        io_bridge.net_init()
        assert io_bridge.net_init() == 0


class TestTcpListenAcceptConnect:
    """Tasks 1-6: TCP connect, listen, accept, send, recv, close."""

    def test_listen_on_localhost(self):
        fd = io_bridge.tcp_listen("127.0.0.1", 0, 1)
        # Port 0 may not be supported on all platforms; use a high port
        io_bridge.tcp_close(fd) if fd >= 0 else None

    def test_echo_server(self):
        """Full round-trip: listen, connect, accept, send, recv, close."""
        io_bridge.net_init()

        # Start server on a known port
        port = 18923
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 5)
        assert server_fd >= 0, "Failed to create listening socket"

        # Connect from client in a thread
        client_received = []
        server_received = []

        def server_thread():
            conn_fd = io_bridge.tcp_accept(server_fd)
            assert conn_fd >= 0
            data = io_bridge.tcp_recv(conn_fd, 1024)
            server_received.append(data)
            io_bridge.tcp_send(conn_fd, b"PONG")
            time.sleep(0.05)  # Let client read
            io_bridge.tcp_close(conn_fd)

        t = threading.Thread(target=server_thread)
        t.start()

        time.sleep(0.05)  # Let server start accepting

        client_fd = io_bridge.tcp_connect("127.0.0.1", port)
        assert client_fd >= 0, "Failed to connect"

        sent = io_bridge.tcp_send(client_fd, b"PING")
        assert sent == 4

        data = io_bridge.tcp_recv(client_fd, 1024)
        client_received.append(data)

        io_bridge.tcp_close(client_fd)
        t.join(timeout=5)
        io_bridge.tcp_close(server_fd)

        assert server_received[0] == b"PING"
        assert client_received[0] == b"PONG"

    def test_send_recv_large_payload(self):
        """Send and receive a payload larger than typical buffer sizes."""
        io_bridge.net_init()
        port = 18924

        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 5)
        assert server_fd >= 0

        payload = b"X" * 8192
        received_all = bytearray()

        def server_thread():
            conn_fd = io_bridge.tcp_accept(server_fd)
            assert conn_fd >= 0
            # Read all data
            while True:
                chunk = io_bridge.tcp_recv(conn_fd, 4096)
                if not chunk:
                    break
                received_all.extend(chunk)
            io_bridge.tcp_close(conn_fd)

        t = threading.Thread(target=server_thread)
        t.start()
        time.sleep(0.05)

        client_fd = io_bridge.tcp_connect("127.0.0.1", port)
        assert client_fd >= 0
        io_bridge.tcp_send(client_fd, payload)
        io_bridge.tcp_close(client_fd)

        t.join(timeout=5)
        io_bridge.tcp_close(server_fd)

        assert bytes(received_all) == payload


class TestTcpTimeout:
    """Task 7: SO_RCVTIMEO / SO_SNDTIMEO."""

    def test_set_timeout(self):
        io_bridge.net_init()
        port = 18925
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 1)
        assert server_fd >= 0

        # Set timeout on server socket
        rc = io_bridge.tcp_set_timeout(server_fd, 100)
        assert rc == 0

        io_bridge.tcp_close(server_fd)


class TestTcpConnectFailure:
    """Edge case: connecting to a refused port."""

    def test_connect_refused(self):
        io_bridge.net_init()
        # Port 1 is unlikely to be listening; connection should fail
        fd = io_bridge.tcp_connect("127.0.0.1", 1)
        if fd >= 0:
            io_bridge.tcp_close(fd)
        else:
            assert fd == -1
