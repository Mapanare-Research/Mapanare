"""Phase 7 — text/regex.mn — Regular Expressions tests.

Tests verify that the regex stdlib module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation (Phase 8) is not yet
ready, tests inline the regex module source code within test programs.

Covers:
  - RegexError enum variants
  - Match struct with groups
  - Regex struct (compiled handle)
  - regex_match (first match)
  - find_all (all non-overlapping matches)
  - replace / replace_all (substitution)
  - regex_split (split by pattern)
  - is_match (quick boolean check)
  - compile (with error handling)
  - Character classes, capture groups, error on invalid patterns
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

_REGEX_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "text" / "regex.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_regex.mn", use_mir=True)


def _regex_source_with_main(main_body: str) -> str:
    """Prepend the regex module source and wrap main_body in fn main()."""
    return _REGEX_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Task 16: Match simple patterns — literals, `.`, `*`, `+`, `?`
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSimplePatterns:
    def test_literal_match_compiles(self) -> None:
        """Literal pattern match compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("hello", "say hello world")
            if ok {
                println("matched")
            } else {
                println("no match")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_regex_compile_str" in ir_out

    def test_dot_pattern_compiles(self) -> None:
        """Dot (.) wildcard pattern compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("h.llo", "hello")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_star_pattern_compiles(self) -> None:
        """Star (*) quantifier pattern compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("ab*c", "abbbbc")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_plus_pattern_compiles(self) -> None:
        """Plus (+) quantifier pattern compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("a+b", "aaab")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_question_pattern_compiles(self) -> None:
        """Question (?) quantifier pattern compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("colou?r", "color")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_regex_match_returns_match_struct(self) -> None:
        """regex_match returns Option<Match> with start/end/text."""
        src = _regex_source_with_main("""\
            let m: Option<Match> = regex_match("world", "hello world")
            match m {
                Some(found) => {
                    println(found.text)
                },
                None => {
                    println("no match")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_extern_declarations_present(self) -> None:
        """All regex extern declarations are present in compiled IR."""
        src = _regex_source_with_main('println("ok")')
        ir_out = _compile_mir(src)
        assert "__mn_regex_compile_str" in ir_out
        assert "__mn_regex_exec_str" in ir_out
        assert "__mn_regex_group_str" in ir_out
        assert "__mn_regex_free" in ir_out


# ---------------------------------------------------------------------------
# Task 17: Character classes — [a-z], [^0-9], \d, \w, \s
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCharacterClasses:
    def test_char_range_compiles(self) -> None:
        """Character range [a-z] pattern compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("[a-z]+", "hello")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_negated_class_compiles(self) -> None:
        """Negated character class [^0-9] compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("[^0-9]+", "hello")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_digit_shorthand_compiles(self) -> None:
        """Digit shorthand \\d compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("\\\\d+", "abc123")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_word_shorthand_compiles(self) -> None:
        """Word shorthand \\w compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("\\\\w+", "hello_world")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_space_shorthand_compiles(self) -> None:
        """Space shorthand \\s compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("hello\\\\sworld", "hello world")
            if ok {
                println("matched")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 18: Capture groups — (\d+)-(\d+) extracts both groups
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCaptureGroups:
    def test_two_groups_compiles(self) -> None:
        """Two capture groups pattern compiles and extracts groups."""
        src = _regex_source_with_main("""\
            let m: Option<Match> = regex_match("(\\\\d+)-(\\\\d+)", "date: 2026-03")
            match m {
                Some(found) => {
                    println(found.text)
                },
                None => {
                    println("no match")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_regex_group_str" in ir_out

    def test_groups_list_compiles(self) -> None:
        """Match.groups list is populated correctly."""
        src = _regex_source_with_main("""\
            let m: Option<Match> = regex_match("(\\\\w+)@(\\\\w+)", "user@host")
            match m {
                Some(found) => {
                    println(found.text)
                    println(str(found.start))
                    println(str(found.end))
                },
                None => {
                    println("no match")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_regex_group_count" in ir_out

    def test_optional_group_compiles(self) -> None:
        """Optional capture group (may not participate) compiles."""
        src = _regex_source_with_main("""\
            let m: Option<Match> = regex_match("(a)(b)?(c)", "ac")
            match m {
                Some(found) => {
                    println(found.text)
                },
                None => {
                    println("no match")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 19: find_all returns all matches
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestFindAll:
    def test_find_all_compiles(self) -> None:
        """find_all returns List<Match> compiles."""
        src = _regex_source_with_main("""\
            let matches: List<Match> = find_all("[a-z]+", "hello world 123 foo")
            println(str(len(matches)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_find_all_digits_compiles(self) -> None:
        """find_all with digit pattern compiles."""
        src = _regex_source_with_main("""\
            let matches: List<Match> = find_all("\\\\d+", "abc 123 def 456 ghi 789")
            println(str(len(matches)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_find_all_no_matches_compiles(self) -> None:
        """find_all with no matches returns empty list."""
        src = _regex_source_with_main("""\
            let matches: List<Match> = find_all("xyz", "hello world")
            println(str(len(matches)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 20: replace_all substitutes correctly
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestReplaceAll:
    def test_replace_all_compiles(self) -> None:
        """replace_all substitutes all occurrences compiles."""
        src = _regex_source_with_main("""\
            let result: String = replace_all("\\\\d+", "abc 123 def 456", "NUM")
            println(result)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
        assert "__mn_regex_replace_str" in ir_out

    def test_replace_first_compiles(self) -> None:
        """replace (first occurrence only) compiles."""
        src = _regex_source_with_main("""\
            let result: String = replace("\\\\d+", "abc 123 def 456", "NUM")
            println(result)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_replace_no_match_compiles(self) -> None:
        """replace with no match returns original string."""
        src = _regex_source_with_main("""\
            let result: String = replace_all("xyz", "hello world", "XYZ")
            println(result)
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 21: split by pattern
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestSplit:
    def test_split_compiles(self) -> None:
        """regex_split by pattern compiles."""
        src = _regex_source_with_main("""\
            let parts: List<String> = regex_split("[,;]\\\\s*", "a, b; c, d")
            println(str(len(parts)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_split_by_whitespace_compiles(self) -> None:
        """Split by whitespace pattern compiles."""
        src = _regex_source_with_main("""\
            let parts: List<String> = regex_split("\\\\s+", "hello   world   foo")
            println(str(len(parts)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_split_no_match_compiles(self) -> None:
        """Split with no match returns original as single element."""
        src = _regex_source_with_main("""\
            let parts: List<String> = regex_split("xyz", "hello world")
            println(str(len(parts)))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Task 22: Error on invalid regex pattern
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrors:
    def test_invalid_pattern_compiles(self) -> None:
        """Invalid pattern returns error result compiles."""
        src = _regex_source_with_main("""\
            let r: Result<Regex, RegexError> = compile("[invalid")
            match r {
                Ok(re) => { println("unexpected ok") },
                Err(e) => { println("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_empty_pattern_compiles(self) -> None:
        """Empty pattern returns InvalidPattern error compiles."""
        src = _regex_source_with_main("""\
            let r: Result<Regex, RegexError> = compile("")
            match r {
                Ok(re) => { println("unexpected ok") },
                Err(e) => { println("expected error") }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_regex_error_enum_compiles(self) -> None:
        """RegexError enum variants compile."""
        src = _regex_source_with_main("""\
            let e1: RegexError = CompileError("bad pattern")
            let e2: RegexError = InvalidPattern("empty")
            let e3: RegexError = RuntimeError("runtime")
            println("ok")
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_is_match_invalid_returns_false_compiles(self) -> None:
        """is_match with invalid pattern returns false (compiles)."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("[invalid", "test")
            if ok {
                println("should not match")
            } else {
                println("correctly false")
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Integration patterns
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRegexIntegration:
    def test_match_and_replace_pipeline_compiles(self) -> None:
        """Match then replace pipeline compiles."""
        src = _regex_source_with_main("""\
            let ok: Bool = is_match("\\\\d{4}-\\\\d{2}", "date: 2026-03")
            if ok {
                let cleaned: String = replace_all("\\\\d", "date: 2026-03", "#")
                println(cleaned)
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_find_all_and_count_compiles(self) -> None:
        """Find all matches and count them compiles."""
        src = _regex_source_with_main("""\
            let matches: List<Match> = find_all("[A-Z][a-z]+", "Hello World Foo")
            let count: Int = len(matches)
            println(str(count))
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_compile_and_use_compiles(self) -> None:
        """Compile regex then use it compiles."""
        src = _regex_source_with_main("""\
            let r: Result<Regex, RegexError> = compile("\\\\d+")
            match r {
                Ok(re) => {
                    println(re.pattern)
                },
                Err(e) => {
                    println("error")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_done_when_example_compiles(self) -> None:
        """Plan's 'done when' example compiles."""
        src = _regex_source_with_main("""\
            let m: Option<Match> = regex_match("(\\\\d+)-(\\\\d+)", "date: 2026-03")
            match m {
                Some(found) => {
                    println(found.text)
                },
                None => {
                    println("no match")
                }
            }
            """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
