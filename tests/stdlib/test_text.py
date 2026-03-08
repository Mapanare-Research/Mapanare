"""Tests for mapanare.text -- string manipulation utilities."""

from __future__ import annotations

import pytest

from stdlib.text import (
    camel_case,
    capitalize,
    center,
    char_at,
    char_code,
    contains,
    count,
    ends_with,
    from_char_code,
    index_of,
    is_alpha,
    is_alphanumeric,
    is_digit,
    is_empty,
    is_whitespace,
    join,
    kebab_case,
    lines,
    pad_end,
    pad_start,
    repeat,
    replace,
    replace_regex,
    reverse,
    slug,
    snake_case,
    split,
    starts_with,
    title_case,
    to_lower,
    to_upper,
    trim,
    trim_end,
    trim_start,
    truncate,
    words,
)

# ---------------------------------------------------------------------------
# Case conversion
# ---------------------------------------------------------------------------


class TestCaseConversion:
    def test_to_upper(self) -> None:
        assert to_upper("hello") == "HELLO"

    def test_to_lower(self) -> None:
        assert to_lower("HELLO") == "hello"

    def test_capitalize(self) -> None:
        assert capitalize("hello world") == "Hello world"

    def test_title_case(self) -> None:
        assert title_case("hello world") == "Hello World"

    def test_camel_case_from_snake(self) -> None:
        assert camel_case("hello_world") == "helloWorld"

    def test_camel_case_from_kebab(self) -> None:
        assert camel_case("hello-world") == "helloWorld"

    def test_snake_case_from_camel(self) -> None:
        assert snake_case("helloWorld") == "hello_world"

    def test_snake_case_from_pascal(self) -> None:
        assert snake_case("HelloWorld") == "hello_world"

    def test_kebab_case(self) -> None:
        assert kebab_case("helloWorld") == "hello-world"


# ---------------------------------------------------------------------------
# Trimming and padding
# ---------------------------------------------------------------------------


class TestTrimPad:
    def test_trim(self) -> None:
        assert trim("  hello  ") == "hello"

    def test_trim_start(self) -> None:
        assert trim_start("  hello  ") == "hello  "

    def test_trim_end(self) -> None:
        assert trim_end("  hello  ") == "  hello"

    def test_pad_start(self) -> None:
        assert pad_start("hi", 5) == "   hi"

    def test_pad_start_char(self) -> None:
        assert pad_start("42", 5, "0") == "00042"

    def test_pad_end(self) -> None:
        assert pad_end("hi", 5) == "hi   "

    def test_center(self) -> None:
        result = center("hi", 6)
        assert len(result) == 6
        assert "hi" in result

    def test_pad_invalid_fill(self) -> None:
        with pytest.raises(ValueError):
            pad_start("x", 5, "ab")


# ---------------------------------------------------------------------------
# Search and replace
# ---------------------------------------------------------------------------


class TestSearchReplace:
    def test_contains_true(self) -> None:
        assert contains("hello world", "world") is True

    def test_contains_false(self) -> None:
        assert contains("hello", "xyz") is False

    def test_starts_with(self) -> None:
        assert starts_with("hello", "hel") is True

    def test_ends_with(self) -> None:
        assert ends_with("hello", "llo") is True

    def test_index_of_found(self) -> None:
        assert index_of("abcdef", "cd") == 2

    def test_index_of_not_found(self) -> None:
        assert index_of("abcdef", "xyz") == -1

    def test_replace(self) -> None:
        assert replace("hello world", "world", "mapanare") == "hello mapanare"

    def test_replace_count(self) -> None:
        assert replace("aaa", "a", "b", count=2) == "bba"

    def test_replace_regex(self) -> None:
        assert replace_regex("abc123def", r"\d+", "NUM") == "abcNUMdef"


# ---------------------------------------------------------------------------
# Splitting and joining
# ---------------------------------------------------------------------------


class TestSplitJoin:
    def test_split_default(self) -> None:
        assert split("a b c") == ["a", "b", "c"]

    def test_split_sep(self) -> None:
        assert split("a,b,c", ",") == ["a", "b", "c"]

    def test_split_max(self) -> None:
        assert split("a,b,c", ",", max_splits=1) == ["a", "b,c"]

    def test_join(self) -> None:
        assert join(["a", "b", "c"], ", ") == "a, b, c"

    def test_join_empty(self) -> None:
        assert join(["a", "b"], "") == "ab"

    def test_lines(self) -> None:
        assert lines("a\nb\nc") == ["a", "b", "c"]

    def test_words(self) -> None:
        assert words("hello  world\tfoo") == ["hello", "world", "foo"]


# ---------------------------------------------------------------------------
# Character utilities
# ---------------------------------------------------------------------------


class TestCharUtils:
    def test_char_at(self) -> None:
        assert char_at("hello", 1) == "e"

    def test_char_code(self) -> None:
        assert char_code("A") == 65

    def test_from_char_code(self) -> None:
        assert from_char_code(65) == "A"

    def test_is_alpha(self) -> None:
        assert is_alpha("abc") is True
        assert is_alpha("abc123") is False
        assert is_alpha("") is False

    def test_is_digit(self) -> None:
        assert is_digit("123") is True
        assert is_digit("12a") is False

    def test_is_alphanumeric(self) -> None:
        assert is_alphanumeric("abc123") is True
        assert is_alphanumeric("abc 123") is False

    def test_is_whitespace(self) -> None:
        assert is_whitespace("  \t\n") is True
        assert is_whitespace("a") is False
        assert is_whitespace("") is False


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


class TestMisc:
    def test_reverse(self) -> None:
        assert reverse("hello") == "olleh"

    def test_repeat(self) -> None:
        assert repeat("ab", 3) == "ababab"

    def test_truncate_short(self) -> None:
        assert truncate("hi", 10) == "hi"

    def test_truncate_long(self) -> None:
        assert truncate("hello world", 8) == "hello..."

    def test_truncate_custom_suffix(self) -> None:
        assert truncate("hello world", 7, "~") == "hello ~"

    def test_count(self) -> None:
        assert count("banana", "an") == 2

    def test_is_empty(self) -> None:
        assert is_empty("") is True
        assert is_empty("   ") is True
        assert is_empty("a") is False

    def test_slug(self) -> None:
        assert slug("Hello World!") == "hello-world"

    def test_slug_special_chars(self) -> None:
        assert slug("  Hello -- World!!  ") == "hello-world"
