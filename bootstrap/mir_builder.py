"""Minimal MIR builder for Phase 1 — constructs MIR skeletons from AST.

This provides enough to support `mapanare emit-mir` for debugging.
Full AST→MIR lowering is implemented in Phase 2 (lower.py).
"""

from __future__ import annotations

from mapanare.ast_nodes import (
    AgentDef,
    DocComment,
    EnumDef,
    ExternFnDef,
    FnDef,
    NamedType,
    Program,
    StructDef,
)
from mapanare.mir import (
    BasicBlock,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRType,
    Return,
    mir_void,
)
from mapanare.types import TypeInfo, TypeKind, kind_from_name


def _resolve_type_expr_to_mir(type_expr: object) -> MIRType:
    """Convert an AST TypeExpr to a MIRType (basic resolution)."""
    if isinstance(type_expr, NamedType):
        k = kind_from_name(type_expr.name)
        if k == TypeKind.UNKNOWN and type_expr.name:
            return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=type_expr.name))
        return MIRType(TypeInfo(kind=k))
    return MIRType(TypeInfo(kind=TypeKind.UNKNOWN))


def build_mir(program: Program, module_name: str = "") -> MIRModule:
    """Build a MIR module from a typed AST (skeleton — Phase 1 only).

    Creates function signatures, struct/enum declarations, and placeholder
    blocks. Full instruction lowering is deferred to Phase 2.
    """
    module = MIRModule(name=module_name)

    for defn in program.definitions:
        # Unwrap doc comments
        actual = defn
        if isinstance(actual, DocComment):
            if actual.definition is not None:
                actual = actual.definition
            else:
                continue

        if isinstance(actual, FnDef):
            mir_fn = _build_fn_skeleton(actual)
            module.functions.append(mir_fn)

        elif isinstance(actual, StructDef):
            fields = [(f.name, _resolve_type_expr_to_mir(f.type_annotation)) for f in actual.fields]
            module.structs[actual.name] = fields

        elif isinstance(actual, EnumDef):
            variants = []
            for v in actual.variants:
                payload_types = [_resolve_type_expr_to_mir(f) for f in v.fields]
                variants.append((v.name, payload_types))
            module.enums[actual.name] = variants

        elif isinstance(actual, ExternFnDef):
            param_types = [_resolve_type_expr_to_mir(p.type_annotation) for p in actual.params]
            ret_type = (
                _resolve_type_expr_to_mir(actual.return_type) if actual.return_type else mir_void()
            )
            module.extern_fns.append(
                (actual.abi, actual.module or "", actual.name, param_types, ret_type)
            )

        elif isinstance(actual, AgentDef):
            # Agents become functions in MIR (simplified for Phase 1)
            for method in actual.methods:
                mir_fn = _build_fn_skeleton(method)
                mir_fn.name = f"{actual.name}_{method.name}"
                module.functions.append(mir_fn)

    return module


def _build_fn_skeleton(fn_def: FnDef) -> MIRFunction:
    """Build a MIR function skeleton from a FnDef."""
    params = [
        MIRParam(
            name=p.name,
            ty=_resolve_type_expr_to_mir(p.type_annotation) if p.type_annotation else MIRType(),
        )
        for p in fn_def.params
    ]

    ret_type = _resolve_type_expr_to_mir(fn_def.return_type) if fn_def.return_type else mir_void()

    decorators = [d.name for d in fn_def.decorators]

    # Placeholder entry block with a void return
    entry = BasicBlock(label="entry", instructions=[Return()])

    return MIRFunction(
        name=fn_def.name,
        params=params,
        return_type=ret_type,
        blocks=[entry],
        decorators=decorators,
        is_public=fn_def.public,
    )
