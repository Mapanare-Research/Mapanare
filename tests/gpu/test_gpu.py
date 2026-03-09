"""Tests for Phase 5.2 — GPU Backend.

Tests cover:
  1. @gpu and @cpu annotations (parsing, AST, semantic validation)
  2. GPU auto-detection (DeviceKind, GPUDetectionResult)
  3. CUDA kernel dispatch (CUDADispatcher, kernel templates)
  4. Metal Performance Shaders dispatch (MetalDispatcher, shader templates)
  5. Vulkan compute dispatch (VulkanDispatcher, shader templates)
  6. C runtime GPU declarations (header/source structs and functions)
  7. LLVM emitter GPU dispatch function declarations
  8. GPUManager unified dispatch
"""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import (
    AgentDef,
    Block,
    Decorator,
    FnDef,
    Identifier,
    IntLiteral,
    NamedType,
    Param,
    Program,
    ReturnStmt,
)
from mapanare.gpu import (
    CUDA_KERNELS,
    DEVICE_ANNOTATIONS,
    METAL_SHADERS,
    VULKAN_SHADERS,
    CUDADispatcher,
    CUDAKernel,
    DeviceKind,
    GPUDetectionResult,
    GPUDevice,
    GPUManager,
    MetalDispatcher,
    MetalKernel,
    VulkanDispatcher,
    VulkanKernel,
    detect_gpus,
    get_device_annotations,
    get_gpu_manager,
    resolve_device_from_annotation,
)
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker

# =========================================================================
# Task 5 & 6: @gpu and @cpu annotations
# =========================================================================


class TestDecorator:
    """Test Decorator AST node."""

    def test_decorator_node_fields(self) -> None:
        dec = Decorator(name="gpu")
        assert dec.name == "gpu"
        assert dec.args == []

    def test_decorator_with_args(self) -> None:
        dec = Decorator(name="compute_block_size", args=[IntLiteral(value=16)])
        assert dec.name == "compute_block_size"
        assert len(dec.args) == 1

    def test_fn_def_has_decorators(self) -> None:
        fn = FnDef(name="matmul", decorators=[Decorator(name="gpu")])
        assert len(fn.decorators) == 1
        assert fn.decorators[0].name == "gpu"

    def test_fn_def_no_decorators_default(self) -> None:
        fn = FnDef(name="foo")
        assert fn.decorators == []

    def test_agent_def_has_decorators(self) -> None:
        agent = AgentDef(name="Worker", decorators=[Decorator(name="cpu")])
        assert len(agent.decorators) == 1
        assert agent.decorators[0].name == "cpu"


class TestDecoratorParsing:
    """Test parsing @gpu and @cpu annotations from source."""

    def test_parse_gpu_fn(self) -> None:
        src = """
@gpu
fn matmul(a: Int, b: Int) -> Int {
    return a
}
"""
        prog = parse(src)
        assert len(prog.definitions) == 1
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.name == "matmul"
        assert len(fn.decorators) == 1
        assert fn.decorators[0].name == "gpu"

    def test_parse_cpu_fn(self) -> None:
        src = """
@cpu
fn process(x: Int) -> Int {
    return x
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert len(fn.decorators) == 1
        assert fn.decorators[0].name == "cpu"

    def test_parse_cuda_fn(self) -> None:
        src = """
@cuda
fn kernel(x: Int) -> Int {
    return x
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.decorators[0].name == "cuda"

    def test_parse_metal_fn(self) -> None:
        src = """
@metal
fn shader(x: Int) -> Int {
    return x
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.decorators[0].name == "metal"

    def test_parse_vulkan_fn(self) -> None:
        src = """
@vulkan
fn compute(x: Int) -> Int {
    return x
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.decorators[0].name == "vulkan"

    def test_parse_decorator_with_args(self) -> None:
        src = """
@gpu(16)
fn matmul(a: Int) -> Int {
    return a
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert len(fn.decorators) == 1
        assert fn.decorators[0].name == "gpu"
        assert len(fn.decorators[0].args) == 1

    def test_parse_multiple_decorators(self) -> None:
        src = """
@gpu
@inline
fn matmul(a: Int) -> Int {
    return a
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert len(fn.decorators) == 2
        names = {d.name for d in fn.decorators}
        assert "gpu" in names
        assert "inline" in names

    def test_parse_gpu_agent(self) -> None:
        src = """
@gpu
agent Worker {
    input data: Int
    output result: Int

    fn process(x: Int) -> Int {
        return x
    }
}
"""
        prog = parse(src)
        agent = prog.definitions[0]
        assert isinstance(agent, AgentDef)
        assert len(agent.decorators) == 1
        assert agent.decorators[0].name == "gpu"

    def test_parse_fn_without_decorator(self) -> None:
        src = """
fn add(a: Int, b: Int) -> Int {
    return a + b
}
"""
        prog = parse(src)
        fn = prog.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.decorators == []


class TestDecoratorSemantic:
    """Test semantic validation of @gpu/@cpu annotations."""

    def test_single_device_annotation_ok(self) -> None:
        src = """
@gpu
fn matmul(a: Int) -> Int {
    return a
}
"""
        prog = parse(src)
        checker = SemanticChecker()
        errors = checker.check(prog)
        assert len(errors) == 0

    def test_multiple_device_annotations_error(self) -> None:
        fn = FnDef(
            name="bad",
            params=[Param(name="x", type_annotation=NamedType(name="Int"))],
            return_type=NamedType(name="Int"),
            body=Block(stmts=[ReturnStmt(value=Identifier(name="x"))]),
            decorators=[Decorator(name="gpu"), Decorator(name="cpu")],
        )
        prog = Program(definitions=[fn])
        checker = SemanticChecker()
        errors = checker.check(prog)
        assert any("Multiple device annotations" in e.message for e in errors)

    def test_cpu_annotation_ok(self) -> None:
        src = """
@cpu
fn process(x: Int) -> Int {
    return x
}
"""
        prog = parse(src)
        checker = SemanticChecker()
        errors = checker.check(prog)
        assert len(errors) == 0

    def test_non_device_decorator_ok(self) -> None:
        src = """
@inline
fn add(a: Int, b: Int) -> Int {
    return a + b
}
"""
        prog = parse(src)
        checker = SemanticChecker()
        errors = checker.check(prog)
        assert len(errors) == 0


# =========================================================================
# Task 4: Auto-detect GPU at compile and runtime
# =========================================================================


class TestDeviceKind:
    """Test DeviceKind enum."""

    def test_device_kinds_exist(self) -> None:
        assert DeviceKind.CPU is not None
        assert DeviceKind.CUDA is not None
        assert DeviceKind.METAL is not None
        assert DeviceKind.VULKAN is not None

    def test_device_kind_values_unique(self) -> None:
        values = {dk.value for dk in DeviceKind}
        assert len(values) == 4

    def test_device_annotations_set(self) -> None:
        assert "gpu" in DEVICE_ANNOTATIONS
        assert "cpu" in DEVICE_ANNOTATIONS
        assert "cuda" in DEVICE_ANNOTATIONS
        assert "metal" in DEVICE_ANNOTATIONS
        assert "vulkan" in DEVICE_ANNOTATIONS


class TestGPUDevice:
    """Test GPUDevice dataclass."""

    def test_gpu_device_creation(self) -> None:
        dev = GPUDevice(kind=DeviceKind.CUDA, name="RTX 3090", index=0)
        assert dev.kind == DeviceKind.CUDA
        assert dev.name == "RTX 3090"
        assert dev.index == 0
        assert dev.memory_bytes == 0

    def test_gpu_device_with_memory(self) -> None:
        dev = GPUDevice(
            kind=DeviceKind.CUDA,
            name="RTX 4090",
            index=0,
            memory_bytes=24 * 1024 * 1024 * 1024,
            compute_capability=(8, 9),
            driver_version="535.104",
        )
        assert dev.memory_bytes == 24 * 1024 * 1024 * 1024
        assert dev.compute_capability == (8, 9)
        assert dev.driver_version == "535.104"

    def test_gpu_device_repr(self) -> None:
        dev = GPUDevice(kind=DeviceKind.CUDA, name="RTX 3090", index=0)
        r = repr(dev)
        assert "CUDA" in r
        assert "RTX 3090" in r

    def test_gpu_device_repr_with_cc(self) -> None:
        dev = GPUDevice(
            kind=DeviceKind.CUDA,
            name="A100",
            index=0,
            compute_capability=(8, 0),
            memory_bytes=40 * 1024 * 1024 * 1024,
        )
        r = repr(dev)
        assert "sm_80" in r

    def test_metal_device(self) -> None:
        dev = GPUDevice(kind=DeviceKind.METAL, name="Apple M1 Pro", index=0)
        assert dev.kind == DeviceKind.METAL

    def test_vulkan_device(self) -> None:
        dev = GPUDevice(
            kind=DeviceKind.VULKAN,
            name="AMD Radeon RX 6800",
            index=0,
            driver_version="23.3.1",
        )
        assert dev.kind == DeviceKind.VULKAN
        assert dev.driver_version == "23.3.1"


class TestGPUDetectionResult:
    """Test GPUDetectionResult."""

    def test_empty_detection(self) -> None:
        result = GPUDetectionResult()
        assert not result.has_gpu
        assert result.preferred_device == DeviceKind.CPU
        assert result.devices == []

    def test_cuda_detection(self) -> None:
        result = GPUDetectionResult(
            devices=[GPUDevice(kind=DeviceKind.CUDA, name="RTX 3090", index=0)],
            cuda_available=True,
        )
        assert result.has_gpu
        assert result.cuda_available
        assert result.preferred_device == DeviceKind.CUDA

    def test_metal_detection(self) -> None:
        result = GPUDetectionResult(
            devices=[GPUDevice(kind=DeviceKind.METAL, name="M1", index=0)],
            metal_available=True,
        )
        assert result.has_gpu
        assert result.preferred_device == DeviceKind.METAL

    def test_vulkan_detection(self) -> None:
        result = GPUDetectionResult(
            devices=[GPUDevice(kind=DeviceKind.VULKAN, name="GTX 1080", index=0)],
            vulkan_available=True,
        )
        assert result.has_gpu
        assert result.preferred_device == DeviceKind.VULKAN

    def test_preferred_device_priority(self) -> None:
        """CUDA > Metal > Vulkan > CPU."""
        result = GPUDetectionResult(
            cuda_available=True,
            metal_available=True,
            vulkan_available=True,
        )
        assert result.preferred_device == DeviceKind.CUDA

    def test_devices_of_kind(self) -> None:
        result = GPUDetectionResult(
            devices=[
                GPUDevice(kind=DeviceKind.CUDA, name="GPU0", index=0),
                GPUDevice(kind=DeviceKind.CUDA, name="GPU1", index=1),
                GPUDevice(kind=DeviceKind.VULKAN, name="VKGPU", index=0),
            ]
        )
        cuda = result.devices_of_kind(DeviceKind.CUDA)
        assert len(cuda) == 2
        vulkan = result.devices_of_kind(DeviceKind.VULKAN)
        assert len(vulkan) == 1

    def test_detection_errors(self) -> None:
        result = GPUDetectionResult(errors=["nvidia-smi not found"])
        assert len(result.errors) == 1

    def test_detect_gpus_returns_result(self) -> None:
        """detect_gpus() should always return a valid result (even if no GPUs)."""
        result = detect_gpus()
        assert isinstance(result, GPUDetectionResult)
        # preferred_device should always be valid
        assert result.preferred_device in (
            DeviceKind.CPU,
            DeviceKind.CUDA,
            DeviceKind.METAL,
            DeviceKind.VULKAN,
        )


class TestResolveDeviceAnnotation:
    """Test resolve_device_from_annotation."""

    def test_cpu(self) -> None:
        assert resolve_device_from_annotation("cpu") == DeviceKind.CPU

    def test_gpu(self) -> None:
        assert resolve_device_from_annotation("gpu") == DeviceKind.CUDA

    def test_cuda(self) -> None:
        assert resolve_device_from_annotation("cuda") == DeviceKind.CUDA

    def test_metal(self) -> None:
        assert resolve_device_from_annotation("metal") == DeviceKind.METAL

    def test_vulkan(self) -> None:
        assert resolve_device_from_annotation("vulkan") == DeviceKind.VULKAN

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown device annotation"):
            resolve_device_from_annotation("tpu")


class TestGetDeviceAnnotations:
    """Test get_device_annotations helper."""

    def test_no_decorators(self) -> None:
        assert get_device_annotations([]) == []

    def test_gpu_decorator(self) -> None:
        devices = get_device_annotations([Decorator(name="gpu")])
        assert devices == [DeviceKind.CUDA]

    def test_cpu_decorator(self) -> None:
        devices = get_device_annotations([Decorator(name="cpu")])
        assert devices == [DeviceKind.CPU]

    def test_non_device_decorator(self) -> None:
        devices = get_device_annotations([Decorator(name="inline")])
        assert devices == []

    def test_mixed_decorators(self) -> None:
        devices = get_device_annotations(
            [
                Decorator(name="inline"),
                Decorator(name="gpu"),
            ]
        )
        assert devices == [DeviceKind.CUDA]


# =========================================================================
# Task 1: CUDA kernel dispatch (NVIDIA)
# =========================================================================


class TestCUDAKernel:
    """Test CUDA kernel templates and dispatcher."""

    def test_cuda_kernel_dataclass(self) -> None:
        k = CUDAKernel(name="tensor_add")
        assert k.name == "tensor_add"
        assert k.grid_dim == (1, 1, 1)
        assert k.block_dim == (256, 1, 1)

    def test_cuda_kernel_repr(self) -> None:
        k = CUDAKernel(name="matmul", block_dim=(16, 16, 1))
        r = repr(k)
        assert "matmul" in r
        assert "(16, 16, 1)" in r

    def test_cuda_kernel_templates_exist(self) -> None:
        assert "tensor_add" in CUDA_KERNELS
        assert "tensor_sub" in CUDA_KERNELS
        assert "tensor_mul" in CUDA_KERNELS
        assert "tensor_div" in CUDA_KERNELS
        assert "matmul" in CUDA_KERNELS

    def test_cuda_kernel_add_source(self) -> None:
        src = CUDA_KERNELS["tensor_add"]
        assert "__global__" in src
        assert "mapanare_tensor_add_cuda" in src
        assert "a[idx] + b[idx]" in src

    def test_cuda_kernel_matmul_source(self) -> None:
        src = CUDA_KERNELS["matmul"]
        assert "__global__" in src
        assert "mapanare_matmul_cuda" in src
        assert "blockIdx" in src
        assert "threadIdx" in src

    def test_cuda_dispatcher_creation(self) -> None:
        d = CUDADispatcher(device_index=0)
        assert d.device_index == 0
        assert not d.is_initialized

    def test_cuda_dispatcher_compute_grid_dim(self) -> None:
        d = CUDADispatcher()
        grid = d.compute_grid_dim(1024, block_dim=(256, 1, 1))
        assert grid == (4, 1, 1)

    def test_cuda_dispatcher_compute_grid_dim_non_divisible(self) -> None:
        d = CUDADispatcher()
        grid = d.compute_grid_dim(1000, block_dim=(256, 1, 1))
        assert grid == (4, 1, 1)  # ceil(1000/256) = 4

    def test_cuda_dispatcher_compute_matmul_grid(self) -> None:
        d = CUDADispatcher()
        grid = d.compute_matmul_grid(64, 64, block_dim=(16, 16, 1))
        assert grid == (4, 4, 1)

    def test_cuda_dispatcher_compute_matmul_grid_non_divisible(self) -> None:
        d = CUDADispatcher()
        grid = d.compute_matmul_grid(100, 100, block_dim=(16, 16, 1))
        assert grid == (7, 7, 1)  # ceil(100/16) = 7


# =========================================================================
# Task 2: Metal Performance Shaders (Apple Silicon)
# =========================================================================


class TestMetalKernel:
    """Test Metal shader templates and dispatcher."""

    def test_metal_kernel_dataclass(self) -> None:
        k = MetalKernel(name="tensor_add")
        assert k.name == "tensor_add"
        assert k.thread_group_size == (256, 1, 1)

    def test_metal_kernel_repr(self) -> None:
        k = MetalKernel(name="matmul", thread_group_size=(16, 16, 1))
        r = repr(k)
        assert "matmul" in r
        assert "(16, 16, 1)" in r

    def test_metal_shader_templates_exist(self) -> None:
        assert "tensor_add" in METAL_SHADERS
        assert "tensor_sub" in METAL_SHADERS
        assert "tensor_mul" in METAL_SHADERS
        assert "tensor_div" in METAL_SHADERS
        assert "matmul" in METAL_SHADERS

    def test_metal_shader_add_source(self) -> None:
        src = METAL_SHADERS["tensor_add"]
        assert "metal_stdlib" in src
        assert "mapanare_tensor_add_metal" in src
        assert "thread_position_in_grid" in src

    def test_metal_shader_matmul_source(self) -> None:
        src = METAL_SHADERS["matmul"]
        assert "mapanare_matmul_metal" in src
        assert "gid" in src

    def test_metal_dispatcher_creation(self) -> None:
        d = MetalDispatcher(device_index=0)
        assert d.device_index == 0
        assert not d.is_initialized

    def test_metal_dispatcher_compute_grid_size(self) -> None:
        d = MetalDispatcher()
        grid = d.compute_grid_size(1024, thread_group_size=(256, 1, 1))
        assert grid == (1024, 1, 1)

    def test_metal_dispatcher_compute_grid_size_non_divisible(self) -> None:
        d = MetalDispatcher()
        grid = d.compute_grid_size(1000, thread_group_size=(256, 1, 1))
        # Rounds up to next multiple: ceil(1000/256)*256 = 4*256 = 1024
        assert grid == (1024, 1, 1)


# =========================================================================
# Task 3: Vulkan compute (cross-platform)
# =========================================================================


class TestVulkanKernel:
    """Test Vulkan compute shader templates and dispatcher."""

    def test_vulkan_kernel_dataclass(self) -> None:
        k = VulkanKernel(name="tensor_add")
        assert k.name == "tensor_add"
        assert k.local_size == (256, 1, 1)

    def test_vulkan_kernel_repr(self) -> None:
        k = VulkanKernel(name="matmul", local_size=(16, 16, 1))
        r = repr(k)
        assert "matmul" in r
        assert "(16, 16, 1)" in r

    def test_vulkan_shader_templates_exist(self) -> None:
        assert "tensor_add" in VULKAN_SHADERS
        assert "tensor_sub" in VULKAN_SHADERS
        assert "tensor_mul" in VULKAN_SHADERS
        assert "tensor_div" in VULKAN_SHADERS
        assert "matmul" in VULKAN_SHADERS

    def test_vulkan_shader_add_source(self) -> None:
        src = VULKAN_SHADERS["tensor_add"]
        assert "#version 450" in src
        assert "gl_GlobalInvocationID" in src
        assert "a[idx] + b[idx]" in src

    def test_vulkan_shader_matmul_source(self) -> None:
        src = VULKAN_SHADERS["matmul"]
        assert "#version 450" in src
        assert "local_size_x = 16" in src
        assert "local_size_y = 16" in src

    def test_vulkan_dispatcher_creation(self) -> None:
        d = VulkanDispatcher(device_index=0)
        assert d.device_index == 0
        assert not d.is_initialized

    def test_vulkan_dispatcher_compute_dispatch_size(self) -> None:
        d = VulkanDispatcher()
        groups = d.compute_dispatch_size(1024, local_size=(256, 1, 1))
        assert groups == (4, 1, 1)

    def test_vulkan_dispatcher_compute_dispatch_size_non_divisible(self) -> None:
        d = VulkanDispatcher()
        groups = d.compute_dispatch_size(1000, local_size=(256, 1, 1))
        assert groups == (4, 1, 1)  # ceil(1000/256) = 4


# =========================================================================
# GPUManager unified dispatch
# =========================================================================


class TestGPUManager:
    """Test unified GPU manager."""

    def test_manager_creation(self) -> None:
        mgr = GPUManager()
        assert mgr._detection is None

    def test_manager_detect(self) -> None:
        mgr = GPUManager()
        result = mgr.detect()
        assert isinstance(result, GPUDetectionResult)
        # Second call returns cached result
        result2 = mgr.detect()
        assert result is result2

    def test_manager_resolve_cpu(self) -> None:
        mgr = GPUManager()
        assert mgr.resolve_device("cpu") == DeviceKind.CPU

    def test_manager_resolve_gpu(self) -> None:
        mgr = GPUManager()
        assert mgr.resolve_device("gpu") == DeviceKind.CUDA

    def test_manager_resolve_auto(self) -> None:
        mgr = GPUManager()
        device = mgr.resolve_device(None)
        assert device in (DeviceKind.CPU, DeviceKind.CUDA, DeviceKind.METAL, DeviceKind.VULKAN)

    def test_manager_initialize_cpu(self) -> None:
        mgr = GPUManager()
        assert mgr.initialize_device(DeviceKind.CPU)

    def test_get_gpu_manager_singleton(self) -> None:
        m1 = get_gpu_manager()
        m2 = get_gpu_manager()
        assert m1 is m2

    def test_manager_get_dispatcher_cpu(self) -> None:
        mgr = GPUManager()
        assert mgr.get_dispatcher(DeviceKind.CPU) is None


# =========================================================================
# LLVM emitter: GPU dispatch declarations
# =========================================================================


class TestLLVMGPUDispatch:
    """Test LLVM emitter declares GPU dispatch runtime functions."""

    def test_declare_tensor_add_dispatch(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_add_dispatch")
        assert fn is not None
        assert fn.name == "__mapanare_tensor_add_dispatch"
        # Should take 3 args: tensor*, tensor*, device_kind
        assert len(fn.args) == 3

    def test_declare_tensor_sub_dispatch(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_sub_dispatch")
        assert fn is not None
        assert len(fn.args) == 3

    def test_declare_tensor_mul_dispatch(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_mul_dispatch")
        assert fn is not None

    def test_declare_tensor_div_dispatch(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_div_dispatch")
        assert fn is not None

    def test_declare_matmul_dispatch(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_tensor_matmul_dispatch")
        assert fn is not None
        assert len(fn.args) == 3

    def test_declare_detect_gpus(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn = emitter._declare_tensor_runtime("__mapanare_detect_gpus")
        assert fn is not None
        assert len(fn.args) == 0

    def test_cached_declaration(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        fn1 = emitter._declare_tensor_runtime("__mapanare_tensor_add_dispatch")
        fn2 = emitter._declare_tensor_runtime("__mapanare_tensor_add_dispatch")
        assert fn1 is fn2


# =========================================================================
# C runtime: GPU declarations verification
# =========================================================================


class TestCRuntimeGPU:
    """Verify C runtime header has GPU structs and functions."""

    def _read_header(self) -> str:
        import os

        hdr = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "runtime",
            "native",
            "mapanare_runtime.h",
        )
        with open(hdr, encoding="utf-8") as f:
            return f.read()

    def test_device_kind_enum(self) -> None:
        h = self._read_header()
        assert "MAPANARE_DEVICE_CPU" in h
        assert "MAPANARE_DEVICE_CUDA" in h
        assert "MAPANARE_DEVICE_METAL" in h
        assert "MAPANARE_DEVICE_VULKAN" in h

    def test_gpu_device_struct(self) -> None:
        h = self._read_header()
        assert "mapanare_gpu_device" in h
        assert "mapanare_gpu_device_t" in h

    def test_gpu_detection_struct(self) -> None:
        h = self._read_header()
        assert "mapanare_gpu_detection" in h
        assert "cuda_available" in h
        assert "metal_available" in h
        assert "vulkan_available" in h

    def test_detect_gpus_function(self) -> None:
        h = self._read_header()
        assert "mapanare_detect_gpus" in h

    def test_dispatch_functions(self) -> None:
        h = self._read_header()
        assert "mapanare_tensor_add_dispatch" in h
        assert "mapanare_tensor_sub_dispatch" in h
        assert "mapanare_tensor_mul_dispatch" in h
        assert "mapanare_tensor_div_dispatch" in h
        assert "mapanare_tensor_matmul_dispatch" in h

    def _read_source(self) -> str:
        import os

        src = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "runtime",
            "native",
            "mapanare_runtime.c",
        )
        with open(src, encoding="utf-8") as f:
            return f.read()

    def test_dispatch_implementations(self) -> None:
        c = self._read_source()
        assert "mapanare_tensor_add_dispatch" in c
        assert "mapanare_tensor_matmul_dispatch" in c
        assert "mapanare_detect_gpus" in c
        assert "mapanare_gpu_detection_free" in c

    def test_gpu_detection_implementation(self) -> None:
        c = self._read_source()
        # Should check for CUDA, Metal, Vulkan
        assert "cuda_available" in c
        assert "metal_available" in c
        assert "vulkan_available" in c
