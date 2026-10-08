"""Prove when a loop's previous factory result has no surviving map alias."""

from dataclasses import fields

from mapanare.mir import (
    Branch,
    Call,
    Copy,
    Instruction,
    Jump,
    MIRFunction,
    Phi,
    Return,
    Switch,
    Value,
)
from mapanare.types import TypeKind


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

    Only Copy/Phi and len uses qualify today. Unknown consumers may retain a
    handle or derive a borrowed view, so they fail closed. Phi uses are treated
    as live on every predecessor, deliberately overestimating liveness.
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
        group = {allocation.dest.name}
        pending = [allocation.dest.name]
        while pending:
            name = pending.pop()
            for alias in aliases.get(name, ()):
                if alias not in group:
                    group.add(alias)
                    pending.append(alias)
        if group & live_before[id(allocation)] or any(p.name in group for p in fn.params):
            continue
        safe = True
        for inst in instructions:
            dest = getattr(inst, "dest", None)
            if isinstance(dest, Value) and dest.name in group:
                if inst is not allocation and not isinstance(inst, (Copy, Phi)):
                    safe = False
            if _uses(inst) & group:
                if isinstance(inst, (Copy, Phi)):
                    continue
                if isinstance(inst, Call) and inst.fn_name == "len" and len(inst.args) == 1:
                    continue
                safe = False
        if safe:
            eligible.add(allocation.dest.name)
    return eligible
