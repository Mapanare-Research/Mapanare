"""Canonical type representation for the Mapanare language.

This module is the single source of truth for:
- TypeKind enum (replaces string-based type comparisons)
- TypeInfo dataclass (resolved type information)
- Builtin type/function registries used by semantic checker and emitters
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type kind enum
# ---------------------------------------------------------------------------


class TypeKind(Enum):
    """Enumeration of all type kinds in Mapanare."""

    # Primitives
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    STRING = auto()
    CHAR = auto()
    VOID = auto()

    # Generic containers
    LIST = auto()
    MAP = auto()
    OPTION = auto()
    RESULT = auto()
    SIGNAL = auto()
    STREAM = auto()
    CHANNEL = auto()
    TENSOR = auto()

    # Compound / user-defined
    FN = auto()
    STRUCT = auto()
    ENUM = auto()
    AGENT = auto()
    PIPE = auto()
    TYPE_ALIAS = auto()
    TRAIT = auto()

    # Special
    TYPE_VAR = auto()
    RANGE = auto()
    UNKNOWN = auto()
    BUILTIN_FN = auto()


# ---------------------------------------------------------------------------
# Name <-> TypeKind mappings
# ---------------------------------------------------------------------------

# Map from canonical type name strings to TypeKind
_NAME_TO_KIND: dict[str, TypeKind] = {
    "Int": TypeKind.INT,
    "Float": TypeKind.FLOAT,
    "Bool": TypeKind.BOOL,
    "String": TypeKind.STRING,
    "Char": TypeKind.CHAR,
    "Void": TypeKind.VOID,
    "List": TypeKind.LIST,
    "Map": TypeKind.MAP,
    "Option": TypeKind.OPTION,
    "Result": TypeKind.RESULT,
    "Signal": TypeKind.SIGNAL,
    "Stream": TypeKind.STREAM,
    "Channel": TypeKind.CHANNEL,
    "Tensor": TypeKind.TENSOR,
    "Range": TypeKind.RANGE,
}

# Map from TypeKind to canonical display name
_KIND_TO_NAME: dict[TypeKind, str] = {v: k for k, v in _NAME_TO_KIND.items()}
_KIND_TO_NAME[TypeKind.FN] = "fn"
_KIND_TO_NAME[TypeKind.UNKNOWN] = "<unknown>"
_KIND_TO_NAME[TypeKind.BUILTIN_FN] = "<builtin>"
_KIND_TO_NAME[TypeKind.STRUCT] = "struct"
_KIND_TO_NAME[TypeKind.ENUM] = "enum"
_KIND_TO_NAME[TypeKind.AGENT] = "agent"
_KIND_TO_NAME[TypeKind.PIPE] = "pipe"
_KIND_TO_NAME[TypeKind.TYPE_ALIAS] = "type"
_KIND_TO_NAME[TypeKind.TRAIT] = "trait"
_KIND_TO_NAME[TypeKind.TYPE_VAR] = "TypeVar"


def kind_from_name(name: str) -> TypeKind:
    """Resolve a type name string to a TypeKind. Returns UNKNOWN for unrecognized names."""
    return _NAME_TO_KIND.get(name, TypeKind.UNKNOWN)


# ---------------------------------------------------------------------------
# TypeInfo dataclass
# ---------------------------------------------------------------------------


@dataclass
class TypeInfo:
    """Resolved type information for an expression or binding."""

    kind: TypeKind = TypeKind.UNKNOWN
    name: str = ""  # User-defined type name (for STRUCT, ENUM, AGENT, etc.)
    args: list[TypeInfo] = field(default_factory=list)
    is_function: bool = False
    param_types: list[TypeInfo] = field(default_factory=list)
    return_type: Optional[TypeInfo] = None
    # Compile-time tensor shape (None = dynamic/unknown)
    tensor_shape: Optional[tuple[int, ...]] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeInfo):
            return NotImplemented
        if self.kind == TypeKind.UNKNOWN or other.kind == TypeKind.UNKNOWN:
            return False
        if self.is_function and other.is_function:
            return (
                self.return_type == other.return_type
                and len(self.param_types) == len(other.param_types)
                and all(a == b for a, b in zip(self.param_types, other.param_types))
            )
        if self.kind != other.kind:
            return False
        # For user-defined types, also compare names
        if self.kind in _USER_DEFINED_KINDS:
            if self.name != other.name:
                return False
        if len(self.args) != len(other.args):
            return False
        return all(a == b for a, b in zip(self.args, other.args))

    def __hash__(self) -> int:
        return hash((self.kind, self.name))

    def __repr__(self) -> str:
        if self.is_function:
            params = ", ".join(repr(p) for p in self.param_types)
            ret = repr(self.return_type) if self.return_type else "Void"
            return f"fn({params}) -> {ret}"
        if self.kind == TypeKind.TENSOR and self.tensor_shape is not None:
            elem = repr(self.args[0]) if self.args else "?"
            dims = ", ".join(str(d) for d in self.tensor_shape)
            return f"Tensor<{elem}>[{dims}]"
        if self.args:
            args = ", ".join(repr(a) for a in self.args)
            return f"{self.display_name}<{args}>"
        return self.display_name

    @property
    def display_name(self) -> str:
        """Human-readable type name."""
        if self.kind in _USER_DEFINED_KINDS and self.name:
            return self.name
        return _KIND_TO_NAME.get(self.kind, "<unknown>")

    def is_compatible_with(self, other: "TypeInfo") -> bool:
        """Permissive matching: UNKNOWN is compatible with anything (recursive).
        Use for inference contexts where UNKNOWN means 'not yet resolved'.
        Use __eq__ for strict equality.
        """
        if self.kind == TypeKind.UNKNOWN or other.kind == TypeKind.UNKNOWN:
            return True
        if self.is_function and other.is_function:
            if self.return_type and other.return_type:
                if not self.return_type.is_compatible_with(other.return_type):
                    return False
            if len(self.param_types) != len(other.param_types):
                return False
            return all(a.is_compatible_with(b) for a, b in zip(self.param_types, other.param_types))
        if self.kind != other.kind:
            return False
        if self.kind in _USER_DEFINED_KINDS:
            if self.name != other.name:
                return False
        if len(self.args) != len(other.args):
            return True  # partial generic matching ok for compatibility
        return all(a.is_compatible_with(b) for a, b in zip(self.args, other.args))

    def is_numeric(self) -> bool:
        """Return True if this is Int or Float."""
        return self.kind in (TypeKind.INT, TypeKind.FLOAT)

    def is_primitive(self) -> bool:
        """Return True if this is a primitive type."""
        return self.kind in PRIMITIVE_KINDS


# Kinds that carry a user-defined name
_USER_DEFINED_KINDS = frozenset(
    {
        TypeKind.STRUCT,
        TypeKind.ENUM,
        TypeKind.AGENT,
        TypeKind.PIPE,
        TypeKind.TYPE_ALIAS,
        TypeKind.TRAIT,
    }
)


# ---------------------------------------------------------------------------
# Canonical type singletons
# ---------------------------------------------------------------------------

UNKNOWN_TYPE = TypeInfo(kind=TypeKind.UNKNOWN)
INT_TYPE = TypeInfo(kind=TypeKind.INT)
FLOAT_TYPE = TypeInfo(kind=TypeKind.FLOAT)
BOOL_TYPE = TypeInfo(kind=TypeKind.BOOL)
STRING_TYPE = TypeInfo(kind=TypeKind.STRING)
CHAR_TYPE = TypeInfo(kind=TypeKind.CHAR)
VOID_TYPE = TypeInfo(kind=TypeKind.VOID)
RANGE_TYPE = TypeInfo(kind=TypeKind.RANGE)


# ---------------------------------------------------------------------------
# Builtin registries (single source of truth)
# ---------------------------------------------------------------------------

PRIMITIVE_TYPES = frozenset({"Int", "Float", "Bool", "String", "Char", "Void"})

PRIMITIVE_KINDS = frozenset(
    {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.STRING, TypeKind.CHAR, TypeKind.VOID}
)

BUILTIN_GENERIC_TYPES = frozenset(
    {"Option", "Result", "List", "Map", "Signal", "Stream", "Channel", "Tensor"}
)

BUILTIN_GENERIC_KINDS = frozenset(
    {
        TypeKind.OPTION,
        TypeKind.RESULT,
        TypeKind.LIST,
        TypeKind.MAP,
        TypeKind.SIGNAL,
        TypeKind.STREAM,
        TypeKind.CHANNEL,
        TypeKind.TENSOR,
    }
)

# Built-in functions: name -> return TypeInfo
BUILTIN_FUNCTIONS: dict[str, TypeInfo] = {
    "print": VOID_TYPE,
    "println": VOID_TYPE,
    "len": INT_TYPE,
    "toString": STRING_TYPE,
    "str": STRING_TYPE,
    "int": INT_TYPE,
    "float": FLOAT_TYPE,
    "Some": TypeInfo(kind=TypeKind.OPTION),
    "Ok": TypeInfo(kind=TypeKind.RESULT),
    "Err": TypeInfo(kind=TypeKind.RESULT),
    "signal": TypeInfo(kind=TypeKind.SIGNAL),
    "stream": TypeInfo(kind=TypeKind.STREAM),
}

# Builtin call name mapping (Mapanare name -> Python name) for emit_python.py
BUILTIN_CALL_MAP: dict[str, str] = {
    "str": "str",
    "toString": "str",
    "int": "int",
    "float": "float",
}

# Mapanare type name -> Python type name for emit_python.py
PYTHON_TYPE_MAP: dict[str, str] = {
    "Int": "int",
    "Float": "float",
    "Bool": "bool",
    "String": "str",
    "Char": "str",
    "Void": "None",
    "Any": "Any",
}


# Builtin trait names and their method signatures:
# Each entry is (trait_name, [(method_name, has_self, param_names, return_type_name)])
BUILTIN_TRAITS: dict[str, list[tuple[str, bool, list[tuple[str, str]], str | None]]] = {
    "Display": [("to_string", True, [], "String")],
    "Eq": [("eq", True, [("other", "Self")], "Bool")],
    "Ord": [("cmp", True, [("other", "Self")], "Int")],
    "Hash": [("hash", True, [], "Int")],
}


def _type_display(t: TypeInfo) -> str:
    """Human-readable type string for error messages."""
    return repr(t)


# ---------------------------------------------------------------------------
# Device annotations (used by semantic checker for @gpu/@cpu validation)
# ---------------------------------------------------------------------------

DEVICE_ANNOTATIONS = frozenset({"gpu", "cpu", "cuda", "metal", "vulkan"})


# ---------------------------------------------------------------------------
# Tensor shape validation (used by semantic checker at compile time)
# ---------------------------------------------------------------------------


def resolve_shape_from_type(
    shape_exprs: list[object],
) -> tuple[int, ...] | None:
    """Try to resolve a shape tuple from AST shape expressions.

    Returns the shape if all dimensions are integer literals, None if
    any dimension is dynamic (non-literal).
    """
    from mapanare.ast_nodes import IntLiteral

    dims: list[int] = []
    for expr in shape_exprs:
        if isinstance(expr, IntLiteral):
            dims.append(expr.value)
        else:
            return None  # Dynamic dimension
    return tuple(dims)


def validate_matmul_shapes(
    a_shape: tuple[int, ...], b_shape: tuple[int, ...]
) -> tuple[int, ...] | None:
    """Validate shapes for matmul and return result shape, or None if invalid."""
    a_ndim = len(a_shape)
    b_ndim = len(b_shape)

    if a_ndim == 1 and b_ndim == 1:
        if a_shape[0] == b_shape[0]:
            return (1,)
        return None
    if a_ndim == 2 and b_ndim == 2:
        if a_shape[1] == b_shape[0]:
            return (a_shape[0], b_shape[1])
        return None
    if a_ndim == 2 and b_ndim == 1:
        if a_shape[1] == b_shape[0]:
            return (a_shape[0],)
        return None
    if a_ndim == 1 and b_ndim == 2:
        if a_shape[0] == b_shape[0]:
            return (b_shape[1],)
        return None
    return None


def make_type(name: str, **kwargs: object) -> TypeInfo:
    """Create a TypeInfo from a type name string. Convenience factory."""
    k = _NAME_TO_KIND.get(name, TypeKind.UNKNOWN)
    if k == TypeKind.UNKNOWN and name not in ("<unknown>", ""):
        # Assume user-defined struct/enum/agent — kind will be refined by semantic checker
        return TypeInfo(kind=TypeKind.STRUCT, name=name, **kwargs)  # type: ignore[arg-type]
    return TypeInfo(kind=k, **kwargs)  # type: ignore[arg-type]
