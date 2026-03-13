"""Mapanare structured error codes.

All compiler and runtime errors are assigned a stable code in the format MN-XNNNN where:
  - X is the phase letter: P=parse, S=semantic, L=lowering, C=codegen, R=runtime, T=tooling
  - NNNN is a four-digit number

Error codes are stable across versions — once assigned, a code keeps its meaning.
Codes may be deprecated but never reassigned.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorCode:
    """A structured compiler/runtime error code."""

    code: str
    title: str
    phase: str
    explanation: str = ""

    def __str__(self) -> str:
        return f"[{self.code}] {self.title}"


# ---------------------------------------------------------------------------
# Parse errors (MN-P0xxx)
# ---------------------------------------------------------------------------

E_PARSE_UNEXPECTED_TOKEN = ErrorCode(
    code="MN-P0001",
    title="unexpected token",
    phase="parse",
    explanation="The parser encountered a token it did not expect at this position.",
)

E_PARSE_UNCLOSED_BRACE = ErrorCode(
    code="MN-P0002",
    title="unclosed brace",
    phase="parse",
    explanation="A '{' was opened but never closed with a matching '}'.",
)

E_PARSE_UNCLOSED_PAREN = ErrorCode(
    code="MN-P0003",
    title="unclosed parenthesis",
    phase="parse",
    explanation="A '(' was opened but never closed with a matching ')'.",
)

E_PARSE_UNCLOSED_BRACKET = ErrorCode(
    code="MN-P0004",
    title="unclosed bracket",
    phase="parse",
    explanation="A '[' was opened but never closed with a matching ']'.",
)

E_PARSE_INVALID_LITERAL = ErrorCode(
    code="MN-P0005",
    title="invalid literal",
    phase="parse",
    explanation="The literal value could not be parsed (e.g., malformed number or string).",
)

E_PARSE_UNTERMINATED_STRING = ErrorCode(
    code="MN-P0006",
    title="unterminated string literal",
    phase="parse",
    explanation="A string literal was opened with a quote but never closed.",
)

E_PARSE_INVALID_ESCAPE = ErrorCode(
    code="MN-P0007",
    title="invalid escape sequence",
    phase="parse",
    explanation="An unrecognized escape sequence was found in a string literal.",
)

# ---------------------------------------------------------------------------
# Semantic errors (MN-S0xxx)
# ---------------------------------------------------------------------------

E_SEM_UNDEFINED_VAR = ErrorCode(
    code="MN-S0001",
    title="undefined variable",
    phase="semantic",
    explanation="The variable was referenced but has not been declared in scope.",
)

E_SEM_TYPE_MISMATCH = ErrorCode(
    code="MN-S0002",
    title="type mismatch",
    phase="semantic",
    explanation="Expected one type but found another.",
)

E_SEM_UNDEFINED_FUNCTION = ErrorCode(
    code="MN-S0003",
    title="undefined function",
    phase="semantic",
    explanation="The function was called but has not been declared.",
)

E_SEM_ARITY_MISMATCH = ErrorCode(
    code="MN-S0004",
    title="argument count mismatch",
    phase="semantic",
    explanation="The function was called with the wrong number of arguments.",
)

E_SEM_DUPLICATE_DEFINITION = ErrorCode(
    code="MN-S0005",
    title="duplicate definition",
    phase="semantic",
    explanation="A name is defined more than once in the same scope.",
)

E_SEM_IMMUTABLE_ASSIGN = ErrorCode(
    code="MN-S0006",
    title="assignment to immutable variable",
    phase="semantic",
    explanation="Cannot assign to a variable not declared with 'let mut'.",
)

E_SEM_UNDEFINED_TYPE = ErrorCode(
    code="MN-S0007",
    title="undefined type",
    phase="semantic",
    explanation="The type name was used but has not been declared.",
)

E_SEM_UNDEFINED_FIELD = ErrorCode(
    code="MN-S0008",
    title="undefined field",
    phase="semantic",
    explanation="The struct does not have a field with this name.",
)

E_SEM_MISSING_RETURN = ErrorCode(
    code="MN-S0009",
    title="missing return value",
    phase="semantic",
    explanation="A function with a return type does not return a value on all paths.",
)

E_SEM_UNREACHABLE_CODE = ErrorCode(
    code="MN-S0010",
    title="unreachable code",
    phase="semantic",
    explanation="Code appears after a return statement and can never execute.",
)

E_SEM_NON_EXHAUSTIVE_MATCH = ErrorCode(
    code="MN-S0011",
    title="non-exhaustive match",
    phase="semantic",
    explanation="Not all enum variants are covered in the match expression.",
)

E_SEM_INVALID_PIPE = ErrorCode(
    code="MN-S0012",
    title="invalid pipe target",
    phase="semantic",
    explanation="The pipe operator '|>' requires a callable as its right operand.",
)

# ---------------------------------------------------------------------------
# Lowering / MIR errors (MN-L0xxx)
# ---------------------------------------------------------------------------

E_LOWER_UNSUPPORTED_NODE = ErrorCode(
    code="MN-L0001",
    title="unsupported AST node",
    phase="lowering",
    explanation="The MIR lowering pass does not support this AST node type.",
)

E_LOWER_INTERNAL = ErrorCode(
    code="MN-L0002",
    title="internal lowering error",
    phase="lowering",
    explanation="An unexpected error occurred during AST-to-MIR lowering.",
)

# ---------------------------------------------------------------------------
# Codegen errors (MN-C0xxx)
# ---------------------------------------------------------------------------

E_CODEGEN_UNSUPPORTED_TYPE = ErrorCode(
    code="MN-C0001",
    title="unsupported type in codegen",
    phase="codegen",
    explanation="The code generator does not support emitting code for this type.",
)

E_CODEGEN_LLVM_ERROR = ErrorCode(
    code="MN-C0002",
    title="LLVM IR generation error",
    phase="codegen",
    explanation="An error occurred while generating LLVM IR.",
)

E_CODEGEN_LINK_ERROR = ErrorCode(
    code="MN-C0003",
    title="linker error",
    phase="codegen",
    explanation="The linker failed to produce a native binary.",
)

# ---------------------------------------------------------------------------
# Runtime errors (MN-R0xxx)
# ---------------------------------------------------------------------------

E_RUNTIME_AGENT_SEND_FAILED = ErrorCode(
    code="MN-R0001",
    title="agent send failed",
    phase="runtime",
    explanation="Failed to send a message to an agent (channel closed or full).",
)

E_RUNTIME_AGENT_SPAWN_FAILED = ErrorCode(
    code="MN-R0002",
    title="agent spawn failed",
    phase="runtime",
    explanation="Failed to spawn an agent.",
)

E_RUNTIME_UNWRAP_NONE = ErrorCode(
    code="MN-R0003",
    title="unwrap on None",
    phase="runtime",
    explanation="Called unwrap() on a None value.",
)

E_RUNTIME_UNWRAP_ERR = ErrorCode(
    code="MN-R0004",
    title="unwrap on Err",
    phase="runtime",
    explanation="Called unwrap() on an Err value.",
)

E_RUNTIME_INDEX_OUT_OF_BOUNDS = ErrorCode(
    code="MN-R0005",
    title="index out of bounds",
    phase="runtime",
    explanation="List index is outside the valid range.",
)

E_RUNTIME_DIVISION_BY_ZERO = ErrorCode(
    code="MN-R0006",
    title="division by zero",
    phase="runtime",
    explanation="Attempted to divide by zero.",
)

E_RUNTIME_ASSERTION_FAILED = ErrorCode(
    code="MN-R0007",
    title="assertion failed",
    phase="runtime",
    explanation="An assert expression evaluated to false.",
)

E_RUNTIME_CHANNEL_CLOSED = ErrorCode(
    code="MN-R0008",
    title="channel closed",
    phase="runtime",
    explanation="Attempted to send or receive on a closed channel.",
)

# ---------------------------------------------------------------------------
# Tooling errors (MN-T0xxx)
# ---------------------------------------------------------------------------

E_TOOL_FILE_NOT_FOUND = ErrorCode(
    code="MN-T0001",
    title="file not found",
    phase="tooling",
    explanation="The specified source file does not exist.",
)

E_TOOL_NO_TESTS_FOUND = ErrorCode(
    code="MN-T0002",
    title="no tests found",
    phase="tooling",
    explanation="No @test functions were found in the specified path.",
)

E_TOOL_MANIFEST_ERROR = ErrorCode(
    code="MN-T0003",
    title="manifest error",
    phase="tooling",
    explanation="The mapanare.toml manifest file is missing or invalid.",
)

# ---------------------------------------------------------------------------
# Error code registry
# ---------------------------------------------------------------------------

ALL_ERROR_CODES: list[ErrorCode] = [
    # Parse
    E_PARSE_UNEXPECTED_TOKEN,
    E_PARSE_UNCLOSED_BRACE,
    E_PARSE_UNCLOSED_PAREN,
    E_PARSE_UNCLOSED_BRACKET,
    E_PARSE_INVALID_LITERAL,
    E_PARSE_UNTERMINATED_STRING,
    E_PARSE_INVALID_ESCAPE,
    # Semantic
    E_SEM_UNDEFINED_VAR,
    E_SEM_TYPE_MISMATCH,
    E_SEM_UNDEFINED_FUNCTION,
    E_SEM_ARITY_MISMATCH,
    E_SEM_DUPLICATE_DEFINITION,
    E_SEM_IMMUTABLE_ASSIGN,
    E_SEM_UNDEFINED_TYPE,
    E_SEM_UNDEFINED_FIELD,
    E_SEM_MISSING_RETURN,
    E_SEM_UNREACHABLE_CODE,
    E_SEM_NON_EXHAUSTIVE_MATCH,
    E_SEM_INVALID_PIPE,
    # Lowering
    E_LOWER_UNSUPPORTED_NODE,
    E_LOWER_INTERNAL,
    # Codegen
    E_CODEGEN_UNSUPPORTED_TYPE,
    E_CODEGEN_LLVM_ERROR,
    E_CODEGEN_LINK_ERROR,
    # Runtime
    E_RUNTIME_AGENT_SEND_FAILED,
    E_RUNTIME_AGENT_SPAWN_FAILED,
    E_RUNTIME_UNWRAP_NONE,
    E_RUNTIME_UNWRAP_ERR,
    E_RUNTIME_INDEX_OUT_OF_BOUNDS,
    E_RUNTIME_DIVISION_BY_ZERO,
    E_RUNTIME_ASSERTION_FAILED,
    E_RUNTIME_CHANNEL_CLOSED,
    # Tooling
    E_TOOL_FILE_NOT_FOUND,
    E_TOOL_NO_TESTS_FOUND,
    E_TOOL_MANIFEST_ERROR,
]

_CODE_INDEX: dict[str, ErrorCode] = {ec.code: ec for ec in ALL_ERROR_CODES}


def lookup_error_code(code: str) -> ErrorCode | None:
    """Look up an error code by its string identifier (e.g., 'MN-S0001')."""
    return _CODE_INDEX.get(code)
