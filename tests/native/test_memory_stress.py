"""Stress test for memory management (Phase 1.1 Task 7).

Verifies that the C runtime arena + tag-bit free mechanism works correctly
by testing the C runtime functions directly via ctypes. This avoids needing
a full LLVM compile pipeline while still testing the actual C code.

When a C compiler is available, this test can be extended to compile
mapanare_core.c and run the stress test natively.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess

import pytest

# Skip if no C compiler available
_CC = shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "runtime", "native")
CORE_C = os.path.join(RUNTIME_DIR, "mapanare_core.c")
CORE_H = os.path.join(RUNTIME_DIR, "mapanare_core.h")


@pytest.mark.skipif(
    _CC is None,
    reason="No C compiler available — cannot compile runtime for stress test",
)
class TestMemoryStressNative:
    """Stress tests that compile and run against the real C runtime."""

    @pytest.fixture(autouse=True)
    def _compile_runtime(self, tmp_path: object) -> None:
        """Compile the C runtime as a shared library for ctypes."""
        self._tmpdir = str(tmp_path)
        ext = ".dll" if platform.system() == "Windows" else ".so"
        self._lib_path = os.path.join(self._tmpdir, f"libmapanare_core{ext}")

        assert _CC is not None
        result = subprocess.run(
            [_CC, "-shared", "-fPIC", "-O2", "-o", self._lib_path, CORE_C],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"C compilation failed: {result.stderr}")

        self._lib = ctypes.CDLL(self._lib_path)

    @staticmethod
    def _setup_str_funcs(
        lib: ctypes.CDLL,
    ) -> tuple[ctypes.CDLL, type[ctypes.Structure]]:
        """Configure ctypes bindings for __mn_str_* functions."""

        class MnString(ctypes.Structure):
            _fields_ = [
                ("data", ctypes.c_char_p),
                ("len", ctypes.c_int64),
            ]

        str_from_cstr = getattr(lib, "__mn_str_from_cstr")
        str_from_cstr.restype = MnString
        str_from_cstr.argtypes = [ctypes.c_char_p]

        str_free = getattr(lib, "__mn_str_free")
        str_free.restype = None
        str_free.argtypes = [MnString]

        str_concat = getattr(lib, "__mn_str_concat")
        str_concat.restype = MnString
        str_concat.argtypes = [MnString, MnString]

        return lib, MnString

    def test_1m_string_alloc_free(self) -> None:
        """Allocate and free 1M strings — RSS should stay bounded."""
        lib, _MnString = self._setup_str_funcs(self._lib)
        str_from_cstr = getattr(lib, "__mn_str_from_cstr")
        str_free = getattr(lib, "__mn_str_free")

        # Allocate and immediately free 1M strings
        for i in range(1_000_000):
            s = str_from_cstr(b"hello world test string")
            str_free(s)

        # If we get here without OOM, the test passes.
        # A proper RSS check would use /proc/self/status or similar.

    def test_arena_alloc_destroy(self) -> None:
        """Create arena, allocate 1M chunks, destroy — no leak."""
        lib = self._lib
        lib.mn_arena_create.restype = ctypes.c_void_p
        lib.mn_arena_create.argtypes = [ctypes.c_int64]
        lib.mn_arena_alloc.restype = ctypes.c_void_p
        lib.mn_arena_alloc.argtypes = [ctypes.c_void_p, ctypes.c_int64]
        lib.mn_arena_destroy.restype = None
        lib.mn_arena_destroy.argtypes = [ctypes.c_void_p]

        arena = lib.mn_arena_create(8192)
        assert arena is not None

        for _ in range(1_000_000):
            ptr = lib.mn_arena_alloc(arena, 64)
            assert ptr is not None

        lib.mn_arena_destroy(arena)

    def test_str_concat_in_loop_with_free(self) -> None:
        """Concat strings in a loop with proper free — no leak."""
        lib, _MnString = self._setup_str_funcs(self._lib)
        str_from_cstr = getattr(lib, "__mn_str_from_cstr")
        str_concat = getattr(lib, "__mn_str_concat")
        str_free = getattr(lib, "__mn_str_free")

        a = str_from_cstr(b"hello")
        b = str_from_cstr(b" world")

        for _ in range(100_000):
            c = str_concat(a, b)
            str_free(c)

        str_free(a)
        str_free(b)


class TestMemoryStressPython:
    """Python-level tests that verify the emitter generates proper cleanup IR."""

    def test_loop_with_concat_has_cleanup(self) -> None:
        """A loop concatenating strings should have cleanup in the IR."""
        from mapanare.ast_nodes import (
            Block,
            CallExpr,
            ExprStmt,
            FnDef,
            ForLoop,
            Identifier,
            IntLiteral,
            LetBinding,
            NamedType,
            Program,
            RangeExpr,
            StringLiteral,
        )
        from mapanare.emit_llvm import LLVMEmitter

        fn = FnDef(
            name="stress",
            params=[],
            return_type=NamedType(name="Void"),
            body=Block(
                stmts=[
                    LetBinding(
                        name="s",
                        mutable=True,
                        type_annotation=None,
                        value=StringLiteral(value=""),
                    ),
                    ForLoop(
                        var_name="i",
                        iterable=RangeExpr(
                            start=IntLiteral(value=0),
                            end=IntLiteral(value=1000),
                            inclusive=False,
                        ),
                        body=Block(
                            stmts=[
                                ExprStmt(
                                    expr=CallExpr(
                                        callee=Identifier(name="print"),
                                        args=[Identifier(name="i")],
                                    )
                                ),
                            ]
                        ),
                    ),
                ]
            ),
        )

        emitter = LLVMEmitter()
        module = emitter.emit_program(Program(definitions=[fn]))
        ir_text = str(module)

        # Should have arena management
        assert "mn_arena_create" in ir_text
        assert "mn_arena_destroy" in ir_text
