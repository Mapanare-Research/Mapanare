"""Conservative ownership summaries for direct map returns.

Only maps rooted in local construction or another proven factory qualify.
Borrowed, mixed, recursive, indirect and externally produced results stay
unproven. This does not establish ownership of nested container elements.
"""

from mapanare.mir import (
    BinOp,
    Branch,
    Call,
    Const,
    Copy,
    IndexGet,
    Jump,
    MapInit,
    MIRFunction,
    Move,
    Phi,
    Return,
    Switch,
    UnaryOp,
    Value,
)
from mapanare.types import TypeKind


def owned_map_factories(functions: list[MIRFunction]) -> set[str]:
    """Find factories whose every returned map has a fresh allocation origin."""
    proven: set[str] = set()
    changed = True
    while changed:
        changed = False
        for fn in functions:
            if fn.name in proven or fn.is_async or fn.return_type.kind != TypeKind.MAP:
                continue
            definitions: dict[str, list[object]] = {}
            returns: list[Value] = []
            unsafe = False
            for block in fn.blocks:
                for inst in block.instructions:
                    # Capturing stores, aggregate construction, indirect calls
                    # and future instructions need their own ownership rules.
                    if not isinstance(
                        inst,
                        (
                            BinOp,
                            Branch,
                            Call,
                            Const,
                            Copy,
                            IndexGet,
                            Jump,
                            MapInit,
                            Move,
                            Phi,
                            Return,
                            Switch,
                            UnaryOp,
                        ),
                    ):
                        unsafe = True
                    if isinstance(inst, MapInit) and any(
                        value.ty.kind == TypeKind.MAP for pair in inst.pairs for value in pair
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
                    # Unknown map consumers may capture a local allocation.
                    if isinstance(inst, Call) and any(a.ty.kind == TypeKind.MAP for a in inst.args):
                        if inst.fn_name not in ("len", "__mn_map_iter_new"):
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
                    if isinstance(origin, MapInit):
                        # Nested resource ownership is a separate contract.
                        if origin.key_type.kind not in (
                            TypeKind.INT,
                            TypeKind.FLOAT,
                            TypeKind.BOOL,
                            TypeKind.STRING,
                        ) or origin.val_type.kind not in (
                            TypeKind.INT,
                            TypeKind.FLOAT,
                            TypeKind.BOOL,
                            TypeKind.STRING,
                        ):
                            return False
                    elif isinstance(origin, Copy):
                        if not fresh(origin.src, visiting):
                            return False
                    elif isinstance(origin, Phi):
                        if not origin.incoming or not all(
                            fresh(v, visiting) for _, v in origin.incoming
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
