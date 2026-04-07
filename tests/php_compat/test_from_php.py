"""Tests for the PHP-to-Mapanare transpiler (mapanare.from_php)."""

from __future__ import annotations

from mapanare.from_php import translate_to_mn

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


class TestPhpFunctions:
    def test_basic_function(self) -> None:
        src = '<?php function greet(string $name): string { return "hello " . $name; }'
        mn = translate_to_mn(src, "<test>")
        assert "fn greet" in mn
        assert "String" in mn

    def test_typed_params(self) -> None:
        src = "<?php function add(int $a, int $b): int { return $a + $b; }"
        mn = translate_to_mn(src, "<test>")
        assert "Int" in mn
        assert "fn add" in mn

    def test_function_no_types(self) -> None:
        src = "<?php function foo($x, $y) { return $x + $y; }"
        mn = translate_to_mn(src, "<test>")
        assert "fn foo(x, y)" in mn
        assert "return" in mn

    def test_function_void_return(self) -> None:
        src = "<?php function say(string $msg): void { echo $msg; }"
        mn = translate_to_mn(src, "<test>")
        assert "fn say" in mn
        # Void return type should not appear in annotation
        assert "-> Void" not in mn


# ---------------------------------------------------------------------------
# Classes / Structs
# ---------------------------------------------------------------------------


class TestPhpClasses:
    def test_class_to_struct(self) -> None:
        src = "<?php class Point { public float $x; public float $y; }"
        mn = translate_to_mn(src, "<test>")
        assert "struct Point" in mn
        assert "Float" in mn

    def test_class_with_methods(self) -> None:
        src = """<?php
class Counter {
    public int $value;
    public function get(): int { return $this->value; }
    public function add(int $n): int { return $this->value + $n; }
}"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Counter" in mn
        assert "impl Counter" in mn
        assert "fn get(self)" in mn
        assert "fn add(self" in mn

    def test_class_with_constructor(self) -> None:
        src = """<?php
class Foo {
    public int $x;
    public function __construct(int $x) { $this->x = $x; }
    public function getX(): int { return $this->x; }
}"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Foo" in mn
        assert "fn getX(self)" in mn
        # Constructor should be skipped
        assert "__construct" not in mn


# ---------------------------------------------------------------------------
# Control Flow
# ---------------------------------------------------------------------------


class TestPhpControlFlow:
    def test_if_else(self) -> None:
        src = '<?php if ($x > 0) { echo "pos"; } else { echo "neg"; }'
        mn = translate_to_mn(src, "<test>")
        assert "if" in mn
        assert "else" in mn

    def test_elseif(self) -> None:
        src = """<?php
if ($x > 10) { echo "big"; }
elseif ($x > 0) { echo "small"; }
else { echo "neg"; }"""
        mn = translate_to_mn(src, "<test>")
        assert "else if" in mn

    def test_while_loop(self) -> None:
        src = "<?php while ($x > 0) { $x = $x - 1; }"
        mn = translate_to_mn(src, "<test>")
        assert "while" in mn

    def test_foreach(self) -> None:
        src = "<?php foreach ($items as $item) { echo $item; }"
        mn = translate_to_mn(src, "<test>")
        assert "for item in" in mn

    def test_foreach_key_value(self) -> None:
        src = "<?php foreach ($map as $k => $v) { echo $k; }"
        mn = translate_to_mn(src, "<test>")
        assert "for k in" in mn

    def test_for_loop_simple(self) -> None:
        src = "<?php for ($i = 0; $i < 10; $i++) { echo $i; }"
        mn = translate_to_mn(src, "<test>")
        assert "for i in 0..10" in mn

    def test_break_continue(self) -> None:
        src = """<?php
while (true) {
    if ($x == 5) { break; }
    if ($x == 3) { continue; }
}"""
        mn = translate_to_mn(src, "<test>")
        assert "break" in mn
        assert "continue" in mn


# ---------------------------------------------------------------------------
# Type Mapping
# ---------------------------------------------------------------------------


class TestPhpTypes:
    def test_type_mapping(self) -> None:
        src = "<?php function foo(int $a, float $b, string $c, bool $d): void { }"
        mn = translate_to_mn(src, "<test>")
        assert "Int" in mn
        assert "Float" in mn
        assert "String" in mn
        assert "Bool" in mn

    def test_nullable_type(self) -> None:
        src = "<?php function foo(?int $x): ?string { return null; }"
        mn = translate_to_mn(src, "<test>")
        assert "Option" in mn


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------


class TestPhpArrays:
    def test_numeric_array(self) -> None:
        src = "<?php $items = [1, 2, 3];"
        mn = translate_to_mn(src, "<test>")
        assert "[1, 2, 3]" in mn

    def test_assoc_array(self) -> None:
        src = '<?php $map = ["a" => 1, "b" => 2];'
        mn = translate_to_mn(src, "<test>")
        assert '"a"' in mn

    def test_empty_array(self) -> None:
        src = "<?php $items = [];"
        mn = translate_to_mn(src, "<test>")
        assert "[]" in mn


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------


class TestPhpStrings:
    def test_concat_operator(self) -> None:
        src = '<?php $x = "hello" . " world";'
        mn = translate_to_mn(src, "<test>")
        assert "+" in mn  # . becomes +

    def test_interpolation(self) -> None:
        src = '<?php $name = "Juan"; $msg = "hello $name";'
        mn = translate_to_mn(src, "<test>")
        assert "str(" in mn or "name" in mn

    def test_single_quoted(self) -> None:
        src = "<?php $x = 'hello world';"
        mn = translate_to_mn(src, "<test>")
        assert '"hello world"' in mn


# ---------------------------------------------------------------------------
# Echo / Print
# ---------------------------------------------------------------------------


class TestPhpEcho:
    def test_echo(self) -> None:
        src = '<?php echo "hello";'
        mn = translate_to_mn(src, "<test>")
        assert "print(" in mn

    def test_echo_variable(self) -> None:
        src = "<?php echo $x;"
        mn = translate_to_mn(src, "<test>")
        assert "print(x)" in mn


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------


class TestPhpOperators:
    def test_strict_equality(self) -> None:
        src = "<?php if ($x === $y) { echo 1; }"
        mn = translate_to_mn(src, "<test>")
        assert "==" in mn
        assert "===" not in mn

    def test_strict_inequality(self) -> None:
        src = "<?php if ($x !== $y) { echo 1; }"
        mn = translate_to_mn(src, "<test>")
        assert "!=" in mn
        assert "!==" not in mn

    def test_null_literal(self) -> None:
        src = "<?php $x = null;"
        mn = translate_to_mn(src, "<test>")
        assert "None" in mn

    def test_boolean_literals(self) -> None:
        src = "<?php $a = true; $b = false;"
        mn = translate_to_mn(src, "<test>")
        assert "true" in mn
        assert "false" in mn


# ---------------------------------------------------------------------------
# Standard Library Mapping
# ---------------------------------------------------------------------------


class TestPhpStdlib:
    def test_strlen(self) -> None:
        src = "<?php $n = strlen($s);"
        mn = translate_to_mn(src, "<test>")
        assert "len(" in mn

    def test_count(self) -> None:
        src = "<?php $n = count($arr);"
        mn = translate_to_mn(src, "<test>")
        assert "len(" in mn

    def test_intval(self) -> None:
        src = "<?php $n = intval($s);"
        mn = translate_to_mn(src, "<test>")
        assert "int(" in mn

    def test_abs(self) -> None:
        src = "<?php $n = abs($x);"
        mn = translate_to_mn(src, "<test>")
        assert "abs(" in mn


# ---------------------------------------------------------------------------
# Casts
# ---------------------------------------------------------------------------


class TestPhpCasts:
    def test_int_cast(self) -> None:
        src = "<?php $n = (int)$x;"
        mn = translate_to_mn(src, "<test>")
        assert "int(" in mn

    def test_string_cast(self) -> None:
        src = "<?php $s = (string)$x;"
        mn = translate_to_mn(src, "<test>")
        assert "str(" in mn


# ---------------------------------------------------------------------------
# New / Constructor
# ---------------------------------------------------------------------------


class TestPhpNew:
    def test_new_object(self) -> None:
        src = "<?php $p = new Point(1, 2);"
        mn = translate_to_mn(src, "<test>")
        assert "Point(1, 2)" in mn
        assert "new" not in mn.split("//")[0].split("Translated")[0]  # not in code part


# ---------------------------------------------------------------------------
# Arrow Functions
# ---------------------------------------------------------------------------


class TestPhpArrowFn:
    def test_arrow_function(self) -> None:
        src = "<?php $add = fn($x, $y) => $x + $y;"
        mn = translate_to_mn(src, "<test>")
        assert "=>" in mn
        assert "x" in mn
        assert "y" in mn


# ---------------------------------------------------------------------------
# Unsupported Constructs
# ---------------------------------------------------------------------------


class TestPhpUnsupported:
    def test_include_warns(self) -> None:
        src = '<?php include "other.php";'
        mn = translate_to_mn(src, "<test>")
        assert "not supported" in mn.lower() or "//" in mn

    def test_try_catch(self) -> None:
        src = """<?php
try { $x = 1; }
catch (Exception $e) { $x = 0; }"""
        mn = translate_to_mn(src, "<test>")
        assert "// try" in mn

    def test_namespace(self) -> None:
        src = "<?php namespace App\\Models;"
        mn = translate_to_mn(src, "<test>")
        assert "//" in mn


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class TestPhpAssignments:
    def test_let_declaration(self) -> None:
        src = "<?php $x = 5;"
        mn = translate_to_mn(src, "<test>")
        assert "let mut x" in mn
        assert "5" in mn

    def test_reassignment(self) -> None:
        src = "<?php $x = 5; $x = 10;"
        mn = translate_to_mn(src, "<test>")
        assert "let mut x" in mn
        # Second assignment should not have let
        lines = [line.strip() for line in mn.split("\n") if "= 10" in line]
        assert lines
        assert not lines[0].startswith("let")

    def test_augmented_assignment(self) -> None:
        src = "<?php $x = 0; $x += 5;"
        mn = translate_to_mn(src, "<test>")
        assert "x = x + 5" in mn

    def test_increment(self) -> None:
        src = "<?php $x = 0; $x++;"
        mn = translate_to_mn(src, "<test>")
        assert "x = x + 1" in mn


# ---------------------------------------------------------------------------
# End-to-end: complex examples
# ---------------------------------------------------------------------------


class TestPhpEndToEnd:
    def test_fizzbuzz(self) -> None:
        src = """<?php
function fizzbuzz(int $n): string {
    if ($n % 15 === 0) { return "FizzBuzz"; }
    elseif ($n % 3 === 0) { return "Fizz"; }
    elseif ($n % 5 === 0) { return "Buzz"; }
    return strval($n);
}

function main(): void {
    for ($i = 1; $i < 16; $i++) {
        echo fizzbuzz($i);
    }
}"""
        mn = translate_to_mn(src, "<test>")
        assert "fn fizzbuzz" in mn
        assert "fn main" in mn
        assert "% 15" in mn
        assert "str(" in mn

    def test_fibonacci(self) -> None:
        src = """<?php
function fib(int $n): int {
    if ($n <= 1) { return $n; }
    return fib($n - 1) + fib($n - 2);
}

function main(): void {
    echo strval(fib(10));
}"""
        mn = translate_to_mn(src, "<test>")
        assert "fn fib" in mn
        assert "fn main" in mn
        assert "fib(" in mn

    def test_class_with_method_call(self) -> None:
        src = """<?php
class Greeter {
    public string $name;
    public function greet(): string {
        return "Hello, " . $this->name;
    }
}"""
        mn = translate_to_mn(src, "<test>")
        assert "struct Greeter" in mn
        assert "impl Greeter" in mn
        assert "fn greet(self)" in mn


# ---------------------------------------------------------------------------
# Header comment
# ---------------------------------------------------------------------------


class TestPhpHeader:
    def test_header_comment(self) -> None:
        src = "<?php echo 1;"
        mn = translate_to_mn(src, "<test>")
        assert "// Translated from" in mn
        assert "mapanare transpile" in mn
