"""Prove local borrowed Strings whose parent map can be retained explicitly."""

from dataclasses import dataclass

from mapanare.map_liveness import _alias_closure, _uses
from mapanare.mir import BinOp, BinOpKind, Call, Const, Copy, IndexGet, MIRFunction, Phi, Value
from mapanare.types import TypeKind

_SCALARS = {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.CHAR}


@dataclass(frozen=True)
class MapViewPlan:
    strings: frozenset[str]
    cursors: frozenset[str]


def retained_map_views(fn: MIRFunction, maps: set[str]) -> MapViewPlan | None:
    """Reject escaping views and unknown origins; private cursors cannot alias."""
    instructions = [inst for block in fn.blocks for inst in block.instructions]
    definitions: dict[str, list[object]] = {}
    aliases: dict[str, set[str]] = {}
    used = set().union(*(_uses(inst) for inst in instructions))
    cursors = {
        inst.dest.name
        for inst in instructions
        if isinstance(inst, Call)
        and inst.fn_name == "__mn_map_iter_new"
        and len(inst.args) == 1
        and inst.args[0].name in maps
        and inst.dest.ty.kind == TypeKind.ANY
    }
    reads: set[int] = set()
    strings: set[str] = set()
    for inst in instructions:
        dest = getattr(inst, "dest", None)
        if isinstance(dest, Value):
            definitions.setdefault(dest.name, []).append(inst)
        if isinstance(inst, Copy):
            aliases.setdefault(inst.dest.name, set()).add(inst.src.name)
            aliases.setdefault(inst.src.name, set()).add(inst.dest.name)
        if (
            isinstance(inst, IndexGet)
            and inst.obj.name in maps
            or isinstance(inst, Call)
            and inst.fn_name == "__map_iter_next"
            and len(inst.args) == 1
            and inst.args[0].name in cursors
        ):
            if dest.ty.kind not in _SCALARS | {TypeKind.STRING}:
                return None
            reads.add(id(inst))
            if dest.ty.kind == TypeKind.STRING:
                strings.add(dest.name)
    strings = _alias_closure(strings, aliases)
    if (strings | cursors) & ({p.name for p in fn.params} | maps) or strings & cursors:
        return None
    for name in cursors:
        origins = definitions.get(name, [])
        if len(origins) != 1 or not isinstance(origins[0], Call):
            return None
    for name in strings:
        origins = definitions.get(name, [])
        if not origins:
            return None
        for origin in origins:
            if origin.dest.ty.kind != TypeKind.STRING:
                return None
            if id(origin) in reads or isinstance(origin, Const) and isinstance(origin.value, str):
                continue
            if isinstance(origin, Copy) and origin.src.ty.kind == TypeKind.STRING:
                continue
            return None
    for inst in instructions:
        uses = _uses(inst)
        if uses & cursors:
            if not isinstance(inst, Call) or len(inst.args) != 1:
                return None
            if inst.args[0].name not in cursors:
                return None
            if not (
                id(inst) in reads
                or inst.fn_name == "__map_iter_has_next"
                and inst.dest.ty.kind == TypeKind.BOOL
                or inst.fn_name == "__mn_map_iter_free"
                and inst.dest.ty.kind == TypeKind.VOID
            ):
                return None
        if not uses & strings:
            continue
        if isinstance(inst, Phi) and inst.dest.name not in used:
            continue
        if isinstance(inst, Copy) and inst.dest.name in strings:
            continue
        if id(inst) in reads:
            continue
        if isinstance(inst, Call) and inst.fn_name in ("len", "print", "println"):
            if len(inst.args) == 1 and inst.args[0].ty.kind == TypeKind.STRING:
                continue
        if isinstance(inst, BinOp) and inst.op in (BinOpKind.EQ, BinOpKind.NE):
            if inst.dest.ty.kind == TypeKind.BOOL and all(
                value.ty.kind == TypeKind.STRING for value in (inst.lhs, inst.rhs)
            ):
                continue
        return None
    return MapViewPlan(frozenset(strings), frozenset(cursors))
