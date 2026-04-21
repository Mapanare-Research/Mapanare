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
    FUTURE = auto()  # v4.69.0: Future<T> — coroutine result type

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
    ANY = auto()
    UNKNOWN = auto()  # deprecated alias for UNRESOLVED
    UNRESOLVED = auto()  # inference pending — will be resolved later
    ERROR = auto()  # inference failed — must produce diagnostic
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
    "Future": TypeKind.FUTURE,
    "Range": TypeKind.RANGE,
    "any": TypeKind.ANY,
}

# Map from TypeKind to canonical display name
_KIND_TO_NAME: dict[TypeKind, str] = {v: k for k, v in _NAME_TO_KIND.items()}
_KIND_TO_NAME[TypeKind.FN] = "fn"
_KIND_TO_NAME[TypeKind.UNKNOWN] = "<unknown>"
_KIND_TO_NAME[TypeKind.UNRESOLVED] = "<unresolved>"
_KIND_TO_NAME[TypeKind.ERROR] = "<error>"
_KIND_TO_NAME[TypeKind.BUILTIN_FN] = "<builtin>"
_KIND_TO_NAME[TypeKind.STRUCT] = "struct"
_KIND_TO_NAME[TypeKind.ENUM] = "enum"
_KIND_TO_NAME[TypeKind.AGENT] = "agent"
_KIND_TO_NAME[TypeKind.PIPE] = "pipe"
_KIND_TO_NAME[TypeKind.TYPE_ALIAS] = "type"
_KIND_TO_NAME[TypeKind.TRAIT] = "trait"
_KIND_TO_NAME[TypeKind.TYPE_VAR] = "TypeVar"
_KIND_TO_NAME[TypeKind.ANY] = "any"


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
        if self.kind in (TypeKind.UNKNOWN, TypeKind.UNRESOLVED, TypeKind.ERROR):
            return False
        if other.kind in (TypeKind.UNKNOWN, TypeKind.UNRESOLVED, TypeKind.ERROR):
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
        return hash((self.kind, self.name, tuple(self.args)))

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
        """Permissive matching for inference contexts.

        UNKNOWN/UNRESOLVED is compatible with anything (not yet resolved).
        ERROR is compatible with nothing (forces error propagation).
        """
        if self.kind == TypeKind.ERROR or other.kind == TypeKind.ERROR:
            return False
        if self.kind in (TypeKind.UNKNOWN, TypeKind.UNRESOLVED):
            return True
        if other.kind in (TypeKind.UNKNOWN, TypeKind.UNRESOLVED):
            return True
        # Dynamic `any` type is compatible with everything (gradual typing)
        if self.kind == TypeKind.ANY or other.kind == TypeKind.ANY:
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

UNKNOWN_TYPE = TypeInfo(kind=TypeKind.UNKNOWN)  # deprecated, use UNRESOLVED_TYPE
UNRESOLVED_TYPE = TypeInfo(kind=TypeKind.UNRESOLVED)
ERROR_TYPE = TypeInfo(kind=TypeKind.ERROR)
INT_TYPE = TypeInfo(kind=TypeKind.INT)
FLOAT_TYPE = TypeInfo(kind=TypeKind.FLOAT)
BOOL_TYPE = TypeInfo(kind=TypeKind.BOOL)
STRING_TYPE = TypeInfo(kind=TypeKind.STRING)
CHAR_TYPE = TypeInfo(kind=TypeKind.CHAR)
VOID_TYPE = TypeInfo(kind=TypeKind.VOID)
RANGE_TYPE = TypeInfo(kind=TypeKind.RANGE)
ANY_TYPE = TypeInfo(kind=TypeKind.ANY)


# ---------------------------------------------------------------------------
# Builtin registries (single source of truth)
# ---------------------------------------------------------------------------

PRIMITIVE_TYPES = frozenset({"Int", "Float", "Bool", "String", "Char", "Void"})

PRIMITIVE_KINDS = frozenset(
    {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.STRING, TypeKind.CHAR, TypeKind.VOID}
)

BUILTIN_GENERIC_TYPES = frozenset(
    {"Option", "Result", "List", "Map", "Signal", "Stream", "Channel", "Tensor", "Future"}
)

BUILTIN_GENERIC_ARITY: dict[str, int] = {
    "List": 1,
    "Map": 2,
    "Option": 1,
    "Result": 2,
    "Signal": 1,
    "Stream": 1,
    "Tensor": 1,
    "Channel": 1,
    "Future": 1,
}

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
        TypeKind.FUTURE,
    }
)

# Built-in functions: name -> return TypeInfo
BUILTIN_FUNCTIONS: dict[str, TypeInfo] = {
    "print": VOID_TYPE,
    "println": VOID_TYPE,  # deprecated: use print (both add newline)
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
    "ord": INT_TYPE,
    "chr": STRING_TYPE,
    "join": STRING_TYPE,
    "typeof": STRING_TYPE,
    # StringBuilder builtins (v4.95.0)
    "sb_create": UNKNOWN_TYPE,  # sb_create() -> StringBuilder
    "sb_append": VOID_TYPE,  # sb_append(sb, str) -> void
    "sb_to_string": STRING_TYPE,  # sb_to_string(sb) -> String (consumes builder)
    # Async/await builtins (v4.73.0+)
    "block_on": UNKNOWN_TYPE,  # block_on(Future<T>) -> T; type inferred from future
    "spawn": TypeInfo(
        kind=TypeKind.FUTURE
    ),  # v4.93.0: spawn async task for multi-threaded execution
    "__mn_file_read_async": TypeInfo(kind=TypeKind.FUTURE),  # v4.92.0: async file read
    # C runtime functions used by the self-hosted compiler driver (main.mn)
    "__mn_argc": INT_TYPE,
    "__mn_argv": STRING_TYPE,
    "__mn_file_read_or_empty": STRING_TYPE,
    "__mn_exit": VOID_TYPE,
    "__mn_str_eprint": VOID_TYPE,
    "__mn_str_eprintln": VOID_TYPE,
    "__mn_system": INT_TYPE,
    "__mn_file_write": VOID_TYPE,
    # High-level I/O builtins (v3.41.0)
    "read_line": STRING_TYPE,
    "read_file": STRING_TYPE,
    "write_file": VOID_TYPE,
    "append_file": VOID_TYPE,
    "file_exists": TypeInfo(kind=TypeKind.BOOL),
    "list_dir": TypeInfo(kind=TypeKind.LIST),
    # Network, crypto, regex builtins (v3.42.0)
    "http_get": STRING_TYPE,
    "sha256": STRING_TYPE,
    "base64_encode": STRING_TYPE,
    "base64_decode": STRING_TYPE,
    "hmac_sha256": STRING_TYPE,
    "hex_encode": STRING_TYPE,
    "random_bytes": STRING_TYPE,
    "regex_match": TypeInfo(kind=TypeKind.BOOL),
    "regex_replace": STRING_TYPE,
    # GPU builtins (v3.46.0)
    "gpu_available": TypeInfo(kind=TypeKind.BOOL),
    "gpu_device_name": STRING_TYPE,
    "gpu_device_memory": INT_TYPE,
    "gpu_tensor_add": TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)]),
    "gpu_tensor_sub": TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)]),
    "gpu_tensor_mul": TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)]),
    "gpu_tensor_div": TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)]),
    "gpu_tensor_matmul": TypeInfo(kind=TypeKind.LIST, args=[TypeInfo(kind=TypeKind.FLOAT)]),
    # Tensor builtins (v4.42.0)
    "tensor_rank": INT_TYPE,
    "tensor_size": INT_TYPE,
    "tensor_get_f64": TypeInfo(kind=TypeKind.FLOAT),
    "tensor_get_i64": INT_TYPE,
    "tensor_shape_dim": INT_TYPE,
    "tensor_print": VOID_TYPE,
}

# Builtin call name mapping (Mapanare name -> Python name) for emit_python.py
BUILTIN_CALL_MAP: dict[str, str] = {
    "str": "str",
    "toString": "str",
    "int": "int",
    "float": "float",
    "ord": "ord",
    "chr": "chr",
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
    "any": "Any",
}


# Builtin trait names and their method signatures:
# Each entry is (trait_name, [(method_name, has_self, param_names, return_type_name)])
BUILTIN_TRAITS: dict[str, list[tuple[str, bool, list[tuple[str, str]], str | None]]] = {
    "Display": [("to_string", True, [], "String")],
    "Eq": [("eq", True, [("other", "Self")], "Bool")],
    "Ord": [("cmp", True, [("other", "Self")], "Int")],
    "Hash": [("hash", True, [], "Int")],
    "Add": [("add", True, [("other", "Self")], "Self")],
    "Sub": [("sub", True, [("other", "Self")], "Self")],
    "Mul": [("mul", True, [("other", "Self")], "Self")],
    "Div": [("div", True, [("other", "Self")], "Self")],
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


def broadcast_shape(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...] | None:
    """Compute the broadcast result shape using NumPy rules (v4.44.0).

    Aligns from trailing dimensions. Each dimension pair must be equal or
    one of them must be 1. The shorter shape is left-padded with 1s.
    Returns None if shapes are not broadcast-compatible.
    """
    max_rank = max(len(a), len(b))
    a_padded = (1,) * (max_rank - len(a)) + a
    b_padded = (1,) * (max_rank - len(b)) + b

    result: list[int] = []
    for ai, bi in zip(a_padded, b_padded):
        if ai == bi:
            result.append(ai)
        elif ai == 1:
            result.append(bi)
        elif bi == 1:
            result.append(ai)
        else:
            return None  # incompatible
    return tuple(result)


def broadcast_incompatible_dim(a: tuple[int, ...], b: tuple[int, ...]) -> int | None:
    """Return the 0-based dimension index (from trailing) where broadcasting fails.

    Used for rustc-quality diagnostics. Returns None if shapes are compatible.
    """
    max_rank = max(len(a), len(b))
    a_padded = (1,) * (max_rank - len(a)) + a
    b_padded = (1,) * (max_rank - len(b)) + b

    for i, (ai, bi) in enumerate(zip(a_padded, b_padded)):
        if ai != bi and ai != 1 and bi != 1:
            return i
    return None


def make_type(name: str, **kwargs: object) -> TypeInfo:
    """Create a TypeInfo from a type name string. Convenience factory."""
    k = _NAME_TO_KIND.get(name, TypeKind.UNKNOWN)
    if k == TypeKind.UNKNOWN and name not in ("<unknown>", ""):
        # Assume user-defined struct/enum/agent — kind will be refined by semantic checker
        return TypeInfo(kind=TypeKind.STRUCT, name=name, **kwargs)  # type: ignore[arg-type]
    return TypeInfo(kind=k, **kwargs)  # type: ignore[arg-type]
