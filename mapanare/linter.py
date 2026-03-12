"""Linter — static analysis pass over the Mapanare AST.

Runs after semantic checking to catch code quality issues that the type
system does not enforce.  Each rule has an ID (W001–W008), a severity
(warning by default), and an optional auto‑fix.

Rule catalog
────────────
W001  Unused variable
W002  Unused import
W003  Variable shadowing
W004  Unreachable code after return
W005  Mutable variable never mutated
W006  Empty match arm body
W007  Agent handle without send response
W008  Result not checked (? not used)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from mapanare.ast_nodes import (
    AgentDef,
    AssignExpr,
    BinaryExpr,
    Block,
    CallExpr,
    ConstructExpr,
    Definition,
    DocComment,
    ErrExpr,
    ErrorPropExpr,
    ExportDef,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FnDef,
    ForLoop,
    Identifier,
    IfExpr,
    ImplDef,
    ImportDef,
    IndexExpr,
    InterpString,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    MapLiteral,
    MatchExpr,
    MethodCallExpr,
    NamespaceAccessExpr,
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
    Span,
    SpawnExpr,
    StreamDecl,
    SyncExpr,
    UnaryExpr,
    WhileLoop,
)
from mapanare.diagnostics import Diagnostic, Label, Severity, Suggestion

# ---------------------------------------------------------------------------
# Lint rule IDs
# ---------------------------------------------------------------------------


class LintRule(enum.Enum):
    W001 = "unused-variable"
    W002 = "unused-import"
    W003 = "variable-shadowing"
    W004 = "unreachable-code"
    W005 = "unnecessary-mut"
    W006 = "empty-match-arm"
    W007 = "agent-handle-no-send"
    W008 = "unchecked-result"


# ---------------------------------------------------------------------------
# Internal tracking structures
# ---------------------------------------------------------------------------


@dataclass
class _VarInfo:
    """Tracks a locally defined variable for usage analysis."""

    name: str
    span: Span
    used: bool = False
    mutable: bool = False
    mutated: bool = False
    is_param: bool = False
    is_for_var: bool = False
    is_definition: bool = False


@dataclass
class _ImportInfo:
    """Tracks an imported symbol for usage analysis."""

    name: str
    span: Span
    used: bool = False
    module_path: list[str] = field(default_factory=list)


class _Scope:
    """Lightweight scope for the linter's own variable tracking."""

    def __init__(self, parent: _Scope | None = None) -> None:
        self.parent = parent
        self.vars: dict[str, _VarInfo] = {}

    def define(self, info: _VarInfo) -> _VarInfo | None:
        prev = self.vars.get(info.name)
        self.vars[info.name] = info
        return prev

    def lookup(self, name: str) -> _VarInfo | None:
        v = self.vars.get(name)
        if v is not None:
            return v
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> _VarInfo | None:
        return self.vars.get(name)


# ---------------------------------------------------------------------------
# Linter
# ---------------------------------------------------------------------------


class Linter:
    """Walks a type-checked AST and emits lint diagnostics."""

    def __init__(
        self,
        filename: str = "<input>",
        allowed_rules: set[str] | None = None,
    ) -> None:
        self.filename = filename
        self.diagnostics: list[Diagnostic] = []
        # If set, only these rules are suppressed (by ID like "W001" or slug)
        self._suppressed: set[str] = set()
        self._allowed_rules = allowed_rules  # per-file allow set (from CLI)

        # Scope tracking
        self._global_scope = _Scope()
        self._scope = self._global_scope

        # Import tracking
        self._imports: list[_ImportInfo] = []

        # Names used at the expression level (collected globally)
        self._used_names: set[str] = set()

        # Builtin names that should not be flagged
        from mapanare.types import BUILTIN_FUNCTIONS

        self._builtins: set[str] = set(BUILTIN_FUNCTIONS.keys()) | {
            "self",
            "true",
            "false",
            "none",
        }

    # -- Diagnostic helpers ------------------------------------------------

    def _warn(
        self,
        rule: LintRule,
        message: str,
        span: Span,
        label: str = "",
        suggestions: list[Suggestion] | None = None,
        notes: list[str] | None = None,
    ) -> None:
        rule_id = rule.name  # e.g. "W001"
        rule_slug = rule.value  # e.g. "unused-variable"

        # Check suppression
        if rule_id in self._suppressed or rule_slug in self._suppressed:
            return
        if self._allowed_rules is not None and rule_id not in self._allowed_rules:
            return

        full_msg = f"{message} [{rule_id}]"
        labels = [Label(span=span, message=label, primary=True)]
        self.diagnostics.append(
            Diagnostic(
                severity=Severity.WARNING,
                message=full_msg,
                filename=self.filename,
                labels=labels,
                suggestions=suggestions or [],
                notes=notes or [],
            )
        )

    # -- Scope helpers -----------------------------------------------------

    def _push_scope(self) -> _Scope:
        self._scope = _Scope(parent=self._scope)
        return self._scope

    def _pop_scope(self) -> dict[str, _VarInfo]:
        """Pop scope and return its variables (for post-analysis)."""
        old_vars = self._scope.vars
        if self._scope.parent is not None:
            self._scope = self._scope.parent
        return old_vars

    # -- Name collection (expression walk) ---------------------------------

    def _collect_names_expr(self, expr: Expr | None) -> None:
        """Walk an expression tree and record every name that is *used*."""
        if expr is None:
            return
        if isinstance(expr, Identifier):
            self._used_names.add(expr.name)
            info = self._scope.lookup(expr.name)
            if info is not None:
                info.used = True
        elif isinstance(expr, BinaryExpr):
            self._collect_names_expr(expr.left)
            self._collect_names_expr(expr.right)
        elif isinstance(expr, UnaryExpr):
            self._collect_names_expr(expr.operand)
        elif isinstance(expr, CallExpr):
            self._collect_names_expr(expr.callee)
            for a in expr.args:
                self._collect_names_expr(a)
        elif isinstance(expr, MethodCallExpr):
            self._collect_names_expr(expr.object)
            for a in expr.args:
                self._collect_names_expr(a)
        elif isinstance(expr, FieldAccessExpr):
            self._collect_names_expr(expr.object)
        elif isinstance(expr, IndexExpr):
            self._collect_names_expr(expr.object)
            self._collect_names_expr(expr.index)
        elif isinstance(expr, PipeExpr):
            self._collect_names_expr(expr.left)
            self._collect_names_expr(expr.right)
        elif isinstance(expr, RangeExpr):
            self._collect_names_expr(expr.start)
            self._collect_names_expr(expr.end)
        elif isinstance(expr, LambdaExpr):
            self._push_scope()
            for p in expr.params:
                self._scope.define(_VarInfo(name=p.name, span=expr.span, is_param=True))
            if isinstance(expr.body, Block):
                self._lint_block(expr.body)
            elif isinstance(expr.body, Expr):
                self._collect_names_expr(expr.body)
            self._pop_scope()
        elif isinstance(expr, SpawnExpr):
            self._collect_names_expr(expr.callee)
            for a in expr.args:
                self._collect_names_expr(a)
        elif isinstance(expr, SyncExpr):
            self._collect_names_expr(expr.expr)
        elif isinstance(expr, SendExpr):
            self._collect_names_expr(expr.target)
            self._collect_names_expr(expr.value)
        elif isinstance(expr, ErrorPropExpr):
            self._collect_names_expr(expr.expr)
        elif isinstance(expr, ListLiteral):
            for e in expr.elements:
                self._collect_names_expr(e)
        elif isinstance(expr, MapLiteral):
            for entry in expr.entries:
                self._collect_names_expr(entry.key)
                self._collect_names_expr(entry.value)
        elif isinstance(expr, ConstructExpr):
            self._used_names.add(expr.name)
            for fi in expr.fields:
                self._collect_names_expr(fi.value)
        elif isinstance(expr, SomeExpr):
            self._collect_names_expr(expr.value)
        elif isinstance(expr, OkExpr):
            self._collect_names_expr(expr.value)
        elif isinstance(expr, ErrExpr):
            self._collect_names_expr(expr.value)
        elif isinstance(expr, SignalExpr):
            self._collect_names_expr(expr.value)
        elif isinstance(expr, AssignExpr):
            self._collect_names_assign(expr)
        elif isinstance(expr, IfExpr):
            self._collect_names_expr(expr.condition)
            self._push_scope()
            self._lint_block(expr.then_block)
            scope_vars = self._pop_scope()
            self._check_unused_vars(scope_vars)
            if isinstance(expr.else_block, Block):
                self._push_scope()
                self._lint_block(expr.else_block)
                scope_vars = self._pop_scope()
                self._check_unused_vars(scope_vars)
            elif isinstance(expr.else_block, IfExpr):
                self._collect_names_expr(expr.else_block)
        elif isinstance(expr, MatchExpr):
            self._lint_match(expr)
        elif isinstance(expr, NamespaceAccessExpr):
            self._used_names.add(expr.namespace)
        elif isinstance(expr, InterpString):
            for part in expr.parts:
                self._collect_names_expr(part)

    def _collect_names_assign(self, expr: AssignExpr) -> None:
        """Handle assignment — mark target as mutated.

        Handles both plain assignment (`x = 1`) and compound
        assignment (`x += 1`, `x -= 1`, etc.).
        """
        self._collect_names_expr(expr.value)
        # Mark the target variable as mutated
        if isinstance(expr.target, Identifier):
            self._used_names.add(expr.target.name)
            info = self._scope.lookup(expr.target.name)
            if info is not None:
                info.used = True
                info.mutated = True
        elif isinstance(expr.target, FieldAccessExpr):
            self._collect_names_expr(expr.target)
        elif isinstance(expr.target, IndexExpr):
            # arr[i] = val — mark arr as mutated
            self._collect_names_expr(expr.target.object)
            self._collect_names_expr(expr.target.index)
            if isinstance(expr.target.object, Identifier):
                info = self._scope.lookup(expr.target.object.name)
                if info is not None:
                    info.mutated = True

    # -- Block / statement lint --------------------------------------------

    def _lint_block(self, block: Block) -> None:
        """Lint statements in a block, checking for unreachable code (W004)."""
        found_return = False
        return_span: Span | None = None
        for stmt in block.stmts:
            if found_return:
                self._warn(
                    LintRule.W004,
                    "Unreachable code after return statement",
                    stmt.span,
                    label="this code will never execute",
                    notes=[f"return at line {return_span.line}" if return_span else ""],
                )
                # Only warn once per block
                break
            self._lint_stmt(stmt)
            if isinstance(stmt, ReturnStmt):
                found_return = True
                return_span = stmt.span

    def _lint_stmt(self, stmt: object) -> None:
        if isinstance(stmt, LetBinding):
            self._lint_let(stmt)
        elif isinstance(stmt, ExprStmt):
            # W008: Result not checked
            self._check_unchecked_result(stmt)
            self._collect_names_expr(stmt.expr)
        elif isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                self._collect_names_expr(stmt.value)
        elif isinstance(stmt, ForLoop):
            self._lint_for(stmt)
        elif isinstance(stmt, WhileLoop):
            self._lint_while(stmt)
        elif isinstance(stmt, SignalDecl):
            self._collect_names_expr(stmt.value)
            self._scope.define(_VarInfo(name=stmt.name, span=stmt.span, mutable=stmt.mutable))
        elif isinstance(stmt, StreamDecl):
            self._collect_names_expr(stmt.value)
            self._scope.define(_VarInfo(name=stmt.name, span=stmt.span))

    def _lint_let(self, let: LetBinding) -> None:
        """Register a let-binding and check for shadowing (W003)."""
        self._collect_names_expr(let.value)

        # W003: check for shadowing of outer variable
        outer = self._scope.lookup(let.name)
        if outer is not None and let.name not in self._builtins:
            # Only warn if the outer var is actually in a parent scope
            if self._scope.lookup_local(let.name) is None:
                self._warn(
                    LintRule.W003,
                    f"Variable '{let.name}' shadows a variable from an outer scope",
                    let.span,
                    label="shadows outer variable",
                    notes=[f"outer '{let.name}' defined at line {outer.span.line}"],
                )

        self._scope.define(_VarInfo(name=let.name, span=let.span, mutable=let.mutable))

    def _lint_for(self, loop: ForLoop) -> None:
        self._collect_names_expr(loop.iterable)
        self._push_scope()
        self._scope.define(_VarInfo(name=loop.var_name, span=loop.span, is_for_var=True))
        self._lint_block(loop.body)
        scope_vars = self._pop_scope()
        self._check_unused_vars(scope_vars)

    def _lint_while(self, loop: WhileLoop) -> None:
        self._collect_names_expr(loop.condition)
        self._push_scope()
        self._lint_block(loop.body)
        scope_vars = self._pop_scope()
        self._check_unused_vars(scope_vars)

    # -- Match lint --------------------------------------------------------

    def _lint_match(self, expr: MatchExpr) -> None:
        """Lint match expression — W006 (empty arms) and recurse."""
        self._collect_names_expr(expr.subject)
        for arm in expr.arms:
            # W006: empty match arm body
            if isinstance(arm.body, Block) and len(arm.body.stmts) == 0:
                self._warn(
                    LintRule.W006,
                    "Empty match arm body",
                    arm.span,
                    label="this arm does nothing",
                    suggestions=[
                        Suggestion(message="Add a body or use `_ => ()` for intentional no-op")
                    ],
                )
            self._push_scope()
            self._bind_pattern_names(arm.pattern)
            if isinstance(arm.body, Block):
                self._lint_block(arm.body)
            elif isinstance(arm.body, Expr):
                self._collect_names_expr(arm.body)
            scope_vars = self._pop_scope()
            self._check_unused_vars(scope_vars)

    def _bind_pattern_names(self, pattern: object) -> None:
        from mapanare.ast_nodes import ConstructorPattern, IdentPattern

        if isinstance(pattern, IdentPattern):
            self._scope.define(_VarInfo(name=pattern.name, span=pattern.span))
        elif isinstance(pattern, ConstructorPattern):
            self._used_names.add(pattern.name)
            for arg in pattern.args:
                self._bind_pattern_names(arg)

    # -- W001 / W005: unused variable / unnecessary mut --------------------

    def _check_unused_vars(self, scope_vars: dict[str, _VarInfo]) -> None:
        for name, info in scope_vars.items():
            if name.startswith("_") or name in self._builtins:
                continue
            if info.is_definition:
                continue
            # W001: unused variable
            if not info.used and not info.is_param:
                self._warn(
                    LintRule.W001,
                    f"Unused variable '{name}'",
                    info.span,
                    label="defined here but never used",
                    suggestions=[Suggestion(message=f"Prefix with underscore to silence: _{name}")],
                )
            # W005: mutable but never mutated
            if info.mutable and not info.mutated and info.used:
                self._warn(
                    LintRule.W005,
                    f"Variable '{name}' is declared as `mut` but never mutated",
                    info.span,
                    label="declared mutable here",
                    suggestions=[
                        Suggestion(
                            message="Remove `mut` keyword",
                        )
                    ],
                )

    # -- W002: unused import -----------------------------------------------

    def _check_unused_imports(self) -> None:
        for imp in self._imports:
            if not imp.used and not imp.name.startswith("_"):
                mod = "::".join(imp.module_path)
                self._warn(
                    LintRule.W002,
                    f"Unused import '{imp.name}' from '{mod}'",
                    imp.span,
                    label="imported here but never used",
                    suggestions=[
                        Suggestion(
                            message=f"Remove this import: {imp.name}",
                        )
                    ],
                )

    # -- W007: agent handle without send -----------------------------------

    def _check_agent_handle(self, agent: AgentDef) -> None:
        """W007: Agent has a `handle` method but never sends to its output."""
        if not agent.outputs:
            return

        handle_methods = [m for m in agent.methods if m.name == "handle"]
        if not handle_methods:
            return

        for handle_fn in handle_methods:
            if not self._body_has_send(handle_fn.body):
                output_names = ", ".join(o.name for o in agent.outputs)
                self._warn(
                    LintRule.W007,
                    f"Agent '{agent.name}' has a `handle` method but never "
                    f"sends to its output(s): {output_names}",
                    handle_fn.span,
                    label="handle method without send",
                    notes=["Use `self.output <- value` to send a response"],
                )

    def _body_has_send(self, block: Block) -> bool:
        """Check if a block contains any SendExpr."""
        for stmt in block.stmts:
            if self._stmt_has_send(stmt):
                return True
        return False

    def _stmt_has_send(self, stmt: object) -> bool:
        if isinstance(stmt, ExprStmt):
            return self._expr_has_send(stmt.expr)
        if isinstance(stmt, LetBinding):
            return self._expr_has_send(stmt.value)
        if isinstance(stmt, ReturnStmt):
            return stmt.value is not None and self._expr_has_send(stmt.value)
        if isinstance(stmt, ForLoop):
            return self._body_has_send(stmt.body)
        if isinstance(stmt, WhileLoop):
            return self._body_has_send(stmt.body)
        return False

    def _expr_has_send(self, expr: Expr | None) -> bool:
        if expr is None:
            return False
        if isinstance(expr, SendExpr):
            return True
        if isinstance(expr, IfExpr):
            if self._body_has_send(expr.then_block):
                return True
            if isinstance(expr.else_block, Block) and self._body_has_send(expr.else_block):
                return True
            if isinstance(expr.else_block, IfExpr) and self._expr_has_send(expr.else_block):
                return True
        if isinstance(expr, MatchExpr):
            for arm in expr.arms:
                if isinstance(arm.body, Block) and self._body_has_send(arm.body):
                    return True
                if isinstance(arm.body, Expr) and self._expr_has_send(arm.body):
                    return True
        if isinstance(expr, BinaryExpr):
            return self._expr_has_send(expr.left) or self._expr_has_send(expr.right)
        return False

    # -- W008: unchecked Result --------------------------------------------

    def _check_unchecked_result(self, stmt: ExprStmt) -> None:
        """W008: A call that returns Result is used as a bare statement
        without `?` or match/let binding."""
        expr = stmt.expr
        if isinstance(expr, ErrorPropExpr):
            return  # `?` is used — ok
        if isinstance(expr, CallExpr):
            # Heuristic: function name contains "try" or the result is unused
            callee_name = self._callee_name(expr.callee)
            if callee_name and self._is_result_producing(callee_name):
                self._warn(
                    LintRule.W008,
                    f"Result from '{callee_name}' is not checked",
                    stmt.span,
                    label="Result value discarded",
                    suggestions=[
                        Suggestion(
                            message="Use `let result = ...` or append `?` to propagate errors"
                        )
                    ],
                )

    def _callee_name(self, expr: Expr) -> str | None:
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, FieldAccessExpr):
            return expr.field_name
        if isinstance(expr, NamespaceAccessExpr):
            return expr.member
        return None

    def _is_result_producing(self, name: str) -> bool:
        """Heuristic: function names suggesting they return Result."""
        result_prefixes = ("try_", "open", "read", "write", "parse", "connect")
        return name.startswith(result_prefixes)

    # -- Top-level lint entry point ----------------------------------------

    def lint(self, program: Program) -> list[Diagnostic]:
        """Run all lint rules on a program. Returns list of diagnostics."""
        # Process definitions
        for defn in program.definitions:
            self._lint_definition(defn)

        # Post-pass: check unused imports
        # Mark imports as used based on collected names
        for imp in self._imports:
            if imp.name in self._used_names:
                imp.used = True
        self._check_unused_imports()

        # Check unused vars in global scope
        self._check_unused_vars(self._global_scope.vars)

        return self.diagnostics

    def _lint_definition(self, defn: Definition) -> None:
        # Check for #[allow(...)] decorator suppression
        self._apply_decorator_suppression(defn)

        if isinstance(defn, ImportDef):
            self._lint_import(defn)
        elif isinstance(defn, FnDef):
            self._lint_fn(defn)
        elif isinstance(defn, AgentDef):
            self._lint_agent(defn)
        elif isinstance(defn, PipeDef):
            self._lint_pipe(defn)
        elif isinstance(defn, ImplDef):
            self._lint_impl(defn)
        elif isinstance(defn, ExportDef):
            if defn.definition:
                self._lint_definition(defn.definition)
        elif isinstance(defn, DocComment):
            if defn.definition:
                self._lint_definition(defn.definition)

    def _apply_decorator_suppression(self, defn: Definition) -> None:
        """Check for @allow(rule) decorators to suppress lint rules."""
        decorators = getattr(defn, "decorators", [])
        for dec in decorators:
            if hasattr(dec, "name") and dec.name == "allow":
                for arg in getattr(dec, "args", []):
                    if isinstance(arg, Identifier):
                        self._suppressed.add(arg.name)

    def _lint_import(self, imp: ImportDef) -> None:
        """Register imported names for W002 tracking."""
        if imp.items:
            for item_name in imp.items:
                self._imports.append(
                    _ImportInfo(
                        name=item_name,
                        span=imp.span,
                        module_path=imp.path,
                    )
                )
                # Also register in scope so usage is tracked
                self._scope.define(_VarInfo(name=item_name, span=imp.span))
        else:
            # Whole-module import — the module name itself
            mod_name = imp.path[-1] if imp.path else ""
            if mod_name:
                self._imports.append(
                    _ImportInfo(
                        name=mod_name,
                        span=imp.span,
                        module_path=imp.path,
                    )
                )
                self._scope.define(_VarInfo(name=mod_name, span=imp.span))

    def _lint_fn(self, fn: FnDef) -> None:
        """Lint a function definition."""
        # Register function name at current scope (as a definition, not a variable)
        self._scope.define(_VarInfo(name=fn.name, span=fn.span, is_definition=True))

        self._push_scope()

        # Register params
        for p in fn.params:
            self._scope.define(
                _VarInfo(name=p.name, span=p.span if p.span.line > 0 else fn.span, is_param=True)
            )

        self._lint_block(fn.body)

        scope_vars = self._pop_scope()
        self._check_unused_vars(scope_vars)

        # Clear per-definition suppression after leaving scope
        self._suppressed.clear()

    def _lint_agent(self, agent: AgentDef) -> None:
        """Lint an agent definition."""
        self._scope.define(_VarInfo(name=agent.name, span=agent.span, is_definition=True))

        self._push_scope()

        # Register self, inputs, outputs
        self._scope.define(_VarInfo(name="self", span=agent.span))
        for inp in agent.inputs:
            self._scope.define(_VarInfo(name=inp.name, span=inp.span))
        for out in agent.outputs:
            self._scope.define(_VarInfo(name=out.name, span=out.span))

        # Lint state bindings
        for st in agent.state:
            self._lint_let(st)

        # Lint methods
        for method in agent.methods:
            self._push_scope()
            for p in method.params:
                self._scope.define(
                    _VarInfo(
                        name=p.name,
                        span=p.span if p.span.line > 0 else method.span,
                        is_param=True,
                    )
                )
            self._lint_block(method.body)
            method_vars = self._pop_scope()
            self._check_unused_vars(method_vars)

        scope_vars = self._pop_scope()
        self._check_unused_vars(scope_vars)

        # W007
        self._check_agent_handle(agent)

        self._suppressed.clear()

    def _lint_pipe(self, pipe: PipeDef) -> None:
        self._scope.define(_VarInfo(name=pipe.name, span=pipe.span, is_definition=True))
        for stage in pipe.stages:
            self._collect_names_expr(stage)

    def _lint_impl(self, impl: ImplDef) -> None:
        for method in impl.methods:
            self._lint_fn(method)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def lint(
    program: Program,
    *,
    filename: str = "<input>",
) -> list[Diagnostic]:
    """Run the linter on a program. Returns list of warning diagnostics."""
    linter = Linter(filename=filename)
    return linter.lint(program)


def lint_and_fix(
    source: str,
    program: Program,
    *,
    filename: str = "<input>",
) -> tuple[list[Diagnostic], str]:
    """Run the linter and apply auto-fixes.

    Returns (diagnostics, fixed_source).
    Auto-fixable rules:
    - W002: remove unused import lines
    - W005: remove `mut` keyword
    """
    diagnostics = lint(program, filename=filename)
    fixed = source
    # Collect fixable diagnostics sorted by line (descending to preserve offsets)
    fixable: list[Diagnostic] = []
    for d in diagnostics:
        if any("[W002]" in d.message or "[W005]" in d.message for _ in [1]):
            fixable.append(d)

    if not fixable:
        return diagnostics, source

    lines = fixed.split("\n")
    # Process fixes in reverse line order
    fixable.sort(key=lambda d: d.line, reverse=True)

    for diag in fixable:
        line_idx = diag.line - 1
        if line_idx < 0 or line_idx >= len(lines):
            continue
        if "[W002]" in diag.message:
            # Remove the import line
            lines.pop(line_idx)
        elif "[W005]" in diag.message:
            # Remove `mut ` from the line
            lines[line_idx] = lines[line_idx].replace("let mut ", "let ", 1)

    fixed = "\n".join(lines)
    return diagnostics, fixed
