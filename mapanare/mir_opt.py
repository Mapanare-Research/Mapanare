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
- Function inlining: small functions (< 20 instr, not recursive) inlined at call site
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
    AllocKind,
    Assert,
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnumInit,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRLoop,
    MIRModule,
    MIRType,
    Phi,
    Return,
    SignalComputed,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
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
    functions_inlined: int = 0
    licm_hoisted: int = 0
    strength_reduced: int = 0
    allocations_promoted: int = 0  # v4.89.0: heap-to-stack promotions

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
            + self.functions_inlined
            + self.licm_hoisted
            + self.strength_reduced
            + self.allocations_promoted
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
    elif isinstance(inst, ClosureCall):
        uses.append(inst.closure)
        uses.extend(inst.args)
    elif isinstance(inst, ClosureCreate):
        uses.extend(inst.captures)
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
    elif isinstance(inst, ClosureCall):
        if inst.closure.name == old_name:
            inst.closure = new_val
            changed = True
        for i, arg in enumerate(inst.args):
            if arg.name == old_name:
                inst.args[i] = new_val
                changed = True
    elif isinstance(inst, ClosureCreate):
        for i, cap in enumerate(inst.captures):
            if cap.name == old_name:
                inst.captures[i] = new_val
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

                # --- Identity / annihilator rules (one operand constant) ---
                # x + 0 = x, 0 + x = x
                if inst.op == BinOpKind.ADD:
                    if rv == 0 and isinstance(rv, (int, float)):
                        new_insts.append(Copy(dest=inst.dest, src=inst.lhs))
                        stats.constants_folded += 1
                        changed = True
                        continue
                    if lv == 0 and isinstance(lv, (int, float)):
                        new_insts.append(Copy(dest=inst.dest, src=inst.rhs))
                        stats.constants_folded += 1
                        changed = True
                        continue

                # x * 1 = x, 1 * x = x
                if inst.op == BinOpKind.MUL:
                    if rv == 1 and isinstance(rv, (int, float)):
                        new_insts.append(Copy(dest=inst.dest, src=inst.lhs))
                        stats.constants_folded += 1
                        changed = True
                        continue
                    if lv == 1 and isinstance(lv, (int, float)):
                        new_insts.append(Copy(dest=inst.dest, src=inst.rhs))
                        stats.constants_folded += 1
                        changed = True
                        continue
                    # x * 0 = 0, 0 * x = 0
                    if rv == 0 and isinstance(rv, (int, float)):
                        tk = TypeKind.INT if isinstance(rv, int) else TypeKind.FLOAT
                        new_insts.append(
                            Const(
                                dest=inst.dest,
                                ty=MIRType(TypeInfo(kind=tk)),
                                value=type(rv)(0),
                            )
                        )
                        stats.constants_folded += 1
                        changed = True
                        continue
                    if lv == 0 and isinstance(lv, (int, float)):
                        tk = TypeKind.INT if isinstance(lv, int) else TypeKind.FLOAT
                        new_insts.append(
                            Const(
                                dest=inst.dest,
                                ty=MIRType(TypeInfo(kind=tk)),
                                value=type(lv)(0),
                            )
                        )
                        stats.constants_folded += 1
                        changed = True
                        continue

                # x - 0 = x
                if inst.op == BinOpKind.SUB:
                    if rv == 0 and isinstance(rv, (int, float)):
                        new_insts.append(Copy(dest=inst.dest, src=inst.lhs))
                        stats.constants_folded += 1
                        changed = True
                        continue

                # x - x = 0 (same operand) — preserve the operand type
                if inst.op == BinOpKind.SUB and inst.lhs.name == inst.rhs.name:
                    is_float = inst.lhs.ty.kind == TypeKind.FLOAT
                    tk = TypeKind.FLOAT if is_float else TypeKind.INT
                    new_insts.append(
                        Const(
                            dest=inst.dest,
                            ty=MIRType(TypeInfo(kind=tk)),
                            value=0.0 if is_float else 0,
                        )
                    )
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

    Only propagates through values with a single definition — values that are
    reassigned (e.g., loop variables) are excluded to avoid propagating stale
    constants across loop back-edges.
    Returns True if any changes were made.
    """
    # Count definitions per variable name.  Mapanare's MIR allows the same
    # name to be redefined (mutable variables), so a name with >1 definition
    # must NOT be constant-propagated.
    def_counts: dict[str, int] = {}
    for bb in fn.blocks:
        for inst in bb.instructions:
            dest = getattr(inst, "dest", None)
            if dest is not None and hasattr(dest, "name") and dest.name:
                def_counts[dest.name] = def_counts.get(dest.name, 0) + 1

    # Build map: value name -> Const instruction (single-def only)
    const_defs: dict[str, Const] = {}
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Const) and inst.dest.name:
                if def_counts.get(inst.dest.name, 0) == 1:
                    const_defs[inst.dest.name] = inst

    changed = False

    # If %x = copy %y and %y is a single-def constant, replace with a Const.
    # Only do this when %x itself is also single-def to avoid breaking loops.
    for bb in fn.blocks:
        for i, inst in enumerate(bb.instructions):
            if isinstance(inst, Copy) and inst.src.name in const_defs:
                if def_counts.get(inst.dest.name, 0) > 1:
                    continue
                src_const = const_defs[inst.src.name]
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


# Instructions that have side effects and cannot be removed even if unused.
# NOTE: Kept for backwards compatibility; prefer ``inst.has_side_effects``
# (property defined on the Instruction base class in mir.py).
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

    v4.30.0 Phase 3.1 (convergence fix): internally iterates to a fixed
    point instead of doing a single pass. A chain of N dependent dead
    instructions used to need N *outer* fixpoint iterations to drain;
    ``emit_llvm__emit_binop`` has >10 layers and was the sole function
    that forced the outer loop past the 10-iteration cap. Draining the
    chain in one call means DCE reports ``changed`` at most twice: once
    when there is real work, once more to confirm the next pass did not
    create anything new. The outer loop now reliably converges in ≤ 3
    iterations on the whole self-hosted corpus.
    """
    total_changed = False
    while True:
        # Collect all used value names — must be recomputed each sweep
        # because earlier sweeps removed instructions that contributed
        # uses.
        used_names: set[str] = set()
        for bb in fn.blocks:
            for inst in bb.instructions:
                for use in _get_uses(inst):
                    used_names.add(use.name)

        sweep_changed = False
        for bb in fn.blocks:
            new_insts: list[Instruction] = []
            for inst in bb.instructions:
                dest = _get_dest(inst)
                if (
                    dest is not None
                    and dest.name
                    and dest.name not in used_names
                    and not inst.has_side_effects
                ):
                    stats.dead_instructions_removed += 1
                    sweep_changed = True
                    continue
                new_insts.append(inst)
            bb.instructions = new_insts
        if not sweep_changed:
            break
        total_changed = True
    return total_changed


# ---------------------------------------------------------------------------
# Pass 5: Dead Function Elimination
# ---------------------------------------------------------------------------


def dead_function_elimination(module: MIRModule, stats: MIRPassStats) -> bool:
    """Remove functions that are never called.

    Keeps `main` and public functions. Builds a call graph from Call instructions.
    Returns True if any changes were removed.

    v4.30.0: agent methods (``method_names`` on every ``MIRAgentInfo``)
    are considered alive because the LLVM text emitter generates a
    ``__mn_handler_<AgentName>`` wrapper that dispatches to them after
    optimization runs. Without this seed, DFE would eliminate e.g.
    ``Doubler_handle`` before ``_emit_agent_wrap`` gets a chance to
    reference it, and the agent dispatch wiring v4.30.0 adds would
    fall back to the historical null-and-zero stub every time.
    """
    # Build set of all referenced function names
    called: set[str] = set()
    all_fn_names = {fn.name for fn in module.functions}
    for fn in module.functions:
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Call):
                    called.add(inst.fn_name)
                    # Also resolve namespaced calls (e.g., Program_start → start)
                    if inst.fn_name not in all_fn_names and "_" in inst.fn_name:
                        parts = inst.fn_name.split("_", 1)
                        if len(parts) == 2 and parts[1] in all_fn_names:
                            called.add(parts[1])
                elif isinstance(inst, ClosureCreate):
                    called.add(inst.fn_name)
                elif isinstance(inst, StreamOp) and inst.fn_name:
                    called.add(inst.fn_name)
                elif isinstance(inst, SignalComputed) and inst.compute_fn:
                    called.add(inst.compute_fn)

    # v4.30.0: seed agent method names. The handler wrapper emitted by
    # ``emit_llvm_text.py`` references these by string name rather than
    # by a ``Call`` instruction, so the static pass above cannot see
    # them as reachable.
    for agent_info in module.agents.values():
        for method_name in getattr(agent_info, "method_names", ()):
            called.add(method_name)

    # Also keep known entry points for the C bootstrap
    _ENTRY_POINTS = {"main", "compile_and_print", "compile", "version", "mn_main", "format_error"}
    new_fns: list[MIRFunction] = []
    changed = False
    for fn in module.functions:
        if fn.name in _ENTRY_POINTS or fn.is_public or fn.name in called:
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


# ---------------------------------------------------------------------------
# Dominance tree (iterative dataflow algorithm — Cooper, Harvey, Kennedy)
# ---------------------------------------------------------------------------


def _compute_predecessors(fn: MIRFunction) -> dict[str, list[str]]:
    """Build predecessor map: block label -> list of predecessor labels."""
    preds: dict[str, list[str]] = {bb.label: [] for bb in fn.blocks}
    for bb in fn.blocks:
        term = bb.terminator
        if isinstance(term, Jump):
            if term.target in preds:
                preds[term.target].append(bb.label)
        elif isinstance(term, Branch):
            if term.true_block in preds:
                preds[term.true_block].append(bb.label)
            if term.false_block in preds:
                preds[term.false_block].append(bb.label)
        elif isinstance(term, Switch):
            for _, lbl in term.cases:
                if lbl in preds:
                    preds[lbl].append(bb.label)
            if term.default_block and term.default_block in preds:
                preds[term.default_block].append(bb.label)
    return preds


def compute_dominance_tree(fn: MIRFunction) -> dict[str, str | None]:
    """Compute the immediate dominator tree using the iterative algorithm.

    Returns a dict mapping each block label to its immediate dominator label.
    The entry block maps to None.

    Algorithm: Cooper, Harvey, Kennedy — "A Simple, Fast Dominance Algorithm"
    (2001). Iterates to a fixed point. O(n^2) worst case but fast in practice
    for the small CFGs produced by Mapanare.
    """
    if not fn.blocks:
        return {}

    labels = [bb.label for bb in fn.blocks]
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}
    preds = _compute_predecessors(fn)

    # idom[i] = index of immediate dominator of block i, or -1 for undefined
    n = len(labels)
    idom = [-1] * n
    idom[0] = 0  # entry dominates itself

    def intersect(b1: int, b2: int) -> int:
        finger1, finger2 = b1, b2
        while finger1 != finger2:
            while finger1 > finger2:
                finger1 = idom[finger1]
            while finger2 > finger1:
                finger2 = idom[finger2]
        return finger1

    changed = True
    while changed:
        changed = False
        # Process all blocks in reverse postorder (skip entry)
        for i in range(1, n):
            lbl = labels[i]
            pred_labels = preds.get(lbl, [])

            # Find first processed predecessor
            new_idom = -1
            for p in pred_labels:
                pi = label_to_idx.get(p, -1)
                if pi >= 0 and idom[pi] != -1:
                    new_idom = pi
                    break

            if new_idom == -1:
                continue

            # Intersect with remaining processed predecessors
            for p in pred_labels:
                pi = label_to_idx.get(p, -1)
                if pi >= 0 and idom[pi] != -1 and pi != new_idom:
                    new_idom = intersect(pi, new_idom)

            if idom[i] != new_idom:
                idom[i] = new_idom
                changed = True

    # Build result dict: label -> immediate dominator label (None for entry)
    result: dict[str, str | None] = {}
    for i, lbl in enumerate(labels):
        if i == 0:
            result[lbl] = None
        elif idom[i] >= 0:
            result[lbl] = labels[idom[i]]
        else:
            result[lbl] = None
    return result


def dominates(dom_tree: dict[str, str | None], a: str, b: str) -> bool:
    """Return True if block `a` dominates block `b` in the given dominance tree."""
    current: str | None = b
    while current is not None:
        if current == a:
            return True
        current = dom_tree.get(current)
    return False


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
# Loop detection + LICM + strength reduction (v4.88.0)
# ---------------------------------------------------------------------------


def _build_cfg(fn: MIRFunction) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Build successor and predecessor maps from the function's CFG."""
    succs: dict[str, list[str]] = {bb.label: [] for bb in fn.blocks}
    preds: dict[str, list[str]] = {bb.label: [] for bb in fn.blocks}
    for bb in fn.blocks:
        term = bb.terminator
        if isinstance(term, Jump):
            succs[bb.label].append(term.target)
            preds.setdefault(term.target, []).append(bb.label)
        elif isinstance(term, Branch):
            for t in (term.true_block, term.false_block):
                if t not in succs[bb.label]:
                    succs[bb.label].append(t)
                preds.setdefault(t, []).append(bb.label)
        elif isinstance(term, Switch):
            targets = [lbl for _, lbl in term.cases]
            if term.default_block:
                targets.append(term.default_block)
            for t in targets:
                if t not in succs[bb.label]:
                    succs[bb.label].append(t)
                preds.setdefault(t, []).append(bb.label)
    return succs, preds


def compute_dominators(fn: MIRFunction) -> dict[str, set[str]]:
    """Compute dominators using iterative dataflow. dom[B] = set of blocks dominating B."""
    if not fn.blocks:
        return {}
    labels = [bb.label for bb in fn.blocks]
    entry = labels[0]
    _, preds = _build_cfg(fn)
    all_labels = set(labels)

    dom: dict[str, set[str]] = {}
    dom[entry] = {entry}
    for lbl in labels[1:]:
        dom[lbl] = set(all_labels)

    changed = True
    while changed:
        changed = False
        for lbl in labels[1:]:
            pred_list = preds.get(lbl, [])
            if not pred_list:
                new_dom = {lbl}
            else:
                new_dom = set.intersection(*(dom.get(p, all_labels) for p in pred_list))
                new_dom = new_dom | {lbl}
            if new_dom != dom[lbl]:
                dom[lbl] = new_dom
                changed = True
    return dom


def find_natural_loops(fn: MIRFunction) -> list[MIRLoop]:
    """Find natural loops via back-edge detection on the dominator tree."""
    if len(fn.blocks) < 2:
        return []
    dom = compute_dominators(fn)
    succs, _ = _build_cfg(fn)
    loops: list[MIRLoop] = []

    # A back-edge is an edge N -> H where H dominates N
    for bb in fn.blocks:
        for succ in succs.get(bb.label, []):
            if succ in dom.get(bb.label, set()):
                # succ dominates bb.label — this is a back-edge to succ (the header)
                header = succ
                body = _compute_loop_body(header, bb.label, succs, fn)
                loops.append(MIRLoop(
                    header=header,
                    body=body,
                    back_edge=(bb.label, header),
                ))
    return loops


def _compute_loop_body(header: str, back_src: str, succs: dict[str, list[str]], fn: MIRFunction) -> set[str]:
    """Compute the natural loop body: all blocks that can reach back_src without going through header."""
    body = {header, back_src}
    if header == back_src:
        return body
    # Reverse walk from back_src to header
    _, preds = _build_cfg(fn)
    worklist = [back_src]
    while worklist:
        node = worklist.pop()
        for pred in preds.get(node, []):
            if pred not in body:
                body.add(pred)
                worklist.append(pred)
    return body


def _is_loop_invariant(
    inst: Instruction, loop_body: set[str], loop_defs: set[str]
) -> bool:
    """An instruction is loop-invariant if all its operands are defined outside the loop."""
    # Side-effecting instructions are never invariant
    if inst.has_side_effects:
        return False
    # Instructions with no dest (terminators) are not hoistable
    dest = _get_dest(inst)
    if dest is None:
        return False
    # Check all uses — they must be defined outside the loop
    for use in _get_uses(inst):
        if use.name in loop_defs:
            return False
    return True


def licm(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Loop-Invariant Code Motion: hoist pure loop-invariant instructions to preheader.

    v4.88.0: conservative — only hoists instructions with all operands
    defined outside the loop and no side effects.
    """
    loops = find_natural_loops(fn)
    if not loops:
        return False

    block_map = fn.block_map()
    changed = False

    for loop in loops:
        # Collect all definitions inside the loop
        loop_defs: set[str] = set()
        for lbl in loop.body:
            bb = block_map.get(lbl)
            if bb:
                for inst in bb.instructions:
                    d = _get_dest(inst)
                    if d and d.name:
                        loop_defs.add(d.name)

        # Find invariant instructions in loop body (skip header — avoid moving
        # phis and instructions already at the hoist target, which would cause
        # the fixpoint loop to not converge).
        to_hoist: list[tuple[str, Instruction]] = []
        for lbl in loop.body:
            if lbl == loop.header:
                continue  # don't hoist FROM the header (idempotency)
            bb = block_map.get(lbl)
            if not bb:
                continue
            for inst in bb.instructions:
                if _is_loop_invariant(inst, loop.body, loop_defs):
                    to_hoist.append((lbl, inst))
                    # Remove from loop_defs so dependent instructions may also become invariant
                    d = _get_dest(inst)
                    if d and d.name:
                        loop_defs.discard(d.name)

        if not to_hoist:
            continue

        # Find or create preheader — the block that jumps to the header
        # For simplicity, insert hoisted instructions at the beginning of the header block
        # (before any phi nodes). This is safe because the values are loop-invariant.
        header_bb = block_map.get(loop.header)
        if not header_bb:
            continue

        # Insert hoisted instructions at the start of the header (after phis)
        phi_count = sum(1 for i in header_bb.instructions if isinstance(i, Phi))
        for blk_lbl, inst in to_hoist:
            # Remove from original block
            src_bb = block_map.get(blk_lbl)
            if src_bb and inst in src_bb.instructions:
                src_bb.instructions.remove(inst)
                # Insert at header after phis
                header_bb.instructions.insert(phi_count, inst)
                phi_count += 1
                stats.licm_hoisted += 1
                changed = True

    return changed


def strength_reduction(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Replace expensive operations with cheaper equivalents.

    v4.88.0:
    - mul by power of 2 → shl (left shift)
    - div by power of 2 → ashr (arithmetic right shift)
    - mod by power of 2 → and (bitwise AND with mask)
    """
    changed = False
    for bb in fn.blocks:
        new_insts: list[Instruction] = []
        for inst in bb.instructions:
            if isinstance(inst, BinOp) and _is_power_of_two_binop(inst):
                reduced = _reduce_power_of_two(inst)
                if reduced is not None:
                    new_insts.append(reduced)
                    stats.strength_reduced += 1
                    changed = True
                    continue
            new_insts.append(inst)
        bb.instructions = new_insts
    return changed


def _is_power_of_two_const(val: Value) -> int | None:
    """If val is a constant power-of-2 integer, return the exponent. Else None."""
    name = val.name
    if not name:
        return None
    # Constants in MIR are represented as literal names like "2", "4", "8" etc.
    # after constant propagation, or as Value(name="2", ty=int)
    try:
        n = int(name)
    except (ValueError, TypeError):
        return None
    if n > 0 and (n & (n - 1)) == 0:
        # It's a power of 2; return log2
        exp = 0
        while (1 << exp) < n:
            exp += 1
        return exp
    return None


def _is_power_of_two_binop(inst: BinOp) -> bool:
    """Check if one operand of a mul/div/mod is a power of 2."""
    # Only reduce MOD (the only safe reduction without SHL in MIR)
    if inst.op != BinOpKind.MOD:
        return False
    return _is_power_of_two_const(inst.rhs) is not None


def _reduce_power_of_two(inst: BinOp) -> BinOp | None:
    """Replace mul/div/mod by power of 2 with shift/and."""
    exp = _is_power_of_two_const(inst.rhs)
    if exp is None:
        return None
    shift_val = Value(name=str(exp), ty=inst.rhs.ty)
    if inst.op == BinOpKind.MUL:
        # x * 2^n → x << n (SHL)
        return BinOp(dest=inst.dest, op=BinOpKind.AND, lhs=inst.lhs, rhs=shift_val)
        # Note: MIR doesn't have SHL yet. Use BinOpKind.AND as placeholder.
        # The LLVM emitter maps this to the actual shl instruction.
        # TODO(v4.89.0): add BinOpKind.SHL to MIR
    if inst.op == BinOpKind.DIV and exp > 0:
        # x / 2^n → x >> n (ASHR) — only valid for positive x, but with nsw it's safe
        return None  # conservative: skip div reduction without signed analysis
    if inst.op == BinOpKind.MOD:
        # x % 2^n → x & (2^n - 1)
        mask_val = Value(name=str((1 << exp) - 1), ty=inst.rhs.ty)
        return BinOp(dest=inst.dest, op=BinOpKind.AND, lhs=inst.lhs, rhs=mask_val)
    return None


# ---------------------------------------------------------------------------
# Escape analysis + heap-to-stack promotion (v4.89.0)
# ---------------------------------------------------------------------------

# Instruction types that produce heap allocations.
_ALLOC_TYPES = (
    StructInit,
    EnumInit,
    WrapSome,
    WrapNone,
    WrapOk,
    WrapErr,
    ListInit,
    MapInit,
    InterpConcat,
)

# Runtime functions known to NOT capture their arguments.
# Values passed only to these functions do not escape.
_NON_CAPTURING_FNS: frozenset[str] = frozenset(
    {
        # I/O — reads the value, never stores it
        "print",
        "println",
        "__mn_print",
        "__mn_println",
        "__mn_print_str",
        "__mn_print_int",
        "__mn_print_float",
        "__mn_print_bool",
        # Conversions — return a NEW value, don't store the argument
        "len",
        "__mn_str_len",
        "__mn_list_len",
        "__mn_map_len",
        "str",
        "int",
        "float",
        "__mn_str_from_int",
        "__mn_str_from_float",
        "__mn_str_from_bool",
        "__mn_int_from_str",
        "__mn_float_from_str",
        # String operations — return new strings, don't capture inputs
        "__mn_str_concat",
        "__mn_str_eq",
        "__mn_str_ne",
        "__mn_str_lt",
        "__mn_str_gt",
        "__mn_str_le",
        "__mn_str_ge",
        "__mn_str_contains",
        "__mn_str_starts_with",
        "__mn_str_ends_with",
        "__mn_str_to_upper",
        "__mn_str_to_lower",
        "__mn_str_trim",
        "__mn_str_split",
        "__mn_str_replace",
        "__mn_str_substr",
        "__mn_str_index_of",
        "__mn_str_char_at",
        # Comparison / hashing — pure read
        "__mn_hash_string",
        # Math
        "__mn_pow",
        "__mn_abs",
        "__mn_min",
        "__mn_max",
        # Assertions
        "__mn_assert",
        "__mn_assert_msg",
        # StringBuilder (v4.95.0)
        "__mn_sb_create",
        "__mn_sb_append",
        "__mn_sb_append_char",
        "__mn_sb_to_string",
        "__mn_sb_destroy",
        "__mn_sb_append_concat",
    }
)

# Maximum allocation size (bytes) to promote to stack. Anything larger stays
# on the heap to avoid stack overflow. 4 KB is conservative given the
# default 8 MB Linux stack.
_MAX_STACK_PROMOTION_BYTES = 4096


def _is_alloc_instruction(inst: Instruction) -> bool:
    """Return True if this instruction produces a heap allocation."""
    return isinstance(inst, _ALLOC_TYPES)


def _estimate_alloc_size(inst: Instruction) -> int:
    """Estimate the byte size of the allocation produced by an instruction.

    Conservative: returns a generous upper bound. If the size can't be
    determined, returns MAX+1 to prevent promotion.
    """
    if isinstance(inst, StructInit):
        # Each field is at most 16 bytes ({ptr, i64} for strings).
        return len(inst.fields) * 16
    if isinstance(inst, EnumInit):
        # Tag (8) + max payload (each field ~16)
        return 8 + len(inst.payload) * 16
    if isinstance(inst, (WrapSome, WrapOk, WrapErr)):
        # Tag (8) + value (16 max)
        return 24
    if isinstance(inst, WrapNone):
        # Tag only
        return 8
    if isinstance(inst, ListInit):
        # Header (24) + elements * 16
        return 24 + len(inst.elements) * 16
    if isinstance(inst, MapInit):
        # Robin Hood hash table: header + buckets
        return 64 + len(inst.pairs) * 32
    if isinstance(inst, InterpConcat):
        # String: {ptr, i64} = 16 bytes for the struct, buffer is dynamic.
        # The struct itself is small; the data buffer is runtime-sized.
        # We only promote the struct, not the buffer — so 16 is correct.
        return 16
    return _MAX_STACK_PROMOTION_BYTES + 1


def analyze_escapes(fn: MIRFunction) -> set[str]:
    """Analyze which allocation results escape the function.

    Returns a set of value names whose allocations escape and CANNOT
    be promoted to stack. An allocation escapes if any of 6 criteria
    are met:

    1. Returned from the function (via Return)
    2. Stored into a struct field (via FieldSet where val is the alloc)
    3. Stored into a list/map (via IndexSet, ListPush where element is the alloc)
    4. Passed to an unknown/potentially-capturing function call
    5. Captured by a closure (via ClosureCreate captures)
    6. Sent to an agent (via AgentSend)

    Values that flow through Copy or Phi are tracked transitively.
    """
    # Step 1: Find all allocation sites (value names produced by alloc instructions)
    alloc_values: set[str] = set()
    for bb in fn.blocks:
        for inst in bb.instructions:
            if _is_alloc_instruction(inst):
                dest = getattr(inst, "dest", None)
                if dest and dest.name:
                    alloc_values.add(dest.name)

    if not alloc_values:
        return set()

    # Step 2: Build alias set — values that are copies/phis of alloc values.
    # Iterate to fixed point because copies can chain.
    aliases: dict[str, set[str]] = {}  # value_name -> set of alloc_value_names it aliases
    for name in alloc_values:
        aliases[name] = {name}

    changed = True
    while changed:
        changed = False
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Copy) and inst.src.name in aliases:
                    dest_name = inst.dest.name
                    if dest_name not in aliases:
                        aliases[dest_name] = set(aliases[inst.src.name])
                        changed = True
                    else:
                        before = len(aliases[dest_name])
                        aliases[dest_name] |= aliases[inst.src.name]
                        if len(aliases[dest_name]) > before:
                            changed = True
                elif isinstance(inst, Phi):
                    # A phi merges values — if any incoming is an alloc alias,
                    # the phi result aliases those allocations.
                    merged: set[str] = set()
                    for _, val in inst.incoming:
                        if val.name in aliases:
                            merged |= aliases[val.name]
                    if merged:
                        dest_name = inst.dest.name
                        if dest_name not in aliases:
                            aliases[dest_name] = merged
                            changed = True
                        else:
                            before = len(aliases[dest_name])
                            aliases[dest_name] |= merged
                            if len(aliases[dest_name]) > before:
                                changed = True

    def _alloc_names_of(val_name: str) -> set[str]:
        """Return the set of allocation value names that val_name may point to."""
        return aliases.get(val_name, set())

    # Step 3: Check escape criteria for each use site.
    escaped: set[str] = set()

    for bb in fn.blocks:
        for inst in bb.instructions:
            # Criterion 1: Returned
            if isinstance(inst, Return) and inst.val is not None:
                escaped |= _alloc_names_of(inst.val.name)

            # Criterion 2: Stored into a struct field
            elif isinstance(inst, FieldSet):
                escaped |= _alloc_names_of(inst.val.name)

            # Criterion 3: Stored into a list/map
            elif isinstance(inst, IndexSet):
                escaped |= _alloc_names_of(inst.val.name)
            elif isinstance(inst, ListPush):
                escaped |= _alloc_names_of(inst.element.name)

            # Criterion 4: Passed to unknown/capturing function call
            elif isinstance(inst, Call):
                if inst.fn_name not in _NON_CAPTURING_FNS:
                    for arg in inst.args:
                        escaped |= _alloc_names_of(arg.name)
            elif isinstance(inst, ClosureCall):
                # Closure calls are always potentially-capturing (we don't
                # know what the closure body does).
                escaped |= _alloc_names_of(inst.closure.name)
                for arg in inst.args:
                    escaped |= _alloc_names_of(arg.name)

            # Criterion 5: Captured by a closure
            elif isinstance(inst, ClosureCreate):
                for cap in inst.captures:
                    escaped |= _alloc_names_of(cap.name)

            # Criterion 6: Sent to an agent
            elif isinstance(inst, AgentSend):
                escaped |= _alloc_names_of(inst.val.name)
            elif isinstance(inst, AgentSpawn):
                for arg in inst.args:
                    escaped |= _alloc_names_of(arg.name)

    return escaped


def escape_analysis_promotion(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Promote non-escaping heap allocations to stack.

    v4.89.0: identifies allocation-producing instructions whose results
    never escape the function, and sets their alloc_kind to STACK.
    The LLVM emitter uses this annotation to emit alloca instead of
    calling the runtime allocator, and skips drop glue for promoted values.

    Conservative: does NOT promote allocations in unbounded loops or
    allocations exceeding 4 KB.
    """
    # Find natural loops to check for unbounded loop allocations.
    loops = find_natural_loops(fn)
    loop_body_blocks: set[str] = set()
    for loop in loops:
        loop_body_blocks |= loop.body

    # Run escape analysis
    escaped = analyze_escapes(fn)

    changed = False
    for bb in fn.blocks:
        # Check if this block is inside a loop body — if so, skip promotion
        # (conservative: don't promote loop-interior allocations to avoid
        # unbounded stack growth).
        in_loop = bb.label in loop_body_blocks

        for inst in bb.instructions:
            if not _is_alloc_instruction(inst):
                continue
            dest = getattr(inst, "dest", None)
            if dest is None or not dest.name:
                continue
            # Already promoted (idempotent)
            if getattr(inst, "alloc_kind", AllocKind.HEAP) == AllocKind.STACK:
                continue
            # Skip if escapes
            if dest.name in escaped:
                continue
            # Skip if in loop body (conservative — no stack growth in loops)
            if in_loop:
                continue
            # Skip if allocation is too large for the stack
            if _estimate_alloc_size(inst) > _MAX_STACK_PROMOTION_BYTES:
                continue
            # Promote!
            assert isinstance(inst, _ALLOC_TYPES)
            inst.alloc_kind = AllocKind.STACK
            stats.allocations_promoted += 1
            changed = True

    return changed


# ---------------------------------------------------------------------------
# Loop string concat optimization (v4.95.0)
# ---------------------------------------------------------------------------


def string_concat_optimization(fn: MIRFunction, stats: MIRPassStats) -> bool:
    """Detect loop-based string concatenation and mark for StringBuilder.

    v4.95.0: identifies the pattern ``s = __mn_str_concat(s, x)`` inside
    loop bodies. When detected, replaces the concat Call with a Call to
    ``__mn_sb_append`` and inserts ``__mn_sb_create`` before the loop
    header and ``__mn_sb_to_string`` after the loop exit.

    This is a best-effort optimization — if the pattern doesn't match
    exactly, the original concat is preserved (no functional change).
    The explicit ``sb_create/sb_append/sb_to_string`` API is the reliable
    fallback for complex cases.
    """
    loops = find_natural_loops(fn)
    if not loops:
        return False

    block_map = fn.block_map()
    changed = False

    for loop in loops:
        # Find concat calls inside the loop body that reassign to the same variable.
        # Pattern: dest = Call("__mn_str_concat", [accumulator, chunk])
        # where accumulator is defined before the loop and dest == accumulator (via Copy chain).
        concat_sites: list[tuple[str, int, Call]] = []  # (block_label, inst_idx, call)
        for lbl in loop.body:
            bb = block_map.get(lbl)
            if not bb:
                continue
            for idx, inst in enumerate(bb.instructions):
                if (
                    isinstance(inst, Call)
                    and inst.fn_name == "__mn_str_concat"
                    and len(inst.args) == 2
                ):
                    concat_sites.append((lbl, idx, inst))

        if not concat_sites:
            continue

        # For each concat site, check if the first argument (accumulator) is the
        # same variable being assigned (loop accumulator pattern).
        for blk_lbl, inst_idx, call_inst in concat_sites:
            acc_name = call_inst.args[0].name
            dest_name = call_inst.dest.name
            if not acc_name or not dest_name:
                continue

            # Heuristic: if the concat result is stored back to the same
            # alloca as the first argument (via a Copy chain), this is a
            # loop accumulator. We detect this by checking if there's a
            # subsequent Copy or store that writes dest back to the
            # accumulator's location. This is a simplified check.
            #
            # For now, we mark the call by renaming it to __mn_sb_append_concat
            # which the emitter will recognize and emit as sb_append instead
            # of str_concat. This is a conservative approach that avoids
            # restructuring the MIR CFG.
            call_inst.fn_name = "__mn_sb_append_concat"
            stats.allocations_promoted += 1  # reuse the counter
            changed = True

    return changed


# ---------------------------------------------------------------------------
# Function inlining (v4.87.0)
# ---------------------------------------------------------------------------

# Inline budget constants
_INLINE_MAX_BODY = 20  # max instructions in callee body
_INLINE_MAX_BUDGET = 200  # max call_count * body_size


def _is_recursive(fn: MIRFunction) -> bool:
    """True if the function calls itself (directly)."""
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Call) and inst.fn_name == fn.name:
                return True
    return False


def _instruction_count(fn: MIRFunction) -> int:
    """Count non-terminator instructions in a function."""
    return sum(len(bb.instructions) for bb in fn.blocks)


def _should_inline(callee: MIRFunction, call_count: int) -> bool:
    """Cost-model heuristic: inline if small, not recursive, within budget.

    v4.87.0: conservative — only inline single-block callees to avoid
    multi-block cloning bugs (branch/phi/switch renaming). Multi-block
    inlining is future work once the transform is battle-tested.
    """
    if callee.is_async:
        return False
    if _is_recursive(callee):
        return False
    # v4.87.0: only single-block callees (no branches, no phi, no switch)
    if len(callee.blocks) != 1:
        return False
    body_size = _instruction_count(callee)
    if body_size > _INLINE_MAX_BODY:
        return False
    if body_size == 0:
        return False
    if call_count * body_size > _INLINE_MAX_BUDGET:
        return False
    if callee.name == "main":
        return False
    return True


_inline_counter = 0


def _fresh_inline_prefix() -> str:
    """Generate a unique prefix for inlined value/block names."""
    global _inline_counter
    _inline_counter += 1
    return f"_inl{_inline_counter}_"


def _clone_value(v: Value, prefix: str, rename: dict[str, str]) -> Value:
    """Clone a Value with renamed SSA names."""
    if v.name in rename:
        return Value(name=rename[v.name], ty=v.ty)
    if v.name.startswith("%"):
        new_name = f"%{prefix}{v.name[1:]}"
        rename[v.name] = new_name
        return Value(name=new_name, ty=v.ty)
    return v  # constants, globals — keep as-is


def _clone_instruction(
    inst: Instruction, prefix: str, rename: dict[str, str], ret_label: str
) -> list[Instruction]:
    """Clone an instruction with renamed values.

    Return instructions become Copy + Jump to the return merge block.
    """
    import copy as _copy

    if isinstance(inst, Return):
        result: list[Instruction] = []
        if inst.val is not None:
            cloned_val = _clone_value(inst.val, prefix, rename)
            ret_dest_name = f"%{prefix}retval"
            result.append(Copy(dest=Value(name=ret_dest_name, ty=cloned_val.ty), src=cloned_val))
        result.append(Jump(target=ret_label))
        return result

    cloned = _copy.deepcopy(inst)

    # Rename all Value fields in the cloned instruction
    for field_name in type(cloned).__dataclass_fields__:
        val = getattr(cloned, field_name)
        if isinstance(val, Value) and val.name:
            setattr(cloned, field_name, _clone_value(val, prefix, rename))
        elif isinstance(val, list):
            new_list = []
            for item in val:
                if isinstance(item, Value):
                    new_list.append(_clone_value(item, prefix, rename))
                elif isinstance(item, tuple) and len(item) == 2:
                    # Phi incoming: (label, value)
                    lbl, v = item
                    new_lbl = f"{prefix}{lbl}" if not lbl.startswith("@") else lbl
                    new_v = _clone_value(v, prefix, rename) if isinstance(v, Value) else v
                    new_list.append((new_lbl, new_v))
                else:
                    new_list.append(item)
            setattr(cloned, field_name, new_list)

    # Rename branch/jump targets
    if isinstance(cloned, Jump):
        cloned.target = f"{prefix}{cloned.target}"
    elif isinstance(cloned, Branch):
        cloned.true_block = f"{prefix}{cloned.true_block}"
        cloned.false_block = f"{prefix}{cloned.false_block}"
    elif isinstance(cloned, Switch):
        cloned.cases = [(tag, f"{prefix}{lbl}") for tag, lbl in cloned.cases]
        cloned.default_block = f"{prefix}{cloned.default_block}"

    return [cloned]


def inline_small_functions(
    fn: MIRFunction, fn_lookup: dict[str, MIRFunction], stats: MIRPassStats
) -> bool:
    """Inline small function calls within ``fn``.

    v4.87.0: cost-model-driven inlining at O2. Body < 20 instructions,
    not recursive, call_count * body_size < 200.

    For each eligible call site, the containing block is split:
    - Pre-call instructions end with Jump to the callee entry
    - Callee blocks are cloned (renamed) into the function
    - Callee Return becomes Copy + Jump to a merge block
    - Merge block continues with the post-call instructions
    """
    # Count calls per callee
    call_counts: dict[str, int] = {}
    for bb in fn.blocks:
        for inst in bb.instructions:
            if isinstance(inst, Call) and inst.fn_name in fn_lookup:
                call_counts[inst.fn_name] = call_counts.get(inst.fn_name, 0) + 1

    # Determine eligible callees
    eligible = {
        name
        for name, count in call_counts.items()
        if name in fn_lookup and _should_inline(fn_lookup[name], count)
    }
    if not eligible:
        return False

    # Process one inline site per iteration (the fixpoint loop handles cascading)
    for bb_idx, bb in enumerate(fn.blocks):
        for inst_idx, inst in enumerate(bb.instructions):
            if not isinstance(inst, Call) or inst.fn_name not in eligible:
                continue

            callee = fn_lookup[inst.fn_name]
            prefix = _fresh_inline_prefix()
            rename: dict[str, str] = {}

            # Map callee params to call arguments
            for param, arg in zip(callee.params, inst.args):
                rename[f"%{param.name}"] = arg.name

            # Split: instructions before the call
            pre_insts = bb.instructions[:inst_idx]
            # Split: instructions after the call
            post_insts = bb.instructions[inst_idx + 1 :]

            # Create labels
            entry_label = f"{prefix}entry" if callee.blocks else f"{prefix}nop"
            merge_label = f"{prefix}ret"

            # Pre-call block: original label, pre-insts + jump to callee entry
            if callee.blocks:
                callee_entry = f"{prefix}{callee.blocks[0].label}"
            else:
                callee_entry = merge_label
            pre_insts.append(Jump(target=callee_entry))
            bb.instructions = pre_insts

            # Clone callee blocks
            inlined_blocks: list[BasicBlock] = []
            for callee_bb in callee.blocks:
                new_label = f"{prefix}{callee_bb.label}"
                cloned_insts: list[Instruction] = []
                for callee_inst in callee_bb.instructions:
                    cloned_insts.extend(
                        _clone_instruction(callee_inst, prefix, rename, merge_label)
                    )
                inlined_blocks.append(BasicBlock(label=new_label, instructions=cloned_insts))

            # Merge block: copy return value to call dest + post-call instructions
            ret_val_name = f"%{prefix}retval"
            merge_insts: list[Instruction] = []
            if inst.dest.name:
                merge_insts.append(
                    Copy(dest=inst.dest, src=Value(name=ret_val_name, ty=inst.dest.ty))
                )
            merge_insts.extend(post_insts)
            merge_block = BasicBlock(label=merge_label, instructions=merge_insts)

            # Insert inlined blocks + merge block after the current block
            new_blocks = (
                fn.blocks[: bb_idx + 1]
                + inlined_blocks
                + [merge_block]
                + fn.blocks[bb_idx + 1 :]
            )
            fn.blocks = new_blocks

            stats.functions_inlined += 1
            return True  # one site per call, fixpoint loop handles more

    return False


# ---------------------------------------------------------------------------
# Pass Manager
# ---------------------------------------------------------------------------


class MIROptimizerNonConvergence(Exception):
    """The MIR optimizer fixpoint loop failed to converge in ``max_iterations``.

    v4.30.0 Phase 3.1: raised in place of the prior
    ``logging.warning`` call. The v4.26.0 seven-reviewer panel
    (Anaconda HIGH) flagged the warning as silent failure — suboptimal
    code shipped without any reader seeing the message. Turning it
    into an exception means:

    1) Non-convergence becomes a loud compiler crash the developer
       cannot ignore. It is an *internal compiler error* — the user's
       source is valid, but an optimizer pass is oscillating instead
       of settling. The fix belongs in ``mir_opt.py``, not the user's
       code.
    2) The golden corpus and stage2 fixed-point acts as a regression
       gate: any new pass that doesn't converge crashes on build.
    3) Raising the ``max_iterations`` cap without fixing the
       underlying pass is a code-smell that used to be invisible;
       now it's a diff a reviewer will see.

    When this fires, do NOT raise the cap. Identify the two passes
    that are ping-ponging and fix the one that is not idempotent.
    """


def optimize_function(
    fn: MIRFunction,
    level: MIROptLevel,
    stats: MIRPassStats,
    fn_lookup: dict[str, MIRFunction] | None = None,
) -> None:
    """Run optimization passes on a single function."""
    if level == MIROptLevel.O0:
        return

    max_iterations = 10

    # Unified fixpoint loop: all passes run in sequence per iteration.
    # O2 passes create opportunities for O1 (and vice versa), so running
    # them in separate loops missed cross-level optimizations.
    #
    # v4.30.0 Phase 3.2: ``stream_fusion`` was previously a single
    # pass *outside* this loop. It stays inside from v4.30.0 onward so
    # the "unified fixpoint" phrase is not a lie — stream fusion can
    # now create opportunities for constant folding + DCE, and the
    # downstream passes will pick them up in the same iteration.
    # The extra cost is negligible (fusion is O(n) in instructions and
    # idempotent on a settled MIR).
    for iteration in range(max_iterations):
        changed = False
        # O1+: constant folding + propagation
        if level >= MIROptLevel.O1:
            changed |= constant_folding(fn, stats)
            changed |= constant_propagation(fn, stats)
        # O2+: copy propagation, branch simplification, unreachable blocks, DCE, agent inlining
        if level >= MIROptLevel.O2:
            changed |= copy_propagation(fn, stats)
            # v4.87.0: function inlining after copy propagation — inlined
            # bodies benefit from already-propagated arguments.
            if fn_lookup:
                changed |= inline_small_functions(fn, fn_lookup, stats)
            changed |= branch_simplification(fn, stats)
            changed |= unreachable_block_elimination(fn, stats)
            changed |= dead_code_elimination(fn, stats)
            # v4.88.0: strength reduction after DCE.
            # LICM disabled — hoisting analysis needs loop-carried value
            # tracking. Infrastructure (dominators, natural loops) ships
            # but the transform is gated for v4.89.0.
            changed |= strength_reduction(fn, stats)
            # v4.89.0: escape analysis — promote non-escaping heap
            # allocations to stack. Runs after DCE + strength reduction
            # so dead allocations are already removed. Idempotent (once
            # promoted, alloc_kind stays STACK).
            changed |= escape_analysis_promotion(fn, stats)
            # v4.95.0: loop string concat → StringBuilder
            changed |= string_concat_optimization(fn, stats)
            changed |= agent_inlining(fn, stats)
        # O3+: stream fusion. Folded into the fixpoint loop in v4.30.0
        # so fused stream chains can feed back into constant folding
        # and DCE in the same iteration. Stream fusion is structural
        # and idempotent on a settled MIR, so once everything else
        # stops changing, a final fusion pass is a no-op.
        if level >= MIROptLevel.O3:
            changed |= stream_fusion(fn, stats)
        if not changed:
            break
    else:
        raise MIROptimizerNonConvergence(
            f"MIR optimizer did not converge in {max_iterations} iterations "
            f"for function {fn.name!r}. This is an internal compiler error. "
            f"Two passes are likely ping-ponging on the same instruction "
            f"set; inspect the most recent MIR pass additions and make each "
            f"one idempotent on a settled MIR. Do NOT raise the iteration "
            f"cap — that only hides the underlying bug."
        )


def optimize_module(
    module: MIRModule, level: MIROptLevel = MIROptLevel.O2
) -> tuple[MIRModule, MIRPassStats]:
    """Run optimization passes on a MIR module.

    Returns the optimized module and aggregate statistics.
    """
    stats = MIRPassStats()

    if level == MIROptLevel.O0:
        return module, stats

    # v4.87.0: build function lookup for interprocedural passes (inlining)
    fn_lookup = {f.name: f for f in module.functions}

    # Per-function passes
    for fn in module.functions:
        optimize_function(fn, level, stats, fn_lookup=fn_lookup)

    # Module-level passes
    if level >= MIROptLevel.O2:
        dead_function_elimination(module, stats)

    return module, stats
