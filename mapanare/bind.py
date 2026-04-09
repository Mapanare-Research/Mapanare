"""Auto-generated FFI binding generator for Mapanare.

Reads .mn function signatures and generates language-specific bindings:
- Python: ctypes wrapper module
- TypeScript: .d.ts type declarations + WASM loader
- Go: cgo binding file
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mapanare.ast_nodes import (
    Definition,
    EnumDef,
    FnDef,
    NamedType,
    Param,
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
                BindParam(name=p.name, type_name=_type_name(p.type_annotation))
                for p in defn.params
            ]
            ret = _type_name(defn.return_type)
            spec.functions.append(BindFunction(name=defn.name, params=params, return_type=ret))

        elif isinstance(defn, StructDef):
            if defn.name.startswith("_"):
                continue
            fields = [
                BindField(name=f.name, type_name=_type_name(f.type_annotation))
                for f in defn.fields
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


def generate_python(spec: BindingSpec) -> str:
    """Generate Python ctypes binding module."""
    lines = [
        f'"""Auto-generated Python bindings for {spec.module_name}."""',
        "",
        "from __future__ import annotations",
        "",
        "import ctypes",
        "import os",
        "",
        f'_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "lib{spec.module_name}.so"))',
        "",
    ]

    for fn in spec.functions:
        py_params = ", ".join(f"{p.name}: {TYPE_MAP_PYTHON.get(p.type_name, 'int')}" for p in fn.params)
        py_ret = TYPE_MAP_PYTHON.get(fn.return_type, "int")
        lines.append(f"def {fn.name}({py_params}) -> {py_ret}:")
        if fn.params:
            args = ", ".join(p.name for p in fn.params)
            lines.append(f"    return _lib.{fn.name}({args})")
        else:
            lines.append(f"    return _lib.{fn.name}()")
        lines.append("")

    for st in spec.structs:
        lines.append(f"class {st.name}(ctypes.Structure):")
        lines.append("    _fields_ = [")
        for f in st.fields:
            ctype = {"Int": "ctypes.c_int64", "Float": "ctypes.c_double", "Bool": "ctypes.c_bool"}.get(f.type_name, "ctypes.c_void_p")
            lines.append(f'        ("{f.name}", {ctype}),')
        lines.append("    ]")
        lines.append("")

    for en in spec.enums:
        for i, v in enumerate(en.variants):
            lines.append(f"{en.name}_{v} = {i}")
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
        '// #cgo LDFLAGS: -L. -l' + spec.module_name,
        '// #include <stdint.h>',
        'import "C"',
        "",
    ]

    for fn in spec.functions:
        go_params = ", ".join(f"{p.name} {TYPE_MAP_GO.get(p.type_name, 'int64')}" for p in fn.params)
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
