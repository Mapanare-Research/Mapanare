"""Conservative MIR proof that a function only borrows its arguments.

Keep this whitelist aligned with borrow_instruction_safe/function_borrows_strings
in self/emit_llvm.mn. Unknown operations, mutation, capture, allocation, indirect
calls and resource-bearing returns all fail closed. This is not a purity proof:
a pure function may still return or capture an input's storage.
"""

from __future__ import annotations

from mapanare.mir import (
    BinOp,
    Branch,
    Call,
    Cast,
    Const,
    Copy,
    IndexGet,
    Instruction,
    Jump,
    MIRFunction,
    MIRType,
    Phi,
    Return,
    Switch,
    UnaryOp,
)
from mapanare.types import TypeKind


def _scalar(ty: MIRType) -> bool:
    return ty.kind in (TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.CHAR)


def _read_type(ty: MIRType, depth: int = 0) -> bool:
    if depth > 32:
        return False
    if _scalar(ty) or ty.kind == TypeKind.STRING:
        return True
    if ty.kind == TypeKind.LIST and len(ty.type_info.args) == 1:
        return _read_type(MIRType(ty.type_info.args[0]), depth + 1)
    return False


def _instruction_borrows(inst: Instruction) -> bool:
    if isinstance(inst, Jump):
        return True
    if isinstance(inst, Const):
        # Containers must come from parameters or borrowed loads, not constants.
        return _scalar(inst.ty) or inst.ty.kind in (TypeKind.STRING, TypeKind.VOID)
    if isinstance(inst, Copy):
        return _read_type(inst.dest.ty) and _read_type(inst.src.ty)
    if isinstance(inst, IndexGet):
        return (
            inst.obj.ty.kind == TypeKind.LIST
            and _read_type(inst.obj.ty)
            and inst.index.ty.kind == TypeKind.INT
            and _read_type(inst.dest.ty)
        )
    if isinstance(inst, BinOp):
        return all(_scalar(v.ty) for v in (inst.dest, inst.lhs, inst.rhs))
    if isinstance(inst, UnaryOp):
        return _scalar(inst.dest.ty) and _scalar(inst.operand.ty)
    if isinstance(inst, Cast):
        return _scalar(inst.dest.ty) and _scalar(inst.src.ty) and _scalar(inst.target_type)
    if isinstance(inst, Call):
        args = inst.args
        if inst.fn_name == "len":
            return (
                len(args) == 1
                and args[0].ty.kind in (TypeKind.STRING, TypeKind.LIST)
                and _read_type(args[0].ty)
                and inst.dest.ty.kind == TypeKind.INT
            )
        if inst.fn_name in ("__mn_range", "__mn_range_inclusive"):
            return (
                len(args) == 2
                and all(a.ty.kind == TypeKind.INT for a in args)
                and inst.dest.ty.kind == TypeKind.RANGE
            )
        if inst.fn_name in ("__mn_range_start", "__mn_range_end"):
            return (
                len(args) == 1
                and args[0].ty.kind == TypeKind.RANGE
                and inst.dest.ty.kind == TypeKind.INT
            )
        # Python lowering represents range loops using a private iterator;
        # unlike container iteration, these calls only touch range state.
        if inst.fn_name in ("__iter_has_next", "__iter_next", "__mn_range_free"):
            result_kind = {
                "__iter_has_next": TypeKind.BOOL,
                "__iter_next": TypeKind.INT,
                "__mn_range_free": TypeKind.BOOL,  # lowerer's ignored sentinel result
            }[inst.fn_name]
            return (
                len(args) == 1
                and args[0].ty.kind == TypeKind.RANGE
                and inst.dest.ty.kind == result_kind
            )
        return False
    if isinstance(inst, Phi):
        return _read_type(inst.dest.ty) and all(_read_type(v.ty) for _, v in inst.incoming)
    if isinstance(inst, Return):
        return inst.val is None or _scalar(inst.val.ty)
    if isinstance(inst, Branch):
        return _scalar(inst.cond.ty)
    if isinstance(inst, Switch):
        return _scalar(inst.tag.ty)
    return False


def function_borrows_arguments(fn: MIRFunction) -> bool:
    """Prove all arguments stay borrowed throughout every block of a body."""
    if not fn.blocks or fn.is_async:
        return False
    if not _scalar(fn.return_type) and fn.return_type.kind != TypeKind.VOID:
        return False
    if not all(_read_type(param.ty) for param in fn.params):
        return False
    return all(_instruction_borrows(inst) for block in fn.blocks for inst in block.instructions)
