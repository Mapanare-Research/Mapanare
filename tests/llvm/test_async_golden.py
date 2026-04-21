"""v4.75.0 — End-to-end async golden tests.

Verifies that the three async golden tests (55-57) compile through the
full pipeline and produce correct coroutine IR with block_on.
"""

from __future__ import annotations

from pathlib import Path

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def _compile_golden(name: str) -> str:
    """Compile a golden test file and return the LLVM IR."""
    source = (GOLDEN_DIR / name).read_text()
    tree = parse(source)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(module)


class TestAsyncBasicGolden:
    def test_55_compiles(self) -> None:
        """55_async_basic.mn compiles with coroutine prelude."""
        ir = _compile_golden("55_async_basic.mn")
        assert "presplitcoroutine" in ir
        assert "block_on.done" in ir
        assert "@llvm.coro.id" in ir

    def test_55_has_compute_fn(self) -> None:
        """55_async_basic.mn has async fn compute."""
        ir = _compile_golden("55_async_basic.mn")
        assert "@compute" in ir


class TestAsyncAwaitGolden:
    def test_56_compiles(self) -> None:
        """56_async_await.mn compiles with nested await."""
        ir = _compile_golden("56_async_await.mn")
        assert "presplitcoroutine" in ir
        assert "await.drive" in ir or "await.check" in ir

    def test_56_has_both_async_fns(self) -> None:
        """56_async_await.mn has inner and outer async fns."""
        ir = _compile_golden("56_async_await.mn")
        assert "@inner" in ir
        assert "@outer" in ir


class TestRealAwaitGolden:
    def test_57_compiles(self) -> None:
        """57_real_await.mn (the A1 closure test) compiles."""
        ir = _compile_golden("57_real_await.mn")
        assert "presplitcoroutine" in ir

    def test_57_has_all_four_async_fns(self) -> None:
        """57_real_await.mn has fetch_a, fetch_b, fetch_c, fanout."""
        ir = _compile_golden("57_real_await.mn")
        assert "@fetch_a" in ir
        assert "@fetch_b" in ir
        assert "@fetch_c" in ir
        assert "@fanout" in ir

    def test_57_has_multiple_await_points(self) -> None:
        """57_real_await.mn has 3 await suspension points in fanout."""
        ir = _compile_golden("57_real_await.mn")
        # fanout has 3 await points → 3 drive blocks
        drive_count = ir.count("await.drive.")
        assert drive_count >= 3, f"Expected >= 3 await.drive blocks, got {drive_count}"

    def test_57_has_block_on(self) -> None:
        """57_real_await.mn uses block_on in main."""
        ir = _compile_golden("57_real_await.mn")
        assert "block_on.done" in ir
        assert "@llvm.coro.destroy" in ir
