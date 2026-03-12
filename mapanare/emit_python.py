"""Python code emitter -- transpiles Mapanare AST to runnable Python."""

from __future__ import annotations

from mapanare.ast_nodes import (
    AgentDef,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    CharLiteral,
    ConstructExpr,
    Definition,
    DocComment,
    EnumDef,
    EnumVariant,
    ErrExpr,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    ExternFnDef,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    FnType,
    ForLoop,
    GenericType,
    Identifier,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    InterpString,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    MapLiteral,
    MatchArm,
    MatchExpr,
    MethodCallExpr,
    NamedType,
    NamespaceAccessExpr,
    NoneLiteral,
    OkExpr,
    Param,
    Pattern,
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
    TypeAlias,
    TypeExpr,
    UnaryExpr,
    WhileLoop,
)
from mapanare.types import BUILTIN_CALL_MAP, PYTHON_TYPE_MAP


class PythonEmitter:
    """Walks the AST and produces Python source code."""

    def __init__(self, python_path: list[str] | None = None) -> None:
        self._indent = 0
        self._lines: list[str] = []
        self._has_agents = False
        self._has_result = False
        self._has_option = False
        self._has_signal = False
        self._has_stream = False
        self._has_traits = False
        self._impl_methods: dict[str, list[FnDef]] = {}
        self._python_path: list[str] = python_path or []
        # Python interop: extern "Python" fn declarations
        self._extern_python_fns: list[ExternFnDef] = []

    def emit(self, program: Program) -> str:
        """Emit the full program and return Python source."""
        # First pass: collect impl methods and detect features
        self._scan_program(program)
        # Emit header
        self._emit_header()
        # Emit definitions
        for defn in program.definitions:
            self._emit_definition(defn)

        # Emit main guard (only if a main function exists)
        def _is_main(d: Definition) -> bool:
            if isinstance(d, FnDef) and d.name == "main":
                return True
            if (
                isinstance(d, DocComment)
                and isinstance(d.definition, FnDef)
                and d.definition.name == "main"
            ):
                return True
            return False

        has_main = any(_is_main(d) for d in program.definitions)
        if has_main:
            self._emit_line("")
            self._emit_line('if __name__ == "__main__":')
            self._indent += 1
            self._emit_line("import asyncio")
            self._emit_line("")
            self._emit_line("asyncio.run(main())")
            self._indent -= 1
        return "\n".join(self._lines) + "\n"

    # ------------------------------------------------------------------
    # Scanning pass
    # ------------------------------------------------------------------

    def _scan_program(self, program: Program) -> None:
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) else defn
            if isinstance(inner, ImplDef):
                self._impl_methods.setdefault(inner.target, []).extend(inner.methods)
            if isinstance(inner, AgentDef):
                self._has_agents = True
            if isinstance(inner, TraitDef):
                self._has_traits = True
            if isinstance(inner, ExternFnDef) and inner.abi == "Python":
                self._extern_python_fns.append(inner)
            self._scan_definition(defn)

    def _scan_definition(self, defn: Definition) -> None:
        """Detect feature usage for imports."""
        if isinstance(defn, AgentDef):
            self._has_agents = True
            for method in defn.methods:
                self._scan_block(method.body)
            for s in defn.state:
                self._scan_expr(s.value)
        elif isinstance(defn, FnDef):
            self._scan_block(defn.body)
        elif isinstance(defn, PipeDef):
            self._has_agents = True
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._scan_definition(defn.definition)
        elif isinstance(defn, DocComment):
            if defn.definition:
                self._scan_definition(defn.definition)

    def _scan_block(self, block: Block) -> None:
        for stmt in block.stmts:
            if isinstance(stmt, LetBinding):
                self._scan_expr(stmt.value)
            elif isinstance(stmt, ExprStmt):
                self._scan_expr(stmt.expr)
            elif isinstance(stmt, ReturnStmt):
                if stmt.value:
                    self._scan_expr(stmt.value)
            elif isinstance(stmt, ForLoop):
                self._scan_expr(stmt.iterable)
                self._scan_block(stmt.body)
            elif isinstance(stmt, WhileLoop):
                self._scan_expr(stmt.condition)
                self._scan_block(stmt.body)
            elif isinstance(stmt, SignalDecl):
                self._has_signal = True
                self._scan_expr(stmt.value)
            elif isinstance(stmt, StreamDecl):
                self._has_stream = True
                self._scan_expr(stmt.value)

    def _scan_expr(self, expr: Expr) -> None:
        if isinstance(expr, InterpString):
            for part in expr.parts:
                if not isinstance(part, StringLiteral):
                    self._scan_expr(part)
            return
        if isinstance(expr, SignalExpr):
            self._has_signal = True
        elif isinstance(expr, SpawnExpr):
            self._has_agents = True
        elif isinstance(expr, (OkExpr, ErrExpr, ErrorPropExpr)):
            self._has_result = True
        elif isinstance(expr, SomeExpr):
            self._has_option = True
        elif isinstance(expr, BinaryExpr):
            self._scan_expr(expr.left)
            self._scan_expr(expr.right)
        elif isinstance(expr, UnaryExpr):
            self._scan_expr(expr.operand)
        elif isinstance(expr, CallExpr):
            # Detect builtin calls that need runtime imports
            if isinstance(expr.callee, Identifier):
                if expr.callee.name == "stream":
                    self._has_stream = True
                elif expr.callee.name in ("Ok", "Err"):
                    self._has_result = True
                elif expr.callee.name == "Some":
                    self._has_option = True
            self._scan_expr(expr.callee)
            for a in expr.args:
                self._scan_expr(a)
        elif isinstance(expr, MethodCallExpr):
            self._scan_expr(expr.object)
            for a in expr.args:
                self._scan_expr(a)
        elif isinstance(expr, PipeExpr):
            self._scan_expr(expr.left)
            self._scan_expr(expr.right)
        elif isinstance(expr, IfExpr):
            self._scan_expr(expr.condition)
            self._scan_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                self._scan_block(expr.else_block)
            elif isinstance(expr.else_block, IfExpr):
                self._scan_expr(expr.else_block)
        elif isinstance(expr, MatchExpr):
            self._scan_expr(expr.subject)
        elif isinstance(expr, LambdaExpr):
            if isinstance(expr.body, Block):
                self._scan_block(expr.body)
            else:
                self._scan_expr(expr.body)
        elif isinstance(expr, SyncExpr):
            self._scan_expr(expr.expr)
        elif isinstance(expr, SendExpr):
            self._scan_expr(expr.target)
            self._scan_expr(expr.value)
        elif isinstance(expr, ListLiteral):
            for e in expr.elements:
                self._scan_expr(e)
        elif isinstance(expr, MapLiteral):
            for entry in expr.entries:
                self._scan_expr(entry.key)
                self._scan_expr(entry.value)
        elif isinstance(expr, IndexExpr):
            self._scan_expr(expr.object)
            self._scan_expr(expr.index)
        elif isinstance(expr, FieldAccessExpr):
            self._scan_expr(expr.object)
        elif isinstance(expr, AssignExpr):
            self._scan_expr(expr.target)
            self._scan_expr(expr.value)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _emit_header(self) -> None:
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
            self._emit_line("stream = Stream.from_iter")
        if self._has_result:
            self._emit_line("from runtime.result import Ok, Err, unwrap_or_return, _EarlyReturn")
        if self._has_option:
            self._emit_line("from runtime.result import Some")
        # Python path for interop
        if self._python_path:
            self._emit_line("import sys")
            for p in self._python_path:
                self._emit_line(f"sys.path.insert(0, {repr(p)})")
            self._emit_line("")
        # Python interop imports and wrappers
        if self._extern_python_fns:
            self._emit_python_interop()
        self._emit_line("")
        self._emit_line("println = print")
        self._emit_line("")
        # Division helper: truncate toward zero for ints, real division for floats
        self._emit_line("def _mn_div(a, b):")
        self._indent += 1
        self._emit_line("if isinstance(a, float) or isinstance(b, float):")
        self._indent += 1
        self._emit_line("return a / b")
        self._indent -= 1
        self._emit_line("return int(a / b)")
        self._indent -= 1
        self._emit_line("")

    # ------------------------------------------------------------------
    # Python interop
    # ------------------------------------------------------------------

    def _emit_python_interop(self) -> None:
        """Emit imports and wrapper functions for extern "Python" declarations."""
        # Group by module
        modules: dict[str, list[ExternFnDef]] = {}
        for fn in self._extern_python_fns:
            if fn.module:
                modules.setdefault(fn.module, []).append(fn)

        for mod, fns in modules.items():
            self._emit_line(f"import {mod}")

        self._emit_line("")

        for fn in self._extern_python_fns:
            self._emit_python_wrapper(fn)

    def _emit_python_wrapper(self, fn: ExternFnDef) -> None:
        """Emit a Python wrapper function for an extern 'Python' declaration."""
        params = ", ".join(p.name for p in fn.params)
        call = f"{fn.module}.{fn.name}({params})"

        # Check if return type is Result<T, String> — wrap in try/except
        is_result_return = False
        if (
            fn.return_type
            and isinstance(fn.return_type, GenericType)
            and fn.return_type.name == "Result"
        ):
            is_result_return = True
            self._has_result = True

        self._emit_line(f"def {fn.name}({params}):")
        self._indent += 1
        if is_result_return:
            self._emit_line("try:")
            self._indent += 1
            self._emit_line(f"return Ok({call})")
            self._indent -= 1
            self._emit_line("except Exception as __e:")
            self._indent += 1
            self._emit_line("return Err(str(__e))")
            self._indent -= 1
        else:
            self._emit_line(f"return {call}")
        self._indent -= 1
        self._emit_line("")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _emit_line(self, text: str) -> None:
        if text == "":
            self._lines.append("")
        else:
            self._lines.append("    " * self._indent + text)

    def _ind(self) -> str:
        return "    " * self._indent

    # ------------------------------------------------------------------
    # Type emission
    # ------------------------------------------------------------------

    def _emit_type(self, t: TypeExpr) -> str:
        if isinstance(t, NamedType):
            return _TYPE_MAP.get(t.name, t.name)
        elif isinstance(t, GenericType):
            if t.name == "Option":
                inner = self._emit_type(t.args[0]) if t.args else "Any"
                return f"{inner} | None"
            elif t.name == "Result":
                ok_t = self._emit_type(t.args[0]) if len(t.args) > 0 else "Any"
                err_t = self._emit_type(t.args[1]) if len(t.args) > 1 else "Any"
                return f"Ok[{ok_t}] | Err[{err_t}]"
            elif t.name == "List":
                inner = self._emit_type(t.args[0]) if t.args else "Any"
                return f"list[{inner}]"
            elif t.name == "Map":
                k = self._emit_type(t.args[0]) if len(t.args) > 0 else "Any"
                v = self._emit_type(t.args[1]) if len(t.args) > 1 else "Any"
                return f"dict[{k}, {v}]"
            elif t.name == "Signal":
                inner = self._emit_type(t.args[0]) if t.args else "Any"
                return f"Signal[{inner}]"
            elif t.name == "Stream":
                inner = self._emit_type(t.args[0]) if t.args else "Any"
                return f"Stream[{inner}]"
            elif t.name == "Channel":
                inner = self._emit_type(t.args[0]) if t.args else "Any"
                return f"Channel[{inner}]"
            else:
                args_str = ", ".join(self._emit_type(a) for a in t.args)
                return f"{t.name}[{args_str}]"
        elif isinstance(t, FnType):
            return "Callable"
        return "Any"

    # ------------------------------------------------------------------
    # Definition emission
    # ------------------------------------------------------------------

    def _emit_definition(self, defn: Definition) -> None:
        if isinstance(defn, FnDef):
            self._emit_fn(defn)
        elif isinstance(defn, AgentDef):
            self._emit_agent(defn)
        elif isinstance(defn, PipeDef):
            self._emit_pipe(defn)
        elif isinstance(defn, TraitDef):
            self._emit_trait(defn)
        elif isinstance(defn, StructDef):
            self._emit_struct(defn)
        elif isinstance(defn, EnumDef):
            self._emit_enum(defn)
        elif isinstance(defn, TypeAlias):
            self._emit_type_alias(defn)
        elif isinstance(defn, ImplDef):
            pass  # methods merged during scan
        elif isinstance(defn, ImportDef):
            self._emit_import(defn)
        elif isinstance(defn, ExportDef):
            self._emit_export(defn)
        elif isinstance(defn, ExternFnDef):
            pass  # handled in header via _emit_python_interop
        elif isinstance(defn, DocComment):
            if defn.definition:
                self._emit_definition(defn.definition)

    # -- fn ---------------------------------------------------------------

    def _emit_fn(
        self,
        fn: FnDef,
        *,
        is_method: bool = False,
        is_agent_method: bool = False,
    ) -> None:
        params = self._emit_params(fn.params, is_method=is_method)
        ret = ""
        if fn.return_type:
            ret = f" -> {self._emit_type(fn.return_type)}"
        is_async = is_agent_method or fn.name == "main" or self._fn_needs_async(fn)
        prefix = "async def" if is_async else "def"
        self._emit_line(f"{prefix} {fn.name}({params}){ret}:")
        self._indent += 1
        has_error_prop = self._block_has_error_prop(fn.body)
        if has_error_prop:
            self._emit_line("try:")
            self._indent += 1
            self._emit_block_body(fn.body)
            self._indent -= 1
            self._emit_line("except _EarlyReturn as __e:")
            self._indent += 1
            self._emit_line("return __e.err")
            self._indent -= 1
        else:
            self._emit_block_body(fn.body)
        self._indent -= 1
        self._emit_line("")

    def _fn_needs_async(self, fn: FnDef) -> bool:
        """Check if a function body uses spawn/sync/send."""
        return self._block_needs_async(fn.body)

    def _block_needs_async(self, block: Block) -> bool:
        for stmt in block.stmts:
            if isinstance(stmt, ExprStmt) and self._expr_needs_async(stmt.expr):
                return True
            if isinstance(stmt, LetBinding) and self._expr_needs_async(stmt.value):
                return True
            if isinstance(stmt, ReturnStmt) and stmt.value and self._expr_needs_async(stmt.value):
                return True
            if isinstance(stmt, ForLoop):
                if self._expr_needs_async(stmt.iterable):
                    return True
                if self._block_needs_async(stmt.body):
                    return True
            if isinstance(stmt, WhileLoop):
                if self._expr_needs_async(stmt.condition):
                    return True
                if self._block_needs_async(stmt.body):
                    return True
        return False

    def _expr_needs_async(self, expr: Expr) -> bool:
        if isinstance(expr, (SpawnExpr, SyncExpr, SendExpr)):
            return True
        if isinstance(expr, BinaryExpr):
            return self._expr_needs_async(expr.left) or self._expr_needs_async(expr.right)
        if isinstance(expr, CallExpr):
            return self._expr_needs_async(expr.callee) or any(
                self._expr_needs_async(a) for a in expr.args
            )
        if isinstance(expr, MethodCallExpr):
            return self._expr_needs_async(expr.object) or any(
                self._expr_needs_async(a) for a in expr.args
            )
        if isinstance(expr, PipeExpr):
            return self._expr_needs_async(expr.left) or self._expr_needs_async(expr.right)
        if isinstance(expr, IfExpr):
            return self._expr_needs_async(expr.condition)
        if isinstance(expr, AssignExpr):
            return self._expr_needs_async(expr.value)
        return False

    def _block_has_error_prop(self, block: Block) -> bool:
        for stmt in block.stmts:
            if isinstance(stmt, ExprStmt) and self._expr_has_error_prop(stmt.expr):
                return True
            if isinstance(stmt, LetBinding) and self._expr_has_error_prop(stmt.value):
                return True
            if (
                isinstance(stmt, ReturnStmt)
                and stmt.value
                and self._expr_has_error_prop(stmt.value)
            ):
                return True
        return False

    def _expr_has_error_prop(self, expr: Expr) -> bool:
        if isinstance(expr, ErrorPropExpr):
            return True
        if isinstance(expr, BinaryExpr):
            return self._expr_has_error_prop(expr.left) or self._expr_has_error_prop(expr.right)
        if isinstance(expr, CallExpr):
            return any(self._expr_has_error_prop(a) for a in expr.args)
        return False

    def _emit_params(self, params: list[Param], *, is_method: bool = False) -> str:
        parts: list[str] = []
        if is_method:
            parts.append("self")
        for p in params:
            if p.type_annotation:
                parts.append(f"{p.name}: {self._emit_type(p.type_annotation)}")
            else:
                parts.append(p.name)
        return ", ".join(parts)

    # -- agent ------------------------------------------------------------

    def _emit_agent(self, agent: AgentDef) -> None:
        self._emit_line(f"class {agent.name}(AgentBase):")
        self._indent += 1

        # __init__
        self._emit_line("def __init__(self) -> None:")
        self._indent += 1
        self._emit_line("super().__init__()")
        for inp in agent.inputs:
            self._emit_line(f'self.{inp.name} = self._register_input("{inp.name}")')
        for out in agent.outputs:
            self._emit_line(f'self.{out.name} = self._register_output("{out.name}")')
        for s in agent.state:
            self._emit_line(f"self.{s.name} = {self._emit_expr(s.value)}")
        if not agent.inputs and not agent.outputs and not agent.state:
            self._emit_line("pass")
        self._indent -= 1
        self._emit_line("")

        # methods
        for method in agent.methods:
            self._emit_fn(method, is_method=True, is_agent_method=True)

        # impl methods
        impl_methods = self._impl_methods.get(agent.name, [])
        for method in impl_methods:
            self._emit_fn(method, is_method=True, is_agent_method=True)

        self._indent -= 1
        self._emit_line("")

    # -- pipe -------------------------------------------------------------

    def _emit_pipe(self, pipe: PipeDef) -> None:
        stage_names = []
        for stage in pipe.stages:
            stage_names.append(self._emit_expr(stage))
        self._emit_line(f"async def {pipe.name}(input_value):")
        self._indent += 1
        if not stage_names:
            self._emit_line("return input_value")
        else:
            self._emit_line("_val = input_value")
            for name in stage_names:
                self._emit_line(f"_agent = await {name}.spawn()")
                self._emit_line("_input_name = list(_agent._agent._inputs.keys())[0]")
                self._emit_line("_output_name = list(_agent._agent._outputs.keys())[0]")
                self._emit_line("await _agent._agent._inputs[_input_name].send(_val)")
                self._emit_line("_val = await _agent._agent._outputs[_output_name].receive()")
                self._emit_line("await _agent.stop()")
            self._emit_line("return _val")
        self._indent -= 1
        self._emit_line("")

    # -- trait ------------------------------------------------------------

    def _emit_trait(self, trait: TraitDef) -> None:
        self._emit_line(f"class {trait.name}(Protocol):")
        self._indent += 1
        if not trait.methods:
            self._emit_line("pass")
        for method in trait.methods:
            params = "self"
            if method.params:
                p_strs = ", ".join(
                    (
                        f"{p.name}: {self._emit_type(p.type_annotation)}"
                        if p.type_annotation
                        else p.name
                    )
                    for p in method.params
                )
                params = f"self, {p_strs}"
            ret = ""
            if method.return_type:
                ret = f" -> {self._emit_type(method.return_type)}"
            self._emit_line(f"def {method.name}({params}){ret}: ...")
        self._indent -= 1
        self._emit_line("")

    # -- struct -----------------------------------------------------------

    def _emit_struct(self, struct: StructDef) -> None:
        self._emit_line(f"class {struct.name}:")
        self._indent += 1
        # __init__
        params = ", ".join(f"{f.name}: {self._emit_type(f.type_annotation)}" for f in struct.fields)
        self._emit_line(f"def __init__(self, {params}) -> None:")
        self._indent += 1
        if struct.fields:
            for f in struct.fields:
                self._emit_line(f"self.{f.name} = {f.name}")
        else:
            self._emit_line("pass")
        self._indent -= 1
        # impl methods
        impl_methods = self._impl_methods.get(struct.name, [])
        for method in impl_methods:
            self._emit_line("")
            self._emit_fn(method, is_method=True)
        self._indent -= 1
        self._emit_line("")

    # -- enum -------------------------------------------------------------

    def _emit_enum(self, enum: EnumDef) -> None:
        # Each variant becomes a class
        for variant in enum.variants:
            self._emit_enum_variant(enum.name, variant)
        # Type alias
        variant_names = [f"{enum.name}_{v.name}" for v in enum.variants]
        self._emit_line(
            f"{enum.name} = {' | '.join(variant_names)}"
            if variant_names
            else f"# enum {enum.name} (empty)"
        )
        self._emit_line("")

    def _emit_enum_variant(self, enum_name: str, variant: EnumVariant) -> None:
        cls_name = f"{enum_name}_{variant.name}"
        self._emit_line(f"class {cls_name}:")
        self._indent += 1
        if variant.fields:
            field_names = [f"_f{i}" for i in range(len(variant.fields))]
            self._emit_line(f'__match_args__ = ({", ".join(repr(n) for n in field_names)},)')
            params = ", ".join(
                f"{n}: {self._emit_type(t)}" for n, t in zip(field_names, variant.fields)
            )
            self._emit_line(f"def __init__(self, {params}) -> None:")
            self._indent += 1
            for n in field_names:
                self._emit_line(f"self.{n} = {n}")
            self._indent -= 1
        else:
            self._emit_line("pass")
        self._indent -= 1
        self._emit_line("")

    # -- type alias -------------------------------------------------------

    def _emit_type_alias(self, alias: TypeAlias) -> None:
        self._emit_line(f"{alias.name} = {self._emit_type(alias.type_expr)}")
        self._emit_line("")

    # -- import/export ----------------------------------------------------

    def _emit_import(self, imp: ImportDef) -> None:
        mod_path = ".".join(imp.path)
        if imp.items:
            items = ", ".join(imp.items)
            self._emit_line(f"from {mod_path} import {items}")
        else:
            self._emit_line(f"import {mod_path}")

    def _emit_export(self, exp: ExportDef) -> None:
        if exp.definition:
            self._emit_definition(exp.definition)
        # exports are just public in Python

    # ------------------------------------------------------------------
    # Statement emission
    # ------------------------------------------------------------------

    def _emit_block_body(self, block: Block) -> None:
        if not block.stmts:
            self._emit_line("pass")
            return
        for stmt in block.stmts:
            self._emit_stmt(stmt)

    def _emit_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, LetBinding):
            self._emit_let(stmt)
        elif isinstance(stmt, ExprStmt):
            self._emit_expr_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._emit_return(stmt)
        elif isinstance(stmt, ForLoop):
            self._emit_for(stmt)
        elif isinstance(stmt, WhileLoop):
            self._emit_while(stmt)
        elif isinstance(stmt, SignalDecl):
            self._emit_signal_decl(stmt)
        elif isinstance(stmt, StreamDecl):
            self._emit_stream_decl(stmt)

    def _emit_let(self, let: LetBinding) -> None:
        val = self._emit_expr(let.value)
        if let.type_annotation:
            ty = self._emit_type(let.type_annotation)
            self._emit_line(f"{let.name}: {ty} = {val}")
        else:
            self._emit_line(f"{let.name} = {val}")

    def _emit_expr_stmt(self, stmt: ExprStmt) -> None:
        expr = stmt.expr
        # Handle if/match as statements
        if isinstance(expr, IfExpr):
            self._emit_if(expr)
        elif isinstance(expr, MatchExpr):
            self._emit_match(expr)
        elif isinstance(expr, SpawnExpr):
            self._emit_line(f"await {self._emit_expr(expr)}")
        elif isinstance(expr, SyncExpr):
            self._emit_line(self._emit_sync(expr))
        elif isinstance(expr, SendExpr):
            self._emit_line(
                f"await {self._emit_expr(expr.target)}.send({self._emit_expr(expr.value)})"
            )
        elif isinstance(expr, AssignExpr):
            self._emit_assign(expr)
        else:
            self._emit_line(self._emit_expr(expr))

    def _emit_return(self, ret: ReturnStmt) -> None:
        if ret.value:
            self._emit_line(f"return {self._emit_expr(ret.value)}")
        else:
            self._emit_line("return")

    def _emit_for(self, loop: ForLoop) -> None:
        iterable = self._emit_expr(loop.iterable)
        self._emit_line(f"for {loop.var_name} in {iterable}:")
        self._indent += 1
        self._emit_block_body(loop.body)
        self._indent -= 1

    def _emit_while(self, loop: WhileLoop) -> None:
        cond = self._emit_expr(loop.condition)
        self._emit_line(f"while {cond}:")
        self._indent += 1
        self._emit_block_body(loop.body)
        self._indent -= 1

    def _emit_signal_decl(self, decl: SignalDecl) -> None:
        if decl.is_computed:
            self._emit_line(f"{decl.name} = Signal(computed=lambda: {self._emit_expr(decl.value)})")
        else:
            self._emit_line(f"{decl.name} = Signal({self._emit_expr(decl.value)})")

    def _emit_stream_decl(self, decl: StreamDecl) -> None:
        self._emit_line(f"{decl.name} = Stream.from_iter({self._emit_expr(decl.value)})")

    def _emit_if(self, expr: IfExpr) -> None:
        self._emit_line(f"if {self._emit_expr(expr.condition)}:")
        self._indent += 1
        self._emit_block_body(expr.then_block)
        self._indent -= 1
        if expr.else_block is not None:
            if isinstance(expr.else_block, IfExpr):
                cond = self._emit_expr(expr.else_block.condition)
                self._emit_line(f"elif {cond}:")
                self._indent += 1
                self._emit_block_body(expr.else_block.then_block)
                self._indent -= 1
                if expr.else_block.else_block is not None:
                    if isinstance(expr.else_block.else_block, IfExpr):
                        self._emit_if_chain_rest(expr.else_block.else_block)
                    else:
                        self._emit_line("else:")
                        self._indent += 1
                        self._emit_block_body(expr.else_block.else_block)
                        self._indent -= 1
            else:
                self._emit_line("else:")
                self._indent += 1
                self._emit_block_body(expr.else_block)
                self._indent -= 1

    def _emit_if_chain_rest(self, expr: IfExpr) -> None:
        """Continue an elif chain."""
        self._emit_line(f"elif {self._emit_expr(expr.condition)}:")
        self._indent += 1
        self._emit_block_body(expr.then_block)
        self._indent -= 1
        if expr.else_block is not None:
            if isinstance(expr.else_block, IfExpr):
                self._emit_if_chain_rest(expr.else_block)
            else:
                self._emit_line("else:")
                self._indent += 1
                self._emit_block_body(expr.else_block)
                self._indent -= 1

    def _emit_match(self, expr: MatchExpr) -> None:
        subject = self._emit_expr(expr.subject)
        self._emit_line(f"match {subject}:")
        self._indent += 1
        for arm in expr.arms:
            self._emit_match_arm(arm)
        self._indent -= 1

    def _emit_match_arm(self, arm: MatchArm) -> None:
        from mapanare.ast_nodes import (
            ConstructorPattern,
            IdentPattern,
            LiteralPattern,
            WildcardPattern,
        )

        pat = arm.pattern
        if isinstance(pat, WildcardPattern):
            self._emit_line("case _:")
        elif isinstance(pat, IdentPattern):
            self._emit_line(f"case {pat.name}:")
        elif isinstance(pat, LiteralPattern):
            self._emit_line(f"case {self._emit_expr(pat.value)}:")
        elif isinstance(pat, ConstructorPattern):
            if pat.args:
                arg_pats = ", ".join(self._emit_pattern(a) for a in pat.args)
                self._emit_line(f"case {pat.name}({arg_pats}):")
            else:
                self._emit_line(f"case {pat.name}():")
        else:
            self._emit_line("case _:")

        self._indent += 1
        if isinstance(arm.body, Block):
            self._emit_block_body(arm.body)
        else:
            self._emit_line(self._emit_expr(arm.body))
        self._indent -= 1

    def _emit_pattern(self, pat: Pattern) -> str:
        from mapanare.ast_nodes import (
            ConstructorPattern,
            IdentPattern,
            LiteralPattern,
            WildcardPattern,
        )

        if isinstance(pat, WildcardPattern):
            return "_"
        elif isinstance(pat, IdentPattern):
            return pat.name
        elif isinstance(pat, LiteralPattern):
            return self._emit_expr(pat.value)
        elif isinstance(pat, ConstructorPattern):
            if pat.args:
                args = ", ".join(self._emit_pattern(a) for a in pat.args)
                return f"{pat.name}({args})"
            return f"{pat.name}()"
        return "_"

    def _emit_assign(self, expr: AssignExpr) -> None:
        target = self._emit_expr(expr.target)
        value = self._emit_expr(expr.value)
        if expr.op == "=":
            self._emit_line(f"{target} = {value}")
        else:
            self._emit_line(f"{target} {expr.op} {value}")

    # ------------------------------------------------------------------
    # Expression emission
    # ------------------------------------------------------------------

    def _emit_expr(self, expr: Expr) -> str:
        if isinstance(expr, IntLiteral):
            return str(expr.value)
        elif isinstance(expr, FloatLiteral):
            return repr(expr.value)
        elif isinstance(expr, StringLiteral):
            return repr(expr.value)
        elif isinstance(expr, InterpString):
            return self._emit_interp_string(expr)
        elif isinstance(expr, CharLiteral):
            return repr(expr.value)
        elif isinstance(expr, BoolLiteral):
            return "True" if expr.value else "False"
        elif isinstance(expr, NoneLiteral):
            return "None"
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, BinaryExpr):
            return self._emit_binary(expr)
        elif isinstance(expr, UnaryExpr):
            return self._emit_unary(expr)
        elif isinstance(expr, CallExpr):
            return self._emit_call(expr)
        elif isinstance(expr, MethodCallExpr):
            return self._emit_method_call(expr)
        elif isinstance(expr, FieldAccessExpr):
            return f"{self._emit_expr(expr.object)}.{expr.field_name}"
        elif isinstance(expr, NamespaceAccessExpr):
            return f"{expr.namespace}.{expr.member}"
        elif isinstance(expr, IndexExpr):
            return f"{self._emit_expr(expr.object)}[{self._emit_expr(expr.index)}]"
        elif isinstance(expr, PipeExpr):
            return self._emit_pipe_expr(expr)
        elif isinstance(expr, RangeExpr):
            return self._emit_range(expr)
        elif isinstance(expr, LambdaExpr):
            return self._emit_lambda(expr)
        elif isinstance(expr, SpawnExpr):
            args_str = ", ".join(self._emit_expr(a) for a in expr.args)
            callee = self._emit_expr(expr.callee)
            return f"await {callee}.spawn({args_str})"
        elif isinstance(expr, SyncExpr):
            return self._emit_sync(expr)
        elif isinstance(expr, SendExpr):
            return f"await {self._emit_expr(expr.target)}.send({self._emit_expr(expr.value)})"
        elif isinstance(expr, ErrorPropExpr):
            return f"unwrap_or_return({self._emit_expr(expr.expr)})"
        elif isinstance(expr, ListLiteral):
            elems = ", ".join(self._emit_expr(e) for e in expr.elements)
            return f"[{elems}]"
        elif isinstance(expr, MapLiteral):
            if not expr.entries:
                return "{}"
            pairs = ", ".join(
                f"{self._emit_expr(e.key)}: {self._emit_expr(e.value)}" for e in expr.entries
            )
            return f"{{{pairs}}}"
        elif isinstance(expr, ConstructExpr):
            return self._emit_construct(expr)
        elif isinstance(expr, SomeExpr):
            return f"Some({self._emit_expr(expr.value)})"
        elif isinstance(expr, OkExpr):
            return f"Ok({self._emit_expr(expr.value)})"
        elif isinstance(expr, ErrExpr):
            return f"Err({self._emit_expr(expr.value)})"
        elif isinstance(expr, SignalExpr):
            if expr.is_computed:
                body = expr.value
                # Computed signal body is a Block — extract the single expression
                if isinstance(body, Block) and body.stmts:
                    first = body.stmts[0]
                    if isinstance(first, ExprStmt):
                        body = first.expr
                    elif isinstance(first, ReturnStmt) and first.value:
                        body = first.value
                return f"Signal(computed=lambda: {self._emit_expr(body)})"
            return f"Signal({self._emit_expr(expr.value)})"
        elif isinstance(expr, AssignExpr):
            return f"{self._emit_expr(expr.target)} {expr.op} {self._emit_expr(expr.value)}"
        elif isinstance(expr, IfExpr):
            # Inline ternary
            then_expr: Expr = IntLiteral(value=0)
            if expr.then_block.stmts and isinstance(expr.then_block.stmts[0], ExprStmt):
                then_expr = expr.then_block.stmts[0].expr
            then_val = self._emit_expr(then_expr)
            else_val = "None"
            if isinstance(expr.else_block, Block) and expr.else_block.stmts:
                first = expr.else_block.stmts[0]
                if isinstance(first, ExprStmt):
                    else_val = self._emit_expr(first.expr)
            return f"({then_val} if {self._emit_expr(expr.condition)} else {else_val})"
        elif isinstance(expr, MatchExpr):
            # Match as expression not directly supported in Python inline
            return f"_match_{id(expr)}"
        return "None"

    def _emit_binary(self, expr: BinaryExpr) -> str:
        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        if expr.op == "/":
            # Mapanare integer division truncates toward zero (matches LLVM sdiv).
            # Python's / always returns float, so we use int(a/b) for int operands
            # while preserving real division for floats.
            return f"_mn_div({left}, {right})"
        op = _OP_MAP.get(expr.op, expr.op)
        return f"({left} {op} {right})"

    def _emit_unary(self, expr: UnaryExpr) -> str:
        operand = self._emit_expr(expr.operand)
        if expr.op == "!":
            return f"(not {operand})"
        return f"({expr.op}{operand})"

    # Mapanare builtins that map directly to Python builtins (from types.py)
    _BUILTIN_CALL_MAP: dict[str, str] = BUILTIN_CALL_MAP

    def _emit_call(self, expr: CallExpr) -> str:
        callee = self._emit_expr(expr.callee)
        # Map Mapanare builtins to Python equivalents
        mapped = self._BUILTIN_CALL_MAP.get(callee, callee)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        return f"{mapped}({args})"

    # Mapanare method → Python equivalent for lists and strings
    _LIST_METHOD_MAP: dict[str, str] = {
        "push": "append",
        "pop": "pop",
        "clear": "clear",
        "length": "__len__",
    }

    _STRING_METHOD_MAP: dict[str, str] = {
        "length": "__len__",
        "find": "find",
        "starts_with": "startswith",
        "ends_with": "endswith",
        "char_at": "__getitem__",
        "to_upper": "upper",
        "to_lower": "lower",
        "trim": "strip",
        "split": "split",
        "contains": "__contains__",
        "replace": "replace",
    }

    _MAP_METHOD_MAP: dict[str, str] = {
        "get": "get",
        "insert": "__setitem__",
        "delete": "pop",
        "contains": "__contains__",
        "keys": "keys",
        "values": "values",
        "length": "__len__",
        "clear": "clear",
    }

    def _emit_method_call(self, expr: MethodCallExpr) -> str:
        obj = self._emit_expr(expr.object)
        args = ", ".join(self._emit_expr(a) for a in expr.args)
        method = expr.method

        # List methods
        if method in self._LIST_METHOD_MAP:
            mapped = self._LIST_METHOD_MAP[method]
            if mapped == "__len__":
                return f"len({obj})"
            return f"{obj}.{mapped}({args})"

        # String methods
        if method in self._STRING_METHOD_MAP:
            mapped = self._STRING_METHOD_MAP[method]
            if mapped == "__len__":
                return f"len({obj})"
            if mapped == "__getitem__":
                return f"{obj}[{args}]"
            if mapped == "__contains__":
                return f"({args} in {obj})"
            return f"{obj}.{mapped}({args})"

        # Map methods
        if method in self._MAP_METHOD_MAP:
            mapped = self._MAP_METHOD_MAP[method]
            if mapped == "__len__":
                return f"len({obj})"
            if mapped == "__contains__":
                return f"({args} in {obj})"
            if mapped == "__setitem__":
                arg_list = [self._emit_expr(a) for a in expr.args]
                return f"{obj}.__setitem__({', '.join(arg_list)})"
            return f"{obj}.{mapped}({args})"

        # substring(start, end) → Python slicing
        if method == "substring":
            arg_list = [self._emit_expr(a) for a in expr.args]
            if len(arg_list) == 2:
                return f"{obj}[{arg_list[0]}:{arg_list[1]}]"
            return f"{obj}[{args}]"

        return f"{obj}.{method}({args})"

    def _emit_sync(self, expr: SyncExpr) -> str:
        """Emit sync (await).  When the inner expression is a field access on
        an agent handle (i.e. a Channel), emit `await ch.receive()`.
        For method calls (like `e.stop()`) or other expressions, emit plain await."""
        inner = expr.expr
        if isinstance(inner, FieldAccessExpr):
            return f"await {self._emit_expr(inner)}.receive()"
        return f"await {self._emit_expr(inner)}"

    def _emit_pipe_expr(self, expr: PipeExpr) -> str:
        """Pipe `a |> b` → `b(a)`."""
        left = self._emit_expr(expr.left)
        right = expr.right
        if isinstance(right, CallExpr):
            # a |> f(x) → f(a, x)
            callee = self._emit_expr(right.callee)
            args = [left] + [self._emit_expr(a) for a in right.args]
            return f"{callee}({', '.join(args)})"
        elif isinstance(right, Identifier):
            return f"{right.name}({left})"
        else:
            return f"{self._emit_expr(right)}({left})"

    def _emit_range(self, expr: RangeExpr) -> str:
        start = self._emit_expr(expr.start)
        end = self._emit_expr(expr.end)
        if expr.inclusive:
            return f"range({start}, {end} + 1)"
        return f"range({start}, {end})"

    def _emit_lambda(self, expr: LambdaExpr) -> str:
        params = ", ".join(p.name for p in expr.params)
        if isinstance(expr.body, Block):
            # Multi-statement lambda not supported in Python -- use first expr
            if expr.body.stmts:
                first = expr.body.stmts[0]
                if isinstance(first, ReturnStmt) and first.value:
                    body = self._emit_expr(first.value)
                elif isinstance(first, ExprStmt):
                    body = self._emit_expr(first.expr)
                else:
                    body = "None"
            else:
                body = "None"
        else:
            body = self._emit_expr(expr.body)
        return f"lambda {params}: {body}"

    def _emit_interp_string(self, expr: InterpString) -> str:
        """Emit an interpolated string as a Python f-string."""
        parts: list[str] = []
        for part in expr.parts:
            if isinstance(part, StringLiteral):
                # Escape braces in literal parts for f-string
                escaped = part.value.replace("{", "{{").replace("}", "}}")
                parts.append(escaped)
            else:
                parts.append(f"{{{self._emit_expr(part)}}}")
        joined = "".join(parts)
        return f'f"{joined}"'

    def _emit_construct(self, expr: ConstructExpr) -> str:
        fields = ", ".join(f"{f.name}={self._emit_expr(f.value)}" for f in expr.fields)
        return f"{expr.name}({fields})"


# -- Mappings -----------------------------------------------------------

_TYPE_MAP: dict[str, str] = PYTHON_TYPE_MAP

_OP_MAP: dict[str, str] = {
    "&&": "and",
    "||": "or",
    "==": "==",
    "!=": "!=",
}
