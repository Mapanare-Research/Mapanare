"""Python bridge to the Mapanare native C runtime via ctypes.

Provides Pythonic wrappers around the C agent scheduler, ring buffer,
thread pool, and backpressure APIs for testing and FFI integration.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import platform
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

_NATIVE_DIR = Path(__file__).parent / "native"


def _lib_name() -> str:
    if platform.system() == "Windows":
        return "mapanare_runtime.dll"
    elif platform.system() == "Darwin":
        return "libmapanare_runtime.dylib"
    return "libmapanare_runtime.so"


def _load_lib() -> ctypes.CDLL:
    lib_path = _NATIVE_DIR / _lib_name()
    if not lib_path.exists():
        raise FileNotFoundError(
            f"Native runtime not built: {lib_path}\n" "Run: python runtime/native/build_native.py"
        )
    return ctypes.CDLL(str(lib_path))


try:
    _lib = _load_lib()
    NATIVE_AVAILABLE = True
except (FileNotFoundError, OSError):
    _lib = None  # type: ignore[assignment]
    NATIVE_AVAILABLE = False

# ---------------------------------------------------------------------------
# ctypes struct definitions — must match mapanare_runtime.h layouts
# ---------------------------------------------------------------------------

CACHE_LINE = 64


class RingBuffer(ctypes.Structure):
    _fields_ = [
        ("slots", ctypes.POINTER(ctypes.c_void_p)),
        ("capacity", ctypes.c_uint32),
        ("mask", ctypes.c_uint32),
        ("_pad0", ctypes.c_char * (CACHE_LINE - ctypes.sizeof(ctypes.c_void_p) - 8)),
        ("head", ctypes.c_int64),
        ("_pad1", ctypes.c_char * (CACHE_LINE - 8)),
        ("tail", ctypes.c_int64),
        ("_pad2", ctypes.c_char * (CACHE_LINE - 8)),
    ]


class Backpressure(ctypes.Structure):
    _fields_ = [
        ("pending", ctypes.c_int64),
        ("capacity", ctypes.c_int64),
        ("overloaded", ctypes.c_int32),
    ]


# ---------------------------------------------------------------------------
# Ring buffer API
# ---------------------------------------------------------------------------


class NativeRingBuffer:
    """Python wrapper for the lock-free SPSC ring buffer."""

    def __init__(self, capacity: int = 256) -> None:
        if not NATIVE_AVAILABLE:
            raise RuntimeError("Native runtime not available")
        self._rb = RingBuffer()
        rc = _lib.mapanare_ring_create(ctypes.byref(self._rb), ctypes.c_uint32(capacity))
        if rc != 0:
            raise MemoryError("Failed to create ring buffer")

    def destroy(self) -> None:
        _lib.mapanare_ring_destroy(ctypes.byref(self._rb))

    def push(self, value: int) -> bool:
        """Push a value (as void*). Returns True on success."""
        rc: int = _lib.mapanare_ring_push(ctypes.byref(self._rb), ctypes.c_void_p(value))
        return rc == 0

    def pop(self) -> int | None:
        """Pop a value. Returns None if empty."""
        out = ctypes.c_void_p()
        rc = _lib.mapanare_ring_pop(ctypes.byref(self._rb), ctypes.byref(out))
        if rc != 0:
            return None
        return int(out.value or 0)

    @property
    def size(self) -> int:
        _lib.mapanare_ring_size.restype = ctypes.c_uint32
        return int(_lib.mapanare_ring_size(ctypes.byref(self._rb)))

    @property
    def capacity(self) -> int:
        _lib.mapanare_ring_capacity.restype = ctypes.c_uint32
        return int(_lib.mapanare_ring_capacity(ctypes.byref(self._rb)))

    @property
    def is_full(self) -> bool:
        result: int = _lib.mapanare_ring_is_full(ctypes.byref(self._rb))
        return result != 0

    @property
    def is_empty(self) -> bool:
        result: int = _lib.mapanare_ring_is_empty(ctypes.byref(self._rb))
        return result != 0

    def __del__(self) -> None:
        try:
            self.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Backpressure API
# ---------------------------------------------------------------------------


class NativeBackpressure:
    """Python wrapper for the atomic backpressure counters."""

    def __init__(self, capacity: int) -> None:
        if not NATIVE_AVAILABLE:
            raise RuntimeError("Native runtime not available")
        self._bp = Backpressure()
        _lib.mapanare_bp_init(ctypes.byref(self._bp), ctypes.c_int64(capacity))

    def increment(self) -> None:
        _lib.mapanare_bp_increment(ctypes.byref(self._bp))

    def decrement(self) -> None:
        _lib.mapanare_bp_decrement(ctypes.byref(self._bp))

    @property
    def pending(self) -> int:
        _lib.mapanare_bp_pending.restype = ctypes.c_int64
        return int(_lib.mapanare_bp_pending(ctypes.byref(self._bp)))

    @property
    def is_overloaded(self) -> bool:
        result: int = _lib.mapanare_bp_is_overloaded(ctypes.byref(self._bp))
        return result != 0

    @property
    def pressure(self) -> float:
        _lib.mapanare_bp_pressure.restype = ctypes.c_double
        return float(_lib.mapanare_bp_pressure(ctypes.byref(self._bp)))


# ---------------------------------------------------------------------------
# Thread pool API
# ---------------------------------------------------------------------------

# Callback type for work items
WORK_FN = ctypes.CFUNCTYPE(None, ctypes.c_void_p)


class NativeThreadPool:
    """Python wrapper for the thread pool."""

    def __init__(self, num_threads: int = 0) -> None:
        if not NATIVE_AVAILABLE:
            raise RuntimeError("Native runtime not available")
        # Allocate pool struct as raw bytes (complex struct with platform types)
        # We use the C API directly with an opaque buffer
        self._pool_buf = ctypes.create_string_buffer(4096)  # oversized for safety
        rc = _lib.mapanare_pool_create(self._pool_buf, ctypes.c_uint32(num_threads))
        if rc != 0:
            raise RuntimeError("Failed to create thread pool")

    def destroy(self) -> None:
        _lib.mapanare_pool_destroy(self._pool_buf)

    def submit(self, fn: Any, arg: int = 0) -> bool:
        """Submit a work item. fn must be a WORK_FN ctypes callback."""
        rc: int = _lib.mapanare_pool_submit(self._pool_buf, fn, ctypes.c_void_p(arg))
        return rc == 0

    @property
    def thread_count(self) -> int:
        _lib.mapanare_pool_thread_count.restype = ctypes.c_uint32
        return int(_lib.mapanare_pool_thread_count(self._pool_buf))


# ---------------------------------------------------------------------------
# Agent API
# ---------------------------------------------------------------------------

# Handler callback: int handler(void* agent_data, void* msg, void** out_msg)
HANDLER_FN = ctypes.CFUNCTYPE(
    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
)

# Lifecycle callback: void lifecycle(void* agent_data)
LIFECYCLE_FN = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

# Agent state enum values
AGENT_IDLE = 0
AGENT_RUNNING = 1
AGENT_PAUSED = 2
AGENT_STOPPED = 3
AGENT_FAILED = 4


class NativeAgent:
    """Python wrapper for a native C agent."""

    def __init__(
        self,
        name: str,
        handler: Any,
        agent_data: int = 0,
        inbox_cap: int = 256,
        outbox_cap: int = 256,
    ) -> None:
        if not NATIVE_AVAILABLE:
            raise RuntimeError("Native runtime not available")
        # Oversized buffer for the agent struct
        self._buf = ctypes.create_string_buffer(4096)
        self._handler_ref = handler  # prevent GC
        self._name = name.encode("utf-8")
        rc = _lib.mapanare_agent_init(
            self._buf,
            self._name,
            handler,
            ctypes.c_void_p(agent_data),
            ctypes.c_uint32(inbox_cap),
            ctypes.c_uint32(outbox_cap),
        )
        if rc != 0:
            raise RuntimeError("Failed to init agent")

    def spawn(self) -> None:
        rc = _lib.mapanare_agent_spawn(self._buf)
        if rc != 0:
            raise RuntimeError("Failed to spawn agent")

    def send(self, msg_val: int) -> bool:
        rc: int = _lib.mapanare_agent_send(self._buf, ctypes.c_void_p(msg_val))
        return rc == 0

    def recv(self) -> int | None:
        out = ctypes.c_void_p()
        rc = _lib.mapanare_agent_recv(self._buf, ctypes.byref(out))
        if rc != 0:
            return None
        return int(out.value or 0)

    def pause(self) -> None:
        _lib.mapanare_agent_pause(self._buf)

    def resume(self) -> None:
        _lib.mapanare_agent_resume(self._buf)

    def stop(self) -> None:
        _lib.mapanare_agent_stop(self._buf)

    def destroy(self) -> None:
        _lib.mapanare_agent_destroy(self._buf)

    @property
    def state(self) -> int:
        _lib.mapanare_agent_get_state.restype = ctypes.c_int
        return int(_lib.mapanare_agent_get_state(self._buf))

    @property
    def messages_processed(self) -> int:
        _lib.mapanare_agent_messages_processed.restype = ctypes.c_int64
        return int(_lib.mapanare_agent_messages_processed(self._buf))

    @property
    def avg_latency_us(self) -> float:
        _lib.mapanare_agent_avg_latency_us.restype = ctypes.c_double
        return float(_lib.mapanare_agent_avg_latency_us(self._buf))


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def cpu_count() -> int:
    """Return the number of CPU cores as detected by the native runtime."""
    if not NATIVE_AVAILABLE:
        import os

        return os.cpu_count() or 1
    _lib.mapanare_cpu_count.restype = ctypes.c_uint32
    return int(_lib.mapanare_cpu_count())
