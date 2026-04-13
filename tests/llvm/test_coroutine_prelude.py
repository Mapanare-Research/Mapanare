"""v4.70.0 — Coroutine prelude LLVM IR emission tests.

Tests that async fn emits the coroutine prelude: presplitcoroutine attribute,
llvm.coro.id, llvm.coro.begin, llvm.coro.suspend, llvm.coro.end, cleanup block,
and Future struct allocation.
"""

from __future__ import annotations

import textwrap

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(source: str) -> str:
    """Parse, check, lower, emit LLVM IR for the given source."""
    tree = parse(source)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(module)


class TestCoroutinePrelude:
    def test_async_fn_has_presplitcoroutine(self) -> None:
        """async fn should have the presplitcoroutine attribute."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "presplitcoroutine" in ir

    def test_async_fn_has_coro_id(self) -> None:
        """async fn should call llvm.coro.id."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "@llvm.coro.id" in ir

    def test_async_fn_has_coro_begin(self) -> None:
        """async fn should call llvm.coro.begin."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "@llvm.coro.begin" in ir

    def test_async_fn_has_coro_suspend(self) -> None:
        """async fn should have initial and final suspend points."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "@llvm.coro.suspend" in ir

    def test_async_fn_has_coro_end(self) -> None:
        """async fn should call llvm.coro.end."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "@llvm.coro.end" in ir

    def test_async_fn_has_cleanup_block(self) -> None:
        """async fn should have a coro.cleanup block with coro.free."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "coro.cleanup:" in ir
        assert "@llvm.coro.free" in ir

    def test_async_fn_allocates_future(self) -> None:
        """async fn should allocate a Future struct."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "%future" in ir

    def test_async_fn_returns_ptr(self) -> None:
        """async fn should return ptr (Future handle), not the declared type."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # The define line should return ptr
        assert "define ptr @compute" in ir or "define internal ptr @compute" in ir

    def test_sync_fn_no_coroutine(self) -> None:
        """Regular fn should NOT have coroutine intrinsics."""
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "presplitcoroutine" not in ir
        assert "llvm.coro" not in ir

    def test_coro_intrinsic_declarations(self) -> None:
        """Module with async fn should have coro intrinsic declarations."""
        source = textwrap.dedent("""\
            async fn compute() -> Int {
                return 42
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "declare token @llvm.coro.id" in ir
        assert "declare ptr @llvm.coro.begin" in ir
        assert "declare i8 @llvm.coro.suspend" in ir


class TestAwaitStillErrors:
    def test_await_expr_errors_at_v4_72(self) -> None:
        """await expression should still error, now pointing at v4.72.0."""
        import pytest

        source = textwrap.dedent("""\
            async fn get() -> Int { return 1 }
            async fn f() -> Int {
                let x = await get()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        with pytest.raises(RuntimeError, match=r"v4\.72\.0"):
            _emit(source)
