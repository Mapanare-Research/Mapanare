"""Phase 2 — Emitter Hardening tests.

Task 5: Mutable variable reassignment in loops produces correct values.
Task 6: List accumulation via reassignment in loops.
Task 7: Emitter output comparison suite (10+ programs).

All tests compile Mapanare source to LLVM IR via the MIR pipeline and
verify the IR is structurally correct.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string via MIR pipeline."""
    return _compile_to_llvm_ir(source, filename)


# ===========================================================================
# Task 5: Mutable variable reassignment in loops
# ===========================================================================


class TestMutableVarReassignInLoop:
    """Task 5 — mutable variable reassignment in loops produces correct values."""

    def test_simple_counter_loop(self) -> None:
        """let mut x = 0; for i in 0..5 { x = x + 1 } — x should be 5."""
        source = textwrap.dedent("""\
            fn main() {
                let mut x: Int = 0
                for i in 0..5 {
                    x = x + 1
                }
                print(str(x))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        # Must have an add instruction for x + 1
        assert "add i64" in ir_text or "add nsw i64" in ir_text
        # Must store back to the alloca for x
        assert "store i64" in ir_text

    def test_compound_assign_in_loop(self) -> None:
        """let mut total = 0; for i in 0..10 { total += i } — compound assign."""
        source = textwrap.dedent("""\
            fn main() {
                let mut total: Int = 0
                for i in 0..10 {
                    total += i
                }
                print(str(total))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "add i64" in ir_text or "add nsw i64" in ir_text

    def test_reassign_string_in_loop(self) -> None:
        """let mut s = ""; for i in 0..3 { s = "hello" } — string reassignment."""
        source = textwrap.dedent("""\
            fn main() {
                let mut s: String = "start"
                for i in 0..3 {
                    s = "updated"
                }
                print(s)
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_while_loop_counter(self) -> None:
        """let mut n = 10; while n > 0 { n = n - 1 } — while loop mutation."""
        source = textwrap.dedent("""\
            fn main() {
                let mut n: Int = 10
                while n > 0 {
                    n = n - 1
                }
                print(str(n))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "sub" in ir_text and "i64" in ir_text or "add" in ir_text and "i64" in ir_text

    def test_nested_loop_mutation(self) -> None:
        """Mutable variable updated in nested loops."""
        source = textwrap.dedent("""\
            fn main() {
                let mut count: Int = 0
                for i in 0..3 {
                    for j in 0..3 {
                        count = count + 1
                    }
                }
                print(str(count))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "add i64" in ir_text or "add nsw i64" in ir_text

    def test_reassign_after_loop(self) -> None:
        """Variable used after loop should see final value."""
        source = textwrap.dedent("""\
            fn main() {
                let mut x: Int = 0
                for i in 0..5 {
                    x = x + 1
                }
                let y: Int = x + 100
                print(str(y))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        # Should reference x's alloca after the loop
        assert "add i64" in ir_text or "add nsw i64" in ir_text


# ===========================================================================
# Task 6: List accumulation via reassignment in loops
# ===========================================================================


class TestListAccumulationReassign:
    """Task 6 — list accumulation via reassignment in loops."""

    def test_list_push_in_loop(self) -> None:
        """let mut xs = []; for i in 0..3 { xs.push(i) } — push-based."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                for i in 0..3 {
                    xs.push(i)
                }
                print(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__mn_list_push" in ir_text

    def test_list_concat_reassign_in_loop(self) -> None:
        """let mut xs = []; for i in 0..3 { xs = xs + [i] } — concat reassignment."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                for i in 0..3 {
                    xs = xs + [i]
                }
                print(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_list_push_preserves_elements(self) -> None:
        """Push then index access — elements should be preserved."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = []
                xs.push(10)
                xs.push(20)
                xs.push(30)
                print(str(xs[0]))
                print(str(xs[1]))
                print(str(xs[2]))
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_list_push" in ir_text
        # v5.1.0 Perf.1: List<Int> indexing is now inline GEP, not __mn_list_get
        assert "getelementptr inbounds i64" in ir_text


# ===========================================================================
# v4.122.0 (Qs.1): List<Int> indexing in argument position emits `load i64`,
# not a raw pointer read. Before the fix, an empty list literal with an
# explicit annotation (`let arr: List<Int> = []`) lost its element type
# args on the Value, so IndexGet emitted `store ptr`/`load ptr` instead of
# `store i64`/`load i64`. The symptom was `print(str(arr[0]))` printing
# "<?>" (str() fell through to the placeholder for UNKNOWN) and
# `let v: Int = arr[0]` binding a ptrtoint'd heap pointer.
# ===========================================================================


class TestListIntIndexingQs1:
    """Qs.1 regression (v4.122.0) — `List<Int>` element access emits a
    proper `load i64` after `__mn_list_get`, not a raw pointer store/load."""

    def test_empty_literal_annotation_indexing_loads_i64(self) -> None:
        """`let arr: List<Int> = []; arr.push(42); print(str(arr[0]))`
        must produce a `load i64` instruction for the element access."""
        source = textwrap.dedent("""\
            fn main() {
                let mut arr: List<Int> = []
                arr.push(42)
                print(str(arr[0]))
            }
        """)
        ir_text = _to_ir(source)
        # v5.1.0 Perf.1: List<Int> indexing is now inline GEP, not __mn_list_get
        assert "getelementptr inbounds i64" in ir_text
        # The element must be dereferenced as i64 (not left as ptr).
        assert "load i64, ptr" in ir_text
        # The fallback "<?>" string must NOT appear — that means str()
        # saw an UNKNOWN-typed argument, which is the pre-fix symptom.
        assert '"<?>"' not in ir_text
        # The IndexGet result alloca must be typed i64, not ptr.
        # (The pre-fix IR had `%t5.a.N = alloca ptr`; post-fix is `alloca i64`.)
        assert "alloca i64" in ir_text

    def test_let_binding_from_index_is_i64(self) -> None:
        """`let v: Int = arr[0]` must not use `ptrtoint` to coerce a
        pointer to i64 — it must be a real `load i64` followed by a store."""
        source = textwrap.dedent("""\
            fn main() {
                let mut arr: List<Int> = []
                arr.push(42)
                let v: Int = arr[0]
                print(str(v))
            }
        """)
        ir_text = _to_ir(source)
        # v5.1.0 Perf.1: List<Int> indexing is now inline GEP
        assert "getelementptr inbounds i64" in ir_text
        assert "load i64, ptr" in ir_text
        # No ptrtoint should bridge an IndexGet result to an Int argument
        # passed to __mn_str_from_int. Pre-fix had `%p2i = ptrtoint ptr %el
        # to i64` immediately before a `__mn_str_from_int(i64 %p2i)` call.
        tail_after_ptrtoint = ir_text.split("ptrtoint")[-1].split("}")[0]
        assert "ptrtoint" not in ir_text or "__mn_str_from_int" not in tail_after_ptrtoint

    def test_index_in_arithmetic_uses_i64_operands(self) -> None:
        """`let sum: Int = arr[0] + arr[1]` must add two i64 loads,
        not two ptrtoint'd pointer values."""
        source = textwrap.dedent("""\
            fn main() {
                let mut arr: List<Int> = []
                arr.push(10)
                arr.push(32)
                let sum: Int = arr[0] + arr[1]
                print(str(sum))
            }
        """)
        ir_text = _to_ir(source)
        # v5.1.0 Perf.1: List<Int> indexing is now inline GEP
        assert "getelementptr inbounds i64" in ir_text
        # Two i64 loads (one per index), then an add on i64 operands.
        assert ir_text.count("load i64, ptr") >= 2
        assert "add nsw i64" in ir_text or "add i64" in ir_text
        # Pre-fix had `%p2i.86 = ptrtoint ptr %l.84 to i64` to coerce the
        # IndexGet result into an addable integer — the post-fix emits
        # real i64 loads and no ptrtoint is needed for this shape.
        assert "ptrtoint ptr" not in ir_text

    def test_float_list_empty_annotation_loads_double(self) -> None:
        """`List<Float>` with empty-literal + annotation must emit a
        `load double` for the element access — the lowerer fix must
        cover all primitive element types, not just Int."""
        source = textwrap.dedent("""\
            fn main() {
                let mut arr: List<Float> = []
                arr.push(3.14)
                print(str(arr[0]))
            }
        """)
        ir_text = _to_ir(source)
        # v5.1.0 Perf.1: List<Float> (8-byte elem) also uses inline GEP
        assert "getelementptr inbounds i64" in ir_text
        assert "load double, ptr" in ir_text
        assert '"<?>"' not in ir_text

    def test_struct_list_still_loads_correctly(self) -> None:
        """Regression guard: the fix must not break `List<MyStruct>` —
        the element slot must be loaded as the struct's inline type
        ({i64, i64} for a two-int struct), not stored/loaded as a raw
        `ptr`. The Pt struct is emitted as the anonymous aggregate
        {i64, i64}; indexing pts[0] must load that aggregate."""
        source = textwrap.dedent("""\
            struct Pt { x: Int, y: Int }

            fn main() {
                let mut pts: List<Pt> = []
                pts.push(new Pt { x: 1, y: 2 })
                print(str(pts[0].x))
            }
        """)
        ir_text = _to_ir(source)
        assert "__mn_list_get" in ir_text
        # The struct element must be loaded as a {i64, i64} aggregate
        # (inline struct repr). A raw `load ptr, ptr` here would be the
        # pre-fix symptom of dropped element type info.
        assert "load {i64, i64}, ptr" in ir_text
        assert '"<?>"' not in ir_text


# ===========================================================================
# Task 7: Emitter output comparison suite (10+ programs)
# ===========================================================================


class TestEmitterOutputSuite:
    """Task 7 — verify LLVM IR output for 10+ programs.

    Each test compiles a program and checks the IR contains
    the expected structural elements.
    """

    def test_hello_world(self) -> None:
        """Simple hello world program."""
        source = textwrap.dedent("""\
            fn main() {
                print("Hello, world!")
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "Hello, world!" in ir_text or "Hello" in ir_text

    def test_fibonacci(self) -> None:
        """Fibonacci function with recursion."""
        source = textwrap.dedent("""\
            fn fib(n: Int) -> Int {
                if n <= 1 {
                    return n
                }
                return fib(n - 1) + fib(n - 2)
            }

            fn main() {
                print(str(fib(10)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "fib" in ir_text
        # Recursive call
        assert "call" in ir_text

    def test_factorial(self) -> None:
        """Factorial function."""
        source = textwrap.dedent("""\
            fn factorial(n: Int) -> Int {
                if n <= 1 {
                    return 1
                }
                return n * factorial(n - 1)
            }

            fn main() {
                print(str(factorial(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "factorial" in ir_text
        assert "mul i64" in ir_text or "mul nsw i64" in ir_text

    def test_if_else(self) -> None:
        """If-else branching."""
        source = textwrap.dedent("""\
            fn classify(n: Int) -> String {
                if n > 0 {
                    return "positive"
                } else if n < 0 {
                    return "negative"
                } else {
                    return "zero"
                }
            }

            fn main() {
                print(classify(42))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "icmp" in ir_text
        assert "br" in ir_text

    def test_for_loop(self) -> None:
        """For loop with range."""
        source = textwrap.dedent("""\
            fn main() {
                for i in 0..10 {
                    print(str(i))
                }
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__mn_range" in ir_text or "__iter" in ir_text

    def test_match_expression(self) -> None:
        """Match expression with patterns."""
        source = textwrap.dedent("""\
            fn describe(n: Int) -> String {
                let result: String = match n {
                    0 => "zero",
                    1 => "one",
                    _ => "other"
                }
                return result
            }

            fn main() {
                print(describe(1))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "switch" in ir_text or "icmp" in ir_text

    def test_struct_creation(self) -> None:
        """Struct definition and field access."""
        source = textwrap.dedent("""\
            struct Point {
                x: Int,
                y: Int,
            }

            fn main() {
                let p: Point = Point(10, 20)
                print(str(p.x))
                print(str(p.y))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_enum_and_match(self) -> None:
        """Enum definition with pattern matching."""
        source = textwrap.dedent("""\
            enum Color {
                Red,
                Green,
                Blue,
            }

            fn name(c: Color) -> String {
                let result: String = match c {
                    Red => "red",
                    Green => "green",
                    Blue => "blue"
                }
                return result
            }

            fn main() {
                let c: Color = Color::Red
                print(name(c))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_list_operations(self) -> None:
        """List creation, push, and index access."""
        source = textwrap.dedent("""\
            fn main() {
                let mut xs: List<Int> = [1, 2, 3]
                xs.push(4)
                print(str(xs[0]))
                print(str(len(xs)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text
        assert "__mn_list" in ir_text

    def test_string_methods(self) -> None:
        """String method calls."""
        source = textwrap.dedent("""\
            fn main() {
                let s: String = "Hello, World!"
                print(str(len(s)))
                print(s.to_upper())
                print(s.to_lower())
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_result_type(self) -> None:
        """Result<T, E> construction and matching."""
        source = textwrap.dedent("""\
            fn divide(a: Int, b: Int) -> Result<Int, String> {
                if b == 0 {
                    return Err("division by zero")
                }
                return Ok(a / b)
            }

            fn main() {
                let r: Result<Int, String> = divide(10, 2)
                match r {
                    Ok(v) => { print(str(v)) },
                    Err(e) => { print(e) }
                }
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_closure(self) -> None:
        """Closure with captured variable."""
        source = textwrap.dedent("""\
            fn main() {
                let x: Int = 10
                let add_x = (n) => n + x
                print(str(add_x(5)))
            }
        """)
        ir_text = _to_ir(source)
        assert "define" in ir_text

    def test_multiple_functions(self) -> None:
        """Multiple function definitions and calls.

        v4.121.0: compiled at -O0 so the inliner does not collapse the
        two-line ``add``/``mul`` helpers into ``main`` and DCE them.
        At the test's previous default (O2) the optimizer eliminated
        both function definitions, leaving the IR with only ``main`` —
        a real win for codegen, but the assertion was written when the
        emitter still left the named definitions in place.
        """
        from mapanare.mir_opt import MIROptLevel as OptLevel

        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }

            fn mul(a: Int, b: Int) -> Int {
                return a * b
            }

            fn main() {
                let x: Int = add(3, 4)
                let y: Int = mul(x, 2)
                print(str(y))
            }
        """)
        ir_text = _compile_to_llvm_ir(source, "test.mn", opt_level=OptLevel.O0)
        assert "define" in ir_text
        assert "add" in ir_text
        assert "mul" in ir_text
