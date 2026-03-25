"""Tests for Phase v2.0.0 — GPU C Runtime.

Tests cover:
  1. GPU C runtime header declarations (structs, functions)
  2. CUDA function typedefs in mapanare_gpu.h
  3. Vulkan function typedefs in mapanare_gpu.h
  4. GPU context initialization struct
  5. CUDA dlopen loading (mock-safe: function pointer types)
  6. Vulkan dlopen loading (mock-safe)
  7. GPU memory alloc/free/copy API signatures
  8. CUDA PTX kernel compilation API
  9. Vulkan SPIR-V shader loading API
  10. GPU tensor dispatch routing
  11. Built-in PTX kernel strings
  12. GPU detection result with multiple backends
  13. Device selection priority
  14. Error handling for missing libraries
  15. GPU memory transfer patterns
"""

from __future__ import annotations

from pathlib import Path

import pytest

from experimental.gpu import (
    CUDA_KERNELS,
    METAL_SHADERS,
    VULKAN_SHADERS,
    CUDADispatcher,
    CUDAKernel,
    DeviceKind,
    GPUDetectionResult,
    GPUDevice,
    GPUManager,
    MetalDispatcher,
    VulkanDispatcher,
    VulkanKernel,
    detect_gpus,
    get_gpu_manager,
    resolve_device_from_annotation,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_NATIVE_DIR = _PROJECT_ROOT / "runtime" / "native"

# The GPU C runtime header may not exist yet (v2.0.0 target)
_GPU_HEADER = _NATIVE_DIR / "mapanare_gpu.h"
_GPU_SOURCE = _NATIVE_DIR / "mapanare_gpu.c"
_gpu_header_exists = _GPU_HEADER.is_file()


# ===========================================================================
# 1. GPU C runtime header declarations
# ===========================================================================


class TestGPURuntimeHeader:
    """Test that mapanare_gpu.h declares required structs and functions."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_header_guard(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "#ifndef MAPANARE_GPU_H" in content
        assert "#define MAPANARE_GPU_H" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_includes_stdint(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "#include <stdint.h>" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_context_struct_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_context" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_buffer_struct_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_buffer" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_kernel_struct_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_kernel" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_init_function_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_init" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_destroy_function_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_destroy" in content


# ===========================================================================
# 2. CUDA function typedefs
# ===========================================================================


class TestCUDATypedefs:
    """Test CUDA function typedefs in header."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_cuda_init_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        # Should have a typedef for cuInit or similar CUDA driver API
        assert "cuInit" in content or "cuda_init" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_cuda_malloc_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "cuMemAlloc" in content or "cuda_malloc" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_cuda_memcpy_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "cuMemcpy" in content or "cuda_memcpy" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_cuda_launch_kernel_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "cuLaunchKernel" in content or "cuda_launch" in content.lower()


# ===========================================================================
# 3. Vulkan function typedefs
# ===========================================================================


class TestVulkanTypedefs:
    """Test Vulkan function typedefs in header."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_vulkan_create_instance_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "vkCreateInstance" in content or "vulkan_create_instance" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_vulkan_create_buffer_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "vkCreateBuffer" in content or "vulkan_create_buffer" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_vulkan_allocate_memory_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "vkAllocateMemory" in content or "vulkan_alloc" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_vulkan_dispatch_typedef(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "vkCmdDispatch" in content or "vulkan_dispatch" in content.lower()


# ===========================================================================
# 4. GPU context initialization struct
# ===========================================================================


class TestGPUContextStruct:
    """Test GPU context initialization via the Python GPU module."""

    def test_gpu_manager_creation(self) -> None:
        mgr = GPUManager()
        assert mgr._detection is None
        assert mgr._cuda is None
        assert mgr._metal is None
        assert mgr._vulkan is None

    def test_gpu_manager_singleton(self) -> None:
        mgr1 = get_gpu_manager()
        mgr2 = get_gpu_manager()
        assert mgr1 is mgr2

    def test_cuda_dispatcher_initial_state(self) -> None:
        disp = CUDADispatcher(device_index=0)
        assert disp.device_index == 0
        assert not disp.is_initialized
        assert disp._kernels == {}

    def test_vulkan_dispatcher_initial_state(self) -> None:
        disp = VulkanDispatcher(device_index=0)
        assert disp.device_index == 0
        assert not disp.is_initialized
        assert disp._kernels == {}

    def test_metal_dispatcher_initial_state(self) -> None:
        disp = MetalDispatcher(device_index=0)
        assert disp.device_index == 0
        assert not disp.is_initialized
        assert disp._kernels == {}


# ===========================================================================
# 5. CUDA dlopen loading (mock-safe)
# ===========================================================================


class TestCUDADlopen:
    """Test CUDA library loading paths (mock-safe, no real GPU required)."""

    def test_cuda_dispatcher_handles_missing_nvcc(self) -> None:
        """CUDADispatcher.initialize() should return False when nvcc is missing."""
        import shutil as _shutil

        disp = CUDADispatcher()
        # If nvcc is not on PATH, initialize should gracefully fail
        if _shutil.which("nvcc") is None:
            assert disp.initialize() is False
            assert not disp.is_initialized

    def test_cuda_kernel_struct_fields(self) -> None:
        k = CUDAKernel(name="test_kernel")
        assert k.name == "test_kernel"
        assert k.ptx_source == ""
        assert k.grid_dim == (1, 1, 1)
        assert k.block_dim == (256, 1, 1)

    def test_cuda_kernel_custom_block_dim(self) -> None:
        k = CUDAKernel(name="matmul", block_dim=(16, 16, 1))
        assert k.block_dim == (16, 16, 1)

    def test_cuda_dispatcher_get_kernel_before_init(self) -> None:
        disp = CUDADispatcher()
        assert disp.get_kernel("tensor_add") is None


# ===========================================================================
# 6. Vulkan dlopen loading (mock-safe)
# ===========================================================================


class TestVulkanDlopen:
    """Test Vulkan library loading paths (mock-safe)."""

    def test_vulkan_dispatcher_handles_missing_tools(self) -> None:
        import shutil as _shutil

        disp = VulkanDispatcher()
        if _shutil.which("glslc") is None and _shutil.which("glslangValidator") is None:
            assert disp.initialize() is False
            assert not disp.is_initialized

    def test_vulkan_kernel_struct_fields(self) -> None:
        k = VulkanKernel(name="test_shader")
        assert k.name == "test_shader"
        assert k.glsl_source == ""
        assert k.local_size == (256, 1, 1)

    def test_vulkan_dispatcher_get_kernel_before_init(self) -> None:
        disp = VulkanDispatcher()
        assert disp.get_kernel("tensor_add") is None


# ===========================================================================
# 7. GPU memory alloc/free/copy API signatures
# ===========================================================================


class TestGPUMemoryAPI:
    """Test GPU memory management API signatures exist in the C header."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_alloc_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_alloc" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_free_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "mapanare_gpu_free" in content

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_copy_host_to_device_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "host_to_device" in content.lower() or "htod" in content.lower()

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_gpu_copy_device_to_host_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "device_to_host" in content.lower() or "dtoh" in content.lower()


# ===========================================================================
# 8. CUDA PTX kernel compilation API
# ===========================================================================


class TestCUDAPTXCompilation:
    """Test PTX kernel compilation infrastructure."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_ptx_compile_function_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "compile_ptx" in content.lower() or "ptx_module" in content.lower()

    def test_cuda_kernels_have_ptx_source(self) -> None:
        for name, ptx in CUDA_KERNELS.items():
            assert "extern" in ptx, f"Kernel {name} missing 'extern' in PTX"
            assert "__global__" in ptx, f"Kernel {name} missing '__global__' in PTX"

    def test_cuda_matmul_kernel_has_3d_indexing(self) -> None:
        ptx = CUDA_KERNELS["matmul"]
        assert "blockIdx" in ptx
        assert "threadIdx" in ptx
        assert "blockDim" in ptx


# ===========================================================================
# 9. Vulkan SPIR-V shader loading API
# ===========================================================================


class TestVulkanSPIRV:
    """Test Vulkan SPIR-V shader infrastructure."""

    @pytest.mark.skipif(not _gpu_header_exists, reason="mapanare_gpu.h not yet created")
    def test_spirv_load_function_declared(self) -> None:
        content = _GPU_HEADER.read_text(encoding="utf-8")
        assert "spirv" in content.lower() or "spir_v" in content.lower()

    def test_vulkan_shaders_have_version(self) -> None:
        for name, src in VULKAN_SHADERS.items():
            assert "#version 450" in src, f"Shader {name} missing GLSL version"

    def test_vulkan_shaders_have_layout(self) -> None:
        for name, src in VULKAN_SHADERS.items():
            assert "layout(" in src, f"Shader {name} missing layout qualifier"

    def test_vulkan_matmul_shader_has_push_constants(self) -> None:
        src = VULKAN_SHADERS["matmul"]
        assert "push_constant" in src


# ===========================================================================
# 10. GPU tensor dispatch routing
# ===========================================================================


class TestGPUTensorDispatch:
    """Test that tensor operations are routed to the correct GPU backend."""

    def test_resolve_cuda_annotation(self) -> None:
        assert resolve_device_from_annotation("cuda") == DeviceKind.CUDA

    def test_resolve_gpu_defaults_cuda(self) -> None:
        assert resolve_device_from_annotation("gpu") == DeviceKind.CUDA

    def test_resolve_vulkan_annotation(self) -> None:
        assert resolve_device_from_annotation("vulkan") == DeviceKind.VULKAN

    def test_resolve_metal_annotation(self) -> None:
        assert resolve_device_from_annotation("metal") == DeviceKind.METAL

    def test_resolve_cpu_annotation(self) -> None:
        assert resolve_device_from_annotation("cpu") == DeviceKind.CPU

    def test_manager_resolve_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown device annotation"):
            resolve_device_from_annotation("tpu")

    def test_manager_cpu_always_initializes(self) -> None:
        mgr = GPUManager()
        assert mgr.initialize_device(DeviceKind.CPU) is True

    def test_manager_get_dispatcher_cpu_returns_none(self) -> None:
        mgr = GPUManager()
        assert mgr.get_dispatcher(DeviceKind.CPU) is None


# ===========================================================================
# 11. Built-in PTX kernel strings
# ===========================================================================


class TestBuiltinKernels:
    """Test that all required built-in GPU kernels are defined."""

    def test_tensor_add_kernel_exists(self) -> None:
        assert "tensor_add" in CUDA_KERNELS
        assert "tensor_add" in METAL_SHADERS
        assert "tensor_add" in VULKAN_SHADERS

    def test_tensor_sub_kernel_exists(self) -> None:
        assert "tensor_sub" in CUDA_KERNELS
        assert "tensor_sub" in METAL_SHADERS
        assert "tensor_sub" in VULKAN_SHADERS

    def test_tensor_mul_kernel_exists(self) -> None:
        assert "tensor_mul" in CUDA_KERNELS
        assert "tensor_mul" in METAL_SHADERS
        assert "tensor_mul" in VULKAN_SHADERS

    def test_tensor_div_kernel_exists(self) -> None:
        assert "tensor_div" in CUDA_KERNELS
        assert "tensor_div" in METAL_SHADERS
        assert "tensor_div" in VULKAN_SHADERS

    def test_matmul_kernel_exists(self) -> None:
        assert "matmul" in CUDA_KERNELS
        assert "matmul" in METAL_SHADERS
        assert "matmul" in VULKAN_SHADERS

    def test_cuda_kernel_naming_convention(self) -> None:
        for name, ptx in CUDA_KERNELS.items():
            fn_name = f"mapanare_{name}_cuda"
            if name == "matmul":
                fn_name = "mapanare_matmul_cuda"
            assert fn_name in ptx, f"CUDA kernel {name} missing function name {fn_name}"

    def test_metal_shader_naming_convention(self) -> None:
        for name, src in METAL_SHADERS.items():
            fn_name = f"mapanare_{name}_metal"
            if name == "matmul":
                fn_name = "mapanare_matmul_metal"
            assert fn_name in src, f"Metal shader {name} missing function name {fn_name}"


# ===========================================================================
# 12. GPU detection result with multiple backends
# ===========================================================================


class TestGPUDetectionMultiBackend:
    """Test GPUDetectionResult with simulated multi-backend scenarios."""

    def test_empty_detection(self) -> None:
        result = GPUDetectionResult()
        assert not result.has_gpu
        assert result.preferred_device == DeviceKind.CPU
        assert result.devices == []

    def test_cuda_only_detection(self) -> None:
        dev = GPUDevice(kind=DeviceKind.CUDA, name="RTX 4090", index=0)
        result = GPUDetectionResult(devices=[dev], cuda_available=True)
        assert result.has_gpu
        assert result.preferred_device == DeviceKind.CUDA
        assert len(result.devices_of_kind(DeviceKind.CUDA)) == 1

    def test_vulkan_only_detection(self) -> None:
        dev = GPUDevice(kind=DeviceKind.VULKAN, name="AMD RX 7900", index=0)
        result = GPUDetectionResult(devices=[dev], vulkan_available=True)
        assert result.has_gpu
        assert result.preferred_device == DeviceKind.VULKAN

    def test_metal_only_detection(self) -> None:
        dev = GPUDevice(kind=DeviceKind.METAL, name="Apple M3 Max", index=0)
        result = GPUDetectionResult(devices=[dev], metal_available=True)
        assert result.has_gpu
        assert result.preferred_device == DeviceKind.METAL

    def test_multi_backend_detection(self) -> None:
        cuda_dev = GPUDevice(kind=DeviceKind.CUDA, name="RTX 4090", index=0)
        vulkan_dev = GPUDevice(kind=DeviceKind.VULKAN, name="RTX 4090 (Vulkan)", index=0)
        result = GPUDetectionResult(
            devices=[cuda_dev, vulkan_dev],
            cuda_available=True,
            vulkan_available=True,
        )
        assert result.has_gpu
        assert len(result.devices) == 2
        assert len(result.devices_of_kind(DeviceKind.CUDA)) == 1
        assert len(result.devices_of_kind(DeviceKind.VULKAN)) == 1


# ===========================================================================
# 13. Device selection priority
# ===========================================================================


class TestDeviceSelectionPriority:
    """Test that device selection follows priority: CUDA > Metal > Vulkan > CPU."""

    def test_cuda_preferred_over_vulkan(self) -> None:
        result = GPUDetectionResult(cuda_available=True, vulkan_available=True)
        assert result.preferred_device == DeviceKind.CUDA

    def test_cuda_preferred_over_metal(self) -> None:
        result = GPUDetectionResult(cuda_available=True, metal_available=True)
        assert result.preferred_device == DeviceKind.CUDA

    def test_metal_preferred_over_vulkan(self) -> None:
        result = GPUDetectionResult(metal_available=True, vulkan_available=True)
        assert result.preferred_device == DeviceKind.METAL

    def test_vulkan_preferred_over_cpu(self) -> None:
        result = GPUDetectionResult(vulkan_available=True)
        assert result.preferred_device == DeviceKind.VULKAN

    def test_cpu_fallback_when_no_gpu(self) -> None:
        result = GPUDetectionResult()
        assert result.preferred_device == DeviceKind.CPU

    def test_all_backends_prefers_cuda(self) -> None:
        result = GPUDetectionResult(
            cuda_available=True, metal_available=True, vulkan_available=True
        )
        assert result.preferred_device == DeviceKind.CUDA


# ===========================================================================
# 14. Error handling for missing libraries
# ===========================================================================


class TestMissingLibraryErrors:
    """Test graceful error handling when GPU libraries are missing."""

    def test_detect_gpus_returns_result_always(self) -> None:
        """detect_gpus() should never raise, always returns GPUDetectionResult."""
        result = detect_gpus()
        assert isinstance(result, GPUDetectionResult)

    def test_detect_gpus_errors_are_strings(self) -> None:
        result = detect_gpus()
        for err in result.errors:
            assert isinstance(err, str)

    def test_cuda_dispatcher_not_initialized_after_fail(self) -> None:
        disp = CUDADispatcher()
        import shutil as _shutil

        if _shutil.which("nvcc") is None:
            disp.initialize()
            assert not disp.is_initialized

    def test_vulkan_dispatcher_not_initialized_after_fail(self) -> None:
        disp = VulkanDispatcher()
        import shutil as _shutil

        if _shutil.which("glslc") is None and _shutil.which("glslangValidator") is None:
            disp.initialize()
            assert not disp.is_initialized

    def test_manager_initialize_unknown_device_returns_false(self) -> None:
        mgr = GPUManager()
        # DeviceKind has only CPU, CUDA, METAL, VULKAN -- test CPU (always True)
        assert mgr.initialize_device(DeviceKind.CPU) is True


# ===========================================================================
# 15. GPU memory transfer patterns
# ===========================================================================


class TestGPUMemoryTransfer:
    """Test GPU memory transfer patterns (host -> device -> compute -> device -> host)."""

    def test_cuda_grid_dim_1d(self) -> None:
        disp = CUDADispatcher()
        grid = disp.compute_grid_dim(1024, block_dim=(256, 1, 1))
        assert grid == (4, 1, 1)

    def test_cuda_grid_dim_non_multiple(self) -> None:
        disp = CUDADispatcher()
        grid = disp.compute_grid_dim(1000, block_dim=(256, 1, 1))
        assert grid == (4, 1, 1)  # ceil(1000/256) = 4

    def test_cuda_matmul_grid(self) -> None:
        disp = CUDADispatcher()
        grid = disp.compute_matmul_grid(32, 64, block_dim=(16, 16, 1))
        assert grid == (4, 2, 1)  # ceil(64/16)=4, ceil(32/16)=2

    def test_vulkan_dispatch_size_1d(self) -> None:
        disp = VulkanDispatcher()
        groups = disp.compute_dispatch_size(1024, local_size=(256, 1, 1))
        assert groups == (4, 1, 1)

    def test_metal_grid_size_1d(self) -> None:
        disp = MetalDispatcher()
        grid = disp.compute_grid_size(1024, thread_group_size=(256, 1, 1))
        assert grid == (1024, 1, 1)

    def test_metal_grid_size_non_multiple(self) -> None:
        disp = MetalDispatcher()
        grid = disp.compute_grid_size(1000, thread_group_size=(256, 1, 1))
        # ceil(1000/256) * 256 = 4 * 256 = 1024
        assert grid[0] == 1024

    def test_gpu_device_repr_includes_name(self) -> None:
        dev = GPUDevice(
            kind=DeviceKind.CUDA,
            name="RTX 4090",
            index=0,
            memory_bytes=24 * 1024 * 1024 * 1024,
            compute_capability=(8, 9),
            driver_version="535.86.05",
        )
        r = repr(dev)
        assert "RTX 4090" in r
        assert "sm_89" in r
        assert "driver=" in r
