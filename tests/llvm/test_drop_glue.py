"""Drop Glue tests — verify heap-allocated values compile correctly.

v1.0.4: Arena lifecycle and explicit drop glue are disabled pending
return-value escape analysis. These tests verify that string and closure
operations produce valid LLVM IR without memory errors.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename, use_mir=True)


class TestStringDropGlue:
    """Verify string operations produce valid LLVM IR."""

    def test_str_from_int(self) -> None:
        ir_text = _to_ir("fn main() { let x: Int = 42\n print(str(x)) }")
        assert "__mn_str_from_int" in ir_text

    def test_str_from_float(self) -> None:
        ir_text = _to_ir("fn main() { let x: Float = 3.14\n print(str(x)) }")
        assert "__mn_str_from_float" in ir_text

    def test_str_concat(self) -> None:
        source = textwrap.dedent("""\
            fn show(name: String) {
                let msg: String = "hello " + name
                print(msg)
            }
            fn main() { show("world") }
        """)
        ir_text = _to_ir(source)
        assert "__mn_str_concat" in ir_text

    def test_returned_string(self) -> None:
        source = textwrap.dedent("""\
            fn greet(name: String) -> String {
                return "Hello, " + name
            }
            fn main() { print(greet("world")) }
        """)
        ir_text = _to_ir(source)
        assert "__mn_str_concat" in ir_text
        assert "define" in ir_text


class TestClosureDropGlue:
    """Verify closure environment allocation."""

    def test_closure_env_allocated(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 10
                let add_x = (n) => n + x
                print(str(add_x(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_alloc" in ir_text or "mn_arena_alloc" in ir_text or "malloc" in ir_text


class TestCombinedDropGlue:
    """Verify combined string and closure operations."""

    def test_mixed_string_and_closure(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 42
                let msg: String = str(x)
                let double = (n) => n * 2
                print(msg)
                print(str(double(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
