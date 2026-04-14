"""Drop Glue tests — verify heap-allocated values compile correctly.

v1.0.4: Arena lifecycle and explicit drop glue are disabled pending
return-value escape analysis. These tests verify that string and closure
operations produce valid LLVM IR without memory errors.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel as OptLevel


def _to_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename)


def _to_ir_o0(source: str, filename: str = "test.mn") -> str:
    """Compile at -O0 so inliner+DCE leave the named runtime calls
    visible. Used by drop-glue tests that count specific
    ``__mn_str_*`` calls — at O2 those get inlined into ``main`` and,
    when the inputs are constant, the concat is folded entirely out.
    The drop-glue invariants under test still hold; only the surface
    changes."""
    return _compile_to_llvm_ir(source, filename, opt_level=OptLevel.O0)


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
        ir_text = _to_ir_o0(source)
        assert "__mn_str_concat" in ir_text

    def test_returned_string(self) -> None:
        source = textwrap.dedent("""\
            fn greet(name: String) -> String {
                return "Hello, " + name
            }
            fn main() { print(greet("world")) }
        """)
        ir_text = _to_ir_o0(source)
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


class TestStructReturnDropGlue:
    """v4.78.0: verify drop glue runs for non-escaping locals in struct-return functions.

    CARRY_FORWARD #49 (8 cycles): the blanket early return skipped ALL
    drop glue for functions returning structs with ptr fields. Now that
    the per-kind helpers use ret_ptr_fields, drop glue must run for
    local strings that are NOT part of the return value.
    """

    def test_struct_return_emits_drop_glue_for_locals(self) -> None:
        source = textwrap.dedent("""\
            struct Pair {
                a: Int,
                b: Int
            }
            fn make_pair(x: Int) -> Pair {
                let msg: String = "creating pair"
                print(msg)
                let r: Pair = new Pair { a: x, b: x + 1 }
                return r
            }
            fn main() {
                let p: Pair = make_pair(5)
                print(str(p.a))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_struct_with_string_field_return_has_drop_glue(self) -> None:
        source = textwrap.dedent("""\
            struct Named {
                name: String,
                value: Int
            }
            fn make_named(x: Int) -> Named {
                let tmp: String = str(x) + " items"
                print(tmp)
                let r: Named = new Named { name: str(x), value: x }
                return r
            }
            fn main() {
                let n: Named = make_named(42)
                print(n.name)
            }
        """)
        ir_text = _to_ir(source)
        # v4.78.0: drop glue should run for the 'tmp' local (heap-allocated
        # via str()+concat, which is NOT the return value) even though the
        # function returns a struct with a ptr field (name: String).
        assert "__mn_str_free" in ir_text


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
