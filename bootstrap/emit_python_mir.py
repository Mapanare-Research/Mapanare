"""Python code emitter that consumes MIR (not AST).

Reconstructs structured control flow from basic blocks and emits
idiomatic Python source with asyncio agents, reactive signals, and
async streams.
"""

from __future__ import annotations

from typing import Any

from mapanare.mir import (
    TERMINATOR_TYPES,
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Call,
    Cast,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    ExternCall,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    SignalSet,
    StreamOp,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
)
from mapanare.types import BUILTIN_CALL_MAP, PYTHON_TYPE_MAP, TypeKind


class PythonMIREmitter:
    """Emits Python source code from a MIR module.

    Reconstructs structured control flow (if/else, while, match) from
    basic blocks, resolves phi nodes by inserting assignments in
    predecessor blocks, and maps MIR instructions to Python constructs.
    """

    def __init__(self, python_path: list[str] | None = None) -> None:
        self._indent: int = 0
        self._lines: list[str] = []
        # Per-function state
        self._block_map: dict[str, BasicBlock] = {}
        self._visited: set[str] = set()
        self._loop_headers: set[str] = set()
        # Feature flags
        self._has_agents: bool = False
        self._has_result: bool = False
        self._has_option: bool = False
        self._has_signal: bool = False
        self._has_stream: bool = False
        self._has_traits: bool = False
        # Set of async function names
        self._async_fns: set[str] = set()
        # Extern Python modules to import
        self._extern_modules: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit(self, module: MIRModule) -> str:
        """Emit a complete Python source file from a MIR module."""
        self._lines = []
        self._scan_features(module)
        self._detect_async_fns(module)
        self._emit_header(module)
        self._emit_structs(module)
        self._emit_enums(module)
        self._emit_traits(module)
        self._emit_agents(module)
        self._emit_pipes(module)
        self._emit_functions(module)
        self._emit_main_guard(module)
        return "\n".join(self._lines) + "\n"

    # ------------------------------------------------------------------
    # Feature scanning
    # ------------------------------------------------------------------

    def _scan_features(self, module: MIRModule) -> None:
        """Scan MIR instructions to determine which runtime imports are needed."""
        self._has_agents = bool(module.agents)
        self._has_traits = bool(module.trait_names)
        self._extern_modules = set()

        for fn in module.functions:
            for bb in fn.blocks:
                for inst in bb.instructions:
                    if isinstance(inst, (AgentSpawn, AgentSend, AgentSync)):
                        self._has_agents = True
                    elif isinstance(inst, (SignalInit, SignalGet, SignalSet)):
                        self._has_signal = True
                    elif isinstance(inst, StreamOp):
                        self._has_stream = True
                    elif isinstance(inst, (WrapOk, WrapErr, Unwrap)):
                        self._has_result = True
                    elif isinstance(inst, WrapSome):
                        self._has_option = True
                    elif isinstance(inst, WrapNone):
                        self._has_option = True
                    elif isinstance(inst, ExternCall):
                        if inst.abi == "Python" and inst.module:
                            self._extern_modules.add(inst.module)

    def _detect_async_fns(self, module: MIRModule) -> None:
        """Detect which functions need to be async."""
        self._async_fns = set()
        for fn in module.functions:
            if self._fn_needs_async(fn):
                self._async_fns.add(fn.name)

    def _fn_needs_async(self, fn: MIRFunction) -> bool:
        """Return True if the function should be emitted as async def."""
        if fn.name == "main":
            return True
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, (AgentSpawn, AgentSend, AgentSync)):
                    return True
        return False

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _emit_header(self, module: MIRModule) -> None:
        """Emit the file header with imports."""
        self._emit_line("# Generated by mapa -- do not edit")
        self._emit_line("from __future__ import annotations")
        self._emit_line("")

        if self._has_traits:
            self._emit_line("from typing import Protocol")
            self._emit_line("")

        if self._has_agents:
            self._emit_line("import asyncio")
            self._emit_line("")
            self._emit_line("from runtime.agent import AgentBase, Channel")

        if self._has_signal:
            self._emit_line("from runtime.signal import Signal")

        if self._has_stream:
            self._emit_line("from runtime.stream import Stream")
            self._emit_line("")
            self._emit_line("stream = Stream.from_iter")

        if self._has_result:
            self._emit_line("from runtime.result import Ok, Err, unwrap_or_return, _EarlyReturn")

        if self._has_option:
            self._emit_line("from runtime.result import Some")

        # Imports from module.imports
        for path, items in module.imports:
            mod_path = ".".join(path)
            if items:
                item_list = ", ".join(items)
                self._emit_line(f"from {mod_path} import {item_list}")
            else:
                self._emit_line(f"import {mod_path}")

        # Extern Python modules
        for mod in sorted(self._extern_modules):
            self._emit_line(f"import {mod}")

        self._emit_line("")
        self._emit_line("println = print")
        self._emit_line("")
        self._emit_line("")
        self._emit_line("def _mn_div(a, b):")
        self._indent += 1
        self._emit_line("if isinstance(a, float) or isinstance(b, float):")
        self._indent += 1
        self._emit_line("return a / b")
        self._indent -= 1
        self._emit_line("return int(a / b)")
        self._indent -= 1
        self._emit_line("")
        self._emit_line("")
        # Iteration wrapper for MIR for-loop lowering
        self._emit_line("")
        self._emit_line("class _MnIter:")
        self._indent += 1
        self._emit_line("__slots__ = ('_it', '_next')")
        self._emit_line("def __init__(self, iterable):")
        self._indent += 1
        self._emit_line("self._it = iter(iterable)")
        self._emit_line("self._next = None")
        self._indent -= 1
        self._indent -= 1
        self._emit_line("")
        self._emit_line("_mn_iters: dict = {}")
        self._emit_line("")
        self._emit_line("")
        self._emit_line("def __iter_has_next(it):")
        self._indent += 1
        self._emit_line("k = id(it)")
        self._emit_line("if k not in _mn_iters:")
        self._indent += 1
        self._emit_line("_mn_iters[k] = _MnIter(it)")
        self._indent -= 1
        self._emit_line("w = _mn_iters[k]")
        self._emit_line("try:")
        self._indent += 1
        self._emit_line("w._next = next(w._it)")
        self._emit_line("return True")
        self._indent -= 1
        self._emit_line("except StopIteration:")
        self._indent += 1
        self._emit_line("del _mn_iters[k]")
        self._emit_line("return False")
        self._indent -= 1
        self._indent -= 1
        self._emit_line("")
        self._emit_line("")
        self._emit_line("def __iter_next(it):")
        self._indent += 1
        self._emit_line("return _mn_iters[id(it)]._next")
        self._indent -= 1
        self._emit_line("")

    # ------------------------------------------------------------------
    # Structs
    # ------------------------------------------------------------------

    def _emit_structs(self, module: MIRModule) -> None:
        """Emit struct definitions as Python classes."""
        for name, fields in module.structs.items():
            self._emit_line("")
            self._emit_line(f"class {name}:")
            self._indent += 1
            # __init__
            params = ", ".join(f"{fname}=None" for fname, _ in fields)
            self._emit_line(f"def __init__(self, {params}):")
            self._indent += 1
            if fields:
                for fname, _ in fields:
                    self._emit_line(f"self.{fname} = {fname}")
            else:
                self._emit_line("pass")
            self._indent -= 1
            # __repr__
            self._emit_line("")
            self._emit_line("def __repr__(self):")
            self._indent += 1
            if fields:
                field_strs = ", ".join(f"{fname}={{self.{fname}!r}}" for fname, _ in fields)
                self._emit_line(f'return f"{name}({field_strs})"')
            else:
                self._emit_line(f'return "{name}()"')
            self._indent -= 1
            self._indent -= 1
            self._emit_line("")

    # ------------------------------------------------------------------
    # Enums
    # ------------------------------------------------------------------

    def _emit_enums(self, module: MIRModule) -> None:
        """Emit enum definitions as variant classes."""
        for enum_name, variants in module.enums.items():
            for variant_name, payload_types in variants:
                cls_name = f"{enum_name}_{variant_name}"
                self._emit_line("")
                self._emit_line(f"class {cls_name}:")
                self._indent += 1
                # __match_args__
                n_fields = len(payload_types)
                if n_fields > 0:
                    field_names = [f"_f{i}" for i in range(n_fields)]
                    match_args = ", ".join(f'"{f}"' for f in field_names)
                    self._emit_line(f"__match_args__ = ({match_args},)")
                    # __init__
                    params = ", ".join(field_names)
                    self._emit_line(f"def __init__(self, {params}):")
                    self._indent += 1
                    for f in field_names:
                        self._emit_line(f"self.{f} = {f}")
                    self._indent -= 1
                else:
                    self._emit_line("__match_args__ = ()")
                    self._emit_line("def __init__(self):")
                    self._indent += 1
                    self._emit_line("pass")
                    self._indent -= 1
                # __repr__
                self._emit_line("")
                self._emit_line("def __repr__(self):")
                self._indent += 1
                if n_fields > 0:
                    field_strs = ", ".join(
                        f"{{self.{f}!r}}" for f in [f"_f{i}" for i in range(n_fields)]
                    )
                    self._emit_line(f'return f"{cls_name}({field_strs})"')
                else:
                    self._emit_line(f'return "{cls_name}()"')
                self._indent -= 1
                self._indent -= 1
                self._emit_line("")

    # ------------------------------------------------------------------
    # Traits
    # ------------------------------------------------------------------

    def _emit_traits(self, module: MIRModule) -> None:
        """Emit trait names as Protocol stubs."""
        for trait_name in module.trait_names:
            self._emit_line("")
            self._emit_line(f"class {trait_name}(Protocol):")
            self._indent += 1
            self._emit_line("...")
            self._indent -= 1
            self._emit_line("")

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def _emit_agents(self, module: MIRModule) -> None:
        """Emit agent class definitions from MIRAgentInfo metadata."""
        for agent_name, info in module.agents.items():
            self._emit_line("")
            self._emit_line(f"class {agent_name}(AgentBase):")
            self._indent += 1

            # __init__
            self._emit_line("def __init__(self):")
            self._indent += 1
            self._emit_line("super().__init__()")
            for ch in info.inputs:
                self._emit_line(f"self.{ch} = Channel()")
            for ch in info.outputs:
                if ch not in info.inputs:
                    self._emit_line(f"self.{ch} = Channel()")
            for state_name, state_val in info.state:
                self._emit_line(f"self.{state_name} = {_py_literal(state_val)}")
            if not info.inputs and not info.outputs and not info.state:
                self._emit_line("pass")
            self._indent -= 1

            # spawn classmethod
            self._emit_line("")
            self._emit_line("@classmethod")
            self._emit_line("async def spawn(cls, *args):")
            self._indent += 1
            self._emit_line("instance = cls()")
            self._emit_line("await instance.start()")
            self._emit_line("return instance")
            self._indent -= 1

            self._indent -= 1
            self._emit_line("")

    # ------------------------------------------------------------------
    # Pipes
    # ------------------------------------------------------------------

    def _emit_pipes(self, module: MIRModule) -> None:
        """Emit pipe definitions as async pipeline functions."""
        for pipe_name, info in module.pipes.items():
            self._emit_line("")
            self._emit_line(f"async def {pipe_name}(input_data):")
            self._indent += 1
            if not info.stages:
                self._emit_line("return input_data")
            else:
                self._emit_line("data = input_data")
                for stage in info.stages:
                    self._emit_line(f"agent = await {stage}.spawn()")
                    self._emit_line("await agent.input.send(data)")
                    self._emit_line("data = await agent.output.receive()")
                self._emit_line("return data")
            self._indent -= 1
            self._emit_line("")

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def _emit_functions(self, module: MIRModule) -> None:
        """Emit all MIR functions as Python functions."""
        # Collect agent method names to skip top-level emission
        agent_methods: set[str] = set()
        for info in module.agents.values():
            agent_methods.update(info.method_names)

        for fn in module.functions:
            if fn.name in agent_methods:
                continue
            self._emit_function(fn)

    def _emit_function(self, fn: MIRFunction) -> None:
        """Emit a single MIR function."""
        if not fn.blocks:
            return

        # Build block map and detect loop headers
        self._block_map = fn.block_map()
        self._visited = set()
        self._loop_headers = self._find_loop_headers(fn)

        # Function signature
        fn_name = fn.name.lstrip("%")
        params = ", ".join(p.name.lstrip("%") for p in fn.params)
        is_async = fn.name in self._async_fns
        prefix = "async def" if is_async else "def"

        self._emit_line("")
        for dec in fn.decorators:
            if dec == "test":
                continue  # @test is a Mapanare test marker, not a Python decorator
            self._emit_line(f"@{dec}")
        self._emit_line(f"{prefix} {fn_name}({params}):")
        self._indent += 1

        # Wrap body in try/except for _EarlyReturn if function uses unwrap
        needs_early_return = self._fn_uses_unwrap(fn)
        if needs_early_return:
            self._emit_line("try:")
            self._indent += 1

        # Emit the entry block region
        entry = fn.blocks[0].label
        self._emit_region(entry)

        if needs_early_return:
            self._indent -= 1
            self._emit_line("except _EarlyReturn as _er:")
            self._indent += 1
            self._emit_line("return _er.value")
            self._indent -= 1

        self._indent -= 1
        self._emit_line("")

    def _fn_uses_unwrap(self, fn: MIRFunction) -> bool:
        """Check if a function uses Unwrap instructions."""
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Unwrap):
                    return True
        return False

    # ------------------------------------------------------------------
    # Loop header detection
    # ------------------------------------------------------------------

    def _find_loop_headers(self, fn: MIRFunction) -> set[str]:
        """Find loop headers by detecting back-edges via DFS."""
        block_map = self._block_map
        headers: set[str] = set()
        if not fn.blocks:
            return headers

        visited: set[str] = set()
        on_stack: set[str] = set()

        def dfs(label: str) -> None:
            if label not in block_map:
                return
            visited.add(label)
            on_stack.add(label)
            bb = block_map[label]
            for succ in self._successors(bb):
                if succ in on_stack:
                    headers.add(succ)
                elif succ not in visited:
                    dfs(succ)
            on_stack.discard(label)

        dfs(fn.blocks[0].label)
        return headers

    def _successors(self, bb: BasicBlock) -> list[str]:
        """Return successor labels for a basic block."""
        term = bb.terminator
        if isinstance(term, Jump):
            return [term.target]
        if isinstance(term, Branch):
            return [term.true_block, term.false_block]
        if isinstance(term, Switch):
            targets = [lbl for _, lbl in term.cases]
            if term.default_block:
                targets.append(term.default_block)
            return targets
        return []

    # ------------------------------------------------------------------
    # Control flow reconstruction
    # ------------------------------------------------------------------

    def _emit_region(self, start_label: str, stop_label: str | None = None) -> None:
        """Emit blocks from start_label until stop_label or end."""
        label: str | None = start_label
        while label and label != stop_label and label not in self._visited:
            bb = self._block_map.get(label)
            if bb is None:
                break
            self._visited.add(label)

            # Emit non-phi, non-terminator instructions
            for inst in bb.instructions:
                if isinstance(inst, (Phi, *TERMINATOR_TYPES)):
                    continue
                self._emit_instruction(inst)

            term = bb.terminator
            if isinstance(term, Return):
                self._emit_return(term)
                break
            elif isinstance(term, Jump):
                target = term.target
                if target in self._loop_headers and target in self._visited:
                    # Back-edge: emit phi assignments, end of while body
                    self._emit_phi_assignments(target, bb.label)
                    break
                else:
                    self._emit_phi_assignments(target, bb.label)
                    label = target
                    continue
            elif isinstance(term, Branch):
                if bb.label in self._loop_headers:
                    # While loop pattern
                    self._emit_while(bb, term, stop_label)
                    # Continue after the loop exit block
                    exit_label = term.false_block
                    if exit_label not in self._visited:
                        label = exit_label
                        continue
                    break
                else:
                    # If/else pattern
                    merge = self._find_merge(term.true_block, term.false_block)
                    self._emit_if_else(bb, term, merge, stop_label)
                    if merge and merge not in self._visited:
                        label = merge
                        continue
                    break
            elif isinstance(term, Switch):
                merge = self._find_switch_merge(term)
                self._emit_switch(bb, term, merge, stop_label)
                if merge and merge not in self._visited:
                    label = merge
                    continue
                break
            else:
                break

    def _emit_while(
        self,
        header_bb: BasicBlock,
        term: Branch,
        stop_label: str | None,
    ) -> None:
        """Emit a while loop from a loop header block."""
        cond_var = self._val(term.cond)
        self._emit_line(f"while {cond_var}:")
        self._indent += 1
        # Emit the body region (true branch -> back to header)
        self._emit_region(term.true_block, stop_label)
        # Re-emit header's non-phi, non-terminator instructions at end of loop
        # body so the condition variable is updated for the next iteration.
        for inst in header_bb.instructions:
            if isinstance(inst, (Phi, *TERMINATOR_TYPES)):
                continue
            self._emit_instruction(inst)
        self._indent -= 1

    def _emit_if_else(
        self,
        bb: BasicBlock,
        term: Branch,
        merge: str | None,
        stop_label: str | None,
    ) -> None:
        """Emit an if/else construct."""
        cond_var = self._val(term.cond)
        self._emit_line(f"if {cond_var}:")
        self._indent += 1
        # Emit phi assignments for merge before entering the branch
        if merge:
            self._emit_phi_assignments(merge, term.true_block)
        self._emit_region(term.true_block, merge)
        self._indent -= 1

        # Check if false branch is non-trivial (not just a jump to merge)
        false_bb = self._block_map.get(term.false_block)
        false_is_trivial = (
            false_bb is not None
            and merge is not None
            and isinstance(false_bb.terminator, Jump)
            and false_bb.terminator.target == merge
            and all(isinstance(i, (Phi, Jump)) for i in false_bb.instructions)
        )

        if not false_is_trivial and term.false_block != merge:
            self._emit_line("else:")
            self._indent += 1
            if merge:
                self._emit_phi_assignments(merge, term.false_block)
            self._emit_region(term.false_block, merge)
            self._indent -= 1
        elif false_is_trivial and false_bb is not None and merge:
            # Still need to mark false block as visited and emit phi assignments
            self._visited.add(term.false_block)
            # Check if there are phi assignments needed
            has_meaningful_phi = False
            if merge:
                merge_bb = self._block_map.get(merge)
                if merge_bb:
                    for inst in merge_bb.instructions:
                        if not isinstance(inst, Phi):
                            break
                        for lbl, val in inst.incoming:
                            if lbl == term.false_block:
                                if self._val(inst.dest) != self._val(val):
                                    has_meaningful_phi = True
            if has_meaningful_phi:
                self._emit_line("else:")
                self._indent += 1
                self._emit_phi_assignments(merge, term.false_block)
                self._indent -= 1

    def _emit_switch(
        self,
        bb: BasicBlock,
        term: Switch,
        merge: str | None,
        stop_label: str | None,
    ) -> None:
        """Emit a match/switch as if/elif chain."""
        tag_var = self._val(term.tag)
        first = True
        for case_val, case_label in term.cases:
            case_repr = _py_literal(case_val)
            keyword = "if" if first else "elif"
            self._emit_line(f"{keyword} {tag_var} == {case_repr}:")
            self._indent += 1
            if merge:
                self._emit_phi_assignments(merge, case_label)
            self._emit_region(case_label, merge)
            self._indent -= 1
            first = False

        if term.default_block:
            self._emit_line("else:")
            self._indent += 1
            if merge:
                self._emit_phi_assignments(merge, term.default_block)
            self._emit_region(term.default_block, merge)
            self._indent -= 1

    # ------------------------------------------------------------------
    # Merge block finding
    # ------------------------------------------------------------------

    def _find_merge(self, true_label: str, false_label: str) -> str | None:
        """Find the merge block for an if/else diamond.

        Follows each branch forward through non-loop jumps and finds
        the first common target.
        """
        true_targets = self._collect_forward_targets(true_label)
        false_targets = self._collect_forward_targets(false_label)
        # Find first common target
        for t in true_targets:
            if t in false_targets:
                return t
        return None

    def _collect_forward_targets(self, label: str) -> list[str]:
        """Collect labels reachable by following forward (non-back-edge) jumps."""
        targets: list[str] = []
        visited: set[str] = set()
        current: str | None = label
        while current and current not in visited:
            visited.add(current)
            bb = self._block_map.get(current)
            if bb is None:
                break
            term = bb.terminator
            if isinstance(term, Jump):
                target = term.target
                if target not in self._loop_headers or target not in visited:
                    targets.append(target)
                    current = target
                else:
                    break
            elif isinstance(term, Branch):
                # Both branches may converge; add the false block as potential merge
                targets.append(term.true_block)
                targets.append(term.false_block)
                break
            elif isinstance(term, Return):
                break
            else:
                break
        return targets

    def _find_switch_merge(self, term: Switch) -> str | None:
        """Find the merge block for a switch statement."""
        all_targets: list[list[str]] = []
        for _, case_label in term.cases:
            all_targets.append(self._collect_forward_targets(case_label))
        if term.default_block:
            all_targets.append(self._collect_forward_targets(term.default_block))

        if len(all_targets) < 2:
            return None

        # Find common target across all branches
        first_set = set(all_targets[0])
        for targets in all_targets[1:]:
            first_set &= set(targets)

        if not first_set:
            return None
        # Return the one that appears earliest in the first branch's list
        for t in all_targets[0]:
            if t in first_set:
                return t
        return None

    # ------------------------------------------------------------------
    # Phi resolution
    # ------------------------------------------------------------------

    def _emit_phi_assignments(self, target_label: str, from_label: str) -> None:
        """Emit assignments for phi nodes in target_label coming from from_label."""
        target_bb = self._block_map.get(target_label)
        if target_bb is None:
            return
        for inst in target_bb.instructions:
            if not isinstance(inst, Phi):
                break
            for lbl, val in inst.incoming:
                if lbl == from_label:
                    dest_name = self._val(inst.dest)
                    src_name = self._val(val)
                    if dest_name != src_name:
                        self._emit_line(f"{dest_name} = {src_name}")

    # ------------------------------------------------------------------
    # Instruction emission
    # ------------------------------------------------------------------

    def _emit_instruction(self, inst: Instruction) -> None:  # noqa: C901
        """Emit a single MIR instruction as Python code."""
        if isinstance(inst, Const):
            dest = self._val(inst.dest)
            # Function references: emit the function name directly (not as string)
            if inst.ty.kind == TypeKind.FN and isinstance(inst.value, str):
                self._emit_line(f"{dest} = {inst.value}")
            else:
                val = _py_literal(inst.value)
                self._emit_line(f"{dest} = {val}")

        elif isinstance(inst, Copy):
            dest = self._val(inst.dest)
            src = self._val(inst.src)
            self._emit_line(f"{dest} = {src}")

        elif isinstance(inst, Cast):
            dest = self._val(inst.dest)
            src = self._val(inst.src)
            target = self._cast_fn(inst.target_type)
            self._emit_line(f"{dest} = {target}({src})")

        elif isinstance(inst, BinOp):
            self._emit_binop(inst)

        elif isinstance(inst, UnaryOp):
            self._emit_unaryop(inst)

        elif isinstance(inst, StructInit):
            dest = self._val(inst.dest)
            type_name = inst.struct_type.name
            fields = ", ".join(f"{fname}={self._val(v)}" for fname, v in inst.fields)
            self._emit_line(f"{dest} = {type_name}({fields})")

        elif isinstance(inst, FieldGet):
            dest = self._val(inst.dest)
            obj = self._val(inst.obj)
            self._emit_line(f"{dest} = {obj}.{inst.field_name}")

        elif isinstance(inst, FieldSet):
            obj = self._val(inst.obj)
            val = self._val(inst.val)
            self._emit_line(f"{obj}.{inst.field_name} = {val}")

        elif isinstance(inst, ListInit):
            dest = self._val(inst.dest)
            elems = ", ".join(self._val(e) for e in inst.elements)
            self._emit_line(f"{dest} = [{elems}]")

        elif isinstance(inst, IndexGet):
            dest = self._val(inst.dest)
            obj = self._val(inst.obj)
            idx = self._val(inst.index)
            self._emit_line(f"{dest} = {obj}[{idx}]")

        elif isinstance(inst, IndexSet):
            obj = self._val(inst.obj)
            idx = self._val(inst.index)
            val = self._val(inst.val)
            self._emit_line(f"{obj}[{idx}] = {val}")

        elif isinstance(inst, MapInit):
            dest = self._val(inst.dest)
            pairs = ", ".join(f"{self._val(k)}: {self._val(v)}" for k, v in inst.pairs)
            self._emit_line(f"{dest} = {{{pairs}}}")

        elif isinstance(inst, EnumInit):
            dest = self._val(inst.dest)
            enum_name = inst.enum_type.name
            cls_name = f"{enum_name}_{inst.variant}"
            if inst.payload:
                args = ", ".join(self._val(p) for p in inst.payload)
                self._emit_line(f"{dest} = {cls_name}({args})")
            else:
                self._emit_line(f"{dest} = {cls_name}()")

        elif isinstance(inst, EnumTag):
            dest = self._val(inst.dest)
            val = self._val(inst.enum_val)
            self._emit_line(f"{dest} = type({val}).__name__")

        elif isinstance(inst, EnumPayload):
            dest = self._val(inst.dest)
            val = self._val(inst.enum_val)
            # Option/Result builtins use .value; user enums use ._f0
            if inst.variant in ("Some", "Ok", "Err"):
                self._emit_line(f"{dest} = {val}.value")
            else:
                self._emit_line(f"{dest} = {val}._f0")

        elif isinstance(inst, WrapSome):
            dest = self._val(inst.dest)
            val = self._val(inst.val)
            self._emit_line(f"{dest} = Some({val})")

        elif isinstance(inst, WrapNone):
            dest = self._val(inst.dest)
            self._emit_line(f"{dest} = None")

        elif isinstance(inst, WrapOk):
            dest = self._val(inst.dest)
            val = self._val(inst.val)
            self._emit_line(f"{dest} = Ok({val})")

        elif isinstance(inst, WrapErr):
            dest = self._val(inst.dest)
            val = self._val(inst.val)
            self._emit_line(f"{dest} = Err({val})")

        elif isinstance(inst, Unwrap):
            dest = self._val(inst.dest)
            val = self._val(inst.val)
            self._emit_line(f"{dest} = unwrap_or_return({val})")

        elif isinstance(inst, Call):
            self._emit_call(inst)

        elif isinstance(inst, ExternCall):
            self._emit_extern_call(inst)

        elif isinstance(inst, AgentSpawn):
            dest = self._val(inst.dest)
            type_name = inst.agent_type.name
            args = ", ".join(self._val(a) for a in inst.args)
            self._emit_line(f"{dest} = await {type_name}.spawn({args})")

        elif isinstance(inst, AgentSend):
            agent = self._val(inst.agent)
            val = self._val(inst.val)
            if inst.channel:
                self._emit_line(f"await {agent}.{inst.channel}.send({val})")
            else:
                self._emit_line(f"await {agent}.send({val})")

        elif isinstance(inst, AgentSync):
            dest = self._val(inst.dest)
            agent = self._val(inst.agent)
            if inst.channel:
                self._emit_line(f"{dest} = await {agent}.{inst.channel}.receive()")
            else:
                self._emit_line(f"{dest} = await {agent}.receive()")

        elif isinstance(inst, SignalInit):
            dest = self._val(inst.dest)
            val = self._val(inst.initial_val)
            self._emit_line(f"{dest} = Signal({val})")

        elif isinstance(inst, SignalGet):
            dest = self._val(inst.dest)
            sig = self._val(inst.signal)
            self._emit_line(f"{dest} = {sig}.value")

        elif isinstance(inst, SignalSet):
            sig = self._val(inst.signal)
            val = self._val(inst.val)
            self._emit_line(f"{sig}.value = {val}")

        elif isinstance(inst, StreamOp):
            self._emit_stream_op(inst)

        elif isinstance(inst, InterpConcat):
            dest = self._val(inst.dest)
            parts = "".join(f"{{{self._val(p)}}}" for p in inst.parts)
            self._emit_line(f'{dest} = f"{parts}"')

        elif isinstance(inst, Assert):
            cond = self._val(inst.cond)
            if inst.message is not None:
                msg = self._val(inst.message)
                self._emit_line(
                    f"if not ({cond}): raise AssertionError("
                    f'f"{inst.filename}:{inst.line}: assertion failed: {{{msg}}}")'
                )
            else:
                self._emit_line(
                    f"if not ({cond}): raise AssertionError("
                    f'"{inst.filename}:{inst.line}: assertion failed")'
                )

    # ------------------------------------------------------------------
    # Specialized instruction emitters
    # ------------------------------------------------------------------

    def _emit_binop(self, inst: BinOp) -> None:
        """Emit a binary operation."""
        dest = self._val(inst.dest)
        lhs = self._val(inst.lhs)
        rhs = self._val(inst.rhs)

        if inst.op == BinOpKind.DIV:
            self._emit_line(f"{dest} = _mn_div({lhs}, {rhs})")
        elif inst.op == BinOpKind.AND:
            self._emit_line(f"{dest} = ({lhs} and {rhs})")
        elif inst.op == BinOpKind.OR:
            self._emit_line(f"{dest} = ({lhs} or {rhs})")
        else:
            op_str = inst.op.value
            self._emit_line(f"{dest} = ({lhs} {op_str} {rhs})")

    def _emit_unaryop(self, inst: UnaryOp) -> None:
        """Emit a unary operation."""
        dest = self._val(inst.dest)
        operand = self._val(inst.operand)

        if inst.op == UnaryOpKind.NOT:
            self._emit_line(f"{dest} = (not {operand})")
        elif inst.op == UnaryOpKind.NEG:
            self._emit_line(f"{dest} = (-{operand})")

    # Method-like MIR calls that should be emitted as Python method calls
    _METHOD_CALL_MAP: dict[str, str] = {
        "push": "append",
        "pop": "pop",
        "length": "__len_call__",  # special: len(obj)
        "contains": "__contains__",  # special: val in obj
        "remove": "remove",
        "insert": "insert",
        "clear": "clear",
        "keys": "keys",
        "values": "values",
    }

    def _emit_call(self, inst: Call) -> None:
        """Emit a function call."""
        dest = self._val(inst.dest)

        # Handle method-like calls (push, length, etc.)
        method_py = self._METHOD_CALL_MAP.get(inst.fn_name)
        if method_py and len(inst.args) >= 1:
            obj = self._val(inst.args[0])
            rest_args = ", ".join(self._val(a) for a in inst.args[1:])
            if method_py == "__len_call__":
                if dest and inst.dest.name:
                    self._emit_line(f"{dest} = len({obj})")
                else:
                    self._emit_line(f"len({obj})")
            elif method_py == "__contains__" and len(inst.args) >= 2:
                val_arg = self._val(inst.args[1])
                if dest and inst.dest.name:
                    self._emit_line(f"{dest} = ({val_arg} in {obj})")
                else:
                    self._emit_line(f"({val_arg} in {obj})")
            else:
                if dest and inst.dest.name:
                    self._emit_line(f"{dest} = {obj}.{method_py}({rest_args})")
                else:
                    self._emit_line(f"{obj}.{method_py}({rest_args})")
            return

        # Handle internal MIR range calls
        if inst.fn_name == "__range" and len(inst.args) == 2:
            start = self._val(inst.args[0])
            end = self._val(inst.args[1])
            if dest and inst.dest.name:
                self._emit_line(f"{dest} = range({start}, {end})")
            else:
                self._emit_line(f"range({start}, {end})")
            return
        if inst.fn_name == "__range_inclusive" and len(inst.args) == 2:
            start = self._val(inst.args[0])
            end = self._val(inst.args[1])
            if dest and inst.dest.name:
                self._emit_line(f"{dest} = range({start}, {end} + 1)")
            else:
                self._emit_line(f"range({start}, {end} + 1)")
            return

        args = ", ".join(self._val(a) for a in inst.args)

        # Map builtins (strip % prefix from MIR names)
        raw_name = inst.fn_name.lstrip("%")
        fn_name = BUILTIN_CALL_MAP.get(raw_name, raw_name)

        # Check if the called function is async
        is_async = inst.fn_name in self._async_fns

        if dest and inst.dest.name:
            prefix = "await " if is_async else ""
            self._emit_line(f"{dest} = {prefix}{fn_name}({args})")
        else:
            prefix = "await " if is_async else ""
            self._emit_line(f"{prefix}{fn_name}({args})")

    def _emit_extern_call(self, inst: ExternCall) -> None:
        """Emit an extern function call."""
        dest = self._val(inst.dest)
        args = ", ".join(self._val(a) for a in inst.args)

        if inst.abi == "Python" and inst.module:
            call_expr = f"{inst.module}.{inst.fn_name}({args})"
        else:
            call_expr = f"{inst.fn_name}({args})"

        if dest and inst.dest.name:
            self._emit_line(f"{dest} = {call_expr}")
        else:
            self._emit_line(call_expr)

    def _emit_stream_op(self, inst: StreamOp) -> None:
        """Emit a stream operation."""
        dest = self._val(inst.dest)
        source = self._val(inst.source)
        op_name = inst.op_kind.name.lower()

        if inst.args:
            args = ", ".join(self._val(a) for a in inst.args)
            self._emit_line(f"{dest} = {source}.{op_name}({args})")
        else:
            self._emit_line(f"{dest} = {source}.{op_name}()")

    def _emit_return(self, inst: Return) -> None:
        """Emit a return statement."""
        if inst.val is not None:
            val = self._val(inst.val)
            self._emit_line(f"return {val}")
        else:
            self._emit_line("return")

    # ------------------------------------------------------------------
    # Main guard
    # ------------------------------------------------------------------

    def _emit_main_guard(self, module: MIRModule) -> None:
        """Emit the if __name__ == '__main__' guard if a main function exists."""
        has_main = any(fn.name == "main" for fn in module.functions)
        if has_main:
            self._emit_line("")
            self._emit_line('if __name__ == "__main__":')
            self._indent += 1
            self._emit_line("import asyncio")
            self._emit_line("")
            self._emit_line("asyncio.run(main())")
            self._indent -= 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _val(self, v: Value) -> str:
        """Convert a MIR Value to a Python variable name.

        Strips the ``%`` prefix and prepends ``_`` for temporaries
        (names starting with digits or ``t``).
        """
        name = v.name
        if not name:
            return "_"
        if name.startswith("%"):
            name = name[1:]
        # Prepend _ for numeric temps like "0", "t0", etc.
        if name and (name[0].isdigit() or name.startswith("t")):
            return f"_{name}"
        return name

    def _cast_fn(self, target_type: MIRType) -> str:
        """Return the Python cast function for a MIR type."""
        kind = target_type.kind
        if kind == TypeKind.INT:
            return "int"
        if kind == TypeKind.FLOAT:
            return "float"
        if kind == TypeKind.STRING:
            return "str"
        if kind == TypeKind.BOOL:
            return "bool"
        # Fallback: use the display name
        py_name = PYTHON_TYPE_MAP.get(target_type.name, target_type.name)
        return py_name

    def _emit_line(self, line: str) -> None:
        """Append an indented line to the output."""
        if line == "":
            self._lines.append("")
        else:
            self._lines.append("    " * self._indent + line)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _py_literal(value: Any) -> str:
    """Convert a Python value to its source representation."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return repr(value)
    return str(value)
