"""Mapanare lexer -- tokenizes .mn source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedCharacters, UnexpectedToken


@dataclass(frozen=True, slots=True)
class Token:
    """A single lexical token produced by the Mapanare lexer."""

    type: str
    value: str
    line: int
    column: int
    end_line: int
    end_column: int

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r}, {self.line}:{self.column})"


class LexError(Exception):
    """Raised when the lexer encounters invalid input."""

    def __init__(
        self,
        message: str,
        line: int,
        column: int,
        filename: str = "<input>",
    ) -> None:
        self.message = message
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(f"{filename}:{line}:{column}: {message}")


# All Mapanare keywords and their token types
KEYWORDS: dict[str, str] = {
    "let": "KW_LET",
    "mut": "KW_MUT",
    "fn": "KW_FN",
    "return": "KW_RETURN",
    "pub": "KW_PUB",
    "self": "KW_SELF",
    "agent": "KW_AGENT",
    "spawn": "KW_SPAWN",
    "sync": "KW_SYNC",
    "signal": "KW_SIGNAL",
    "stream": "KW_STREAM",
    "pipe": "KW_PIPE",
    "if": "KW_IF",
    "else": "KW_ELSE",
    "match": "KW_MATCH",
    "for": "KW_FOR",
    "in": "KW_IN",
    "type": "KW_TYPE",
    "struct": "KW_STRUCT",
    "enum": "KW_ENUM",
    "impl": "KW_IMPL",
    "import": "KW_IMPORT",
    "export": "KW_EXPORT",
    "true": "KW_TRUE",
    "false": "KW_FALSE",
    "none": "KW_NONE",
    "input": "KW_INPUT",
    "output": "KW_OUTPUT",
    "Tensor": "KW_TENSOR",
    "_": "KW_WILDCARD",
}

KEYWORD_SET: frozenset[str] = frozenset(KEYWORDS)

# Load grammar once at import time
_GRAMMAR_PATH = Path(__file__).parent / "mapanare.lark"
_lark = Lark(
    _GRAMMAR_PATH.read_text(encoding="utf-8"),
    parser="lalr",
)


def _do_tokenize(
    source: str,
    filename: str,
    *,
    keep_newlines: bool,
) -> list[Token]:
    """Internal tokenizer implementation."""
    try:
        tokens: list[Token] = []
        for lt in _lark.lex(source):
            if not keep_newlines and lt.type == "NEWLINE":
                continue
            tokens.append(
                Token(
                    type=lt.type,
                    value=str(lt),
                    line=lt.line or 1,
                    column=lt.column or 1,
                    end_line=lt.end_line or lt.line or 1,
                    end_column=lt.end_column or (lt.column or 1) + len(str(lt)),
                )
            )
        return tokens
    except UnexpectedCharacters as exc:
        raise LexError(
            f"Unexpected character: {exc.char!r}",
            line=exc.line,
            column=exc.column,
            filename=filename,
        ) from None
    except UnexpectedToken as exc:
        line = getattr(exc, "line", 1)
        column = getattr(exc, "column", 1)
        raise LexError(
            "Unexpected token",
            line=line,
            column=column,
            filename=filename,
        ) from None


def tokenize(source: str, *, filename: str = "<input>") -> list[Token]:
    """Tokenize Mapanare source code, filtering out NEWLINE tokens.

    Args:
        source: The Mapanare source code to tokenize.
        filename: Filename used in error messages.

    Returns:
        A list of Token objects.

    Raises:
        LexError: If the source contains invalid tokens.
    """
    return _do_tokenize(source, filename, keep_newlines=False)


def tokenize_with_newlines(source: str, *, filename: str = "<input>") -> list[Token]:
    """Tokenize Mapanare source code, preserving NEWLINE tokens.

    Args:
        source: The Mapanare source code to tokenize.
        filename: Filename used in error messages.

    Returns:
        A list of Token objects including NEWLINEs.

    Raises:
        LexError: If the source contains invalid tokens.
    """
    return _do_tokenize(source, filename, keep_newlines=True)
