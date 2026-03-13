"""AST → MIR lowering pass.

Walks the typed AST (after semantic analysis) and produces MIR functions
with basic blocks. Nested expressions become flat three-address code and
control flow becomes explicit jumps/branches.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mapanare.ast_nodes import (
    AgentDef,
    AssertStmt,
    AssignExpr,
    ASTNode,
    BinaryExpr,
    Block,
    BoolLiteral,
    BreakStmt,
    CallExpr,
    CharLiteral,
    ConstructExpr,
    ConstructorPattern,
    Definition,
    DocComment,
    EnumDef,
    ErrExpr,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    ExternFnDef,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    ForLoop,
    GenericType,
    Identifier,
    IdentPattern,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    InterpString,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    LiteralPattern,
    MapLiteral,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    OkExpr,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalDecl,
    SignalExpr,
    SomeExpr,
    SpawnExpr,
    Stmt,
    StreamDecl,
    StringLiteral,
    StructDef,
    SyncExpr,
    TraitDef,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
    WildcardPattern,
)
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
    Cast,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    EnvLoad,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    MapInit,
    MIRAgentInfo,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRPipeInfo,
    MIRType,
    Phi,
    Return,
    SignalGet,
    SignalInit,
    SignalSet,
    SourceSpan,
    StreamInit,
    StreamOp,
    StreamOpKind,
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
    mir_bool,
    mir_float,
    mir_int,
    mir_string,
    mir_unknown,
    mir_void,
)
from mapanare.types import TypeInfo, TypeKind, kind_from_name

# ---------------------------------------------------------------------------
# Operator mapping from AST strings to MIR enums
# ---------------------------------------------------------------------------

_BINOP_MAP: dict[str, BinOpKind] = {
    "+": BinOpKind.ADD,
    "-": BinOpKind.SUB,
    "*": BinOpKind.MUL,
    "/": BinOpKind.DIV,
    "%": BinOpKind.MOD,
    "==": BinOpKind.EQ,
    "!=": BinOpKind.NE,
    "<": BinOpKind.LT,
    ">": BinOpKind.GT,
    "<=": BinOpKind.LE,
    ">=": BinOpKind.GE,
    "&&": BinOpKind.AND,
    "||": BinOpKind.OR,
}

_UNARYOP_MAP: dict[str, UnaryOpKind] = {
    "-": UnaryOpKind.NEG,
    "!": UnaryOpKind.NOT,
}

_STREAM_OP_MAP: dict[str, StreamOpKind] = {
    "map": StreamOpKind.MAP,
    "filter": StreamOpKind.FILTER,
    "fold": StreamOpKind.FOLD,
    "take": StreamOpKind.TAKE,
    "skip": StreamOpKind.SKIP,
    "collect": StreamOpKind.COLLECT,
}


def _ast_span_to_mir(node: ASTNode | None) -> SourceSpan | None:
    """Convert an AST node's span to a MIR SourceSpan, or None if unavailable."""
    if node is None or not hasattr(node, "span") or node.span is None:
        return None
    s = node.span
    return SourceSpan(line=s.line, column=s.column, end_line=s.end_line, end_column=s.end_column)


# ---------------------------------------------------------------------------
# Type resolution helpers
# ---------------------------------------------------------------------------


def _resolve_type_expr(te: TypeExpr | None) -> MIRType:
    """Convert an AST TypeExpr to a MIRType."""
    if te is None:
        return mir_unknown()
    if isinstance(te, NamedType):
        k = kind_from_name(te.name)
        if k == TypeKind.UNKNOWN and te.name:
            return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=te.name))
        return MIRType(TypeInfo(kind=k))
    if isinstance(te, GenericType):
        args = [_resolve_type_expr(a).type_info for a in te.args]
        k = kind_from_name(te.name)
        if k != TypeKind.UNKNOWN:
            return MIRType(TypeInfo(kind=k, args=args))
        return MIRType(TypeInfo(kind=TypeKind.STRUCT, name=te.name, args=args))
    return mir_unknown()


def _type_for_literal(expr: Expr) -> MIRType:
    """Return the MIR type for a literal expression."""
    if isinstance(expr, IntLiteral):
        return mir_int()
    if isinstance(expr, FloatLiteral):
        return mir_float()
    if isinstance(expr, BoolLiteral):
        return mir_bool()
    if isinstance(expr, (StringLiteral, InterpString, CharLiteral)):
        return mir_string()
    if isinstance(expr, NoneLiteral):
        return MIRType(TypeInfo(kind=TypeKind.OPTION))
    return mir_unknown()


# ---------------------------------------------------------------------------
# Lowerer
# ---------------------------------------------------------------------------


@dataclass
class _VarInfo:
    """Tracks the current SSA value for a variable."""

    current: Value
    mutable: bool = False


class MIRLowerer:
    """Lowers a typed AST into MIR."""

    def __init__(self) -> None:
        self._module = MIRModule()
        self._fn: MIRFunction | None = None
        self._block: BasicBlock | None = None
        self._tmp_counter = 0
        self._block_counter = 0
        # Variable name → current SSA value
        self._vars: dict[str, _VarInfo] = {}
        # Scope stack for nested scopes
        self._scope_stack: list[dict[str, _VarInfo]] = []
        # Impl methods: (type_name, method_name) → MIR function name
        self._impl_methods: dict[tuple[str, str], str] = {}
        # Struct info: name -> list of field names
        self._struct_fields: dict[str, list[str]] = {}
        # Lambda variable mappings: variable name -> lambda function name
        self._lambda_vars: dict[str, str] = {}
        # Closure variable names: variables bound to closures (lambdas with captures)
        self._closure_vars: set[str] = set()
        # Active closure captures: set during lambda lowering so _lower_fn can inject env loads
        self._pending_captures: list[tuple[str, MIRType]] | None = None
        # Enum info: name → list of variant names
        self._enum_variants: dict[str, list[str]] = {}
        # Decorator metadata for functions
        self._fn_decorators: dict[str, list[str]] = {}
        # Current source span — set by _lower_expr/_lower_stmt for debug info
        self._current_span: SourceSpan | None = None
        # Loop exit label stack for break statements
        self._loop_exit_stack: list[str] = []

    # -- Name generation ---------------------------------------------------

    def _fresh_tmp(self, prefix: str = "t") -> str:
        n = self._tmp_counter
        self._tmp_counter += 1
        return f"%{prefix}{n}"

    def _fresh_block(self, prefix: str = "bb") -> str:
        n = self._block_counter
        self._block_counter += 1
        return f"{prefix}{n}"

    def _make_value(self, ty: MIRType = mir_unknown(), prefix: str = "t") -> Value:
        return Value(name=self._fresh_tmp(prefix), ty=ty)

    # -- Block management --------------------------------------------------

    def _new_block(self, label: str | None = None) -> BasicBlock:
        if label is None:
            label = self._fresh_block()
        bb = BasicBlock(label=label)
        if self._fn is not None:
            self._fn.blocks.append(bb)
        return bb

    def _set_block(self, bb: BasicBlock) -> None:
        self._block = bb

    def _emit(self, inst: Instruction) -> None:
        assert self._block is not None, "No current basic block"
        if inst.span is None and self._current_span is not None:
            inst.span = self._current_span
        self._block.instructions.append(inst)

    def _block_terminated(self) -> bool:
        if self._block is None:
            return True
        if not self._block.instructions:
            return False
        from mapanare.mir import is_terminator

        return is_terminator(self._block.instructions[-1])

    # -- Scope management --------------------------------------------------

    def _push_scope(self) -> None:
        self._scope_stack.append(dict(self._vars))

    def _pop_scope(self) -> None:
        if self._scope_stack:
            self._vars = self._scope_stack.pop()

    def _define_var(self, name: str, val: Value, mutable: bool = False) -> None:
        self._vars[name] = _VarInfo(current=val, mutable=mutable)

    def _lookup_var(self, name: str) -> Value | None:
        info = self._vars.get(name)
        return info.current if info else None

    def _update_var(self, name: str, val: Value) -> None:
        info = self._vars.get(name)
        if info is not None:
            info.current = val

    # -- Free variable analysis --------------------------------------------

    def _analyze_free_vars(
        self,
        body: Expr | Block,
        param_names: set[str],
    ) -> list[str]:
        """Collect identifiers in a lambda body that reference enclosing scope variables.

        Returns a deduplicated list of variable names that are free in the body
        (i.e., not lambda parameters, not builtins, not struct/enum names, and
        defined in the current scope).
        """
        from mapanare.types import BUILTIN_FUNCTIONS

        builtin_names = set(BUILTIN_FUNCTIONS.keys()) | {
            "println",
            "print",
            "len",
            "str",
            "int",
            "float",
            "Some",
            "Ok",
            "Err",
            "signal",
            "stream",
            "computed",
        }
        struct_names = set(self._struct_fields.keys())
        enum_names = set(self._enum_variants.keys())
        # All enum variant names as well
        variant_names: set[str] = set()
        for variants in self._enum_variants.values():
            variant_names.update(variants)

        refs: list[str] = []
        seen: set[str] = set()

        def _collect(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, Identifier):
                name = node.name
                if (
                    name not in param_names
                    and name not in builtin_names
                    and name not in struct_names
                    and name not in enum_names
                    and name not in variant_names
                    and name not in seen
                    and self._lookup_var(name) is not None
                ):
                    seen.add(name)
                    refs.append(name)
                return
            if isinstance(node, LambdaExpr):
                # Nested lambda: its params shadow outer vars
                inner_params = param_names | {p.name for p in node.params}
                inner_refs: list[str] = []
                inner_seen: set[str] = set()

                def _collect_inner(n: Any) -> None:
                    if n is None:
                        return
                    if isinstance(n, Identifier):
                        nm = n.name
                        if (
                            nm not in inner_params
                            and nm not in builtin_names
                            and nm not in struct_names
                            and nm not in enum_names
                            and nm not in variant_names
                            and nm not in inner_seen
                            and self._lookup_var(nm) is not None
                        ):
                            inner_seen.add(nm)
                            inner_refs.append(nm)
                        return
                    if isinstance(n, LambdaExpr):
                        return  # Don't recurse into doubly-nested lambdas
                    for attr_val in (vars(n).values() if hasattr(n, "__dict__") else []):
                        if isinstance(attr_val, list):
                            for item in attr_val:
                                if isinstance(item, ASTNode):
                                    _collect_inner(item)
                        elif isinstance(attr_val, ASTNode):
                            _collect_inner(attr_val)

                _collect_inner(node.body)
                # Add inner refs to our refs (they're also free in the outer lambda)
                for r in inner_refs:
                    if r not in seen:
                        seen.add(r)
                        refs.append(r)
                return

            # Generic AST walk
            for attr_val in vars(node).values() if hasattr(node, "__dict__") else []:
                if isinstance(attr_val, list):
                    for item in attr_val:
                        if isinstance(item, ASTNode):
                            _collect(item)
                elif isinstance(attr_val, ASTNode):
                    _collect(attr_val)

        _collect(body)
        return refs

    # -- Top-level lowering ------------------------------------------------

    def lower(
        self,
        program: Program,
        module_name: str = "",
        source_file: str = "",
        source_directory: str = "",
    ) -> MIRModule:
        """Lower an entire program to MIR."""
        self._module = MIRModule(
            name=module_name,
            source_file=source_file,
            source_directory=source_directory,
        )

        # First pass: register struct/enum/extern/impl declarations
        self._register_declarations(program)

        # Second pass: lower function bodies
        for defn in program.definitions:
            self._lower_definition(defn)

        return self._module

    def _register_declarations(self, program: Program) -> None:
        """Pre-register type declarations and impl methods."""
        for defn in program.definitions:
            actual = defn
            if isinstance(actual, DocComment) and actual.definition is not None:
                actual = actual.definition

            if isinstance(actual, StructDef):
                fields = [(f.name, _resolve_type_expr(f.type_annotation)) for f in actual.fields]
                self._module.structs[actual.name] = fields
                self._struct_fields[actual.name] = [f.name for f in actual.fields]

            elif isinstance(actual, EnumDef):
                variants = []
                variant_names = []
                for v in actual.variants:
                    payload_types = [_resolve_type_expr(f) for f in v.fields]
                    variants.append((v.name, payload_types))
                    variant_names.append(v.name)
                self._module.enums[actual.name] = variants
                self._enum_variants[actual.name] = variant_names

            elif isinstance(actual, ExternFnDef):
                param_types = [_resolve_type_expr(p.type_annotation) for p in actual.params]
                ret_type = (
                    _resolve_type_expr(actual.return_type) if actual.return_type else mir_void()
                )
                self._module.extern_fns.append(
                    (actual.abi, actual.module or "", actual.name, param_types, ret_type)
                )

            elif isinstance(actual, ImplDef):
                for method in actual.methods:
                    mir_name = f"{actual.target}_{method.name}"
                    self._impl_methods[(actual.target, method.name)] = mir_name

            elif isinstance(actual, ImportDef):
                self._module.imports.append((actual.path, actual.items))

            elif isinstance(actual, TraitDef):
                self._module.trait_names.append(actual.name)

            elif isinstance(actual, PipeDef):
                stages = []
                for s in actual.stages:
                    if isinstance(s, Identifier):
                        stages.append(s.name)
                self._module.pipes[actual.name] = MIRPipeInfo(name=actual.name, stages=stages)

    def _lower_definition(self, defn: Definition) -> None:
        """Lower a single top-level definition."""
        actual: Definition = defn
        if isinstance(actual, DocComment):
            if actual.definition is not None:
                actual = actual.definition
            else:
                return

        if isinstance(actual, FnDef):
            self._lower_fn(actual)
        elif isinstance(actual, AgentDef):
            self._lower_agent(actual)
        elif isinstance(actual, ImplDef):
            self._lower_impl(actual)
        elif isinstance(actual, ExportDef):
            if actual.definition is not None:
                self._lower_definition(actual.definition)
                # Mark the lowered function as public
                if isinstance(actual.definition, FnDef):
                    fn = self._module.get_function(actual.definition.name)
                    if fn is not None:
                        fn.is_public = True
        # StructDef, EnumDef, ExternFnDef, TraitDef, TypeAlias, PipeDef, ImportDef
        # are handled in _register_declarations or need no MIR lowering

    # -- Function lowering -------------------------------------------------

    def _lower_fn(self, fn_def: FnDef, name_prefix: str = "") -> MIRFunction:
        """Lower a function definition to MIR."""
        fn_name = f"{name_prefix}{fn_def.name}" if name_prefix else fn_def.name

        params = [
            MIRParam(
                name=p.name,
                ty=_resolve_type_expr(p.type_annotation) if p.type_annotation else mir_unknown(),
            )
            for p in fn_def.params
        ]
        ret_type = _resolve_type_expr(fn_def.return_type) if fn_def.return_type else mir_void()
        decorators = [d.name for d in fn_def.decorators]

        source_line = fn_def.span.line if fn_def.span else 0
        source_file = self._module.source_file if self._module else ""

        mir_fn = MIRFunction(
            name=fn_name,
            params=params,
            return_type=ret_type,
            blocks=[],
            decorators=decorators,
            is_public=fn_def.public,
            source_line=source_line,
            source_file=source_file,
        )

        # Save/restore lowerer state for nested functions
        prev_fn = self._fn
        prev_block = self._block
        prev_tmp = self._tmp_counter
        prev_blk_cnt = self._block_counter
        prev_vars = dict(self._vars)

        self._fn = mir_fn
        self._tmp_counter = 0
        self._block_counter = 0
        self._vars = {}

        # Create entry block
        entry = self._new_block("entry")
        self._set_block(entry)

        # Bind params as variables
        for p in fn_def.params:
            param_val = Value(
                name=f"%{p.name}",
                ty=_resolve_type_expr(p.type_annotation) if p.type_annotation else mir_unknown(),
            )
            self._define_var(p.name, param_val)

        # If this is a closure lambda, inject env loads for captured variables
        if self._pending_captures is not None:
            env_val = Value(name="%__env_ptr", ty=MIRType(TypeInfo(kind=TypeKind.UNKNOWN)))
            for idx, (cap_name, cap_type) in enumerate(self._pending_captures):
                dest = Value(name=f"%{cap_name}", ty=cap_type)
                self._emit(EnvLoad(dest=dest, env=env_val, index=idx, val_type=cap_type))
                self._define_var(cap_name, dest)
            self._pending_captures = None  # consumed

        # Lower body
        last_val = self._lower_block(fn_def.body)

        # Add implicit return if block isn't terminated
        if not self._block_terminated():
            if ret_type.kind == TypeKind.VOID:
                self._emit(Return())
            elif last_val is not None:
                self._emit(Return(val=last_val))
            else:
                self._emit(Return())

        self._module.functions.append(mir_fn)

        # Restore state
        self._fn = prev_fn
        self._block = prev_block
        self._tmp_counter = prev_tmp
        self._block_counter = prev_blk_cnt
        self._vars = prev_vars

        return mir_fn

    def _lower_agent(self, agent_def: AgentDef) -> None:
        """Lower an agent definition — each method becomes a standalone function."""
        method_names = []
        for method in agent_def.methods:
            fn = self._lower_fn(method, name_prefix=f"{agent_def.name}_")
            method_names.append(fn.name)

        # Store agent metadata for emitters
        state_info: list[tuple[str, Any]] = []
        for s in agent_def.state:
            val: Any = None
            if isinstance(s.value, IntLiteral):
                val = s.value.value
            elif isinstance(s.value, FloatLiteral):
                val = s.value.value
            elif isinstance(s.value, StringLiteral):
                val = s.value.value
            elif isinstance(s.value, BoolLiteral):
                val = s.value.value
            state_info.append((s.name, val))

        self._module.agents[agent_def.name] = MIRAgentInfo(
            name=agent_def.name,
            inputs=[inp.name for inp in agent_def.inputs],
            outputs=[out.name for out in agent_def.outputs],
            state=state_info,
            method_names=method_names,
        )

    def _lower_impl(self, impl_def: ImplDef) -> None:
        """Lower an impl block — each method becomes a standalone function."""
        for method in impl_def.methods:
            self._lower_fn(method, name_prefix=f"{impl_def.target}_")

    # -- Block / statement lowering ----------------------------------------

    def _lower_block(self, block: Block) -> Value | None:
        """Lower a block of statements. Returns the value of the last expression, if any."""
        last_val: Value | None = None
        self._push_scope()
        for stmt in block.stmts:
            if self._block_terminated():
                break
            val = self._lower_stmt(stmt)
            if val is not None:
                last_val = val
        self._pop_scope()
        return last_val

    def _lower_stmt(self, stmt: Stmt) -> Value | None:
        """Lower a single statement. Returns a value for expression-statements."""
        # Track source span for debug info
        span = _ast_span_to_mir(stmt)
        if span is not None:
            self._current_span = span

        if isinstance(stmt, LetBinding):
            self._lower_let(stmt)
            return None
        if isinstance(stmt, ExprStmt):
            return self._lower_expr(stmt.expr)
        if isinstance(stmt, ReturnStmt):
            self._lower_return(stmt)
            return None
        if isinstance(stmt, ForLoop):
            self._lower_for(stmt)
            return None
        if isinstance(stmt, WhileLoop):
            self._lower_while(stmt)
            return None
        if isinstance(stmt, SignalDecl):
            self._lower_signal_decl(stmt)
            return None
        if isinstance(stmt, BreakStmt):
            if self._loop_exit_stack:
                self._emit(Jump(target=self._loop_exit_stack[-1]))
            return None
        if isinstance(stmt, AssertStmt):
            self._lower_assert(stmt)
            return None
        if isinstance(stmt, StreamDecl):
            self._lower_stream_decl(stmt)
            return None
        return None

    def _lower_let(self, let: LetBinding) -> None:
        """Lower a let binding."""
        # Track lambda bindings so calls can resolve the function name
        if isinstance(let.value, LambdaExpr):
            val = self._lower_expr(let.value)
            named = Value(name=f"%{let.name}", ty=val.ty)
            self._emit(Copy(dest=named, src=val))
            self._define_var(let.name, named, mutable=let.mutable)
            # Check if this was a closure (ClosureCreate) or plain lambda (Const)
            for bb in (self._fn.blocks if self._fn else []):
                for inst in bb.instructions:
                    if isinstance(inst, ClosureCreate) and inst.dest == val:
                        self._lambda_vars[let.name] = inst.fn_name
                        self._closure_vars.add(let.name)
                        return
                    if isinstance(inst, Const) and inst.dest == val:
                        if isinstance(inst.value, str):
                            self._lambda_vars[let.name] = inst.value
            return
        val = self._lower_expr(let.value)
        # Create a named copy for readability
        named = Value(name=f"%{let.name}", ty=val.ty)
        self._emit(Copy(dest=named, src=val))
        self._define_var(let.name, named, mutable=let.mutable)

    def _lower_return(self, ret: ReturnStmt) -> None:
        """Lower a return statement."""
        if ret.value is not None:
            val = self._lower_expr(ret.value)
            self._emit(Return(val=val))
        else:
            self._emit(Return())

    def _lower_assert(self, stmt: AssertStmt) -> None:
        """Lower an assert statement to an Assert MIR instruction."""
        cond = self._lower_expr(stmt.condition)
        msg_val = self._lower_expr(stmt.message) if stmt.message is not None else None
        line = stmt.span.line if stmt.span else 0
        filename = self._module.name if self._module else ""
        self._emit(Assert(cond=cond, message=msg_val, filename=filename, line=line))

    def _lower_for(self, loop: ForLoop) -> None:
        """Lower a for loop to basic blocks.

        Structure:
            current_block → jump header
            header: %iter_val = phi [...]; branch has_next, body, exit
            body: ... ; jump header
            exit: continue
        """
        # Lower the iterable
        iterable = self._lower_expr(loop.iterable)

        # Create blocks
        header = self._new_block(self._fresh_block("for_header"))
        body = self._new_block(self._fresh_block("for_body"))
        exit_bb = self._new_block(self._fresh_block("for_exit"))

        # Jump from current block to header
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Header: we model the loop variable as receiving values
        self._set_block(header)
        iter_val = self._make_value(prefix="iter")
        self._define_var(loop.var_name, iter_val)
        # For simplicity, we use a Call to a runtime iterator function
        has_next = self._make_value(ty=mir_bool(), prefix="has_next")
        self._emit(Call(dest=has_next, fn_name="__iter_has_next", args=[iterable]))
        self._emit(Branch(cond=has_next, true_block=body.label, false_block=exit_bb.label))

        # Body
        self._set_block(body)
        next_val = self._make_value(prefix="next")
        self._emit(Call(dest=next_val, fn_name="__iter_next", args=[iterable]))
        self._define_var(loop.var_name, next_val)
        self._push_scope()
        self._loop_exit_stack.append(exit_bb.label)
        self._lower_block(loop.body)
        self._loop_exit_stack.pop()
        self._pop_scope()
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Exit
        self._set_block(exit_bb)

    def _lower_while(self, loop: WhileLoop) -> None:
        """Lower a while loop to basic blocks.

        Structure:
            current_block → jump header
            header: %cond = ...; branch %cond, body, exit
            body: ...; jump header
            exit: continue
        """
        header = self._new_block(self._fresh_block("while_header"))
        body = self._new_block(self._fresh_block("while_body"))
        exit_bb = self._new_block(self._fresh_block("while_exit"))

        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Header
        self._set_block(header)
        cond = self._lower_expr(loop.condition)
        self._emit(Branch(cond=cond, true_block=body.label, false_block=exit_bb.label))

        # Body
        self._set_block(body)
        self._loop_exit_stack.append(exit_bb.label)
        self._lower_block(loop.body)
        self._loop_exit_stack.pop()
        if not self._block_terminated():
            self._emit(Jump(target=header.label))

        # Exit
        self._set_block(exit_bb)

    def _lower_signal_decl(self, decl: SignalDecl) -> None:
        """Lower a signal declaration."""
        init_val = self._lower_expr(decl.value)
        sig_type = _resolve_type_expr(decl.type_annotation)
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.SIGNAL)), prefix="sig")
        self._emit(SignalInit(dest=dest, signal_type=sig_type, initial_val=init_val))
        self._define_var(decl.name, dest, mutable=decl.mutable)

    def _lower_stream_decl(self, decl: StreamDecl) -> None:
        """Lower a stream declaration."""
        val = self._lower_expr(decl.value)
        self._define_var(decl.name, val)

    # -- Expression lowering -----------------------------------------------

    def _lower_expr(self, expr: Expr) -> Value:  # noqa: C901
        """Lower an expression to MIR, returning the SSA value holding the result."""
        # Track source span for debug info
        span = _ast_span_to_mir(expr)
        if span is not None:
            self._current_span = span

        if isinstance(expr, IntLiteral):
            dest = self._make_value(ty=mir_int())
            self._emit(Const(dest=dest, ty=mir_int(), value=expr.value))
            return dest

        if isinstance(expr, FloatLiteral):
            dest = self._make_value(ty=mir_float())
            self._emit(Const(dest=dest, ty=mir_float(), value=expr.value))
            return dest

        if isinstance(expr, BoolLiteral):
            dest = self._make_value(ty=mir_bool())
            self._emit(Const(dest=dest, ty=mir_bool(), value=expr.value))
            return dest

        if isinstance(expr, StringLiteral):
            dest = self._make_value(ty=mir_string())
            self._emit(Const(dest=dest, ty=mir_string(), value=expr.value))
            return dest

        if isinstance(expr, CharLiteral):
            dest = self._make_value(ty=mir_string())
            self._emit(Const(dest=dest, ty=mir_string(), value=expr.value))
            return dest

        if isinstance(expr, NoneLiteral):
            ty = MIRType(TypeInfo(kind=TypeKind.OPTION))
            dest = self._make_value(ty=ty)
            self._emit(WrapNone(dest=dest, ty=ty))
            return dest

        if isinstance(expr, Identifier):
            return self._lower_identifier(expr)

        if isinstance(expr, BinaryExpr):
            return self._lower_binary(expr)

        if isinstance(expr, UnaryExpr):
            return self._lower_unary(expr)

        if isinstance(expr, CallExpr):
            return self._lower_call(expr)

        if isinstance(expr, MethodCallExpr):
            return self._lower_method_call(expr)

        if isinstance(expr, FieldAccessExpr):
            return self._lower_field_access(expr)

        if isinstance(expr, NamespaceAccessExpr):
            return self._lower_namespace_access(expr)

        if isinstance(expr, IndexExpr):
            return self._lower_index(expr)

        if isinstance(expr, PipeExpr):
            return self._lower_pipe(expr)

        if isinstance(expr, RangeExpr):
            return self._lower_range(expr)

        if isinstance(expr, LambdaExpr):
            return self._lower_lambda(expr)

        if isinstance(expr, SpawnExpr):
            return self._lower_spawn(expr)

        if isinstance(expr, SyncExpr):
            return self._lower_sync(expr)

        if isinstance(expr, SendExpr):
            return self._lower_send(expr)

        if isinstance(expr, ErrorPropExpr):
            return self._lower_error_prop(expr)

        if isinstance(expr, ListLiteral):
            return self._lower_list(expr)

        if isinstance(expr, MapLiteral):
            return self._lower_map(expr)

        if isinstance(expr, ConstructExpr):
            return self._lower_construct(expr)

        if isinstance(expr, SomeExpr):
            val = self._lower_expr(expr.value)
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.OPTION)))
            self._emit(WrapSome(dest=dest, val=val))
            return dest

        if isinstance(expr, OkExpr):
            val = self._lower_expr(expr.value)
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RESULT)))
            self._emit(WrapOk(dest=dest, val=val))
            return dest

        if isinstance(expr, ErrExpr):
            val = self._lower_expr(expr.value)
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RESULT)))
            self._emit(WrapErr(dest=dest, val=val))
            return dest

        if isinstance(expr, SignalExpr):
            return self._lower_signal_expr(expr)

        if isinstance(expr, AssignExpr):
            return self._lower_assign(expr)

        if isinstance(expr, IfExpr):
            return self._lower_if(expr)

        if isinstance(expr, MatchExpr):
            return self._lower_match(expr)

        if isinstance(expr, InterpString):
            return self._lower_interp_string(expr)

        # Fallback: unknown expression type
        dest = self._make_value()
        self._emit(Const(dest=dest, ty=mir_unknown(), value=None))
        return dest

    # -- Expression lowering helpers ---------------------------------------

    def _lower_identifier(self, expr: Identifier) -> Value:
        """Lower an identifier reference."""
        val = self._lookup_var(expr.name)
        if val is not None:
            return val
        # Check if it's a bare enum variant (no payload)
        for enum_name, variant_names in self._enum_variants.items():
            if expr.name in variant_names:
                enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=enum_name))
                dest = self._make_value(ty=enum_ty)
                self._emit(EnumInit(dest=dest, enum_type=enum_ty, variant=expr.name, payload=[]))
                return dest
        # Unknown variable — emit a placeholder
        dest = self._make_value(prefix=expr.name)
        self._emit(Const(dest=dest, ty=mir_unknown(), value=None))
        return dest

    def _lower_binary(self, expr: BinaryExpr) -> Value:
        """Lower a binary expression."""
        # Handle pipe operator specially
        if expr.op == "|>":
            return self._lower_pipe_binary(expr)

        lhs = self._lower_expr(expr.left)
        rhs = self._lower_expr(expr.right)

        op = _BINOP_MAP.get(expr.op)
        if op is None:
            # Unknown operator — emit as call
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=f"__op_{expr.op}", args=[lhs, rhs]))
            return dest

        # Determine result type
        if op in (
            BinOpKind.EQ,
            BinOpKind.NE,
            BinOpKind.LT,
            BinOpKind.GT,
            BinOpKind.LE,
            BinOpKind.GE,
            BinOpKind.AND,
            BinOpKind.OR,
        ):
            result_ty = mir_bool()
        else:
            result_ty = lhs.ty  # inherit from left operand

        dest = self._make_value(ty=result_ty)
        self._emit(BinOp(dest=dest, op=op, lhs=lhs, rhs=rhs))
        return dest

    def _lower_pipe_binary(self, expr: BinaryExpr) -> Value:
        """Lower `a |> f` to `Call(f, [a])`, with special handling for stream ops."""
        arg = self._lower_expr(expr.left)

        # Check for stream operations via pipe: `x |> stream()`, `x |> filter(fn)`, etc.
        if isinstance(expr.right, CallExpr) and isinstance(expr.right.callee, Identifier):
            fn_name = expr.right.callee.name

            # `list |> stream()` → StreamInit
            if fn_name == "stream" and not expr.right.args:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                elem_type = arg.ty
                self._emit(
                    StreamInit(dest=dest, source=arg, elem_type=MIRType(elem_type.type_info))
                )
                return dest

            # Stream operator via pipe: `stream |> filter(fn)`, `stream |> map(fn)`, etc.
            stream_op = _STREAM_OP_MAP.get(fn_name)
            if stream_op is not None:
                extra_args = [self._lower_expr(a) for a in expr.right.args]
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                if stream_op == StreamOpKind.COLLECT:
                    dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
                # Resolve lambda function name
                fn_arg_name = ""
                if expr.right.args and isinstance(expr.right.args[0], LambdaExpr):
                    fn_arg_name = extra_args[0].name if extra_args else ""
                    for var_name, lambda_fn in self._lambda_vars.items():
                        if var_name == fn_arg_name.lstrip("%"):
                            fn_arg_name = lambda_fn
                            break
                self._emit(
                    StreamOp(
                        dest=dest,
                        op_kind=stream_op,
                        source=arg,
                        args=extra_args,
                        fn_name=fn_arg_name,
                    )
                )
                return dest

            # Regular pipe: `a |> f(b)` → `f(a, b)`
            extra_args = [self._lower_expr(a) for a in expr.right.args]
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=fn_name, args=[arg] + extra_args))
            return dest

        # The right side should be a callable
        if isinstance(expr.right, Identifier):
            # Check for bare stream op names: `x |> collect`
            stream_op = _STREAM_OP_MAP.get(expr.right.name)
            if stream_op is not None:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                if stream_op == StreamOpKind.COLLECT:
                    dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
                self._emit(StreamOp(dest=dest, op_kind=stream_op, source=arg, args=[]))
                return dest
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.name, args=[arg]))
            return dest

        # General case
        fn_val = self._lower_expr(expr.right)
        dest = self._make_value()
        self._emit(Call(dest=dest, fn_name=fn_val.name, args=[arg]))
        return dest

    def _lower_unary(self, expr: UnaryExpr) -> Value:
        """Lower a unary expression."""
        operand = self._lower_expr(expr.operand)
        op = _UNARYOP_MAP.get(expr.op)
        if op is None:
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=f"__unary_{expr.op}", args=[operand]))
            return dest

        if op == UnaryOpKind.NOT:
            result_ty = mir_bool()
        else:
            result_ty = operand.ty

        dest = self._make_value(ty=result_ty)
        self._emit(UnaryOp(dest=dest, op=op, operand=operand))
        return dest

    def _lower_call(self, expr: CallExpr) -> Value:
        """Lower a function call."""
        args = [self._lower_expr(a) for a in expr.args]
        dest = self._make_value()

        if isinstance(expr.callee, Identifier):
            fn_name = expr.callee.name

            # Handle Option/Result builtins
            if fn_name == "Some" and len(args) == 1:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.OPTION)))
                self._emit(WrapSome(dest=dest, val=args[0]))
                return dest
            if fn_name == "Ok" and len(args) == 1:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RESULT)))
                self._emit(WrapOk(dest=dest, val=args[0]))
                return dest
            if fn_name == "Err" and len(args) == 1:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RESULT)))
                self._emit(WrapErr(dest=dest, val=args[0]))
                return dest

            # Handle stream() builtin: create stream from list
            if fn_name == "stream" and len(args) == 1:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
                elem_type = args[0].ty  # inherit element type info from source
                self._emit(
                    StreamInit(dest=dest, source=args[0], elem_type=MIRType(elem_type.type_info))
                )
                return dest

            # Check if this is an enum variant constructor
            for enum_name, variant_names in self._enum_variants.items():
                if fn_name in variant_names:
                    enum_ty = MIRType(TypeInfo(kind=TypeKind.ENUM, name=enum_name))
                    dest = self._make_value(ty=enum_ty)
                    self._emit(
                        EnumInit(dest=dest, enum_type=enum_ty, variant=fn_name, payload=args)
                    )
                    return dest

            # Check if this is a struct constructor (Name(args) for a known struct)
            if fn_name in self._struct_fields:
                struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name=fn_name))
                field_names = self._struct_fields[fn_name]
                fields = list(zip(field_names, args))
                dest = self._make_value(ty=struct_ty)
                self._emit(StructInit(dest=dest, struct_type=struct_ty, fields=fields))
                return dest

            # Check if this is a closure call (lambda with captures)
            if fn_name in self._closure_vars:
                closure_val = self._lookup_var(fn_name)
                if closure_val is not None:
                    self._emit(ClosureCall(dest=dest, closure=closure_val, args=args))
                    return dest

            # Resolve lambda variable names to actual function names
            resolved_name = self._lambda_vars.get(fn_name, fn_name)
            self._emit(Call(dest=dest, fn_name=resolved_name, args=args))
        elif isinstance(expr.callee, FieldAccessExpr):
            # obj.method(args) that parsed as CallExpr(FieldAccessExpr, args)
            obj = self._lower_expr(expr.callee.object)
            method = expr.callee.field_name
            self._emit(Call(dest=dest, fn_name=method, args=[obj] + args))
        elif isinstance(expr.callee, NamespaceAccessExpr):
            # Namespace::fn(args)
            fn_name = f"{expr.callee.namespace}_{expr.callee.member}"
            self._emit(Call(dest=dest, fn_name=fn_name, args=args))
        else:
            callee_val = self._lower_expr(expr.callee)
            self._emit(Call(dest=dest, fn_name=callee_val.name, args=args))

        return dest

    def _lower_method_call(self, expr: MethodCallExpr) -> Value:
        """Lower a method call: `obj.method(args)`."""
        obj = self._lower_expr(expr.object)
        args = [self._lower_expr(a) for a in expr.args]

        # Check if this is a stream operation
        stream_op = _STREAM_OP_MAP.get(expr.method)
        if stream_op is not None:
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.STREAM)))
            # For collect, the result is a list, not a stream
            if stream_op == StreamOpKind.COLLECT:
                dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
            # Resolve lambda function name from args if the first arg is a lambda
            fn_name = ""
            if expr.args and isinstance(expr.args[0], LambdaExpr):
                # The lambda was lowered and its function name is stored
                fn_name = args[0].name if args else ""
                # Look up the actual MIR function name from lambda vars
                for var_name, lambda_fn in self._lambda_vars.items():
                    if var_name == fn_name.lstrip("%"):
                        fn_name = lambda_fn
                        break
            self._emit(
                StreamOp(dest=dest, op_kind=stream_op, source=obj, args=args, fn_name=fn_name)
            )
            return dest

        # Check if this is a signal .value access
        if expr.method == "value" and not args:
            dest = self._make_value()
            self._emit(SignalGet(dest=dest, signal=obj))
            return dest

        # General method call → Call with self as first arg
        dest = self._make_value()
        self._emit(Call(dest=dest, fn_name=expr.method, args=[obj] + args))
        return dest

    def _lower_field_access(self, expr: FieldAccessExpr) -> Value:
        """Lower field access: `obj.field`."""
        obj = self._lower_expr(expr.object)

        # Check for signal .value
        if expr.field_name == "value":
            dest = self._make_value()
            self._emit(SignalGet(dest=dest, signal=obj))
            return dest

        dest = self._make_value()
        self._emit(FieldGet(dest=dest, obj=obj, field_name=expr.field_name))
        return dest

    def _lower_namespace_access(self, expr: NamespaceAccessExpr) -> Value:
        """Lower namespace access: `Math::PI`."""
        dest = self._make_value()
        fn_name = f"{expr.namespace}_{expr.member}"
        self._emit(Call(dest=dest, fn_name=fn_name, args=[]))
        return dest

    def _lower_index(self, expr: IndexExpr) -> Value:
        """Lower index access: `arr[i]`."""
        obj = self._lower_expr(expr.object)
        index = self._lower_expr(expr.index)
        dest = self._make_value()
        self._emit(IndexGet(dest=dest, obj=obj, index=index))
        return dest

    def _lower_pipe(self, expr: PipeExpr) -> Value:
        """Lower pipe expression: `a |> f`."""
        arg = self._lower_expr(expr.left)
        if isinstance(expr.right, Identifier):
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.name, args=[arg]))
            return dest
        if isinstance(expr.right, CallExpr) and isinstance(expr.right.callee, Identifier):
            extra_args = [self._lower_expr(a) for a in expr.right.args]
            dest = self._make_value()
            self._emit(Call(dest=dest, fn_name=expr.right.callee.name, args=[arg] + extra_args))
            return dest
        fn_val = self._lower_expr(expr.right)
        dest = self._make_value()
        self._emit(Call(dest=dest, fn_name=fn_val.name, args=[arg]))
        return dest

    def _lower_range(self, expr: RangeExpr) -> Value:
        """Lower a range expression."""
        start = self._lower_expr(expr.start)
        end = self._lower_expr(expr.end)
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.RANGE)))
        fn_name = "__range_inclusive" if expr.inclusive else "__range"
        self._emit(Call(dest=dest, fn_name=fn_name, args=[start, end]))
        return dest

    def _lower_lambda(self, expr: LambdaExpr) -> Value:
        """Lower a lambda expression.

        Creates an anonymous function in the module and returns a reference.
        If the lambda body references variables from the enclosing scope,
        a closure is created with an environment struct containing captured values.
        """
        lambda_name = self._fresh_tmp("lambda")
        from mapanare.ast_nodes import Block as _Block
        from mapanare.ast_nodes import FnDef as _FnDef
        from mapanare.ast_nodes import Param as _Param

        body_block: Block
        if isinstance(expr.body, Block):
            body_block = expr.body
        else:
            body_block = _Block(stmts=[ReturnStmt(value=expr.body)])

        # Analyze free variables in the lambda body
        param_names = {p.name for p in expr.params}
        free_vars = self._analyze_free_vars(expr.body, param_names)

        # Collect captured values from current scope
        captures: list[tuple[str, Value]] = []
        for var_name in free_vars:
            var_val = self._lookup_var(var_name)
            if var_val is not None:
                captures.append((var_name, var_val))

        if not captures:
            # No captures — plain function reference (existing behavior)
            fn_def = _FnDef(
                name=lambda_name,
                params=list(expr.params),
                body=body_block,
            )
            self._lower_fn(fn_def)
            dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.FN)))
            self._emit(Const(dest=dest, ty=MIRType(TypeInfo(kind=TypeKind.FN)), value=lambda_name))
            return dest

        # Has captures — create a closure
        # Add __env_ptr as first parameter
        env_param = _Param(name="__env_ptr")
        modified_params = [env_param] + list(expr.params)

        fn_def = _FnDef(
            name=lambda_name,
            params=modified_params,
            body=body_block,
        )

        # Set pending captures so _lower_fn injects EnvLoad instructions
        capture_info = [(name, val.ty) for name, val in captures]
        self._pending_captures = capture_info
        self._lower_fn(fn_def)

        # Emit ClosureCreate instruction
        captured_values = [val for _, val in captures]
        capture_types = [val.ty for _, val in captures]
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.FN)))
        self._emit(
            ClosureCreate(
                dest=dest,
                fn_name=lambda_name,
                captures=captured_values,
                capture_types=capture_types,
            )
        )
        return dest

    def _lower_spawn(self, expr: SpawnExpr) -> Value:
        """Lower spawn expression: `spawn Agent(args)`."""
        args = [self._lower_expr(a) for a in expr.args]
        agent_name = ""
        if isinstance(expr.callee, Identifier):
            agent_name = expr.callee.name

        agent_ty = MIRType(TypeInfo(kind=TypeKind.AGENT, name=agent_name))
        dest = self._make_value(ty=agent_ty)
        self._emit(AgentSpawn(dest=dest, agent_type=agent_ty, args=args))
        return dest

    def _lower_sync(self, expr: SyncExpr) -> Value:
        """Lower sync expression: `sync agent.output`."""
        if isinstance(expr.expr, FieldAccessExpr):
            agent = self._lower_expr(expr.expr.object)
            channel = expr.expr.field_name
            dest = self._make_value()
            self._emit(AgentSync(dest=dest, agent=agent, channel=channel))
            return dest
        # Generic sync
        val = self._lower_expr(expr.expr)
        dest = self._make_value()
        self._emit(AgentSync(dest=dest, agent=val, channel=""))
        return dest

    def _lower_send(self, expr: SendExpr) -> Value:
        """Lower send expression: `agent.input <- value`."""
        val = self._lower_expr(expr.value)
        if isinstance(expr.target, FieldAccessExpr):
            agent = self._lower_expr(expr.target.object)
            channel = expr.target.field_name
            self._emit(AgentSend(agent=agent, channel=channel, val=val))
        else:
            target = self._lower_expr(expr.target)
            self._emit(AgentSend(agent=target, channel="", val=val))
        dest = self._make_value(ty=mir_void())
        self._emit(Const(dest=dest, ty=mir_void(), value=None))
        return dest

    def _lower_error_prop(self, expr: ErrorPropExpr) -> Value:
        """Lower `expr?` — tag-check + branch (early return on Err/None).

        Generates:
            %val = <lower expr>
            %tag = enum_tag %val
            branch %tag == ok, ok_block, err_block
        err_block:
            ret %val  (propagate error)
        ok_block:
            %unwrapped = unwrap %val
        """
        val = self._lower_expr(expr.expr)

        tag = self._make_value(ty=mir_bool(), prefix="tag")
        self._emit(EnumTag(dest=tag, enum_val=val))

        ok_block = self._new_block(self._fresh_block("prop_ok"))
        err_block = self._new_block(self._fresh_block("prop_err"))

        self._emit(Branch(cond=tag, true_block=ok_block.label, false_block=err_block.label))

        # Error path: return the error
        self._set_block(err_block)
        self._emit(Return(val=val))

        # Ok path: unwrap
        self._set_block(ok_block)
        dest = self._make_value()
        self._emit(Unwrap(dest=dest, val=val))
        return dest

    def _lower_list(self, expr: ListLiteral) -> Value:
        """Lower a list literal."""
        elements = [self._lower_expr(e) for e in expr.elements]
        elem_type = elements[0].ty if elements else mir_unknown()
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.LIST)))
        self._emit(ListInit(dest=dest, elem_type=elem_type, elements=elements))
        return dest

    def _lower_map(self, expr: MapLiteral) -> Value:
        """Lower a map literal."""
        pairs = [(self._lower_expr(e.key), self._lower_expr(e.value)) for e in expr.entries]
        key_type = pairs[0][0].ty if pairs else mir_unknown()
        val_type = pairs[0][1].ty if pairs else mir_unknown()
        dest = self._make_value(ty=MIRType(TypeInfo(kind=TypeKind.MAP)))
        self._emit(MapInit(dest=dest, key_type=key_type, val_type=val_type, pairs=pairs))
        return dest

    def _lower_construct(self, expr: ConstructExpr) -> Value:
        """Lower struct construction: `Point { x: 1.0, y: 2.0 }`."""
        fields = [(f.name, self._lower_expr(f.value)) for f in expr.fields]
        struct_ty = MIRType(TypeInfo(kind=TypeKind.STRUCT, name=expr.name))
        dest = self._make_value(ty=struct_ty)
        self._emit(StructInit(dest=dest, struct_type=struct_ty, fields=fields))
        return dest

    def _lower_signal_expr(self, expr: SignalExpr) -> Value:
        """Lower signal expression: `signal(value)`."""
        init_val = self._lower_expr(expr.value)
        sig_ty = MIRType(TypeInfo(kind=TypeKind.SIGNAL))
        dest = self._make_value(ty=sig_ty)
        self._emit(SignalInit(dest=dest, signal_type=sig_ty, initial_val=init_val))
        return dest

    def _lower_assign(self, expr: AssignExpr) -> Value:
        """Lower assignment: `x = 5` or `x += 1`."""
        val = self._lower_expr(expr.value)

        if isinstance(expr.target, Identifier):
            if expr.op != "=":
                # Compound assignment: x += 1 → x = x + 1
                old_val = self._lower_identifier(expr.target)
                op_str = expr.op[:-1]  # "+=" → "+"
                binop = _BINOP_MAP.get(op_str)
                if binop is not None:
                    result = self._make_value(ty=old_val.ty)
                    self._emit(BinOp(dest=result, op=binop, lhs=old_val, rhs=val))
                    val = result

            # Reuse the same variable name for mutable reassignment so that
            # the Python emitter produces correct code for loops. This breaks
            # strict SSA uniqueness but the MIR optimizer must handle this.
            new_val = Value(name=f"%{expr.target.name}", ty=val.ty)
            self._emit(Copy(dest=new_val, src=val))
            self._update_var(expr.target.name, new_val)
            return new_val

        if isinstance(expr.target, FieldAccessExpr):
            obj = self._lower_expr(expr.target.object)
            # Signal .value assignment → emit SignalSet for reactivity
            if expr.target.field_name == "value":
                self._emit(SignalSet(signal=obj, val=val))
                return val
            self._emit(FieldSet(obj=obj, field_name=expr.target.field_name, val=val))
            return val

        if isinstance(expr.target, IndexExpr):
            obj = self._lower_expr(expr.target.object)
            index = self._lower_expr(expr.target.index)
            self._emit(IndexSet(obj=obj, index=index, val=val))
            return val

        return val

    def _lower_if(self, expr: IfExpr) -> Value:
        """Lower if/else to basic blocks with Branch terminator.

        Structure:
            %cond = <condition>
            branch %cond, then_bb, else_bb
        then_bb:
            %then_val = <then block>
            jump merge_bb
        else_bb:
            %else_val = <else block>
            jump merge_bb
        merge_bb:
            %result = phi [then_bb: %then_val, else_bb: %else_val]
        """
        cond = self._lower_expr(expr.condition)

        then_bb = self._new_block(self._fresh_block("if_then"))
        else_bb = self._new_block(self._fresh_block("if_else"))
        merge_bb = self._new_block(self._fresh_block("if_merge"))

        self._emit(Branch(cond=cond, true_block=then_bb.label, false_block=else_bb.label))

        # Then block
        self._set_block(then_bb)
        then_val = self._lower_block(expr.then_block)
        then_exit_bb = self._block  # may have changed due to nested control flow
        if not self._block_terminated():
            self._emit(Jump(target=merge_bb.label))

        # Else block
        self._set_block(else_bb)
        else_val: Value | None = None
        if isinstance(expr.else_block, Block):
            else_val = self._lower_block(expr.else_block)
        elif isinstance(expr.else_block, IfExpr):
            else_val = self._lower_if(expr.else_block)
        else_exit_bb = self._block
        if not self._block_terminated():
            self._emit(Jump(target=merge_bb.label))

        # Merge block with phi
        self._set_block(merge_bb)
        if then_val is not None or else_val is not None:
            tv = then_val if then_val is not None else Value(name="%void", ty=mir_void())
            ev = else_val if else_val is not None else Value(name="%void", ty=mir_void())
            assert then_exit_bb is not None
            assert else_exit_bb is not None
            result = self._make_value(ty=tv.ty, prefix="if_result")
            self._emit(
                Phi(
                    dest=result,
                    incoming=[
                        (then_exit_bb.label, tv),
                        (else_exit_bb.label, ev),
                    ],
                )
            )
            return result

        # Void if — no value
        result = self._make_value(ty=mir_void())
        self._emit(Const(dest=result, ty=mir_void(), value=None))
        return result

    def _lower_match(self, expr: MatchExpr) -> Value:
        """Lower match expression to Switch + basic blocks.

        Structure:
            %subject = <lower subject>
            %tag = enum_tag %subject
            switch %tag [variant1 => arm1_bb, ...] default default_bb
        arm_bb:
            %payload = enum_payload %subject::Variant
            <bind pattern vars>
            %arm_val = <lower arm body>
            jump merge_bb
        merge_bb:
            %result = phi [arm1_bb: %val1, arm2_bb: %val2, ...]
        """
        subject = self._lower_expr(expr.subject)

        merge_bb = self._new_block(self._fresh_block("match_merge"))

        # Create blocks for each arm
        arm_blocks: list[BasicBlock] = []
        for _arm in expr.arms:
            arm_bb = self._new_block(self._fresh_block("match_arm"))
            arm_blocks.append(arm_bb)

        # Build switch cases
        cases: list[tuple[Any, str]] = []
        default_block = merge_bb.label

        for i, arm in enumerate(expr.arms):
            pat = arm.pattern
            if isinstance(pat, ConstructorPattern):
                cases.append((pat.name, arm_blocks[i].label))
            elif isinstance(pat, LiteralPattern):
                lit_val = self._get_literal_value(pat.value)
                cases.append((lit_val, arm_blocks[i].label))
            elif isinstance(pat, IdentPattern) and self._is_enum_variant(pat.name):
                # Bare enum variant name used as pattern (e.g., `Up => ...`)
                cases.append((pat.name, arm_blocks[i].label))
            elif isinstance(pat, (WildcardPattern, IdentPattern)):
                default_block = arm_blocks[i].label
            else:
                default_block = arm_blocks[i].label

        # Emit switch or branch
        if cases:
            tag = self._make_value(ty=mir_unknown(), prefix="tag")
            self._emit(EnumTag(dest=tag, enum_val=subject))
            self._emit(Switch(tag=tag, cases=cases, default_block=default_block))
        elif arm_blocks:
            # No enum patterns — jump to first arm
            self._emit(Jump(target=arm_blocks[0].label))

        # Lower each arm
        arm_results: list[tuple[str, Value]] = []
        for i, arm in enumerate(expr.arms):
            self._set_block(arm_blocks[i])
            self._push_scope()

            # Bind pattern variables
            pat = arm.pattern
            if isinstance(pat, ConstructorPattern):
                for j, arg_pat in enumerate(pat.args):
                    if isinstance(arg_pat, IdentPattern):
                        payload = self._make_value(prefix=arg_pat.name)
                        self._emit(EnumPayload(dest=payload, enum_val=subject, variant=pat.name))
                        self._define_var(arg_pat.name, payload)
            elif isinstance(pat, IdentPattern):
                self._define_var(pat.name, subject)

            # Lower arm body
            if isinstance(arm.body, Block):
                arm_val = self._lower_block(arm.body)
            else:
                arm_val = self._lower_expr(arm.body)

            exit_bb = self._block
            if not self._block_terminated():
                self._emit(Jump(target=merge_bb.label))

            self._pop_scope()

            if arm_val is not None and exit_bb is not None:
                arm_results.append((exit_bb.label, arm_val))

        # Merge block
        self._set_block(merge_bb)
        if arm_results:
            result = self._make_value(ty=arm_results[0][1].ty, prefix="match_result")
            self._emit(Phi(dest=result, incoming=arm_results))
            return result

        result = self._make_value(ty=mir_void())
        self._emit(Const(dest=result, ty=mir_void(), value=None))
        return result

    def _lower_interp_string(self, expr: InterpString) -> Value:
        """Lower string interpolation."""
        parts = []
        for part in expr.parts:
            val = self._lower_expr(part)
            if not isinstance(part, StringLiteral):
                # Cast non-string parts to string
                str_val = self._make_value(ty=mir_string())
                self._emit(Cast(dest=str_val, src=val, target_type=mir_string()))
                parts.append(str_val)
            else:
                parts.append(val)

        dest = self._make_value(ty=mir_string())
        self._emit(InterpConcat(dest=dest, parts=parts))
        return dest

    # -- Helpers -----------------------------------------------------------

    def _is_enum_variant(self, name: str) -> bool:
        """Check if a name matches a known enum variant."""
        for variant_names in self._enum_variants.values():
            if name in variant_names:
                return True
        return False

    def _get_literal_value(self, expr: Expr) -> Any:
        """Extract the literal value from an expression (for switch cases)."""
        if isinstance(expr, IntLiteral):
            return expr.value
        if isinstance(expr, FloatLiteral):
            return expr.value
        if isinstance(expr, BoolLiteral):
            return expr.value
        if isinstance(expr, StringLiteral):
            return expr.value
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def lower(
    program: Program,
    module_name: str = "",
    source_file: str = "",
    source_directory: str = "",
) -> MIRModule:
    """Lower an AST program to MIR.

    Args:
        program: The typed AST (after semantic analysis).
        module_name: Optional module name.
        source_file: Original source file name (for debug info).
        source_directory: Directory of the source file (for debug info).

    Returns:
        A MIRModule containing the lowered MIR.
    """
    return MIRLowerer().lower(
        program,
        module_name,
        source_file=source_file,
        source_directory=source_directory,
    )
