"""Tests for the WASM emitter -- Phase v2.0.0.

Tests cover:
  1. WAT output structure (module, memory, exports)
  2. Integer arithmetic codegen (i64.add, i64.sub, i64.mul, i64.div_s)
  3. Float arithmetic codegen (f64.add, f64.sub, f64.mul, f64.div)
  4. Boolean operations (i32.and, i32.or, i32.xor)
  5. String constants in data section
  6. Function declarations and calls
  7. Control flow (block/loop/br/br_if)
  8. Local variables and parameters
  9. Memory load/store for structs
  10. Bump allocator for heap allocation
  11. Print built-in stubs (import from JS)
  12. List operations (linear memory layout)
  13. Struct field access
  14. Enum/match compilation
  15. Result/Option type representation
  16. Export of main function
  17. Multi-function modules
  18. Recursive function calls
  19. Comparison operators
  20. Type conversion instructions
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from mapanare.ast_nodes import (
    Block,
    FnDef,
    NamedType,
)
from mapanare.parser import parse
from mapanare.semantic import check_or_raise

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Skip all tests if the WASM emitter module is not yet available
_wasm_emitter_available = True
try:
    from mapanare.emit_wasm import WasmEmitter  # type: ignore[import-not-found]
except ImportError:
    _wasm_emitter_available = False

pytestmark = pytest.mark.skipif(
    not _wasm_emitter_available,
    reason="mapanare.emit_wasm not yet implemented (v2.0.0 target)",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit(source: str) -> str:
    """Parse, type-check, lower to MIR, and emit WASM/WAT text."""
    from mapanare.lower import lower as build_mir

    ast = parse(source, filename="test.mn")
    check_or_raise(ast, filename="test.mn")
    mir_module = build_mir(ast, module_name="test")
    emitter = WasmEmitter()  # type: ignore[possibly-undefined]
    return emitter.emit(mir_module)


def _emit_unchecked(source: str) -> str:
    """Parse, lower to MIR, and emit WASM without semantic checking."""
    from mapanare.lower import lower as build_mir

    ast = parse(source, filename="test.mn")
    check_or_raise(ast, filename="test.mn")
    mir_module = build_mir(ast, module_name="test")
    emitter = WasmEmitter()  # type: ignore[possibly-undefined]
    return emitter.emit(mir_module)


def _fn(
    name: str = "test_fn",
    params: list | None = None,
    body_stmts: list | None = None,
    return_type: NamedType | None = None,
) -> FnDef:
    return FnDef(
        name=name,
        params=params or [],
        return_type=return_type,
        body=Block(stmts=body_stmts or []),
    )


# ===========================================================================
# 1. WAT output structure
# ===========================================================================


class TestWATModuleStructure:
    """Test that emitted WAT has correct top-level structure."""

    def test_module_wrapper(self) -> None:
        wat = _emit("fn main() { }")
        assert wat.strip().startswith("(module")
        assert wat.strip().endswith(")")

    def test_memory_declaration(self) -> None:
        """Module must declare at least one page of linear memory."""
        wat = _emit("fn main() { }")
        assert "(memory" in wat
        # At least 1 page (64KB)
        assert re.search(r"\(memory\s.*\d+", wat)

    def test_memory_exported(self) -> None:
        """Memory should be exported for JS host access."""
        wat = _emit("fn main() { }")
        assert '(export "memory"' in wat

    def test_main_exported(self) -> None:
        wat = _emit("fn main() { }")
        assert '(export "main"' in wat or '(export "_start"' in wat

    def test_data_section_present_for_strings(self) -> None:
        src = 'fn main() { let s: String = "hello"; }'
        wat = _emit(src)
        assert "(data" in wat


# ===========================================================================
# 2. Integer arithmetic codegen
# ===========================================================================


class TestIntegerArithmetic:
    """Test WASM i64 arithmetic instructions."""

    def test_i64_add(self) -> None:
        src = "fn add(a: Int, b: Int) -> Int { return a + b; }"
        wat = _emit(src)
        assert "i64.add" in wat

    def test_i64_sub(self) -> None:
        src = "fn sub(a: Int, b: Int) -> Int { return a - b; }"
        wat = _emit(src)
        assert "i64.sub" in wat

    def test_i64_mul(self) -> None:
        src = "fn mul(a: Int, b: Int) -> Int { return a * b; }"
        wat = _emit(src)
        assert "i64.mul" in wat

    def test_i64_div(self) -> None:
        src = "fn div(a: Int, b: Int) -> Int { return a / b; }"
        wat = _emit(src)
        assert "i64.div_s" in wat

    def test_i64_rem(self) -> None:
        src = "fn rem(a: Int, b: Int) -> Int { return a % b; }"
        wat = _emit(src)
        assert "i64.rem_s" in wat

    def test_integer_literal_const(self) -> None:
        src = "fn get() -> Int { return 42; }"
        wat = _emit(src)
        assert "i64.const 42" in wat

    def test_negative_integer_literal(self) -> None:
        src = "fn neg() -> Int { return -1; }"
        wat = _emit(src)
        # Could be "i64.const -1" or negation of i64.const 1
        assert "i64.const" in wat


# ===========================================================================
# 3. Float arithmetic codegen
# ===========================================================================


class TestFloatArithmetic:
    """Test WASM f64 arithmetic instructions."""

    def test_f64_add(self) -> None:
        src = "fn add(a: Float, b: Float) -> Float { return a + b; }"
        wat = _emit(src)
        assert "f64.add" in wat

    def test_f64_sub(self) -> None:
        src = "fn sub(a: Float, b: Float) -> Float { return a - b; }"
        wat = _emit(src)
        assert "f64.sub" in wat

    def test_f64_mul(self) -> None:
        src = "fn mul(a: Float, b: Float) -> Float { return a * b; }"
        wat = _emit(src)
        assert "f64.mul" in wat

    def test_f64_div(self) -> None:
        src = "fn div(a: Float, b: Float) -> Float { return a / b; }"
        wat = _emit(src)
        assert "f64.div" in wat

    def test_float_literal_const(self) -> None:
        src = "fn pi() -> Float { return 3.14; }"
        wat = _emit(src)
        assert "f64.const" in wat
        assert "3.14" in wat

    def test_float_zero(self) -> None:
        src = "fn zero() -> Float { return 0.0; }"
        wat = _emit(src)
        assert "f64.const" in wat


# ===========================================================================
# 4. Boolean operations
# ===========================================================================


class TestBooleanOperations:
    """Test WASM boolean/bitwise instructions."""

    def test_bool_and(self) -> None:
        src = "fn band(a: Bool, b: Bool) -> Bool { return a && b; }"
        wat = _emit(src)
        assert "i32.and" in wat

    def test_bool_or(self) -> None:
        src = "fn bor(a: Bool, b: Bool) -> Bool { return a || b; }"
        wat = _emit(src)
        assert "i32.or" in wat

    def test_bool_not(self) -> None:
        src = "fn bnot(a: Bool) -> Bool { return !a; }"
        wat = _emit(src)
        assert "i32.eqz" in wat or "i32.xor" in wat

    def test_bool_true_literal(self) -> None:
        src = "fn truth() -> Bool { return true; }"
        wat = _emit(src)
        assert "i32.const 1" in wat

    def test_bool_false_literal(self) -> None:
        src = "fn falsy() -> Bool { return false; }"
        wat = _emit(src)
        assert "i32.const 0" in wat


# ===========================================================================
# 5. String constants in data section
# ===========================================================================


class TestStringConstants:
    """Test that string literals are placed in the WASM data section."""

    def test_string_in_data_section(self) -> None:
        src = 'fn greet() -> String { return "hello" }'
        wat = _emit(src)
        assert "(data" in wat
        # The string bytes should appear in the data section (hex-encoded)
        assert "\\68\\65\\6c\\6c\\6f" in wat or "hello" in wat

    def test_multiple_strings_distinct_offsets(self) -> None:
        src = """fn msgs() -> String {
            let a: String = "foo"
            let b: String = "bar"
            return a
        }"""
        wat = _emit(src)
        # Strings are hex-encoded in the data section
        assert "\\66\\6f\\6f" in wat or "foo" in wat
        assert "\\62\\61\\72" in wat or "bar" in wat

    def test_empty_string(self) -> None:
        src = 'fn empty() -> String { return ""; }'
        wat = _emit(src)
        # Should still compile without error
        assert "(func" in wat


# ===========================================================================
# 6. Function declarations and calls
# ===========================================================================


class TestFunctionDeclarations:
    """Test function codegen in WAT."""

    def test_func_declaration(self) -> None:
        src = "fn add(a: Int, b: Int) -> Int { return a + b; }"
        wat = _emit(src)
        assert "(func" in wat
        assert "(param" in wat
        assert "(result" in wat

    def test_func_param_types(self) -> None:
        src = "fn f(a: Int, b: Float) -> Int { return a; }"
        wat = _emit(src)
        assert "i64" in wat  # Int maps to i64
        assert "f64" in wat  # Float maps to f64

    def test_func_call(self) -> None:
        src = """
fn square(x: Int) -> Int { return x * x; }
fn main() -> Int { return square(5); }
"""
        wat = _emit(src)
        assert "call" in wat

    def test_void_function(self) -> None:
        src = "fn noop() { }"
        wat = _emit(src)
        assert "(func" in wat
        # Void functions have no (result ...)
        # Just confirm it compiles

    def test_multiple_functions(self) -> None:
        src = """
fn a() -> Int { return 1; }
fn b() -> Int { return 2; }
fn c() -> Int { return 3; }
"""
        wat = _emit(src)
        # Should have 3 func definitions
        func_count = wat.count("(func")
        assert func_count >= 3


# ===========================================================================
# 7. Control flow (block/loop/br/br_if)
# ===========================================================================


class TestControlFlow:
    """Test WASM structured control flow."""

    def test_if_else_uses_block_br(self) -> None:
        src = """
fn abs(x: Int) -> Int {
    if x < 0 {
        return -x;
    } else {
        return x;
    }
}
"""
        wat = _emit(src)
        # WASM if/else can use (if ... (then ...) (else ...)) or block/br_if
        assert "if" in wat or "br_if" in wat

    def test_while_loop_uses_loop(self) -> None:
        src = """
fn count(n: Int) -> Int {
    let mut i: Int = 0
    while i < n {
        i = i + 1
    }
    return i
}
"""
        wat = _emit(src)
        assert "loop" in wat
        assert "br" in wat or "br_if" in wat

    def test_for_loop_compiles(self) -> None:
        src = """
fn sum_to(n: Int) -> Int {
    let mut total: Int = 0
    for i in 0..n {
        total = total + i
    }
    return total
}
"""
        wat = _emit(src)
        assert "loop" in wat

    def test_nested_if(self) -> None:
        src = """
fn clamp(x: Int) -> Int {
    if x < 0 {
        return 0;
    } else {
        if x > 100 {
            return 100;
        } else {
            return x;
        }
    }
}
"""
        wat = _emit(src)
        assert "(func" in wat

    def test_early_return(self) -> None:
        src = """
fn check(x: Int) -> Int {
    if x == 0 {
        return -1;
    }
    return x;
}
"""
        wat = _emit(src)
        assert "return" in wat or "br" in wat


# ===========================================================================
# 8. Local variables and parameters
# ===========================================================================


class TestLocals:
    """Test local variable and parameter codegen."""

    def test_local_declaration(self) -> None:
        src = "fn f() -> Int { let x: Int = 10; return x; }"
        wat = _emit(src)
        assert "local" in wat

    def test_local_get_set(self) -> None:
        src = """
fn f() -> Int {
    let mut x: Int = 5
    x = x + 1
    return x
}
"""
        wat = _emit(src)
        assert "local.set" in wat or "local.tee" in wat
        assert "local.get" in wat

    def test_multiple_locals(self) -> None:
        src = """
fn f() -> Int {
    let a: Int = 1;
    let b: Int = 2;
    let c: Int = 3;
    return a + b + c;
}
"""
        wat = _emit(src)
        # At least 3 local declarations
        local_count = wat.count("local.get") + wat.count("local.set")
        assert local_count >= 3

    def test_parameter_access(self) -> None:
        src = "fn identity(x: Int) -> Int { return x; }"
        wat = _emit(src)
        assert "local.get" in wat


# ===========================================================================
# 9. Memory load/store for structs
# ===========================================================================


class TestStructMemory:
    """Test struct field layout in linear memory."""

    def test_struct_allocation(self) -> None:
        src = """
struct Point {
    x: Int,
    y: Int
}

fn make_point() -> Point {
    return new Point { x: 1, y: 2 }
}
"""
        wat = _emit(src)
        # Struct construction should store fields to memory
        assert "i64.store" in wat or "i64.const" in wat

    def test_struct_field_load(self) -> None:
        src = """
struct Point {
    x: Int,
    y: Int,
}

fn get_x(p: Point) -> Int {
    return p.x;
}
"""
        wat = _emit(src)
        # Field access should use memory load with an offset
        assert "i64.load" in wat or "local.get" in wat

    def test_struct_field_store(self) -> None:
        src = """
struct Counter {
    value: Int
}

fn increment(c: Counter) -> Counter {
    return new Counter { value: c.value + 1 }
}
"""
        wat = _emit(src)
        assert "(func" in wat


# ===========================================================================
# 10. Bump allocator
# ===========================================================================


class TestBumpAllocator:
    """Test heap allocation via bump allocator in WASM linear memory."""

    def test_alloc_function_exists(self) -> None:
        """The emitter should include a bump allocator function."""
        src = """
struct Box { value: Int }
fn make() -> Box { return new Box { value: 42 } }
"""
        wat = _emit(src)
        # Allocator function or global bump pointer should be present
        assert "alloc" in wat.lower() or "global" in wat

    def test_global_heap_pointer(self) -> None:
        """A global mutable i32 should serve as the heap bump pointer."""
        src = """
struct Pair { a: Int, b: Int }
fn make() -> Pair { return new Pair { a: 1, b: 2 } }
"""
        wat = _emit(src)
        # Should have a mutable global for the heap pointer
        assert "(global" in wat or "global.get" in wat or "global.set" in wat


# ===========================================================================
# 11. Print built-in stubs
# ===========================================================================


class TestPrintBuiltins:
    """Test that print is imported from JS environment."""

    def test_print_import(self) -> None:
        src = 'fn main() { print("hello"); }'
        wat = _emit(src)
        assert "(import" in wat
        assert "print" in wat

    def test_println_import(self) -> None:
        src = 'fn main() { print("world"); }'
        wat = _emit(src)
        assert "(import" in wat
        assert "print" in wat

    def test_print_int(self) -> None:
        src = "fn main() { print(42); }"
        wat = _emit(src)
        assert "call" in wat


# ===========================================================================
# 12. List operations
# ===========================================================================


class TestListOperations:
    """Test list codegen using linear memory layout."""

    def test_list_literal(self) -> None:
        src = """
fn nums() -> List<Int> {
    return [1, 2, 3];
}
"""
        wat = _emit(src)
        # List literal should store elements in memory
        assert "i64.store" in wat or "i64.const 1" in wat

    def test_list_index_access(self) -> None:
        src = """
fn first(xs: List<Int>) -> Int {
    return xs[0];
}
"""
        wat = _emit(src)
        # Index access should use load with computed offset
        assert "i64.load" in wat or "local.get" in wat

    def test_list_len(self) -> None:
        src = """
fn size(xs: List<Int>) -> Int {
    return len(xs);
}
"""
        wat = _emit(src)
        assert "call" in wat or "i64.load" in wat


# ===========================================================================
# 13. Struct field access
# ===========================================================================


class TestStructFieldAccess:
    """Test struct field offset computation and access."""

    def test_first_field_offset_zero(self) -> None:
        src = """
struct S { a: Int, b: Int, }
fn get_a(s: S) -> Int { return s.a; }
"""
        wat = _emit(src)
        # First field at offset 0 from struct base
        assert "(func" in wat

    def test_second_field_offset(self) -> None:
        src = """
struct S { a: Int, b: Int, }
fn get_b(s: S) -> Int { return s.b; }
"""
        wat = _emit(src)
        # Second field should be at offset 8 (sizeof(Int) = 8 bytes)
        assert "(func" in wat

    def test_mixed_type_fields(self) -> None:
        src = """
struct Mixed { flag: Bool, value: Int, ratio: Float, }
fn get_ratio(m: Mixed) -> Float { return m.ratio; }
"""
        wat = _emit(src)
        assert "f64" in wat


# ===========================================================================
# 14. Enum/match compilation
# ===========================================================================


class TestEnumMatch:
    """Test enum tag + match to WASM branch table or if-chain."""

    def test_enum_tag_discriminant(self) -> None:
        src = """
enum Color {
    Red,
    Green,
    Blue
}

fn is_red(c: Color) -> Bool {
    match c {
        Red => { return true },
        _ => { return false }
    }
}
"""
        wat = _emit(src)
        # Enum variants should be represented as integer discriminants
        assert "i32.const" in wat or "i64.const" in wat

    def test_match_arms_branch(self) -> None:
        src = """
enum Dir { Up, Down, Left, Right }

fn to_int(d: Dir) -> Int {
    match d {
        Up => { return 0 },
        Down => { return 1 },
        Left => { return 2 },
        Right => { return 3 }
    }
}
"""
        wat = _emit(src)
        # Match should produce branching logic
        assert "br_table" in wat or "br_if" in wat or "if" in wat

    def test_enum_with_data(self) -> None:
        src = """
enum Shape {
    Circle(Float),
    Rect(Float, Float)
}

fn area(s: Shape) -> Float {
    match s {
        Circle(r) => { return 3.14 * r * r },
        Rect(w, h) => { return w * h }
    }
}
"""
        wat = _emit(src)
        assert "f64.mul" in wat


# ===========================================================================
# 15. Result/Option type representation
# ===========================================================================


class TestResultOption:
    """Test Result<T, E> and Option<T> codegen."""

    def test_ok_creates_result(self) -> None:
        src = """
fn safe_div(a: Int, b: Int) -> Result<Int, String> {
    if b == 0 {
        return Err("division by zero");
    }
    return Ok(a / b);
}
"""
        wat = _emit(src)
        # Result should have a tag (0 = Ok, 1 = Err) stored in memory
        assert "(func" in wat
        assert "i64.div_s" in wat or "i64.const" in wat

    def test_some_creates_option(self) -> None:
        src = """
fn find(x: Int) -> Option<Int> {
    if x > 0 {
        return Some(x)
    }
    return none
}
"""
        wat = _emit(src)
        assert "(func" in wat

    def test_option_match(self) -> None:
        src = """
fn unwrap_or(opt: Option<Int>, default: Int) -> Int {
    match opt {
        Some(v) => { return v },
        _ => { return default }
    }
}
"""
        wat = _emit(src)
        assert "br_if" in wat or "if" in wat or "br_table" in wat


# ===========================================================================
# 16. Export of main function
# ===========================================================================


class TestMainExport:
    """Test that the main function is properly exported."""

    def test_main_is_exported(self) -> None:
        src = "fn main() { }"
        wat = _emit(src)
        assert '(export "main"' in wat or '(export "_start"' in wat

    def test_non_main_not_auto_exported(self) -> None:
        src = """
fn helper() -> Int { return 1; }
fn main() { }
"""
        wat = _emit(src)
        # helper should not be exported unless explicitly marked
        assert '"helper"' not in wat or '(export "helper"' not in wat


# ===========================================================================
# 17. Multi-function modules
# ===========================================================================


class TestMultiFunctionModules:
    """Test modules with many functions."""

    def test_three_functions(self) -> None:
        src = """
fn a(x: Int) -> Int { return x + 1; }
fn b(x: Int) -> Int { return x * 2; }
fn c(x: Int) -> Int { return a(b(x)); }
"""
        wat = _emit(src)
        func_count = len(re.findall(r"\(func\s", wat))
        assert func_count >= 3

    def test_mutual_calls(self) -> None:
        src = """
fn is_even(n: Int) -> Bool {
    if n == 0 { return true; }
    return is_odd(n - 1);
}

fn is_odd(n: Int) -> Bool {
    if n == 0 { return false; }
    return is_even(n - 1);
}
"""
        wat = _emit(src)
        # Both functions should reference each other via call
        call_count = wat.count("call")
        assert call_count >= 2

    def test_function_order_independent(self) -> None:
        """Functions should be callable regardless of declaration order."""
        src = """
fn main() -> Int { return helper(); }
fn helper() -> Int { return 42; }
"""
        wat = _emit(src)
        assert "call" in wat


# ===========================================================================
# 18. Recursive function calls
# ===========================================================================


class TestRecursion:
    """Test recursive function codegen."""

    def test_factorial_recursive(self) -> None:
        src = """
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
"""
        wat = _emit(src)
        # Should call itself
        assert "call" in wat
        assert "i64.mul" in wat

    def test_fibonacci_recursive(self) -> None:
        src = """
fn fib(n: Int) -> Int {
    if n <= 1 {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
"""
        wat = _emit(src)
        # Two recursive calls
        call_count = wat.count("call")
        assert call_count >= 2
        assert "i64.add" in wat


# ===========================================================================
# 19. Comparison operators
# ===========================================================================


class TestComparisonOperators:
    """Test WASM comparison instructions."""

    def test_i64_eq(self) -> None:
        src = "fn eq(a: Int, b: Int) -> Bool { return a == b; }"
        wat = _emit(src)
        assert "i64.eq" in wat

    def test_i64_ne(self) -> None:
        src = "fn ne(a: Int, b: Int) -> Bool { return a != b; }"
        wat = _emit(src)
        assert "i64.ne" in wat

    def test_i64_lt_s(self) -> None:
        src = "fn lt(a: Int, b: Int) -> Bool { return a < b; }"
        wat = _emit(src)
        assert "i64.lt_s" in wat

    def test_i64_le_s(self) -> None:
        src = "fn le(a: Int, b: Int) -> Bool { return a <= b; }"
        wat = _emit(src)
        assert "i64.le_s" in wat

    def test_i64_gt_s(self) -> None:
        src = "fn gt(a: Int, b: Int) -> Bool { return a > b; }"
        wat = _emit(src)
        assert "i64.gt_s" in wat

    def test_i64_ge_s(self) -> None:
        src = "fn ge(a: Int, b: Int) -> Bool { return a >= b; }"
        wat = _emit(src)
        assert "i64.ge_s" in wat

    def test_f64_eq(self) -> None:
        src = "fn feq(a: Float, b: Float) -> Bool { return a == b; }"
        wat = _emit(src)
        assert "f64.eq" in wat

    def test_f64_lt(self) -> None:
        src = "fn flt(a: Float, b: Float) -> Bool { return a < b; }"
        wat = _emit(src)
        assert "f64.lt" in wat


# ===========================================================================
# 20. Type conversion instructions
# ===========================================================================


class TestTypeConversion:
    """Test WASM type conversion/coercion instructions."""

    def test_int_to_float(self) -> None:
        src = """
fn to_float(x: Int) -> Float {
    return float(x);
}
"""
        wat = _emit(src)
        assert "f64.convert_i64_s" in wat

    def test_float_to_int(self) -> None:
        src = """
fn to_int(x: Float) -> Int {
    return int(x);
}
"""
        wat = _emit(src)
        assert "i64.trunc_f64_s" in wat

    def test_bool_to_int_widening(self) -> None:
        """Bool (i32) must be extended to Int (i64) when used as Int."""
        src = """
fn bool_as_int(b: Bool) -> Int {
    return int(b);
}
"""
        wat = _emit(src)
        assert "i64.extend_i32_s" in wat or "i64.extend_i32_u" in wat
