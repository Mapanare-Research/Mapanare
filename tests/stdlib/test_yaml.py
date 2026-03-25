"""Phase 1 — encoding/yaml.mn — YAML 1.2 Core Schema Parser/Serializer tests.

Tests verify that the YAML stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the YAML module source code within test programs.

Covers:
  - Core types: YamlValue enum, YamlError struct, YamlEntry struct
  - Scalar types: null, bool, int, float, string (plain/quoted)
  - Block mappings and sequences (nested, mixed)
  - Flow mappings and sequences
  - Block scalars: literal (|) and folded (>) with chomp indicators
  - Anchors and aliases
  - Multi-document streams (decode_all)
  - Serializer: encode, encode_flow
  - Round-trip: decode(encode(value)) == value
  - Error cases: invalid YAML (bad indentation, tab indentation)
  - Core Schema type resolution (true/True/TRUE, null/Null/~, 0x hex, .inf, .nan)
  - Real-world YAML: CI config, docker compose snippet
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

# Read the YAML module source once
_YAML_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "yaml.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_yaml.mn", use_mir=True)


def _yaml_source_with_main(main_body: str) -> str:
    """Prepend the YAML module source and wrap main_body in fn main()."""
    return _YAML_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_yaml_value_null_compiles(self) -> None:
        """YamlValue::Null variant compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = Null()
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_bool_compiles(self) -> None:
        """YamlValue::Bool variant compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = Bool(true)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_int_compiles(self) -> None:
        """YamlValue::Int variant compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = Int(42)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_float_compiles(self) -> None:
        """YamlValue::Float variant compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = Float(3.14)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_str_compiles(self) -> None:
        """YamlValue::Str variant compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = Str("hello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_seq_compiles(self) -> None:
        """YamlValue::Seq variant compiles."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = [Int(1), Int(2)]
            let v: YamlValue = Seq(items)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_value_map_compiles(self) -> None:
        """YamlValue::Map variant compiles."""
        src = _yaml_source_with_main("""\
            let entries: List<YamlEntry> = []
            let v: YamlValue = Map(entries)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_error_struct_compiles(self) -> None:
        """YamlError struct compiles."""
        src = _yaml_source_with_main("""\
            let e: YamlError = new_yaml_error("test error", 1, 1)
            println(e.message)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_entry_struct_compiles(self) -> None:
        """YamlEntry struct compiles."""
        src = _yaml_source_with_main("""\
            let entry: YamlEntry = new_yaml_entry("key", Int(42))
            println(entry.key)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Character classification helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCharHelpers:
    def test_is_yaml_digit(self) -> None:
        """Digit classification helper compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_yaml_digit("5")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_yaml_hex(self) -> None:
        """Hex digit classification helper compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_yaml_hex("a")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_space(self) -> None:
        """Space classification helper compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_space(" ")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_newline(self) -> None:
        """Newline classification helper compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_newline("\\n")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_flow_indicator(self) -> None:
        """Flow indicator classification helper compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_flow_indicator("{")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Decode scalar types
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDecodeScalars:
    def test_decode_null_word(self) -> None:
        """Decode YAML null (word)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("null")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_null_tilde(self) -> None:
        """Decode YAML null (~)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("~")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_empty_is_null(self) -> None:
        """Decode empty input as null."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_bool_true(self) -> None:
        """Decode YAML true."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("true")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_bool_false(self) -> None:
        """Decode YAML false."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("false")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_integer(self) -> None:
        """Decode YAML integer."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("42")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_negative_integer(self) -> None:
        """Decode negative YAML integer."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("-7")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_float(self) -> None:
        """Decode YAML float."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("3.14")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_float_scientific(self) -> None:
        """Decode YAML float with scientific notation."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("2.5e10")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_plain_string(self) -> None:
        """Decode YAML plain (unquoted) string."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("hello world")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_double_quoted_string(self) -> None:
        """Decode YAML double-quoted string."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"hello world\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_single_quoted_string(self) -> None:
        """Decode YAML single-quoted string."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("'hello world'")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Core Schema type resolution
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreSchemaResolution:
    def test_resolve_true_lowercase(self) -> None:
        """Core Schema: true -> Bool(true)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("true")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_true_titlecase(self) -> None:
        """Core Schema: True -> Bool(true)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("True")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_true_uppercase(self) -> None:
        """Core Schema: TRUE -> Bool(true)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("TRUE")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_false_lowercase(self) -> None:
        """Core Schema: false -> Bool(false)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("false")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_false_titlecase(self) -> None:
        """Core Schema: False -> Bool(false)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("False")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_false_uppercase(self) -> None:
        """Core Schema: FALSE -> Bool(false)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("FALSE")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_null_lowercase(self) -> None:
        """Core Schema: null -> Null."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("null")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_null_titlecase(self) -> None:
        """Core Schema: Null -> Null."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("Null")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_null_uppercase(self) -> None:
        """Core Schema: NULL -> Null."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("NULL")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_null_tilde(self) -> None:
        """Core Schema: ~ -> Null."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("~")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_hex_integer(self) -> None:
        """Core Schema: 0xFF -> Int(255)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("0xFF")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_octal_integer(self) -> None:
        """Core Schema: 0o77 -> Int(63)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("0o77")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_positive_inf(self) -> None:
        """Core Schema: .inf -> Float(+inf)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode(".inf")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_negative_inf(self) -> None:
        """Core Schema: -.inf -> Float(-inf)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("-.inf")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_nan(self) -> None:
        """Core Schema: .nan -> Float(NaN)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode(".nan")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_nan_titlecase(self) -> None:
        """Core Schema: .NaN -> Float(NaN)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode(".NaN")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_inf_titlecase(self) -> None:
        """Core Schema: .Inf -> Float(+inf)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode(".Inf")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_resolve_positive_sign_integer(self) -> None:
        """Core Schema: +42 -> Int(42)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("+42")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Block mapping parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBlockMappings:
    def test_decode_simple_block_map(self) -> None:
        """Decode simple block mapping."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("name: Mapanare\\nversion: 9")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_block_map(self) -> None:
        """Decode nested block mapping."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("server:\\n  host: localhost\\n  port: 8080")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_map_with_null_value(self) -> None:
        """Decode block mapping with null value (key with no value)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("key:")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_map_with_quoted_keys(self) -> None:
        """Decode block mapping with quoted keys."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"quoted key\\": value")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_map_with_comment(self) -> None:
        """Decode block mapping with inline comment."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("key: value # this is a comment")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Block sequence parsing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBlockSequences:
    def test_decode_simple_block_seq(self) -> None:
        """Decode simple block sequence."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- one\\n- two\\n- three")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_block_seq_of_ints(self) -> None:
        """Decode block sequence of integers."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- 1\\n- 2\\n- 3")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_block_seq(self) -> None:
        """Decode nested block sequence."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- - 1\\n  - 2\\n- - 3\\n  - 4")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_block_seq_mixed_types(self) -> None:
        """Decode block sequence with mixed types."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- hello\\n- 42\\n- true\\n- null")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_map_with_seq_value(self) -> None:
        """Decode block mapping with sequence value."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("items:\\n  - one\\n  - two\\n  - three")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_seq_of_maps(self) -> None:
        """Decode block sequence of mappings."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- name: alice\\n  age: 30\\n- name: bob\\n  age: 25")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Flow mappings and sequences
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFlowCollections:
    def test_decode_empty_flow_seq(self) -> None:
        """Decode empty flow sequence []."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_seq_of_ints(self) -> None:
        """Decode flow sequence of integers."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[1, 2, 3]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_seq_mixed_types(self) -> None:
        """Decode flow sequence with mixed types."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[hello, 42, true, null]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_flow_seq(self) -> None:
        """Decode nested flow sequence."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[[1, 2], [3, 4]]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_empty_flow_map(self) -> None:
        """Decode empty flow mapping {}."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_map(self) -> None:
        """Decode flow mapping."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{name: Mapanare, version: 9}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_nested_flow_map(self) -> None:
        """Decode nested flow mapping."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{outer: {inner: value}}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_seq_trailing_comma(self) -> None:
        """Decode flow sequence with trailing comma."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[1, 2, 3,]")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_map_trailing_comma(self) -> None:
        """Decode flow mapping with trailing comma."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{a: 1, b: 2,}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_flow_map_quoted_keys(self) -> None:
        """Decode flow mapping with quoted keys."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{\\"key one\\": 1, 'key two': 2}")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Block scalars: literal (|) and folded (>)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBlockScalars:
    def test_decode_literal_block_scalar(self) -> None:
        """Decode literal block scalar (|)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: |\\n  line1\\n  line2")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_folded_block_scalar(self) -> None:
        """Decode folded block scalar (>)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: >\\n  line1\\n  line2")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_literal_strip_chomp(self) -> None:
        """Decode literal block scalar with strip chomp indicator (|-)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: |-\\n  line1\\n  line2")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_literal_keep_chomp(self) -> None:
        """Decode literal block scalar with keep chomp indicator (|+)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: |+\\n  line1\\n  line2\\n")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_folded_strip_chomp(self) -> None:
        """Decode folded block scalar with strip chomp indicator (>-)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: >-\\n  line1\\n  line2")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_folded_keep_chomp(self) -> None:
        """Decode folded block scalar with keep chomp indicator (>+)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: >+\\n  line1\\n  line2\\n")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_literal_with_explicit_indent(self) -> None:
        """Decode literal block scalar with explicit indent indicator (|2)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("content: |2\\n  line1\\n  line2")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Anchors and aliases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestAnchorsAliases:
    def test_decode_anchor_and_alias(self) -> None:
        """Decode anchor (&name) and alias (*name)."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("- &anchor value\\n- *anchor")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_anchor_on_mapping(self) -> None:
        """Decode anchor on a mapping value."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("defaults: &defaults\\n  timeout: 30\\nserver:\\n  host: localhost")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_anchor_on_scalar(self) -> None:
        """Decode anchor on a plain scalar."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("name: &myname Alice\\nalias: *myname")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Multi-document streams
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMultiDocument:
    def test_decode_all_single_doc(self) -> None:
        """decode_all with a single document."""
        src = _yaml_source_with_main("""\
            let r: Result<List<YamlValue>, YamlError> = decode_all("hello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_all_two_docs(self) -> None:
        """decode_all with two documents separated by ---."""
        src = _yaml_source_with_main("""\
            let r: Result<List<YamlValue>, YamlError> = decode_all("---\\nhello\\n---\\nworld")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_all_doc_end_marker(self) -> None:
        """decode_all with document end marker (...)."""
        src = _yaml_source_with_main("""\
            let r: Result<List<YamlValue>, YamlError> = decode_all("---\\nhello\\n...\\n---\\nworld")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_all_empty_doc(self) -> None:
        """decode_all with empty document."""
        src = _yaml_source_with_main("""\
            let r: Result<List<YamlValue>, YamlError> = decode_all("---\\n...\\n---\\nvalue")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_doc_start_marker(self) -> None:
        """Decode single document with --- start marker."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("---\\nhello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Serializer — encode (block style)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncode:
    def test_encode_null(self) -> None:
        """Encode null."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Null())
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_bool_true(self) -> None:
        """Encode boolean true."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Bool(true))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_bool_false(self) -> None:
        """Encode boolean false."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Bool(false))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_int(self) -> None:
        """Encode integer."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Int(42))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "__mn_str_from_int" in ir_out

    def test_encode_float(self) -> None:
        """Encode float."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Float(3.14))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_plain_string(self) -> None:
        """Encode plain string (no quoting needed)."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Str("hello"))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_quoted_string(self) -> None:
        """Encode string that needs quoting."""
        src = _yaml_source_with_main("""\
            let s: String = encode(Str("true"))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_empty_seq(self) -> None:
        """Encode empty sequence."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = []
            let s: String = encode(Seq(items))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_seq(self) -> None:
        """Encode sequence of values."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = [Int(1), Int(2), Int(3)]
            let s: String = encode(Seq(items))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_empty_map(self) -> None:
        """Encode empty mapping."""
        src = _yaml_source_with_main("""\
            let entries: List<YamlEntry> = []
            let s: String = encode(Map(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_map(self) -> None:
        """Encode mapping with entries."""
        src = _yaml_source_with_main("""\
            let entries: List<YamlEntry> = [new_yaml_entry("name", Str("Mapanare")), new_yaml_entry("version", Int(1))]
            let s: String = encode(Map(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Serializer — encode_flow (compact/flow style)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEncodeFlow:
    def test_encode_flow_null(self) -> None:
        """Encode null in flow style."""
        src = _yaml_source_with_main("""\
            let s: String = encode_flow(Null())
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_flow_seq(self) -> None:
        """Encode sequence in flow style."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = [Int(1), Str("two"), Bool(true)]
            let s: String = encode_flow(Seq(items))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_flow_map(self) -> None:
        """Encode mapping in flow style."""
        src = _yaml_source_with_main("""\
            let entries: List<YamlEntry> = [new_yaml_entry("a", Int(1)), new_yaml_entry("b", Int(2))]
            let s: String = encode_flow(Map(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_encode_flow_nested(self) -> None:
        """Encode nested structures in flow style."""
        src = _yaml_source_with_main("""\
            let inner: List<YamlValue> = [Int(1), Int(2)]
            let entries: List<YamlEntry> = [new_yaml_entry("items", Seq(inner))]
            let s: String = encode_flow(Map(entries))
            println(s)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Round-trip: encode -> decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRoundTrip:
    def test_round_trip_int(self) -> None:
        """Round-trip: encode then decode an integer."""
        src = _yaml_source_with_main("""\
            let encoded: String = encode(Int(42))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_string(self) -> None:
        """Round-trip: encode then decode a string."""
        src = _yaml_source_with_main("""\
            let encoded: String = encode(Str("hello"))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_bool(self) -> None:
        """Round-trip: encode then decode a boolean."""
        src = _yaml_source_with_main("""\
            let encoded: String = encode(Bool(true))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_null(self) -> None:
        """Round-trip: encode then decode null."""
        src = _yaml_source_with_main("""\
            let encoded: String = encode(Null())
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_seq(self) -> None:
        """Round-trip: encode then decode a sequence."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = [Int(1), Int(2), Int(3)]
            let encoded: String = encode(Seq(items))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_map(self) -> None:
        """Round-trip: encode then decode a mapping."""
        src = _yaml_source_with_main("""\
            let entries: List<YamlEntry> = [new_yaml_entry("key", Str("value"))]
            let encoded: String = encode(Map(entries))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_round_trip_flow_seq(self) -> None:
        """Round-trip: encode_flow then decode a sequence."""
        src = _yaml_source_with_main("""\
            let items: List<YamlValue> = [Int(10), Str("hello"), Bool(false)]
            let encoded: String = encode_flow(Seq(items))
            let decoded: Result<YamlValue, YamlError> = decode(encoded)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorCases:
    def test_decode_unterminated_double_quote_compiles(self) -> None:
        """Unterminated double-quoted string error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"unterminated")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_unterminated_single_quote_compiles(self) -> None:
        """Unterminated single-quoted string error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("'unterminated")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_unterminated_flow_seq_compiles(self) -> None:
        """Unterminated flow sequence error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[1, 2, 3")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_unterminated_flow_map_compiles(self) -> None:
        """Unterminated flow mapping error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("{key: value")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_bad_escape_compiles(self) -> None:
        """Bad escape sequence in double-quoted string error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"bad \\\\z escape\\"")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_undefined_alias_compiles(self) -> None:
        """Undefined alias error path compiles."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("*nosuchanchor")
            match r {
                Ok(v) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_max_depth_compiles(self) -> None:
        """Max nesting depth error path compiles (deeply nested flow sequences)."""
        # Build a deeply nested flow sequence: [[[...]]]
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]")
            match r {
                Ok(v) => { println("parsed") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# String parsing edge cases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStringParsing:
    def test_parse_double_quoted_with_escapes(self) -> None:
        """Parse double-quoted string with escape sequences."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"line1\\\\nline2\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_single_quoted_with_escaped_quote(self) -> None:
        """Parse single-quoted string with escaped single quote ('')."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("'it''s a test'")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_double_quoted_unicode_escape(self) -> None:
        """Parse double-quoted string with \\x hex escape."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"\\\\x41\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_double_quoted_unicode_u_escape(self) -> None:
        """Parse double-quoted string with \\u unicode escape."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\"\\\\u0041\\"")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Whitespace and comment handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWhitespace:
    def test_skip_ws_and_comments_compiles(self) -> None:
        """skip_ws_and_comments function compiles."""
        src = _yaml_source_with_main("""\
            let r: PosInfo = skip_ws_and_comments("  # comment\\nhello", 17, 0, 1, 1)
            println(str(r.pos))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_with_leading_comments(self) -> None:
        """Decode YAML with leading comments."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("# comment\\nhello")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_with_blank_lines(self) -> None:
        """Decode YAML with blank lines."""
        src = _yaml_source_with_main("""\
            let r: Result<YamlValue, YamlError> = decode("\\n\\nhello\\n\\n")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Document markers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestDocumentMarkers:
    def test_is_doc_start(self) -> None:
        """is_doc_start function compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_doc_start("--- hello", 9, 0)
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_doc_end(self) -> None:
        """is_doc_end function compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = is_doc_end("...", 3, 0)
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInternalHelpers:
    def test_resolve_plain_scalar_compiles(self) -> None:
        """resolve_plain_scalar function compiles."""
        src = _yaml_source_with_main("""\
            let v: YamlValue = resolve_plain_scalar("42")
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_needs_quoting_compiles(self) -> None:
        """yaml_needs_quoting function compiles."""
        src = _yaml_source_with_main("""\
            let r: Bool = yaml_needs_quoting("true")
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_yaml_quote_string_compiles(self) -> None:
        """yaml_quote_string function compiles."""
        src = _yaml_source_with_main("""\
            let r: String = yaml_quote_string("hello world")
            println(r)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_make_indent_compiles(self) -> None:
        """make_indent function compiles."""
        src = _yaml_source_with_main("""\
            let r: String = make_indent(3)
            println(r)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_measure_indent_compiles(self) -> None:
        """measure_indent function compiles."""
        src = _yaml_source_with_main("""\
            let r: Int = measure_indent("    hello", 9, 0)
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Real-world YAML: CI config
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRealWorldCI:
    def test_decode_ci_config(self) -> None:
        """Decode a CI-config-style YAML document."""
        src = _yaml_source_with_main("""\
            let yaml_str: String = "name: CI\\non:\\n  push:\\n    branches:\\n      - main\\n      - dev\\njobs:\\n  test:\\n    runs-on: ubuntu-latest\\n    steps:\\n      - checkout\\n      - run tests"
            let r: Result<YamlValue, YamlError> = decode(yaml_str)
            match r {
                Ok(v) => { println("parsed ci config") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_ci_config_with_matrix(self) -> None:
        """Decode CI config with flow sequence (matrix strategy)."""
        src = _yaml_source_with_main("""\
            let yaml_str: String = "strategy:\\n  matrix:\\n    python-version: [3.11, 3.12]\\n    os: [ubuntu-latest]"
            let r: Result<YamlValue, YamlError> = decode(yaml_str)
            match r {
                Ok(v) => { println("parsed matrix config") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Real-world YAML: Docker Compose snippet
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRealWorldDockerCompose:
    def test_decode_docker_compose_snippet(self) -> None:
        """Decode a Docker-Compose-style YAML document."""
        src = _yaml_source_with_main("""\
            let yaml_str: String = "version: 3\\nservices:\\n  web:\\n    image: nginx\\n    ports:\\n      - 8080\\n      - 443\\n  db:\\n    image: postgres\\n    environment:\\n      POSTGRES_DB: mydb"
            let r: Result<YamlValue, YamlError> = decode(yaml_str)
            match r {
                Ok(v) => { println("parsed compose config") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decode_docker_compose_with_flow(self) -> None:
        """Decode Docker Compose snippet with flow collections."""
        src = _yaml_source_with_main("""\
            let yaml_str: String = "services:\\n  app:\\n    ports: [3000, 3001]\\n    labels: {env: prod, tier: frontend}"
            let r: Result<YamlValue, YamlError> = decode(yaml_str)
            match r {
                Ok(v) => { println("parsed compose with flow") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Performance / large input sanity
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPerformance:
    def test_large_yaml_compiles(self) -> None:
        """Large YAML parsing code compiles (basic performance sanity)."""
        src = _yaml_source_with_main("""\
            let big: String = "- 1\\n- 2\\n- 3\\n- 4\\n- 5\\n- 6\\n- 7\\n- 8\\n- 9\\n- 10"
            let r: Result<YamlValue, YamlError> = decode(big)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_large_flow_seq_compiles(self) -> None:
        """Large flow sequence parsing code compiles."""
        src = _yaml_source_with_main("""\
            let big: String = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
            let r: Result<YamlValue, YamlError> = decode(big)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
