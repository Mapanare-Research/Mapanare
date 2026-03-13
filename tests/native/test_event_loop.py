"""Tests for the event loop in the C I/O runtime (Phase 6, Tasks 21-26)."""

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
    from runtime.io_bridge import MN_EVENT_CALLBACK, MN_EVENT_READ


class TestEventLoopLifecycle:
    """Tasks 21, 23: Create and free event loop."""

    def test_create_and_free(self):
        loop = io_bridge.event_loop_new()
        assert loop is not None
        io_bridge.event_loop_free(loop)

    def test_run_once_empty(self):
        """run_once with no fds and timeout=0 should return immediately."""
        loop = io_bridge.event_loop_new()
        assert loop is not None
        n = io_bridge.event_loop_run_once(loop, 0)
        assert n == 0
        io_bridge.event_loop_free(loop)


class TestEventLoopWithSockets:
    """Tasks 22, 24-25: add_fd, run_once, callbacks."""

    def test_readable_callback(self):
        """Register a socket for READ, write data, verify callback fires."""
        io_bridge.net_init()

        port = 18930
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 5)
        assert server_fd >= 0

        # Connect a client
        client_fd = io_bridge.tcp_connect("127.0.0.1", port)
        assert client_fd >= 0

        conn_fd = io_bridge.tcp_accept(server_fd)
        assert conn_fd >= 0

        # Send data to make conn_fd readable
        io_bridge.tcp_send(client_fd, b"DATA")
        time.sleep(0.05)

        # Track callback invocations
        callback_fds = []

        @MN_EVENT_CALLBACK
        def on_readable(fd, events, user_data):
            callback_fds.append(fd)

        loop = io_bridge.event_loop_new()
        assert loop is not None

        rc = io_bridge.event_loop_add_fd(loop, conn_fd, MN_EVENT_READ, on_readable)
        assert rc == 0

        n = io_bridge.event_loop_run_once(loop, 100)
        assert n >= 1
        assert conn_fd in callback_fds

        io_bridge.event_loop_remove_fd(loop, conn_fd)
        io_bridge.event_loop_free(loop)

        io_bridge.tcp_close(conn_fd)
        io_bridge.tcp_close(client_fd)
        io_bridge.tcp_close(server_fd)

    def test_remove_fd(self):
        """Remove an fd and verify callback no longer fires."""
        io_bridge.net_init()

        port = 18931
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 5)
        assert server_fd >= 0

        client_fd = io_bridge.tcp_connect("127.0.0.1", port)
        assert client_fd >= 0

        conn_fd = io_bridge.tcp_accept(server_fd)
        assert conn_fd >= 0

        io_bridge.tcp_send(client_fd, b"DATA")
        time.sleep(0.05)

        callback_count = [0]

        @MN_EVENT_CALLBACK
        def on_event(fd, events, user_data):
            callback_count[0] += 1

        loop = io_bridge.event_loop_new()
        rc = io_bridge.event_loop_add_fd(loop, conn_fd, MN_EVENT_READ, on_event)
        assert rc == 0

        # Remove before polling
        rc = io_bridge.event_loop_remove_fd(loop, conn_fd)
        assert rc == 0

        io_bridge.event_loop_run_once(loop, 50)
        assert callback_count[0] == 0

        io_bridge.event_loop_free(loop)
        io_bridge.tcp_close(conn_fd)
        io_bridge.tcp_close(client_fd)
        io_bridge.tcp_close(server_fd)

    def test_multi_fd(self):
        """Register multiple fds and verify all get dispatched."""
        io_bridge.net_init()

        port1, port2 = 18932, 18933
        srv1 = io_bridge.tcp_listen("127.0.0.1", port1, 5)
        srv2 = io_bridge.tcp_listen("127.0.0.1", port2, 5)
        assert srv1 >= 0 and srv2 >= 0

        cli1 = io_bridge.tcp_connect("127.0.0.1", port1)
        cli2 = io_bridge.tcp_connect("127.0.0.1", port2)
        assert cli1 >= 0 and cli2 >= 0

        conn1 = io_bridge.tcp_accept(srv1)
        conn2 = io_bridge.tcp_accept(srv2)
        assert conn1 >= 0 and conn2 >= 0

        io_bridge.tcp_send(cli1, b"A")
        io_bridge.tcp_send(cli2, b"B")
        time.sleep(0.05)

        ready_fds = set()

        @MN_EVENT_CALLBACK
        def on_event(fd, events, user_data):
            ready_fds.add(fd)

        loop = io_bridge.event_loop_new()
        io_bridge.event_loop_add_fd(loop, conn1, MN_EVENT_READ, on_event)
        io_bridge.event_loop_add_fd(loop, conn2, MN_EVENT_READ, on_event)

        # May need multiple iterations to get both
        for _ in range(3):
            io_bridge.event_loop_run_once(loop, 100)
            if conn1 in ready_fds and conn2 in ready_fds:
                break

        assert conn1 in ready_fds
        assert conn2 in ready_fds

        io_bridge.event_loop_free(loop)
        for fd in [conn1, conn2, cli1, cli2, srv1, srv2]:
            io_bridge.tcp_close(fd)


class TestEventLoopTimeout:
    """Task 25: run_once with timeout."""

    def test_timeout_no_events(self):
        """run_once with no ready fds should return 0 after timeout."""
        io_bridge.net_init()

        port = 18934
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 1)
        assert server_fd >= 0

        @MN_EVENT_CALLBACK
        def noop(fd, events, user_data):
            pass

        loop = io_bridge.event_loop_new()
        # Register server fd for read — but nobody is connecting
        io_bridge.event_loop_add_fd(loop, server_fd, MN_EVENT_READ, noop)

        start = time.monotonic()
        n = io_bridge.event_loop_run_once(loop, 50)  # 50ms timeout
        elapsed = time.monotonic() - start

        assert n == 0
        assert elapsed >= 0.03  # Should have waited ~50ms

        io_bridge.event_loop_remove_fd(loop, server_fd)
        io_bridge.event_loop_free(loop)
        io_bridge.tcp_close(server_fd)


class TestEventLoopStop:
    """Task 24: event_loop_run + stop from another thread."""

    def test_stop_from_thread(self):
        io_bridge.net_init()

        port = 18935
        server_fd = io_bridge.tcp_listen("127.0.0.1", port, 1)
        assert server_fd >= 0

        @MN_EVENT_CALLBACK
        def noop(fd, events, user_data):
            pass

        loop = io_bridge.event_loop_new()
        io_bridge.event_loop_add_fd(loop, server_fd, MN_EVENT_READ, noop)

        # Run loop in background, stop from main thread
        t = threading.Thread(target=io_bridge.event_loop_run, args=(loop,))
        t.start()

        time.sleep(0.1)
        io_bridge.event_loop_stop(loop)
        t.join(timeout=5)
        assert not t.is_alive()

        io_bridge.event_loop_free(loop)
        io_bridge.tcp_close(server_fd)
