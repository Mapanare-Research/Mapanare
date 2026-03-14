"""Tests for list.push() on LLVM backend — Phase 2 prerequisite.

Verifies that list.push() compiles to valid LLVM IR via the MIR pipeline,
including both local variable push and struct field push patterns.
"""

from __future__ import annotations

import textwrap

import pytest

from mapanare.cli import _compile_to_llvm_ir


def _to_llvm_ir_mir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename, use_mir=True)


class TestListPushLLVM:
    """List .push() compiles to valid LLVM IR via MIR."""

    def test_push_to_local_list(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut nums: List<Int> = []
                nums.push(1)
                nums.push(2)
                nums.push(3)
                println(len(nums))
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text
        assert "__mn_list_new" in ir_text
        assert "define" in ir_text

    def test_push_to_local_string_list(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut words: List<String> = []
                words.push("hello")
                words.push("world")
                println(len(words))
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text

    def test_push_and_index_access(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                xs.push(10)
                xs.push(20)
                println(xs[0])
                println(xs[1])
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text
        assert "__mn_list_get" in ir_text

    def test_push_in_loop(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut items: List<Int> = []
                for i in 0..5 {
                    items.push(i)
                }
                println(len(items))
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text

    def test_push_to_struct_field(self) -> None:
        source = textwrap.dedent("""\
            struct Container {
                items: List<Int>
            }

            fn new_container() -> Container {
                let items: List<Int> = []
                return new Container { items: items }
            }

            fn main() {
                let mut c: Container = new_container()
                c.items.push(42)
                println(len(c.items))
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text

    def test_push_preserves_previous_elements(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = [1, 2]
                xs.push(3)
                println(len(xs))
                println(xs[0])
                println(xs[2])
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text

    def test_push_return_value_unused(self) -> None:
        source = textwrap.dedent("""\
            fn build_list() -> List<Int> {
                let mut result: List<Int> = []
                result.push(1)
                result.push(2)
                return result
            }

            fn main() {
                let xs: List<Int> = build_list()
                println(len(xs))
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        assert "__mn_list_push" in ir_text


class TestIndexSetLLVM:
    """list[i] = val on LLVM backend."""

    def test_index_set_basic(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = [10, 20, 30]
                xs[1] = 99
                println(xs[1])
            }
        """)
        ir_text = _to_llvm_ir_mir(source)
        # Compiles without error; IndexSet + IndexGet generate list_get calls
        assert "define" in ir_text
        assert "__mn_list" in ir_text
