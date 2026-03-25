"""Phase 1 — encoding/toml.mn — TOML v1.0 Parser/Serializer tests.

Tests verify that the TOML stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the TOML module source code within test programs.

Covers:
  - Core types: TomlValue enum, TomlError struct
  - Parse all value types: string, int, float, bool, datetime, array, table
  - Dotted keys, nested tables, array of tables
  - Multi-line strings (basic + literal)
  - Encode → decode round-trip
  - Error cases: duplicate keys, invalid input
  - Inline tables
  - Hex/octal/binary integers
  - Special floats (inf, nan)
  - Typed getters (get_string, get_int, get_float, get_bool)
  - Pretty-print serializer
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Read the TOML module source once
_TOML_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "toml.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_toml.mn", use_mir=True)


def _toml_source_with_main(main_body: str) -> str:
    """Prepend the TOML module source and wrap main_body in fn main()."""
    return _TOML_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_toml_value_enum_compiles(self) -> None:
        """TomlValue enum (with Table and Array variants) compiles."""
        src = _toml_source_with_main("""\
            let v: TomlValue = Str("hello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_error_struct_compiles(self) -> None:
        """TomlError struct compiles."""
        src = _toml_source_with_main("""\
            let e: TomlError = new TomlError { message: "test", line: 1, col: 1 }
            println(e.message)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_int_variant(self) -> None:
        """TomlValue::Int variant compiles."""
        src = _toml_source_with_main("""\
            let v: TomlValue = Int(42)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_float_variant(self) -> None:
        """TomlValue::Float variant compiles."""
        src = _toml_source_with_main("""\
            let v: TomlValue = Float(3.14)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_bool_variant(self) -> None:
        """TomlValue::Bool variant compiles."""
        src = _toml_source_with_main("""\
            let v: TomlValue = Bool(true)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_datetime_variant(self) -> None:
        """TomlValue::DateTime variant compiles."""
        src = _toml_source_with_main("""\
            let v: TomlValue = DateTime("2024-01-15T10:30:00Z")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_array_variant(self) -> None:
        """TomlValue::Array variant compiles."""
        src = _toml_source_with_main("""\
            let items: List<TomlValue> = [Int(1), Int(2)]
            let v: TomlValue = Array(items)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_toml_value_table_variant(self) -> None:
        """TomlValue::Table variant compiles."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let v: TomlValue = Table(entries)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Character classification helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCharHelpers:
    def test_is_toml_digit(self) -> None:
        """Digit classification helper compiles."""
        src = _toml_source_with_main("""\
            let r: Bool = is_toml_digit("5")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_hex(self) -> None:
        """Hex classification helper compiles."""
        src = _toml_source_with_main("""\
            let r: Bool = is_hex("a")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_bare_key_char(self) -> None:
        """Bare key char classification compiles."""
        src = _toml_source_with_main("""\
            let r: Bool = is_bare_key_char("k")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_octal_digit(self) -> None:
        """Octal digit classification compiles."""
        src = _toml_source_with_main("""\
            let r: Bool = is_octal_digit("7")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_binary_digit(self) -> None:
        """Binary digit classification compiles."""
        src = _toml_source_with_main("""\
            let r: Bool = is_binary_digit("1")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Whitespace and comment handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWhitespace:
    def test_skip_ws_compiles(self) -> None:
        """skip_ws function compiles."""
        src = _toml_source_with_main("""\
            let r: ParseState = skip_ws("  hello", 0, 1, 1)
            println(str(r.pos))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_skip_ws_and_comments_compiles(self) -> None:
        """skip_ws_and_comments function compiles."""
        src = _toml_source_with_main("""\
            let r: ParseState = skip_ws_and_comments("  # comment", 0, 1, 1)
            println(str(r.pos))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_skip_ws_comments_newlines_compiles(self) -> None:
        """skip_ws_comments_newlines function compiles."""
        src = _toml_source_with_main("""\
            let r: ParseState = skip_ws_comments_newlines("  \\n  hello", 0, 1, 1)
            println(str(r.pos))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# String parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStringParsing:
    def test_parse_basic_string(self) -> None:
        """Parse a basic TOML string."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_basic_string("\\"hello\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_char_at" in ir_out

    def test_parse_basic_string_with_escapes(self) -> None:
        """Parse basic string with escape sequences."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_basic_string("\\"line1\\\\nline2\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_literal_string(self) -> None:
        """Parse a literal string (no escapes)."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_literal_string("'raw \\\\string'", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Multi-line strings
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMultiLineStrings:
    def test_parse_ml_basic_string_compiles(self) -> None:
        """Multi-line basic string parser compiles."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_ml_basic_string("\\"\\"\\"\\nhello\\nworld\\"\\"\\"\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_ml_literal_string_compiles(self) -> None:
        """Multi-line literal string parser compiles."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_ml_literal_string("'''\\nhello\\nworld'''", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_toml_string_dispatch(self) -> None:
        """String dispatch function routes to correct parser."""
        src = _toml_source_with_main("""\
            let r: StringParseResult = parse_toml_string("\\"test\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Key parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestKeyParsing:
    def test_parse_bare_key(self) -> None:
        """Parse a bare key."""
        src = _toml_source_with_main("""\
            let r: KeyResult = parse_bare_key("my-key = 1", 0, 1, 1)
            println(r.key)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_simple_key_quoted(self) -> None:
        """Parse a quoted key."""
        src = _toml_source_with_main("""\
            let r: KeyResult = parse_simple_key("\\"complex key\\" = 1", 0, 1, 1)
            println(r.key)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_dotted_key(self) -> None:
        """Parse a dotted key (a.b.c)."""
        src = _toml_source_with_main("""\
            let r: DottedKeyResult = parse_dotted_key("a.b.c = 1", 0, 1, 1)
            println(str(len(r.keys)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Number parsing: decimal integers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestNumberParsing:
    def test_parse_integer(self) -> None:
        """Parse a decimal integer."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("42", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_negative_integer(self) -> None:
        """Parse a negative integer."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("-7", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_positive_integer(self) -> None:
        """Parse a positive integer with explicit + sign."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("+99", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_integer_with_underscores(self) -> None:
        """Parse integer with underscore separators."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("1_000_000", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_float(self) -> None:
        """Parse a float with decimal point."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("3.14", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_float_exponent(self) -> None:
        """Parse a float with exponent."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("2.5e10", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_float_negative_exponent(self) -> None:
        """Parse a float with negative exponent."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("5e-3", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Hex, octal, binary integers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestIntegerBases:
    def test_parse_hex_integer(self) -> None:
        """Parse a hexadecimal integer (0xDEAD)."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("0xDEAD", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_hex_with_underscores(self) -> None:
        """Parse hex integer with underscore separators."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("0xdead_beef", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_octal_integer(self) -> None:
        """Parse an octal integer (0o755)."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("0o755", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_binary_integer(self) -> None:
        """Parse a binary integer (0b1010)."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("0b1010", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_binary_with_underscores(self) -> None:
        """Parse binary integer with underscore separators."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("0b1111_0000", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Special floats: inf, nan
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSpecialFloats:
    def test_parse_inf(self) -> None:
        """Parse inf value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("inf", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_positive_inf(self) -> None:
        """Parse +inf value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("+inf", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_negative_inf(self) -> None:
        """Parse -inf value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("-inf", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_nan(self) -> None:
        """Parse nan value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("nan", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_positive_nan(self) -> None:
        """Parse +nan value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("+nan", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_negative_nan(self) -> None:
        """Parse -nan value."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_number("-nan", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Value parser (dispatch)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestValueParsing:
    def test_parse_string_value(self) -> None:
        """Parse a string value via top-level dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("\\"hello\\"", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_bool_true(self) -> None:
        """Parse true boolean via value dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("true", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_bool_false(self) -> None:
        """Parse false boolean via value dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("false", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_integer_value(self) -> None:
        """Parse integer via value dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("42", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_float_value(self) -> None:
        """Parse float via value dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("3.14", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_datetime_value(self) -> None:
        """Parse datetime via value dispatch."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_value("2024-01-15T10:30:00Z", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Array parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestArrayParsing:
    def test_decode_empty_array(self) -> None:
        """Parse empty TOML array."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_array("[]", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_of_ints(self) -> None:
        """Parse array of integers."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_array("[1, 2, 3]", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_of_strings(self) -> None:
        """Parse array of strings."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_array("[\\"a\\", \\"b\\", \\"c\\"]", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_array(self) -> None:
        """Parse nested TOML array."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_array("[[1, 2], [3, 4]]", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_trailing_comma(self) -> None:
        """Parse array with trailing comma."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_toml_array("[1, 2, 3,]", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Inline table parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInlineTableParsing:
    def test_parse_empty_inline_table(self) -> None:
        """Parse empty inline table."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_inline_table("{}", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_inline_table_simple(self) -> None:
        """Parse inline table with key-value pairs."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_inline_table("{name = \\"test\\", version = 1}", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_inline_table_dotted_key(self) -> None:
        """Parse inline table with dotted keys."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_inline_table("{a.b = 1}", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Top-level document decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDecode:
    def test_decode_empty(self) -> None:
        """Decode empty TOML document."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_simple_key_value(self) -> None:
        """Decode simple key = value pair."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"Mapanare\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_integer_value(self) -> None:
        """Decode integer value."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("port = 8080")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_float_value(self) -> None:
        """Decode float value."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("pi = 3.14")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_bool_values(self) -> None:
        """Decode boolean values."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("enabled = true")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_datetime_value(self) -> None:
        """Decode datetime value."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("created = 2024-01-15T10:30:00Z")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_value(self) -> None:
        """Decode array value."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("ports = [8080, 8443, 9090]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_multiple_keys(self) -> None:
        """Decode multiple key-value pairs."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"test\\"\\nversion = 1")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_with_comments(self) -> None:
        """Decode TOML with comments."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("# comment\\nkey = \\"value\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Dotted keys in document
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDottedKeys:
    def test_decode_dotted_key(self) -> None:
        """Decode dotted key creates nested tables."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("a.b.c = 1")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_quoted_dotted_key(self) -> None:
        """Decode quoted key in dotted path."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("a.\\"complex key\\".c = 1")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Nested tables [section]
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestNestedTables:
    def test_decode_table_header(self) -> None:
        """Decode standard table header [section]."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[server]\\nhost = \\"localhost\\"\\nport = 8080")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_table_headers(self) -> None:
        """Decode nested table headers [a.b]."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[database]\\nhost = \\"db\\"\\n[database.pool]\\nsize = 10")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_multiple_tables(self) -> None:
        """Decode document with multiple table sections."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[server]\\nport = 80\\n[database]\\nhost = \\"db\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Array of tables [[section]]
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestArrayOfTables:
    def test_decode_array_of_tables(self) -> None:
        """Decode array of tables [[section]]."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[[products]]\\nname = \\"Hammer\\"\\n[[products]]\\nname = \\"Nail\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_of_tables_with_fields(self) -> None:
        """Decode array of tables with multiple fields per entry."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[[servers]]\\nhost = \\"a\\"\\nport = 80\\n[[servers]]\\nhost = \\"b\\"\\nport = 443")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorCases:
    def test_decode_duplicate_key_compiles(self) -> None:
        """Duplicate key error path compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("key = 1\\nkey = 2")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_unterminated_string_compiles(self) -> None:
        """Unterminated string error path compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("key = \\"hello")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_missing_value_compiles(self) -> None:
        """Missing value after = error path compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("key = ")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_invalid_escape_compiles(self) -> None:
        """Invalid escape sequence error path compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("key = \\"bad\\\\qescape\\"")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_unterminated_table_header_compiles(self) -> None:
        """Unterminated table header error path compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[missing_close")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Serializer: encode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncode:
    def test_encode_string(self) -> None:
        """Encode string value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["name"] = Str("Mapanare")
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_int(self) -> None:
        """Encode integer value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["port"] = Int(8080)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_from_int" in ir_out

    def test_encode_float(self) -> None:
        """Encode float value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["pi"] = Float(3.14)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_bool(self) -> None:
        """Encode boolean value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["enabled"] = Bool(true)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_datetime(self) -> None:
        """Encode datetime value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["created"] = DateTime("2024-01-15T10:30:00Z")
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_empty_array(self) -> None:
        """Encode empty array."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let items: List<TomlValue> = []
            entries["tags"] = Array(items)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_array(self) -> None:
        """Encode array of values."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let items: List<TomlValue> = [Int(1), Int(2), Int(3)]
            entries["ports"] = Array(items)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_nested_table(self) -> None:
        """Encode nested table produces [section] headers."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let sub: Map<String, TomlValue> = #{}
            sub["host"] = Str("localhost")
            entries["server"] = Table(sub)
            let s: String = encode(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_inline_value(self) -> None:
        """Encode value inline (for simple values)."""
        src = _toml_source_with_main("""\
            let s: String = encode_value_inline(Str("hello"))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Pretty-print serializer
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncodePretty:
    def test_encode_pretty_compiles(self) -> None:
        """Pretty-print serializer compiles."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["name"] = Str("test")
            entries["version"] = Int(1)
            let s: String = encode_pretty(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_pretty_nested(self) -> None:
        """Pretty-print with nested tables compiles."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["name"] = Str("project")
            let db: Map<String, TomlValue> = #{}
            db["host"] = Str("localhost")
            db["port"] = Int(5432)
            entries["database"] = Table(db)
            let s: String = encode_pretty(Table(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Round-trip: encode then decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRoundTrip:
    def test_round_trip_string(self) -> None:
        """Round-trip: encode then decode a string value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["name"] = Str("Mapanare")
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_integer(self) -> None:
        """Round-trip: encode then decode an integer value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["count"] = Int(42)
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_bool(self) -> None:
        """Round-trip: encode then decode a boolean value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["flag"] = Bool(true)
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_array(self) -> None:
        """Round-trip: encode then decode an array."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let items: List<TomlValue> = [Int(1), Int(2), Int(3)]
            entries["ports"] = Array(items)
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_nested_table(self) -> None:
        """Round-trip: encode then decode a nested table."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            let sub: Map<String, TomlValue> = #{}
            sub["host"] = Str("localhost")
            sub["port"] = Int(5432)
            entries["db"] = Table(sub)
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_float(self) -> None:
        """Round-trip: encode then decode a float value."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["pi"] = Float(3.14)
            let encoded: String = encode(Table(entries))
            let decoded: Result<TomlValue, TomlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Typed getters
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTypedGetters:
    def test_get_string_compiles(self) -> None:
        """get_string typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"hello\\"")
            match r {
                Ok(v) => {
                    let s: Result<String, TomlError> = get_string(v, "name")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_int_compiles(self) -> None:
        """get_int typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("port = 8080")
            match r {
                Ok(v) => {
                    let n: Result<Int, TomlError> = get_int(v, "port")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_float_compiles(self) -> None:
        """get_float typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("pi = 3.14")
            match r {
                Ok(v) => {
                    let f: Result<Float, TomlError> = get_float(v, "pi")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_bool_compiles(self) -> None:
        """get_bool typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("enabled = true")
            match r {
                Ok(v) => {
                    let b: Result<Bool, TomlError> = get_bool(v, "enabled")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_array_compiles(self) -> None:
        """get_array typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("tags = [1, 2, 3]")
            match r {
                Ok(v) => {
                    let a: Result<List<TomlValue>, TomlError> = get_array(v, "tags")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_table_compiles(self) -> None:
        """get_table typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[server]\\nhost = \\"localhost\\"")
            match r {
                Ok(v) => {
                    let t: Result<TomlValue, TomlError> = get_table(v, "server")
                    println("ok")
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_or_default_str_compiles(self) -> None:
        """get_or_default_str typed getter compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"test\\"")
            match r {
                Ok(v) => {
                    let s: String = get_or_default_str(v, "name", "fallback")
                    println(s)
                    let missing: String = get_or_default_str(v, "absent", "default")
                    println(missing)
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_string_missing_key_compiles(self) -> None:
        """get_string with missing key returns Err."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"test\\"")
            match r {
                Ok(v) => {
                    let s: Result<String, TomlError> = get_string(v, "nonexistent")
                    match s {
                        Ok(val) => { println("unexpected ok") },
                        Err(e) => { println(e.message) }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_int_wrong_type_compiles(self) -> None:
        """get_int on a string value returns type error."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("name = \\"test\\"")
            match r {
                Ok(v) => {
                    let n: Result<Int, TomlError> = get_int(v, "name")
                    match n {
                        Ok(val) => { println("unexpected ok") },
                        Err(e) => { println(e.message) }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Escape sequence handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEscapeHandling:
    def test_handle_toml_escape_newline(self) -> None:
        """Handle \\n escape sequence."""
        src = _toml_source_with_main("""\
            let r: EscapeResult = handle_toml_escape("nhello", 0, 6)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_handle_toml_escape_tab(self) -> None:
        """Handle \\t escape sequence."""
        src = _toml_source_with_main("""\
            let r: EscapeResult = handle_toml_escape("thello", 0, 6)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_handle_toml_escape_unicode(self) -> None:
        """Handle \\uXXXX escape sequence."""
        src = _toml_source_with_main("""\
            let r: EscapeResult = handle_toml_escape("u0041rest", 0, 9)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_handle_toml_escape_backslash(self) -> None:
        """Handle \\\\ escape sequence."""
        src = _toml_source_with_main("""\
            let r: EscapeResult = handle_toml_escape("\\\\hello", 0, 6)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_handle_toml_escape_invalid(self) -> None:
        """Handle invalid escape sequence returns error."""
        src = _toml_source_with_main("""\
            let r: EscapeResult = handle_toml_escape("qhello", 0, 6)
            println(str(r.ok))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Serializer helper functions
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSerializerHelpers:
    def test_escape_toml_basic_string_compiles(self) -> None:
        """escape_toml_basic_string compiles."""
        src = _toml_source_with_main("""\
            let r: String = escape_toml_basic_string("hello\\"world")
            println(r)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_needs_quoting_compiles(self) -> None:
        """needs_quoting check compiles."""
        src = _toml_source_with_main("""\
            let r1: Bool = needs_quoting("simple")
            let r2: Bool = needs_quoting("has spaces")
            println(str(r1))
            println(str(r2))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_key_bare(self) -> None:
        """encode_key for bare key compiles."""
        src = _toml_source_with_main("""\
            let r: String = encode_key("simple_key")
            println(r)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_key_quoted(self) -> None:
        """encode_key for key needing quotes compiles."""
        src = _toml_source_with_main("""\
            let r: String = encode_key("complex key")
            println(r)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_simple_value_compiles(self) -> None:
        """is_simple_value helper compiles."""
        src = _toml_source_with_main("""\
            let r1: Bool = is_simple_value(Str("hello"))
            let r2: Bool = is_simple_value(Int(42))
            println(str(r1))
            println(str(r2))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_table_array_compiles(self) -> None:
        """is_table_array helper compiles."""
        src = _toml_source_with_main("""\
            let entries: Map<String, TomlValue> = #{}
            entries["a"] = Int(1)
            let items: List<TomlValue> = [Table(entries)]
            let r: Bool = is_table_array(Array(items))
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# DateTime parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDateTimeParsing:
    def test_looks_like_datetime_date(self) -> None:
        """Datetime heuristic detects date pattern."""
        src = _toml_source_with_main("""\
            let r: Bool = looks_like_datetime("2024-01-15", 0)
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_full_datetime(self) -> None:
        """Parse full RFC 3339 datetime."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_datetime("2024-01-15T10:30:00Z", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_local_date(self) -> None:
        """Parse local date (no time component)."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_datetime("2024-01-15", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_datetime_with_offset(self) -> None:
        """Parse datetime with timezone offset."""
        src = _toml_source_with_main("""\
            let r: ValueResult = parse_datetime("2024-01-15T10:30:00+05:30", 0, 1, 1)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Performance / large document sanity
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPerformance:
    def test_large_toml_compiles(self) -> None:
        """Large TOML parsing code compiles (basic performance sanity)."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("a = 1\\nb = 2\\nc = 3\\nd = 4\\ne = 5\\nf = 6\\ng = 7\\nh = 8\\ni = 9\\nj = 10")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_complex_document_compiles(self) -> None:
        """Complex TOML document with tables and arrays compiles."""
        src = _toml_source_with_main("""\
            let r: Result<TomlValue, TomlError> = decode("[package]\\nname = \\"test\\"\\nversion = \\"1.0\\"\\n[dependencies]\\nhttp = \\"0.2\\"\\njson = \\"1.0\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
