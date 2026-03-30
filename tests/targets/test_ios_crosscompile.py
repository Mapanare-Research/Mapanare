"""
iOS cross-compilation tests — verify Mach-O output, symbol visibility,
and end-to-end compilation from .mn source to arm64 iOS object files.

Requires macOS with Xcode and iOS SDK installed.
"""

import os
import platform
import shutil
import subprocess
import tempfile

import pytest

from mapanare.targets import TARGETS

# Skip entire module on non-macOS platforms
pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="iOS cross-compilation requires macOS with Xcode",
)

HAS_LLVMLITE = False
try:
    import llvmlite  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    pass


def _ios_sdk_path() -> str | None:
    """Return the iOS SDK path or None if unavailable."""
    try:
        result = subprocess.run(
            ["xcrun", "--sdk", "iphoneos", "--show-sdk-path"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


IOS_SDK = _ios_sdk_path()
HAS_IOS_SDK = IOS_SDK is not None

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "runtime", "native")
GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "golden")


# =========================================================================
# 1. C Runtime cross-compilation to iOS
# =========================================================================


@pytest.mark.skipif(not HAS_IOS_SDK, reason="iOS SDK not found")
class TestCRuntimeIOSCrossCompile:
    """Cross-compile the C runtime to iOS and verify Mach-O output."""

    def _compile_ios(self, source: str, output: str) -> subprocess.CompletedProcess:
        """Compile a C source file for iOS ARM64."""
        return subprocess.run(
            [
                "xcrun",
                "--sdk",
                "iphoneos",
                "clang",
                "-c",
                "-std=c11",
                "-O2",
                "-Wall",
                "-target",
                "arm64-apple-ios17.0",
                "-isysroot",
                IOS_SDK,
                source,
                "-o",
                output,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=RUNTIME_DIR,
        )

    def test_core_compiles(self, tmp_path: object) -> None:
        out = os.path.join(str(tmp_path), "core.o")
        result = self._compile_ios("mapanare_core.c", out)
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out)

    def test_runtime_compiles(self, tmp_path: object) -> None:
        out = os.path.join(str(tmp_path), "runtime.o")
        result = self._compile_ios("mapanare_runtime.c", out)
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out)

    def test_io_compiles(self, tmp_path: object) -> None:
        out = os.path.join(str(tmp_path), "io.o")
        result = self._compile_ios("mapanare_io.c", out)
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out)

    def test_gpu_compiles(self, tmp_path: object) -> None:
        out = os.path.join(str(tmp_path), "gpu.o")
        result = self._compile_ios("mapanare_gpu.c", out)
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out)

    def test_macho_format(self, tmp_path: object) -> None:
        """Verify compiled objects are Mach-O arm64."""
        out = os.path.join(str(tmp_path), "core.o")
        self._compile_ios("mapanare_core.c", out)
        result = subprocess.run(["file", out], capture_output=True, text=True, timeout=5)
        assert "Mach-O 64-bit object arm64" in result.stdout

    def test_architecture_arm64(self, tmp_path: object) -> None:
        """Verify lipo reports arm64 architecture."""
        out = os.path.join(str(tmp_path), "core.o")
        self._compile_ios("mapanare_core.c", out)
        result = subprocess.run(["lipo", "-info", out], capture_output=True, text=True, timeout=5)
        assert "arm64" in result.stdout

    def test_static_library_builds(self, tmp_path: object) -> None:
        """Build a static library from all iOS objects."""
        objs = []
        for src in ["mapanare_core.c", "mapanare_runtime.c", "mapanare_io.c", "mapanare_gpu.c"]:
            out = os.path.join(str(tmp_path), src.replace(".c", ".o"))
            r = self._compile_ios(src, out)
            assert r.returncode == 0, f"{src}: {r.stderr}"
            objs.append(out)

        lib = os.path.join(str(tmp_path), "libmapanare.a")
        result = subprocess.run(
            ["ar", "rcs", lib] + objs,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert os.path.exists(lib)
        assert os.path.getsize(lib) > 0

    def test_symbol_visibility(self, tmp_path: object) -> None:
        """Verify key symbols are exported in the iOS runtime object."""
        out = os.path.join(str(tmp_path), "runtime.o")
        self._compile_ios("mapanare_runtime.c", out)

        result = subprocess.run(["nm", "-g", out], capture_output=True, text=True, timeout=5)
        symbols = result.stdout

        # Agent lifecycle symbols must be exported
        expected = [
            "mapanare_agent_init",
            "mapanare_agent_spawn",
            "mapanare_agent_send",
            "mapanare_agent_stop",
            "mapanare_ring_create",
            "mapanare_ring_push",
            "mapanare_ring_pop",
            "mapanare_pool_create",
            "mapanare_coop_scheduler_init",
            "mapanare_coop_scheduler_run",
        ]
        for sym in expected:
            assert sym in symbols, f"Missing exported symbol: {sym}"

    def test_dispatch_semaphore_used(self, tmp_path: object) -> None:
        """Verify iOS build uses dispatch_semaphore, not deprecated sem_init."""
        out = os.path.join(str(tmp_path), "runtime.o")
        self._compile_ios("mapanare_runtime.c", out)

        result = subprocess.run(["nm", "-u", out], capture_output=True, text=True, timeout=5)
        undefined = result.stdout
        assert "dispatch_semaphore_create" in undefined
        assert "sem_init" not in undefined

    def test_kqueue_backend_on_ios(self, tmp_path: object) -> None:
        """Verify iOS I/O build uses kqueue, not epoll."""
        out = os.path.join(str(tmp_path), "io.o")
        self._compile_ios("mapanare_io.c", out)

        result = subprocess.run(["nm", "-g", out], capture_output=True, text=True, timeout=5)
        # The event loop backend function should be exported
        assert "__mn_event_loop_backend" in result.stdout
        assert "__mn_event_loop_new" in result.stdout

        # Check undefined symbols: should reference kqueue, not epoll
        undef = subprocess.run(["nm", "-u", out], capture_output=True, text=True, timeout=5)
        assert "epoll" not in undef.stdout.lower()


# =========================================================================
# 2. LLVM IR emission with iOS target
# =========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestLLVMIRIOSTarget:
    """Test LLVM IR emission with iOS target triple."""

    def test_emit_llvm_ios_triple(self) -> None:
        """Verify emitted IR contains the iOS target triple."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(GOLDEN_DIR, "01_hello.mn")
            if not os.path.exists(src):
                pytest.skip("Golden test 01_hello.mn not found")

            # Copy to tmp to avoid modifying golden dir
            tmp_src = os.path.join(tmpdir, "hello.mn")
            shutil.copy(src, tmp_src)

            result = subprocess.run(
                [
                    "mapanare",
                    "emit-llvm",
                    "--target",
                    "aarch64-apple-ios",
                    tmp_src,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr

            ll_file = tmp_src.replace(".mn", ".ll")
            assert os.path.exists(ll_file)

            with open(ll_file) as f:
                ir = f.read()
            assert 'target triple = "aarch64-apple-ios17.0"' in ir

    def test_ios_data_layout(self) -> None:
        """Verify the iOS target data layout matches what we defined."""
        target = TARGETS["aarch64-apple-ios"]
        assert target.data_layout.startswith("e-m:o-")
        assert "i64:64" in target.data_layout


# =========================================================================
# 3. End-to-end: .mn -> LLVM IR -> Mach-O .o
# =========================================================================


@pytest.mark.skipif(not HAS_IOS_SDK, reason="iOS SDK not found")
@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not available")
class TestEndToEndIOSCompile:
    """Full pipeline: .mn source -> LLVM IR -> iOS Mach-O object."""

    def test_hello_to_macho(self) -> None:
        """Compile hello world all the way to iOS Mach-O."""
        src = os.path.join(GOLDEN_DIR, "01_hello.mn")
        if not os.path.exists(src):
            pytest.skip("Golden test 01_hello.mn not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_src = os.path.join(tmpdir, "hello.mn")
            shutil.copy(src, tmp_src)

            # Step 1: emit LLVM IR
            result = subprocess.run(
                [
                    "mapanare",
                    "emit-llvm",
                    "--target",
                    "aarch64-apple-ios",
                    tmp_src,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr

            ll_file = os.path.join(tmpdir, "hello.ll")
            assert os.path.exists(ll_file)

            # Step 2: compile IR to Mach-O
            obj_file = os.path.join(tmpdir, "hello.o")
            result = subprocess.run(
                [
                    "xcrun",
                    "--sdk",
                    "iphoneos",
                    "clang",
                    "-c",
                    "-target",
                    "arm64-apple-ios17.0",
                    "-isysroot",
                    IOS_SDK,
                    ll_file,
                    "-o",
                    obj_file,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, result.stderr

            # Verify Mach-O format
            file_result = subprocess.run(
                ["file", obj_file], capture_output=True, text=True, timeout=5
            )
            assert "Mach-O 64-bit object arm64" in file_result.stdout

            # Verify _main symbol exists
            nm_result = subprocess.run(
                ["nm", "-g", obj_file], capture_output=True, text=True, timeout=5
            )
            assert "_main" in nm_result.stdout
