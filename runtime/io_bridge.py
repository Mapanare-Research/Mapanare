"""Python ctypes bridge for the Mapanare I/O runtime.

Provides Python wrappers around the C I/O primitives: TCP sockets,
TLS (OpenSSL), file I/O, and event loop multiplexing.
"""

from __future__ import annotations

import ctypes
import platform
from pathlib import Path

# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

_NATIVE_DIR = Path(__file__).parent / "native"

IO_AVAILABLE = False
_lib = None

try:
    system = platform.system()
    if system == "Windows":
        lib_name = "mapanare_io.dll"
    elif system == "Darwin":
        lib_name = "libmapanare_io.dylib"
    else:
        lib_name = "libmapanare_io.so"

    lib_path = _NATIVE_DIR / lib_name
    if lib_path.exists():
        _lib = ctypes.CDLL(str(lib_path))
        IO_AVAILABLE = True
except OSError:
    pass

# ---------------------------------------------------------------------------
# ctypes struct definitions
# ---------------------------------------------------------------------------


class MnFileStat(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_int64),
        ("mtime", ctypes.c_int64),
        ("is_dir", ctypes.c_int64),
    ]


class MnDirEntry(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * 256),
        ("is_dir", ctypes.c_int64),
    ]


# Event callback type: void (*)(int64_t fd, int64_t events, void *user_data)
MN_EVENT_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int64, ctypes.c_int64, ctypes.c_void_p)

# ---------------------------------------------------------------------------
# Function signatures
# ---------------------------------------------------------------------------

if IO_AVAILABLE and _lib is not None:
    # -- Networking init --
    _lib.__mn_net_init.restype = ctypes.c_int64
    _lib.__mn_net_init.argtypes = []

    _lib.__mn_net_cleanup.restype = None
    _lib.__mn_net_cleanup.argtypes = []

    # -- TCP --
    _lib.__mn_tcp_connect.restype = ctypes.c_int64
    _lib.__mn_tcp_connect.argtypes = [ctypes.c_char_p, ctypes.c_int64]

    _lib.__mn_tcp_listen.restype = ctypes.c_int64
    _lib.__mn_tcp_listen.argtypes = [ctypes.c_char_p, ctypes.c_int64, ctypes.c_int64]

    _lib.__mn_tcp_accept.restype = ctypes.c_int64
    _lib.__mn_tcp_accept.argtypes = [ctypes.c_int64]

    _lib.__mn_tcp_send.restype = ctypes.c_int64
    _lib.__mn_tcp_send.argtypes = [ctypes.c_int64, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_tcp_recv.restype = ctypes.c_int64
    _lib.__mn_tcp_recv.argtypes = [ctypes.c_int64, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_tcp_close.restype = None
    _lib.__mn_tcp_close.argtypes = [ctypes.c_int64]

    _lib.__mn_tcp_set_timeout.restype = ctypes.c_int64
    _lib.__mn_tcp_set_timeout.argtypes = [ctypes.c_int64, ctypes.c_int64]

    # -- TLS --
    _lib.__mn_tls_init.restype = ctypes.c_int64
    _lib.__mn_tls_init.argtypes = []

    _lib.__mn_tls_connect.restype = ctypes.c_void_p
    _lib.__mn_tls_connect.argtypes = [ctypes.c_int64, ctypes.c_char_p]

    _lib.__mn_tls_read.restype = ctypes.c_int64
    _lib.__mn_tls_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_tls_write.restype = ctypes.c_int64
    _lib.__mn_tls_write.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_tls_close.restype = None
    _lib.__mn_tls_close.argtypes = [ctypes.c_void_p]

    # -- File I/O --
    _lib.__mn_file_open.restype = ctypes.c_int64
    _lib.__mn_file_open.argtypes = [ctypes.c_char_p, ctypes.c_int64]

    _lib.__mn_file_read_fd.restype = ctypes.c_int64
    _lib.__mn_file_read_fd.argtypes = [ctypes.c_int64, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_file_write_fd.restype = ctypes.c_int64
    _lib.__mn_file_write_fd.argtypes = [ctypes.c_int64, ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_file_close.restype = None
    _lib.__mn_file_close.argtypes = [ctypes.c_int64]

    _lib.__mn_file_stat.restype = ctypes.c_int64
    _lib.__mn_file_stat.argtypes = [ctypes.c_char_p, ctypes.POINTER(MnFileStat)]

    _lib.__mn_dir_list.restype = ctypes.c_int64
    _lib.__mn_dir_list.argtypes = [ctypes.c_char_p, ctypes.POINTER(MnDirEntry), ctypes.c_int64]

    # -- Event Loop --
    _lib.__mn_event_loop_new.restype = ctypes.c_void_p
    _lib.__mn_event_loop_new.argtypes = []

    _lib.__mn_event_loop_add_fd.restype = ctypes.c_int64
    _lib.__mn_event_loop_add_fd.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int64,
        ctypes.c_int64,
        MN_EVENT_CALLBACK,
        ctypes.c_void_p,
    ]

    _lib.__mn_event_loop_remove_fd.restype = ctypes.c_int64
    _lib.__mn_event_loop_remove_fd.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_event_loop_run.restype = None
    _lib.__mn_event_loop_run.argtypes = [ctypes.c_void_p]

    _lib.__mn_event_loop_run_once.restype = ctypes.c_int64
    _lib.__mn_event_loop_run_once.argtypes = [ctypes.c_void_p, ctypes.c_int64]

    _lib.__mn_event_loop_stop.restype = None
    _lib.__mn_event_loop_stop.argtypes = [ctypes.c_void_p]

    _lib.__mn_event_loop_free.restype = None
    _lib.__mn_event_loop_free.argtypes = [ctypes.c_void_p]


# ---------------------------------------------------------------------------
# Python API wrappers
# ---------------------------------------------------------------------------

# File mode constants
MN_FILE_READ = 0
MN_FILE_WRITE = 1
MN_FILE_APPEND = 2
MN_FILE_CREATE = 3

# Event flags
MN_EVENT_READ = 1
MN_EVENT_WRITE = 2


def net_init() -> int:
    """Initialize the networking subsystem."""
    assert _lib is not None
    return int(_lib.__mn_net_init())


def net_cleanup() -> None:
    """Cleanup the networking subsystem."""
    assert _lib is not None
    _lib.__mn_net_cleanup()


def tcp_connect(host: str, port: int) -> int:
    """Connect to host:port via TCP. Returns socket fd or -1."""
    assert _lib is not None
    return int(_lib.__mn_tcp_connect(host.encode("utf-8"), port))


def tcp_listen(host: str | None, port: int, backlog: int = 128) -> int:
    """Listen on host:port. Returns listening socket fd or -1."""
    assert _lib is not None
    h = host.encode("utf-8") if host else None
    return int(_lib.__mn_tcp_listen(h, port, backlog))


def tcp_accept(listen_fd: int) -> int:
    """Accept connection. Returns new fd or -1."""
    assert _lib is not None
    return int(_lib.__mn_tcp_accept(listen_fd))


def tcp_send(fd: int, data: bytes) -> int:
    """Send data. Returns bytes sent or -1."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(data)
    return int(_lib.__mn_tcp_send(fd, buf, len(data)))


def tcp_recv(fd: int, max_len: int = 4096) -> bytes:
    """Receive data. Returns bytes received (empty on error/close)."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(max_len)
    n = _lib.__mn_tcp_recv(fd, buf, max_len)
    if n <= 0:
        return b""
    return buf.raw[:n]


def tcp_close(fd: int) -> None:
    """Close a socket."""
    assert _lib is not None
    _lib.__mn_tcp_close(fd)


def tcp_set_timeout(fd: int, ms: int) -> int:
    """Set socket timeout in milliseconds."""
    assert _lib is not None
    return int(_lib.__mn_tcp_set_timeout(fd, ms))


def tls_init() -> int:
    """Initialize TLS (OpenSSL). Returns 0 on success, -1 if unavailable."""
    assert _lib is not None
    return int(_lib.__mn_tls_init())


def tls_connect(fd: int, hostname: str) -> int | None:
    """Wrap a TCP socket with TLS. Returns opaque context or None."""
    assert _lib is not None
    ctx = _lib.__mn_tls_connect(fd, hostname.encode("utf-8"))
    return ctx if ctx else None


def tls_read(ctx: int, max_len: int = 4096) -> bytes:
    """Read from TLS connection."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(max_len)
    n = _lib.__mn_tls_read(ctx, buf, max_len)
    if n <= 0:
        return b""
    return buf.raw[:n]


def tls_write(ctx: int, data: bytes) -> int:
    """Write to TLS connection. Returns bytes written or -1."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(data)
    return int(_lib.__mn_tls_write(ctx, buf, len(data)))


def tls_close(ctx: int) -> None:
    """Close TLS connection."""
    assert _lib is not None
    _lib.__mn_tls_close(ctx)


def file_open(path: str, mode: int = MN_FILE_READ) -> int:
    """Open a file. Returns fd or -1."""
    assert _lib is not None
    return int(_lib.__mn_file_open(path.encode("utf-8"), mode))


def file_read_fd(fd: int, max_len: int = 4096) -> bytes:
    """Read from an open file fd."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(max_len)
    n = _lib.__mn_file_read_fd(fd, buf, max_len)
    if n <= 0:
        return b""
    return buf.raw[:n]


def file_write_fd(fd: int, data: bytes) -> int:
    """Write to an open file fd. Returns bytes written or -1."""
    assert _lib is not None
    buf = ctypes.create_string_buffer(data)
    return int(_lib.__mn_file_write_fd(fd, buf, len(data)))


def file_close(fd: int) -> None:
    """Close an open file fd."""
    assert _lib is not None
    _lib.__mn_file_close(fd)


def file_stat(path: str) -> MnFileStat | None:
    """Get file status. Returns MnFileStat or None on error."""
    assert _lib is not None
    st = MnFileStat()
    rc = _lib.__mn_file_stat(path.encode("utf-8"), ctypes.byref(st))
    if rc < 0:
        return None
    return st


def dir_list(path: str, max_entries: int = 1024) -> list[dict[str, object]]:
    """List directory entries. Returns list of {name, is_dir} dicts."""
    assert _lib is not None
    entries = (MnDirEntry * max_entries)()
    n = _lib.__mn_dir_list(path.encode("utf-8"), entries, max_entries)
    if n < 0:
        return []
    result = []
    for i in range(n):
        result.append(
            {
                "name": entries[i].name.decode("utf-8", errors="replace"),
                "is_dir": bool(entries[i].is_dir),
            }
        )
    return result


def event_loop_new() -> int | None:
    """Create a new event loop. Returns opaque handle or None."""
    assert _lib is not None
    loop = _lib.__mn_event_loop_new()
    return loop if loop else None


def event_loop_add_fd(loop: int, fd: int, events: int, callback: object, user_data: int = 0) -> int:
    """Register fd with event loop. Returns 0 on success."""
    assert _lib is not None
    return int(_lib.__mn_event_loop_add_fd(loop, fd, events, callback, user_data))


def event_loop_remove_fd(loop: int, fd: int) -> int:
    """Remove fd from event loop. Returns 0 on success."""
    assert _lib is not None
    return int(_lib.__mn_event_loop_remove_fd(loop, fd))


def event_loop_run(loop: int) -> None:
    """Run event loop until no fds or stop called."""
    assert _lib is not None
    _lib.__mn_event_loop_run(loop)


def event_loop_run_once(loop: int, timeout_ms: int = 0) -> int:
    """Run one iteration. Returns events dispatched or -1."""
    assert _lib is not None
    return int(_lib.__mn_event_loop_run_once(loop, timeout_ms))


def event_loop_stop(loop: int) -> None:
    """Signal event loop to stop."""
    assert _lib is not None
    _lib.__mn_event_loop_stop(loop)


def event_loop_free(loop: int) -> None:
    """Free event loop resources."""
    assert _lib is not None
    _lib.__mn_event_loop_free(loop)
