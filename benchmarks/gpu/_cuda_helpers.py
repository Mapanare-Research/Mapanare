"""CUDA Driver API helpers for GPU benchmarks.

Loads nvcuda.dll (Windows) or libcuda.so (Linux) at runtime via ctypes
and exposes thin wrappers around the CUDA Driver API for:
  - Context creation
  - Device memory alloc/free
  - Host<->device transfers
  - PTX module loading and kernel launch

This mirrors what mapanare_gpu.h does in C, but from pure Python so the
benchmarks can run without compiling the Mapanare C runtime.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import platform
import sys
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# CUDA Driver API types
# ---------------------------------------------------------------------------

CUresult = ctypes.c_int
CUdevice = ctypes.c_int
CUcontext = ctypes.c_void_p
CUmodule = ctypes.c_void_p
CUfunction = ctypes.c_void_p
CUdeviceptr = ctypes.c_uint64
CUstream = ctypes.c_void_p

CUDA_SUCCESS = 0


# ---------------------------------------------------------------------------
# Library loading
# ---------------------------------------------------------------------------

_cuda_lib: ctypes.CDLL | None = None


def _load_cuda_driver() -> ctypes.CDLL | None:
    """Try to load the CUDA driver library."""
    global _cuda_lib
    if _cuda_lib is not None:
        return _cuda_lib

    candidates: list[str] = []
    if platform.system() == "Windows":
        candidates = ["nvcuda.dll", "nvcuda"]
    else:
        candidates = ["libcuda.so.1", "libcuda.so", "cuda"]

    for name in candidates:
        try:
            _cuda_lib = ctypes.CDLL(name)
            return _cuda_lib
        except OSError:
            continue

    # Try ctypes.util as fallback
    path = ctypes.util.find_library("cuda")
    if path:
        try:
            _cuda_lib = ctypes.CDLL(path)
            return _cuda_lib
        except OSError:
            pass

    return None


# ---------------------------------------------------------------------------
# CUDA context management
# ---------------------------------------------------------------------------

@dataclass
class CUDAContext:
    """Holds an initialized CUDA driver context."""

    lib: ctypes.CDLL
    device: int
    context: ctypes.c_void_p
    device_name: str
    total_mem: int  # bytes
    compute_cap: tuple[int, int]

    def __repr__(self) -> str:
        mem_gb = self.total_mem / (1024**3)
        return (
            f"CUDAContext(device={self.device}, name={self.device_name!r}, "
            f"mem={mem_gb:.1f}GB, sm_{self.compute_cap[0]}{self.compute_cap[1]})"
        )


def cuda_init() -> CUDAContext | None:
    """Initialize the CUDA driver and create a context on device 0.

    Returns None if CUDA is not available.
    """
    lib = _load_cuda_driver()
    if lib is None:
        return None

    # cuInit
    try:
        rc = lib.cuInit(ctypes.c_uint(0))
        if rc != CUDA_SUCCESS:
            return None
    except (OSError, AttributeError):
        return None

    # Device count
    count = ctypes.c_int(0)
    rc = lib.cuDeviceGetCount(ctypes.byref(count))
    if rc != CUDA_SUCCESS or count.value == 0:
        return None

    # Get device 0
    dev = CUdevice(0)
    rc = lib.cuDeviceGet(ctypes.byref(dev), 0)
    if rc != CUDA_SUCCESS:
        return None

    # Device name
    name_buf = ctypes.create_string_buffer(256)
    lib.cuDeviceGetName(name_buf, 256, dev)
    device_name = name_buf.value.decode("utf-8", errors="replace")

    # Total memory
    total_mem = ctypes.c_size_t(0)
    lib.cuDeviceTotalMem_v2(ctypes.byref(total_mem), dev)

    # Compute capability
    major = ctypes.c_int(0)
    minor = ctypes.c_int(0)
    # CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR = 75
    # CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR = 76
    lib.cuDeviceGetAttribute(ctypes.byref(major), 75, dev)
    lib.cuDeviceGetAttribute(ctypes.byref(minor), 76, dev)

    # Create context
    ctx = CUcontext()
    rc = lib.cuCtxCreate_v2(ctypes.byref(ctx), 0, dev)
    if rc != CUDA_SUCCESS:
        return None

    return CUDAContext(
        lib=lib,
        device=dev.value,
        context=ctx,
        device_name=device_name,
        total_mem=total_mem.value,
        compute_cap=(major.value, minor.value),
    )


def cuda_shutdown(ctx: CUDAContext) -> None:
    """Destroy the CUDA context."""
    try:
        ctx.lib.cuCtxDestroy_v2(ctx.context)
    except (OSError, AttributeError):
        pass


# ---------------------------------------------------------------------------
# Device memory management
# ---------------------------------------------------------------------------


def cuda_malloc(ctx: CUDAContext, size_bytes: int) -> CUdeviceptr:
    """Allocate device memory. Returns a CUdeviceptr (uint64)."""
    dptr = CUdeviceptr(0)
    rc = ctx.lib.cuMemAlloc_v2(ctypes.byref(dptr), ctypes.c_size_t(size_bytes))
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuMemAlloc_v2 failed: {rc}")
    return dptr


def cuda_free(ctx: CUDAContext, dptr: CUdeviceptr) -> None:
    """Free device memory."""
    ctx.lib.cuMemFree_v2(dptr)


def cuda_memcpy_htod(ctx: CUDAContext, dst: CUdeviceptr, src: ctypes.c_void_p, size: int) -> None:
    """Copy host -> device."""
    rc = ctx.lib.cuMemcpyHtoD_v2(dst, src, ctypes.c_size_t(size))
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuMemcpyHtoD_v2 failed: {rc}")


def cuda_memcpy_dtoh(ctx: CUDAContext, dst: ctypes.c_void_p, src: CUdeviceptr, size: int) -> None:
    """Copy device -> host."""
    rc = ctx.lib.cuMemcpyDtoH_v2(dst, src, ctypes.c_size_t(size))
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuMemcpyDtoH_v2 failed: {rc}")


def cuda_synchronize(ctx: CUDAContext) -> None:
    """Synchronize the current CUDA context."""
    rc = ctx.lib.cuCtxSynchronize()
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuCtxSynchronize failed: {rc}")


# ---------------------------------------------------------------------------
# PTX kernel loading and launch
# ---------------------------------------------------------------------------


def cuda_load_module(ctx: CUDAContext, ptx_source: str) -> CUmodule:
    """Load a PTX module from source string."""
    mod = CUmodule()
    ptx_bytes = ptx_source.encode("utf-8") + b"\x00"
    rc = ctx.lib.cuModuleLoadDataEx(
        ctypes.byref(mod),
        ptx_bytes,
        ctypes.c_uint(0),
        None,
        None,
    )
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuModuleLoadDataEx failed: {rc}")
    return mod


def cuda_get_function(ctx: CUDAContext, module: CUmodule, name: str) -> CUfunction:
    """Get a kernel function from a loaded module."""
    func = CUfunction()
    rc = ctx.lib.cuModuleGetFunction(
        ctypes.byref(func), module, name.encode("utf-8")
    )
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuModuleGetFunction failed: {rc}")
    return func


def cuda_launch_kernel(
    ctx: CUDAContext,
    func: CUfunction,
    grid: tuple[int, int, int],
    block: tuple[int, int, int],
    params: list[ctypes.c_void_p],
    shared_mem: int = 0,
) -> None:
    """Launch a CUDA kernel with the given grid/block dimensions and parameters."""
    # Build the params array (array of void pointers to each argument)
    param_array = (ctypes.c_void_p * len(params))(*params)

    rc = ctx.lib.cuLaunchKernel(
        func,
        ctypes.c_uint(grid[0]),
        ctypes.c_uint(grid[1]),
        ctypes.c_uint(grid[2]),
        ctypes.c_uint(block[0]),
        ctypes.c_uint(block[1]),
        ctypes.c_uint(block[2]),
        ctypes.c_uint(shared_mem),
        CUstream(0),  # default stream
        param_array,
        None,
    )
    if rc != CUDA_SUCCESS:
        raise RuntimeError(f"cuLaunchKernel failed: {rc}")
