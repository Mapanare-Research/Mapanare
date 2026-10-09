"""Identify private range temporaries whose cleanup cannot invalidate an alias."""

from mapanare.map_liveness import _uses
from mapanare.mir import Call, MIRFunction, Value
from mapanare.types import TypeKind


def private_range_results(fn: MIRFunction) -> set[str]:
    """Accept direct iterator uses; copies, captures and returns stay untracked."""
    if fn.is_async:
        return set()
    instructions = [inst for block in fn.blocks for inst in block.instructions]
    definitions: dict[str, int] = {}
    for inst in instructions:
        dest = getattr(inst, "dest", None)
        if isinstance(dest, Value):
            definitions[dest.name] = definitions.get(dest.name, 0) + 1
    parameters = {p.name for p in fn.params}
    safe: set[str] = set()
    for inst in instructions:
        if not (
            isinstance(inst, Call)
            and inst.fn_name in ("__mn_range", "__mn_range_inclusive")
            and inst.dest.ty.kind == TypeKind.RANGE
            and len(inst.args) == 2
            and all(arg.ty.kind == TypeKind.INT for arg in inst.args)
        ):
            continue
        name = inst.dest.name
        if name in parameters or definitions[name] != 1:
            continue
        uses = [use for use in instructions if name in _uses(use)]
        if (
            all(
                isinstance(use, Call)
                and use.fn_name in ("__iter_has_next", "__iter_next", "__mn_range_free")
                and len(use.args) == 1
                and use.args[0].name == name
                for use in uses
            )
            and sum(isinstance(use, Call) and use.fn_name == "__mn_range_free" for use in uses) <= 1
        ):
            safe.add(name)
    return safe
