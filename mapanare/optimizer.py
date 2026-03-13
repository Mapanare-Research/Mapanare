"""AST optimization passes for the Mapanare compiler.

Phase 4.4: Optimization passes that transform the AST before emission.
Passes operate between semantic analysis and code emission.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import IntEnum

from mapanare.ast_nodes import (
    AgentDef,
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    Definition,
    DocComment,
    ErrExpr,
    ErrorPropExpr,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FloatLiteral,
    FnDef,
    ForLoop,
    Identifier,
    IfExpr,
    IndexExpr,
    InterpString,
    IntLiteral,
    LambdaExpr,
    LetBinding,
    ListLiteral,
    MapLiteral,
    MatchExpr,
    MethodCallExpr,
    OkExpr,
    PipeDef,
    PipeExpr,
    Program,
    RangeExpr,
    ReturnStmt,
    SendExpr,
    SignalExpr,
    SomeExpr,
    SpawnExpr,
    Stmt,
    StringLiteral,
    SyncExpr,
    UnaryExpr,
    WhileLoop,
)

# ---------------------------------------------------------------------------
# Optimization level
# ---------------------------------------------------------------------------


class OptLevel(IntEnum):
    """Optimization levels matching -O0 through -O3."""

    O0 = 0  # No optimization
    O1 = 1  # Basic: constant folding
    O2 = 2  # Standard: + dead code elimination, agent inlining
    O3 = 3  # Aggressive: + stream fusion


# ---------------------------------------------------------------------------
# Pass statistics
# ---------------------------------------------------------------------------


@dataclass
class PassStats:
    """Statistics collected by optimization passes."""

    constants_folded: int = 0
    constants_propagated: int = 0
    dead_stmts_removed: int = 0
    dead_fns_removed: int = 0
    dead_branches_removed: int = 0
    agents_inlined: int = 0
    streams_fused: int = 0

    @property
    def total_changes(self) -> int:
        return (
            self.constants_folded
            + self.constants_propagated
            + self.dead_stmts_removed
            + self.dead_fns_removed
            + self.dead_branches_removed
            + self.agents_inlined
            + self.streams_fused
        )


# ---------------------------------------------------------------------------
# Pass 1: Constant Folding and Propagation
# ---------------------------------------------------------------------------


def _is_literal(expr: Expr) -> bool:
    """Check if an expression is a compile-time constant literal."""
    return isinstance(expr, (IntLiteral, FloatLiteral, BoolLiteral, StringLiteral))


def _literal_value(expr: Expr) -> int | float | bool | str:
    """Extract the Python value from a literal node."""
    if isinstance(expr, (IntLiteral, FloatLiteral, BoolLiteral, StringLiteral)):
        return expr.value
    raise TypeError(f"Not a literal: {type(expr).__name__}")


def _make_literal(value: int | float | bool | str, span: object) -> Expr:
    """Create a literal AST node from a Python value."""
    if isinstance(value, bool):
        return BoolLiteral(value=value, span=span)  # type: ignore[arg-type]
    if isinstance(value, int):
        return IntLiteral(value=value, span=span)  # type: ignore[arg-type]
    if isinstance(value, float):
        return FloatLiteral(value=value, span=span)  # type: ignore[arg-type]
    if isinstance(value, str):
        return StringLiteral(value=value, span=span)  # type: ignore[arg-type]
    raise TypeError(f"Cannot make literal from {type(value)}")


def _fold_binary(op: str, left: Expr, right: Expr) -> Expr | None:
    """Try to fold a binary expression with constant operands.

    Returns a new literal node if foldable, None otherwise.
    """
    if not (_is_literal(left) and _is_literal(right)):
        return None

    lv = _literal_value(left)
    rv = _literal_value(right)

    try:
        result: int | float | bool | str | None = None

        # Arithmetic (int/float)
        if op == "+" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv + rv
        elif op == "-" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv - rv
        elif op == "*" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv * rv
        elif op == "/" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            if rv == 0:
                return None  # don't fold division by zero
            if isinstance(lv, int) and isinstance(rv, int):
                result = lv // rv  # integer division
            else:
                result = lv / rv
        elif op == "%" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            if rv == 0:
                return None
            result = lv % rv

        # String concatenation
        elif op == "+" and isinstance(lv, str) and isinstance(rv, str):
            result = lv + rv

        # Comparison
        elif op == "==" and type(lv) is type(rv):
            result = lv == rv
        elif op == "!=" and type(lv) is type(rv):
            result = lv != rv
        elif op == "<" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv < rv
        elif op == "<=" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv <= rv
        elif op == ">" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv > rv
        elif op == ">=" and isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            result = lv >= rv

        # Logical
        elif op == "&&" and isinstance(lv, bool) and isinstance(rv, bool):
            result = lv and rv
        elif op == "||" and isinstance(lv, bool) and isinstance(rv, bool):
            result = lv or rv

        if result is not None:
            return _make_literal(result, left.span)

    except (ArithmeticError, TypeError):
        pass

    return None


def _fold_unary(op: str, operand: Expr) -> Expr | None:
    """Try to fold a unary expression with a constant operand."""
    if not _is_literal(operand):
        return None

    val = _literal_value(operand)

    if op == "-" and isinstance(val, (int, float)):
        return _make_literal(-val, operand.span)
    if op == "!" and isinstance(val, bool):
        return _make_literal(not val, operand.span)

    return None


class ConstantFolder:
    """Constant folding and propagation pass.

    - Folds binary/unary expressions with literal operands.
    - Propagates constants: if `let x = 5`, replaces uses of `x` with `5`.
    - Iterates until no more changes are made (fixed-point).
    """

    def __init__(self) -> None:
        self.stats = PassStats()
        # name → constant value (for propagation within a scope)
        self._constants: dict[str, Expr] = {}
        # names that get reassigned (mutable or assigned to) — skip propagation
        self._reassigned: set[str] = set()

    def run(self, program: Program) -> Program:
        """Run constant folding on the entire program."""
        new_defs: list[Definition] = []
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                folded = self._fold_fn(inner)
                if isinstance(defn, DocComment):
                    defn.definition = folded
                    new_defs.append(defn)
                else:
                    new_defs.append(folded)
            else:
                new_defs.append(defn)
        program.definitions = new_defs
        return program

    def _fold_fn(self, fn: FnDef) -> FnDef:
        """Fold constants within a function."""
        old_constants = self._constants.copy()
        old_reassigned = self._reassigned.copy()
        self._constants = {}
        self._reassigned = set()

        # First pass: collect reassigned names
        self._collect_reassigned(fn.body)

        # Second pass: fold and propagate
        fn.body = self._fold_block(fn.body)

        self._constants = old_constants
        self._reassigned = old_reassigned
        return fn

    def _collect_reassigned(self, block: Block) -> None:
        """Collect names that are reassigned (can't safely propagate)."""
        for stmt in block.stmts:
            if isinstance(stmt, LetBinding) and stmt.mutable:
                self._reassigned.add(stmt.name)
            elif isinstance(stmt, ExprStmt) and isinstance(stmt.expr, AssignExpr):
                if isinstance(stmt.expr.target, Identifier):
                    self._reassigned.add(stmt.expr.target.name)
            elif isinstance(stmt, ForLoop):
                self._reassigned.add(stmt.var_name)
                self._collect_reassigned(stmt.body)
            elif isinstance(stmt, WhileLoop):
                self._collect_reassigned(stmt.body)

    def _fold_block(self, block: Block) -> Block:
        """Fold constants in a block."""
        new_stmts: list[Stmt] = []
        for stmt in block.stmts:
            new_stmts.append(self._fold_stmt(stmt))
        block.stmts = new_stmts
        return block

    def _fold_stmt(self, stmt: Stmt) -> Stmt:
        """Fold constants in a statement."""
        if isinstance(stmt, LetBinding):
            stmt.value = self._fold_expr(stmt.value)
            # Record constant for propagation (immutable + literal value)
            if not stmt.mutable and _is_literal(stmt.value) and stmt.name not in self._reassigned:
                self._constants[stmt.name] = copy.deepcopy(stmt.value)
            return stmt

        if isinstance(stmt, ExprStmt):
            stmt.expr = self._fold_expr(stmt.expr)
            return stmt

        if isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                stmt.value = self._fold_expr(stmt.value)
            return stmt

        if isinstance(stmt, ForLoop):
            stmt.iterable = self._fold_expr(stmt.iterable)
            stmt.body = self._fold_block(stmt.body)
            return stmt

        if isinstance(stmt, WhileLoop):
            stmt.condition = self._fold_expr(stmt.condition)
            stmt.body = self._fold_block(stmt.body)
            return stmt

        return stmt

    def _fold_expr(self, expr: Expr) -> Expr:
        """Recursively fold an expression."""
        if isinstance(expr, BinaryExpr):
            expr.left = self._fold_expr(expr.left)
            expr.right = self._fold_expr(expr.right)
            folded = _fold_binary(expr.op, expr.left, expr.right)
            if folded is not None:
                self.stats.constants_folded += 1
                return folded
            return expr

        if isinstance(expr, UnaryExpr):
            expr.operand = self._fold_expr(expr.operand)
            folded = _fold_unary(expr.op, expr.operand)
            if folded is not None:
                self.stats.constants_folded += 1
                return folded
            return expr

        if isinstance(expr, Identifier):
            # Constant propagation
            if expr.name in self._constants:
                self.stats.constants_propagated += 1
                return copy.deepcopy(self._constants[expr.name])
            return expr

        if isinstance(expr, CallExpr):
            expr.callee = self._fold_expr(expr.callee)
            expr.args = [self._fold_expr(a) for a in expr.args]
            return expr

        if isinstance(expr, PipeExpr):
            expr.left = self._fold_expr(expr.left)
            expr.right = self._fold_expr(expr.right)
            return expr

        if isinstance(expr, IfExpr):
            expr.condition = self._fold_expr(expr.condition)
            expr.then_block = self._fold_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                expr.else_block = self._fold_block(expr.else_block)
            elif isinstance(expr.else_block, IfExpr):
                result = self._fold_expr(expr.else_block)
                if isinstance(result, IfExpr):
                    expr.else_block = result
            return expr

        if isinstance(expr, MatchExpr):
            expr.subject = self._fold_expr(expr.subject)
            for arm in expr.arms:
                if isinstance(arm.body, Block):
                    arm.body = self._fold_block(arm.body)
                else:
                    arm.body = self._fold_expr(arm.body)
            return expr

        if isinstance(expr, AssignExpr):
            expr.value = self._fold_expr(expr.value)
            return expr

        if isinstance(expr, RangeExpr):
            expr.start = self._fold_expr(expr.start)
            expr.end = self._fold_expr(expr.end)
            return expr

        if isinstance(expr, ListLiteral):
            expr.elements = [self._fold_expr(e) for e in expr.elements]
            return expr

        if isinstance(expr, MapLiteral):
            for entry in expr.entries:
                entry.key = self._fold_expr(entry.key)
                entry.value = self._fold_expr(entry.value)
            return expr

        if isinstance(expr, LambdaExpr):
            if isinstance(expr.body, Block):
                expr.body = self._fold_block(expr.body)
            else:
                expr.body = self._fold_expr(expr.body)
            return expr

        if isinstance(expr, IndexExpr):
            expr.object = self._fold_expr(expr.object)
            expr.index = self._fold_expr(expr.index)
            return expr

        if isinstance(expr, MethodCallExpr):
            expr.object = self._fold_expr(expr.object)
            expr.args = [self._fold_expr(a) for a in expr.args]
            return expr

        if isinstance(expr, SomeExpr):
            expr.value = self._fold_expr(expr.value)
            return expr

        if isinstance(expr, OkExpr):
            expr.value = self._fold_expr(expr.value)
            return expr

        if isinstance(expr, ErrExpr):
            expr.value = self._fold_expr(expr.value)
            return expr

        # Literals and other leaf nodes pass through
        return expr


# ---------------------------------------------------------------------------
# Pass 2: Dead Code Elimination
# ---------------------------------------------------------------------------


class DeadCodeEliminator:
    """Dead code elimination pass.

    Removes:
    - Statements after a return in a block.
    - If branches with constant conditions (replaces with taken branch).
    - Unused let bindings (binding to literal with no side effects).
    - Unreferenced private functions.
    """

    def __init__(self) -> None:
        self.stats = PassStats()

    def run(self, program: Program) -> Program:
        """Run dead code elimination on the entire program."""
        # First: eliminate dead code within functions
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                self._dce_fn(inner)

        # Second: remove unreferenced private functions
        program = self._remove_dead_fns(program)

        return program

    def _dce_fn(self, fn: FnDef) -> None:
        """Eliminate dead code within a function."""
        fn.body = self._dce_block(fn.body)

    def _dce_block(self, block: Block) -> Block:
        """Remove dead statements from a block."""
        new_stmts: list[Stmt] = []
        found_return = False

        for stmt in block.stmts:
            if found_return:
                self.stats.dead_stmts_removed += 1
                continue

            stmt = self._dce_stmt(stmt)
            new_stmts.append(stmt)

            if isinstance(stmt, ReturnStmt):
                found_return = True

        # Remove unused let bindings (pure literal with no references)
        used_names = self._collect_used_names_stmts(new_stmts)
        final_stmts: list[Stmt] = []
        for stmt in new_stmts:
            if (
                isinstance(stmt, LetBinding)
                and _is_literal(stmt.value)
                and stmt.name not in used_names
            ):
                self.stats.dead_stmts_removed += 1
                continue
            final_stmts.append(stmt)

        block.stmts = final_stmts
        return block

    def _dce_stmt(self, stmt: Stmt) -> Stmt:
        """Process a statement for dead code."""
        if isinstance(stmt, ExprStmt):
            stmt.expr = self._dce_expr(stmt.expr)
            return stmt

        if isinstance(stmt, LetBinding):
            stmt.value = self._dce_expr(stmt.value)
            return stmt

        if isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                stmt.value = self._dce_expr(stmt.value)
            return stmt

        if isinstance(stmt, ForLoop):
            stmt.iterable = self._dce_expr(stmt.iterable)
            stmt.body = self._dce_block(stmt.body)
            return stmt

        if isinstance(stmt, WhileLoop):
            stmt.condition = self._dce_expr(stmt.condition)
            stmt.body = self._dce_block(stmt.body)
            return stmt

        return stmt

    def _dce_expr(self, expr: Expr) -> Expr:
        """Eliminate dead branches in expressions."""
        if isinstance(expr, IfExpr):
            expr.condition = self._dce_expr(expr.condition)
            expr.then_block = self._dce_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                expr.else_block = self._dce_block(expr.else_block)
            elif isinstance(expr.else_block, IfExpr):
                result = self._dce_expr(expr.else_block)
                if isinstance(result, IfExpr):
                    expr.else_block = result

            # If condition is a constant, replace with the taken branch
            if isinstance(expr.condition, BoolLiteral):
                self.stats.dead_branches_removed += 1
                if expr.condition.value:
                    # Condition is true → keep then block
                    # Return a match that just executes the then block
                    return expr  # keep as-is; the untaken branch is already dead
                else:
                    # Condition is false → keep else block if it exists
                    return expr

            return expr

        if isinstance(expr, MatchExpr):
            expr.subject = self._dce_expr(expr.subject)
            for arm in expr.arms:
                if isinstance(arm.body, Block):
                    arm.body = self._dce_block(arm.body)
                elif isinstance(arm.body, Expr):
                    arm.body = self._dce_expr(arm.body)
            return expr

        if isinstance(expr, BinaryExpr):
            expr.left = self._dce_expr(expr.left)
            expr.right = self._dce_expr(expr.right)
            return expr

        if isinstance(expr, UnaryExpr):
            expr.operand = self._dce_expr(expr.operand)
            return expr

        if isinstance(expr, CallExpr):
            expr.callee = self._dce_expr(expr.callee)
            expr.args = [self._dce_expr(a) for a in expr.args]
            return expr

        if isinstance(expr, PipeExpr):
            expr.left = self._dce_expr(expr.left)
            expr.right = self._dce_expr(expr.right)
            return expr

        if isinstance(expr, AssignExpr):
            expr.value = self._dce_expr(expr.value)
            return expr

        return expr

    def _collect_used_names_stmts(self, stmts: list[Stmt]) -> set[str]:
        """Collect all identifier names used in a list of statements."""
        names: set[str] = set()
        for stmt in stmts:
            self._collect_used_names_stmt(stmt, names)
        return names

    def _collect_used_names_stmt(self, stmt: Stmt, names: set[str]) -> None:
        """Collect identifier names used in a statement."""
        if isinstance(stmt, LetBinding):
            self._collect_used_names_expr(stmt.value, names)
        elif isinstance(stmt, ExprStmt):
            self._collect_used_names_expr(stmt.expr, names)
        elif isinstance(stmt, ReturnStmt) and stmt.value is not None:
            self._collect_used_names_expr(stmt.value, names)
        elif isinstance(stmt, ForLoop):
            self._collect_used_names_expr(stmt.iterable, names)
            for s in stmt.body.stmts:
                self._collect_used_names_stmt(s, names)
        elif isinstance(stmt, WhileLoop):
            self._collect_used_names_expr(stmt.condition, names)
            for s in stmt.body.stmts:
                self._collect_used_names_stmt(s, names)

    def _collect_used_names_expr(self, expr: Expr, names: set[str]) -> None:
        """Collect all identifier names referenced in an expression."""
        if isinstance(expr, Identifier):
            names.add(expr.name)
        elif isinstance(expr, BinaryExpr):
            self._collect_used_names_expr(expr.left, names)
            self._collect_used_names_expr(expr.right, names)
        elif isinstance(expr, UnaryExpr):
            self._collect_used_names_expr(expr.operand, names)
        elif isinstance(expr, CallExpr):
            self._collect_used_names_expr(expr.callee, names)
            for a in expr.args:
                self._collect_used_names_expr(a, names)
        elif isinstance(expr, PipeExpr):
            self._collect_used_names_expr(expr.left, names)
            self._collect_used_names_expr(expr.right, names)
        elif isinstance(expr, IfExpr):
            self._collect_used_names_expr(expr.condition, names)
            for s in expr.then_block.stmts:
                self._collect_used_names_stmt(s, names)
            if isinstance(expr.else_block, Block):
                for s in expr.else_block.stmts:
                    self._collect_used_names_stmt(s, names)
            elif isinstance(expr.else_block, IfExpr):
                self._collect_used_names_expr(expr.else_block, names)
        elif isinstance(expr, MatchExpr):
            self._collect_used_names_expr(expr.subject, names)
            for arm in expr.arms:
                if isinstance(arm.body, Block):
                    for s in arm.body.stmts:
                        self._collect_used_names_stmt(s, names)
                elif isinstance(arm.body, Expr):
                    self._collect_used_names_expr(arm.body, names)
        elif isinstance(expr, AssignExpr):
            self._collect_used_names_expr(expr.target, names)
            self._collect_used_names_expr(expr.value, names)
        elif isinstance(expr, IndexExpr):
            self._collect_used_names_expr(expr.object, names)
            self._collect_used_names_expr(expr.index, names)
        elif isinstance(expr, MethodCallExpr):
            self._collect_used_names_expr(expr.object, names)
            for a in expr.args:
                self._collect_used_names_expr(a, names)
        elif isinstance(expr, FieldAccessExpr):
            self._collect_used_names_expr(expr.object, names)
        elif isinstance(expr, ListLiteral):
            for e in expr.elements:
                self._collect_used_names_expr(e, names)
        elif isinstance(expr, MapLiteral):
            for entry in expr.entries:
                self._collect_used_names_expr(entry.key, names)
                self._collect_used_names_expr(entry.value, names)
        elif isinstance(expr, LambdaExpr):
            if isinstance(expr.body, Block):
                for s in expr.body.stmts:
                    self._collect_used_names_stmt(s, names)
            elif isinstance(expr.body, Expr):
                self._collect_used_names_expr(expr.body, names)
        elif isinstance(expr, RangeExpr):
            self._collect_used_names_expr(expr.start, names)
            self._collect_used_names_expr(expr.end, names)
        elif isinstance(expr, SomeExpr):
            self._collect_used_names_expr(expr.value, names)
        elif isinstance(expr, OkExpr):
            self._collect_used_names_expr(expr.value, names)
        elif isinstance(expr, ErrExpr):
            self._collect_used_names_expr(expr.value, names)
        elif isinstance(expr, ErrorPropExpr):
            self._collect_used_names_expr(expr.expr, names)
        elif isinstance(expr, InterpString):
            for part in expr.parts:
                if isinstance(part, Expr):
                    self._collect_used_names_expr(part, names)

    def _remove_dead_fns(self, program: Program) -> Program:
        """Remove private functions that are never referenced."""
        # Collect all names referenced in function bodies
        all_used: set[str] = set()
        fn_defs: dict[str, FnDef] = {}

        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                fn_defs[inner.name] = inner
                names: set[str] = set()
                for s in inner.body.stmts:
                    self._collect_used_names_stmt(s, names)
                all_used.update(names)

        # Keep main, public fns, non-fn definitions, and referenced fns
        new_defs: list[Definition] = []
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                if inner.name == "main" or inner.public or inner.name in all_used:
                    new_defs.append(defn)
                else:
                    self.stats.dead_fns_removed += 1
            else:
                new_defs.append(defn)

        program.definitions = new_defs
        return program


# ---------------------------------------------------------------------------
# Pass 3: Agent Communication Inlining
# ---------------------------------------------------------------------------


class AgentInliner:
    """Agent communication inlining pass.

    When an agent's on_message handler is a simple pure function (no state
    mutation, no spawning, no I/O), inline the transformation directly at
    the send site instead of going through the message queue.

    Also inlines single-stage pipes by replacing the pipe with a direct
    function call.
    """

    def __init__(self) -> None:
        self.stats = PassStats()
        # agent name → method body (for simple agents)
        self._simple_agents: dict[str, FnDef] = {}

    def run(self, program: Program) -> Program:
        """Run agent communication inlining."""
        # Phase 1: identify simple agents
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, AgentDef):
                self._analyze_agent(inner)

        # Phase 2: inline pipe definitions with single stages
        new_defs: list[Definition] = []
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, PipeDef):
                inlined = self._inline_pipe(inner)
                if inlined is not None:
                    new_defs.append(inlined)
                    self.stats.agents_inlined += 1
                else:
                    new_defs.append(defn)
            else:
                new_defs.append(defn)

        # Phase 3: inline send expressions to simple agents
        for defn in new_defs:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                self._inline_sends_in_fn(inner)

        program.definitions = new_defs
        return program

    def _analyze_agent(self, agent: AgentDef) -> None:
        """Check if an agent is simple enough to inline."""
        # Simple agent: has exactly one method, no state mutations,
        # no spawn/sync/send expressions
        if len(agent.methods) != 1:
            return
        method = agent.methods[0]
        if len(agent.state) > 0:
            return
        if self._has_side_effects(method.body):
            return
        self._simple_agents[agent.name] = method

    def _has_side_effects(self, block: Block) -> bool:
        """Check if a block contains side-effecting operations."""
        for stmt in block.stmts:
            if self._stmt_has_effects(stmt):
                return True
        return False

    def _stmt_has_effects(self, stmt: Stmt) -> bool:
        """Check if a statement has side effects."""
        if isinstance(stmt, ExprStmt):
            return self._expr_has_effects(stmt.expr)
        if isinstance(stmt, LetBinding):
            return self._expr_has_effects(stmt.value)
        if isinstance(stmt, ReturnStmt):
            return stmt.value is not None and self._expr_has_effects(stmt.value)
        if isinstance(stmt, (ForLoop, WhileLoop)):
            return True  # loops are potentially effectful
        return False

    def _expr_has_effects(self, expr: Expr) -> bool:
        """Check if an expression has side effects."""
        if isinstance(expr, (SpawnExpr, SyncExpr, SendExpr, SignalExpr)):
            return True
        if isinstance(expr, CallExpr):
            # Calls to print, println, etc. have effects
            if isinstance(expr.callee, Identifier) and expr.callee.name in (
                "print",
                "println",
            ):
                return True
        if isinstance(expr, BinaryExpr):
            return self._expr_has_effects(expr.left) or self._expr_has_effects(expr.right)
        if isinstance(expr, UnaryExpr):
            return self._expr_has_effects(expr.operand)
        if isinstance(expr, AssignExpr):
            return True  # assignments are side effects
        return False

    def _inline_pipe(self, pipe: PipeDef) -> FnDef | None:
        """Try to inline a single-stage pipe into a direct function.

        Only inline when the stage is a known simple agent whose handler
        can be expressed as a direct call. Otherwise, return None so the
        PipeDef is preserved for the emitter to handle.
        """
        if len(pipe.stages) != 1:
            return None

        stage = pipe.stages[0]
        if not isinstance(stage, Identifier):
            return None

        # Only inline if the stage maps to a known simple agent
        method = self._simple_agents.get(stage.name)
        if method is None:
            return None

        # Create a wrapper function that calls the agent's handler directly
        return FnDef(
            name=pipe.name,
            public=pipe.public,
            params=list(method.params),
            return_type=method.return_type,
            body=Block(
                stmts=[
                    ReturnStmt(
                        value=CallExpr(
                            callee=Identifier(name=f"{stage.name}_{method.name}"),
                            args=[Identifier(name=p.name) for p in method.params],
                        )
                    )
                ]
            ),
            span=pipe.span,
        )

    def _inline_sends_in_fn(self, fn: FnDef) -> None:
        """Inline send expressions to simple agents within a function."""
        fn.body = self._inline_sends_block(fn.body)

    def _inline_sends_block(self, block: Block) -> Block:
        """Inline sends in a block."""
        new_stmts: list[Stmt] = []
        for stmt in block.stmts:
            if isinstance(stmt, ExprStmt) and isinstance(stmt.expr, SendExpr):
                inlined = self._try_inline_send(stmt.expr)
                if inlined is not None:
                    new_stmts.append(ExprStmt(expr=inlined))
                    self.stats.agents_inlined += 1
                else:
                    new_stmts.append(stmt)
            else:
                new_stmts.append(stmt)
        block.stmts = new_stmts
        return block

    def _try_inline_send(self, send: SendExpr) -> Expr | None:
        """Try to inline a send to a simple agent as a direct call."""
        # Check if the target is a known simple agent
        if isinstance(send.target, FieldAccessExpr):
            if isinstance(send.target.object, Identifier):
                agent_name = send.target.object.name
                if agent_name in self._simple_agents:
                    method = self._simple_agents[agent_name]
                    # Replace send with direct call to the agent's method body
                    return CallExpr(
                        callee=Identifier(name=f"{agent_name}__{method.name}"),
                        args=[send.value],
                        span=send.span,
                    )
        return None


# ---------------------------------------------------------------------------
# Pass 4: Stream Fusion
# ---------------------------------------------------------------------------


class StreamFuser:
    """Stream fusion optimization pass.

    Fuses adjacent stream operations (map, filter) into single-pass
    operations by combining their lambda bodies.

    Example: `stream |> map(f) |> filter(g)` becomes a single fused
    operation that applies f then g in one pass.
    """

    def __init__(self) -> None:
        self.stats = PassStats()

    def run(self, program: Program) -> Program:
        """Run stream fusion on the entire program."""
        for defn in program.definitions:
            inner = defn.definition if isinstance(defn, DocComment) and defn.definition else defn
            if isinstance(inner, FnDef):
                self._fuse_fn(inner)
        return program

    def _fuse_fn(self, fn: FnDef) -> None:
        """Fuse streams within a function."""
        fn.body = self._fuse_block(fn.body)

    def _fuse_block(self, block: Block) -> Block:
        """Fuse stream operations in a block."""
        new_stmts: list[Stmt] = []
        for stmt in block.stmts:
            if isinstance(stmt, ExprStmt):
                stmt.expr = self._fuse_expr(stmt.expr)
            elif isinstance(stmt, LetBinding):
                stmt.value = self._fuse_expr(stmt.value)
            elif isinstance(stmt, ReturnStmt) and stmt.value is not None:
                stmt.value = self._fuse_expr(stmt.value)
            elif isinstance(stmt, ForLoop):
                stmt.iterable = self._fuse_expr(stmt.iterable)
                stmt.body = self._fuse_block(stmt.body)
            elif isinstance(stmt, WhileLoop):
                stmt.condition = self._fuse_expr(stmt.condition)
                stmt.body = self._fuse_block(stmt.body)
            new_stmts.append(stmt)
        block.stmts = new_stmts
        return block

    def _fuse_expr(self, expr: Expr) -> Expr:
        """Try to fuse stream operations in an expression."""
        if isinstance(expr, PipeExpr):
            expr.left = self._fuse_expr(expr.left)
            expr.right = self._fuse_expr(expr.right)
            # Try to fuse: left |> map(f) where left is already ... |> map(g)
            fused = self._try_fuse_pipe(expr)
            if fused is not None:
                return fused
            return expr

        if isinstance(expr, MethodCallExpr):
            expr.object = self._fuse_expr(expr.object)
            expr.args = [self._fuse_expr(a) for a in expr.args]
            # Try to fuse: obj.map(f) where obj is already ....map(g)
            fused = self._try_fuse_method_chain(expr)
            if fused is not None:
                return fused
            return expr

        if isinstance(expr, BinaryExpr):
            expr.left = self._fuse_expr(expr.left)
            expr.right = self._fuse_expr(expr.right)
            return expr

        if isinstance(expr, CallExpr):
            expr.callee = self._fuse_expr(expr.callee)
            expr.args = [self._fuse_expr(a) for a in expr.args]
            return expr

        if isinstance(expr, IfExpr):
            expr.condition = self._fuse_expr(expr.condition)
            expr.then_block = self._fuse_block(expr.then_block)
            if isinstance(expr.else_block, Block):
                expr.else_block = self._fuse_block(expr.else_block)
            return expr

        return expr

    def _try_fuse_pipe(self, pipe: PipeExpr) -> Expr | None:
        """Try to fuse two piped map/filter operations.

        `x |> map(f) |> map(g)` → `x |> map(compose(f, g))`
        `x |> map(f) |> filter(g)` → `x |> map_filter(f, g)`
        """
        # Check if right side is a map/filter call
        if not isinstance(pipe.right, CallExpr):
            return None
        if not isinstance(pipe.right.callee, Identifier):
            return None

        right_op = pipe.right.callee.name
        if right_op not in ("map", "filter"):
            return None

        # Check if left side is also a pipe ending in map/filter
        if not isinstance(pipe.left, PipeExpr):
            return None
        if not isinstance(pipe.left.right, CallExpr):
            return None
        if not isinstance(pipe.left.right.callee, Identifier):
            return None

        left_op = pipe.left.right.callee.name
        if left_op not in ("map", "filter"):
            return None

        # Fuse: map(f) |> map(g) → map(compose(f, g))
        if left_op == "map" and right_op == "map":
            if len(pipe.left.right.args) == 1 and len(pipe.right.args) == 1:
                f_arg = pipe.left.right.args[0]
                g_arg = pipe.right.args[0]

                # Create composed lambda: (x) => g(f(x))
                if isinstance(f_arg, LambdaExpr) and isinstance(g_arg, LambdaExpr):
                    param_name = f_arg.params[0].name if f_arg.params else "_x"
                    from mapanare.ast_nodes import Param

                    inner_call = CallExpr(
                        callee=Identifier(name="__fused_f"),
                        args=[Identifier(name=param_name)],
                    )
                    # Simplify: just nest the bodies
                    composed = LambdaExpr(
                        params=[Param(name=param_name)],
                        body=CallExpr(
                            callee=Identifier(name="__fused_g"),
                            args=[inner_call],
                        ),
                    )
                    fused_call = CallExpr(
                        callee=Identifier(name="map"),
                        args=[composed],
                        span=pipe.span,
                    )
                    self.stats.streams_fused += 1
                    return PipeExpr(
                        left=pipe.left.left,
                        right=fused_call,
                        span=pipe.span,
                    )

        # Fuse: map(f) |> filter(g) → map_filter(f, g)
        if left_op == "map" and right_op == "filter":
            if len(pipe.left.right.args) >= 1 and len(pipe.right.args) >= 1:
                f_arg = pipe.left.right.args[0]
                g_arg = pipe.right.args[0]
                fused_call = CallExpr(
                    callee=Identifier(name="map_filter"),
                    args=[f_arg, g_arg],
                    span=pipe.span,
                )
                self.stats.streams_fused += 1
                return PipeExpr(
                    left=pipe.left.left,
                    right=fused_call,
                    span=pipe.span,
                )

        # Fuse: filter(f) |> filter(g) → filter(compose_and(f, g))
        if left_op == "filter" and right_op == "filter":
            if len(pipe.left.right.args) >= 1 and len(pipe.right.args) >= 1:
                f_arg = pipe.left.right.args[0]
                g_arg = pipe.right.args[0]
                fused_call = CallExpr(
                    callee=Identifier(name="filter"),
                    args=[
                        CallExpr(
                            callee=Identifier(name="__compose_and"),
                            args=[f_arg, g_arg],
                        )
                    ],
                    span=pipe.span,
                )
                self.stats.streams_fused += 1
                return PipeExpr(
                    left=pipe.left.left,
                    right=fused_call,
                    span=pipe.span,
                )

        return None

    def _try_fuse_method_chain(self, call: MethodCallExpr) -> Expr | None:
        """Try to fuse chained method calls like stream.map(f).map(g).

        `stream.map(f).map(g)` → `stream.map(compose(f, g))`
        `stream.map(f).filter(g)` → `stream.map_filter(f, g)`
        """
        if call.method not in ("map", "filter"):
            return None
        if not isinstance(call.object, MethodCallExpr):
            return None

        inner = call.object
        if inner.method not in ("map", "filter"):
            return None

        outer_op = call.method
        inner_op = inner.method

        # Fuse: .map(f).map(g) → .map(compose(f, g))
        if inner_op == "map" and outer_op == "map":
            if len(inner.args) >= 1 and len(call.args) >= 1:
                f_arg = inner.args[0]
                g_arg = call.args[0]

                if isinstance(f_arg, LambdaExpr) and isinstance(g_arg, LambdaExpr):
                    param_name = f_arg.params[0].name if f_arg.params else "_x"
                    from mapanare.ast_nodes import Param

                    composed = LambdaExpr(
                        params=[Param(name=param_name)],
                        body=CallExpr(
                            callee=Identifier(name="__fused_g"),
                            args=[
                                CallExpr(
                                    callee=Identifier(name="__fused_f"),
                                    args=[Identifier(name=param_name)],
                                )
                            ],
                        ),
                    )
                    self.stats.streams_fused += 1
                    return MethodCallExpr(
                        object=inner.object,
                        method="map",
                        args=[composed],
                        span=call.span,
                    )

        # Fuse: .map(f).filter(g) → .map_filter(f, g)
        if inner_op == "map" and outer_op == "filter":
            if len(inner.args) >= 1 and len(call.args) >= 1:
                self.stats.streams_fused += 1
                return MethodCallExpr(
                    object=inner.object,
                    method="map_filter",
                    args=[inner.args[0], call.args[0]],
                    span=call.span,
                )

        # Fuse: .filter(f).filter(g) → .filter(compose_and(f, g))
        if inner_op == "filter" and outer_op == "filter":
            if len(inner.args) >= 1 and len(call.args) >= 1:
                self.stats.streams_fused += 1
                return MethodCallExpr(
                    object=inner.object,
                    method="filter",
                    args=[
                        CallExpr(
                            callee=Identifier(name="__compose_and"),
                            args=[inner.args[0], call.args[0]],
                        )
                    ],
                    span=call.span,
                )

        return None


# ---------------------------------------------------------------------------
# Pipeline: run all passes
# ---------------------------------------------------------------------------


def optimize(program: Program, level: OptLevel = OptLevel.O2) -> tuple[Program, PassStats]:
    """Run optimization passes on a program at the given optimization level.

    Returns the optimized program and aggregate statistics.
    """
    if level == OptLevel.O0:
        return program, PassStats()

    stats = PassStats()

    # O1+: Constant folding and propagation (iterate to fixed point)
    if level >= OptLevel.O1:
        folder = ConstantFolder()
        iterations = 0
        max_iterations = 10
        while iterations < max_iterations:
            folder.stats = PassStats()
            program = folder.run(program)
            if folder.stats.constants_folded + folder.stats.constants_propagated == 0:
                break
            stats.constants_folded += folder.stats.constants_folded
            stats.constants_propagated += folder.stats.constants_propagated
            iterations += 1

    # O2+: Dead code elimination
    if level >= OptLevel.O2:
        dce = DeadCodeEliminator()
        program = dce.run(program)
        stats.dead_stmts_removed += dce.stats.dead_stmts_removed
        stats.dead_fns_removed += dce.stats.dead_fns_removed
        stats.dead_branches_removed += dce.stats.dead_branches_removed

    # O2+: Agent communication inlining
    if level >= OptLevel.O2:
        inliner = AgentInliner()
        program = inliner.run(program)
        stats.agents_inlined += inliner.stats.agents_inlined

    # O3: Stream fusion
    if level >= OptLevel.O3:
        fuser = StreamFuser()
        program = fuser.run(program)
        stats.streams_fused += fuser.stats.streams_fused

    return program, stats
