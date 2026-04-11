"""Auto-generated FFI binding generator for Mapanare.

Reads .mn function signatures and generates language-specific bindings:
- Python: ctypes wrapper module
- TypeScript: .d.ts type declarations + WASM loader
- Go: cgo binding file
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mapanare.ast_nodes import (
    EnumDef,
    FnDef,
    NamedType,
    StructDef,
    TypeExpr,
)
from mapanare.parser import parse

# ---------------------------------------------------------------------------
# Binding spec extraction
# ---------------------------------------------------------------------------

TYPE_MAP_PYTHON = {
    "Int": "int",
    "Float": "float",
    "Bool": "bool",
    "String": "str",
    "Void": "None",
}

TYPE_MAP_TS = {
    "Int": "number",
    "Float": "number",
    "Bool": "boolean",
    "String": "string",
    "Void": "void",
}

TYPE_MAP_GO = {
    "Int": "int64",
    "Float": "float64",
    "Bool": "bool",
    "String": "string",
    "Void": "",
}


@dataclass
class BindParam:
    name: str
    type_name: str


@dataclass
class BindFunction:
    name: str
    params: list[BindParam] = field(default_factory=list)
    return_type: str = "Void"


@dataclass
class BindField:
    name: str
    type_name: str


@dataclass
class BindStruct:
    name: str
    fields: list[BindField] = field(default_factory=list)


@dataclass
class BindEnum:
    name: str
    variants: list[str] = field(default_factory=list)


@dataclass
class BindingSpec:
    module_name: str = ""
    functions: list[BindFunction] = field(default_factory=list)
    structs: list[BindStruct] = field(default_factory=list)
    enums: list[BindEnum] = field(default_factory=list)


def _type_name(te: TypeExpr | None) -> str:
    if te is None:
        return "Void"
    if isinstance(te, NamedType):
        return te.name
    return "Void"


def extract_binding_spec(source: str, module_name: str = "module") -> BindingSpec:
    """Parse .mn source and extract public API for binding generation."""
    ast = parse(source, filename=module_name + ".mn")
    spec = BindingSpec(module_name=module_name)

    for defn in ast.definitions:
        if isinstance(defn, FnDef):
            if defn.name.startswith("_") or defn.name == "main":
                continue
            params = [
                BindParam(name=p.name, type_name=_type_name(p.type_annotation)) for p in defn.params
            ]
            ret = _type_name(defn.return_type)
            spec.functions.append(BindFunction(name=defn.name, params=params, return_type=ret))

        elif isinstance(defn, StructDef):
            if defn.name.startswith("_"):
                continue
            fields = [
                BindField(name=f.name, type_name=_type_name(f.type_annotation)) for f in defn.fields
            ]
            spec.structs.append(BindStruct(name=defn.name, fields=fields))

        elif isinstance(defn, EnumDef):
            if defn.name.startswith("_"):
                continue
            variants = [v.name for v in defn.variants]
            spec.enums.append(BindEnum(name=defn.name, variants=variants))

    return spec


# ---------------------------------------------------------------------------
# Python binding generation
# ---------------------------------------------------------------------------


_PY_CTYPE_FOR_PRIMITIVE = {
    "Int": "ctypes.c_int64",
    "Float": "ctypes.c_double",
    "Bool": "ctypes.c_bool",
}

_PY_ANNOTATION_FOR_PRIMITIVE = {
    "Int": "int",
    "Float": "float",
    "Bool": "bool",
    "String": "str",
    "Void": "None",
}


def _py_ctype_for(type_name: str, known_structs: set[str]) -> str:
    """Return the ctypes token used in argtypes/restype for a Mapanare type."""
    if type_name == "String":
        return "_MnString"
    if type_name in _PY_CTYPE_FOR_PRIMITIVE:
        return _PY_CTYPE_FOR_PRIMITIVE[type_name]
    if type_name in known_structs:
        return type_name
    if type_name == "Void":
        return "None"
    # Enum variants reach the .so as i64 tag values.
    return "ctypes.c_int64"


def _py_annotation_for(type_name: str, known_structs: set[str]) -> str:
    """Return the Python type annotation used in the wrapper function signature."""
    if type_name in _PY_ANNOTATION_FOR_PRIMITIVE:
        return _PY_ANNOTATION_FOR_PRIMITIVE[type_name]
    if type_name in known_structs:
        return type_name
    return "int"


def generate_python(spec: BindingSpec) -> str:
    """Generate a Python ctypes binding module.

    v4.27.0 recovery: the wrapper now populates ``argtypes`` and ``restype``
    from the Mapanare signature so ctypes does not silently reinterpret
    ``Float`` returns as ``c_int`` or pass ``str`` through ``char*`` (which
    corrupts ABI on the Mapanare side because ``String`` is ``{ptr, i64}``).
    Previously only ``add(int, int) -> int`` worked, and only by coincidence.
    """
    known_structs = {st.name for st in spec.structs}

    lines: list[str] = [
        f'"""Auto-generated Python bindings for {spec.module_name}.',
        "",
        "Generated by ``mapanare bind --lang python`` (v4.27.0). The wrapper",
        "populates ctypes ``argtypes`` and ``restype`` so every Mapanare type",
        "is marshalled correctly on the way in and the way out.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "import ctypes",
        "import os",
        "",
        f'_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "lib{spec.module_name}.so"))',
        "",
        "",
        "# ---------------------------------------------------------------------------",
        "# Mapanare ABI glue",
        "# ---------------------------------------------------------------------------",
        "",
        "",
        "# Mapanare uses low-bit pointer tagging (``mn_tag_heap``/``mn_untag``) on",
        "# string data: a heap-allocated string has its pointer OR'd with 1 so the",
        "# runtime can tell heap strings from static ones for drop glue. All C",
        "# consumers call ``mn_untag`` before dereferencing. The Python wrapper has",
        "# to do the same when it reads a ``String`` result back — skipping this",
        "# step reads one byte into the real allocation and drops the leading",
        "# character, which is exactly how v4.25.0 ``greet`` produced ``ello, world``.",
        "_MN_PTR_TAG_MASK = ~1",
        "",
        "",
        "class _MnString(ctypes.Structure):",
        '    """Mapanare ``String`` — a ``{ptr, len}`` value, not a C char*."""',
        "",
        "    _fields_ = [",
        '        ("ptr", ctypes.c_void_p),',
        '        ("len", ctypes.c_int64),',
        "    ]",
        "",
        "    @classmethod",
        "    def from_str(cls, s: str) -> _MnString:",
        '        """Encode a Python ``str`` into a Mapanare-owned byte buffer.',
        "",
        "        Python allocators return at least 8-byte-aligned buffers, so the",
        "        low pointer bit is already 0 (i.e. ``mn_is_heap`` is false). Leave",
        '        it untagged so the Mapanare runtime treats the buffer as borrowed."""',
        '        data = s.encode("utf-8")',
        "        buf = ctypes.create_string_buffer(data)",
        "        # Keep the underlying buffer alive by stashing it on the struct.",
        "        inst = cls()",
        "        inst.ptr = ctypes.cast(buf, ctypes.c_void_p).value or 0",
        "        inst.len = len(data)",
        "        inst._keepalive = buf  # type: ignore[attr-defined]",
        "        return inst",
        "",
        "    def to_str(self) -> str:",
        '        """Decode a Mapanare ``String`` value back to a Python ``str``.',
        "",
        "        Strips the low-bit heap tag before dereferencing the pointer; the",
        "        Mapanare runtime sets that bit on heap-allocated strings (see",
        '        ``mn_tag_heap`` in ``runtime/native/mapanare_core.c``)."""',
        "        if not self.ptr or self.len <= 0:",
        '            return ""',
        "        real_ptr = self.ptr & _MN_PTR_TAG_MASK",
        "        raw = ctypes.string_at(real_ptr, self.len)",
        '        return raw.decode("utf-8")',
        "",
    ]

    # Struct definitions must appear before any function that references them in
    # argtypes / restype — ctypes needs the class to exist when we assign.
    for st in spec.structs:
        lines.append(f"class {st.name}(ctypes.Structure):")
        lines.append(f'    """Mapanare ``{st.name}`` — passed and returned by value."""')
        lines.append("")
        lines.append("    _fields_ = [")
        for f in st.fields:
            ctype = _py_ctype_for(f.type_name, known_structs)
            if ctype == "_MnString":
                ctype = "_MnString"
            elif ctype not in {"_MnString"} and not ctype.startswith("ctypes."):
                # Nested struct — reference the class directly.
                pass
            lines.append(f'        ("{f.name}", {ctype}),')
        lines.append("    ]")
        lines.append("")

    for en in spec.enums:
        for i, v in enumerate(en.variants):
            lines.append(f"{en.name}_{v} = {i}")
        lines.append("")

    # ``argtypes``/``restype`` assignments. Doing this once at module load time
    # means every subsequent call is correctly typed.
    divider = "# " + "-" * 73
    if spec.functions:
        lines.append(divider)
        lines.append("# ctypes argtypes / restype — v4.27.0: no more silent ABI corruption")
        lines.append(divider)
        lines.append("")
    for fn in spec.functions:
        argtypes = ", ".join(_py_ctype_for(p.type_name, known_structs) for p in fn.params)
        restype = _py_ctype_for(fn.return_type, known_structs)
        lines.append(f"_lib.{fn.name}.argtypes = [{argtypes}]")
        if restype == "None":
            lines.append(f"_lib.{fn.name}.restype = None")
        else:
            lines.append(f"_lib.{fn.name}.restype = {restype}")
    if spec.functions:
        lines.append("")

    # Python wrapper functions — convert ``str``→``_MnString`` on input and
    # ``_MnString``→``str`` on output so callers work with native Python types.
    for fn in spec.functions:
        py_params = ", ".join(
            f"{p.name}: {_py_annotation_for(p.type_name, known_structs)}" for p in fn.params
        )
        py_ret = _py_annotation_for(fn.return_type, known_structs)
        lines.append(f"def {fn.name}({py_params}) -> {py_ret}:")
        # Marshal inputs
        call_args: list[str] = []
        for p in fn.params:
            if p.type_name == "String":
                call_args.append(f"_MnString.from_str({p.name})")
            else:
                call_args.append(p.name)
        call_expr = f"_lib.{fn.name}({', '.join(call_args)})"
        if fn.return_type == "String":
            lines.append(f"    _result = {call_expr}")
            lines.append("    return _result.to_str()")
        elif fn.return_type == "Void":
            lines.append(f"    {call_expr}")
        else:
            lines.append(f"    return {call_expr}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TypeScript binding generation
# ---------------------------------------------------------------------------


def generate_typescript(spec: BindingSpec) -> str:
    """Generate TypeScript type declarations."""
    lines = [
        f"// Auto-generated TypeScript bindings for {spec.module_name}",
        "",
    ]

    for st in spec.structs:
        lines.append(f"export interface {st.name} {{")
        for f in st.fields:
            ts_ty = TYPE_MAP_TS.get(f.type_name, "any")
            lines.append(f"  {f.name}: {ts_ty};")
        lines.append("}")
        lines.append("")

    for en in spec.enums:
        lines.append(f"export enum {en.name} {{")
        for v in en.variants:
            lines.append(f"  {v},")
        lines.append("}")
        lines.append("")

    for fn in spec.functions:
        ts_params = ", ".join(f"{p.name}: {TYPE_MAP_TS.get(p.type_name, 'any')}" for p in fn.params)
        ts_ret = TYPE_MAP_TS.get(fn.return_type, "any")
        lines.append(f"export declare function {fn.name}({ts_params}): {ts_ret};")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Go binding generation
# ---------------------------------------------------------------------------


def generate_go(spec: BindingSpec) -> str:
    """Generate Go cgo binding file."""
    lines = [
        f"// Auto-generated Go bindings for {spec.module_name}",
        f"package {spec.module_name}",
        "",
        "// #cgo LDFLAGS: -L. -l" + spec.module_name,
        "// #include <stdint.h>",
        'import "C"',
        "",
    ]

    for fn in spec.functions:
        go_params = ", ".join(
            f"{p.name} {TYPE_MAP_GO.get(p.type_name, 'int64')}" for p in fn.params
        )
        go_ret = TYPE_MAP_GO.get(fn.return_type, "int64")
        ret_decl = f" {go_ret}" if go_ret else ""
        lines.append(f"func {fn.name.title()}({go_params}){ret_decl} {{")
        if go_ret:
            c_args = ", ".join(f"C.int64_t({p.name})" for p in fn.params)
            lines.append(f"\treturn {go_ret}(C.{fn.name}({c_args}))")
        else:
            c_args = ", ".join(f"C.int64_t({p.name})" for p in fn.params)
            lines.append(f"\tC.{fn.name}({c_args})")
        lines.append("}")
        lines.append("")

    for st in spec.structs:
        lines.append(f"type {st.name} struct {{")
        for f in st.fields:
            go_ty = TYPE_MAP_GO.get(f.type_name, "int64")
            lines.append(f"\t{f.name.title()} {go_ty}")
        lines.append("}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_bindings(source: str, lang: str, module_name: str = "module") -> str:
    """Generate FFI bindings for the given language."""
    spec = extract_binding_spec(source, module_name)
    if lang == "python":
        return generate_python(spec)
    elif lang in ("ts", "typescript"):
        return generate_typescript(spec)
    elif lang == "go":
        return generate_go(spec)
    else:
        raise ValueError(f"Unsupported language: {lang}. Use: python, ts, go")
