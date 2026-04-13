"""v4.72.0 — Coroutine lowering pt 2: await suspension IR tests.

Tests that await expr emits coro.save + coro.suspend + switch, fast-path
readiness check, and value extraction from Future struct.
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


class TestAwaitSuspension:
    def test_await_emits_coro_save(self) -> None:
        """await should produce a llvm.coro.save call."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # The outer function should have coro.save for the await point
        assert ir.count("@llvm.coro.save") >= 3  # init + await + final (at least)

    def test_await_emits_coro_suspend(self) -> None:
        """await should produce a llvm.coro.suspend call."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # At least 3 suspends: init, await, final
        assert ir.count("@llvm.coro.suspend") >= 3

    def test_await_has_fast_path_check(self) -> None:
        """await should check if the future is already ready before suspending."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # Fast path: load state byte, compare to 1
        assert "icmp eq i8" in ir

    def test_await_extracts_value(self) -> None:
        """await should extract the value from the ready Future."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # GEP to get payload ptr from Future {i8, ptr}
        assert "getelementptr inbounds {i8, ptr}" in ir

    def test_await_drive_and_ready_labels(self) -> None:
        """await should create drive/check/ready labels (v4.73.0 inline resume)."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "await.drive" in ir
        assert "await.ready" in ir

    def test_multiple_awaits_unique_labels(self) -> None:
        """Multiple awaits should get unique labels."""
        source = textwrap.dedent("""\
            async fn a() -> Int { return 1 }
            async fn b() -> Int { return 2 }
            async fn f() -> Int {
                let x = await a()
                let y = await b()
                return x + y
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        # Should have at least 2 distinct await.ready labels
        ready_count = ir.count("await.ready.")
        assert ready_count >= 2, f"Expected >= 2 await.ready labels, got {ready_count}"

    def test_no_await_error(self) -> None:
        """await no longer raises an error (v4.72.0 shipped suspension)."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        # Should not raise — await lowering is real now
        ir = _emit(source)
        assert len(ir) > 0


class TestCoroutinePreludeStillWorks:
    def test_prelude_with_await(self) -> None:
        """async fn with await still has the full coroutine prelude."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int { return 0 }
        """)
        ir = _emit(source)
        assert "presplitcoroutine" in ir
        assert "@llvm.coro.id" in ir
        assert "@llvm.coro.begin" in ir
        assert "coro.cleanup:" in ir
        assert "@llvm.coro.end" in ir
