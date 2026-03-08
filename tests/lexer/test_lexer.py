"""Comprehensive tests for the Mapanare lexer (Phase 2.1)."""

import pytest

from mapa.lexer import LexError, Token, tokenize, tokenize_with_newlines

# ── Helpers ──────────────────────────────────────────────────


def types(source: str) -> list[str]:
    """Return just the token types for *source*."""
    return [t.type for t in tokenize(source)]


def values(source: str) -> list[str]:
    """Return just the token values for *source*."""
    return [t.value for t in tokenize(source)]


def single(source: str) -> Token:
    """Assert *source* produces exactly one token and return it."""
    tokens = tokenize(source)
    assert len(tokens) == 1, f"Expected 1 token, got {len(tokens)}: {tokens}"
    return tokens[0]


# ── Keywords (26) ────────────────────────────────────────────


class TestKeywords:
    """Every Mapanare keyword must lex as its own KW_* token type."""

    ALL_KEYWORDS: list[tuple[str, str]] = [
        ("let", "KW_LET"),
        ("mut", "KW_MUT"),
        ("fn", "KW_FN"),
        ("return", "KW_RETURN"),
        ("pub", "KW_PUB"),
        ("self", "KW_SELF"),
        ("agent", "KW_AGENT"),
        ("spawn", "KW_SPAWN"),
        ("sync", "KW_SYNC"),
        ("signal", "KW_SIGNAL"),
        ("stream", "KW_STREAM"),
        ("pipe", "KW_PIPE"),
        ("if", "KW_IF"),
        ("else", "KW_ELSE"),
        ("match", "KW_MATCH"),
        ("for", "KW_FOR"),
        ("in", "KW_IN"),
        ("type", "KW_TYPE"),
        ("struct", "KW_STRUCT"),
        ("enum", "KW_ENUM"),
        ("impl", "KW_IMPL"),
        ("import", "KW_IMPORT"),
        ("export", "KW_EXPORT"),
        ("true", "KW_TRUE"),
        ("false", "KW_FALSE"),
        ("none", "KW_NONE"),
    ]

    @pytest.mark.parametrize("text,expected_type", ALL_KEYWORDS)
    def test_keyword(self, text: str, expected_type: str) -> None:
        tok = single(text)
        assert tok.type == expected_type
        assert tok.value == text

    def test_all_26_keywords_present(self) -> None:
        assert len(self.ALL_KEYWORDS) == 26

    def test_keyword_prefix_is_name(self) -> None:
        """'letter' should lex as NAME, not KW_LET + NAME."""
        tok = single("letter")
        assert tok.type == "NAME"
        assert tok.value == "letter"

    def test_keyword_with_trailing_digits(self) -> None:
        tok = single("return2")
        assert tok.type == "NAME"

    def test_keyword_with_underscore_suffix(self) -> None:
        tok = single("let_")
        assert tok.type == "NAME"

    def test_keyword_with_underscore_prefix(self) -> None:
        tok = single("_let")
        assert tok.type == "NAME"


# ── Operators ────────────────────────────────────────────────


class TestOperators:
    """All Mapanare operators must lex correctly."""

    OPERATORS: list[tuple[str, str]] = [
        # Multi-character
        ("|>", "PIPE_OP"),
        ("->", "ARROW"),
        ("=>", "FAT_ARROW"),
        ("::", "DOUBLE_COLON"),
        ("..=", "RANGE_INCL"),
        ("..", "RANGE"),
        ("<-", "SEND"),
        ("<=", "LE"),
        (">=", "GE"),
        ("==", "EQ"),
        ("!=", "NE"),
        ("&&", "AND"),
        ("||", "OR"),
        ("+=", "PLUS_ASSIGN"),
        ("-=", "MINUS_ASSIGN"),
        ("*=", "STAR_ASSIGN"),
        ("/=", "SLASH_ASSIGN"),
        # Single-character
        ("@", "AT"),
        (".", "DOT"),
        ("+", "PLUS"),
        ("-", "MINUS"),
        ("*", "STAR"),
        ("/", "SLASH"),
        ("%", "PERCENT"),
        ("<", "LT"),
        (">", "GT"),
        ("!", "BANG"),
        ("=", "ASSIGN"),
        ("?", "QUESTION"),
    ]

    @pytest.mark.parametrize("text,expected_type", OPERATORS)
    def test_operator(self, text: str, expected_type: str) -> None:
        tok = single(text)
        assert tok.type == expected_type
        assert tok.value == text

    def test_pipe_op_not_split(self) -> None:
        """'|>' must be a single PIPE_OP, not two tokens."""
        assert types("|>") == ["PIPE_OP"]

    def test_arrow_not_split(self) -> None:
        assert types("->") == ["ARROW"]

    def test_range_incl_not_range_plus_assign(self) -> None:
        assert types("..=") == ["RANGE_INCL"]

    def test_send_not_lt_minus(self) -> None:
        assert types("<-") == ["SEND"]

    def test_le_not_lt_assign(self) -> None:
        assert types("<=") == ["LE"]

    def test_consecutive_operators(self) -> None:
        assert types("+ - * /") == ["PLUS", "MINUS", "STAR", "SLASH"]

    def test_operators_without_spaces(self) -> None:
        assert types("a+b") == ["NAME", "PLUS", "NAME"]


# ── Delimiters ───────────────────────────────────────────────


class TestDelimiters:
    """All delimiters must lex correctly."""

    DELIMITERS: list[tuple[str, str]] = [
        ("(", "LPAREN"),
        (")", "RPAREN"),
        ("{", "LBRACE"),
        ("}", "RBRACE"),
        ("[", "LBRACKET"),
        ("]", "RBRACKET"),
        (",", "COMMA"),
        (":", "COLON"),
        (";", "SEMICOLON"),
    ]

    @pytest.mark.parametrize("text,expected_type", DELIMITERS)
    def test_delimiter(self, text: str, expected_type: str) -> None:
        tok = single(text)
        assert tok.type == expected_type
        assert tok.value == text

    def test_nested_delimiters(self) -> None:
        assert types("({[]})") == [
            "LPAREN",
            "LBRACE",
            "LBRACKET",
            "RBRACKET",
            "RBRACE",
            "RPAREN",
        ]


# ── Integer Literals ─────────────────────────────────────────


class TestIntLiterals:
    """Decimal, hex, binary, and octal integer literals."""

    def test_zero(self) -> None:
        tok = single("0")
        assert tok.type == "DEC_INT"
        assert tok.value == "0"

    def test_simple_decimal(self) -> None:
        tok = single("42")
        assert tok.type == "DEC_INT"
        assert tok.value == "42"

    def test_decimal_with_underscores(self) -> None:
        tok = single("1_000_000")
        assert tok.type == "DEC_INT"
        assert tok.value == "1_000_000"

    def test_hex_lowercase(self) -> None:
        tok = single("0xff")
        assert tok.type == "HEX_INT"
        assert tok.value == "0xff"

    def test_hex_uppercase(self) -> None:
        tok = single("0xFF")
        assert tok.type == "HEX_INT"
        assert tok.value == "0xFF"

    def test_hex_mixed(self) -> None:
        tok = single("0xDEAD_BEEF")
        assert tok.type == "HEX_INT"
        assert tok.value == "0xDEAD_BEEF"

    def test_binary(self) -> None:
        tok = single("0b1010")
        assert tok.type == "BIN_INT"
        assert tok.value == "0b1010"

    def test_binary_with_underscores(self) -> None:
        tok = single("0b1111_0000")
        assert tok.type == "BIN_INT"
        assert tok.value == "0b1111_0000"

    def test_octal(self) -> None:
        tok = single("0o77")
        assert tok.type == "OCT_INT"
        assert tok.value == "0o77"

    def test_octal_with_underscores(self) -> None:
        tok = single("0o7_7_7")
        assert tok.type == "OCT_INT"
        assert tok.value == "0o7_7_7"


# ── Float Literals ───────────────────────────────────────────


class TestFloatLiterals:
    """Floating-point literals with optional scientific notation."""

    def test_simple_float(self) -> None:
        tok = single("3.14")
        assert tok.type == "FLOAT_LIT"
        assert tok.value == "3.14"

    def test_float_with_underscores(self) -> None:
        tok = single("1_000.000_1")
        assert tok.type == "FLOAT_LIT"
        assert tok.value == "1_000.000_1"

    def test_scientific_notation(self) -> None:
        tok = single("1.0e10")
        assert tok.type == "FLOAT_LIT"

    def test_scientific_negative_exponent(self) -> None:
        tok = single("1.0e-10")
        assert tok.type == "FLOAT_LIT"
        assert tok.value == "1.0e-10"

    def test_scientific_positive_exponent(self) -> None:
        tok = single("2.5E+3")
        assert tok.type == "FLOAT_LIT"

    def test_scientific_no_decimal(self) -> None:
        """'1e10' is a valid float (integer with exponent)."""
        tok = single("1e10")
        assert tok.type == "FLOAT_LIT"

    def test_float_not_split(self) -> None:
        """'3.14' must be one FLOAT_LIT, not DEC_INT DOT DEC_INT."""
        assert types("3.14") == ["FLOAT_LIT"]


# ── String Literals ──────────────────────────────────────────


class TestStringLiterals:
    """Double-quoted string literals with escape sequences."""

    def test_empty_string(self) -> None:
        tok = single('""')
        assert tok.type == "STRING_LIT"
        assert tok.value == '""'

    def test_simple_string(self) -> None:
        tok = single('"hello, world"')
        assert tok.type == "STRING_LIT"
        assert tok.value == '"hello, world"'

    def test_string_with_escapes(self) -> None:
        tok = single(r'"line one\nline two"')
        assert tok.type == "STRING_LIT"

    def test_string_with_tab_escape(self) -> None:
        tok = single(r'"col1\tcol2"')
        assert tok.type == "STRING_LIT"

    def test_string_with_escaped_quote(self) -> None:
        tok = single(r'"say \"hello\""')
        assert tok.type == "STRING_LIT"

    def test_string_with_escaped_backslash(self) -> None:
        tok = single(r'"path\\to\\file"')
        assert tok.type == "STRING_LIT"

    def test_string_with_interpolation_syntax(self) -> None:
        """Interpolation like '${x}' is part of the string token at lex time."""
        tok = single('"value is ${x}"')
        assert tok.type == "STRING_LIT"
        assert "${x}" in tok.value

    def test_unterminated_string_raises(self) -> None:
        with pytest.raises(LexError):
            tokenize('"unterminated')


# ── Char Literals ────────────────────────────────────────────


class TestCharLiterals:
    """Single-quoted character literals."""

    def test_simple_char(self) -> None:
        tok = single("'a'")
        assert tok.type == "CHAR_LIT"
        assert tok.value == "'a'"

    def test_escaped_char(self) -> None:
        tok = single(r"'\n'")
        assert tok.type == "CHAR_LIT"

    def test_escaped_quote_char(self) -> None:
        tok = single(r"'\''")
        assert tok.type == "CHAR_LIT"


# ── Comments ─────────────────────────────────────────────────


class TestComments:
    """Line and block comments must be ignored by the lexer."""

    def test_line_comment_ignored(self) -> None:
        assert types("let x = 42 // this is a comment") == [
            "KW_LET",
            "NAME",
            "ASSIGN",
            "DEC_INT",
        ]

    def test_line_comment_only(self) -> None:
        assert tokenize("// just a comment") == []

    def test_block_comment_ignored(self) -> None:
        assert types("let /* skip */ x") == ["KW_LET", "NAME"]

    def test_multiline_block_comment(self) -> None:
        source = "let /* this\nspans\nlines */ x"
        assert types(source) == ["KW_LET", "NAME"]

    def test_block_comment_with_stars(self) -> None:
        source = "let /*** stars ***/ x"
        assert types(source) == ["KW_LET", "NAME"]

    def test_empty_block_comment(self) -> None:
        assert types("let /**/ x") == ["KW_LET", "NAME"]


# ── Identifiers ──────────────────────────────────────────────


class TestIdentifiers:
    """NAME tokens for identifiers."""

    def test_simple_name(self) -> None:
        tok = single("foo")
        assert tok.type == "NAME"
        assert tok.value == "foo"

    def test_name_with_underscore(self) -> None:
        tok = single("my_var")
        assert tok.type == "NAME"

    def test_name_starting_with_underscore(self) -> None:
        tok = single("_private")
        assert tok.type == "NAME"

    def test_name_with_digits(self) -> None:
        tok = single("x2")
        assert tok.type == "NAME"

    def test_single_underscore(self) -> None:
        tok = single("_")
        assert tok.type == "KW_WILDCARD"

    def test_uppercase_name(self) -> None:
        tok = single("MyAgent")
        assert tok.type == "NAME"

    def test_all_caps(self) -> None:
        tok = single("MAX_SIZE")
        assert tok.type == "NAME"


# ── Whitespace Handling ──────────────────────────────────────


class TestWhitespace:
    """Mapanare uses braces for blocks; whitespace is non-significant
    except for separating tokens. Newlines are tracked for error
    reporting but filtered from the default token stream."""

    def test_spaces_ignored(self) -> None:
        assert types("let   x   =   42") == ["KW_LET", "NAME", "ASSIGN", "DEC_INT"]

    def test_tabs_ignored(self) -> None:
        assert types("let\tx\t=\t42") == ["KW_LET", "NAME", "ASSIGN", "DEC_INT"]

    def test_newlines_filtered_by_default(self) -> None:
        source = "let x = 42\nlet y = 10"
        toks = tokenize(source)
        assert "NEWLINE" not in [t.type for t in toks]

    def test_newlines_preserved_when_requested(self) -> None:
        source = "let x = 42\nlet y = 10"
        toks = tokenize_with_newlines(source)
        assert "NEWLINE" in [t.type for t in toks]

    def test_multiple_blank_lines_collapsed(self) -> None:
        source = "a\n\n\nb"
        toks = tokenize_with_newlines(source)
        newlines = [t for t in toks if t.type == "NEWLINE"]
        assert len(newlines) == 1  # collapsed into one NEWLINE

    def test_empty_source(self) -> None:
        assert tokenize("") == []

    def test_whitespace_only(self) -> None:
        assert tokenize("   \t  ") == []


# ── Error Reporting ──────────────────────────────────────────


class TestErrorReporting:
    """Errors must include line, column, and filename."""

    def test_unexpected_char_raises(self) -> None:
        with pytest.raises(LexError) as exc_info:
            tokenize("let x = `bad`")
        err = exc_info.value
        assert err.line >= 1
        assert err.column >= 1

    def test_error_includes_filename(self) -> None:
        with pytest.raises(LexError) as exc_info:
            tokenize("let x = `bad`", filename="test.mn")
        assert "test.mn" in str(exc_info.value)

    def test_error_line_tracking(self) -> None:
        source = "let x = 42\nlet y = `bad`"
        with pytest.raises(LexError) as exc_info:
            tokenize(source)
        assert exc_info.value.line == 2

    def test_token_line_column(self) -> None:
        """Tokens must carry correct line and column info."""
        source = "let x = 42"
        toks = tokenize(source)
        # 'let' starts at column 1
        assert toks[0].line == 1
        assert toks[0].column == 1
        # 'x' starts at column 5
        assert toks[1].column == 5
        # '=' starts at column 7
        assert toks[2].column == 7
        # '42' starts at column 9
        assert toks[3].column == 9

    def test_multiline_token_positions(self) -> None:
        source = "let x = 42\nlet y = 10"
        toks = tokenize(source)
        # Second 'let' is on line 2
        second_let = [t for t in toks if t.type == "KW_LET"][1]
        assert second_let.line == 2
        assert second_let.column == 1


# ── Full Program Tokenization ────────────────────────────────


class TestFullProgram:
    """Tokenize complete Mapanare programs from the spec examples."""

    def test_hello_world(self) -> None:
        source = """\
fn main() {
    print("Hello, Mapanare!")
}"""
        assert types(source) == [
            "KW_FN",
            "NAME",  # main
            "LPAREN",
            "RPAREN",
            "LBRACE",
            "NAME",  # print
            "LPAREN",
            "STRING_LIT",
            "RPAREN",
            "RBRACE",
        ]

    def test_let_binding(self) -> None:
        source = "let mut x: Int = 42"
        assert types(source) == [
            "KW_LET",
            "KW_MUT",
            "NAME",  # x
            "COLON",
            "NAME",  # Int
            "ASSIGN",
            "DEC_INT",
        ]

    def test_agent_definition_fragment(self) -> None:
        source = """\
agent Greeter {
    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}"""
        toks = tokenize(source)
        type_list = [t.type for t in toks]
        assert type_list[0] == "KW_AGENT"
        assert "ARROW" in type_list
        assert "KW_RETURN" in type_list
        assert "PLUS" in type_list

    def test_pipe_expression(self) -> None:
        source = "data |> tokenize |> classify |> format"
        assert types(source) == [
            "NAME",
            "PIPE_OP",
            "NAME",
            "PIPE_OP",
            "NAME",
            "PIPE_OP",
            "NAME",
        ]

    def test_spawn_and_sync(self) -> None:
        source = "let g = spawn Greeter()"
        assert types(source) == [
            "KW_LET",
            "NAME",
            "ASSIGN",
            "KW_SPAWN",
            "NAME",
            "LPAREN",
            "RPAREN",
        ]

    def test_channel_send(self) -> None:
        source = 'greeter.name <- "World"'
        assert types(source) == [
            "NAME",
            "DOT",
            "NAME",
            "SEND",
            "STRING_LIT",
        ]

    def test_match_expression(self) -> None:
        source = """\
match x {
    Some(v) => print(v),
    None => print("nothing"),
}"""
        toks = tokenize(source)
        type_list = [t.type for t in toks]
        assert "KW_MATCH" in type_list
        assert "FAT_ARROW" in type_list

    def test_for_loop(self) -> None:
        source = "for x in items { print(x) }"
        assert types(source) == [
            "KW_FOR",
            "NAME",
            "KW_IN",
            "NAME",
            "LBRACE",
            "NAME",
            "LPAREN",
            "NAME",
            "RPAREN",
            "RBRACE",
        ]

    def test_generic_type(self) -> None:
        source = "Option<Int>"
        assert types(source) == ["NAME", "LT", "NAME", "GT"]

    def test_range_expression(self) -> None:
        assert types("0..10") == ["DEC_INT", "RANGE", "DEC_INT"]
        assert types("0..=10") == ["DEC_INT", "RANGE_INCL", "DEC_INT"]

    def test_error_propagation(self) -> None:
        source = "let n = parse_int(s)?"
        toks = tokenize(source)
        assert toks[-1].type == "QUESTION"

    def test_namespace_access(self) -> None:
        source = "Math::sqrt"
        assert types(source) == ["NAME", "DOUBLE_COLON", "NAME"]

    def test_decorator(self) -> None:
        source = "@restart"
        assert types(source) == ["AT", "NAME"]

    def test_struct_definition(self) -> None:
        source = """\
struct Point {
    x: Float,
    y: Float,
}"""
        assert types(source) == [
            "KW_STRUCT",
            "NAME",
            "LBRACE",
            "NAME",
            "COLON",
            "NAME",
            "COMMA",
            "NAME",
            "COLON",
            "NAME",
            "COMMA",
            "RBRACE",
        ]

    def test_import_export(self) -> None:
        assert types("import foo") == ["KW_IMPORT", "NAME"]
        assert types("export bar") == ["KW_EXPORT", "NAME"]

    def test_compound_assignment(self) -> None:
        assert types("x += 1") == ["NAME", "PLUS_ASSIGN", "DEC_INT"]
        assert types("x -= 1") == ["NAME", "MINUS_ASSIGN", "DEC_INT"]
        assert types("x *= 2") == ["NAME", "STAR_ASSIGN", "DEC_INT"]
        assert types("x /= 2") == ["NAME", "SLASH_ASSIGN", "DEC_INT"]

    def test_logical_operators(self) -> None:
        assert types("a && b || !c") == [
            "NAME",
            "AND",
            "NAME",
            "OR",
            "BANG",
            "NAME",
        ]

    def test_comparison_operators(self) -> None:
        assert types("a == b != c < d > e <= f >= g") == [
            "NAME",
            "EQ",
            "NAME",
            "NE",
            "NAME",
            "LT",
            "NAME",
            "GT",
            "NAME",
            "LE",
            "NAME",
            "GE",
            "NAME",
        ]

    def test_mixed_program(self) -> None:
        """A realistic multi-line program with diverse tokens."""
        source = """\
fn add(a: Int, b: Int) -> Int {
    let result = a + b
    return result
}

fn main() {
    let x = add(1, 2)
    if x > 0 {
        print("positive")
    } else {
        print("non-positive")
    }
}"""
        toks = tokenize(source)
        assert len(toks) > 0
        # Spot-check key tokens
        type_list = [t.type for t in toks]
        assert type_list.count("KW_FN") == 2
        assert type_list.count("KW_LET") == 2
        assert "KW_IF" in type_list
        assert "KW_ELSE" in type_list
        assert "ARROW" in type_list
        assert "KW_RETURN" in type_list
