"""LLVM IR emitter -- compiles AST to LLVM IR.

Phase 4.1: Type mapping from Mapanare types to LLVM IR types via llvmlite.
Phase 4.2: IR emitter — AST nodes to LLVM instructions.
Phase 5.1: Tensor operations — element-wise SIMD, matmul runtime calls.
"""

from __future__ import annotations

from llvmlite import ir

from mapa.ast_nodes import (
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    ExprStmt,
    FloatLiteral,
    FnDef,
    ForLoop,
    GenericType,
    Identifier,
    IfExpr,
    IntLiteral,
    LetBinding,
    LiteralPattern,
    MatchArm,
    MatchExpr,
    NamedType,
    PipeExpr,
    Program,
    ReturnStmt,
    StringLiteral,
    TensorType,
    TypeExpr,
    UnaryExpr,
    WildcardPattern,
)

# ---------------------------------------------------------------------------
# LLVM type constants
# ---------------------------------------------------------------------------

# Primitives
LLVM_INT = ir.IntType(64)  # Int → i64
LLVM_FLOAT = ir.DoubleType()  # Float → double
LLVM_BOOL = ir.IntType(1)  # Bool → i1
LLVM_CHAR = ir.IntType(8)  # Char → i8
LLVM_VOID = ir.VoidType()  # Void

# String: { i8*, i64 } — pointer to data + length
LLVM_STRING = ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])


def option_type(inner: ir.Type) -> ir.LiteralStructType:
    """Option<T> → { i1, T } — tag (1=Some, 0=None) + value."""
    return ir.LiteralStructType([LLVM_BOOL, inner])


def result_type(ok_ty: ir.Type, err_ty: ir.Type) -> ir.LiteralStructType:
    """Result<T, E> → { i1, { T, E } } — tag (1=Ok, 0=Err) + payload union.

    Since LLVM doesn't have real unions, we store both fields and the tag
    indicates which is valid. The struct size is the sum of both types.
    """
    return ir.LiteralStructType([LLVM_BOOL, ir.LiteralStructType([ok_ty, err_ty])])


def tensor_type(element_ty: ir.Type) -> ir.LiteralStructType:
    """Tensor<T>[...] → { T*, i64, i64*, i64 }

    Layout:
      - data:  pointer to contiguous heap-allocated element buffer
      - ndim:  number of dimensions (i64)
      - shape: pointer to shape array (i64* — ndim elements)
      - size:  total number of elements (i64)
    """
    return ir.LiteralStructType(
        [element_ty.as_pointer(), LLVM_INT, LLVM_INT.as_pointer(), LLVM_INT]
    )


def list_type(element_ty: ir.Type) -> ir.LiteralStructType:
    """List<T> → { T*, i64, i64 } — data pointer, length, capacity."""
    return ir.LiteralStructType([element_ty.as_pointer(), LLVM_INT, LLVM_INT])


def map_type(key_ty: ir.Type, val_ty: ir.Type) -> ir.LiteralStructType:
    """Map<K, V> → opaque pointer (hash map implementation detail).

    Represented as { i8*, i64 } — pointer to hash table + count.
    """
    return ir.LiteralStructType([ir.IntType(8).as_pointer(), LLVM_INT])


# ---------------------------------------------------------------------------
# Named type table
# ---------------------------------------------------------------------------

_PRIMITIVE_MAP: dict[str, ir.Type] = {
    "Int": LLVM_INT,
    "Float": LLVM_FLOAT,
    "Bool": LLVM_BOOL,
    "Char": LLVM_CHAR,
    "String": LLVM_STRING,
    "Void": LLVM_VOID,
}


# ---------------------------------------------------------------------------
# Type resolver: Mapanare TypeExpr → LLVM ir.Type
# ---------------------------------------------------------------------------


class TypeMapper:
    """Resolves Mapanare AST type expressions to llvmlite IR types."""

    def __init__(self) -> None:
        self._struct_types: dict[str, ir.Type] = {}

    def register_struct(self, name: str, llvm_ty: ir.Type) -> None:
        """Register a named struct type (for user-defined structs)."""
        self._struct_types[name] = llvm_ty

    def resolve(self, ty: TypeExpr) -> ir.Type:
        """Convert a Mapanare TypeExpr AST node to the corresponding LLVM type."""
        if isinstance(ty, NamedType):
            return self._resolve_named(ty)
        if isinstance(ty, GenericType):
            return self._resolve_generic(ty)
        if isinstance(ty, TensorType):
            return self._resolve_tensor(ty)
        raise TypeError(f"Unsupported Mapanare type expression: {type(ty).__name__}")

    # -- private helpers -----------------------------------------------------

    def _resolve_named(self, ty: NamedType) -> ir.Type:
        if ty.name in _PRIMITIVE_MAP:
            return _PRIMITIVE_MAP[ty.name]
        if ty.name in self._struct_types:
            return self._struct_types[ty.name]
        raise TypeError(f"Unknown Mapanare type: {ty.name}")

    def _resolve_generic(self, ty: GenericType) -> ir.Type:
        name = ty.name

        if name == "Option":
            if len(ty.args) != 1:
                raise TypeError("Option expects exactly 1 type argument")
            inner = self.resolve(ty.args[0])
            return option_type(inner)

        if name == "Result":
            if len(ty.args) != 2:
                raise TypeError("Result expects exactly 2 type arguments")
            ok = self.resolve(ty.args[0])
            err = self.resolve(ty.args[1])
            return result_type(ok, err)

        if name == "List":
            if len(ty.args) != 1:
                raise TypeError("List expects exactly 1 type argument")
            elem = self.resolve(ty.args[0])
            return list_type(elem)

        if name == "Map":
            if len(ty.args) != 2:
                raise TypeError("Map expects exactly 2 type arguments")
            key = self.resolve(ty.args[0])
            val = self.resolve(ty.args[1])
            return map_type(key, val)

        raise TypeError(f"Unknown generic Mapanare type: {name}")

    def _resolve_tensor(self, ty: TensorType) -> ir.Type:
        elem = self.resolve(ty.element_type)
        return tensor_type(elem)


# ---------------------------------------------------------------------------
# IR Emitter: Mapanare AST → LLVM IR module
# ---------------------------------------------------------------------------


class LLVMEmitter:
    """Compiles an Mapanare AST into an LLVM IR module using llvmlite."""

    def __init__(
        self,
        module_name: str = "mapanare_module",
        target_triple: str | None = None,
        data_layout: str | None = None,
    ) -> None:
        self.module = ir.Module(name=module_name)
        if target_triple is not None:
            self.module.triple = target_triple
        if data_layout is not None:
            self.module.data_layout = data_layout
        self.type_mapper = TypeMapper()
        self._builder: ir.IRBuilder | None = None
        # Variable name → alloca instruction (stack slot)
        self._locals: dict[str, ir.AllocaInstr] = {}
        # Function name → LLVM function
        self._functions: dict[str, ir.Function] = {}
        # Track mutable variables
        self._mutables: set[str] = set()

    @property
    def builder(self) -> ir.IRBuilder:
        assert self._builder is not None, "No active IRBuilder — not inside a function"
        return self._builder

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def emit_program(self, program: Program) -> ir.Module:
        """Emit an entire Mapanare program to an LLVM module."""
        for defn in program.definitions:
            if isinstance(defn, FnDef):
                self.emit_fn(defn)
        return self.module

    # -----------------------------------------------------------------------
    # Task 1: fn → LLVM function declarations
    # -----------------------------------------------------------------------

    def emit_fn(self, node: FnDef) -> ir.Function:
        """Emit a function definition as an LLVM function."""
        # Resolve parameter types
        param_types: list[ir.Type] = []
        for p in node.params:
            if p.type_annotation is not None:
                param_types.append(self.type_mapper.resolve(p.type_annotation))
            else:
                param_types.append(LLVM_INT)  # default to i64

        # Resolve return type
        if node.return_type is not None:
            ret_type = self.type_mapper.resolve(node.return_type)
        else:
            ret_type = LLVM_VOID

        fn_type = ir.FunctionType(ret_type, param_types)
        func = ir.Function(self.module, fn_type, name=node.name)

        # Name the parameters
        for i, p in enumerate(node.params):
            func.args[i].name = p.name

        self._functions[node.name] = func

        # Create entry block and builder
        block = func.append_basic_block(name="entry")
        old_builder = self._builder
        old_locals = self._locals.copy()
        old_mutables = self._mutables.copy()
        self._builder = ir.IRBuilder(block)
        self._locals = {}
        self._mutables = set()

        # Alloca params so they can be loaded/stored like locals
        for i, p in enumerate(node.params):
            alloca = self.builder.alloca(param_types[i], name=p.name)
            self.builder.store(func.args[i], alloca)
            self._locals[p.name] = alloca

        # Emit function body
        self._emit_block(node.body)

        # If the block has no terminator, add a default return
        if not self.builder.block.is_terminated:
            if isinstance(ret_type, ir.VoidType):
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(ret_type, 0))

        # Restore state
        self._builder = old_builder
        self._locals = old_locals
        self._mutables = old_mutables

        return func

    # -----------------------------------------------------------------------
    # Block & statement emission
    # -----------------------------------------------------------------------

    def _emit_block(self, block: Block) -> ir.Value | None:
        """Emit all statements in a block, returning the last expression value."""
        result: ir.Value | None = None
        for stmt in block.stmts:
            result = self._emit_stmt(stmt)
        return result

    def _emit_stmt(self, stmt: object) -> ir.Value | None:
        """Emit a single statement."""
        if isinstance(stmt, LetBinding):
            return self._emit_let(stmt)
        if isinstance(stmt, ReturnStmt):
            return self._emit_return(stmt)
        if isinstance(stmt, ExprStmt):
            return self._emit_expr(stmt.expr)
        if isinstance(stmt, ForLoop):
            return self._emit_for(stmt)
        return None

    # -----------------------------------------------------------------------
    # Task 7: let → stack alloca + store/load
    # -----------------------------------------------------------------------

    def _emit_let(self, node: LetBinding) -> ir.Value:
        """Emit a let binding as alloca + store."""
        val = self._emit_expr(node.value)
        alloca = self.builder.alloca(val.type, name=node.name)
        self.builder.store(val, alloca)
        self._locals[node.name] = alloca
        if node.mutable:
            self._mutables.add(node.name)
        return val

    # -----------------------------------------------------------------------
    # Return statement
    # -----------------------------------------------------------------------

    def _emit_return(self, node: ReturnStmt) -> ir.Value | None:
        """Emit a return statement."""
        if node.value is not None:
            val = self._emit_expr(node.value)
            self.builder.ret(val)
            return val
        self.builder.ret_void()
        return None

    # -----------------------------------------------------------------------
    # Expression dispatch
    # -----------------------------------------------------------------------

    def _emit_expr(self, expr: object) -> ir.Value:
        """Emit an expression, returning its LLVM value."""
        if isinstance(expr, IntLiteral):
            return ir.Constant(LLVM_INT, expr.value)

        if isinstance(expr, FloatLiteral):
            return ir.Constant(LLVM_FLOAT, expr.value)

        if isinstance(expr, BoolLiteral):
            return ir.Constant(LLVM_BOOL, int(expr.value))

        if isinstance(expr, StringLiteral):
            return self._emit_string_literal(expr)

        if isinstance(expr, Identifier):
            return self._emit_identifier(expr)

        if isinstance(expr, BinaryExpr):
            return self._emit_binary(expr)

        if isinstance(expr, UnaryExpr):
            return self._emit_unary(expr)

        if isinstance(expr, CallExpr):
            return self._emit_call(expr)

        if isinstance(expr, PipeExpr):
            return self._emit_pipe(expr)

        if isinstance(expr, IfExpr):
            return self._emit_if(expr)

        if isinstance(expr, MatchExpr):
            return self._emit_match(expr)

        if isinstance(expr, AssignExpr):
            return self._emit_assign(expr)

        raise NotImplementedError(f"Cannot emit expression: {type(expr).__name__}")

    # -----------------------------------------------------------------------
    # Literals & identifiers
    # -----------------------------------------------------------------------

    def _emit_string_literal(self, node: StringLiteral) -> ir.Value:
        """Emit a string literal as a global constant."""
        encoded = node.value.encode("utf-8")
        str_const = ir.Constant(ir.ArrayType(LLVM_CHAR, len(encoded)), bytearray(encoded))
        gname = self.module.get_unique_name("str")
        global_str = ir.GlobalVariable(self.module, str_const.type, name=gname)
        global_str.global_constant = True
        global_str.initializer = str_const
        global_str.linkage = "private"

        # GEP to get i8* pointer
        zero = ir.Constant(LLVM_INT, 0)
        ptr = self.builder.gep(global_str, [zero, zero], inbounds=True, name="str_ptr")

        # Build { i8*, i64 } struct
        str_struct = ir.Constant(LLVM_STRING, ir.Undefined)
        str_struct = self.builder.insert_value(str_struct, ptr, 0, name="str_data")
        str_struct = self.builder.insert_value(
            str_struct, ir.Constant(LLVM_INT, len(encoded)), 1, name="str_len"
        )
        return str_struct

    def _emit_identifier(self, node: Identifier) -> ir.Value:
        """Load a variable from its stack slot."""
        if node.name in self._locals:
            return self.builder.load(self._locals[node.name], name=node.name)
        if node.name in self._functions:
            return self._functions[node.name]
        raise NameError(f"Undefined variable: {node.name}")

    # -----------------------------------------------------------------------
    # Task 2: Arithmetic expressions → LLVM arithmetic instructions
    # -----------------------------------------------------------------------

    def _emit_binary(self, node: BinaryExpr) -> ir.Value:
        """Emit a binary expression."""
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right)

        # Determine if we're working with ints or floats
        is_float = isinstance(left.type, ir.DoubleType) or isinstance(right.type, ir.DoubleType)

        # Arithmetic
        if node.op == "+":
            if is_float:
                return self.builder.fadd(left, right, name="fadd")
            return self.builder.add(left, right, name="add")

        if node.op == "-":
            if is_float:
                return self.builder.fsub(left, right, name="fsub")
            return self.builder.sub(left, right, name="sub")

        if node.op == "*":
            if is_float:
                return self.builder.fmul(left, right, name="fmul")
            return self.builder.mul(left, right, name="mul")

        if node.op == "/":
            if is_float:
                return self.builder.fdiv(left, right, name="fdiv")
            return self.builder.sdiv(left, right, name="sdiv")

        if node.op == "%":
            if is_float:
                return self.builder.frem(left, right, name="frem")
            return self.builder.srem(left, right, name="srem")

        # Matrix multiply (@ operator) — emitted as a call to runtime matmul
        if node.op == "@":
            if "__mapanare_matmul" not in self._functions:
                # Declare the external matmul runtime function
                # Signature: mapanare_matmul(a: Tensor*, b: Tensor*) -> Tensor*
                tensor_ptr = ir.IntType(8).as_pointer()
                matmul_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr])
                matmul_fn = ir.Function(self.module, matmul_ty, name="__mapanare_matmul")
                self._functions["__mapanare_matmul"] = matmul_fn
            matmul_fn = self._functions["__mapanare_matmul"]
            return self.builder.call(matmul_fn, [left, right], name="matmul")

        # ---------------------------------------------------------------
        # Task 3: Boolean expressions → LLVM comparison instructions
        # ---------------------------------------------------------------

        if node.op == "==":
            if is_float:
                return self.builder.fcmp_ordered("==", left, right, name="feq")
            return self.builder.icmp_signed("==", left, right, name="eq")

        if node.op == "!=":
            if is_float:
                return self.builder.fcmp_ordered("!=", left, right, name="fne")
            return self.builder.icmp_signed("!=", left, right, name="ne")

        if node.op == "<":
            if is_float:
                return self.builder.fcmp_ordered("<", left, right, name="flt")
            return self.builder.icmp_signed("<", left, right, name="lt")

        if node.op == "<=":
            if is_float:
                return self.builder.fcmp_ordered("<=", left, right, name="fle")
            return self.builder.icmp_signed("<=", left, right, name="le")

        if node.op == ">":
            if is_float:
                return self.builder.fcmp_ordered(">", left, right, name="fgt")
            return self.builder.icmp_signed(">", left, right, name="gt")

        if node.op == ">=":
            if is_float:
                return self.builder.fcmp_ordered(">=", left, right, name="fge")
            return self.builder.icmp_signed(">=", left, right, name="ge")

        # Logical
        if node.op == "&&":
            return self.builder.and_(left, right, name="and")

        if node.op == "||":
            return self.builder.or_(left, right, name="or")

        raise NotImplementedError(f"Unknown binary operator: {node.op}")

    def _emit_unary(self, node: UnaryExpr) -> ir.Value:
        """Emit a unary expression."""
        operand = self._emit_expr(node.operand)

        if node.op == "-":
            if isinstance(operand.type, ir.DoubleType):
                return self.builder.fneg(operand, name="fneg")
            return self.builder.neg(operand, name="neg")

        if node.op == "!":
            return self.builder.not_(operand, name="not")

        raise NotImplementedError(f"Unknown unary operator: {node.op}")

    # -----------------------------------------------------------------------
    # Task 6: Function calls → LLVM call instructions
    # -----------------------------------------------------------------------

    def _emit_call(self, node: CallExpr) -> ir.Value:
        """Emit a function call instruction."""
        # Resolve the callee
        if isinstance(node.callee, Identifier):
            if node.callee.name not in self._functions:
                raise NameError(f"Undefined function: {node.callee.name}")
            func = self._functions[node.callee.name]
        else:
            func = self._emit_expr(node.callee)

        args = [self._emit_expr(a) for a in node.args]
        return self.builder.call(func, args, name="call")

    # -----------------------------------------------------------------------
    # Task 9: |> → inlined LLVM call chain
    # -----------------------------------------------------------------------

    def _emit_pipe(self, node: PipeExpr) -> ir.Value:
        """Emit a pipe expression as an inlined call chain.

        `a |> f |> g` becomes `g(f(a))`.
        """
        left_val = self._emit_expr(node.left)

        # The right side should be a callable (Identifier or CallExpr)
        if isinstance(node.right, Identifier):
            # f(left_val)
            if node.right.name not in self._functions:
                raise NameError(f"Undefined function: {node.right.name}")
            func = self._functions[node.right.name]
            return self.builder.call(func, [left_val], name="pipe_call")

        if isinstance(node.right, CallExpr) and isinstance(node.right.callee, Identifier):
            # f(extra_args...)(left_val) → f(left_val, extra_args...)
            if node.right.callee.name not in self._functions:
                raise NameError(f"Undefined function: {node.right.callee.name}")
            func = self._functions[node.right.callee.name]
            args = [left_val] + [self._emit_expr(a) for a in node.right.args]
            return self.builder.call(func, args, name="pipe_call")

        raise NotImplementedError("Pipe RHS must be an identifier or call expression")

    # -----------------------------------------------------------------------
    # Task 4: if/else → basic blocks + branch instructions
    # -----------------------------------------------------------------------

    def _emit_if(self, node: IfExpr) -> ir.Value:
        """Emit an if/else as basic blocks with conditional branches."""
        cond = self._emit_expr(node.condition)
        func = self.builder.function

        then_bb = func.append_basic_block(name="if.then")
        else_bb = func.append_basic_block(name="if.else")
        merge_bb = func.append_basic_block(name="if.merge")

        self.builder.cbranch(cond, then_bb, else_bb)

        # Then block
        self._builder = ir.IRBuilder(then_bb)
        then_val = self._emit_block(node.then_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        then_exit_bb = self.builder.block

        # Else block
        self._builder = ir.IRBuilder(else_bb)
        if node.else_block is not None:
            if isinstance(node.else_block, IfExpr):
                else_val = self._emit_if(node.else_block)
            else:
                else_val = self._emit_block(node.else_block)
        else:
            else_val = None
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        else_exit_bb = self.builder.block

        # Merge block
        self._builder = ir.IRBuilder(merge_bb)

        # If both branches produce values of the same type, create a phi node
        if then_val is not None and else_val is not None and then_val.type == else_val.type:
            phi = self.builder.phi(then_val.type, name="if.val")
            phi.add_incoming(then_val, then_exit_bb)
            phi.add_incoming(else_val, else_exit_bb)
            return phi

        # Return a dummy zero value
        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Task 5: for/in → LLVM loop with phi nodes
    # -----------------------------------------------------------------------

    def _emit_for(self, node: ForLoop) -> ir.Value:
        """Emit a for/in loop over a range as LLVM loop with phi node.

        Compiles `for x in start..end { body }` to:
          - preheader: compute start and end
          - header: phi node for loop variable, compare with end
          - body: emit body, increment counter
          - exit: continue after loop
        """
        from mapa.ast_nodes import RangeExpr

        func = self.builder.function

        if not isinstance(node.iterable, RangeExpr):
            raise NotImplementedError("for/in currently only supports range iterables")

        # Evaluate range bounds in current block
        start_val = self._emit_expr(node.iterable.start)
        end_val = self._emit_expr(node.iterable.end)

        # Create blocks
        header_bb = func.append_basic_block(name="for.header")
        body_bb = func.append_basic_block(name="for.body")
        exit_bb = func.append_basic_block(name="for.exit")

        # Branch from current block to header
        preheader_bb = self.builder.block
        self.builder.branch(header_bb)

        # Header: phi node for loop variable
        self._builder = ir.IRBuilder(header_bb)
        phi = self.builder.phi(LLVM_INT, name=node.var_name)
        phi.add_incoming(start_val, preheader_bb)

        # Store loop variable so body can access it
        loop_alloca = self.builder.alloca(LLVM_INT, name=f"{node.var_name}.addr")
        self.builder.store(phi, loop_alloca)
        old_var = self._locals.get(node.var_name)
        self._locals[node.var_name] = loop_alloca

        # Condition: i < end (or i <= end for inclusive)
        if node.iterable.inclusive:
            cmp = self.builder.icmp_signed("<=", phi, end_val, name="for.cond")
        else:
            cmp = self.builder.icmp_signed("<", phi, end_val, name="for.cond")
        self.builder.cbranch(cmp, body_bb, exit_bb)

        # Body
        self._builder = ir.IRBuilder(body_bb)
        self._emit_block(node.body)

        # Increment loop variable
        next_val = self.builder.add(phi, ir.Constant(LLVM_INT, 1), name="for.next")
        if not self.builder.block.is_terminated:
            self.builder.branch(header_bb)
        body_exit_bb = self.builder.block

        # Add incoming from body back-edge
        phi.add_incoming(next_val, body_exit_bb)

        # Restore and continue at exit
        if old_var is not None:
            self._locals[node.var_name] = old_var
        else:
            del self._locals[node.var_name]
        self._builder = ir.IRBuilder(exit_bb)

        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Task 8: match → LLVM switch + conditional branches
    # -----------------------------------------------------------------------

    def _emit_match(self, node: MatchExpr) -> ir.Value:
        """Emit a match expression as LLVM switch + conditional branches.

        Integer literal patterns use the LLVM switch instruction.
        Wildcard patterns become the switch default.
        """
        subject = self._emit_expr(node.subject)
        func = self.builder.function

        merge_bb = func.append_basic_block(name="match.merge")

        # Separate arms into literal arms and default (wildcard) arm
        literal_arms: list[tuple[int, MatchArm]] = []
        default_arm: MatchArm | None = None

        for arm in node.arms:
            if isinstance(arm.pattern, LiteralPattern) and isinstance(
                arm.pattern.value, IntLiteral
            ):
                literal_arms.append((arm.pattern.value.value, arm))
            elif isinstance(arm.pattern, WildcardPattern):
                default_arm = arm
            else:
                literal_arms.append((0, arm))

        # Create basic blocks for each arm
        arm_blocks: list[ir.Block] = []
        for _ in literal_arms:
            arm_blocks.append(func.append_basic_block(name="match.arm"))

        default_bb = func.append_basic_block(name="match.default")

        # Build switch instruction
        switch = self.builder.switch(subject, default_bb)
        for i, (val, _arm) in enumerate(literal_arms):
            switch.add_case(ir.Constant(LLVM_INT, val), arm_blocks[i])

        # Emit each literal arm
        arm_values: list[tuple[ir.Value, ir.Block]] = []
        for i, (_val, arm) in enumerate(literal_arms):
            self._builder = ir.IRBuilder(arm_blocks[i])
            if isinstance(arm.body, Block):
                result = self._emit_block(arm.body)
            else:
                result = self._emit_expr(arm.body)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)
            if result is not None:
                arm_values.append((result, self.builder.block))

        # Emit default arm
        self._builder = ir.IRBuilder(default_bb)
        if default_arm is not None:
            if isinstance(default_arm.body, Block):
                default_result = self._emit_block(default_arm.body)
            else:
                default_result = self._emit_expr(default_arm.body)
        else:
            default_result = ir.Constant(LLVM_INT, 0)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        if default_result is not None:
            arm_values.append((default_result, self.builder.block))

        # Merge block
        self._builder = ir.IRBuilder(merge_bb)

        # If all arms produced values of same type, phi them together
        if arm_values and all(v.type == arm_values[0][0].type for v, _bb in arm_values):
            phi = self.builder.phi(arm_values[0][0].type, name="match.val")
            for val, bb in arm_values:
                phi.add_incoming(val, bb)
            return phi

        return ir.Constant(LLVM_INT, 0)

    # -----------------------------------------------------------------------
    # Tensor runtime helpers (Phase 5.1)
    # -----------------------------------------------------------------------

    def _declare_tensor_runtime(self, name: str) -> ir.Function:
        """Declare an external tensor runtime function if not already declared.

        All tensor runtime functions use opaque pointer (i8*) for tensor structs,
        following C FFI conventions.
        """
        if name in self._functions:
            return self._functions[name]

        tensor_ptr = ir.IntType(8).as_pointer()
        # LLVM_INT used as device kind enum (i64)
        device_kind_ty = LLVM_INT

        # Element-wise ops: (Tensor*, Tensor*) -> Tensor*
        if name in (
            "__mapanare_tensor_add",
            "__mapanare_tensor_sub",
            "__mapanare_tensor_mul",
            "__mapanare_tensor_div",
            "__mapanare_matmul",
        ):
            fn_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr])
        # GPU dispatch ops: (Tensor*, Tensor*, device_kind) -> Tensor*
        elif name in (
            "__mapanare_tensor_add_dispatch",
            "__mapanare_tensor_sub_dispatch",
            "__mapanare_tensor_mul_dispatch",
            "__mapanare_tensor_div_dispatch",
            "__mapanare_tensor_matmul_dispatch",
        ):
            fn_ty = ir.FunctionType(tensor_ptr, [tensor_ptr, tensor_ptr, device_kind_ty])
        # Tensor alloc: (i64 ndim, i64* shape, i64 elem_size) -> Tensor*
        elif name == "__mapanare_tensor_alloc":
            fn_ty = ir.FunctionType(tensor_ptr, [LLVM_INT, LLVM_INT.as_pointer(), LLVM_INT])
        # Tensor free: (Tensor*) -> void
        elif name == "__mapanare_tensor_free":
            fn_ty = ir.FunctionType(LLVM_VOID, [tensor_ptr])
        # Shape check: (Tensor*, Tensor*) -> i1
        elif name == "__mapanare_tensor_shape_eq":
            fn_ty = ir.FunctionType(LLVM_BOOL, [tensor_ptr, tensor_ptr])
        # GPU detection: () -> i8* (detection struct pointer)
        elif name == "__mapanare_detect_gpus":
            fn_ty = ir.FunctionType(tensor_ptr, [])
        else:
            raise ValueError(f"Unknown tensor runtime function: {name}")

        func = ir.Function(self.module, fn_ty, name=name)
        self._functions[name] = func
        return func

    def _emit_tensor_elementwise_loop(self, a_ptr: ir.Value, b_ptr: ir.Value, op: str) -> ir.Value:
        """Emit an element-wise tensor operation as a vectorizable loop.

        Generates LLVM IR with loop structure that LLVM's auto-vectorizer
        can convert to SIMD instructions (SSE/AVX/NEON) when optimizing.

        For the interpreter/Python path, we call the runtime helper instead.
        """
        # Call the appropriate runtime function
        if op == "+":
            fn = self._declare_tensor_runtime("__mapanare_tensor_add")
        elif op == "-":
            fn = self._declare_tensor_runtime("__mapanare_tensor_sub")
        elif op == "*":
            fn = self._declare_tensor_runtime("__mapanare_tensor_mul")
        elif op == "/":
            fn = self._declare_tensor_runtime("__mapanare_tensor_div")
        else:
            raise NotImplementedError(f"Unknown tensor elementwise op: {op}")

        return self.builder.call(fn, [a_ptr, b_ptr], name=f"tensor_{op}")

    # -----------------------------------------------------------------------
    # Assignment expression
    # -----------------------------------------------------------------------

    def _emit_assign(self, node: AssignExpr) -> ir.Value:
        """Emit an assignment to a mutable variable."""
        if not isinstance(node.target, Identifier):
            raise NotImplementedError("Assignment target must be an identifier")
        name = node.target.name
        if name not in self._locals:
            raise NameError(f"Undefined variable: {name}")

        val = self._emit_expr(node.value)

        if node.op == "=":
            self.builder.store(val, self._locals[name])
            return val

        # Compound assignment: +=, -=, *=, /=
        current = self.builder.load(self._locals[name], name=f"{name}.cur")
        if node.op == "+=":
            result = self.builder.add(current, val, name="add_assign")
        elif node.op == "-=":
            result = self.builder.sub(current, val, name="sub_assign")
        elif node.op == "*=":
            result = self.builder.mul(current, val, name="mul_assign")
        elif node.op == "/=":
            result = self.builder.sdiv(current, val, name="div_assign")
        else:
            raise NotImplementedError(f"Unknown assignment operator: {node.op}")

        self.builder.store(result, self._locals[name])
        return result
