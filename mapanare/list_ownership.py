"""Conservative ownership summaries for direct list returns.

Mirrors map_ownership.py: only lists rooted in local construction or another
proven factory qualify. Borrowed, mixed, recursive, indirect and externally
produced results stay unproven.
"""

from mapanare.mir import (
    BinOp,
    Branch,
    Call,
    Const,
    Copy,
    EnumTag,
    IndexGet,
    Jump,
    ListInit,
    ListPush,
    MIRFunction,
    Move,
    Phi,
    Return,
    Switch,
    UnaryOp,
    Value,
)
from mapanare.types import TypeKind


def owned_list_factories(functions: list[MIRFunction]) -> set[str]:
    """Find factories whose every returned list has a fresh allocation origin."""
    proven: set[str] = set()
    changed = True
    while changed:
        changed = False
        for fn in functions:
            if fn.name in proven or fn.is_async or fn.return_type.kind != TypeKind.LIST:
                continue
            definitions: dict[str, list[object]] = {}
            returns: list[Value] = []
            unsafe = False
            for block in fn.blocks:
                for inst in block.instructions:
                    if not isinstance(
                        inst,
                        (
                            BinOp,
                            Branch,
                            Call,
                            Const,
                            Copy,
                            EnumTag,
                            IndexGet,
                            Jump,
                            ListInit,
                            ListPush,
                            Move,
                            Phi,
                            Return,
                            Switch,
                            UnaryOp,
                        ),
                    ):
                        unsafe = True
                    dest = getattr(inst, "dest", None)
                    if isinstance(dest, Value):
                        definitions.setdefault(dest.name, []).append(inst)
                    if isinstance(inst, Return):
                        if inst.val is None:
                            unsafe = True
                        else:
                            returns.append(inst.val)
                    # Unknown list consumers may capture a local allocation.
                    if isinstance(inst, Call) and any(
                        a.ty.kind == TypeKind.LIST for a in inst.args
                    ):
                        if inst.fn_name not in ("len", "__mn_list_push"):
                            unsafe = True

            parameters = {param.name for param in fn.params}

            def fresh(value: Value, visiting: frozenset[str] = frozenset()) -> bool:
                if len(visiting) >= 64 or value.name in visiting or value.name in parameters:
                    return False
                origins = definitions.get(value.name, [])
                if not origins:
                    return False
                visiting = visiting | {value.name}
                for origin in origins:
                    if isinstance(origin, ListInit):
                        continue
                    if isinstance(origin, Copy):
                        if not fresh(origin.src, visiting):
                            return False
                    elif isinstance(origin, ListPush):
                        # In-place push (dest == list_val) keeps the same
                        # allocation; a push into a different value must be
                        # traced like a copy.
                        if origin.list_val.name != value.name and not fresh(
                            origin.list_val, visiting
                        ):
                            return False
                    elif isinstance(origin, Phi):
                        if not origin.incoming or not all(
                            fresh(v, visiting) for _, v in origin.incoming
                        ):
                            return False
                    elif isinstance(origin, IndexGet):
                        # The emitter retains nested-list reads, so a read
                        # from a fresh outer list yields an owned handle.
                        if (
                            origin.obj.ty.kind != TypeKind.LIST
                            or origin.dest.ty.kind != TypeKind.LIST
                            or not fresh(origin.obj, visiting)
                        ):
                            return False
                    elif isinstance(origin, Call):
                        if origin.fn_name not in proven:
                            return False
                    else:
                        return False
                return True

            if not unsafe and returns and all(fresh(value) for value in returns):
                proven.add(fn.name)
                changed = True
    return proven
