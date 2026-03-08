"""Comprehensive tests for the Mapanare semantic checker."""

from __future__ import annotations

import pytest

from mapa.parser import parse
from mapa.semantic import (
    SemanticError,
    SemanticErrors,
    check,
    check_or_raise,
)


def _check(source: str, filename: str = "test.mn") -> list[SemanticError]:
    """Parse + semantic check, return errors."""
    program = parse(source, filename=filename)
    return check(program, filename=filename)


def _check_ok(source: str) -> None:
    """Assert that the source has no semantic errors."""
    errors = _check(source)
    assert errors == [], f"Expected no errors, got: {errors}"


def _check_err(source: str, expected_fragment: str) -> list[SemanticError]:
    """Assert at least one error contains the expected fragment."""
    errors = _check(source)
    assert errors, f"Expected errors but got none for:\n{source}"
    msgs = [e.message for e in errors]
    assert any(
        expected_fragment in m for m in msgs
    ), f"Expected error containing '{expected_fragment}', got: {msgs}"
    return errors


# ======================================================================
# Task 1: Variable scope analysis
# ======================================================================


class TestVariableScope:
    """Tests for variable scope analysis."""

    def test_let_binding_in_scope(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 42
                let y: Int = x
            }
        """
        )

    def test_nested_scope_access_outer(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 1
                if true {
                    let y: Int = x
                }
            }
        """
        )

    def test_nested_scope_no_leak(self) -> None:
        _check_err(
            """
            fn main() {
                if true {
                    let inner: Int = 1
                }
                let y: Int = inner
            }
            """,
            "Undefined variable 'inner'",
        )

    def test_for_loop_variable_scoped(self) -> None:
        _check_ok(
            """
            fn main() {
                for i in 0..10 {
                    let x: Int = i
                }
            }
        """
        )

    def test_for_loop_var_not_visible_outside(self) -> None:
        _check_err(
            """
            fn main() {
                for i in 0..10 {
                    let x: Int = 1
                }
                let y: Int = i
            }
            """,
            "Undefined variable 'i'",
        )

    def test_fn_params_in_scope(self) -> None:
        _check_ok(
            """
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """
        )

    def test_shadowing_allowed(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 1
                let x: Int = 2
            }
        """
        )

    def test_function_defined_after_use_ok(self) -> None:
        """Top-level functions should be available due to first-pass registration."""
        _check_ok(
            """
            fn main() {
                let x: Int = add(1, 2)
            }
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """
        )

    def test_lambda_params_scoped(self) -> None:
        _check_ok(
            """
            fn main() {
                let f = (x) => x
            }
        """
        )


# ======================================================================
# Task 2: Basic type inference
# ======================================================================


class TestTypeInference:
    """Tests for basic type inference from literals and annotations."""

    def test_int_literal_inferred(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = 42
            }
        """
        )

    def test_float_literal_inferred(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = 3.14
            }
        """
        )

    def test_string_literal_inferred(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = "hello"
            }
        """
        )

    def test_bool_literal_inferred(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = true
            }
        """
        )

    def test_type_annotation_used(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 42
            }
        """
        )

    def test_annotation_mismatch(self) -> None:
        _check_err(
            """
            fn main() {
                let x: Int = "hello"
            }
            """,
            "Type mismatch",
        )

    def test_arithmetic_result_type(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 1 + 2
            }
        """
        )

    def test_float_arithmetic(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = 1.0 + 2.0
            }
        """
        )

    def test_mixed_int_float_arithmetic(self) -> None:
        """Int + Float should yield Float."""
        _check_ok(
            """
            fn main() {
                let x = 1 + 2.0
            }
        """
        )

    def test_string_concat(self) -> None:
        _check_ok(
            """
            fn main() {
                let x = "a" + "b"
            }
        """
        )

    def test_comparison_yields_bool(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Bool = 1 < 2
            }
        """
        )

    def test_logical_yields_bool(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Bool = true && false
            }
        """
        )

    def test_function_return_type_inferred(self) -> None:
        _check_ok(
            """
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let y: Int = double(5)
            }
        """
        )

    def test_list_element_type(self) -> None:
        _check_ok(
            """
            fn main() {
                let xs = [1, 2, 3]
            }
        """
        )


# ======================================================================
# Task 3: Type checking for assignments and calls
# ======================================================================


class TestTypeChecking:
    """Tests for type checking on assignments and function calls."""

    def test_assign_type_mismatch(self) -> None:
        _check_err(
            """
            fn main() {
                let mut x: Int = 1
                x = "hello"
            }
            """,
            "Cannot assign",
        )

    def test_assign_immutable(self) -> None:
        _check_err(
            """
            fn main() {
                let x: Int = 1
                x = 2
            }
            """,
            "Cannot assign to immutable",
        )

    def test_assign_mutable_ok(self) -> None:
        _check_ok(
            """
            fn main() {
                let mut x: Int = 1
                x = 2
            }
        """
        )

    def test_call_arg_count_mismatch(self) -> None:
        _check_err(
            """
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn main() {
                let x = add(1)
            }
            """,
            "expects 2 argument(s), got 1",
        )

    def test_call_arg_type_mismatch(self) -> None:
        _check_err(
            """
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let x = double("hello")
            }
            """,
            "expects Int, got String",
        )

    def test_call_correct_args_ok(self) -> None:
        _check_ok(
            """
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn main() {
                let x = add(1, 2)
            }
        """
        )

    def test_arithmetic_on_bool_error(self) -> None:
        _check_err(
            """
            fn main() {
                let x = true + 1
            }
            """,
            "not supported",
        )

    def test_logical_on_int_error(self) -> None:
        _check_err(
            """
            fn main() {
                let x = 1 && 2
            }
            """,
            "requires Bool",
        )

    def test_negate_string_error(self) -> None:
        _check_err(
            """
            fn main() {
                let x = -"hello"
            }
            """,
            "not supported",
        )

    def test_not_int_error(self) -> None:
        _check_err(
            """
            fn main() {
                let x = !42
            }
            """,
            "requires Bool",
        )

    def test_if_condition_must_be_bool(self) -> None:
        _check_err(
            """
            fn main() {
                if 42 {
                    let x = 1
                }
            }
            """,
            "must be Bool",
        )


# ======================================================================
# Task 4: Undefined variable detection
# ======================================================================


class TestUndefinedVariable:
    """Tests for undefined variable detection."""

    def test_undefined_variable(self) -> None:
        _check_err(
            """
            fn main() {
                let x = y
            }
            """,
            "Undefined variable 'y'",
        )

    def test_undefined_function(self) -> None:
        _check_err(
            """
            fn main() {
                let x = foo(1)
            }
            """,
            "Undefined function 'foo'",
        )

    def test_builtin_print_defined(self) -> None:
        _check_ok(
            """
            fn main() {
                print("hello")
            }
        """
        )

    def test_defined_in_outer_scope(self) -> None:
        _check_ok(
            """
            fn main() {
                let x: Int = 1
                if true {
                    let y = x
                }
            }
        """
        )

    def test_multiple_undefined(self) -> None:
        errors = _check(
            """
            fn main() {
                let a = x
                let b = y
            }
        """
        )
        undefined_msgs = [e.message for e in errors if "Undefined" in e.message]
        assert len(undefined_msgs) >= 2

    def test_spawn_undefined_agent(self) -> None:
        _check_err(
            """
            fn main() {
                let a = spawn UnknownAgent()
            }
            """,
            "Undefined agent 'UnknownAgent'",
        )

    def test_spawn_non_agent_error(self) -> None:
        _check_err(
            """
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let a = spawn double()
            }
            """,
            "requires an agent",
        )


# ======================================================================
# Task 5: Agent input/output type validation
# ======================================================================


class TestAgentValidation:
    """Tests for agent input/output type validation."""

    def test_agent_inputs_outputs_valid(self) -> None:
        _check_ok(
            """
            agent Processor {
                input data: String
                output result: Int
                let mut count: Int = 0
            }
        """
        )

    def test_agent_method_can_access_state(self) -> None:
        _check_ok(
            """
            agent Counter {
                input tick: Int
                output value: Int
                let mut count: Int = 0

                fn process() {
                    let x = count
                }
            }
        """
        )

    def test_agent_spawn_ok(self) -> None:
        _check_ok(
            """
            agent Worker {
                input task: String
                output result: String
            }
            fn main() {
                let w = spawn Worker()
            }
        """
        )

    def test_send_wrong_type_to_agent_input(self) -> None:
        _check_err(
            """
            agent Worker {
                input task: String
                output result: Int
            }
            fn main() {
                let w = spawn Worker()
                w.task <- 42
            }
            """,
            "Cannot send Int to input 'task'",
        )

    def test_send_correct_type_ok(self) -> None:
        _check_ok(
            """
            agent Worker {
                input task: String
                output result: Int
            }
            fn main() {
                let w = spawn Worker()
                w.task <- "do work"
            }
        """
        )

    def test_agent_unknown_input_type_error(self) -> None:
        errors = _check(
            """
            agent Bad {
                input data: NonexistentType
                output result: Int
            }
        """
        )
        type_msgs = [e.message for e in errors if "Unknown type" in e.message]
        assert len(type_msgs) >= 1


# ======================================================================
# Task 6: Pipe connection type compatibility
# ======================================================================


class TestPipeCompatibility:
    """Tests for pipe connection type compatibility checks."""

    def test_pipe_compatible_types(self) -> None:
        _check_ok(
            """
            agent Tokenizer {
                input text: String
                output tokens: String
            }
            agent Classifier {
                input tokens: String
                output label: String
            }
            pipe Pipeline {
                Tokenizer |> Classifier
            }
        """
        )

    def test_pipe_incompatible_types(self) -> None:
        _check_err(
            """
            agent Tokenizer {
                input text: String
                output tokens: Int
            }
            agent Classifier {
                input tokens: String
                output label: String
            }
            pipe Pipeline {
                Tokenizer |> Classifier
            }
            """,
            "Pipe type mismatch",
        )

    def test_pipe_expression_type_check(self) -> None:
        _check_ok(
            """
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let result = 5 |> double
            }
        """
        )

    def test_pipe_expression_type_mismatch(self) -> None:
        _check_err(
            """
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let result = "hello" |> double
            }
            """,
            "Pipe type mismatch",
        )

    def test_pipe_undefined_stage(self) -> None:
        _check_err(
            """
            agent Tokenizer {
                input text: String
                output tokens: String
            }
            pipe Pipeline {
                Tokenizer |> UnknownStage
            }
            """,
            "Undefined stage 'UnknownStage'",
        )

    def test_pipe_with_functions(self) -> None:
        _check_ok(
            """
            fn parse_input(x: String) -> Int {
                return 0
            }
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn main() {
                let result = "42" |> parse_input |> double
            }
        """
        )


# ======================================================================
# Task 7: Error messages with file, line, column
# ======================================================================


class TestErrorMessages:
    """Tests that errors include file, line, and column information."""

    def test_error_has_filename(self) -> None:
        errors = _check(
            """
            fn main() {
                let x = undefined_var
            }
            """,
            filename="my_file.mn",
        )
        assert errors
        assert errors[0].filename == "my_file.mn"

    def test_error_has_line_number(self) -> None:
        errors = _check(
            """
            fn main() {
                let x = undefined_var
            }
        """
        )
        assert errors
        assert errors[0].line > 0

    def test_error_has_column(self) -> None:
        errors = _check(
            """
            fn main() {
                let x = undefined_var
            }
        """
        )
        assert errors
        assert errors[0].column > 0

    def test_error_str_format(self) -> None:
        errors = _check(
            """
            fn main() {
                let x = nope
            }
            """,
            filename="test.mn",
        )
        assert errors
        s = str(errors[0])
        assert "test.mn:" in s
        assert "Undefined" in s

    def test_check_or_raise_raises(self) -> None:
        program = parse(
            """
            fn main() {
                let x = nope
            }
        """
        )
        with pytest.raises(SemanticErrors) as exc_info:
            check_or_raise(program, filename="test.mn")
        assert len(exc_info.value.errors) >= 1

    def test_check_or_raise_no_errors(self) -> None:
        program = parse(
            """
            fn main() {
                let x: Int = 42
            }
        """
        )
        check_or_raise(program)  # Should not raise

    def test_multiple_errors_reported(self) -> None:
        errors = _check(
            """
            fn main() {
                let a = x
                let b = y
                let c = z
            }
        """
        )
        assert len(errors) >= 3


# ======================================================================
# Integration tests
# ======================================================================


class TestIntegration:
    """Integration tests combining multiple semantic features."""

    def test_full_program(self) -> None:
        _check_ok(
            """
            agent Doubler {
                input value: Int
                output result: Int
                let mut count: Int = 0

                fn process() {
                    let x: Int = 1
                }
            }

            fn add(a: Int, b: Int) -> Int {
                return a + b
            }

            fn main() {
                let d = spawn Doubler()
                d.value <- 42
                let x = add(1, 2)
                print("done")
            }
        """
        )

    def test_struct_and_enum(self) -> None:
        _check_ok(
            """
            struct Point {
                x: Float,
                y: Float
            }

            enum Shape {
                Circle(Float),
                Rect(Float, Float)
            }

            fn main() {
                let p = Point(1.0, 2.0)
                let s = Circle(5.0)
            }
        """
        )

    def test_match_with_patterns(self) -> None:
        _check_ok(
            """
            fn check(x: Int) -> Int {
                match x {
                    0 => 0,
                    n => n
                }
                return 0
            }
        """
        )

    def test_for_with_range(self) -> None:
        _check_ok(
            """
            fn main() {
                let mut sum: Int = 0
                for i in 0..10 {
                    sum = sum + 1
                }
            }
        """
        )

    def test_import_export(self) -> None:
        _check_ok(
            """
            import std::io
            fn main() {
                print("hello")
            }
        """
        )

    def test_type_alias(self) -> None:
        _check_ok(
            """
            type Name = String
            fn greet(n: Name) -> String {
                return n
            }
        """
        )


# =====================================================================
# Phase 5.1 — Tensor operator type checking
# =====================================================================


class TestTensorOps:
    """Tests for tensor operator type checking in semantic analysis."""

    def test_matmul_operator_parses(self) -> None:
        """The @ operator parses and type-checks with Tensor operands."""
        _check_ok(
            """
            fn dot(a: Tensor<Float>[3, 3], b: Tensor<Float>[3, 3]) -> Tensor<Float>[3, 3] {
                return a @ b
            }
        """
        )

    def test_tensor_add(self) -> None:
        """Element-wise + on tensors is valid."""
        _check_ok(
            """
            fn add(a: Tensor<Float>[3], b: Tensor<Float>[3]) -> Tensor<Float>[3] {
                return a + b
            }
        """
        )

    def test_tensor_sub(self) -> None:
        _check_ok(
            """
            fn sub(a: Tensor<Float>[3], b: Tensor<Float>[3]) -> Tensor<Float>[3] {
                return a - b
            }
        """
        )

    def test_tensor_mul(self) -> None:
        _check_ok(
            """
            fn mul(a: Tensor<Float>[3], b: Tensor<Float>[3]) -> Tensor<Float>[3] {
                return a * b
            }
        """
        )

    def test_tensor_div(self) -> None:
        _check_ok(
            """
            fn div(a: Tensor<Float>[3], b: Tensor<Float>[3]) -> Tensor<Float>[3] {
                return a / b
            }
        """
        )

    def test_tensor_scalar_mul(self) -> None:
        """Tensor * scalar is valid."""
        _check_ok(
            """
            fn scale(a: Tensor<Float>[3], s: Float) -> Tensor<Float>[3] {
                return a * s
            }
        """
        )


class TestCompileTimeShapeValidation:
    """Phase 5.1 — Compile-time tensor shape validation."""

    def test_matmul_valid_shapes(self) -> None:
        """(3,3) @ (3,3) is valid."""
        _check_ok(
            """
            fn mm(a: Tensor<Float>[3, 3], b: Tensor<Float>[3, 3]) -> Tensor<Float>[3, 3] {
                return a @ b
            }
        """
        )

    def test_matmul_compatible_shapes(self) -> None:
        """(2,3) @ (3,4) is valid."""
        _check_ok(
            """
            fn mm(a: Tensor<Float>[2, 3], b: Tensor<Float>[3, 4]) -> Tensor<Float>[2, 4] {
                return a @ b
            }
        """
        )

    def test_matmul_invalid_shapes(self) -> None:
        """(2,3) @ (4,5) should produce a shape mismatch error."""
        _check_err(
            """
            fn mm(a: Tensor<Float>[2, 3], b: Tensor<Float>[4, 5]) -> Tensor<Float>[2, 5] {
                return a @ b
            }
        """,
            "shape mismatch",
        )

    def test_elementwise_valid_shapes(self) -> None:
        """Element-wise ops with same shape are valid."""
        _check_ok(
            """
            fn add(a: Tensor<Float>[3, 3], b: Tensor<Float>[3, 3]) -> Tensor<Float>[3, 3] {
                return a + b
            }
        """
        )

    def test_elementwise_invalid_shapes(self) -> None:
        """Element-wise ops with different shapes produce error."""
        _check_err(
            """
            fn add(a: Tensor<Float>[2, 3], b: Tensor<Float>[3, 2]) -> Tensor<Float>[2, 3] {
                return a + b
            }
        """,
            "Shape mismatch",
        )

    def test_matmul_dot_product_shapes(self) -> None:
        """1D @ 1D dot product with matching dims is valid."""
        _check_ok(
            """
            fn dot(a: Tensor<Float>[4], b: Tensor<Float>[4]) -> Tensor<Float>[1] {
                return a @ b
            }
        """
        )

    def test_matmul_dot_product_mismatch(self) -> None:
        """1D @ 1D with different sizes is invalid."""
        _check_err(
            """
            fn dot(a: Tensor<Float>[3], b: Tensor<Float>[4]) -> Tensor<Float>[1] {
                return a @ b
            }
        """,
            "shape mismatch",
        )
