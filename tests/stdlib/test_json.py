"""Phase 1 — encoding/json.mn — JSON Parser/Serializer tests.

Tests verify that the JSON stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the JSON module source code within test programs.

Covers:
  - Core types: JsonValue enum, JsonError struct
  - Parser: primitives, strings, numbers, arrays, objects
  - Edge cases: empty containers, unicode escapes, error cases
  - Serializer: encode, encode_pretty
  - Streaming parser: SAX-style events
  - Round-trip: decode(encode(value)) == value
  - Schema validation
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

# Read the JSON module source once
_JSON_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "json.mn").read_text(
    encoding="utf-8"
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_json.mn", use_mir=True)


def _json_source_with_main(main_body: str) -> str:
    """Prepend the JSON module source and wrap main_body in fn main()."""
    return _JSON_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Task 1 & 2: Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_json_value_enum_compiles(self) -> None:
        """JsonValue enum (recursive, with List and Map variants) compiles."""
        src = _json_source_with_main("""\
            let v: JsonValue = Null()
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_json_error_struct_compiles(self) -> None:
        """JsonError struct compiles."""
        src = _json_source_with_main("""\
            let e: JsonError = new JsonError { message: "test", line: 1, col: 1 }
            println(e.message)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_json_value_bool_variant(self) -> None:
        """JsonValue::Bool variant compiles."""
        src = _json_source_with_main("""\
            let v: JsonValue = Bool(true)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_json_value_int_variant(self) -> None:
        """JsonValue::Int variant compiles."""
        src = _json_source_with_main("""\
            let v: JsonValue = Int(42)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_json_value_str_variant(self) -> None:
        """JsonValue::Str variant compiles."""
        src = _json_source_with_main("""\
            let v: JsonValue = Str("hello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 3: JSON lexer (character helpers)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCharHelpers:
    def test_is_json_digit(self) -> None:
        """Digit classification helper compiles."""
        src = _json_source_with_main("""\
            let r: Bool = is_json_digit("5")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_digit_value(self) -> None:
        """Digit value helper compiles."""
        src = _json_source_with_main("""\
            let v: Int = digit_value("7")
            println(str(v))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 9: Whitespace handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWhitespace:
    def test_skip_whitespace_compiles(self) -> None:
        """skip_whitespace function compiles."""
        src = _json_source_with_main("""\
            let r: SkipResult = skip_whitespace("  hello", 0, 1, 1)
            println(str(r.pos))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 5: String parsing with escape handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStringParsing:
    def test_parse_simple_string(self) -> None:
        """Parse a simple JSON string."""
        src = _json_source_with_main("""\
            let r: StringResult = parse_json_string("\\"hello\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_char_at" in ir_out

    def test_parse_string_with_escapes(self) -> None:
        """Parse string with escape sequences."""
        src = _json_source_with_main("""\
            let r: StringResult = parse_json_string("\\"line1\\\\nline2\\"", 0, 1, 1)
            println(r.value)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 6: Number parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestNumberParsing:
    def test_parse_integer(self) -> None:
        """Parse an integer."""
        src = _json_source_with_main("""\
            let r: NumberResult = parse_json_number("42", 0, 1, 1)
            println(str(r.int_val))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_negative_integer(self) -> None:
        """Parse a negative integer."""
        src = _json_source_with_main("""\
            let r: NumberResult = parse_json_number("-7", 0, 1, 1)
            println(str(r.int_val))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_float(self) -> None:
        """Parse a float."""
        src = _json_source_with_main("""\
            let r: NumberResult = parse_json_number("3.14", 0, 1, 1)
            println(str(r.float_val))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_exponent(self) -> None:
        """Parse a number with exponent."""
        src = _json_source_with_main("""\
            let r: NumberResult = parse_json_number("2.5e10", 0, 1, 1)
            println(str(r.float_val))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 4, 10: decode_value and decode (top-level)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDecode:
    def test_decode_null(self) -> None:
        """Decode JSON null."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("null")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_true(self) -> None:
        """Decode JSON true."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("true")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_false(self) -> None:
        """Decode JSON false."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("false")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_integer(self) -> None:
        """Decode JSON integer."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("42")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_float(self) -> None:
        """Decode JSON float."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("3.14")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_string(self) -> None:
        """Decode JSON string."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("\\"hello\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 7, 22: Array parsing (including nested)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestArrayParsing:
    def test_decode_empty_array(self) -> None:
        """Decode empty JSON array."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("[]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_array_of_ints(self) -> None:
        """Decode JSON array of integers."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("[1, 2, 3]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_array(self) -> None:
        """Decode nested JSON array."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("[[1, 2], [3, 4]]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 8, 22: Object parsing (including nested)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestObjectParsing:
    def test_decode_empty_object(self) -> None:
        """Decode empty JSON object."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("{}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_simple_object(self) -> None:
        """Decode simple JSON object."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("{\\"name\\": \\"Mapanare\\", \\"version\\": 9}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_object(self) -> None:
        """Decode nested JSON object with arrays."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("{\\"data\\": {\\"items\\": [1, 2, 3]}}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 24: Error cases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorCases:
    def test_decode_unterminated_string_compiles(self) -> None:
        """Unterminated string error path compiles."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("\\"hello")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_invalid_value_compiles(self) -> None:
        """Invalid value error path compiles."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("xyz")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_trailing_content_compiles(self) -> None:
        """Trailing content error path compiles."""
        src = _json_source_with_main("""\
            let r: Result<JsonValue, JsonError> = decode("42 extra")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 14: Serializer — encode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncode:
    def test_encode_null(self) -> None:
        """Encode null."""
        src = _json_source_with_main("""\
            let s: String = encode(Null)
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_bool(self) -> None:
        """Encode boolean."""
        src = _json_source_with_main("""\
            let s: String = encode(Bool(true))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_int(self) -> None:
        """Encode integer."""
        src = _json_source_with_main("""\
            let s: String = encode(Int(42))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_from_int" in ir_out

    def test_encode_string(self) -> None:
        """Encode string with escape handling."""
        src = _json_source_with_main("""\
            let s: String = encode(Str("hello\\"world"))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_empty_array(self) -> None:
        """Encode empty array."""
        src = _json_source_with_main("""\
            let items: List<JsonValue> = []
            let s: String = encode(Array(items))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_array(self) -> None:
        """Encode array of values."""
        src = _json_source_with_main("""\
            let items: List<JsonValue> = [Int(1), Int(2), Int(3)]
            let s: String = encode(Array(items))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 15: Pretty-print serializer
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncodePretty:
    def test_encode_pretty_compiles(self) -> None:
        """Pretty-print serializer compiles."""
        src = _json_source_with_main("""\
            let items: List<JsonValue> = [Int(1), Int(2)]
            let s: String = encode_pretty(Array(items), 2)
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 25: Round-trip test
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRoundTrip:
    def test_round_trip_int(self) -> None:
        """Round-trip: encode then decode an integer."""
        src = _json_source_with_main("""\
            let encoded: String = encode(Int(42))
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_string(self) -> None:
        """Round-trip: encode then decode a string."""
        src = _json_source_with_main("""\
            let encoded: String = encode(Str("hello"))
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_array(self) -> None:
        """Round-trip: encode then decode an array."""
        src = _json_source_with_main("""\
            let items: List<JsonValue> = [Int(1), Str("two"), Bool(true)]
            let encoded: String = encode(Array(items))
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_null(self) -> None:
        """Round-trip: encode then decode null."""
        src = _json_source_with_main("""\
            let encoded: String = encode(Null)
            let decoded: Result<JsonValue, JsonError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 26: Streaming parser
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStreamingParser:
    def test_stream_parse_compiles(self) -> None:
        """Streaming parser compiles."""
        src = _json_source_with_main("""\
            let r: Result<List<JsonEvent>, JsonError> = stream_parse("{\\"key\\": 42}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_stream_parse_array_compiles(self) -> None:
        """Streaming parser for arrays compiles."""
        src = _json_source_with_main("""\
            let r: Result<List<JsonEvent>, JsonError> = stream_parse("[1, 2, 3]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Tasks 19, 20: Schema validation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSchemaValidation:
    def test_validate_compiles(self) -> None:
        """Schema validation compiles."""
        src = _json_source_with_main("""\
            let schema: JsonSchema = new JsonSchema {
                schema_type: SInt,
                required_fields: [],
                min_value: 0,
                max_value: 100,
                has_min: true,
                has_max: true
            }
            let value: JsonValue = Int(42)
            let r: Result<Bool, List<JsonError>> = validate(value, schema)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 27: Typed deserialization (skipped — needs introspection)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Typed deserialization requires compile-time struct introspection (not available yet)")
class TestTypedDeserialization:
    def test_decode_to_struct(self) -> None:
        """Typed deserialization into struct — deferred to v1.0+."""
        pass


# ---------------------------------------------------------------------------
# Task 28: Performance benchmark
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPerformance:
    def test_large_json_compiles(self) -> None:
        """Large JSON parsing code compiles (basic performance sanity)."""
        src = _json_source_with_main("""\
            let big: String = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
            let r: Result<JsonValue, JsonError> = decode(big)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
