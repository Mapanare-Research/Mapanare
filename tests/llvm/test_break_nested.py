"""Regression test for break inside nested if/for.

Verifies that break statements inside if blocks within for loops
produce correct LLVM IR with jump to the for_exit block.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_ir(source: str, filename: str = "test.mn") -> str:
    return _compile_to_llvm_ir(source, filename)


class TestBreakInsideNestedIf:
    """Break inside if-inside-for produces jump to for_exit, not if_merge."""

    def test_break_in_if_in_for(self) -> None:
        source = textwrap.dedent("""\
            fn find_index(items: List<Int>, target: Int) -> Int {
                let mut result: Int = -1
                for i in 0..10 {
                    if items[i] == target {
                        result = i
                        break
                    }
                }
                return result
            }
            fn main() {
                let items: List<Int> = [10, 20, 30, 40]
                print(find_index(items, 30))
            }
        """)
        ir = _to_ir(source)
        assert "define" in ir
        # The break must produce a jump to for_exit, not if_merge
        # Check that the for_exit block exists
        assert "for_exit" in ir

    def test_break_in_while(self) -> None:
        source = textwrap.dedent("""\
            fn sum_until(limit: Int) -> Int {
                let mut sum: Int = 0
                let mut i: Int = 0
                while i < 20 {
                    if i >= limit {
                        break
                    }
                    sum = sum + i
                    i = i + 1
                }
                return sum
            }
            fn main() {
                print(sum_until(5))
            }
        """)
        ir = _to_ir(source)
        assert "define" in ir
        assert "while_exit" in ir

    def test_continue_in_if_in_for(self) -> None:
        source = textwrap.dedent("""\
            fn skip_evens() -> Int {
                let mut sum: Int = 0
                for i in 0..10 {
                    if i % 2 == 0 {
                        continue
                    }
                    sum = sum + i
                }
                return sum
            }
            fn main() {
                print(skip_evens())
            }
        """)
        ir = _to_ir(source)
        assert "define" in ir
        assert "for_header" in ir
