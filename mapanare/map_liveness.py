"""Prove when a loop's previous factory result has no surviving map alias."""

from dataclasses import fields

from mapanare.mir import (
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Copy,
    IndexGet,
    Instruction,
    Jump,
    MIRFunction,
    Phi,
    Return,
    Switch,
    Value,
)
from mapanare.types import TypeKind

_SCALARS = {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.CHAR}


def valid_ownership_phis(fn: MIRFunction, kind: TypeKind) -> set[int]:
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
                and inst.dest.ty.kind == kind
                and all(value.ty.kind == kind for _, value in inst.incoming)
            ):
                valid.add(id(inst))
    return valid


def _alias_closure(roots: set[str], aliases: dict[str, set[str]]) -> set[str]:
    result = set(roots)
    pending = list(roots)
    while pending:
        for alias in aliases.get(pending.pop(), ()):
            if alias not in result:
                result.add(alias)
                pending.append(alias)
    return result


def _borrowed_uses_safe(
    maps: set[str],
    instructions: list[Instruction],
    aliases: dict[str, set[str]],
    live: set[str],
    parameters: set[str],
) -> bool:
    """Keep the parent map alive for cursors and borrowed String reads.

    Scalar loads are detached values. String loads retain a dependency on the
    map and may only flow through copies/phis and known noncapturing reads.
    """
    cursor_defs = {
        id(inst): inst
        for inst in instructions
        if isinstance(inst, Call)
        and inst.fn_name == "__mn_map_iter_new"
        and len(inst.args) == 1
        and inst.args[0].name in maps
        and inst.dest.ty.kind == TypeKind.ANY
    }
    cursors = _alias_closure({inst.dest.name for inst in cursor_defs.values()}, aliases)
    read_defs: dict[int, IndexGet | Call] = {}
    for inst in instructions:
        if isinstance(inst, IndexGet) and inst.obj.name in maps:
            if inst.dest.ty.kind in _SCALARS | {TypeKind.STRING}:
                read_defs[id(inst)] = inst
        if isinstance(inst, Call) and inst.fn_name == "__map_iter_next":
            if len(inst.args) == 1 and inst.args[0].name in cursors:
                if inst.dest.ty.kind in _SCALARS | {TypeKind.STRING}:
                    read_defs[id(inst)] = inst
    strings = _alias_closure(
        {inst.dest.name for inst in read_defs.values() if inst.dest.ty.kind == TypeKind.STRING},
        aliases,
    )
    if (cursors | strings) & (live | parameters):
        return False
    if maps & (cursors | strings) or cursors & strings:
        return False
    for inst in instructions:
        uses = _uses(inst)
        dest = getattr(inst, "dest", None)
        if isinstance(dest, Value):
            if dest.name in cursors:
                if dest.ty.kind != TypeKind.ANY:
                    return False
                if id(inst) not in cursor_defs and not isinstance(inst, (Copy, Phi)):
                    return False
            if dest.name in strings:
                if dest.ty.kind != TypeKind.STRING:
                    return False
                if id(inst) not in read_defs and not isinstance(inst, (Copy, Phi)):
                    return False
        if uses & maps:
            if isinstance(inst, (Copy, Phi)) or id(inst) in cursor_defs or id(inst) in read_defs:
                pass
            elif isinstance(inst, Call) and inst.fn_name == "len" and len(inst.args) == 1:
                pass
            else:
                return False
        if uses & cursors:
            if isinstance(inst, (Copy, Phi)) or id(inst) in read_defs:
                pass
            elif isinstance(inst, Call) and len(inst.args) == 1 and inst.args[0].name in cursors:
                if not (
                    (inst.fn_name == "__map_iter_has_next" and inst.dest.ty.kind == TypeKind.BOOL)
                    or (inst.fn_name == "__mn_map_iter_free" and inst.dest.ty.kind == TypeKind.VOID)
                ):
                    return False
            else:
                return False
        if uses & strings:
            if isinstance(inst, (Copy, Phi)) or id(inst) in read_defs:
                continue
            if isinstance(inst, Call) and inst.fn_name in ("len", "print", "println"):
                if len(inst.args) == 1 and inst.args[0].ty.kind == TypeKind.STRING:
                    continue
            if isinstance(inst, BinOp) and inst.op in (BinOpKind.EQ, BinOpKind.NE):
                if inst.dest.ty.kind == TypeKind.BOOL and all(
                    value.ty.kind == TypeKind.STRING for value in (inst.lhs, inst.rhs)
                ):
                    continue
            return False
    return True


def _uses(inst: Instruction) -> set[str]:
    def names(value: object) -> set[str]:
        if isinstance(value, Value):
            return {value.name}
        if isinstance(value, (list, tuple)):
            return set().union(*(names(item) for item in value)) if value else set()
        return set()

    return set().union(
        *(names(getattr(inst, field.name)) for field in fields(inst) if field.name != "dest")
    )


def recyclable_map_results(fn: MIRFunction, factories: set[str]) -> set[str]:
    """Select closed, single-origin alias groups dead before their next allocation.

    Map aliases, cursors and borrowed String views must all be dead. Unknown
    consumers fail closed. Phi uses are treated as live on every predecessor,
    deliberately overestimating liveness.
    """
    if fn.is_async:
        return set()
    candidates = [
        (block.label, inst)
        for block in fn.blocks
        for inst in block.instructions
        if isinstance(inst, Call)
        and inst.dest.ty.kind == TypeKind.MAP
        and inst.fn_name in factories
    ]
    if not candidates:
        return set()
    successors: dict[str, set[str]] = {}
    for block in fn.blocks:
        if not block.instructions:
            return set()
        term = block.instructions[-1]
        if isinstance(term, Jump):
            successors[block.label] = {term.target}
        elif isinstance(term, Branch):
            successors[block.label] = {term.true_block, term.false_block}
        elif isinstance(term, Switch):
            successors[block.label] = {term.default_block, *(label for _, label in term.cases)}
        elif isinstance(term, Return):
            successors[block.label] = set()
        else:
            return set()
    if any(target not in successors for targets in successors.values() for target in targets):
        return set()

    live_in = {label: set() for label in successors}
    live_before: dict[int, set[str]] = {}
    changed = True
    while changed:
        changed = False
        for block in reversed(fn.blocks):
            live = set().union(*(live_in[target] for target in successors[block.label]))
            for inst in reversed(block.instructions):
                dest = getattr(inst, "dest", None)
                if isinstance(dest, Value):
                    live.discard(dest.name)
                live.update(_uses(inst))
                live_before[id(inst)] = set(live)
            if live != live_in[block.label]:
                live_in[block.label] = live
                changed = True

    aliases: dict[str, set[str]] = {}
    instructions = [inst for block in fn.blocks for inst in block.instructions]
    for inst in instructions:
        if isinstance(inst, (Copy, Phi)):
            for name in _uses(inst):
                aliases.setdefault(inst.dest.name, set()).add(name)
                aliases.setdefault(name, set()).add(inst.dest.name)

    eligible: set[str] = set()
    for label, allocation in candidates:
        # A call outside a cycle cannot overwrite its own previous result.
        pending = list(successors[label])
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current not in visited:
                visited.add(current)
                pending.extend(successors[current] - visited)
        if label not in visited:
            continue
        group = _alias_closure({allocation.dest.name}, aliases)
        if group & live_before[id(allocation)] or any(p.name in group for p in fn.params):
            continue
        safe = True
        for inst in instructions:
            dest = getattr(inst, "dest", None)
            if isinstance(dest, Value) and dest.name in group:
                if inst is not allocation and not isinstance(inst, (Copy, Phi)):
                    safe = False
        if safe and _borrowed_uses_safe(
            group, instructions, aliases, live_before[id(allocation)], {p.name for p in fn.params}
        ):
            eligible.add(allocation.dest.name)
    return eligible
