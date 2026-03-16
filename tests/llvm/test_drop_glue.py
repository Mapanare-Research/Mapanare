"""Drop Glue tests — verify cleanup code for heap-allocated values.

v1.0.4: String and closure environment cleanup via arena lifecycle.

Drop glue (explicit __mn_str_free / __mn_free) is deferred due to LLVM
dominance errors when tracking values across basic blocks. The arena
lifecycle (mn_arena_create / mn_arena_destroy) handles cleanup instead.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename, use_mir=True)


class TestStringDropGlue:
    """Verify that string operations produce valid LLVM IR with arena cleanup."""

    def test_str_from_int(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 42
                println(str(x))
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_str_from_int" in ir_text
        assert "mn_arena_destroy" in ir_text

    def test_str_concat(self) -> None:
        source = textwrap.dedent("""\
            fn show(name: String) {
                let msg: String = "hello " + name
                println(msg)
            }

            fn main() {
                show("world")
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_str_concat" in ir_text

    def test_returned_string(self) -> None:
        source = textwrap.dedent("""\
            fn greet(name: String) -> String {
                return "Hello, " + name
            }

            fn main() {
                let msg: String = greet("world")
                println(msg)
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_str_concat" in ir_text
        assert "define" in ir_text


class TestClosureDropGlue:
    """Verify closure environment allocation uses arena lifecycle."""

    def test_closure_env_allocated(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 10
                let add_x = (n) => n + x
                println(str(add_x(5)))
            }
        """)
        ir_text = _to_ir(source)
        has_alloc = "mn_arena_alloc" in ir_text or "__mn_alloc" in ir_text
        assert has_alloc, "Closure should allocate an environment"
        assert "mn_arena_destroy" in ir_text


class TestCombinedDropGlue:
    """Verify arena lifecycle handles both strings and closures."""

    def test_mixed_string_and_closure(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 42
                let msg: String = str(x)
                let double = (n) => n * 2
                println(msg)
                println(str(double(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "mn_arena_destroy" in ir_text
        assert "define" in ir_text
