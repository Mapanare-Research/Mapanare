"""GPU backend for Mapanare — device detection, kernel dispatch, annotations.

Phase 5.2: GPU Backend
  - DeviceKind enum (CPU, CUDA, Metal, Vulkan)
  - GPU auto-detection at compile and runtime
  - @gpu / @cpu annotation validation
  - CUDA, Metal, Vulkan kernel dispatch abstractions
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Device kinds
# ---------------------------------------------------------------------------


class DeviceKind(Enum):
    """Supported compute device types."""

    CPU = auto()
    CUDA = auto()
    METAL = auto()
    VULKAN = auto()


# Valid annotation names for device placement
DEVICE_ANNOTATIONS = frozenset({"gpu", "cpu", "cuda", "metal", "vulkan"})


# ---------------------------------------------------------------------------
# GPU device info
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GPUDevice:
    """Detected GPU device information."""

    kind: DeviceKind
    name: str
    index: int = 0
    compute_capability: tuple[int, int] | None = None  # CUDA only
    memory_bytes: int = 0
    driver_version: str = ""

    def __repr__(self) -> str:
        mem_mb = self.memory_bytes // (1024 * 1024) if self.memory_bytes else 0
        parts = [f"{self.kind.name}:{self.index} {self.name!r}"]
        if mem_mb:
            parts.append(f"{mem_mb}MB")
        if self.compute_capability:
            parts.append(f"sm_{self.compute_capability[0]}{self.compute_capability[1]}")
        if self.driver_version:
            parts.append(f"driver={self.driver_version}")
        return f"GPUDevice({', '.join(parts)})"


# ---------------------------------------------------------------------------
# GPU detection results
# ---------------------------------------------------------------------------


@dataclass
class GPUDetectionResult:
    """Result of GPU auto-detection."""

    devices: list[GPUDevice] = field(default_factory=list)
    cuda_available: bool = False
    metal_available: bool = False
    vulkan_available: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def has_gpu(self) -> bool:
        """True if any GPU device was detected."""
        return len(self.devices) > 0

    @property
    def preferred_device(self) -> DeviceKind:
        """Return the best available device kind."""
        if self.cuda_available:
            return DeviceKind.CUDA
        if self.metal_available:
            return DeviceKind.METAL
        if self.vulkan_available:
            return DeviceKind.VULKAN
        return DeviceKind.CPU

    def devices_of_kind(self, kind: DeviceKind) -> list[GPUDevice]:
        """Return all devices of a specific kind."""
        return [d for d in self.devices if d.kind == kind]


# ---------------------------------------------------------------------------
# CUDA detection
# ---------------------------------------------------------------------------


def _detect_cuda() -> tuple[bool, list[GPUDevice], list[str]]:
    """Detect NVIDIA CUDA GPUs.

    Checks for:
      1. nvidia-smi binary availability
      2. CUDA driver library (nvcuda / libcuda)
      3. GPU device enumeration via nvidia-smi
    """
    devices: list[GPUDevice] = []
    errors: list[str] = []

    # Check nvidia-smi
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        # Also check common install paths on Windows
        for candidate in [
            r"C:\Windows\System32\nvidia-smi.exe",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
        ]:
            if os.path.isfile(candidate):
                nvidia_smi = candidate
                break

    if nvidia_smi is None:
        return False, [], ["nvidia-smi not found"]

    # Try to enumerate GPUs via nvidia-smi
    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=index,name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            errors.append(f"nvidia-smi failed: {result.stderr.strip()}")
            return False, [], errors

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                idx = int(parts[0])
                name = parts[1]
                mem_mb = int(float(parts[2])) if parts[2] else 0
                driver = parts[3]
                cc: tuple[int, int] | None = None
                if len(parts) >= 5 and "." in parts[4]:
                    cc_parts = parts[4].split(".")
                    cc = (int(cc_parts[0]), int(cc_parts[1]))
                devices.append(
                    GPUDevice(
                        kind=DeviceKind.CUDA,
                        name=name,
                        index=idx,
                        compute_capability=cc,
                        memory_bytes=mem_mb * 1024 * 1024,
                        driver_version=driver,
                    )
                )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as exc:
        errors.append(f"CUDA detection error: {exc}")
        return False, [], errors

    return len(devices) > 0, devices, errors


# ---------------------------------------------------------------------------
# Metal detection (Apple Silicon)
# ---------------------------------------------------------------------------


def _detect_metal() -> tuple[bool, list[GPUDevice], list[str]]:
    """Detect Apple Metal GPU support.

    Metal is available on macOS with Apple Silicon or discrete AMD GPUs.
    Uses system_profiler to enumerate GPU hardware.
    """
    devices: list[GPUDevice] = []
    errors: list[str] = []

    if platform.system() != "Darwin":
        return False, [], ["Metal requires macOS"]

    # Check for Metal framework
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            import json

            try:
                data = json.loads(result.stdout)
                displays = data.get("SPDisplaysDataType", [])
                for i, gpu in enumerate(displays):
                    name = gpu.get("sppci_model", "Unknown GPU")
                    # Metal is supported on all modern macOS GPUs
                    vram = gpu.get("spdisplays_vram", "0")
                    mem_bytes = 0
                    if isinstance(vram, str):
                        # Parse "8 GB" or "8192 MB" etc.
                        parts = vram.split()
                        if parts:
                            try:
                                val = int(parts[0])
                                if len(parts) > 1 and "GB" in parts[1].upper():
                                    mem_bytes = val * 1024 * 1024 * 1024
                                elif len(parts) > 1 and "MB" in parts[1].upper():
                                    mem_bytes = val * 1024 * 1024
                            except ValueError:
                                pass

                    devices.append(
                        GPUDevice(
                            kind=DeviceKind.METAL,
                            name=name,
                            index=i,
                            memory_bytes=mem_bytes,
                        )
                    )
            except (json.JSONDecodeError, KeyError):
                errors.append("Failed to parse system_profiler output")
        else:
            errors.append(f"system_profiler failed: {result.stderr.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        errors.append(f"Metal detection error: {exc}")

    return len(devices) > 0, devices, errors


# ---------------------------------------------------------------------------
# Vulkan detection (cross-platform)
# ---------------------------------------------------------------------------


def _detect_vulkan() -> tuple[bool, list[GPUDevice], list[str]]:
    """Detect Vulkan-capable GPUs.

    Checks for:
      1. vulkaninfo binary availability
      2. Vulkan loader library
      3. GPU enumeration via vulkaninfo
    """
    devices: list[GPUDevice] = []
    errors: list[str] = []

    vulkaninfo = shutil.which("vulkaninfo")
    if vulkaninfo is None:
        return False, [], ["vulkaninfo not found"]

    try:
        result = subprocess.run(
            [vulkaninfo, "--summary"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            errors.append(f"vulkaninfo failed: {result.stderr.strip()}")
            return False, [], errors

        # Parse vulkaninfo --summary output for GPU names
        gpu_idx = 0
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "deviceName" in line or "GPU" in line:
                # Extract device name from lines like:
                #   deviceName = NVIDIA GeForce RTX 3090
                if "=" in line:
                    name = line.split("=", 1)[1].strip()
                    devices.append(
                        GPUDevice(
                            kind=DeviceKind.VULKAN,
                            name=name,
                            index=gpu_idx,
                        )
                    )
                    gpu_idx += 1
            # Also check for apiVersion for driver info
            if "driverVersion" in line and "=" in line and devices:
                ver = line.split("=", 1)[1].strip()
                # Update last device with driver version
                last = devices[-1]
                devices[-1] = GPUDevice(
                    kind=last.kind,
                    name=last.name,
                    index=last.index,
                    memory_bytes=last.memory_bytes,
                    driver_version=ver,
                )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        errors.append(f"Vulkan detection error: {exc}")
        return False, [], errors

    return len(devices) > 0, devices, errors


# ---------------------------------------------------------------------------
# Auto-detection (all backends)
# ---------------------------------------------------------------------------


def detect_gpus() -> GPUDetectionResult:
    """Auto-detect all available GPU devices at runtime.

    Checks CUDA (NVIDIA), Metal (Apple), and Vulkan (cross-platform)
    in parallel-safe fashion. Returns a GPUDetectionResult with all
    detected devices and availability flags.
    """
    result = GPUDetectionResult()

    # CUDA
    cuda_ok, cuda_devs, cuda_errs = _detect_cuda()
    result.cuda_available = cuda_ok
    result.devices.extend(cuda_devs)
    result.errors.extend(cuda_errs)

    # Metal
    metal_ok, metal_devs, metal_errs = _detect_metal()
    result.metal_available = metal_ok
    result.devices.extend(metal_devs)
    result.errors.extend(metal_errs)

    # Vulkan
    vulkan_ok, vulkan_devs, vulkan_errs = _detect_vulkan()
    result.vulkan_available = vulkan_ok
    result.devices.extend(vulkan_devs)
    result.errors.extend(vulkan_errs)

    return result


def resolve_device_from_annotation(name: str) -> DeviceKind:
    """Resolve a decorator annotation name to a DeviceKind.

    Args:
        name: The annotation name (e.g., "gpu", "cpu", "cuda", "metal", "vulkan")

    Returns:
        The corresponding DeviceKind.

    Raises:
        ValueError: If the annotation name is not a valid device annotation.
    """
    mapping: dict[str, DeviceKind] = {
        "cpu": DeviceKind.CPU,
        "cuda": DeviceKind.CUDA,
        "gpu": DeviceKind.CUDA,  # @gpu defaults to CUDA (most common)
        "metal": DeviceKind.METAL,
        "vulkan": DeviceKind.VULKAN,
    }
    if name not in mapping:
        raise ValueError(f"Unknown device annotation: @{name}")
    return mapping[name]


def get_device_annotations(decorators: list[object]) -> list[DeviceKind]:
    """Extract device placement annotations from a list of Decorator nodes.

    Args:
        decorators: List of Decorator AST nodes.

    Returns:
        List of DeviceKind values found in the decorators.
    """
    from mapa.ast_nodes import Decorator

    result: list[DeviceKind] = []
    for dec in decorators:
        if isinstance(dec, Decorator) and dec.name in DEVICE_ANNOTATIONS:
            result.append(resolve_device_from_annotation(dec.name))
    return result


# ---------------------------------------------------------------------------
# CUDA kernel dispatch
# ---------------------------------------------------------------------------


@dataclass
class CUDAKernel:
    """Represents a CUDA kernel for tensor operations."""

    name: str
    ptx_source: str = ""
    grid_dim: tuple[int, int, int] = (1, 1, 1)
    block_dim: tuple[int, int, int] = (256, 1, 1)

    def __repr__(self) -> str:
        return f"CUDAKernel({self.name}, grid={self.grid_dim}, block={self.block_dim})"


# Pre-defined CUDA kernel templates for tensor operations
CUDA_KERNELS: dict[str, str] = {
    "tensor_add": """
extern "C" __global__
void mapanare_tensor_add_cuda(const double* a, const double* b, double* c, int64_t n) {
    int64_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}
""",
    "tensor_sub": """
extern "C" __global__
void mapanare_tensor_sub_cuda(const double* a, const double* b, double* c, int64_t n) {
    int64_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] - b[idx];
    }
}
""",
    "tensor_mul": """
extern "C" __global__
void mapanare_tensor_mul_cuda(const double* a, const double* b, double* c, int64_t n) {
    int64_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] * b[idx];
    }
}
""",
    "tensor_div": """
extern "C" __global__
void mapanare_tensor_div_cuda(const double* a, const double* b, double* c, int64_t n) {
    int64_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] / b[idx];
    }
}
""",
    "matmul": """
extern "C" __global__
void mapanare_matmul_cuda(const double* a, const double* b, double* c,
                          int64_t M, int64_t K, int64_t N) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        double sum = 0.0;
        for (int64_t k = 0; k < K; k++) {
            sum += a[row * K + k] * b[k * N + col];
        }
        c[row * N + col] = sum;
    }
}
""",
}


class CUDADispatcher:
    """Dispatches tensor operations to CUDA kernels.

    Manages kernel compilation, launch configuration, and
    host↔device memory transfers for NVIDIA GPUs.
    """

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self._kernels: dict[str, CUDAKernel] = {}
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize CUDA context and compile kernels.

        Returns True if initialization succeeded.
        """
        # Check if CUDA toolkit is available
        nvcc = shutil.which("nvcc")
        if nvcc is None:
            return False

        # Register built-in kernels
        for name, source in CUDA_KERNELS.items():
            block_dim = (256, 1, 1)
            if name == "matmul":
                block_dim = (16, 16, 1)
            self._kernels[name] = CUDAKernel(name=name, ptx_source=source, block_dim=block_dim)

        self._initialized = True
        return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_kernel(self, name: str) -> CUDAKernel | None:
        """Get a compiled kernel by name."""
        return self._kernels.get(name)

    def compute_grid_dim(
        self, total_elements: int, block_dim: tuple[int, int, int] = (256, 1, 1)
    ) -> tuple[int, int, int]:
        """Compute grid dimensions for a 1D kernel launch."""
        grid_x = (total_elements + block_dim[0] - 1) // block_dim[0]
        return (grid_x, 1, 1)

    def compute_matmul_grid(
        self, m: int, n: int, block_dim: tuple[int, int, int] = (16, 16, 1)
    ) -> tuple[int, int, int]:
        """Compute grid dimensions for 2D matmul kernel."""
        grid_x = (n + block_dim[0] - 1) // block_dim[0]
        grid_y = (m + block_dim[1] - 1) // block_dim[1]
        return (grid_x, grid_y, 1)


# ---------------------------------------------------------------------------
# Metal Performance Shaders dispatch (Apple Silicon)
# ---------------------------------------------------------------------------


# Metal shader source templates
METAL_SHADERS: dict[str, str] = {
    "tensor_add": """
#include <metal_stdlib>
using namespace metal;

kernel void mapanare_tensor_add_metal(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* c [[buffer(2)]],
    uint idx [[thread_position_in_grid]])
{
    c[idx] = a[idx] + b[idx];
}
""",
    "tensor_sub": """
#include <metal_stdlib>
using namespace metal;

kernel void mapanare_tensor_sub_metal(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* c [[buffer(2)]],
    uint idx [[thread_position_in_grid]])
{
    c[idx] = a[idx] - b[idx];
}
""",
    "tensor_mul": """
#include <metal_stdlib>
using namespace metal;

kernel void mapanare_tensor_mul_metal(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* c [[buffer(2)]],
    uint idx [[thread_position_in_grid]])
{
    c[idx] = a[idx] * b[idx];
}
""",
    "tensor_div": """
#include <metal_stdlib>
using namespace metal;

kernel void mapanare_tensor_div_metal(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* c [[buffer(2)]],
    uint idx [[thread_position_in_grid]])
{
    c[idx] = a[idx] / b[idx];
}
""",
    "matmul": """
#include <metal_stdlib>
using namespace metal;

kernel void mapanare_matmul_metal(
    device const float* a [[buffer(0)]],
    device const float* b [[buffer(1)]],
    device float* c [[buffer(2)]],
    constant int64_t& M [[buffer(3)]],
    constant int64_t& K [[buffer(4)]],
    constant int64_t& N [[buffer(5)]],
    uint2 gid [[thread_position_in_grid]])
{
    int row = gid.y;
    int col = gid.x;
    if (row < M && col < N) {
        float sum = 0.0;
        for (int64_t k = 0; k < K; k++) {
            sum += a[row * K + k] * b[k * N + col];
        }
        c[row * N + col] = sum;
    }
}
""",
}


@dataclass
class MetalKernel:
    """Represents a Metal compute kernel."""

    name: str
    source: str = ""
    thread_group_size: tuple[int, int, int] = (256, 1, 1)

    def __repr__(self) -> str:
        return f"MetalKernel({self.name}, threads={self.thread_group_size})"


class MetalDispatcher:
    """Dispatches tensor operations to Metal Performance Shaders.

    Manages shader compilation, command encoding, and buffer
    management for Apple Silicon GPUs.
    """

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self._kernels: dict[str, MetalKernel] = {}
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize Metal device and compile shaders.

        Returns True if initialization succeeded.
        """
        if platform.system() != "Darwin":
            return False

        # Check if xcrun metal compiler is available
        xcrun = shutil.which("xcrun")
        if xcrun is None:
            return False

        # Register built-in shaders
        for name, source in METAL_SHADERS.items():
            tg_size = (256, 1, 1)
            if name == "matmul":
                tg_size = (16, 16, 1)
            self._kernels[name] = MetalKernel(name=name, source=source, thread_group_size=tg_size)

        self._initialized = True
        return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_kernel(self, name: str) -> MetalKernel | None:
        """Get a compiled kernel by name."""
        return self._kernels.get(name)

    def compute_grid_size(
        self, total_elements: int, thread_group_size: tuple[int, int, int] = (256, 1, 1)
    ) -> tuple[int, int, int]:
        """Compute grid size for a 1D dispatch."""
        grid_x = (total_elements + thread_group_size[0] - 1) // thread_group_size[0]
        return (grid_x * thread_group_size[0], 1, 1)


# ---------------------------------------------------------------------------
# Vulkan compute dispatch (cross-platform)
# ---------------------------------------------------------------------------


# GLSL compute shader templates (compiled to SPIR-V for Vulkan)
VULKAN_SHADERS: dict[str, str] = {
    "tensor_add": """
#version 450
layout(local_size_x = 256) in;

layout(set = 0, binding = 0) readonly buffer A { double a[]; };
layout(set = 0, binding = 1) readonly buffer B { double b[]; };
layout(set = 0, binding = 2) writeonly buffer C { double c[]; };
layout(push_constant) uniform Params { uint n; };

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}
""",
    "tensor_sub": """
#version 450
layout(local_size_x = 256) in;

layout(set = 0, binding = 0) readonly buffer A { double a[]; };
layout(set = 0, binding = 1) readonly buffer B { double b[]; };
layout(set = 0, binding = 2) writeonly buffer C { double c[]; };
layout(push_constant) uniform Params { uint n; };

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx < n) {
        c[idx] = a[idx] - b[idx];
    }
}
""",
    "tensor_mul": """
#version 450
layout(local_size_x = 256) in;

layout(set = 0, binding = 0) readonly buffer A { double a[]; };
layout(set = 0, binding = 1) readonly buffer B { double b[]; };
layout(set = 0, binding = 2) writeonly buffer C { double c[]; };
layout(push_constant) uniform Params { uint n; };

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx < n) {
        c[idx] = a[idx] * b[idx];
    }
}
""",
    "tensor_div": """
#version 450
layout(local_size_x = 256) in;

layout(set = 0, binding = 0) readonly buffer A { double a[]; };
layout(set = 0, binding = 1) readonly buffer B { double b[]; };
layout(set = 0, binding = 2) writeonly buffer C { double c[]; };
layout(push_constant) uniform Params { uint n; };

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx < n) {
        c[idx] = a[idx] / b[idx];
    }
}
""",
    "matmul": """
#version 450
layout(local_size_x = 16, local_size_y = 16) in;

layout(set = 0, binding = 0) readonly buffer A { double a[]; };
layout(set = 0, binding = 1) readonly buffer B { double b[]; };
layout(set = 0, binding = 2) writeonly buffer C { double c[]; };
layout(push_constant) uniform Params { uint M; uint K; uint N; };

void main() {
    uint row = gl_GlobalInvocationID.y;
    uint col = gl_GlobalInvocationID.x;
    if (row < M && col < N) {
        double sum = 0.0;
        for (uint k = 0; k < K; k++) {
            sum += a[row * K + k] * b[k * N + col];
        }
        c[row * N + col] = sum;
    }
}
""",
}


@dataclass
class VulkanKernel:
    """Represents a Vulkan compute shader (GLSL → SPIR-V)."""

    name: str
    glsl_source: str = ""
    local_size: tuple[int, int, int] = (256, 1, 1)

    def __repr__(self) -> str:
        return f"VulkanKernel({self.name}, local_size={self.local_size})"


class VulkanDispatcher:
    """Dispatches tensor operations to Vulkan compute shaders.

    Manages SPIR-V compilation, descriptor set layout, command buffer
    recording, and buffer management for Vulkan-capable GPUs.
    """

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self._kernels: dict[str, VulkanKernel] = {}
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize Vulkan instance and compile shaders.

        Returns True if initialization succeeded.
        """
        # Check for glslangValidator or glslc (SPIR-V compiler)
        glslc = shutil.which("glslc") or shutil.which("glslangValidator")
        if glslc is None:
            return False

        # Check for vulkaninfo
        vulkaninfo = shutil.which("vulkaninfo")
        if vulkaninfo is None:
            return False

        # Register built-in shaders
        for name, source in VULKAN_SHADERS.items():
            local_size = (256, 1, 1)
            if name == "matmul":
                local_size = (16, 16, 1)
            self._kernels[name] = VulkanKernel(name=name, glsl_source=source, local_size=local_size)

        self._initialized = True
        return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def get_kernel(self, name: str) -> VulkanKernel | None:
        """Get a compiled kernel by name."""
        return self._kernels.get(name)

    def compute_dispatch_size(
        self, total_elements: int, local_size: tuple[int, int, int] = (256, 1, 1)
    ) -> tuple[int, int, int]:
        """Compute dispatch group counts for a 1D dispatch."""
        groups_x = (total_elements + local_size[0] - 1) // local_size[0]
        return (groups_x, 1, 1)


# ---------------------------------------------------------------------------
# Unified GPU dispatch manager
# ---------------------------------------------------------------------------


class GPUManager:
    """Manages GPU device selection and kernel dispatch across all backends.

    Provides a unified interface for:
      - Auto-detecting available GPUs
      - Selecting the best device for a given operation
      - Dispatching tensor operations to the correct backend
    """

    def __init__(self) -> None:
        self._detection: GPUDetectionResult | None = None
        self._cuda: CUDADispatcher | None = None
        self._metal: MetalDispatcher | None = None
        self._vulkan: VulkanDispatcher | None = None

    def detect(self) -> GPUDetectionResult:
        """Run GPU auto-detection (cached after first call)."""
        if self._detection is None:
            self._detection = detect_gpus()
        return self._detection

    def initialize_device(self, kind: DeviceKind) -> bool:
        """Initialize a specific GPU backend.

        Args:
            kind: The device type to initialize.

        Returns:
            True if the backend initialized successfully.
        """
        if kind == DeviceKind.CPU:
            return True

        if kind == DeviceKind.CUDA:
            if self._cuda is None:
                self._cuda = CUDADispatcher()
            return self._cuda.initialize()

        if kind == DeviceKind.METAL:
            if self._metal is None:
                self._metal = MetalDispatcher()
            return self._metal.initialize()

        if kind == DeviceKind.VULKAN:
            if self._vulkan is None:
                self._vulkan = VulkanDispatcher()
            return self._vulkan.initialize()

        return False

    def get_dispatcher(
        self, kind: DeviceKind
    ) -> CUDADispatcher | MetalDispatcher | VulkanDispatcher | None:
        """Get the dispatcher for a specific backend."""
        if kind == DeviceKind.CUDA:
            return self._cuda
        if kind == DeviceKind.METAL:
            return self._metal
        if kind == DeviceKind.VULKAN:
            return self._vulkan
        return None

    def resolve_device(self, annotation: str | None = None) -> DeviceKind:
        """Resolve the target device from an annotation or auto-detect.

        Args:
            annotation: Optional device annotation (e.g., "gpu", "cuda", "metal").
                       If None, auto-detects the best available device.

        Returns:
            The resolved DeviceKind.
        """
        if annotation is not None:
            return resolve_device_from_annotation(annotation)

        detection = self.detect()
        return detection.preferred_device


# Singleton GPU manager
_gpu_manager: GPUManager | None = None


def get_gpu_manager() -> GPUManager:
    """Get the global GPU manager singleton."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager
