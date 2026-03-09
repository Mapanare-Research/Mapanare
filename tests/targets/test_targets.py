"""Tests for cross-compilation targets (Phase 4.5)."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from mapanare.targets import (
    TARGET_AARCH64_APPLE_MACOS,
    TARGET_X86_64_LINUX_GNU,
    TARGET_X86_64_WINDOWS_MSVC,
    TARGETS,
    Target,
    get_target,
    host_target_name,
    list_targets,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run mapa CLI as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "mapanare.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(_PROJECT_ROOT),
    )


SIMPLE_FN = """\
fn add(a: Int, b: Int) -> Int {
    return a + b
}
"""


# ---------------------------------------------------------------------------
# Target definitions
# ---------------------------------------------------------------------------


class TestTargetDefinitions:
    def test_x86_64_linux_gnu_exists(self) -> None:
        target = TARGETS["x86_64-linux-gnu"]
        assert target is TARGET_X86_64_LINUX_GNU
        assert target.triple == "x86_64-unknown-linux-gnu"
        assert "e-m:e" in target.data_layout
        assert target.obj_ext == ".o"
        assert target.exe_ext == ""
        assert target.lib_ext == ".so"

    def test_aarch64_apple_macos_exists(self) -> None:
        target = TARGETS["aarch64-apple-macos"]
        assert target is TARGET_AARCH64_APPLE_MACOS
        assert "aarch64-apple" in target.triple
        assert "e-m:o" in target.data_layout
        assert target.obj_ext == ".o"
        assert target.exe_ext == ""
        assert target.lib_ext == ".dylib"

    def test_x86_64_windows_msvc_exists(self) -> None:
        target = TARGETS["x86_64-windows-msvc"]
        assert target is TARGET_X86_64_WINDOWS_MSVC
        assert target.triple == "x86_64-pc-windows-msvc"
        assert "e-m:w" in target.data_layout
        assert target.obj_ext == ".obj"
        assert target.exe_ext == ".exe"
        assert target.lib_ext == ".dll"

    def test_all_targets_have_required_fields(self) -> None:
        for name, target in TARGETS.items():
            assert target.triple, f"{name}: missing triple"
            assert target.data_layout, f"{name}: missing data_layout"
            assert target.description, f"{name}: missing description"
            assert target.linker, f"{name}: missing linker"

    def test_target_is_frozen(self) -> None:
        target = TARGET_X86_64_LINUX_GNU
        with pytest.raises(AttributeError):
            target.triple = "changed"  # type: ignore[misc]

    def test_three_targets_registered(self) -> None:
        assert len(TARGETS) == 3


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


class TestGetTarget:
    def test_get_target_by_name(self) -> None:
        target = get_target("x86_64-linux-gnu")
        assert target.triple == "x86_64-unknown-linux-gnu"

    def test_get_target_autodetect(self) -> None:
        target = get_target(None)
        assert isinstance(target, Target)
        assert target.triple  # non-empty

    def test_get_target_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown target"):
            get_target("riscv64-unknown")

    def test_host_target_name_returns_string(self) -> None:
        name = host_target_name()
        assert isinstance(name, str)
        assert name in TARGETS


# ---------------------------------------------------------------------------
# list_targets
# ---------------------------------------------------------------------------


class TestListTargets:
    def test_list_targets_returns_all(self) -> None:
        targets = list_targets()
        assert len(targets) == 3
        names = [name for name, _ in targets]
        assert "x86_64-linux-gnu" in names
        assert "aarch64-apple-macos" in names
        assert "x86_64-windows-msvc" in names

    def test_list_targets_sorted(self) -> None:
        targets = list_targets()
        names = [name for name, _ in targets]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# LLVM IR emission with target
# ---------------------------------------------------------------------------


class TestLLVMEmitterTarget:
    def test_emit_llvm_sets_target_triple(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter(
            target_triple="x86_64-unknown-linux-gnu",
            data_layout="e-m:e-p270:32:32",
        )
        assert emitter.module.triple == "x86_64-unknown-linux-gnu"
        assert emitter.module.data_layout == "e-m:e-p270:32:32"

    def test_emit_llvm_no_target_no_crash(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter

        emitter = LLVMEmitter()
        assert emitter.module is not None

    def test_emit_llvm_ir_for_each_target(self) -> None:
        from mapanare.emit_llvm import LLVMEmitter
        from mapanare.parser import parse
        from mapanare.semantic import check_or_raise

        ast = parse(SIMPLE_FN, filename="test.mn")
        check_or_raise(ast, filename="test.mn")

        for name, target in TARGETS.items():
            emitter = LLVMEmitter(
                target_triple=target.triple,
                data_layout=target.data_layout,
            )
            module = emitter.emit_program(ast)
            ir_str = str(module)
            assert f'target triple = "{target.triple}"' in ir_str
            assert f'target datalayout = "{target.data_layout}"' in ir_str


# ---------------------------------------------------------------------------
# CLI: emit-llvm subcommand
# ---------------------------------------------------------------------------


class TestEmitLLVMCommand:
    def test_emit_llvm_default_target(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        try:
            result = _run_cli("emit-llvm", src.name)
            assert result.returncode == 0
            ll_path = src.name.replace(".mn", ".ll")
            assert os.path.isfile(ll_path)
            content = Path(ll_path).read_text(encoding="utf-8")
            assert "target triple" in content
            os.unlink(ll_path)
        finally:
            os.unlink(src.name)

    def test_emit_llvm_with_target_flag(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        try:
            result = _run_cli("emit-llvm", src.name, "--target", "x86_64-linux-gnu")
            assert result.returncode == 0
            ll_path = src.name.replace(".mn", ".ll")
            content = Path(ll_path).read_text(encoding="utf-8")
            assert "x86_64-unknown-linux-gnu" in content
            os.unlink(ll_path)
        finally:
            os.unlink(src.name)

    def test_emit_llvm_with_output_flag(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        out = tempfile.mktemp(suffix=".ll")
        try:
            result = _run_cli("emit-llvm", src.name, "-o", out)
            assert result.returncode == 0
            assert os.path.isfile(out)
            os.unlink(out)
        finally:
            os.unlink(src.name)

    def test_emit_llvm_invalid_target(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        try:
            result = _run_cli("emit-llvm", src.name, "--target", "bad-target")
            assert result.returncode == 1
        finally:
            os.unlink(src.name)

    def test_emit_llvm_windows_target(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        try:
            result = _run_cli("emit-llvm", src.name, "--target", "x86_64-windows-msvc")
            assert result.returncode == 0
            ll_path = src.name.replace(".mn", ".ll")
            content = Path(ll_path).read_text(encoding="utf-8")
            assert "x86_64-pc-windows-msvc" in content
            os.unlink(ll_path)
        finally:
            os.unlink(src.name)

    def test_emit_llvm_macos_target(self) -> None:
        src = tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False, encoding="utf-8")
        src.write(SIMPLE_FN)
        src.close()
        try:
            result = _run_cli("emit-llvm", src.name, "--target", "aarch64-apple-macos")
            assert result.returncode == 0
            ll_path = src.name.replace(".mn", ".ll")
            content = Path(ll_path).read_text(encoding="utf-8")
            assert "aarch64-apple" in content
            os.unlink(ll_path)
        finally:
            os.unlink(src.name)


# ---------------------------------------------------------------------------
# CLI: targets subcommand
# ---------------------------------------------------------------------------


class TestTargetsCommand:
    def test_targets_lists_all(self) -> None:
        result = _run_cli("targets")
        assert result.returncode == 0
        assert "x86_64-linux-gnu" in result.stdout
        assert "aarch64-apple-macos" in result.stdout
        assert "x86_64-windows-msvc" in result.stdout
        assert "Host target:" in result.stdout
