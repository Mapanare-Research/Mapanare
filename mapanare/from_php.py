"""PHP-to-Mapanare transpiler.

Translates PHP 7.4+ source code into Mapanare (.mn) source text, which can
then be fed through the standard Mapanare compilation pipeline.

Since Python has no built-in PHP parser, this module includes a regex-based
tokenizer and a top-down translator that walks the token stream.

Usage::

    from mapanare.from_php import translate_to_mn

    mn_source = translate_to_mn(php_source, "example.php")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class TranslateError(Exception):
    """Raised when a PHP construct cannot be translated to Mapanare."""

    def __init__(self, message: str, lineno: int = 0, filename: str = "<unknown>"):
        self.message = message
        self.lineno = lineno
        self.filename = filename
        super().__init__(f"{filename}:{lineno}: {message}")


# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------

_PHP_TYPE_MAP: dict[str, str] = {
    "int": "Int",
    "integer": "Int",
    "float": "Float",
    "double": "Float",
    "string": "String",
    "bool": "Bool",
    "boolean": "Bool",
    "void": "Void",
    "mixed": "any",
    "array": "List<any>",
    "object": "any",
    "null": "Void",
    "self": "Self",
    "callable": "any",
    "iterable": "List<any>",
    "?int": "Option<Int>",
    "?float": "Option<Float>",
    "?string": "Option<String>",
    "?bool": "Option<Bool>",
}

# ---------------------------------------------------------------------------
# PHP stdlib function mapping
# ---------------------------------------------------------------------------

_PHP_FUNC_MAP: dict[str, str] = {
    "strlen": "len",
    "count": "len",
    "sizeof": "len",
    "array_push": ".push",
    "strtolower": ".to_lower",
    "strtoupper": ".to_upper",
    "trim": ".trim",
    "ltrim": ".trim_start",
    "rtrim": ".trim_end",
    "str_replace": ".replace",
    "substr": ".substr",
    "explode": ".split",
    "implode": "join",
    "in_array": ".contains",
    "intval": "int",
    "floatval": "float",
    "strval": "str",
    "abs": "abs",
    "sqrt": "sqrt",
    "floor": "floor",
    "ceil": "ceil",
    "max": "max",
    "min": "min",
    "isset": "!= None",
    "empty": "len() == 0",
    "var_dump": "print",
    "print_r": "print",
    "is_array": 'typeof() == "List"',
    "is_string": 'typeof() == "String"',
    "is_int": 'typeof() == "Int"',
    "echo": "print",
}

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


class TokKind(Enum):
    KEYWORD = auto()
    VARIABLE = auto()
    STRING = auto()
    NUMBER = auto()
    OPERATOR = auto()
    PUNC = auto()
    IDENT = auto()
    ARROW = auto()  # ->
    FAT_ARROW = auto()  # =>
    DOUBLE_COLON = auto()  # ::
    ELLIPSIS = auto()  # ...
    EOF = auto()


@dataclass
class Token:
    kind: TokKind
    value: str
    line: int


_KEYWORDS = frozenset(
    {
        "function",
        "class",
        "interface",
        "trait",
        "extends",
        "implements",
        "public",
        "private",
        "protected",
        "static",
        "abstract",
        "final",
        "const",
        "var",
        "if",
        "elseif",
        "else",
        "while",
        "do",
        "for",
        "foreach",
        "as",
        "switch",
        "case",
        "default",
        "break",
        "continue",
        "return",
        "echo",
        "print",
        "new",
        "null",
        "true",
        "false",
        "try",
        "catch",
        "finally",
        "throw",
        "use",
        "namespace",
        "include",
        "require",
        "include_once",
        "require_once",
        "fn",
        "match",
        "array",
        "list",
        "yield",
    }
)

# Order matters: longer operators first
_TOKEN_PATTERNS: list[tuple[str, TokKind | None]] = [
    # Whitespace (skip)
    (r"[ \t]+", None),
    # Newlines (skip, but we count them)
    (r"\n", None),
    # Single-line comments
    (r"//[^\n]*", None),
    (r"#[^\n]*", None),
    # Multi-line comments
    (r"/\*[\s\S]*?\*/", None),
    # PHP open/close tags
    (r"<\?php\b", None),
    (r"<\?=", None),
    (r"<\?", None),
    (r"\?>", None),
    # Double-quoted string (handled specially for interpolation)
    (r'"(?:[^"\\]|\\.)*"', TokKind.STRING),
    # Single-quoted string
    (r"'(?:[^'\\]|\\.)*'", TokKind.STRING),
    # Numbers (float before int)
    (r"\d+\.\d+", TokKind.NUMBER),
    (r"\d+", TokKind.NUMBER),
    # Multi-char operators (order matters)
    (r"===", TokKind.OPERATOR),
    (r"!==", TokKind.OPERATOR),
    (r"<=>", TokKind.OPERATOR),
    (r"=>", TokKind.FAT_ARROW),
    (r"->", TokKind.ARROW),
    (r"::", TokKind.DOUBLE_COLON),
    (r"\.\.\.", TokKind.ELLIPSIS),
    (r"==", TokKind.OPERATOR),
    (r"!=", TokKind.OPERATOR),
    (r"<=", TokKind.OPERATOR),
    (r">=", TokKind.OPERATOR),
    (r"&&", TokKind.OPERATOR),
    (r"\|\|", TokKind.OPERATOR),
    (r"\*\*", TokKind.OPERATOR),
    (r"\.\.", TokKind.OPERATOR),
    (r"\+=", TokKind.OPERATOR),
    (r"-=", TokKind.OPERATOR),
    (r"\*=", TokKind.OPERATOR),
    (r"/=", TokKind.OPERATOR),
    (r"\.=", TokKind.OPERATOR),
    (r"\+\+", TokKind.OPERATOR),
    (r"--", TokKind.OPERATOR),
    (r"<<", TokKind.OPERATOR),
    (r">>", TokKind.OPERATOR),
    # Single-char operators
    (r"[+\-*/%<>=!&|^~@?]", TokKind.OPERATOR),
    # String concat operator
    (r"\.", TokKind.OPERATOR),
    # Variables
    (r"\$[a-zA-Z_][a-zA-Z0-9_]*", TokKind.VARIABLE),
    # Identifiers / keywords
    (r"[a-zA-Z_][a-zA-Z0-9_]*", TokKind.IDENT),
    # Punctuation
    (r"[{}()\[\];:,\\]", TokKind.PUNC),
]

_TOKEN_REGEX = re.compile("|".join(f"({pat})" for pat, _ in _TOKEN_PATTERNS))


def _tokenize(source: str, filename: str = "<unknown>") -> list[Token]:
    """Tokenize PHP source into a list of tokens."""
    tokens: list[Token] = []
    line = 1
    pos = 0

    while pos < len(source):
        m = _TOKEN_REGEX.match(source, pos)
        if m is None:
            # Skip unrecognized character
            if source[pos] == "\n":
                line += 1
            pos += 1
            continue

        text = m.group()
        matched_group = m.lastindex
        if matched_group is None:
            pos += len(text)
            continue

        kind = _TOKEN_PATTERNS[matched_group - 1][1]

        # Count newlines in matched text
        line += text.count("\n")

        if kind is not None:
            # Classify identifiers as keywords if applicable
            if kind == TokKind.IDENT and text.lower() in _KEYWORDS:
                tokens.append(Token(TokKind.KEYWORD, text.lower(), line))
            elif kind == TokKind.IDENT:
                tokens.append(Token(kind, text, line))
            else:
                tokens.append(Token(kind, text, line))

        pos += len(text)

    tokens.append(Token(TokKind.EOF, "", line))
    return tokens


# ---------------------------------------------------------------------------
# Helper: indentation
# ---------------------------------------------------------------------------


@dataclass
class _Indent:
    """Tracks current indentation level for output formatting."""

    level: int = 0
    _tab: str = "    "

    def push(self) -> None:
        self.level += 1

    def pop(self) -> None:
        self.level = max(0, self.level - 1)

    def prefix(self) -> str:
        return self._tab * self.level


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------


@dataclass
class PhpTranslator:
    """Translates PHP source into Mapanare source text.

    The translator tokenizes the input, then walks top-level constructs
    (functions, classes, statements) emitting valid ``.mn`` source that
    can be parsed by the standard Mapanare parser.
    """

    filename: str = "<unknown>"
    _indent: _Indent = field(default_factory=_Indent)
    _lines: list[str] = field(default_factory=list)
    _tokens: list[Token] = field(default_factory=list)
    _pos: int = 0
    _current_class: str | None = None
    _declared_vars: list[set[str]] = field(default_factory=lambda: [set()])

    # -- Scope helpers --

    def _push_scope(self) -> None:
        self._declared_vars.append(set())

    def _pop_scope(self) -> None:
        if len(self._declared_vars) > 1:
            self._declared_vars.pop()

    def _is_declared(self, name: str) -> bool:
        for scope in reversed(self._declared_vars):
            if name in scope:
                return True
        return False

    def _declare(self, name: str) -> None:
        self._declared_vars[-1].add(name)

    # -- Token helpers --

    def _cur(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TokKind.EOF, "", 0)

    def _peek(self, offset: int = 1) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return Token(TokKind.EOF, "", 0)

    def _advance(self) -> Token:
        tok = self._cur()
        if self._pos < len(self._tokens):
            self._pos += 1
        return tok

    def _expect(self, kind: TokKind, value: str | None = None) -> Token:
        tok = self._cur()
        if tok.kind != kind or (value is not None and tok.value != value):
            expected = f"{kind.name}"
            if value:
                expected += f" '{value}'"
            raise TranslateError(
                f"expected {expected}, got {tok.kind.name} '{tok.value}'",
                lineno=tok.line,
                filename=self.filename,
            )
        return self._advance()

    def _match(self, kind: TokKind, value: str | None = None) -> Token | None:
        tok = self._cur()
        if tok.kind == kind and (value is None or tok.value == value):
            return self._advance()
        return None

    def _at(self, kind: TokKind, value: str | None = None) -> bool:
        tok = self._cur()
        return tok.kind == kind and (value is None or tok.value == value)

    def _at_eof(self) -> bool:
        return self._cur().kind == TokKind.EOF

    # -- Output helpers --

    def _emit(self, text: str) -> None:
        self._lines.append(self._indent.prefix() + text)

    def _emit_raw(self, text: str) -> None:
        self._lines.append(text)

    # -- Type translation --

    def _translate_type(self, type_str: str) -> str:
        """Translate a PHP type hint string to a Mapanare type."""
        type_str = type_str.strip()
        if not type_str:
            return "any"

        # Nullable type
        if type_str.startswith("?"):
            inner = self._translate_type(type_str[1:])
            return f"Option<{inner}>"

        return _PHP_TYPE_MAP.get(type_str.lower(), type_str)

    def _infer_type_from_token(self, tok: Token) -> str:
        """Infer a Mapanare type from a token."""
        if tok.kind == TokKind.NUMBER:
            if "." in tok.value:
                return "Float"
            return "Int"
        if tok.kind == TokKind.STRING:
            return "String"
        if tok.kind == TokKind.KEYWORD:
            if tok.value == "true" or tok.value == "false":
                return "Bool"
            if tok.value == "null":
                return "Option<any>"
        return "any"

    # -- Expression parsing --

    def _translate_expr(self) -> str:
        """Parse and translate a PHP expression."""
        return self._translate_ternary()

    def _translate_ternary(self) -> str:
        """Parse ternary: expr ? expr : expr."""
        left = self._translate_or()
        if self._match(TokKind.OPERATOR, "?"):
            then_expr = self._translate_expr()
            self._expect(TokKind.PUNC, ":")
            else_expr = self._translate_expr()
            return f"if {left} {{ {then_expr} }} else {{ {else_expr} }}"
        return left

    def _translate_or(self) -> str:
        left = self._translate_and()
        while self._at(TokKind.OPERATOR, "||"):
            self._advance()
            right = self._translate_and()
            left = f"{left} || {right}"
        return left

    def _translate_and(self) -> str:
        left = self._translate_equality()
        while self._at(TokKind.OPERATOR, "&&"):
            self._advance()
            right = self._translate_equality()
            left = f"{left} && {right}"
        return left

    def _translate_equality(self) -> str:
        left = self._translate_comparison()
        while self._at(TokKind.OPERATOR) and self._cur().value in ("===", "!==", "==", "!="):
            op = self._advance().value
            right = self._translate_comparison()
            # === and !== become == and !=
            if op == "===":
                op = "=="
            elif op == "!==":
                op = "!="
            left = f"({left} {op} {right})"
        return left

    def _translate_comparison(self) -> str:
        left = self._translate_concat()
        while self._at(TokKind.OPERATOR) and self._cur().value in ("<", ">", "<=", ">=", "<=>"):
            op = self._advance().value
            right = self._translate_concat()
            left = f"({left} {op} {right})"
        return left

    def _translate_concat(self) -> str:
        """PHP string concatenation: . becomes +."""
        left = self._translate_addition()
        while self._at(TokKind.OPERATOR, "."):
            self._advance()
            right = self._translate_addition()
            left = f"({left} + {right})"
        return left

    def _translate_addition(self) -> str:
        left = self._translate_multiplication()
        while self._at(TokKind.OPERATOR) and self._cur().value in ("+", "-"):
            op = self._advance().value
            right = self._translate_multiplication()
            left = f"({left} {op} {right})"
        return left

    def _translate_multiplication(self) -> str:
        left = self._translate_unary()
        while self._at(TokKind.OPERATOR) and self._cur().value in ("*", "/", "%", "**"):
            op = self._advance().value
            right = self._translate_unary()
            left = f"({left} {op} {right})"
        return left

    def _translate_unary(self) -> str:
        # Unary minus, plus, not
        if self._at(TokKind.OPERATOR, "-"):
            self._advance()
            operand = self._translate_unary()
            return f"-{operand}"
        if self._at(TokKind.OPERATOR, "+"):
            self._advance()
            return self._translate_unary()
        if self._at(TokKind.OPERATOR, "!"):
            self._advance()
            operand = self._translate_unary()
            return f"!{operand}"
        # PHP cast: (int)$x, (string)$x, etc.
        if self._at(TokKind.PUNC, "("):
            next_tok = self._peek()
            if next_tok.kind == TokKind.IDENT and next_tok.value.lower() in _PHP_TYPE_MAP:
                after = self._peek(2)
                if after.kind == TokKind.PUNC and after.value == ")":
                    self._advance()  # (
                    cast_type = self._advance().value.lower()  # type
                    self._advance()  # )
                    operand = self._translate_unary()
                    # Map cast to function call
                    mn_type = _PHP_TYPE_MAP.get(cast_type, cast_type)
                    if mn_type == "Int":
                        return f"int({operand})"
                    if mn_type == "Float":
                        return f"float({operand})"
                    if mn_type == "String":
                        return f"str({operand})"
                    if mn_type == "Bool":
                        return f"bool({operand})"
                    return operand
            # Check for keyword casts like (int), (string)
            if next_tok.kind == TokKind.KEYWORD and next_tok.value in _PHP_TYPE_MAP:
                after = self._peek(2)
                if after.kind == TokKind.PUNC and after.value == ")":
                    self._advance()  # (
                    cast_type = self._advance().value  # type keyword
                    self._advance()  # )
                    operand = self._translate_unary()
                    mn_type = _PHP_TYPE_MAP.get(cast_type, cast_type)
                    if mn_type == "Int":
                        return f"int({operand})"
                    if mn_type == "Float":
                        return f"float({operand})"
                    if mn_type == "String":
                        return f"str({operand})"
                    if mn_type == "Bool":
                        return f"bool({operand})"
                    return operand
        return self._translate_postfix()

    def _translate_postfix(self) -> str:
        """Parse postfix: calls, member access, subscript, ++, --."""
        expr = self._translate_primary()
        while True:
            if self._at(TokKind.ARROW):
                self._advance()
                member = self._expect(TokKind.IDENT).value
                if self._at(TokKind.PUNC, "("):
                    # Method call
                    self._advance()
                    args = self._parse_arg_list()
                    self._expect(TokKind.PUNC, ")")
                    expr = f"{expr}.{member}({', '.join(args)})"
                else:
                    expr = f"{expr}.{member}"
            elif self._at(TokKind.DOUBLE_COLON):
                self._advance()
                member = self._expect(TokKind.IDENT).value
                if self._at(TokKind.PUNC, "("):
                    self._advance()
                    args = self._parse_arg_list()
                    self._expect(TokKind.PUNC, ")")
                    expr = f"{expr}.{member}({', '.join(args)})"
                else:
                    expr = f"{expr}.{member}"
            elif self._at(TokKind.PUNC, "("):
                # Function call on expression
                self._advance()
                args = self._parse_arg_list()
                self._expect(TokKind.PUNC, ")")
                expr = f"{expr}({', '.join(args)})"
            elif self._at(TokKind.PUNC, "["):
                self._advance()
                idx = self._translate_expr()
                self._expect(TokKind.PUNC, "]")
                expr = f"{expr}[{idx}]"
            elif self._at(TokKind.OPERATOR, "++"):
                self._advance()
                expr = f"{expr} = {expr} + 1"
            elif self._at(TokKind.OPERATOR, "--"):
                self._advance()
                expr = f"{expr} = {expr} - 1"
            else:
                break
        return expr

    def _translate_primary(self) -> str:
        """Parse a primary expression (literal, variable, identifier, parenthesized)."""
        tok = self._cur()

        # Numbers
        if tok.kind == TokKind.NUMBER:
            self._advance()
            return tok.value

        # Strings
        if tok.kind == TokKind.STRING:
            self._advance()
            return self._translate_string(tok.value)

        # Variables ($name)
        if tok.kind == TokKind.VARIABLE:
            self._advance()
            name = tok.value[1:]  # Strip $
            if name == "this":
                name = "self"
            return name

        # Parenthesized expression
        if tok.kind == TokKind.PUNC and tok.value == "(":
            self._advance()
            expr = self._translate_expr()
            self._expect(TokKind.PUNC, ")")
            return f"({expr})"

        # Array literal: [expr, ...]
        if tok.kind == TokKind.PUNC and tok.value == "[":
            return self._translate_array_literal()

        # Keywords
        if tok.kind == TokKind.KEYWORD:
            kw = tok.value
            if kw == "true":
                self._advance()
                return "true"
            if kw == "false":
                self._advance()
                return "false"
            if kw == "null":
                self._advance()
                return "None"
            if kw == "new":
                return self._translate_new()
            if kw == "fn":
                return self._translate_arrow_fn()
            if kw == "array":
                self._advance()
                if self._match(TokKind.PUNC, "("):
                    return self._translate_array_construct()
                return "[]"
            if kw == "echo" or kw == "print":
                # Shouldn't normally hit here as a primary, but handle gracefully
                self._advance()
                arg = self._translate_expr()
                return f"print({arg})"

        # Identifiers (function names, class names, constants)
        if tok.kind == TokKind.IDENT:
            self._advance()
            name = tok.value
            # Check for function call
            if self._at(TokKind.PUNC, "("):
                self._advance()
                args = self._parse_arg_list()
                self._expect(TokKind.PUNC, ")")
                return self._translate_func_call(name, args)
            return name

        # If we can't parse, return a placeholder
        if tok.kind != TokKind.EOF:
            self._advance()
            return f"/* {tok.value} */"
        return ""

    def _parse_arg_list(self) -> list[str]:
        """Parse a comma-separated argument list (does not consume parens)."""
        args: list[str] = []
        if self._at(TokKind.PUNC, ")"):
            return args
        args.append(self._translate_expr())
        while self._match(TokKind.PUNC, ","):
            if self._at(TokKind.PUNC, ")"):
                break
            args.append(self._translate_expr())
        return args

    def _translate_string(self, raw: str) -> str:
        """Translate a PHP string literal, handling interpolation in double-quoted strings."""
        if raw.startswith("'"):
            # Single-quoted: no interpolation, just convert to double quotes
            inner = raw[1:-1]
            inner = inner.replace("\\'", "'")
            inner = inner.replace('"', '\\"')
            return f'"{inner}"'

        # Double-quoted: check for $variable interpolation
        inner = raw[1:-1]
        if "$" not in inner:
            return raw  # No interpolation needed

        # Split on $varname occurrences
        parts: list[str] = []
        pattern = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)")
        last_end = 0
        for m in pattern.finditer(inner):
            before = inner[last_end : m.start()]
            if before:
                escaped = before.replace("\\", "\\\\").replace('"', '\\"')
                parts.append(f'"{escaped}"')
            var_name = m.group(1)
            parts.append(f"str({var_name})")
            last_end = m.end()
        after = inner[last_end:]
        if after:
            escaped = after.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'"{escaped}"')

        if not parts:
            return '""'
        if len(parts) == 1:
            return parts[0]
        return " + ".join(parts)

    def _translate_array_literal(self) -> str:
        """Translate [...] array literal."""
        self._expect(TokKind.PUNC, "[")
        if self._at(TokKind.PUNC, "]"):
            self._advance()
            return "[]"

        # Check if it's an associative array (has =>)
        first = self._translate_expr()
        if self._at(TokKind.FAT_ARROW):
            # Associative array
            self._advance()
            val = self._translate_expr()
            pairs = [f"{first}: {val}"]
            while self._match(TokKind.PUNC, ","):
                if self._at(TokKind.PUNC, "]"):
                    break
                k = self._translate_expr()
                self._expect(TokKind.FAT_ARROW)
                v = self._translate_expr()
                pairs.append(f"{k}: {v}")
            self._expect(TokKind.PUNC, "]")
            return "{" + ", ".join(pairs) + "}"

        # Numeric array
        elts = [first]
        while self._match(TokKind.PUNC, ","):
            if self._at(TokKind.PUNC, "]"):
                break
            elts.append(self._translate_expr())
        self._expect(TokKind.PUNC, "]")
        return "[" + ", ".join(elts) + "]"

    def _translate_array_construct(self) -> str:
        """Translate array(...) constructor."""
        if self._at(TokKind.PUNC, ")"):
            self._advance()
            return "[]"

        first = self._translate_expr()
        if self._at(TokKind.FAT_ARROW):
            self._advance()
            val = self._translate_expr()
            pairs = [f"{first}: {val}"]
            while self._match(TokKind.PUNC, ","):
                if self._at(TokKind.PUNC, ")"):
                    break
                k = self._translate_expr()
                self._expect(TokKind.FAT_ARROW)
                v = self._translate_expr()
                pairs.append(f"{k}: {v}")
            self._expect(TokKind.PUNC, ")")
            return "{" + ", ".join(pairs) + "}"

        elts = [first]
        while self._match(TokKind.PUNC, ","):
            if self._at(TokKind.PUNC, ")"):
                break
            elts.append(self._translate_expr())
        self._expect(TokKind.PUNC, ")")
        return "[" + ", ".join(elts) + "]"

    def _translate_new(self) -> str:
        """Translate 'new ClassName(args)' to 'ClassName(args)'."""
        self._expect(TokKind.KEYWORD, "new")
        name = self._expect(TokKind.IDENT).value
        if self._match(TokKind.PUNC, "("):
            args = self._parse_arg_list()
            self._expect(TokKind.PUNC, ")")
            return f"{name}({', '.join(args)})"
        return f"{name}()"

    def _translate_arrow_fn(self) -> str:
        """Translate 'fn($x) => expr' to '(x) => expr'."""
        self._expect(TokKind.KEYWORD, "fn")
        self._expect(TokKind.PUNC, "(")
        params: list[str] = []
        while not self._at(TokKind.PUNC, ")"):
            if self._at(TokKind.VARIABLE):
                params.append(self._advance().value[1:])  # Strip $
            elif self._at(TokKind.IDENT):
                # Type hint before parameter
                self._advance()  # skip type
                if self._at(TokKind.VARIABLE):
                    params.append(self._advance().value[1:])
            if not self._match(TokKind.PUNC, ","):
                break
        self._expect(TokKind.PUNC, ")")
        self._expect(TokKind.FAT_ARROW)
        body = self._translate_expr()
        return f"({', '.join(params)}) => {body}"

    def _translate_func_call(self, name: str, args: list[str]) -> str:
        """Translate a PHP function call to Mapanare."""
        # Pattern-based mappings for PHP builtins without direct equivalents
        if name == "isset" and args:
            return f"{args[0]} != None"
        if name == "empty" and args:
            return f"len({args[0]}) == 0"
        if name == "is_array" and args:
            return f'typeof({args[0]}) == "List"'
        if name == "is_string" and args:
            return f'typeof({args[0]}) == "String"'
        if name == "is_int" and args:
            return f'typeof({args[0]}) == "Int"'

        mapped = _PHP_FUNC_MAP.get(name)

        if mapped is None:
            return f"{name}({', '.join(args)})"

        # Simple 1-to-1 function mapping
        if not mapped.startswith("."):
            # Global function
            if mapped == "print":
                return f"print({', '.join(args)})"
            return f"{mapped}({', '.join(args)})"

        # Method-style mapping: first arg becomes receiver
        if not args:
            return f"{name}({', '.join(args)})"

        method = mapped[1:]  # strip leading .
        receiver = args[0]
        rest = args[1:]

        # Special cases with reversed arguments
        if name == "explode":
            # explode(delimiter, string) -> string.split(delimiter)
            if len(args) >= 2:
                return f"{args[1]}.split({args[0]})"
        if name == "implode":
            # implode(glue, pieces) -> pieces.join(glue)  — but no join method, use concat
            if len(args) >= 2:
                return f"{args[1]}.join({args[0]})"
        if name == "in_array":
            # in_array(needle, haystack) -> haystack.contains(needle)
            if len(args) >= 2:
                return f"{args[1]}.contains({args[0]})"
        if name == "str_replace":
            # str_replace(search, replace, subject) -> subject.replace(search, replace)
            if len(args) >= 3:
                return f"{args[2]}.replace({args[0]}, {args[1]})"
        if name == "array_push":
            # array_push($arr, val) -> arr.push(val)
            if len(args) >= 2:
                return f"{receiver}.push({', '.join(rest)})"

        return f"{receiver}.{method}({', '.join(rest)})"

    # -- Statement parsing --

    def _translate_stmt(self) -> None:
        """Parse and translate a single top-level or block-level statement."""
        tok = self._cur()

        if tok.kind == TokKind.EOF:
            return

        if tok.kind == TokKind.PUNC and tok.value == ";":
            self._advance()
            return

        if tok.kind == TokKind.KEYWORD:
            kw = tok.value
            if kw == "function":
                self._translate_function()
                return
            if kw == "class":
                self._translate_class()
                return
            if kw == "if":
                self._translate_if()
                return
            if kw == "while":
                self._translate_while()
                return
            if kw == "do":
                self._translate_do_while()
                return
            if kw == "for":
                self._translate_for()
                return
            if kw == "foreach":
                self._translate_foreach()
                return
            if kw == "switch":
                self._translate_switch()
                return
            if kw == "return":
                self._translate_return()
                return
            if kw == "echo":
                self._translate_echo()
                return
            if kw == "break":
                self._advance()
                self._match(TokKind.PUNC, ";")
                self._emit("break")
                return
            if kw == "continue":
                self._advance()
                self._match(TokKind.PUNC, ";")
                self._emit("continue")
                return
            if kw == "try":
                self._translate_try()
                return
            if kw == "throw":
                self._translate_throw()
                return
            if kw in ("include", "require", "include_once", "require_once"):
                self._translate_include(kw)
                return
            if kw in ("namespace", "use"):
                self._translate_namespace_or_use(kw)
                return
            if kw == "interface" or kw == "trait" or kw == "abstract":
                self._translate_class()
                return
            if kw == "const":
                self._translate_const()
                return

        # Variable assignment or expression statement
        if tok.kind == TokKind.VARIABLE:
            self._translate_var_stmt()
            return

        # Expression statement (function call, etc.)
        expr = self._translate_expr()
        self._match(TokKind.PUNC, ";")
        if expr:
            self._emit(expr)

    def _translate_function(self) -> None:
        """Translate a PHP function definition."""
        self._expect(TokKind.KEYWORD, "function")
        name = self._expect(TokKind.IDENT).value
        self._expect(TokKind.PUNC, "(")
        params = self._parse_param_list()
        self._expect(TokKind.PUNC, ")")

        # Return type
        ret_type = ""
        if self._match(TokKind.PUNC, ":"):
            ret_type = self._parse_type_hint()
            ret_type = self._translate_type(ret_type)

        ret_annotation = ""
        if ret_type and ret_type not in ("any", "Void"):
            ret_annotation = f" -> {ret_type}"

        param_str = ", ".join(params)
        self._emit(f"fn {name}({param_str}){ret_annotation} {{")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()
        self._emit("}")
        self._emit_raw("")

    def _translate_method(self) -> None:
        """Translate a class method definition."""
        # Skip visibility/static/abstract modifiers
        while self._at(TokKind.KEYWORD) and self._cur().value in (
            "public",
            "private",
            "protected",
            "static",
            "abstract",
            "final",
        ):
            self._advance()

        self._expect(TokKind.KEYWORD, "function")
        name = self._expect(TokKind.IDENT).value

        if name == "__construct":
            # Constructor: skip it, fields are extracted separately
            self._expect(TokKind.PUNC, "(")
            self._skip_balanced("(", ")")
            if self._at(TokKind.PUNC, "{"):
                self._advance()
                self._skip_balanced("{", "}")
            return

        self._expect(TokKind.PUNC, "(")
        params = self._parse_param_list()
        self._expect(TokKind.PUNC, ")")

        ret_type = ""
        if self._match(TokKind.PUNC, ":"):
            ret_type = self._parse_type_hint()
            ret_type = self._translate_type(ret_type)

        ret_annotation = ""
        if ret_type and ret_type not in ("any", "Void"):
            ret_annotation = f" -> {ret_type}"

        all_params = ["self"] + params
        param_str = ", ".join(all_params)
        self._emit(f"fn {name}({param_str}){ret_annotation} {{")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()
        self._emit("}")
        self._emit_raw("")

    def _parse_param_list(self) -> list[str]:
        """Parse function parameter list (inside parens)."""
        params: list[str] = []
        while not self._at(TokKind.PUNC, ")") and not self._at_eof():
            # Optional type hint
            type_hint = ""
            if self._at(TokKind.IDENT) or (
                self._at(TokKind.OPERATOR, "?") and self._peek().kind == TokKind.IDENT
            ):
                type_hint = self._parse_type_hint()

            if self._at(TokKind.VARIABLE):
                var_name = self._advance().value[1:]  # Strip $

                # Default value
                if self._match(TokKind.OPERATOR, "="):
                    self._translate_expr()  # Skip default value

                if type_hint:
                    mn_type = self._translate_type(type_hint)
                    params.append(f"{var_name}: {mn_type}")
                else:
                    params.append(var_name)
            elif self._at(TokKind.KEYWORD) and self._cur().value in _PHP_TYPE_MAP:
                # Keyword type like 'int', 'string', 'bool', etc.
                type_hint = self._advance().value
                if self._at(TokKind.VARIABLE):
                    var_name = self._advance().value[1:]
                    if self._match(TokKind.OPERATOR, "="):
                        self._translate_expr()
                    mn_type = self._translate_type(type_hint)
                    params.append(f"{var_name}: {mn_type}")
            elif self._at(TokKind.ELLIPSIS):
                self._advance()
                if self._at(TokKind.VARIABLE):
                    var_name = self._advance().value[1:]
                    params.append(f"{var_name}: List<any>")
            else:
                # Skip unknown tokens in param list
                if not self._at(TokKind.PUNC, ")"):
                    self._advance()

            if not self._match(TokKind.PUNC, ","):
                break

        return params

    def _parse_type_hint(self) -> str:
        """Parse a PHP type hint (simple: int, string, ?int, ClassName)."""
        nullable = ""
        if self._at(TokKind.OPERATOR, "?"):
            self._advance()
            nullable = "?"

        if self._at(TokKind.IDENT):
            return nullable + self._advance().value
        if self._at(TokKind.KEYWORD) and self._cur().value in _PHP_TYPE_MAP:
            return nullable + self._advance().value
        return "any"

    def _translate_block_body(self) -> None:
        """Translate statements until the matching closing brace."""
        depth = 1
        while depth > 0 and not self._at_eof():
            if self._at(TokKind.PUNC, "}"):
                depth -= 1
                if depth == 0:
                    self._advance()
                    return
                self._advance()
                continue
            if self._at(TokKind.PUNC, "{"):
                depth += 1
                self._advance()
                continue
            # Put the brace tracking back and let statement parser handle it
            # But we need to be careful: reset depth tracking
            break

        # Normal statement-by-statement parsing
        while not self._at(TokKind.PUNC, "}") and not self._at_eof():
            self._translate_stmt()
        self._match(TokKind.PUNC, "}")

    def _skip_balanced(self, open_ch: str, close_ch: str) -> None:
        """Skip tokens until balanced braces/parens."""
        depth = 1
        while depth > 0 and not self._at_eof():
            if self._at(TokKind.PUNC, close_ch):
                depth -= 1
                self._advance()
            elif self._at(TokKind.PUNC, open_ch):
                depth += 1
                self._advance()
            else:
                self._advance()

    def _translate_class(self) -> None:
        """Translate a PHP class to a Mapanare struct + impl block."""
        # Skip abstract/final
        while self._at(TokKind.KEYWORD) and self._cur().value in ("abstract", "final"):
            self._advance()

        kind = self._expect(TokKind.KEYWORD).value  # class, interface, trait
        name = self._expect(TokKind.IDENT).value
        self._current_class = name

        # Skip extends/implements
        while self._at(TokKind.KEYWORD) and self._cur().value in ("extends", "implements"):
            self._advance()
            self._expect(TokKind.IDENT)
            while self._match(TokKind.PUNC, ","):
                self._expect(TokKind.IDENT)

        self._expect(TokKind.PUNC, "{")

        # Collect fields and methods by scanning the class body
        fields: list[tuple[str, str]] = []
        methods_start: list[int] = []

        # Save position to scan twice
        scan_start = self._pos
        depth = 1

        # First pass: extract fields
        while depth > 0 and not self._at_eof():
            if self._at(TokKind.PUNC, "}"):
                depth -= 1
                if depth == 0:
                    break
                self._advance()
                continue
            if self._at(TokKind.PUNC, "{"):
                depth += 1
                self._advance()
                continue

            # Check for property declarations
            if self._at(TokKind.KEYWORD) and self._cur().value in (
                "public",
                "private",
                "protected",
            ):
                save_pos = self._pos
                self._advance()  # visibility

                # Skip static
                if self._at(TokKind.KEYWORD, "static"):
                    self._advance()

                # Check if this is a method (function keyword) or property
                if self._at(TokKind.KEYWORD, "function"):
                    # Method — record position for second pass
                    methods_start.append(save_pos)
                    # Skip to end of method
                    self._advance()  # function
                    if self._at(TokKind.IDENT):
                        self._advance()  # name
                    if self._at(TokKind.PUNC, "("):
                        self._advance()
                        self._skip_balanced("(", ")")
                    # Skip return type
                    if self._match(TokKind.PUNC, ":"):
                        self._parse_type_hint()
                    if self._at(TokKind.PUNC, "{"):
                        self._advance()
                        self._skip_balanced("{", "}")
                    continue

                # Property: [type] $name [= value];
                type_hint = ""
                if self._at(TokKind.IDENT) or (
                    self._at(TokKind.KEYWORD) and self._cur().value in _PHP_TYPE_MAP
                ):
                    type_hint = self._parse_type_hint()
                elif self._at(TokKind.OPERATOR, "?"):
                    type_hint = self._parse_type_hint()

                if self._at(TokKind.VARIABLE):
                    var_name = self._advance().value[1:]
                    mn_type = self._translate_type(type_hint) if type_hint else "any"
                    fields.append((var_name, mn_type))
                    # Skip = default
                    if self._match(TokKind.OPERATOR, "="):
                        while not self._at(TokKind.PUNC, ";") and not self._at_eof():
                            self._advance()
                    self._match(TokKind.PUNC, ";")
                    continue
                # Not a property, restore
                self._pos = save_pos
            elif self._at(TokKind.KEYWORD, "const"):
                # Class constant — skip
                while not self._at(TokKind.PUNC, ";") and not self._at_eof():
                    self._advance()
                self._match(TokKind.PUNC, ";")
                continue

            self._advance()

        # Emit struct
        if kind == "interface":
            self._emit(f"// interface {name}")
            self._emit(f"struct {name} {{")
        else:
            self._emit(f"struct {name} {{")
        self._indent.push()
        for i, (fname, ftype) in enumerate(fields):
            comma = "," if i < len(fields) - 1 else ""
            self._emit(f"{fname}: {ftype}{comma}")
        self._indent.pop()
        self._emit("}")
        self._emit_raw("")

        # Second pass: emit methods
        if methods_start:
            self._emit(f"impl {name} {{")
            self._indent.push()
            for mpos in methods_start:
                self._pos = mpos
                self._translate_method()
            self._indent.pop()
            self._emit("}")
            self._emit_raw("")

        # Skip to end of class body
        self._pos = scan_start
        depth = 1
        while depth > 0 and not self._at_eof():
            if self._at(TokKind.PUNC, "}"):
                depth -= 1
                self._advance()
            elif self._at(TokKind.PUNC, "{"):
                depth += 1
                self._advance()
            else:
                self._advance()

        self._current_class = None

    def _translate_if(self) -> None:
        """Translate if/elseif/else."""
        self._expect(TokKind.KEYWORD, "if")
        self._expect(TokKind.PUNC, "(")
        cond = self._translate_expr()
        self._expect(TokKind.PUNC, ")")
        self._emit(f"if {cond} {{")

        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()

        while self._at(TokKind.KEYWORD, "elseif"):
            self._advance()
            self._expect(TokKind.PUNC, "(")
            cond = self._translate_expr()
            self._expect(TokKind.PUNC, ")")
            self._emit(f"}} else if {cond} {{")
            self._expect(TokKind.PUNC, "{")
            self._indent.push()
            self._push_scope()
            self._translate_block_body()
            self._pop_scope()
            self._indent.pop()

        if self._match(TokKind.KEYWORD, "else"):
            self._emit("} else {")
            self._expect(TokKind.PUNC, "{")
            self._indent.push()
            self._push_scope()
            self._translate_block_body()
            self._pop_scope()
            self._indent.pop()

        self._emit("}")

    def _translate_while(self) -> None:
        """Translate while loop."""
        self._expect(TokKind.KEYWORD, "while")
        self._expect(TokKind.PUNC, "(")
        cond = self._translate_expr()
        self._expect(TokKind.PUNC, ")")
        self._emit(f"while {cond} {{")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()
        self._emit("}")

    def _translate_do_while(self) -> None:
        """Translate do-while loop (approximated as loop with break)."""
        self._expect(TokKind.KEYWORD, "do")
        self._emit("// do-while loop")
        self._emit("while true {")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()

        # while condition
        self._expect(TokKind.KEYWORD, "while")
        self._expect(TokKind.PUNC, "(")
        cond = self._translate_expr()
        self._expect(TokKind.PUNC, ")")
        self._match(TokKind.PUNC, ";")
        self._emit(f"if !({cond}) {{ break }}")
        self._indent.pop()
        self._emit("}")

    def _translate_for(self) -> None:
        """Translate C-style for loop.

        for ($i = 0; $i < 10; $i++) → for i in 0..10
        """
        self._expect(TokKind.KEYWORD, "for")
        self._expect(TokKind.PUNC, "(")

        # Try to detect simple range pattern: $i = start; $i < end; $i++
        save_pos = self._pos
        can_simplify = False
        var_name = ""
        start_val = ""
        end_val = ""

        try:
            # Init: $i = start
            if self._at(TokKind.VARIABLE):
                var_name = self._cur().value[1:]
                self._advance()
                if self._match(TokKind.OPERATOR, "="):
                    start_val = self._translate_expr()
                    if self._match(TokKind.PUNC, ";"):
                        # Condition: $i < end
                        if self._at(TokKind.VARIABLE) and self._cur().value[1:] == var_name:
                            self._advance()
                            if self._at(TokKind.OPERATOR, "<"):
                                self._advance()
                                end_val = self._translate_expr()
                                if self._match(TokKind.PUNC, ";"):
                                    # Increment: $i++ or $i += 1 or ++$i
                                    if (
                                        self._at(TokKind.VARIABLE)
                                        and self._cur().value[1:] == var_name
                                    ):
                                        self._advance()
                                        if self._match(TokKind.OPERATOR, "++"):
                                            can_simplify = True
                                        elif self._match(TokKind.OPERATOR, "+="):
                                            inc = self._translate_expr()
                                            if inc == "1":
                                                can_simplify = True
        except TranslateError:
            pass

        if can_simplify:
            self._expect(TokKind.PUNC, ")")
            self._emit(f"for {var_name} in {start_val}..{end_val} {{")
            self._declare(var_name)
            self._expect(TokKind.PUNC, "{")
            self._indent.push()
            self._push_scope()
            self._translate_block_body()
            self._pop_scope()
            self._indent.pop()
            self._emit("}")
            return

        # Fall back to while loop
        self._pos = save_pos
        # Parse init
        init_parts: list[tuple[str, str]] = []
        while not self._at(TokKind.PUNC, ";") and not self._at_eof():
            if self._at(TokKind.VARIABLE):
                vname = self._cur().value[1:]
                self._advance()
                if self._match(TokKind.OPERATOR, "="):
                    val = self._translate_expr()
                    init_parts.append((vname, val))
                    self._declare(vname)
            else:
                self._advance()
        self._match(TokKind.PUNC, ";")

        # Parse condition
        cond = "true"
        if not self._at(TokKind.PUNC, ";"):
            cond = self._translate_expr()
        self._match(TokKind.PUNC, ";")

        # Parse increment (skip, emit in loop body)
        inc_tokens_start = self._pos
        while not self._at(TokKind.PUNC, ")") and not self._at_eof():
            self._advance()
        inc_tokens_end = self._pos
        self._expect(TokKind.PUNC, ")")

        # Emit init
        for vn, vl in init_parts:
            self._emit(f"let mut {vn} = {vl}")

        self._emit(f"while {cond} {{")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()

        # Emit increment at end of loop body
        save = self._pos
        self._pos = inc_tokens_start
        while self._pos < inc_tokens_end:
            if self._at(TokKind.VARIABLE):
                vname = self._cur().value[1:]
                self._advance()
                if self._match(TokKind.OPERATOR, "++"):
                    self._emit(f"{vname} = {vname} + 1")
                elif self._match(TokKind.OPERATOR, "--"):
                    self._emit(f"{vname} = {vname} - 1")
                elif self._match(TokKind.OPERATOR, "+="):
                    val = self._translate_expr()
                    self._emit(f"{vname} = {vname} + {val}")
                elif self._match(TokKind.OPERATOR, "-="):
                    val = self._translate_expr()
                    self._emit(f"{vname} = {vname} - {val}")
                elif self._match(TokKind.OPERATOR, "="):
                    val = self._translate_expr()
                    self._emit(f"{vname} = {val}")
            else:
                self._advance()
        self._pos = save

        self._pop_scope()
        self._indent.pop()
        self._emit("}")

    def _translate_foreach(self) -> None:
        """Translate foreach ($items as $item) and foreach ($map as $k => $v)."""
        self._expect(TokKind.KEYWORD, "foreach")
        self._expect(TokKind.PUNC, "(")
        iterable = self._translate_expr()
        self._expect(TokKind.KEYWORD, "as")

        var1 = self._expect(TokKind.VARIABLE).value[1:]

        if self._at(TokKind.FAT_ARROW):
            # foreach ($map as $k => $v) — simplified to for k in map
            self._advance()
            _var2 = self._expect(TokKind.VARIABLE).value[1:]
            self._expect(TokKind.PUNC, ")")
            self._emit(f"for {var1} in {iterable} {{")
            self._declare(var1)
        else:
            self._expect(TokKind.PUNC, ")")
            self._emit(f"for {var1} in {iterable} {{")
            self._declare(var1)

        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()
        self._emit("}")

    def _translate_switch(self) -> None:
        """Translate switch to if/else if chain."""
        self._expect(TokKind.KEYWORD, "switch")
        self._expect(TokKind.PUNC, "(")
        expr = self._translate_expr()
        self._expect(TokKind.PUNC, ")")
        self._expect(TokKind.PUNC, "{")

        self._emit(f"// switch ({expr})")
        first = True
        while not self._at(TokKind.PUNC, "}") and not self._at_eof():
            if self._match(TokKind.KEYWORD, "case"):
                val = self._translate_expr()
                self._expect(TokKind.PUNC, ":")
                if first:
                    self._emit(f"if {expr} == {val} {{")
                    first = False
                else:
                    self._emit(f"}} else if {expr} == {val} {{")
                self._indent.push()
                self._push_scope()
                while (
                    not self._at(TokKind.KEYWORD, "case")
                    and not self._at(TokKind.KEYWORD, "default")
                    and not self._at(TokKind.PUNC, "}")
                    and not self._at_eof()
                ):
                    if self._at(TokKind.KEYWORD, "break"):
                        self._advance()
                        self._match(TokKind.PUNC, ";")
                        continue
                    self._translate_stmt()
                self._pop_scope()
                self._indent.pop()
            elif self._match(TokKind.KEYWORD, "default"):
                self._expect(TokKind.PUNC, ":")
                if first:
                    self._emit("// default")
                    first = False
                else:
                    self._emit("} else {")
                self._indent.push()
                self._push_scope()
                while not self._at(TokKind.PUNC, "}") and not self._at_eof():
                    if self._at(TokKind.KEYWORD, "break"):
                        self._advance()
                        self._match(TokKind.PUNC, ";")
                        continue
                    self._translate_stmt()
                self._pop_scope()
                self._indent.pop()
            else:
                self._advance()

        if not first:
            self._emit("}")
        self._match(TokKind.PUNC, "}")

    def _translate_return(self) -> None:
        """Translate return statement."""
        self._expect(TokKind.KEYWORD, "return")
        if self._at(TokKind.PUNC, ";"):
            self._advance()
            self._emit("return")
        else:
            val = self._translate_expr()
            self._match(TokKind.PUNC, ";")
            self._emit(f"return {val}")

    def _translate_echo(self) -> None:
        """Translate echo statement."""
        self._expect(TokKind.KEYWORD, "echo")
        args: list[str] = []
        args.append(self._translate_expr())
        while self._match(TokKind.PUNC, ","):
            args.append(self._translate_expr())
        self._match(TokKind.PUNC, ";")

        for arg in args:
            self._emit(f"print({arg})")

    def _translate_var_stmt(self) -> None:
        """Translate variable assignment or expression statement."""
        var_name = self._cur().value[1:]  # Strip $
        self._advance()

        # Check for assignment operators
        if self._match(TokKind.OPERATOR, "="):
            val = self._translate_expr()
            self._match(TokKind.PUNC, ";")
            if self._is_declared(var_name):
                self._emit(f"{var_name} = {val}")
            else:
                # Infer type from expression tokens (basic heuristic)
                type_ann = self._guess_type(val)
                if type_ann != "any":
                    self._emit(f"let mut {var_name}: {type_ann} = {val}")
                else:
                    self._emit(f"let mut {var_name} = {val}")
                self._declare(var_name)
            return

        if self._at(TokKind.OPERATOR) and self._cur().value in ("+=", "-=", "*=", "/=", ".="):
            op = self._advance().value
            val = self._translate_expr()
            self._match(TokKind.PUNC, ";")
            if op == ".=":
                self._emit(f"{var_name} = {var_name} + {val}")
            else:
                base_op = op[0]
                self._emit(f"{var_name} = {var_name} {base_op} {val}")
            return

        if self._match(TokKind.OPERATOR, "++"):
            self._match(TokKind.PUNC, ";")
            self._emit(f"{var_name} = {var_name} + 1")
            return

        if self._match(TokKind.OPERATOR, "--"):
            self._match(TokKind.PUNC, ";")
            self._emit(f"{var_name} = {var_name} - 1")
            return

        # Back up and parse as expression
        self._pos -= 1
        expr = self._translate_expr()
        self._match(TokKind.PUNC, ";")
        if expr:
            self._emit(expr)

    def _translate_try(self) -> None:
        """Translate try/catch to comments (Mapanare uses Result types)."""
        self._expect(TokKind.KEYWORD, "try")
        self._emit("// try {")
        self._expect(TokKind.PUNC, "{")
        self._indent.push()
        self._push_scope()
        self._translate_block_body()
        self._pop_scope()
        self._indent.pop()

        while self._match(TokKind.KEYWORD, "catch"):
            self._expect(TokKind.PUNC, "(")
            exc_type = ""
            if self._at(TokKind.IDENT):
                exc_type = self._advance().value
            exc_name = "_"
            if self._at(TokKind.VARIABLE):
                exc_name = self._advance().value[1:]
            self._expect(TokKind.PUNC, ")")
            self._emit(f"// }} catch ({exc_type} {exc_name}) {{")
            self._expect(TokKind.PUNC, "{")
            self._indent.push()
            self._push_scope()
            self._translate_block_body()
            self._pop_scope()
            self._indent.pop()

        if self._match(TokKind.KEYWORD, "finally"):
            self._emit("// } finally {")
            self._expect(TokKind.PUNC, "{")
            self._indent.push()
            self._push_scope()
            self._translate_block_body()
            self._pop_scope()
            self._indent.pop()

        self._emit("// }")

    def _translate_throw(self) -> None:
        """Translate throw to Err()."""
        self._expect(TokKind.KEYWORD, "throw")
        exc = self._translate_expr()
        self._match(TokKind.PUNC, ";")
        self._emit(f"return Err({exc})  // throw {exc}")

    def _translate_include(self, keyword: str) -> None:
        """Translate include/require to a comment."""
        self._advance()  # keyword
        if self._at(TokKind.STRING):
            path = self._advance().value
            self._match(TokKind.PUNC, ";")
            self._emit(f"// {keyword} {path} (not supported)")
        elif self._at(TokKind.PUNC, "("):
            self._advance()
            path = self._translate_expr()
            self._expect(TokKind.PUNC, ")")
            self._match(TokKind.PUNC, ";")
            self._emit(f"// {keyword} {path} (not supported)")
        else:
            path = self._translate_expr()
            self._match(TokKind.PUNC, ";")
            self._emit(f"// {keyword} {path} (not supported)")

    def _translate_namespace_or_use(self, keyword: str) -> None:
        """Translate namespace/use to a comment."""
        self._advance()
        parts: list[str] = []
        while (
            not self._at(TokKind.PUNC, ";")
            and not self._at(TokKind.PUNC, "{")
            and not self._at_eof()
        ):
            parts.append(self._advance().value)
        self._match(TokKind.PUNC, ";")
        if self._at(TokKind.PUNC, "{"):
            # namespace { ... } block
            self._advance()
            self._skip_balanced("{", "}")
        self._emit(f"// {keyword} {''.join(parts)}")

    def _translate_const(self) -> None:
        """Translate const NAME = value;"""
        self._expect(TokKind.KEYWORD, "const")
        name = self._expect(TokKind.IDENT).value
        self._expect(TokKind.OPERATOR, "=")
        val = self._translate_expr()
        self._match(TokKind.PUNC, ";")
        type_ann = self._guess_type(val)
        if type_ann != "any":
            self._emit(f"let {name}: {type_ann} = {val}")
        else:
            self._emit(f"let {name} = {val}")

    def _guess_type(self, val_str: str) -> str:
        """Heuristic type inference from a translated value string."""
        val = val_str.strip()
        if val.startswith('"') or val.startswith("str("):
            return "String"
        if val == "true" or val == "false":
            return "Bool"
        if val == "None":
            return "Option<any>"
        if val.startswith("["):
            return "List<any>"
        if val.startswith("{"):
            return "Map<any, any>"
        # Check for numeric
        try:
            if "." in val:
                float(val)
                return "Float"
            int(val)
            return "Int"
        except ValueError:
            pass
        return "any"

    # -- Top-level translation --

    def translate(self, source: str) -> str:
        """Translate PHP source text to Mapanare source text."""
        self._tokens = _tokenize(source, self.filename)
        self._pos = 0
        self._lines = []
        self._declared_vars = [set()]

        self._emit_raw(f"// Translated from {self.filename} by mapanare transpile")
        self._emit_raw("")

        while not self._at_eof():
            if self._at(TokKind.PUNC, ";"):
                self._advance()
                continue

            if self._at(TokKind.KEYWORD):
                kw = self._cur().value
                if kw == "function":
                    self._translate_function()
                    continue
                if kw in ("class", "interface", "trait", "abstract"):
                    self._translate_class()
                    continue
                if kw == "namespace" or kw == "use":
                    self._translate_namespace_or_use(kw)
                    continue

            # Global statement
            self._translate_stmt()

        return "\n".join(self._lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def translate_to_mn(source: str, filename: str = "<stdin>") -> str:
    """Translate PHP source code into Mapanare (.mn) source text.

    Parameters
    ----------
    source:
        The PHP source code to translate.
    filename:
        The filename used in error messages and the output header comment.

    Returns
    -------
    str
        Valid Mapanare source code that can be parsed by the Mapanare parser.

    Raises
    ------
    TranslateError
        If a PHP construct cannot be translated.
    """
    translator = PhpTranslator(filename=filename)
    return translator.translate(source)
