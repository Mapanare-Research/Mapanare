"""Tests for the Python-to-Mapanare transpiler (mapanare.from_python)."""

from __future__ import annotations

import pytest

from mapanare.from_python import TranslateError, translate_to_mn

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


class TestFunctions:
    def test_basic_function(self) -> None:
        src = """
def greet(name: str) -> str:
    return "hello " + name
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn greet" in mn
        assert "String" in mn
        assert 'return ("hello " + name)' in mn

    def test_function_no_annotations(self) -> None:
        src = """
def add(a, b):
    return a + b
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn add(a: Int, b: Int)" in mn
        assert "return (a + b)" in mn

    def test_function_int_params(self) -> None:
        src = """
def multiply(x: int, y: int) -> int:
    return x * y
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn multiply(x: Int, y: Int) -> Int" in mn


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------


class TestTypeMapping:
    def test_all_basic_types(self) -> None:
        src = """
def foo(a: int, b: float, c: str, d: bool) -> int:
    return a
"""
        mn = translate_to_mn(src, "<test>")
        assert "Int" in mn
        assert "Float" in mn
        assert "String" in mn
        assert "Bool" in mn

    def test_list_type(self) -> None:
        src = """
def process(items: list[int]) -> int:
    return 0
"""
        mn = translate_to_mn(src, "<test>")
        assert "List<Int>" in mn

    def test_dict_type(self) -> None:
        src = """
def lookup(data: dict[str, int]) -> int:
    return 0
"""
        mn = translate_to_mn(src, "<test>")
        assert "Map<String, Int>" in mn


# ---------------------------------------------------------------------------
# Classes / Structs
# ---------------------------------------------------------------------------


class TestClasses:
    def test_class_to_struct(self) -> None:
        src = """
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Point" in mn
        assert "x: Float" in mn
        assert "y: Float" in mn

    def test_class_with_methods(self) -> None:
        src = """
class Counter:
    def __init__(self, value: int):
        self.value = value

    def get(self) -> int:
        return self.value

    def add(self, n: int) -> int:
        return self.value + n
"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Counter" in mn
        assert "impl Counter" in mn
        assert "fn get(self) -> Int" in mn
        assert "fn add(self, n: Int) -> Int" in mn

    def test_class_annotated_fields(self) -> None:
        src = """
class Config:
    name: str
    value: int
"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Config" in mn
        assert "name: String" in mn
        assert "value: Int" in mn


# ---------------------------------------------------------------------------
# Control flow
# ---------------------------------------------------------------------------


class TestControlFlow:
    def test_if_else(self) -> None:
        src = """
def check(x: int) -> str:
    if x > 10:
        return "big"
    else:
        return "small"
"""
        mn = translate_to_mn(src, "<test>")
        assert "if (x > 10)" in mn
        assert "} else {" in mn
        assert 'return "big"' in mn
        assert 'return "small"' in mn

    def test_elif(self) -> None:
        src = """
def grade(score: int) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    else:
        return "C"
"""
        mn = translate_to_mn(src, "<test>")
        assert "if (score >= 90)" in mn
        assert "} else if (score >= 80) {" in mn
        assert "} else {" in mn

    def test_for_range(self) -> None:
        src = """
def count() -> int:
    total = 0
    for i in range(10):
        total = total + i
    return total
"""
        mn = translate_to_mn(src, "<test>")
        assert "for i in 0..10" in mn
        assert "total = (total + i)" in mn

    def test_for_range_start_end(self) -> None:
        src = """
def count_from(start: int, end: int):
    for i in range(start, end):
        print(i)
"""
        mn = translate_to_mn(src, "<test>")
        assert "for i in start..end" in mn

    def test_while_loop(self) -> None:
        src = """
def countdown(n: int):
    while n > 0:
        n = n - 1
"""
        mn = translate_to_mn(src, "<test>")
        assert "while (n > 0)" in mn

    def test_break_continue(self) -> None:
        src = """
def search(items: list[int]) -> int:
    for i in range(10):
        if i == 5:
            break
        if i == 3:
            continue
    return 0
"""
        mn = translate_to_mn(src, "<test>")
        assert "break" in mn
        assert "continue" in mn


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


class TestExpressions:
    def test_binary_ops(self) -> None:
        src = """
def math(a: int, b: int) -> int:
    return a + b * 2 - 1
"""
        mn = translate_to_mn(src, "<test>")
        assert "return" in mn
        # The expression should contain the operators
        assert "+" in mn
        assert "*" in mn
        assert "-" in mn

    def test_comparison(self) -> None:
        src = """
def check(x: int) -> bool:
    return x >= 10 and x < 100
"""
        mn = translate_to_mn(src, "<test>")
        assert ">=" in mn
        assert "<" in mn
        assert "&&" in mn

    def test_string_literal(self) -> None:
        src = """
def hello() -> str:
    return "hello world"
"""
        mn = translate_to_mn(src, "<test>")
        assert '"hello world"' in mn

    def test_int_literal(self) -> None:
        src = """
x = 42
"""
        mn = translate_to_mn(src, "<test>")
        assert "42" in mn

    def test_float_literal(self) -> None:
        src = """
pi = 3.14
"""
        mn = translate_to_mn(src, "<test>")
        assert "3.14" in mn

    def test_bool_literals(self) -> None:
        src = """
def flags():
    a = True
    b = False
"""
        mn = translate_to_mn(src, "<test>")
        assert "true" in mn
        assert "false" in mn

    def test_list_literal(self) -> None:
        src = """
items = [1, 2, 3]
"""
        mn = translate_to_mn(src, "<test>")
        assert "[1, 2, 3]" in mn

    def test_lambda(self) -> None:
        src = """
add = lambda x, y: x + y
"""
        mn = translate_to_mn(src, "<test>")
        assert "(x, y) => (x + y)" in mn

    def test_unary_ops(self) -> None:
        src = """
def negate(x: int) -> int:
    return -x
"""
        mn = translate_to_mn(src, "<test>")
        assert "-x" in mn

    def test_fstring(self) -> None:
        src = """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
        mn = translate_to_mn(src, "<test>")
        # f-string becomes concatenation
        assert '"Hello, "' in mn
        assert "str(name)" in mn
        assert "+" in mn


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class TestAssignments:
    def test_let_with_type_inference(self) -> None:
        src = """
def f():
    x = 5
"""
        mn = translate_to_mn(src, "<test>")
        assert "let mut x: Int = 5" in mn

    def test_reassignment(self) -> None:
        src = """
def f():
    x = 5
    x = 10
"""
        mn = translate_to_mn(src, "<test>")
        assert "let mut x: Int = 5" in mn
        assert "    x = 10" in mn  # No let on reassignment

    def test_annotated_assignment(self) -> None:
        src = """
def f():
    x: int = 42
"""
        mn = translate_to_mn(src, "<test>")
        assert "let mut x: Int = 42" in mn

    def test_augmented_assignment(self) -> None:
        src = """
def f():
    x = 0
    x += 5
"""
        mn = translate_to_mn(src, "<test>")
        assert "x = x + 5" in mn


# ---------------------------------------------------------------------------
# Call expressions
# ---------------------------------------------------------------------------


class TestCalls:
    def test_print(self) -> None:
        src = """
print("hello")
"""
        mn = translate_to_mn(src, "<test>")
        assert 'print("hello")' in mn

    def test_len(self) -> None:
        src = """
def f(items: list[int]) -> int:
    return len(items)
"""
        mn = translate_to_mn(src, "<test>")
        assert "len(items)" in mn

    def test_method_mapping(self) -> None:
        src = """
def f():
    items = [1, 2, 3]
    items.append(4)
"""
        mn = translate_to_mn(src, "<test>")
        # append → push
        assert "items.push(4)" in mn

    def test_string_method_mapping(self) -> None:
        src = """
def f(s: str) -> str:
    return s.upper()
"""
        mn = translate_to_mn(src, "<test>")
        assert "s.to_upper()" in mn


# ---------------------------------------------------------------------------
# Global code → fn main()
# ---------------------------------------------------------------------------


class TestMainGeneration:
    def test_global_stmts_become_main(self) -> None:
        src = """
x = 42
print(x)
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn main()" in mn
        assert "print(x)" in mn

    def test_no_double_main(self) -> None:
        src = """
def main():
    print("hello")
"""
        mn = translate_to_mn(src, "<test>")
        # Only one main
        assert mn.count("fn main") == 1


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


class TestImports:
    def test_import_becomes_comment(self) -> None:
        src = """
import os
from sys import argv
"""
        mn = translate_to_mn(src, "<test>")
        assert "// import os" in mn
        assert "// from sys import argv" in mn


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrors:
    def test_syntax_error(self) -> None:
        with pytest.raises(TranslateError, match="Python syntax error"):
            translate_to_mn("def (broken", "<test>")

    def test_isinstance_error(self) -> None:
        src = """
def f(x):
    isinstance(x, int)
"""
        with pytest.raises(TranslateError, match="isinstance"):
            translate_to_mn(src, "<test>")


# ---------------------------------------------------------------------------
# Unsupported constructs
# ---------------------------------------------------------------------------


class TestUnsupported:
    def test_try_except_becomes_comment(self) -> None:
        src = """
def f():
    try:
        x = 1
    except Exception as e:
        x = 0
"""
        mn = translate_to_mn(src, "<test>")
        assert "// try" in mn

    def test_with_becomes_comment(self) -> None:
        src = """
def f():
    with open("file.txt") as f:
        pass
"""
        mn = translate_to_mn(src, "<test>")
        assert "// with" in mn

    def test_raise_becomes_err(self) -> None:
        src = """
def f():
    raise ValueError("bad")
"""
        mn = translate_to_mn(src, "<test>")
        assert "Err(" in mn


# ---------------------------------------------------------------------------
# End-to-end: complex examples
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_fizzbuzz(self) -> None:
        src = """
def fizzbuzz(n: int) -> str:
    if n % 15 == 0:
        return "FizzBuzz"
    elif n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    return str(n)

def main():
    for i in range(1, 16):
        print(fizzbuzz(i))
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn fizzbuzz(n: Int) -> String" in mn
        assert "fn main()" in mn
        assert "for i in 1..16" in mn
        assert "% 15" in mn
        assert "} else if ((n % 3) == 0) {" in mn

    def test_fibonacci(self) -> None:
        src = """
def fib(n: int) -> int:
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

def main():
    print(str(fib(10)))
"""
        mn = translate_to_mn(src, "<test>")
        assert "fn fib(n: Int) -> Int" in mn
        assert "fib((n - 1))" in mn
        assert "fn main()" in mn

    def test_linked_list_class(self) -> None:
        src = """
class Node:
    def __init__(self, value: int):
        self.value = value
        self.next = None

    def get_value(self) -> int:
        return self.value
"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Node" in mn
        assert "value: Int" in mn
        assert "impl Node" in mn
        assert "fn get_value(self) -> Int" in mn
