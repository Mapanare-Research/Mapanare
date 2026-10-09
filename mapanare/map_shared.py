"""Closed local map groups whose handle copies can own runtime references."""

from mapanare.map_liveness import _alias_closure, _uses
from mapanare.map_views import retained_map_views
from mapanare.mir import (
    Branch,
    Call,
    Const,
    Copy,
    IndexGet,
    Jump,
    MapInit,
    MIRFunction,
    Phi,
    Return,
    Switch,
    Value,
)
from mapanare.types import TypeKind

_SCALARS = {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.CHAR}


def _valid_map_phis(fn: MIRFunction) -> set[int]:
    """Require leading, typed Phis covering each real predecessor exactly once."""
    predecessors: dict[str, set[str]] = {block.label: set() for block in fn.blocks}
    for block in fn.blocks:
        term = block.terminator
        targets: list[str] = []
        if isinstance(term, Jump):
            targets = [term.target]
        elif isinstance(term, Branch):
            targets = [term.true_block, term.false_block]
        elif isinstance(term, Switch):
            targets = [term.default_block] + [label for _, label in term.cases]
        for target in targets:
            if target in predecessors:
                predecessors[target].add(block.label)
    valid: set[int] = set()
    for block in fn.blocks:
        for inst in block.instructions:
            if not isinstance(inst, Phi):
                break
            labels = [label for label, _ in inst.incoming]
            if (
                labels
                and len(labels) == len(set(labels))
                and set(labels) == predecessors[block.label]
                and inst.dest.ty.kind == TypeKind.MAP
                and all(value.ty.kind == TypeKind.MAP for _, value in inst.incoming)
            ):
                valid.add(id(inst))
    return valid


def shared_map_aliases(fn: MIRFunction, factories: set[str], recycled: set[str]) -> set[str]:
    """Prove complete map alias groups for retain-before-replace assignments.

    No parameters, captures or mutations qualify. Local String views retain
    their parent; private cursors have explicit lifetimes. Direct map returns
    transfer a retained reference to the caller. Construction accepts scalar or literal
    String fields. Factory arguments must be scalars, so a result cannot borrow
    caller-owned storage through its inputs. Existing cheaper recycling wins.
    """
    if fn.is_async:
        return set()
    instructions = [inst for block in fn.blocks for inst in block.instructions]
    used = set().union(*(_uses(inst) for inst in instructions))
    valid_phis = _valid_map_phis(fn)
    definitions: dict[str, list[object]] = {}
    aliases: dict[str, set[str]] = {}
    roots: set[str] = set()
    for inst in instructions:
        dest = getattr(inst, "dest", None)
        if isinstance(dest, Value):
            definitions.setdefault(dest.name, []).append(inst)
            if dest.ty.kind == TypeKind.MAP:
                roots.add(dest.name)
        if isinstance(inst, Copy):
            aliases.setdefault(inst.dest.name, set()).add(inst.src.name)
            aliases.setdefault(inst.src.name, set()).add(inst.dest.name)
        elif isinstance(inst, Phi) and inst.dest.name in used:
            for _, value in inst.incoming:
                aliases.setdefault(inst.dest.name, set()).add(value.name)
                aliases.setdefault(value.name, set()).add(inst.dest.name)
    parameters = {param.name for param in fn.params}

    def literal_string(value: Value, seen: frozenset[str] = frozenset()) -> bool:
        if value.name in parameters or value.name in seen or len(seen) >= 64:
            return False
        origins = definitions.get(value.name, [])
        return bool(origins) and all(
            isinstance(origin, Const)
            and isinstance(origin.value, str)
            or isinstance(origin, Copy)
            and literal_string(origin.src, seen | {value.name})
            for origin in origins
        )

    eligible: set[str] = set()
    visited: set[str] = set()
    for root in sorted(roots):
        if root in visited:
            continue
        group = _alias_closure({root}, aliases)
        visited.update(group)
        if group & (parameters | recycled) or any(name not in definitions for name in group):
            continue
        if retained_map_views(fn, group) is None:
            continue
        safe = True
        has_origin = False
        for inst in instructions:
            dest = getattr(inst, "dest", None)
            if isinstance(dest, Value) and dest.name in group:
                if dest.ty.kind != TypeKind.MAP:
                    safe = False
                if isinstance(inst, Copy):
                    if inst.src.ty.kind != TypeKind.MAP:
                        safe = False
                elif isinstance(inst, Phi):
                    if id(inst) not in valid_phis:
                        safe = False
                elif isinstance(inst, Call):
                    has_origin = True
                    if inst.fn_name not in factories or any(
                        a.ty.kind not in _SCALARS for a in inst.args
                    ):
                        safe = False
                elif isinstance(inst, MapInit):
                    has_origin = True
                    if inst.key_type.kind not in _SCALARS | {
                        TypeKind.STRING
                    } or inst.val_type.kind not in _SCALARS | {TypeKind.STRING}:
                        safe = False
                    if any(
                        value.ty.kind == TypeKind.STRING and not literal_string(value)
                        for pair in inst.pairs
                        for value in pair
                    ):
                        safe = False
                else:
                    safe = False
            if not _uses(inst) & group:
                continue
            # Lowering emits unused statement-result phis (sometimes with a
            # void alternative). They store pointer bits but cannot expose a
            # map or extend its lifetime when the result has no consumers.
            if isinstance(inst, Phi) and inst.dest.name not in used:
                continue
            if isinstance(inst, Copy) and inst.dest.name in group:
                continue
            if isinstance(inst, Phi) and inst.dest.name in group and id(inst) in valid_phis:
                continue
            if (
                isinstance(inst, Return)
                and fn.return_type.kind == TypeKind.MAP
                and inst.val is not None
                and inst.val.ty.kind == TypeKind.MAP
            ):
                continue
            if isinstance(inst, Call) and inst.fn_name == "len" and len(inst.args) == 1:
                continue
            if (
                isinstance(inst, Call)
                and inst.fn_name == "__mn_map_iter_new"
                and len(inst.args) == 1
                and inst.dest.ty.kind == TypeKind.ANY
            ):
                continue
            if (
                isinstance(inst, IndexGet)
                and inst.obj.name in group
                and inst.dest.ty.kind in _SCALARS | {TypeKind.STRING}
            ):
                continue
            safe = False
        if safe and has_origin:
            eligible.update(group)
    return eligible
