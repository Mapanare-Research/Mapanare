"""Phase 2 — encoding/csv.mn — CSV Parser/Writer tests.

Tests verify that the CSV stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the CSV module source code within test programs.

Covers:
  - Core types: CsvTable, CsvError, CsvConfig (Tasks 1-4)
  - Parser: basic CSV, custom delimiters, quoted fields (Tasks 5-8, 13-15)
  - Writer: serialize CsvTable to CSV string (Tasks 9-10, 16)
  - Streaming: collect_rows (Tasks 11-12, 17)
  - Error cases: unclosed quotes, malformed input (Task 18)
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

_CSV_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "csv.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test_csv.mn", use_mir=True)


def _csv_with_main(main_body: str) -> str:
    return _CSV_MN + "\n\n" + textwrap.dedent(
        f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """
    )


# ---------------------------------------------------------------------------
# Tasks 1-4: Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_csv_table_struct(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["name", "age"]
            let rows: List<List<String>> = [["Alice", "30"], ["Bob", "25"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_csv_error_struct(self) -> None:
        src = _csv_with_main("""\
            let e: CsvError = new CsvError { message: "test error", line: 1 }
            println(e.message)
        """)
        assert "main" in _compile_mir(src)

    def test_csv_config_struct(self) -> None:
        src = _csv_with_main("""\
            let config: CsvConfig = new CsvConfig { delimiter: ",", quote_char: "\\"", has_headers: true }
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_default_csv_config(self) -> None:
        src = _csv_with_main("""\
            let config: CsvConfig = default_csv_config()
            println(config.delimiter)
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 13: Parse basic CSV with headers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestBasicParsing:
    def test_parse_basic_csv(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,age\\nAlice,30\\nBob,25"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_parse_single_row(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "x,y\\n1,2"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_parse_empty_string(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = ""
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_parse_header_only(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,age\\n"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 14: Parse with custom delimiter (TSV, pipe-separated)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCustomDelimiter:
    def test_parse_tsv(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name\\tage\\nAlice\\t30"
            let config: CsvConfig = new CsvConfig { delimiter: "\\t", quote_char: "\\"", has_headers: true }
            let result: Result<CsvTable, CsvError> = parse_with(csv_data, config)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_parse_pipe_separated(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name|age\\nAlice|30"
            let config: CsvConfig = new CsvConfig { delimiter: "|", quote_char: "\\"", has_headers: true }
            let result: Result<CsvTable, CsvError> = parse_with(csv_data, config)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_parse_no_headers(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "Alice,30\\nBob,25"
            let config: CsvConfig = new CsvConfig { delimiter: ",", quote_char: "\\"", has_headers: false }
            let result: Result<CsvTable, CsvError> = parse_with(csv_data, config)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 15: Handle quoted fields, embedded commas, embedded newlines
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestQuotedFields:
    def test_quoted_field_with_comma(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,address\\n\\"Alice\\",\\"123 Main St, Apt 4\\""
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_quoted_field_with_newline(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,bio\\n\\"Alice\\",\\"line1\\nline2\\""
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_escaped_quote(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,quote\\nAlice,\\"She said \\"\\"hello\\"\\"\\""
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 16: Write and re-read round-trip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRoundTrip:
    def test_to_string_basic(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["name", "age"]
            let rows: List<List<String>> = [["Alice", "30"], ["Bob", "25"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            let csv_out: String = to_string(table, ",", "\\"")
            println(csv_out)
        """)
        assert "main" in _compile_mir(src)

    def test_round_trip(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["x", "y"]
            let rows: List<List<String>> = [["1", "2"], ["3", "4"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            let csv_str: String = to_string(table, ",", "\\"")
            let result: Result<CsvTable, CsvError> = parse(csv_str)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_round_trip_with_quoting(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["name", "address"]
            let rows: List<List<String>> = [["Alice", "123 Main, Apt 4"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            let csv_str: String = to_string(table, ",", "\\"")
            let result: Result<CsvTable, CsvError> = parse(csv_str)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 17: Streaming
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStreaming:
    def test_collect_rows(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,age\\nAlice,30\\nBob,25\\nCarol,28"
            let result: Result<List<List<String>>, CsvError> = collect_rows(csv_data)
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_stream_state(self) -> None:
        src = _csv_with_main("""\
            let state: StreamState = new_stream_state("a,b\\n1,2", ",", "\\"", true)
            println(str(state.pos))
        """)
        assert "main" in _compile_mir(src)

    def test_stream_next_row(self) -> None:
        src = _csv_with_main("""\
            let state: StreamState = new_stream_state("a,b\\n1,2", ",", "\\"", false)
            let result: Result<List<String>, CsvError> = stream_next_row(state)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Task 18: Error on malformed CSV
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorCases:
    def test_unclosed_quote(self) -> None:
        src = _csv_with_main("""\
            let csv_data: String = "name,age\\n\\"Alice,30"
            let result: Result<CsvTable, CsvError> = parse(csv_data)
            match result {
                Ok(table) => { println("unexpected ok") },
                Err(e) => { println(e.message) }
            }
        """)
        assert "main" in _compile_mir(src)

    def test_error_line_number(self) -> None:
        src = _csv_with_main("""\
            let e: CsvError = new CsvError { message: "test", line: 5 }
            println(str(e.line))
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestWriter:
    def test_field_needs_quoting(self) -> None:
        src = _csv_with_main("""\
            let needs: Bool = field_needs_quoting("hello,world", ",", "\\"")
            println(str(needs))
        """)
        assert "main" in _compile_mir(src)

    def test_quote_field(self) -> None:
        src = _csv_with_main("""\
            let quoted: String = quote_field("hello,world", "\\"")
            println(quoted)
        """)
        assert "main" in _compile_mir(src)

    def test_row_to_csv_string(self) -> None:
        src = _csv_with_main("""\
            let fields: List<String> = ["Alice", "30", "NYC"]
            let row_str: String = row_to_csv_string(fields, ",", "\\"")
            println(row_str)
        """)
        assert "main" in _compile_mir(src)

    def test_write(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["a", "b"]
            let rows: List<List<String>> = [["1", "2"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            let result: Result<Bool, CsvError> = write(table, "/tmp/test.csv")
            println("ok")
        """)
        assert "main" in _compile_mir(src)

    def test_write_with(self) -> None:
        src = _csv_with_main("""\
            let headers: List<String> = ["a", "b"]
            let rows: List<List<String>> = [["1", "2"]]
            let table: CsvTable = new CsvTable { headers: headers, rows: rows }
            let config: CsvConfig = new CsvConfig { delimiter: "\\t", quote_char: "\\"", has_headers: true }
            let result: Result<Bool, CsvError> = write_with(table, "/tmp/test.tsv", config)
            println("ok")
        """)
        assert "main" in _compile_mir(src)


# ---------------------------------------------------------------------------
# Internal parser helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestParserHelpers:
    def test_parse_csv_field_unquoted(self) -> None:
        src = _csv_with_main("""\
            let fr: FieldResult = parse_csv_field("hello,world", 0, 1, ",", "\\"")
            println(fr.value)
        """)
        assert "main" in _compile_mir(src)

    def test_parse_csv_field_quoted(self) -> None:
        src = _csv_with_main("""\
            let fr: FieldResult = parse_csv_field("\\"hello,world\\"", 0, 1, ",", "\\"")
            println(fr.value)
        """)
        assert "main" in _compile_mir(src)

    def test_parse_csv_row(self) -> None:
        src = _csv_with_main("""\
            let rr: RowResult = parse_csv_row("a,b,c\\n", 0, 1, ",", "\\"")
            println(str(len(rr.fields)))
        """)
        assert "main" in _compile_mir(src)
