"""MIR optimization passes for the Mapanare compiler.

Operates on the SSA-based MIR instead of the AST. The flat, three-address
representation makes analysis and transformation simpler than the tree-based
AST optimizer.

Passes:
- Constant folding: evaluate BinOp/UnaryOp on Const operands
- Constant propagation: replace uses of Const-assigned vars
- Copy propagation: replace uses of Copy destinations with source
- Dead code elimination: remove instructions with no uses
- Dead function elimination: remove uncalled functions
- Unreachable block elimination: remove blocks with no predecessors
- Branch simplification: constant conditions become Jump
- Agent inlining: single-spawn agents become direct calls
- Stream fusion: fuse adjacent StreamOp instructions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any

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
    Const,
    Copy,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListPush,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    StreamOp,
    StreamOpKind,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Value,
)
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Optimization level
# ---------------------------------------------------------------------------


class MIROptLevel(IntEnum):
    """Optimization levels matching -O0 through -O3."""

    O0 = 0  # No optimization
    O1 = 1  # Basic: constant folding, constant propagation
    O2 = 2  # Standard: + DCE, dead fn elimination, agent inlining,
    #          copy propagation, unreachable block elim, branch simplification
    O3 = 3  # Aggressive: + stream fusion


# ---------------------------------------------------------------------------
# Pass statistics
# ---------------------------------------------------------------------------


@dataclass
class MIRPassStats:
    """Statistics collected by MIR optimization passes."""

    constants_folded: int = 0
    constants_propagated: int = 0
    copies_propagated: int = 0
    dead_instructions_removed: int = 0
    dead_fns_removed: int = 0
    unreachable_blocks_removed: int = 0
    branches_simplified: int = 0
    agents_inlined: int = 0
    streams_fused: int = 0

    @property
    def total_changes(self) -> int:
        return (
            self.constants_folded
            + self.constants_propagated
            + self.copies_propagated
            + self.dead_instructions_removed
            + self.dead_fns_removed
            + self.unreachable_blocks_removed
            + self.branches_simplified
            + self.agents_inlined
            + self.streams_fused
        )


# ---------------------------------------------------------------------------
# Helpers: instruction use/def analysis
# ---------------------------------------------------------------------------


def _get_dest(inst: Instruction) -> Value | None:
    """Get the destination value of an instruction, if any."""
    return getattr(inst, "dest", None)


def _get_uses(inst: Instruction) -> list[Value]:
    """Get all values used (read) by an instruction."""
    uses: list[Value] = []

    if isinstance(inst, Const):
        pass  # no uses
    elif isinstance(inst, Copy):
        uses.append(inst.src)
    elif isinstance(inst, BinOp):
        uses.extend([inst.lhs, inst.rhs])
    elif isinstance(inst, UnaryOp):
        uses.append(inst.operand)
    elif isinstance(inst, Call):
        uses.extend(inst.args)
    elif isinstance(inst, Return):
        if inst.val is not None:
            uses.append(inst.val)
    elif isinstance(inst, Branch):
        uses.append(inst.cond)
    elif isinstance(inst, Switch):
        uses.append(inst.tag)
    elif isinstance(inst, Phi):
        for _, val in inst.incoming:
            uses.append(val)
    elif isinstance(inst, InterpConcat):
        uses.extend(inst.parts)
    elif isinstance(inst, FieldGet):
        uses.append(inst.obj)
    elif isinstance(inst, FieldSet):
        uses.extend([inst.obj, inst.val])
    elif isinstance(inst, IndexGet):
        uses.extend([inst.obj, inst.index])
    elif isinstance(inst, IndexSet):
        uses.extend([inst.obj, inst.index, inst.val])
    elif isinstance(inst, ListPush):
        uses.extend([inst.list_val, inst.element])
    elif isinstance(inst, AgentSpawn):
        uses.extend(inst.args)
    elif isinstance(inst, AgentSend):
        uses.extend([inst.agent, inst.val])
    elif isinstance(inst, AgentSync):
        uses.append(inst.agent)
    elif isinstance(inst, StreamOp):
        uses.append(inst.source)
        uses.extend(inst.args)
    elif isinstance(inst, Assert):
        uses.append(inst.cond)
        if inst.message is not None:
            uses.append(inst.message)
    else:
        # Generic fallback: look for common value-holding attributes
        for attr in ("src", "val", "signal", "enum_val", "initial_val", "operand"):
            v = getattr(inst, attr, None)
            if isinstance(v, Value):
                uses.append(v)
        for attr in ("args", "parts", "elements", "payload"):
            vs = getattr(inst, attr, None)
            if isinstance(vs, list):
                for v in vs:
                    if isinstance(v, Value):
                        uses.append(v)
        for attr in ("fields", "pairs", "incoming"):
            vs = getattr(inst, attr, None)
            if isinstance(vs, list):
                for item in vs:
                    if isinstance(item, tuple):
                        for v in item:
                            if isinstance(v, Value):
                                uses.append(v)
    return uses


def _replace_use(inst: Instruction, old_name: str, new_val: Value) -> bool:
    """Replace all uses of `old_name` with `new_val` in the instruction. Returns True if changed."""
    changed = False

    if isinstance(inst, Copy) and inst.src.name == old_name:
        inst.src = new_val
        changed = True
    elif isinstance(inst, BinOp):
        if inst.lhs.name == old_name:
            inst.lhs = new_val
            changed = True
        if inst.rhs.name == old_name:
            inst.rhs = new_val
            changed = True
    elif isinstance(inst, UnaryOp) and inst.operand.name == old_name:
        inst.operand = new_val
        changed = True
    elif isinstance(inst, Call):
        for i, arg in enumerate(inst.args):
            if arg.name == old_name:
                inst.args[i] = new_val
                changed = True
    elif isinstance(inst, Return) and inst.val is not None and inst.val.name == old_name:
        inst.val = new_val
        changed = True
    elif isinstance(inst, Branch) and inst.cond.name == old_name:
        inst.cond = new_val
        changed = True
    elif isinstance(inst, Switch) and inst.tag.name == old_name:
        inst.tag = new_val
        changed = True
    elif isinstance(inst, Phi):
        for i, (lbl, val) in enumerate(inst.incoming):
            if val.name == old_name:
                inst.incoming[i] = (lbl, new_val)
                changed = True
    elif isinstance(inst, InterpConcat):
        for i, part in enumerate(inst.parts):
            if part.name == old_name:
                inst.parts[i] = new_val
                changed = True
    elif isinstance(inst, FieldGet) and inst.obj.name == old_name:
        inst.obj = new_val
        changed = True
    elif isinstance(inst, FieldSet):
        if inst.obj.name == old_name:
            inst.obj = new_val
            changed = True
        if inst.val.name == old_name:
            inst.val = new_val
            changed = True
    elif isinstance(inst, IndexGet):
        if inst.obj.name == old_name:
            inst.obj = new_val
            changed = True
        if inst.index.name == old_name:
            inst.index = new_val
            changed = True
    elif isinstance(inst, IndexSet):
        if inst.obj.name == old_name:
            inst.obj = new_val
            changed = True
        if inst.index.name == old_name:
            inst.index = new_val
            changed = True
        if inst.val.name == old_name:
            inst.val = new_val
            changed = True
    elif isinstance(inst, ListPush):
        if inst.list_val.name == old_name:
            inst.list_val = new_val
            changed = True
        if inst.element.name == old_name:
            inst.element = new_val
            changed = True
    elif isinstance(inst, AgentSpawn):
        for i, arg in enumerate(inst.args):
            if arg.name == old_name:
                inst.args[i] = new_val
                changed = True
    elif isinstance(inst, AgentSend):
        if inst.agent.name == old_name:
            inst.agent = new_val
            changed = True
        if inst.val.name == old_name:
            inst.val = new_val
            changed = True
    elif isinstance(inst, AgentSync) and inst.agent.name == old_name:
        inst.agent = new_val
        changed = True
    elif isinstance(inst, StreamOp):
        if inst.source.name == old_name:
            inst.source = new_val
            changed = True
        for i, arg in enumerate(inst.args):
            if arg.name == old_name:
                inst.args[i] = new_val
                changed = True
    return changed


# ---------------------------------------------------------------------------
# Pass 1: Constant Folding
# ---------------------------------------------------------------------------


def _try_fold_binop(op: BinOpKind, lv: Any, rv: Any) -> Any | None:
    """Try to evaluate a binary operation on constant values."""
    try:
        if op == BinOpKind.ADD:
            if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
                return lv + rv
            if isinstance(lv, str) and isinstance(rv, str):
                return lv + rv
        elif op == BinOpKind.SUB and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv - rv
        elif op == BinOpKind.MUL and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv * rv
        elif op == BinOpKind.DIV and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            if rv == 0:
                return None
            if isinstance(lv, int) and isinstance(rv, int):
                return lv // rv
            return lv / rv
        elif op == BinOpKind.MOD and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            if rv == 0:
                return None
            return lv % rv
        elif op == BinOpKind.EQ and type(lv) is type(rv):
            return lv == rv
        elif op == BinOpKind.NE and type(lv) is type(rv):
            return lv != rv
        elif op == BinOpKind.LT and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv < rv
        elif op == BinOpKind.LE and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv <= rv
        elif op == BinOpKind.GT and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv > rv
        elif op == BinOpKind.GE and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv >= rv
        elif op == BinOpKind.AND and isinstance(lv, bool) and isinstance(rv, bool):
            return lv and rv
        elif op == BinOpKind.OR and isinstance(lv, bool) and isinstance(rv, bool):
            return lv or rv
    except (ArithmeticError, TypeError):
        pass
    return None


def _try_fold_unaryop(op: UnaryOpKind, val: Any) -> Any | None:
    """Try to evaluate a unary operation on a constant value."""
    if op == UnaryOpKind.NEG and isinstance(val, (int, float)):
        return -val
    if op == UnaryOpKind.NOT and isinstance(val, bool):
        return not val
    return None


def _type_for_value(val: Any) -> TypeKind:
    """Determine the TypeKind for a Python constant value."""
    if isinstance(val, bool):
        return TypeKind.BOOL
    if isinstance(val, int):
        return TypeKind.INT
    if isinstance(val, float):
        return TypeKind.FLOAT
    if isinstance(val, str):
        return TypeKind.STRING
    return TypeKind.UNKNOWN


def constant_folding(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Fold BinOp/UnaryOp instructions on Const operands.

    Returns True if any changes were made.
    """
    # Build a map of value name -> constant value (from Const instructions)
    # Exclude values that are defined more than once (mutable variable SSA reuse)
    const_vals: dict[str, Any] = {}
    def_counts: dict[str, int] = {}
    const_candidates: list[Const] = []
    for bb in fn.blocks:
        for inst in bb.instructions:
            dest = _get_dest(inst)
            if dest is not None and dest.name:
                def_counts[dest.name] = def_counts.get(dest.name, 0) + 1
            if isinstance(inst, Const):
                const_candidates.append(inst)
    for inst in const_candidates:
        if def_counts.get(inst.dest.name, 0) <= 1:
            const_vals[inst.dest.name] = inst.value

    changed = False
    for bb in fn.blocks:
        new_insts: list[Instruction] = []
        for inst in bb.instructions:
            if isinstance(inst, BinOp):
                lv = const_vals.get(inst.lhs.name)
                rv = const_vals.get(inst.rhs.name)
                if lv is not None and rv is not None:
                    result = _try_fold_binop(inst.op, lv, rv)
                    if result is not None:
                        tk = _type_for_value(result)
                        folded = Const(
                            dest=inst.dest,
                            ty=MIRType(TypeInfo(kind=tk)),
                            value=result,
                        )
                        new_insts.append(folded)
                        const_vals[inst.dest.name] = result
                        stats.constants_folded += 1
                        changed = True
                        continue
            elif isinstance(inst, UnaryOp):
                val = const_vals.get(inst.operand.name)
                if val is not None:
                    result = _try_fold_unaryop(inst.op, val)
                    if result is not None:
                        tk = _type_for_value(result)
                        folded = Const(
                            dest=inst.dest,
                            ty=MIRType(TypeInfo(kind=tk)),
                            value=result,
                        )
                        new_insts.append(folded)
                        const_vals[inst.dest.name] = result
                        stats.constants_folded += 1
                        changed = True
                        continue
            new_insts.append(inst)
        bb.instructions = new_insts
    return changed


# ---------------------------------------------------------------------------
# Pass 2: Constant Propagation
# ---------------------------------------------------------------------------


def constant_propagation(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Replace uses of Const-assigned values with the constant itself.

    SSA makes this straightforward: each value has exactly one definition.
    Returns True if any changes were made.
    """
    # Build map: value name -> Const instruction
    const_defs: dict[str, Const] = {}
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Const) and inst.dest.name:
                const_defs[inst.dest.name] = inst

    changed = False
    for bb in fn.blocks:
        for inst in bb.instructions:
            # Don't propagate into the defining Const itself
            if isinstance(inst, Const):
                continue
            uses = _get_uses(inst)
            for use in uses:
                if use.name in const_defs:
                    # Create a new Const instruction before this one isn't needed —
                    # we just note the propagation. The actual benefit comes when
                    # this enables more folding on the next iteration.
                    # For now, track that the value could be propagated.
                    pass

    # Actually, constant propagation on SSA-MIR means: if a value is defined by
    # a Const, replace all references to that value with a fresh Const-defined
    # value. But since SSA already has single definitions, the real benefit is
    # enabling constant folding in the next iteration. The folding pass already
    # looks up const_vals by name. So propagation here means: if %x = copy %y
    # and %y is const, then %x is also const. Let's handle that case.
    for bb in fn.blocks:
        for i, inst in enumerate(bb.instructions):
            if isinstance(inst, Copy) and inst.src.name in const_defs:
                # This copy of a constant can be turned into a constant itself
                src_const = const_defs[inst.src.name]
                # Replace the Copy with a Const
                new_const = Const(
                    dest=inst.dest,
                    ty=src_const.ty,
                    value=src_const.value,
                )
                bb.instructions[i] = new_const
                const_defs[inst.dest.name] = new_const
                stats.constants_propagated += 1
                changed = True

    return changed


# ---------------------------------------------------------------------------
# Pass 3: Copy Propagation
# ---------------------------------------------------------------------------


def copy_propagation(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Replace uses of Copy destinations with the source value.

    If `%a = copy %b`, replace all uses of `%a` with `%b`.
    Returns True if any changes were made.
    """
    # Build map: copy dest name -> source value (single pass over all instructions)
    # Exclude multiply-defined values and mutation targets
    def_counts: dict[str, int] = {}
    mutated_names: set[str] = set()
    copy_candidates: list[Copy] = []
    for bb in fn.blocks:
        for inst in bb.instructions:
            dest = _get_dest(inst)
            if dest is not None and dest.name:
                def_counts[dest.name] = def_counts.get(dest.name, 0) + 1
            if isinstance(inst, Copy):
                copy_candidates.append(inst)
            elif isinstance(inst, FieldSet):
                mutated_names.add(inst.obj.name)
            elif isinstance(inst, IndexSet):
                mutated_names.add(inst.obj.name)

    copy_map: dict[str, Value] = {}
    for inst in copy_candidates:
        if def_counts.get(inst.dest.name, 0) <= 1 and inst.dest.name not in mutated_names:
            copy_map[inst.dest.name] = inst.src

    # Resolve chains: if %a = copy %b, %b = copy %c → %a maps to %c
    def resolve(name: str) -> Value:
        visited: set[str] = set()
        current = name
        last_val: Value | None = None
        while current in copy_map and current not in visited:
            visited.add(current)
            last_val = copy_map[current]
            current = last_val.name
        if current in copy_map:
            return copy_map[current]
        # Preserve the type from the last known copy source
        if last_val is not None:
            return Value(name=current, ty=last_val.ty)
        return copy_map.get(name, Value(name=name))

    if not copy_map:
        return False

    # Pre-resolve all copy chains once
    resolved_map: dict[str, Value] = {name: resolve(name) for name in copy_map}

    changed = False
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Copy) and inst.dest.name in copy_map:
                continue  # don't modify the Copy itself
            # Only check names that this instruction actually uses
            for used_val in _get_uses(inst):
                if used_val.name in resolved_map:
                    if _replace_use(inst, used_val.name, resolved_map[used_val.name]):
                        stats.copies_propagated += 1
                        changed = True
    return changed


# ---------------------------------------------------------------------------
# Pass 4: Dead Code Elimination (instruction level)
# ---------------------------------------------------------------------------


# Instructions that have side effects and cannot be removed even if unused
_SIDE_EFFECT_TYPES = (
    Call,
    Return,
    Jump,
    Branch,
    Switch,
    FieldSet,
    IndexSet,
    ListPush,
    AgentSpawn,
    AgentSend,
    AgentSync,
)


def dead_code_elimination(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Remove instructions whose dest is never used.

    Does not remove side-effecting instructions (calls, stores, terminators).
    Returns True if any changes were made.
    """
    # Collect all used value names
    used_names: set[str] = set()
    for bb in fn.blocks:
        for inst in bb.instructions:
            for use in _get_uses(inst):
                used_names.add(use.name)

    changed = False
    for bb in fn.blocks:
        new_insts: list[Instruction] = []
        for inst in bb.instructions:
            dest = _get_dest(inst)
            if (
                dest is not None
                and dest.name
                and dest.name not in used_names
                and not isinstance(inst, _SIDE_EFFECT_TYPES)
            ):
                stats.dead_instructions_removed += 1
                changed = True
                continue
            new_insts.append(inst)
        bb.instructions = new_insts
    return changed


# ---------------------------------------------------------------------------
# Pass 5: Dead Function Elimination
# ---------------------------------------------------------------------------


def dead_function_elimination(module: MIRModule, stats: MIRPassStats) -> bool:
    """Remove functions that are never called.

    Keeps `main` and public functions. Builds a call graph from Call instructions.
    Returns True if any changes were removed.
    """
    # Build set of all called function names
    called: set[str] = set()
    for fn in module.functions:
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Call):
                    called.add(inst.fn_name)

    new_fns: list[MIRFunction] = []
    changed = False
    for fn in module.functions:
        if fn.name == "main" or fn.is_public or fn.name in called:
            new_fns.append(fn)
        else:
            stats.dead_fns_removed += 1
            changed = True

    module.functions = new_fns
    return changed


# ---------------------------------------------------------------------------
# Pass 6: Unreachable Block Elimination
# ---------------------------------------------------------------------------


def _compute_reachable(fn: MIRFunction) -> set[str]:
    """Compute set of reachable block labels via BFS from entry."""
    if not fn.blocks:
        return set()

    block_map = fn.block_map()
    reachable: set[str] = set()
    worklist = [fn.blocks[0].label]

    while worklist:
        label = worklist.pop()
        if label in reachable:
            continue
        reachable.add(label)
        bb = block_map.get(label)
        if bb is None:
            continue
        term = bb.terminator
        if isinstance(term, Jump):
            worklist.append(term.target)
        elif isinstance(term, Branch):
            worklist.append(term.true_block)
            worklist.append(term.false_block)
        elif isinstance(term, Switch):
            for _, lbl in term.cases:
                worklist.append(lbl)
            if term.default_block:
                worklist.append(term.default_block)

    return reachable


def unreachable_block_elimination(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Remove basic blocks with no predecessors (except entry).

    Returns True if any blocks were removed.
    """
    if not fn.blocks:
        return False

    reachable = _compute_reachable(fn)
    new_blocks: list[BasicBlock] = []
    changed = False

    for bb in fn.blocks:
        if bb.label in reachable:
            new_blocks.append(bb)
        else:
            stats.unreachable_blocks_removed += 1
            changed = True

    if changed:
        fn.blocks = new_blocks
        # Clean up phi nodes that reference removed blocks
        all_remaining = {bb.label for bb in fn.blocks}
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    inst.incoming = [
                        (lbl, val) for lbl, val in inst.incoming if lbl in all_remaining
                    ]

    return changed


# ---------------------------------------------------------------------------
# Pass 7: Branch Simplification
# ---------------------------------------------------------------------------


def branch_simplification(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Simplify branches with constant conditions to unconditional jumps.

    `Branch(const_true, A, B)` → `Jump(A)`
    `Branch(const_false, A, B)` → `Jump(B)`

    Returns True if any changes were made.
    """
    # Build const map (exclude multiply-defined values)
    const_vals: dict[str, Any] = {}
    def_counts: dict[str, int] = {}
    for bb in fn.blocks:
        for inst in bb.instructions:
            dest = _get_dest(inst)
            if dest is not None and dest.name:
                def_counts[dest.name] = def_counts.get(dest.name, 0) + 1
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Const) and def_counts.get(inst.dest.name, 0) <= 1:
                const_vals[inst.dest.name] = inst.value

    changed = False
    for bb in fn.blocks:
        term = bb.terminator
        if isinstance(term, Branch):
            cond_val = const_vals.get(term.cond.name)
            if cond_val is True:
                bb.instructions[-1] = Jump(target=term.true_block)
                stats.branches_simplified += 1
                changed = True
            elif cond_val is False:
                bb.instructions[-1] = Jump(target=term.false_block)
                stats.branches_simplified += 1
                changed = True
    return changed


# ---------------------------------------------------------------------------
# Pass 8: Agent Inlining
# ---------------------------------------------------------------------------


def agent_inlining(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Inline single-spawn agents as direct calls.

    When an agent is spawned exactly once and only has simple send/sync
    patterns, replace the AgentSpawn/AgentSend/AgentSync sequence with
    direct Call instructions.

    Returns True if any changes were made.
    """
    # Find AgentSpawn instructions and track their uses
    spawns: dict[str, AgentSpawn] = {}  # dest name -> spawn instruction
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, AgentSpawn):
                spawns[inst.dest.name] = inst

    if not spawns:
        return False

    # Count uses of each spawned agent
    agent_sends: dict[str, list[tuple[BasicBlock, int, AgentSend]]] = {}
    agent_syncs: dict[str, list[tuple[BasicBlock, int, AgentSync]]] = {}

    for bb in fn.blocks:
        for i, inst in enumerate(bb.instructions):
            if isinstance(inst, AgentSend) and inst.agent.name in spawns:
                agent_sends.setdefault(inst.agent.name, []).append((bb, i, inst))
            elif isinstance(inst, AgentSync) and inst.agent.name in spawns:
                agent_syncs.setdefault(inst.agent.name, []).append((bb, i, inst))

    changed = False
    for agent_name, spawn in spawns.items():
        sends = agent_sends.get(agent_name, [])
        syncs = agent_syncs.get(agent_name, [])

        # Only inline simple patterns: exactly one send followed by one sync
        if len(sends) == 1 and len(syncs) == 1:
            send_bb, send_idx, send_inst = sends[0]
            sync_bb, sync_idx, sync_inst = syncs[0]

            # Get the agent type name for the method call
            agent_type = spawn.agent_type.name

            # Replace send with a call: %result = call AgentType_channel(send_val)
            call_name = f"{agent_type}_{send_inst.channel}"
            call_inst = Call(
                dest=sync_inst.dest,
                fn_name=call_name,
                args=[send_inst.val],
            )

            # Replace the sync with the call
            sync_bb.instructions[sync_idx] = call_inst

            # Remove the send (replace with nothing — just remove it)
            send_bb.instructions[send_idx] = Copy(
                dest=Value(name=f"%_dead_{agent_name}"),
                src=send_inst.val,
            )

            stats.agents_inlined += 1
            changed = True

    return changed


# ---------------------------------------------------------------------------
# Pass 9: Stream Fusion
# ---------------------------------------------------------------------------


def stream_fusion(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Fuse adjacent StreamOp instructions.

    Combines consecutive map+map, map+filter, filter+filter operations
    into single fused operations.

    Returns True if any changes were made.
    """
    changed = False
    for bb in fn.blocks:
        # Build a map of dest name -> StreamOp for this block
        stream_defs: dict[str, tuple[int, StreamOp]] = {}
        removable: set[int] = set()

        for i, inst in enumerate(bb.instructions):
            if not isinstance(inst, StreamOp):
                continue

            # Check if this StreamOp's source was defined by another StreamOp
            prev = stream_defs.get(inst.source.name)
            if prev is not None:
                prev_idx, prev_op = prev

                # map + map → fused map
                if prev_op.op_kind == StreamOpKind.MAP and inst.op_kind == StreamOpKind.MAP:
                    # Fuse: use prev's source, combine args
                    inst.source = prev_op.source
                    inst.args = prev_op.args + inst.args
                    removable.add(prev_idx)
                    stats.streams_fused += 1
                    changed = True

                # map + filter → fused map_filter (keep as map, add filter args)
                elif prev_op.op_kind == StreamOpKind.MAP and inst.op_kind == StreamOpKind.FILTER:
                    inst.source = prev_op.source
                    inst.args = prev_op.args + inst.args
                    removable.add(prev_idx)
                    stats.streams_fused += 1
                    changed = True

                # filter + filter → fused filter
                elif prev_op.op_kind == StreamOpKind.FILTER and inst.op_kind == StreamOpKind.FILTER:
                    inst.source = prev_op.source
                    inst.args = prev_op.args + inst.args
                    removable.add(prev_idx)
                    stats.streams_fused += 1
                    changed = True

            stream_defs[inst.dest.name] = (i, inst)

        if removable:
            bb.instructions = [inst for i, inst in enumerate(bb.instructions) if i not in removable]

    return changed


# ---------------------------------------------------------------------------
# Pass Manager
# ---------------------------------------------------------------------------


def optimize_function(fn: MIRFunction, level: MIROptLevel, stats: MIRPassStats) -> None:
    """Run optimization passes on a single function."""
    if level == MIROptLevel.O0:
        return

    max_iterations = 10

    # O1+: Constant folding + propagation (iterate to fixed point)
    if level >= MIROptLevel.O1:
        for _ in range(max_iterations):
            changed = False
            changed |= constant_folding(fn, stats)
            changed |= constant_propagation(fn, stats)
            if not changed:
                break

    # O2+: Copy propagation, DCE, unreachable blocks, branch simplification
    if level >= MIROptLevel.O2:
        o2_changed = copy_propagation(fn, stats)
        o2_changed |= branch_simplification(fn, stats)
        o2_changed |= unreachable_block_elimination(fn, stats)
        # Run DCE after other passes have created dead code
        dead_code_elimination(fn, stats)
        # Agent inlining
        o2_changed |= agent_inlining(fn, stats)

    # O3: Stream fusion
    if level >= MIROptLevel.O3:
        o2_changed |= stream_fusion(fn, stats)

    # Final cleanup: only re-run DCE if earlier passes created new dead code
    if level >= MIROptLevel.O2 and o2_changed:
        dead_code_elimination(fn, stats)
        unreachable_block_elimination(fn, stats)


def optimize_module(
    module: MIRModule, level: MIROptLevel = MIROptLevel.O2
) -> tuple[MIRModule, MIRPassStats]:
    """Run optimization passes on a MIR module.

    Returns the optimized module and aggregate statistics.
    """
    stats = MIRPassStats()

    if level == MIROptLevel.O0:
        return module, stats

    # Per-function passes
    for fn in module.functions:
        optimize_function(fn, level, stats)

    # Module-level passes
    if level >= MIROptLevel.O2:
        dead_function_elimination(module, stats)

    return module, stats
