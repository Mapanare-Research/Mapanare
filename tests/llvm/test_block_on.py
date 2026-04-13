"""v4.73.0/v4.92.0 — block_on builtin and end-to-end async IR tests.

v4.92.0: block_on now uses the scheduler (__mn_coro_scheduler_register +
__mn_coro_scheduler_run) instead of an inline resume loop. await inside
async functions emits real coro.suspend. Tests updated to match.
"""

from __future__ import annotations

import textwrap

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker


def _emit(source: str) -> str:
    """Parse, check, lower, emit LLVM IR."""
    tree = parse(source)
    checker = SemanticChecker()
    checker.check(tree)
    module = lower(tree)
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(module)


class TestBlockOn:
    def test_block_on_emits_scheduler_call(self) -> None:
        """block_on should register with scheduler and call run (v4.92.0)."""
        source = textwrap.dedent("""\
            async fn compute() -> Int { return 42 }
            fn main() -> Int {
                let result = block_on(compute())
                return result
            }
        """)
        ir = _emit(source)
        assert "@__mn_coro_scheduler_register" in ir
        assert "@__mn_coro_scheduler_run" in ir

    def test_block_on_checks_done(self) -> None:
        """block_on should check coro.done after each resume."""
        source = textwrap.dedent("""\
            async fn compute() -> Int { return 42 }
            fn main() -> Int {
                let result = block_on(compute())
                return result
            }
        """)
        ir = _emit(source)
        assert "@llvm.coro.done" in ir

    def test_block_on_destroys_coroutine(self) -> None:
        """block_on should call coro.destroy + free after completion."""
        source = textwrap.dedent("""\
            async fn compute() -> Int { return 42 }
            fn main() -> Int {
                let result = block_on(compute())
                return result
            }
        """)
        ir = _emit(source)
        assert "@llvm.coro.destroy" in ir
        assert "@free" in ir

    def test_block_on_extracts_value(self) -> None:
        """block_on should extract the value from the completed Future."""
        source = textwrap.dedent("""\
            async fn compute() -> Int { return 42 }
            fn main() -> Int {
                let result = block_on(compute())
                return result
            }
        """)
        ir = _emit(source)
        assert "block_on.done" in ir
        # GEP into future to extract value
        assert "getelementptr inbounds {i8, ptr}" in ir


class TestEndToEndAsyncIR:
    def test_simple_async_fn_full_pipeline(self) -> None:
        """Simple async fn + block_on produces complete IR."""
        source = textwrap.dedent("""\
            async fn compute() -> Int { return 42 }
            fn main() -> Int {
                let result = block_on(compute())
                return result
            }
        """)
        ir = _emit(source)
        # Async fn has coroutine prelude
        assert "presplitcoroutine" in ir
        assert "@llvm.coro.id" in ir
        # block_on uses scheduler (v4.92.0)
        assert "@__mn_coro_scheduler_register" in ir
        # Result extraction
        assert "block_on.done" in ir

    def test_async_with_await_full_pipeline(self) -> None:
        """async fn with await + block_on produces complete IR."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x + 1
            }
            fn main() -> Int {
                let result = block_on(outer())
                return result
            }
        """)
        ir = _emit(source)
        # Both async fns have prelude
        assert ir.count("presplitcoroutine") >= 2
        # await has drive + real suspend (v4.92.0)
        assert "await.drive" in ir or "await.suspend" in ir
        # block_on uses scheduler (v4.92.0)
        assert "@__mn_coro_scheduler_run" in ir

    def test_await_inline_resume(self) -> None:
        """await uses inline resume (coro.resume on inner) not suspension."""
        source = textwrap.dedent("""\
            async fn inner() -> Int { return 42 }
            async fn outer() -> Int {
                let x = await inner()
                return x
            }
            fn main() -> Int {
                let result = block_on(outer())
                return result
            }
        """)
        ir = _emit(source)
        # await.drive block calls coro.resume on the inner handle
        assert "await.drive" in ir
        assert "@llvm.coro.resume" in ir

    def test_multiple_block_on_unique_labels(self) -> None:
        """Multiple block_on calls get unique labels."""
        source = textwrap.dedent("""\
            async fn a() -> Int { return 1 }
            async fn b() -> Int { return 2 }
            fn main() -> Int {
                let x = block_on(a())
                let y = block_on(b())
                return x + y
            }
        """)
        ir = _emit(source)
        assert ir.count("block_on.done.") >= 2
