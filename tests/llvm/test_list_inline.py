"""v5.1.0 Perf.1 — inline list access for value-type elements.

Verifies that List<Int>, List<Float>, List<Ptr> indexing emits inline
GEP+load instead of opaque call @__mn_list_get, and that List<String>
and List<Struct> still fall back to the opaque call.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _ir(source: str) -> str:
    return _compile_to_llvm_ir(textwrap.dedent(source), "test.mn")


class TestListInlineGet:
    """IndexGet inline path for 8-byte element types."""

    def test_list_int_uses_inline_gep(self) -> None:
        """List<Int> indexing emits getelementptr, not __mn_list_get."""
        ir = _ir("""\
            fn main() {
                let mut xs: List<Int> = [10, 20, 30]
                print(str(xs[1]))
            }
        """)
        assert "getelementptr inbounds i64" in ir
        # The opaque call should NOT appear for the indexing operation
        assert "__mn_list_get" not in ir

    def test_list_int_bounds_check_present(self) -> None:
        """Inline path emits icmp uge bounds check + abort trap."""
        ir = _ir("""\
            fn main() {
                let xs: List<Int> = [1, 2, 3]
                print(str(xs[0]))
            }
        """)
        assert "icmp uge i64" in ir
        assert "call void @abort()" in ir
        assert "unreachable" in ir

    def test_list_float_uses_inline_gep(self) -> None:
        """List<Float> (8-byte element) also uses inline GEP."""
        ir = _ir("""\
            fn main() {
                let mut xs: List<Float> = [1.0, 2.0, 3.0]
                print(str(xs[0]))
            }
        """)
        assert "getelementptr inbounds i64" in ir
        assert "load double, ptr" in ir
        assert "__mn_list_get" not in ir

    def test_list_int_push_then_get_roundtrip(self) -> None:
        """Push + inline get produces valid IR with both operations."""
        ir = _ir("""\
            fn main() {
                let mut xs: List<Int> = []
                xs.push(42)
                xs.push(99)
                print(str(xs[0]))
                print(str(xs[1]))
            }
        """)
        assert "__mn_list_push" in ir
        assert "getelementptr inbounds i64" in ir
        # Should have two inline get sequences (two index ops)
        assert ir.count("getelementptr inbounds i64") >= 2


class TestListInlineSet:
    """IndexSet inline path for 8-byte element types."""

    def test_list_int_set_uses_inline_gep(self) -> None:
        """List<Int> index set emits inline GEP + store."""
        ir = _ir("""\
            fn main() {
                let mut xs: List<Int> = [10, 20, 30]
                xs[1] = 99
                print(str(xs[1]))
            }
        """)
        # IndexSet should emit inline store
        assert "store i64" in ir
        assert "getelementptr inbounds i64" in ir

    def test_list_int_set_has_bounds_check(self) -> None:
        """IndexSet also emits bounds check."""
        ir = _ir("""\
            fn main() {
                let mut xs: List<Int> = [1, 2, 3]
                xs[0] = 99
            }
        """)
        # Bounds check from the set operation
        assert "icmp uge i64" in ir
        assert "call void @abort()" in ir


class TestListSlowPath:
    """Non-8-byte element types fall back to __mn_list_get."""

    def test_list_string_uses_slow_path(self) -> None:
        """List<String> (16-byte element) falls back to opaque call."""
        ir = _ir("""\
            fn main() {
                let xs: List<String> = ["hello", "world"]
                print(xs[0])
            }
        """)
        # String elements are 16 bytes — must use slow path
        assert "__mn_list_get" in ir or "__mn_list_str_get" in ir

    def test_list_struct_uses_slow_path(self) -> None:
        """List<Struct> with >8-byte struct falls back to opaque call."""
        ir = _ir("""\
            struct Pair {
                x: Int,
                y: Int
            }

            fn main() {
                let p1: Pair = new Pair { x: 1, y: 2 }
                let mut items: List<Pair> = [p1]
                let p: Pair = items[0]
                print(str(p.x))
            }
        """)
        # Struct with 2 fields (16 bytes) — slow path
        assert "__mn_list_get" in ir


class TestListInlineAbortDeclaration:
    """abort() is properly declared with correct attributes."""

    def test_abort_declared_noreturn_nounwind(self) -> None:
        ir = _ir("""\
            fn main() {
                let xs: List<Int> = [1]
                print(str(xs[0]))
            }
        """)
        assert "declare void @abort() noreturn nounwind" in ir


class TestListInlineLoopAccess:
    """Inline list access in loop context — the primary optimization target."""

    def test_sum_loop_uses_inline_gep(self) -> None:
        """for i in 0..len(items) { total += items[i] } — inline path."""
        ir = _ir("""\
            fn sum_list(items: List<Int>) -> Int {
                let mut total: Int = 0
                for i in 0..len(items) {
                    total = total + items[i]
                }
                return total
            }

            fn main() {
                let nums: List<Int> = [10, 20, 30]
                print(str(sum_list(nums)))
            }
        """)
        assert "getelementptr inbounds i64" in ir
        assert "__mn_list_get" not in ir
