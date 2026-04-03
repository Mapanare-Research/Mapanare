"""emit_c.py — MIR to C emitter for Mapanare (v3.0.0).

Emits portable C99 from the MIR (Mid-level IR).  This backend eliminates
the PHI nodes, SSA renaming, and block-terminator discipline that plague
the LLVM IR emitter.  A ``break`` in C is just ``break``.  An ``if/else``
is just ``if/else``.

Generated code links against the C runtime (``mapanare_core.h``,
``mapanare_runtime.h``) which provides strings, lists, maps, agents,
signals, streams, and memory management.

Usage::

    from mapanare.emit_c import CEmitter
    emitter = CEmitter()
    c_source = emitter.emit(mir_module)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Cast,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    EnvLoad,
    ExternCall,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    SignalComputed,
    SignalGet,
    SignalInit,
    SignalSet,
    SignalSubscribe,
    StreamInit,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
)
from mapanare.types import TypeKind

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_C_RESERVED = frozenset(
    {
        "auto",
        "break",
        "case",
        "char",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extern",
        "float",
        "for",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "register",
        "restrict",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "unsigned",
        "void",
        "volatile",
        "while",
        "_Bool",
        "_Complex",
        "_Imaginary",
        "main",
    }
)

_BINOP_C: dict[BinOpKind, str] = {
    BinOpKind.ADD: "+",
    BinOpKind.SUB: "-",
    BinOpKind.MUL: "*",
    BinOpKind.DIV: "/",
    BinOpKind.MOD: "%",
    BinOpKind.EQ: "==",
    BinOpKind.NE: "!=",
    BinOpKind.LT: "<",
    BinOpKind.GT: ">",
    BinOpKind.LE: "<=",
    BinOpKind.GE: ">=",
    BinOpKind.AND: "&&",
    BinOpKind.OR: "||",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_name(name: str) -> str:
    """Sanitize a MIR value/block name for C."""
    n = name.lstrip("%")
    if not n:
        return "__v"
    # Replace non-identifier chars
    n = re.sub(r"[^A-Za-z0-9_]", "_", n)
    if n[0].isdigit():
        n = "_" + n
    if n in _C_RESERVED:
        n = "mn_" + n
    return n


def _block_label(label: str) -> str:
    """Convert MIR block label to a valid C label."""
    return "bb_" + _safe_name(label)


def _escape_c_string(s: str) -> str:
    """Escape a string for a C string literal."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
        .replace("\0", "\\0")
    )


# ---------------------------------------------------------------------------
# PhiInfo — collected phi metadata for a function
# ---------------------------------------------------------------------------


@dataclass
class _PhiInfo:
    """Collected phi metadata for a single function.

    PHI elimination strategy: for each Phi node we declare a C variable at
    function scope.  In each predecessor block, *before* the terminator, we
    insert an assignment ``phi_var = incoming_value;``.  At the phi site the
    variable already holds the correct value.
    """

    # phi_dest_name → C type string
    declarations: dict[str, str] = field(default_factory=dict)
    # predecessor_block_label → list of (phi_dest_name, incoming_value_name)
    stores: dict[str, list[tuple[str, str]]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# CEmitter
# ---------------------------------------------------------------------------


class CEmitter:
    """Emit C99 source from a MIR module."""

    def __init__(self, debug: bool = False) -> None:
        self._lines: list[str] = []
        self._indent: int = 0
        self._debug = debug

        # Type registries (populated during emit)
        self._structs: dict[str, list[tuple[str, MIRType]]] = {}
        self._enums: dict[str, list[tuple[str, list[MIRType]]]] = {}

        # String constant pool: text → (global_name, length)
        self._string_pool: dict[str, str] = {}
        self._str_counter: int = 0

        # Registered function names (for forward declarations)
        self._fn_names: set[str] = set()
        self._fn_map: dict[str, MIRFunction] = {}

        # Per-function state (reset each function)
        self._cur_fn: MIRFunction | None = None
        self._local_types: dict[str, str] = {}  # var_name → C type
        self._phi_info: _PhiInfo = _PhiInfo()
        self._declared_locals: set[str] = set()

        # Track which types need Option/Result wrappers
        self._option_types: set[str] = set()  # set of inner C type strings
        self._result_types: set[str] = set()  # set of (ok_type, err_type) keys

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _w(self, line: str = "") -> None:
        if line:
            self._lines.append("    " * self._indent + line)
        else:
            self._lines.append("")

    def _indent_inc(self) -> None:
        self._indent += 1

    def _indent_dec(self) -> None:
        self._indent = max(0, self._indent - 1)

    # ------------------------------------------------------------------
    # Type mapping: MIR type → C type string
    # ------------------------------------------------------------------

    def _c_type(self, ty: MIRType) -> str:
        """Map a MIR type to its C representation."""
        kind = ty.type_info.kind
        name = ty.type_info.name

        if kind == TypeKind.INT:
            return "int64_t"
        if kind == TypeKind.FLOAT:
            return "double"
        if kind == TypeKind.BOOL:
            return "int64_t"
        if kind == TypeKind.STRING:
            return "MnString"
        if kind == TypeKind.VOID:
            return "void"
        if kind == TypeKind.CHAR:
            return "int64_t"

        if kind == TypeKind.LIST:
            return "MnList"
        if kind == TypeKind.MAP:
            return "MnMap*"

        if kind == TypeKind.STRUCT:
            if name and name in self._structs:
                return name
            if name:
                return name
            return "void*"

        if kind == TypeKind.ENUM:
            if name and name in self._enums:
                return name
            if name:
                return name
            return "void*"

        if kind == TypeKind.OPTION:
            inner = "int64_t"
            if ty.type_info.args:
                inner_ty = MIRType(type_info=ty.type_info.args[0])
                inner = self._c_type(inner_ty)
            opt_name = f"MnOption_{_safe_name(inner)}"
            self._option_types.add(inner)
            return opt_name

        if kind == TypeKind.RESULT:
            ok_t = "int64_t"
            err_t = "MnString"
            if ty.type_info.args and len(ty.type_info.args) >= 1:
                ok_t = self._c_type(MIRType(type_info=ty.type_info.args[0]))
            if ty.type_info.args and len(ty.type_info.args) >= 2:
                err_t = self._c_type(MIRType(type_info=ty.type_info.args[1]))
            # Use full C type names directly — store the (ok, err) pair
            res_key = f"{ok_t}___{err_t}"
            self._result_types.add(res_key)
            safe_key = _safe_name(ok_t) + "_" + _safe_name(err_t)
            return f"MnResult_{safe_key}"

        if kind == TypeKind.SIGNAL:
            return "MnSignal*"
        if kind == TypeKind.STREAM:
            return "MnStream*"
        if kind == TypeKind.AGENT:
            return "mapanare_agent_t*"
        if kind == TypeKind.TENSOR:
            return "mapanare_tensor_t*"

        if kind == TypeKind.FN:
            return "MnClosure"

        if kind == TypeKind.RANGE:
            return "void*"

        # UNKNOWN or fallback
        if name and name in self._structs:
            return name
        if name and name in self._enums:
            return name
        return "int64_t"

    def _c_type_default(self, ty: MIRType) -> str:
        """Default zero-initializer for a C type."""
        c = self._c_type(ty)
        if c in ("int64_t", "double"):
            return "0"
        if c == "MnString":
            return "(MnString){NULL, 0}"
        if c == "MnList":
            return "(MnList){NULL, 0, 0, 0}"
        if c.endswith("*"):
            return "NULL"
        if c == "MnClosure":
            return "(MnClosure){NULL, NULL}"
        # Struct/enum — zero-init
        return f"({c}){{0}}"

    # ------------------------------------------------------------------
    # String constant pool
    # ------------------------------------------------------------------

    def _intern_string(self, text: str) -> str:
        """Register a string constant and return its C global name."""
        if text in self._string_pool:
            return self._string_pool[text]
        name = f"__mn_str_{self._str_counter}"
        self._str_counter += 1
        self._string_pool[text] = name
        return name

    # ------------------------------------------------------------------
    # Value name resolution
    # ------------------------------------------------------------------

    def _val(self, v: Value) -> str:
        """Get the C variable name for a MIR Value."""
        return _safe_name(v.name)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def emit(self, module: MIRModule) -> str:
        """Emit a complete C source file from a MIR module."""
        self._structs = dict(module.structs)
        self._enums = dict(module.enums)
        for fn in module.functions:
            self._fn_names.add(fn.name)
            self._fn_map[fn.name] = fn

        # Pre-scan all functions for string constants and Option/Result types
        self._prescan_module(module)

        # Emit sections
        self._emit_preamble()
        self._w()
        self._emit_closure_type()
        self._emit_range_type()
        # Forward declarations (all types must be declared before any definition)
        self._emit_struct_forward_decls(module)
        self._emit_enum_forward_decls(module)
        self._emit_option_result_forward_decls()
        self._w()
        # Full definitions in dependency order (structs, enums, Option, Result interleaved)
        self._emitted_types: set[str] = set()
        type_order = self._topo_sort_types(module)
        for tname in type_order:
            if tname in module.structs:
                self._emit_one_struct(tname, module.structs[tname])
            elif tname in module.enums:
                self._emit_one_enum(tname, module.enums[tname])
            elif tname.startswith("MnOption_"):
                self._emit_one_option(tname)
            elif tname.startswith("MnResult_"):
                self._emit_one_result(tname)
        self._w()
        self._emit_string_constants()
        self._w()
        self._emit_function_forward_decls(module)
        self._w()
        self._emit_extern_decls(module)
        self._w()

        # Emit function bodies
        for fn in module.functions:
            self._emit_function(fn)
            self._w()

        # Emit main() wrapper
        self._emit_main_wrapper(module)

        return "\n".join(self._lines) + "\n"

    # ------------------------------------------------------------------
    # Pre-scan: collect string constants and type usage across all fns
    # ------------------------------------------------------------------

    def _prescan_module(self, module: MIRModule) -> None:
        # Scan struct fields for Option/Result types
        for _name, fields in module.structs.items():
            for _fname, ftype in fields:
                self._c_type(ftype)  # Triggers Option/Result registration
        # Scan function signatures
        for fn in module.functions:
            self._c_type(fn.return_type)
            for p in fn.params:
                self._c_type(p.ty)
        # Scan instructions
        for fn in module.functions:
            for block in fn.blocks:
                for inst in block.instructions:
                    self._prescan_inst(inst)

    def _prescan_inst(self, inst: Instruction) -> None:
        if isinstance(inst, Const):
            if inst.ty.type_info.kind == TypeKind.STRING and isinstance(inst.value, str):
                self._intern_string(inst.value)
        elif isinstance(inst, InterpConcat):
            pass  # strings created at runtime
        # Scan types for Option/Result
        for v in self._inst_values(inst):
            if v.ty.type_info.kind == TypeKind.OPTION:
                self._c_type(v.ty)
            elif v.ty.type_info.kind == TypeKind.RESULT:
                self._c_type(v.ty)

    @staticmethod
    def _inst_values(inst: Instruction) -> list[Value]:
        """Extract all Value fields from an instruction."""
        vals: list[Value] = []
        for attr in ("dest", "src", "val"):
            v = getattr(inst, attr, None)
            if isinstance(v, Value):
                vals.append(v)
        return vals

    # ------------------------------------------------------------------
    # Preamble
    # ------------------------------------------------------------------

    def _emit_preamble(self) -> None:
        self._w("/* Generated by Mapanare v3.0.0 C emitter — do not edit. */")
        self._w("#include <stdio.h>")
        self._w("#include <stdlib.h>")
        self._w("#include <string.h>")
        self._w("#include <stdint.h>")
        self._w("#include <math.h>")
        self._w('#include "mapanare_core.h"')
        self._w('#include "mapanare_runtime.h"')

    # ------------------------------------------------------------------
    # Closure, Range, Option/Result helper types
    # ------------------------------------------------------------------

    def _emit_closure_type(self) -> None:
        self._w("/* Closure: function pointer + captured environment */")
        self._w("typedef struct { void *fn; void *env; } MnClosure;")
        self._w()

    def _emit_range_type(self) -> None:
        self._w("typedef struct { int64_t start; int64_t end; int64_t step; } MnRange;")
        self._w()

    def _emit_option_result_types(self) -> None:
        for inner in sorted(self._option_types):
            safe = _safe_name(inner)
            self._w(f"struct MnOption_{safe}_s {{ int64_t has_value; {inner} value; }};")
        if self._option_types:
            self._w()

        for key in sorted(self._result_types):
            parts = key.split("___", 1)
            ok_t = parts[0] if parts else "int64_t"
            err_t = parts[1] if len(parts) > 1 else "MnString"
            safe_key = _safe_name(ok_t) + "_" + _safe_name(err_t)
            body = f"int64_t is_ok; union {{ {ok_t} ok; {err_t} err; }} as;"
            self._w(f"struct MnResult_{safe_key}_s {{ {body} }};")
        if self._result_types:
            self._w()

    # ------------------------------------------------------------------
    # Struct definitions
    # ------------------------------------------------------------------

    def _emit_struct_forward_decls(self, module: MIRModule) -> None:
        for name in module.structs:
            self._w(f"typedef struct {name} {name};")

    def _emit_enum_forward_decls(self, module: MIRModule) -> None:
        for name in module.enums:
            self._w(f"typedef struct {name}_s {name};")

    def _emit_option_result_forward_decls(self) -> None:
        for inner in sorted(self._option_types):
            safe = _safe_name(inner)
            self._w(f"typedef struct MnOption_{safe}_s MnOption_{safe};")
        for key in sorted(self._result_types):
            parts = key.split("___", 1)
            ok_t = parts[0] if parts else "int64_t"
            err_t = parts[1] if len(parts) > 1 else "MnString"
            safe_key = _safe_name(ok_t) + "_" + _safe_name(err_t)
            self._w(f"typedef struct MnResult_{safe_key}_s MnResult_{safe_key};")

    def _topo_sort_types(self, module: MIRModule) -> list[str]:
        """Topologically sort struct/enum names by dependency.

        A type X depends on Y if X has a by-value field of type Y.
        Self-referential fields (X contains X) are handled as pointers.
        """
        all_types = set(module.structs.keys()) | set(module.enums.keys())
        # Also include Option/Result wrapper types
        for inner in self._option_types:
            all_types.add(f"MnOption_{_safe_name(inner)}")
        for key in self._result_types:
            parts = key.split("___", 1)
            ok_t = parts[0] if parts else "int64_t"
            err_t = parts[1] if len(parts) > 1 else "MnString"
            safe_key = _safe_name(ok_t) + "_" + _safe_name(err_t)
            all_types.add(f"MnResult_{safe_key}")

        # Build dependency graph
        deps: dict[str, set[str]] = {t: set() for t in all_types}
        for name, fields in module.structs.items():
            for _, ftype in fields:
                ct = self._c_type(ftype)
                if ct != name and ct in all_types:
                    deps[name].add(ct)
                # Also check Option/Result wrapper dependencies
                if ct.startswith("MnOption_") and ct in all_types:
                    deps[name].add(ct)
                elif ct.startswith("MnResult_") and ct in all_types:
                    deps[name].add(ct)
        # Option depends on its inner type (unless circular)
        for inner in self._option_types:
            opt_name = f"MnOption_{_safe_name(inner)}"
            if inner in all_types and opt_name in all_types:
                # Check for circular: does inner contain this Option?
                is_circular = False
                if inner in module.structs:
                    for _, ftype in module.structs[inner]:
                        if self._c_type(ftype) == opt_name:
                            is_circular = True
                            break
                if not is_circular:
                    deps[opt_name].add(inner)
        for name, variants in module.enums.items():
            for _, payload_types in variants:
                for pt in payload_types:
                    ct = self._c_type(pt)
                    if ct != name and ct in all_types:
                        deps[name].add(ct)

        # Kahn's algorithm — proper topological sort
        in_degree: dict[str, int] = {t: 0 for t in all_types}
        # Build reverse adjacency: for each dep, track who depends on it
        dependents: dict[str, list[str]] = {t: [] for t in all_types}
        for t, d in deps.items():
            # Only count deps that are in our type set
            real_deps = d & all_types
            in_degree[t] = len(real_deps)
            for dep in real_deps:
                dependents[dep].append(t)

        queue = sorted(t for t in all_types if in_degree[t] == 0)
        order: list[str] = []
        while queue:
            t = queue.pop(0)
            order.append(t)
            for dependent in dependents.get(t, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Add any remaining (cyclic) types at the end
        for t in sorted(all_types):
            if t not in order:
                order.append(t)
        return order

    def _emit_one_struct(self, name: str, fields: list[tuple[str, MIRType]]) -> None:
        self._w(f"struct {name} {{")
        self._indent_inc()
        for fname, ftype in fields:
            ct = self._c_type(ftype)
            if ct == name:
                ct = f"{name}*"  # Self-referential → pointer
            self._w(f"{ct} {_safe_name(fname)};")
        self._indent_dec()
        self._w("};")
        self._w()
        self._emitted_types.add(name)

    def _emit_struct_defs(self, module: MIRModule) -> None:
        if not module.structs:
            return
        self._w()
        for name, fields in module.structs.items():
            self._emit_one_struct(name, fields)

    # ------------------------------------------------------------------
    # Enum definitions (tagged unions)
    # ------------------------------------------------------------------

    def _emit_one_enum(self, name: str, variants: list[tuple[str, list[MIRType]]]) -> None:
        # Detect recursive types in payloads
        all_types = set(self._structs.keys()) | set(self._enums.keys())
        self._w(f"struct {name}_s {{")
        self._indent_inc()
        self._w("int64_t tag;")
        has_payload = any(payload_types for _, payload_types in variants)
        if has_payload:
            self._w("union {")
            self._indent_inc()
            for vname, payload_types in variants:
                if payload_types:
                    self._w("struct {")
                    self._indent_inc()
                    for i, pt in enumerate(payload_types):
                        ct = self._c_type(pt)
                        # Self-referential: must be pointer
                        if ct == name:
                            ct = f"{ct}*"
                        self._w(f"{ct} _{i};")
                    self._indent_dec()
                    self._w(f"}} {_safe_name(vname)};")
                else:
                    self._w(f"char {_safe_name(vname)}_empty;  /* no payload */")
            self._indent_dec()
            self._w("} as;")
        self._indent_dec()
        self._w("};")
        self._w()
        # Tag constants
        for i, (vname, _) in enumerate(variants):
            self._w(f"#define {name}_{_safe_name(vname)}_TAG {i}")
        self._emitted_types.add(name)

    def _emit_one_option(self, tname: str) -> None:
        """Emit a single Option type definition (struct already forward-declared)."""
        for inner in self._option_types:
            safe = _safe_name(inner)
            if tname == f"MnOption_{safe}":
                # If the inner type contains this Option (circular), use pointer
                is_circular = False
                if inner in self._structs:
                    for _, ftype in self._structs[inner]:
                        if self._c_type(ftype) == tname:
                            is_circular = True
                            break
                if is_circular:
                    self._w(f"struct MnOption_{safe}_s {{ int64_t has_value; {inner} *value; }};")
                else:
                    self._w(f"struct MnOption_{safe}_s {{ int64_t has_value; {inner} value; }};")
                self._w()
                self._emitted_types.add(tname)
                return

    def _emit_one_result(self, tname: str) -> None:
        """Emit a single Result type definition."""
        for key in self._result_types:
            parts = key.split("___", 1)
            ok_t = parts[0] if parts else "int64_t"
            err_t = parts[1] if len(parts) > 1 else "MnString"
            safe_key = _safe_name(ok_t) + "_" + _safe_name(err_t)
            if tname == f"MnResult_{safe_key}":
                body = f"int64_t is_ok; union {{ {ok_t} ok; {err_t} err; }} as;"
                self._w(f"struct MnResult_{safe_key}_s {{ {body} }};")
                self._w()
                return

    # ------------------------------------------------------------------
    # String constants
    # ------------------------------------------------------------------

    def _emit_string_constants(self) -> None:
        if not self._string_pool:
            return
        self._w("/* String constants */")
        for text, gname in self._string_pool.items():
            escaped = _escape_c_string(text)
            length = len(text.encode("utf-8"))
            self._w(f'static MnString {gname} = {{(const char*)"{escaped}", {length}}};')

    # ------------------------------------------------------------------
    # Forward declarations
    # ------------------------------------------------------------------

    def _emit_function_forward_decls(self, module: MIRModule) -> None:
        self._w("/* Function forward declarations */")
        for fn in module.functions:
            sig = self._fn_signature(fn)
            self._w(f"{sig};")

    def _emit_extern_decls(self, module: MIRModule) -> None:
        if not module.extern_fns:
            return
        self._w("/* Extern declarations */")
        for abi, mod, name, param_types, ret_type in module.extern_fns:
            ret_c = self._c_type(ret_type)
            params = ", ".join(self._c_type(pt) for pt in param_types) or "void"
            self._w(f"extern {ret_c} {name}({params});")

    # ------------------------------------------------------------------
    # Function signature
    # ------------------------------------------------------------------

    def _fn_signature(self, fn: MIRFunction) -> str:
        ret = self._c_type(fn.return_type)
        name = self._fn_c_name(fn.name)
        if fn.params:
            params = ", ".join(f"{self._c_type(p.ty)} {_safe_name(p.name)}" for p in fn.params)
        else:
            params = "void"
        return f"{ret} {name}({params})"

    def _fn_c_name(self, name: str) -> str:
        """Map a MIR function name to a C function name."""
        if name == "main":
            return "mn_main"
        return _safe_name(name)

    # ------------------------------------------------------------------
    # Function body emission
    # ------------------------------------------------------------------

    def _propagate_types(self, fn: MIRFunction) -> dict[str, str]:
        """Pre-pass: infer C types for all values by propagating from known sources.

        Resolves UNKNOWN MIR types by looking at:
        - Enum variant constructors (always known type)
        - Function return types (from _fn_map)
        - Copy instructions (propagate src type)
        - WrapSome/WrapNone (infer Option type from function return)
        """
        types: dict[str, str] = {}
        fn_ret = self._c_type(fn.return_type)

        for block in fn.blocks:
            for inst in block.instructions:
                dest = getattr(inst, "dest", None)
                if dest is None or not isinstance(dest, Value):
                    continue
                vname = self._val(dest)

                # Resolve from MIR type
                ct = self._c_type(dest.ty)

                # Fix generic MnOption_int64_t by inferring from wrapped value or fn return
                if ct == "MnOption_int64_t":
                    if isinstance(inst, WrapSome):
                        # Try to infer from the wrapped value's type
                        wrapped = self._val(inst.val)
                        wrapped_ct = types.get(wrapped, self._c_type(inst.val.ty))
                        if wrapped_ct != "int64_t":
                            opt_ct = f"MnOption_{_safe_name(wrapped_ct)}"
                            types[vname] = opt_ct
                            continue
                    if fn_ret.startswith("MnOption_") and fn_ret != ct:
                        if isinstance(inst, (WrapSome, WrapNone)):
                            types[vname] = fn_ret
                            continue

                if ct != "int64_t" or dest.ty.type_info.kind != TypeKind.UNKNOWN:
                    types[vname] = ct
                    continue

                # Enum variant constructor
                if isinstance(inst, Call):
                    for enum_name in self._enums:
                        for vn, _ in self._enums[enum_name]:
                            if inst.fn_name == f"{enum_name}_{vn}":
                                types[vname] = enum_name
                                break
                    if vname in types:
                        continue
                    # Known function return type
                    if inst.fn_name in self._fn_map:
                        ret_ty = self._fn_map[inst.fn_name].return_type
                        ret_ct = self._c_type(ret_ty)
                        if ret_ct != "int64_t" or ret_ty.type_info.kind != TypeKind.UNKNOWN:
                            types[vname] = ret_ct
                            continue

                # Copy: inherit source type
                if isinstance(inst, Copy):
                    src_name = self._val(inst.src)
                    if src_name in types:
                        types[vname] = types[src_name]
                        continue

                # WrapSome/WrapNone: use function return type when MIR type is generic
                if isinstance(inst, (WrapSome, WrapNone)):
                    if fn_ret.startswith("MnOption_"):
                        types[vname] = fn_ret
                        continue

                # Already resolved but might be wrong Option variant
                if ct.startswith("MnOption_int64_t") and fn_ret.startswith("MnOption_"):
                    types[vname] = fn_ret
                    continue

                # EnumPayload: result type from the enum definition
                if isinstance(inst, EnumPayload):
                    pass  # Already handled by MIR type

                # Default
                types[vname] = ct

        return types

    def _emit_function(self, fn: MIRFunction) -> None:
        self._cur_fn = fn
        self._local_types = {}
        self._declared_locals = set()

        # Pre-propagate types
        self._propagated_types = self._propagate_types(fn)

        # Collect PHI info
        self._phi_info = self._collect_phis(fn)

        # Signature
        sig = self._fn_signature(fn)
        self._w(f"{sig} {{")
        self._indent_inc()

        # Register param types
        for p in fn.params:
            pname = _safe_name(p.name)
            self._local_types[pname] = self._c_type(p.ty)
            self._declared_locals.add(pname)

        # Declare phi variables at function scope
        for phi_dest, phi_ctype in self._phi_info.declarations.items():
            if phi_ctype == "void":
                phi_ctype = "int64_t"  # Can't declare void variables
            self._w(f"{phi_ctype} {phi_dest} = {self._zero_init(phi_ctype)};")
            self._declared_locals.add(phi_dest)
            self._local_types[phi_dest] = phi_ctype

        # Pre-declare all local variables used in blocks
        self._emit_local_declarations(fn)

        self._w()

        # Emit blocks
        for i, block in enumerate(fn.blocks):
            self._emit_block(block, is_first=(i == 0))

        self._indent_dec()
        self._w("}")

        self._cur_fn = None

    def _emit_local_declarations(self, fn: MIRFunction) -> None:
        """Pre-declare all local variables at function scope (C89/C99 style)."""
        for block in fn.blocks:
            for inst in block.instructions:
                if isinstance(inst, Phi):
                    continue  # Already declared
                dest = getattr(inst, "dest", None)
                if dest is not None and isinstance(dest, Value):
                    vname = self._val(dest)
                    if vname not in self._declared_locals:
                        ctype = self._infer_decl_type(inst, dest)
                        if ctype == "void":
                            ctype = "int64_t"  # Fallback for void dests
                        self._w(f"{ctype} {vname} = {self._zero_init(ctype)};")
                        self._declared_locals.add(vname)
                        self._local_types[vname] = ctype
                        self._local_types[vname] = ctype

    def _infer_decl_type(self, inst: Instruction, dest: Value) -> str:
        """Infer the correct C type for a variable declaration.

        Uses propagated types only for struct/Option/Result types (not enums,
        which are often used interchangeably with int64_t in MIR).
        """
        vname = self._val(dest)

        # EnumTag always returns an integer tag
        if isinstance(inst, EnumTag):
            return "int64_t"

        # Use propagated type for structs, Options, Results (not enums)
        if hasattr(self, "_propagated_types") and vname in self._propagated_types:
            pt = self._propagated_types[vname]
            if (
                pt in self._structs
                or pt.startswith("MnOption_")
                or pt.startswith("MnResult_")
                or pt == "MnString"
                or pt == "MnList"
            ):
                return pt

        # Call to enum variant constructor — use enum type
        if isinstance(inst, Call):
            for enum_name in self._enums:
                for vn, _ in self._enums[enum_name]:
                    if inst.fn_name == f"{enum_name}_{vn}":
                        return enum_name

        return self._c_type(dest.ty)

    def _zero_init(self, ctype: str) -> str:
        """Zero-initializer expression for a C type."""
        if ctype in ("int64_t", "double"):
            return "0"
        if ctype == "void":
            return "0"  # Can't zero-init void; use 0 as placeholder
        if ctype == "MnString":
            return "(MnString){NULL, 0}"
        if ctype == "MnList":
            return "(MnList){NULL, 0, 0, 0}"
        if ctype == "MnClosure":
            return "(MnClosure){NULL, NULL}"
        if ctype == "MnRange":
            return "(MnRange){0, 0, 1}"
        if ctype.endswith("*"):
            return "NULL"
        return f"({ctype}){{0}}"

    # ------------------------------------------------------------------
    # PHI collection
    # ------------------------------------------------------------------

    def _collect_phis(self, fn: MIRFunction) -> _PhiInfo:
        info = _PhiInfo()
        prop = getattr(self, "_propagated_types", {})
        for block in fn.blocks:
            for inst in block.instructions:
                if not isinstance(inst, Phi):
                    continue
                dest_name = self._val(inst.dest)
                ctype = self._c_type(inst.dest.ty)
                if ctype == "void":
                    continue
                # Use propagated type for phi dest if available
                if ctype == "int64_t" and dest_name in prop:
                    ctype = prop[dest_name]
                # Also try to infer from non-void incoming values
                if ctype == "int64_t":
                    for _, incoming_val in inst.incoming:
                        iv_name = self._val(incoming_val)
                        if iv_name not in ("mn_void", "mn_return") and iv_name in prop:
                            iv_ct = prop[iv_name]
                            if iv_ct != "int64_t":
                                ctype = iv_ct
                                break
                info.declarations[dest_name] = ctype
                for pred_label, incoming_val in inst.incoming:
                    stores = info.stores.setdefault(pred_label, [])
                    stores.append((dest_name, self._val(incoming_val)))
        return info

    # ------------------------------------------------------------------
    # Block emission
    # ------------------------------------------------------------------

    def _emit_block(self, block: BasicBlock, is_first: bool = False) -> None:
        label = _block_label(block.label)

        # Emit label (skip for first block if it would just be the entry)
        if not is_first:
            # Labels need at least a trailing semicolon in C if no statement follows
            self._indent_dec()
            self._w(f"{label}:;")
            self._indent_inc()
        else:
            # Still emit label for first block in case it's a goto target
            self._indent_dec()
            self._w(f"{label}:;")
            self._indent_inc()

        for inst in block.instructions:
            if isinstance(inst, Phi):
                continue  # Handled by predecessor stores
            self._emit_instruction(inst, block.label)

    # ------------------------------------------------------------------
    # Instruction dispatch
    # ------------------------------------------------------------------

    def _emit_instruction(self, inst: Instruction, block_label: str) -> None:  # noqa: C901
        if isinstance(inst, Const):
            self._emit_const(inst)
        elif isinstance(inst, Copy):
            self._emit_copy(inst)
        elif isinstance(inst, Cast):
            self._emit_cast(inst)
        elif isinstance(inst, BinOp):
            self._emit_binop(inst)
        elif isinstance(inst, UnaryOp):
            self._emit_unaryop(inst)
        elif isinstance(inst, StructInit):
            self._emit_struct_init(inst)
        elif isinstance(inst, FieldGet):
            self._emit_field_get(inst)
        elif isinstance(inst, FieldSet):
            self._emit_field_set(inst)
        elif isinstance(inst, ListInit):
            self._emit_list_init(inst)
        elif isinstance(inst, ListPush):
            self._emit_list_push(inst)
        elif isinstance(inst, IndexGet):
            self._emit_index_get(inst)
        elif isinstance(inst, IndexSet):
            self._emit_index_set(inst)
        elif isinstance(inst, MapInit):
            self._emit_map_init(inst)
        elif isinstance(inst, EnumInit):
            self._emit_enum_init(inst)
        elif isinstance(inst, EnumTag):
            self._emit_enum_tag(inst)
        elif isinstance(inst, EnumPayload):
            self._emit_enum_payload(inst)
        elif isinstance(inst, WrapSome):
            self._emit_wrap_some(inst)
        elif isinstance(inst, WrapNone):
            self._emit_wrap_none(inst)
        elif isinstance(inst, WrapOk):
            self._emit_wrap_ok(inst)
        elif isinstance(inst, WrapErr):
            self._emit_wrap_err(inst)
        elif isinstance(inst, Unwrap):
            self._emit_unwrap(inst)
        elif isinstance(inst, Call):
            self._emit_call(inst)
        elif isinstance(inst, ExternCall):
            self._emit_extern_call(inst)
        elif isinstance(inst, Return):
            self._emit_return(inst, block_label)
        elif isinstance(inst, Jump):
            self._emit_jump(inst, block_label)
        elif isinstance(inst, Branch):
            self._emit_branch(inst, block_label)
        elif isinstance(inst, Switch):
            self._emit_switch(inst, block_label)
        elif isinstance(inst, ClosureCreate):
            self._emit_closure_create(inst)
        elif isinstance(inst, ClosureCall):
            self._emit_closure_call(inst)
        elif isinstance(inst, EnvLoad):
            self._emit_env_load(inst)
        elif isinstance(inst, InterpConcat):
            self._emit_interp_concat(inst)
        elif isinstance(inst, Assert):
            self._emit_assert(inst)
        elif isinstance(inst, AgentSpawn):
            self._emit_agent_spawn(inst)
        elif isinstance(inst, AgentSend):
            self._emit_agent_send(inst)
        elif isinstance(inst, AgentSync):
            self._emit_agent_sync(inst)
        elif isinstance(inst, SignalInit):
            self._emit_signal_init(inst)
        elif isinstance(inst, SignalGet):
            self._emit_signal_get(inst)
        elif isinstance(inst, SignalSet):
            self._emit_signal_set(inst)
        elif isinstance(inst, SignalComputed):
            self._emit_signal_computed(inst)
        elif isinstance(inst, SignalSubscribe):
            self._emit_signal_subscribe(inst)
        elif isinstance(inst, StreamInit):
            self._emit_stream_init(inst)
        elif isinstance(inst, StreamOp):
            self._emit_stream_op(inst)
        elif isinstance(inst, Phi):
            pass  # Handled by phi stores
        else:
            self._w(f"/* unhandled instruction: {type(inst).__name__} */")

    # ------------------------------------------------------------------
    # PHI stores — inserted before terminators
    # ------------------------------------------------------------------

    def _emit_phi_stores(self, block_label: str) -> None:
        """Emit phi variable assignments before a terminator."""
        stores = self._phi_info.stores.get(block_label, [])
        for phi_dest, src_name in stores:
            # Skip void phi variables (not declared)
            if phi_dest not in self._declared_locals:
                continue
            # Skip void/undefined phi values — use memset to zero
            if src_name in ("mn_void", "mn_return"):
                ctype = self._local_types.get(phi_dest, "int64_t")
                if ctype == "void":
                    continue  # Can't assign to void
                self._w(f"memset(&{phi_dest}, 0, sizeof({phi_dest}));")
            else:
                # Use memcpy for potential type mismatches in phi stores
                dest_ct = self._local_types.get(phi_dest, "int64_t")
                src_ct = self._local_types.get(src_name, "int64_t")
                if dest_ct != src_ct and dest_ct not in ("int64_t", "double"):
                    self._w(f"memcpy(&{phi_dest}, &{src_name}, sizeof({phi_dest}));")
                else:
                    self._w(f"{phi_dest} = {src_name};")

    # ------------------------------------------------------------------
    # Instruction handlers
    # ------------------------------------------------------------------

    def _emit_const(self, inst: Const) -> None:
        dest = self._val(inst.dest)
        kind = inst.ty.type_info.kind

        if kind == TypeKind.INT:
            self._w(f"{dest} = (int64_t){inst.value}LL;")
        elif kind == TypeKind.FLOAT:
            val = inst.value
            if isinstance(val, float):
                self._w(f"{dest} = {val!r};")
            else:
                self._w(f"{dest} = (double){val};")
        elif kind == TypeKind.BOOL:
            val = 1 if inst.value else 0
            self._w(f"{dest} = {val};")
        elif kind == TypeKind.STRING:
            if isinstance(inst.value, str):
                gname = self._intern_string(inst.value)
                self._w(f"{dest} = {gname};")
            else:
                self._w(f"{dest} = (MnString){{NULL, 0}};")
        elif kind == TypeKind.CHAR:
            if isinstance(inst.value, str) and len(inst.value) == 1:
                self._w(f"{dest} = (int64_t){ord(inst.value)};")
            else:
                self._w(f"{dest} = (int64_t){inst.value};")
        elif kind == TypeKind.FN:
            # Function reference as closure with no env
            fn_name = inst.value if isinstance(inst.value, str) else str(inst.value)
            c_name = self._fn_c_name(fn_name)
            self._w(f"{dest} = (MnClosure){{(void*){c_name}, NULL}};")
        else:
            # Null/None/unknown
            if inst.value is None or (isinstance(inst.value, str) and inst.value == "None"):
                ct = self._c_type(inst.ty)
                self._w(f"{dest} = {self._zero_init(ct)};")
            else:
                self._w(f"{dest} = (int64_t){inst.value};")

    def _emit_copy(self, inst: Copy) -> None:
        dest_name = self._val(inst.dest)
        src_name = self._val(inst.src)
        dest_ct = self._local_types.get(dest_name, "int64_t")
        src_ct = self._local_types.get(src_name, "int64_t")
        # Type mismatch: use memcpy for struct-to-struct copies
        if dest_ct != src_ct and dest_ct not in ("int64_t", "double", "void"):
            self._w(f"memcpy(&{dest_name}, &{src_name}, sizeof({dest_name}));")
        else:
            self._w(f"{dest_name} = {src_name};")

    def _emit_cast(self, inst: Cast) -> None:
        dest = self._val(inst.dest)
        src = self._val(inst.src)
        target_c = self._c_type(inst.target_type)
        src_kind = inst.src.ty.type_info.kind
        dst_kind = inst.target_type.type_info.kind

        # int → float
        if src_kind == TypeKind.INT and dst_kind == TypeKind.FLOAT:
            self._w(f"{dest} = (double){src};")
        # float → int
        elif src_kind == TypeKind.FLOAT and dst_kind == TypeKind.INT:
            self._w(f"{dest} = (int64_t){src};")
        # int → string
        elif src_kind == TypeKind.INT and dst_kind == TypeKind.STRING:
            self._w(f"{dest} = __mn_str_from_int({src});")
        # float → string
        elif src_kind == TypeKind.FLOAT and dst_kind == TypeKind.STRING:
            self._w(f"{dest} = __mn_str_from_float({src});")
        # bool → string
        elif src_kind == TypeKind.BOOL and dst_kind == TypeKind.STRING:
            self._w(f"{dest} = __mn_str_from_bool({src});")
        # string → int
        elif src_kind == TypeKind.STRING and dst_kind == TypeKind.INT:
            self._w(f"{dest} = __mn_str_to_int({src});")
        # string → float
        elif src_kind == TypeKind.STRING and dst_kind == TypeKind.FLOAT:
            self._w(f"{dest} = __mn_str_to_float({src});")
        else:
            self._w(f"{dest} = ({target_c}){src};")

    def _emit_binop(self, inst: BinOp) -> None:
        dest = self._val(inst.dest)
        lhs = self._val(inst.lhs)
        rhs = self._val(inst.rhs)
        op = _BINOP_C.get(inst.op)

        lhs_kind = inst.lhs.ty.type_info.kind
        rhs_kind = inst.rhs.ty.type_info.kind

        # String concatenation
        if inst.op == BinOpKind.ADD and (
            lhs_kind == TypeKind.STRING or rhs_kind == TypeKind.STRING
        ):
            self._w(f"{dest} = __mn_str_concat({lhs}, {rhs});")
            return

        # String equality
        if inst.op == BinOpKind.EQ and lhs_kind == TypeKind.STRING:
            self._w(f"{dest} = __mn_str_eq({lhs}, {rhs});")
            return
        if inst.op == BinOpKind.NE and lhs_kind == TypeKind.STRING:
            self._w(f"{dest} = !__mn_str_eq({lhs}, {rhs});")
            return

        # String comparison
        if lhs_kind == TypeKind.STRING and inst.op in (
            BinOpKind.LT,
            BinOpKind.GT,
            BinOpKind.LE,
            BinOpKind.GE,
        ):
            cmp_op = _BINOP_C[inst.op]
            self._w(f"{dest} = (__mn_str_cmp({lhs}, {rhs}) {cmp_op} 0);")
            return

        # Float modulo
        if inst.op == BinOpKind.MOD and (lhs_kind == TypeKind.FLOAT or rhs_kind == TypeKind.FLOAT):
            self._w(f"{dest} = fmod({lhs}, {rhs});")
            return

        if op:
            self._w(f"{dest} = {lhs} {op} {rhs};")
        else:
            self._w(f"/* unknown binop {inst.op} */")
            self._w(f"{dest} = 0;")

    def _emit_unaryop(self, inst: UnaryOp) -> None:
        dest = self._val(inst.dest)
        operand = self._val(inst.operand)
        if inst.op == UnaryOpKind.NEG:
            self._w(f"{dest} = -{operand};")
        elif inst.op == UnaryOpKind.NOT:
            self._w(f"{dest} = !{operand};")
        else:
            self._w(f"{dest} = {operand}; /* unknown unaryop */")

    # --- Struct ---

    def _emit_struct_init(self, inst: StructInit) -> None:
        dest = self._val(inst.dest)
        struct_name = inst.struct_type.type_info.name
        fields_str = ", ".join(
            f".{_safe_name(fname)} = {self._val(fval)}" for fname, fval in inst.fields
        )
        self._w(f"{dest} = ({struct_name}){{{fields_str}}};")

    def _emit_field_get(self, inst: FieldGet) -> None:
        dest = self._val(inst.dest)
        obj = self._val(inst.obj)
        fname = _safe_name(inst.field_name)

        # Check if obj is a pointer type
        obj_kind = inst.obj.ty.type_info.kind
        if obj_kind in (TypeKind.SIGNAL,):
            # Signal .value → __mn_signal_get
            if inst.field_name == "value":
                ct = self._c_type(inst.dest.ty)
                self._w(f"{dest} = *({ct}*)__mn_signal_get({obj});")
                return
        # Regular struct field access
        self._w(f"{dest} = {obj}.{fname};")

    def _emit_field_set(self, inst: FieldSet) -> None:
        obj = self._val(inst.obj)
        fname = _safe_name(inst.field_name)
        val = self._val(inst.val)
        self._w(f"{obj}.{fname} = {val};")

    # --- List ---

    def _emit_list_init(self, inst: ListInit) -> None:
        dest = self._val(inst.dest)
        elem_size = self._elem_size(inst.elem_type)
        self._w(f"{dest} = __mn_list_new({elem_size});")
        # Push initial elements
        for elem in inst.elements:
            ev = self._val(elem)
            et = self._c_type(elem.ty)
            self._w(f"{{ {et} __tmp_elem = {ev};")
            self._w(f"  __mn_list_push(&{dest}, &__tmp_elem); }}")

    def _emit_list_push(self, inst: ListPush) -> None:
        dest = self._val(inst.dest)
        list_v = self._val(inst.list_val)
        elem_v = self._val(inst.element)
        # Use propagated type for element (MIR often marks as UNKNOWN)
        elem_type = self._local_types.get(elem_v, self._c_type(inst.element.ty))
        self._w(f"{{ {elem_type} __tmp_push = {elem_v};")
        self._w(f"  __mn_list_push(&{list_v}, &__tmp_push); }}")
        self._w(f"{dest} = {list_v};")

    def _emit_index_get(self, inst: IndexGet) -> None:
        dest = self._val(inst.dest)
        obj = self._val(inst.obj)
        idx = self._val(inst.index)
        obj_kind = inst.obj.ty.type_info.kind

        if obj_kind == TypeKind.LIST:
            ct = self._c_type(inst.dest.ty)
            self._w(f"{dest} = *({ct}*)__mn_list_get(&{obj}, {idx});")
        elif obj_kind == TypeKind.MAP:
            ct = self._c_type(inst.dest.ty)
            self._w(f"{{ void *__map_val = __mn_map_get({obj}, &{idx});")
            self._w(f"  if (__map_val) {dest} = *({ct}*)__map_val; }}")
        elif obj_kind == TypeKind.STRING:
            self._w(f"{dest} = __mn_str_char_at({obj}, {idx});")
        else:
            self._w(f"{dest} = {obj}; /* index_get fallback */")

    def _emit_index_set(self, inst: IndexSet) -> None:
        obj = self._val(inst.obj)
        idx = self._val(inst.index)
        val = self._val(inst.val)
        obj_kind = inst.obj.ty.type_info.kind

        if obj_kind == TypeKind.LIST:
            ct = self._c_type(inst.val.ty)
            self._w(f"{{ {ct} __tmp_set = {val}; __mn_list_set(&{obj}, {idx}, &__tmp_set); }}")
        elif obj_kind == TypeKind.MAP:
            ct = self._c_type(inst.val.ty)
            self._w(f"{{ {ct} __tmp_set = {val}; __mn_map_set({obj}, &{idx}, &__tmp_set); }}")
        else:
            self._w("/* index_set: unsupported obj type */")

    # --- Map ---

    def _emit_map_init(self, inst: MapInit) -> None:
        dest = self._val(inst.dest)
        key_size = self._elem_size(inst.key_type)
        val_size = self._elem_size(inst.val_type)
        key_tag = self._map_key_tag(inst.key_type)
        self._w(f"{dest} = __mn_map_new({key_size}, {val_size}, {key_tag});")
        for kv, vv in inst.pairs:
            kname = self._val(kv)
            vname = self._val(vv)
            kt = self._c_type(kv.ty)
            vt = self._c_type(vv.ty)
            self._w(f"{{ {kt} __mk = {kname}; {vt} __mv = {vname};")
            self._w(f"  __mn_map_set({dest}, &__mk, &__mv); }}")

    # --- Enum ---

    def _emit_enum_init(self, inst: EnumInit) -> None:
        dest = self._val(inst.dest)
        enum_name = inst.enum_type.type_info.name

        # Find variant index
        tag = self._enum_variant_tag(enum_name, inst.variant)
        self._w(f"{dest}.tag = {tag};")

        if inst.payload:
            vname = _safe_name(inst.variant)
            for i, pv in enumerate(inst.payload):
                pval = self._val(pv)
                # Check if this payload field is self-referential (boxed as pointer)
                pt = inst.payload[i].ty
                payload_ct = self._c_type(pt)
                if payload_ct == enum_name and enum_name in self._enums:
                    # Allocate on heap and store pointer
                    self._w(f"{{ {enum_name} *__box = malloc(sizeof({enum_name}));")
                    self._w(f"  *__box = {pval};")
                    self._w(f"  {dest}.as.{vname}._{i} = __box; }}")
                else:
                    # Use memcpy for potential type mismatches
                    self._w(f"memcpy(&{dest}.as.{vname}._{i}, &{pval},")
                    self._w(f"  sizeof({dest}.as.{vname}._{i}));")

    def _emit_enum_tag(self, inst: EnumTag) -> None:
        ev = self._val(inst.enum_val)
        dest = self._val(inst.dest)
        # Option/Result use different field names
        val_kind = inst.enum_val.ty.type_info.kind
        if val_kind == TypeKind.OPTION:
            self._w(f"{dest} = {ev}.has_value;")
        elif val_kind == TypeKind.RESULT:
            self._w(f"{dest} = {ev}.is_ok;")
        else:
            self._w(f"{dest} = {ev}.tag;")

    def _emit_enum_payload(self, inst: EnumPayload) -> None:
        dest = self._val(inst.dest)
        ev = self._val(inst.enum_val)
        val_kind = inst.enum_val.ty.type_info.kind
        # Option/Result use different extraction
        if val_kind == TypeKind.OPTION:
            self._w(f"{dest} = {ev}.value;")
        elif val_kind == TypeKind.RESULT:
            if inst.variant in ("Ok", "ok"):
                self._w(f"{dest} = {ev}.as.ok;")
            else:
                self._w(f"{dest} = {ev}.as.err;")
        else:
            vname = _safe_name(inst.variant)
            idx = inst.payload_idx
            # Check if payload was auto-boxed (self-referential enum)
            enum_name = inst.enum_val.ty.type_info.name
            dest_ct = self._c_type(inst.dest.ty)
            payload_boxed = (dest_ct == enum_name) and enum_name in self._enums
            if payload_boxed:
                self._w(f"{dest} = *{ev}.as.{vname}._{idx};")
            else:
                self._w(f"{dest} = {ev}.as.{vname}._{idx};")

    # --- Option/Result wrappers ---

    def _emit_wrap_some(self, inst: WrapSome) -> None:
        dest = self._val(inst.dest)
        val = self._val(inst.val)
        # Try declared type first
        dest_decl_ct = self._local_types.get(dest)
        if dest_decl_ct and dest_decl_ct.startswith("MnOption_"):
            ct = dest_decl_ct
        elif self._cur_fn:
            # Try function return type if this is likely a return value
            fn_ret = self._c_type(self._cur_fn.return_type)
            if fn_ret.startswith("MnOption_"):
                ct = fn_ret
            else:
                ct = self._c_type(inst.dest.ty)
        else:
            ct = self._c_type(inst.dest.ty)
        self._w(f"{dest} = ({ct}){{1, {val}}};")

    def _emit_wrap_none(self, inst: WrapNone) -> None:
        dest = self._val(inst.dest)
        dest_decl_ct = self._local_types.get(dest)
        if dest_decl_ct and dest_decl_ct.startswith("MnOption_"):
            ct = dest_decl_ct
        else:
            ct = self._c_type(inst.dest.ty)
        self._w(f"memset(&{dest}, 0, sizeof({dest}));")

    def _emit_wrap_ok(self, inst: WrapOk) -> None:
        dest = self._val(inst.dest)
        val = self._val(inst.val)
        ct = self._c_type(inst.dest.ty)
        self._w(f"{dest} = ({ct}){{.is_ok = 1, .as = {{.ok = {val}}}}};")

    def _emit_wrap_err(self, inst: WrapErr) -> None:
        dest = self._val(inst.dest)
        val = self._val(inst.val)
        ct = self._c_type(inst.dest.ty)
        self._w(f"{dest} = ({ct}){{.is_ok = 0, .as = {{.err = {val}}}}};")

    def _emit_unwrap(self, inst: Unwrap) -> None:
        dest = self._val(inst.dest)
        val = self._val(inst.val)
        val_kind = inst.val.ty.type_info.kind
        if val_kind == TypeKind.OPTION:
            self._w(f"{dest} = {val}.value;")
        elif val_kind == TypeKind.RESULT:
            self._w(f"{dest} = {val}.as.ok;")
        else:
            self._w(f"{dest} = {val}; /* unwrap fallback */")

    # --- Function calls ---

    def _emit_call(self, inst: Call) -> None:  # noqa: C901
        dest = self._val(inst.dest)
        fn_name = inst.fn_name
        args = [self._val(a) for a in inst.args]

        # --- Builtin dispatch ---

        # print / println
        if fn_name in ("print", "println"):
            if inst.args:
                arg = inst.args[0]
                kind = arg.ty.type_info.kind
                av = args[0]
                if kind == TypeKind.STRING:
                    self._w(f"__mn_str_println({av});")
                elif kind == TypeKind.INT:
                    self._w(f'printf("%lld\\n", (long long){av});')
                elif kind == TypeKind.FLOAT:
                    self._w(f'printf("%f\\n", {av});')
                elif kind == TypeKind.BOOL:
                    self._w(f"__mn_str_println(__mn_str_from_bool({av}));")
                else:
                    self._w(f'printf("%lld\\n", (long long){av});')
            return

        # len
        if fn_name == "len":
            if inst.args:
                kind = inst.args[0].ty.type_info.kind
                av = args[0]
                if kind == TypeKind.STRING:
                    self._w(f"{dest} = __mn_str_len({av});")
                elif kind == TypeKind.LIST:
                    self._w(f"{dest} = __mn_list_len(&{av});")
                elif kind == TypeKind.MAP:
                    self._w(f"{dest} = __mn_map_len({av});")
                else:
                    self._w(f"{dest} = 0; /* len: unknown type */")
            return

        # str (type conversion to string)
        if fn_name in ("str", "toString"):
            if inst.args:
                kind = inst.args[0].ty.type_info.kind
                av = args[0]
                if kind == TypeKind.INT:
                    self._w(f"{dest} = __mn_str_from_int({av});")
                elif kind == TypeKind.FLOAT:
                    self._w(f"{dest} = __mn_str_from_float({av});")
                elif kind == TypeKind.BOOL:
                    self._w(f"{dest} = __mn_str_from_bool({av});")
                elif kind == TypeKind.STRING:
                    self._w(f"{dest} = {av};")
                else:
                    self._w(f"{dest} = __mn_str_from_int((int64_t){av});")
            return

        # int/float casts
        if fn_name == "int" and inst.args:
            kind = inst.args[0].ty.type_info.kind
            av = args[0]
            if kind == TypeKind.FLOAT:
                self._w(f"{dest} = (int64_t){av};")
            elif kind == TypeKind.STRING:
                self._w(f"{dest} = __mn_str_to_int({av});")
            else:
                self._w(f"{dest} = (int64_t){av};")
            return

        if fn_name == "float" and inst.args:
            kind = inst.args[0].ty.type_info.kind
            av = args[0]
            if kind == TypeKind.INT:
                self._w(f"{dest} = (double){av};")
            elif kind == TypeKind.STRING:
                self._w(f"{dest} = __mn_str_to_float({av});")
            else:
                self._w(f"{dest} = (double){av};")
            return

        # ord / chr
        if fn_name == "ord" and inst.args:
            self._w(f"{dest} = __mn_str_ord({args[0]});")
            return
        if fn_name == "chr" and inst.args:
            self._w(f"{dest} = __mn_str_chr({args[0]});")
            return

        # join
        if fn_name == "join" and len(inst.args) >= 2:
            self._w(f"{dest} = __mn_str_join({args[0]}, &{args[1]});")
            return

        # range — delegates to C runtime __mn_range (returns opaque iterator)
        if fn_name == "range":
            if len(args) == 1:
                self._w(f"{dest} = __mn_range(0, {args[0]});")
            elif len(args) == 2:
                self._w(f"{dest} = __mn_range({args[0]}, {args[1]});")
            elif len(args) >= 3:
                self._w(f"{dest} = __mn_range({args[0]}, {args[1]});")
            return

        # __mn_range / __mn_range_inclusive — C runtime range constructors
        if fn_name in ("__mn_range", "__mn_range_inclusive"):
            args_str = ", ".join(args)
            self._w(f"{dest} = {fn_name}({args_str});")
            return

        # Some/Ok/Err constructors
        if fn_name == "Some" and inst.args:
            ct = self._c_type(inst.dest.ty)
            self._w(f"{dest} = ({ct}){{1, {args[0]}}};")
            return
        if fn_name == "Ok" and inst.args:
            ct = self._c_type(inst.dest.ty)
            self._w(f"{dest} = ({ct}){{.is_ok = 1, .as = {{.ok = {args[0]}}}}};")
            return
        if fn_name == "Err" and inst.args:
            ct = self._c_type(inst.dest.ty)
            self._w(f"{dest} = ({ct}){{.is_ok = 0, .as = {{.err = {args[0]}}}}};")
            return

        # --- String methods (lowered as Call with __ prefix or bare name) ---
        if fn_name.startswith("__mn_str_") or fn_name.startswith("__mn_list_"):
            args_str = ", ".join(args)
            ret_type = self._c_type(inst.dest.ty)
            if ret_type == "void":
                self._w(f"{fn_name}({args_str});")
            else:
                self._w(f"{dest} = {fn_name}({args_str});")
            return

        # String methods lowered as bare names (e.g., contains, to_upper)
        _STR_METHOD_MAP = {
            "contains": "__mn_str_contains",
            "to_upper": "__mn_str_to_upper",
            "to_lower": "__mn_str_to_lower",
            "starts_with": "__mn_str_starts_with",
            "ends_with": "__mn_str_ends_with",
            "trim": "__mn_str_trim",
            "trim_start": "__mn_str_trim_start",
            "trim_end": "__mn_str_trim_end",
            "replace": "__mn_str_replace",
            "split": "__mn_str_split",
            "find": "__mn_str_find",
            "substr": "__mn_str_substr",
            "char_at": "__mn_str_char_at",
            "byte_at": "__mn_str_byte_at",
        }
        if fn_name in _STR_METHOD_MAP:
            rt_name = _STR_METHOD_MAP[fn_name]
            args_str = ", ".join(args)
            ret_type = self._c_type(inst.dest.ty)
            if ret_type == "void":
                self._w(f"{rt_name}({args_str});")
            else:
                self._w(f"{dest} = {rt_name}({args_str});")
            return

        # --- Iterator protocol (C runtime functions) ---
        if fn_name == "__iter_has_next":
            # C runtime: int8_t __iter_has_next(void *iter)
            self._w(f"{dest} = (int64_t)__iter_has_next({args[0]});")
            return

        if fn_name == "__iter_next":
            # C runtime: void* __iter_next(void *iter) — returns value as intptr
            ct = self._c_type(inst.dest.ty)
            if ct in ("int64_t", "double"):
                self._w(f"{dest} = (int64_t)(intptr_t)__iter_next({args[0]});")
            else:
                self._w(f"{dest} = ({ct})__iter_next({args[0]});")
            return

        # --- Enum variant constructors (e.g., Color_Green(), Ok(val)) ---
        # Check if fn_name is an enum variant constructor: EnumName_Variant
        for enum_name, variants in self._enums.items():
            for vname, payload_types in variants:
                constructor_name = f"{enum_name}_{vname}"
                if fn_name == constructor_name:
                    tag = self._enum_variant_tag(enum_name, vname)
                    # Use enum_name as the C type (not inst.dest.ty which may be UNKNOWN)
                    if not payload_types:
                        self._w(f"{dest} = ({enum_name}){{.tag = {tag}}};")
                    else:
                        sv = _safe_name(vname)
                        # Handle self-referential boxing
                        self._w(f"{dest}.tag = {tag};")
                        for pi in range(min(len(args), len(payload_types))):
                            pt_ct = self._c_type(payload_types[pi])
                            if pt_ct == enum_name:
                                # Box: heap-allocate
                                self._w(f"{{ {enum_name} *__bp = malloc(sizeof({enum_name}));")
                                self._w(f"  *__bp = {args[pi]};")
                                self._w(f"  {dest}.as.{sv}._{pi} = __bp; }}")
                            else:
                                self._w(f"memcpy(&{dest}.as.{sv}._{pi}, &{args[pi]},")
                                self._w(f"  sizeof({dest}.as.{sv}._{pi}));")
                    return

        # --- User-defined or runtime function call ---
        c_name = self._fn_c_name(fn_name)
        # Coerce arguments to match function parameter types
        coerced_args = list(args)
        if fn_name in self._fn_map:
            fn_params = self._fn_map[fn_name].params
            for pi in range(min(len(coerced_args), len(fn_params))):
                param_ct = self._c_type(fn_params[pi].ty)
                arg_ct = self._local_types.get(args[pi], "int64_t")
                if param_ct != arg_ct and param_ct not in ("int64_t", "double", "void"):
                    # Cast via temporary variable
                    tmp = f"__coerce_{pi}"
                    self._w(f"{{ {param_ct} {tmp};")
                    self._w(f"  memcpy(&{tmp}, &{args[pi]}, sizeof({tmp}));")
                    coerced_args[pi] = tmp
        args_str = ", ".join(coerced_args)
        ret_type = self._c_type(inst.dest.ty)
        n_coerced = sum(1 for a in coerced_args if a.startswith("__coerce_"))
        if ret_type == "void":
            self._w(f"{c_name}({args_str});")
        else:
            self._w(f"{dest} = {c_name}({args_str});")
        for _ in range(n_coerced):
            self._w("}")

    def _emit_extern_call(self, inst: ExternCall) -> None:
        dest = self._val(inst.dest)
        args_str = ", ".join(self._val(a) for a in inst.args)
        ret_type = self._c_type(inst.dest.ty)
        if ret_type == "void":
            self._w(f"{inst.fn_name}({args_str});")
        else:
            self._w(f"{dest} = {inst.fn_name}({args_str});")

    # --- Control flow ---

    def _emit_return(self, inst: Return, block_label: str) -> None:
        self._emit_phi_stores(block_label)
        if inst.val is not None:
            val_name = self._val(inst.val)
            # Check if return value type matches function return type
            if self._cur_fn:
                fn_ret = self._c_type(self._cur_fn.return_type)
                val_ct = self._local_types.get(val_name, "int64_t")
                if val_ct != fn_ret and fn_ret not in ("void", "int64_t"):
                    # Cast via memcpy for struct types
                    self._w(f"{{ {fn_ret} __rv; memcpy(&__rv, &{val_name}, sizeof(__rv));")
                    self._w("  return __rv; }")
                    return
            self._w(f"return {val_name};")
        else:
            self._w("return;")

    def _emit_jump(self, inst: Jump, block_label: str) -> None:
        self._emit_phi_stores(block_label)
        self._w(f"goto {_block_label(inst.target)};")

    def _emit_branch(self, inst: Branch, block_label: str) -> None:
        self._emit_phi_stores(block_label)
        cond = self._val(inst.cond)
        self._w(f"if ({cond}) goto {_block_label(inst.true_block)};")
        self._w(f"goto {_block_label(inst.false_block)};")

    def _emit_switch(self, inst: Switch, block_label: str) -> None:
        self._emit_phi_stores(block_label)
        tag = self._val(inst.tag)
        tag_kind = inst.tag.ty.type_info.kind
        self._w(f"switch ((int64_t){tag}) {{")
        self._indent_inc()
        for case_val, target in inst.cases:
            if isinstance(case_val, int):
                self._w(f"case {case_val}: goto {_block_label(target)};")
            elif isinstance(case_val, str):
                # Result/Option use is_ok/has_value (1=Ok/Some, 0=Err/None)
                if tag_kind == TypeKind.RESULT or case_val in ("Ok", "Err"):
                    tag_val = "1" if case_val == "Ok" else "0"
                elif tag_kind == TypeKind.OPTION or case_val in ("Some", "None"):
                    tag_val = "1" if case_val == "Some" else "0"
                else:
                    # Regular enum — resolve tag index
                    enum_name = inst.tag.ty.type_info.name if inst.tag.ty.type_info.name else ""
                    tag_val = self._enum_variant_tag(enum_name, case_val)
                self._w(f"case {tag_val}: goto {_block_label(target)};")
            else:
                self._w(f"case {case_val}: goto {_block_label(target)};")
        self._w(f"default: goto {_block_label(inst.default_block)};")
        self._indent_dec()
        self._w("}")

    # --- Closures ---

    def _emit_closure_create(self, inst: ClosureCreate) -> None:
        dest = self._val(inst.dest)
        fn_name = self._fn_c_name(inst.fn_name)

        if not inst.captures:
            self._w(f"{dest} = (MnClosure){{(void*){fn_name}, NULL}};")
            return

        # Allocate environment struct
        captures_size = " + ".join(f"sizeof({self._c_type(ct)})" for ct in inst.capture_types)
        self._w("{")
        self._indent_inc()
        self._w(f"void *__env = malloc({captures_size});")
        self._w("char *__envp = (char*)__env;")
        offset = 0
        for i, (cv, ct) in enumerate(zip(inst.captures, inst.capture_types)):
            ctype = self._c_type(ct)
            cv_name = self._val(cv)
            self._w(f"*({ctype}*)(__envp + {offset}) = {cv_name};")
            " + ".join(f"sizeof({self._c_type(inst.capture_types[j])})" for j in range(i + 1))
            # We track offset symbolically using sizeof
        self._w(f"{dest} = (MnClosure){{(void*){fn_name}, __env}};")
        self._indent_dec()
        self._w("}")

    def _emit_closure_call(self, inst: ClosureCall) -> None:
        dest = self._val(inst.dest)
        closure = self._val(inst.closure)
        args = [self._val(a) for a in inst.args]
        ret_type = self._c_type(inst.dest.ty)

        # Build function pointer type
        param_types = ["void*"] + [self._c_type(a.ty) for a in inst.args]
        params_str = ", ".join(param_types)
        if ret_type == "void":
            fptr_type = f"void(*)({params_str})"
        else:
            fptr_type = f"{ret_type}(*)({params_str})"

        args_with_env = [f"{closure}.env"] + args
        args_str = ", ".join(args_with_env)

        if ret_type == "void":
            self._w(f"(({fptr_type}){closure}.fn)({args_str});")
        else:
            self._w(f"{dest} = (({fptr_type}){closure}.fn)({args_str});")

    def _emit_env_load(self, inst: EnvLoad) -> None:
        dest = self._val(inst.dest)
        env = self._val(inst.env)
        val_type = self._c_type(inst.val_type)
        # Calculate byte offset — we need to know sizes of captures at indices < inst.index
        # For now use a simple approach: index * 8 (assumes 8-byte alignment)
        # A more precise approach would track capture types per function
        offset = inst.index * 8
        self._w(f"{dest} = *({val_type}*)((char*){env} + {offset});")

    # --- String interpolation ---

    def _emit_interp_concat(self, inst: InterpConcat) -> None:
        dest = self._val(inst.dest)
        if not inst.parts:
            self._w(f"{dest} = (MnString){{NULL, 0}};")
            return
        if len(inst.parts) == 1:
            p = inst.parts[0]
            pv = self._val(p)
            if p.ty.type_info.kind == TypeKind.STRING:
                self._w(f"{dest} = {pv};")
            else:
                self._w(f"{dest} = __mn_str_from_int((int64_t){pv});")
            return

        # Chain concatenations
        parts_converted: list[str] = []
        for p in inst.parts:
            pv = self._val(p)
            kind = p.ty.type_info.kind
            if kind == TypeKind.STRING:
                parts_converted.append(pv)
            elif kind == TypeKind.INT:
                parts_converted.append(f"__mn_str_from_int({pv})")
            elif kind == TypeKind.FLOAT:
                parts_converted.append(f"__mn_str_from_float({pv})")
            elif kind == TypeKind.BOOL:
                parts_converted.append(f"__mn_str_from_bool({pv})")
            else:
                parts_converted.append(f"__mn_str_from_int((int64_t){pv})")

        # Build chain: concat(concat(a, b), c)
        chain: str = parts_converted[0]
        for part_str in parts_converted[1:]:
            chain = f"__mn_str_concat({chain}, {part_str})"
        self._w(f"{dest} = {chain};")

    # --- Assert ---

    def _emit_assert(self, inst: Assert) -> None:
        cond = self._val(inst.cond)
        if inst.message is not None:
            msg = self._val(inst.message)
            self._w(f"if (!{cond}) {{")
            fmt = '"assertion failed: %.*s\\n"'
            self._w(f"  fprintf(stderr, {fmt}, (int){msg}.len, {msg}.data);")
            self._w("  exit(1); }")
        else:
            loc = f"{inst.filename}:{inst.line}"
            self._w(f"if (!{cond}) {{")
            self._w(f'  fprintf(stderr, "assertion failed at {loc}\\n");')
            self._w("  exit(1); }")

    # --- Agents ---

    def _emit_agent_spawn(self, inst: AgentSpawn) -> None:
        dest = self._val(inst.dest)
        agent_name = inst.agent_type.type_info.name or "agent"
        escaped = _escape_c_string(agent_name)
        self._w(f'{dest} = mapanare_agent_new("{escaped}");')
        self._w(f"mapanare_agent_spawn({dest});")

    def _emit_agent_send(self, inst: AgentSend) -> None:
        agent = self._val(inst.agent)
        val = self._val(inst.val)
        ct = self._c_type(inst.val.ty)
        self._w(f"{{ {ct} *__msg = malloc(sizeof({ct}));")
        self._w(f"  *__msg = {val};")
        self._w(f"  mapanare_agent_send({agent}, __msg); }}")

    def _emit_agent_sync(self, inst: AgentSync) -> None:
        dest = self._val(inst.dest)
        agent = self._val(inst.agent)
        ct = self._c_type(inst.dest.ty)
        self._w("{ void *__out = NULL;")
        self._w(f"  mapanare_agent_recv_blocking({agent}, &__out);")
        self._w(f"  if (__out) {dest} = *({ct}*)__out; }}")

    # --- Signals ---

    def _emit_signal_init(self, inst: SignalInit) -> None:
        dest = self._val(inst.dest)
        val = self._val(inst.initial_val)
        ct = self._c_type(inst.signal_type)
        self._w(
            f"{{ {ct} __sig_init = {val}; {dest} = __mn_signal_new(&__sig_init, sizeof({ct})); }}"
        )

    def _emit_signal_get(self, inst: SignalGet) -> None:
        dest = self._val(inst.dest)
        signal = self._val(inst.signal)
        ct = self._c_type(inst.dest.ty)
        self._w(f"{dest} = *({ct}*)__mn_signal_get({signal});")

    def _emit_signal_set(self, inst: SignalSet) -> None:
        signal = self._val(inst.signal)
        val = self._val(inst.val)
        ct = self._c_type(inst.val.ty)
        self._w(f"{{ {ct} __sig_val = {val}; __mn_signal_set({signal}, &__sig_val); }}")

    def _emit_signal_computed(self, inst: SignalComputed) -> None:
        dest = self._val(inst.dest)
        fn_name = self._fn_c_name(inst.compute_fn)
        n_deps = len(inst.deps)
        deps_arr = ", ".join(self._val(d) for d in inst.deps)
        self._w(f"{{ MnSignal *__deps[] = {{{deps_arr}}};")
        compute = f"(MnSignalComputeFn){fn_name}"
        self._w(f"  {dest} = __mn_signal_computed({compute}, NULL,")
        self._w(f"    __deps, {n_deps}, {inst.val_size}); }}")

    def _emit_signal_subscribe(self, inst: SignalSubscribe) -> None:
        signal = self._val(inst.signal)
        sub = self._val(inst.subscriber)
        self._w(f"__mn_signal_subscribe({signal}, (MnSignalCallback){sub}, NULL);")

    # --- Streams ---

    def _emit_stream_init(self, inst: StreamInit) -> None:
        dest = self._val(inst.dest)
        source = self._val(inst.source)
        elem_size = self._elem_size(inst.elem_type)
        self._w(f"{dest} = __mn_stream_from_list(&{source}, {elem_size});")

    def _emit_stream_op(self, inst: StreamOp) -> None:
        dest = self._val(inst.dest)
        source = self._val(inst.source)

        if inst.op_kind == StreamOpKind.MAP:
            fn = self._fn_c_name(inst.fn_name) if inst.fn_name else "NULL"
            self._w(f"{dest} = __mn_stream_map({source}, (MnStreamMapFn){fn}, NULL, 0, 0);")
        elif inst.op_kind == StreamOpKind.FILTER:
            fn = self._fn_c_name(inst.fn_name) if inst.fn_name else "NULL"
            self._w(f"{dest} = __mn_stream_filter({source}, (MnStreamFilterFn){fn}, NULL, 0);")
        elif inst.op_kind == StreamOpKind.TAKE:
            count = self._val(inst.args[0]) if inst.args else "0"
            self._w(f"{dest} = __mn_stream_take({source}, {count});")
        elif inst.op_kind == StreamOpKind.SKIP:
            count = self._val(inst.args[0]) if inst.args else "0"
            self._w(f"{dest} = __mn_stream_skip({source}, {count});")
        elif inst.op_kind == StreamOpKind.COLLECT:
            self._w("/* stream collect */")
            # collect returns MnList
            self._w(f"{dest} = __mn_stream_collect({source}, 0, 0);")
        elif inst.op_kind == StreamOpKind.FOLD:
            fn = self._fn_c_name(inst.fn_name) if inst.fn_name else "NULL"
            init_val = self._val(inst.args[0]) if inst.args else "NULL"
            self._w("/* stream fold */")
            self._w(f"{dest} = __mn_stream_fold({source}, &{init_val}, (void*){fn}, 0, 0);")
        else:
            self._w(f"/* unhandled stream op: {inst.op_kind} */")

    # ------------------------------------------------------------------
    # main() wrapper
    # ------------------------------------------------------------------

    def _emit_main_wrapper(self, module: MIRModule) -> None:
        # Check if there's a user-defined main function
        has_main = any(fn.name == "main" for fn in module.functions)
        if not has_main:
            return

        self._w("int main(int argc, char **argv) {")
        self._indent_inc()
        self._w("mn_main();")
        self._w("return 0;")
        self._indent_dec()
        self._w("}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _elem_size(self, ty: MIRType) -> str:
        """Return a C expression for the byte size of a type."""
        ct = self._c_type(ty)
        if ct in ("int64_t", "double"):
            return "sizeof(int64_t)"
        if ct == "MnString":
            return "sizeof(MnString)"
        if ct == "MnList":
            return "sizeof(MnList)"
        if ct.endswith("*"):
            return "sizeof(void*)"
        return f"sizeof({ct})"

    def _map_key_tag(self, key_type: MIRType) -> str:
        """Return the MN_MAP_KEY_* constant for a key type."""
        kind = key_type.type_info.kind
        if kind == TypeKind.INT:
            return "MN_MAP_KEY_INT"
        if kind == TypeKind.STRING:
            return "MN_MAP_KEY_STR"
        if kind == TypeKind.FLOAT:
            return "MN_MAP_KEY_FLOAT"
        return "MN_MAP_KEY_INT"

    def _enum_variant_tag(self, enum_name: str, variant: str) -> str:
        """Get the integer tag for an enum variant."""
        variants = self._enums.get(enum_name, [])
        for i, (vname, _) in enumerate(variants):
            if vname == variant:
                return str(i)
        return f"/* unknown variant {variant} */ 0"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def emit_c(module: MIRModule, debug: bool = False) -> str:
    """Emit C source from a MIR module.

    This is the main entry point for the C backend.

    Args:
        module: The MIR module to compile.
        debug: If True, emit debug comments in the output.

    Returns:
        Complete C source file as a string.
    """
    emitter = CEmitter(debug=debug)
    return emitter.emit(module)
