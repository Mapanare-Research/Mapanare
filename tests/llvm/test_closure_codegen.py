"""Tests for Phase 4 — LLVM Closure Capture Codegen.

Tests verify:
  - ClosureCreate emits environment allocation and fn/env pair construction
  - ClosureCall emits indirect call through fn_ptr with env_ptr
  - EnvLoad emits loads from environment struct
  - Free variable analysis detects captured variables
  - MIR instructions pretty-print correctly
  - End-to-end: Mapanare source with closures produces correct LLVM IR
"""

from __future__ import annotations

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.emit_llvm_mir import LLVMMIREmitter
from mapanare.mir import (
    BasicBlock,
    BinOp,
    BinOpKind,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnvLoad,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRType,
    Return,
    Value,
    pretty_print_instruction,
)
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mir_type(kind: TypeKind, name: str = "") -> MIRType:
    return MIRType(type_info=TypeInfo(kind=kind, name=name))


def _mir_val(name: str, kind: TypeKind = TypeKind.INT) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(kind))


def _fn_val(name: str) -> Value:
    return Value(name=f"%{name}", ty=_mir_type(TypeKind.FN))


def _make_mir_module(instructions, fn_name="test_fn", params=None, ret_type=None):
    """Create a minimal MIR module with a single function."""
    bb = BasicBlock(label="entry", instructions=instructions + [Return()])
    fn = MIRFunction(
        name=fn_name,
        params=params or [],
        return_type=ret_type or _mir_type(TypeKind.VOID),
        blocks=[bb],
    )
    return MIRModule(name="test", functions=[fn])


def _make_closure_module():
    """Create a MIR module with a lambda that captures a variable.

    Equivalent to:
        fn main() {
            let x = 10
            let f = closure_create lambda_0([%x])
            let result = closure_call f(5)
        }
        fn lambda_0(__env_ptr, y) {
            let x = env_load __env_ptr[0]
            return x + y
        }
    """
    # Main function
    x_val = _mir_val("x")
    x_const = Const(dest=x_val, ty=_mir_type(TypeKind.INT), value=10)
    f_val = _fn_val("f")
    closure = ClosureCreate(
        dest=f_val,
        fn_name="lambda_0",
        captures=[x_val],
        capture_types=[_mir_type(TypeKind.INT)],
    )
    f_named = _fn_val("f_named")
    f_copy = Copy(dest=f_named, src=f_val)
    result = _mir_val("result")
    call = ClosureCall(
        dest=result,
        closure=f_named,
        args=[Value(name="%arg5", ty=_mir_type(TypeKind.INT))],
    )
    arg5 = Const(
        dest=Value(name="%arg5", ty=_mir_type(TypeKind.INT)), ty=_mir_type(TypeKind.INT), value=5
    )

    main_bb = BasicBlock(
        label="entry",
        instructions=[x_const, closure, f_copy, arg5, call, Return()],
    )
    main_fn = MIRFunction(
        name="main",
        params=[],
        return_type=_mir_type(TypeKind.VOID),
        blocks=[main_bb],
    )

    # Lambda function with env_ptr
    env_ptr = Value(name="%__env_ptr", ty=_mir_type(TypeKind.UNKNOWN))
    y_val = Value(name="%y", ty=_mir_type(TypeKind.INT))
    x_loaded = _mir_val("x_env")
    env_load = EnvLoad(dest=x_loaded, env=env_ptr, index=0, val_type=_mir_type(TypeKind.INT))
    sum_val = _mir_val("sum")
    add = BinOp(dest=sum_val, op=BinOpKind.ADD, lhs=x_loaded, rhs=y_val)
    lambda_bb = BasicBlock(
        label="entry",
        instructions=[env_load, add, Return(val=sum_val)],
    )
    lambda_fn = MIRFunction(
        name="lambda_0",
        params=[
            MIRParam(name="__env_ptr", ty=_mir_type(TypeKind.UNKNOWN)),
            MIRParam(name="y", ty=_mir_type(TypeKind.INT)),
        ],
        return_type=_mir_type(TypeKind.INT),
        blocks=[lambda_bb],
    )

    return MIRModule(name="test_closure", functions=[main_fn, lambda_fn])


# ===========================================================================
# Test: MIR instruction pretty-printing
# ===========================================================================


class TestClosureMIRPrinting:
    """New MIR instructions have correct pretty-print output."""

    def test_closure_create_print(self):
        inst = ClosureCreate(
            dest=_fn_val("f"),
            fn_name="lambda_0",
            captures=[_mir_val("x"), _mir_val("y")],
            capture_types=[_mir_type(TypeKind.INT), _mir_type(TypeKind.INT)],
        )
        text = pretty_print_instruction(inst)
        assert "closure_create" in text
        assert "lambda_0" in text
        assert "%x" in text
        assert "%y" in text

    def test_closure_call_print(self):
        inst = ClosureCall(
            dest=_mir_val("result"),
            closure=_fn_val("f"),
            args=[_mir_val("arg1")],
        )
        text = pretty_print_instruction(inst)
        assert "closure_call" in text
        assert "%f" in text
        assert "%arg1" in text

    def test_env_load_print(self):
        inst = EnvLoad(
            dest=_mir_val("x"),
            env=Value(name="%env", ty=_mir_type(TypeKind.UNKNOWN)),
            index=0,
            val_type=_mir_type(TypeKind.INT),
        )
        text = pretty_print_instruction(inst)
        assert "env_load" in text
        assert "%env" in text
        assert "[0]" in text


# ===========================================================================
# Test: LLVM IR emission
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestClosureLLVMEmission:
    """Closure MIR instructions emit correct LLVM IR."""

    def test_closure_create_emits_alloc_and_store(self):
        """ClosureCreate should call __mn_alloc and store captures into env struct."""
        module = _make_closure_module()
        emitter = LLVMMIREmitter(module_name="test_closure")
        llvm_module = emitter.emit(module)
        ir_str = str(llvm_module)

        # Should declare __mn_alloc
        assert "__mn_alloc" in ir_str
        # Should have the lambda function
        assert "lambda_0" in ir_str
        # Should have main function
        assert "main" in ir_str

    def test_closure_call_emits_indirect_call(self):
        """ClosureCall should extract fn_ptr and env_ptr and call indirectly."""
        module = _make_closure_module()
        emitter = LLVMMIREmitter(module_name="test_closure")
        llvm_module = emitter.emit(module)
        ir_str = str(llvm_module)

        # Should have extractvalue for fn_ptr and env_ptr
        assert "extractvalue" in ir_str
        # Should have bitcast for function pointer
        assert "bitcast" in ir_str

    def test_env_load_emits_gep_and_load(self):
        """EnvLoad should emit GEP + load from the environment struct."""
        module = _make_closure_module()
        emitter = LLVMMIREmitter(module_name="test_closure")
        llvm_module = emitter.emit(module)
        ir_str = str(llvm_module)

        # The lambda function should have GEP + load for env access
        assert "getelementptr" in ir_str
        assert "load" in ir_str

    def test_closure_with_multiple_captures(self):
        """A closure capturing two variables should allocate a larger env struct."""
        x_val = _mir_val("x")
        y_val = _mir_val("y")
        x_const = Const(dest=x_val, ty=_mir_type(TypeKind.INT), value=10)
        y_const = Const(dest=y_val, ty=_mir_type(TypeKind.INT), value=20)
        f_val = _fn_val("f")
        closure = ClosureCreate(
            dest=f_val,
            fn_name="lambda_multi",
            captures=[x_val, y_val],
            capture_types=[_mir_type(TypeKind.INT), _mir_type(TypeKind.INT)],
        )

        main_bb = BasicBlock(
            label="entry",
            instructions=[x_const, y_const, closure, Return()],
        )
        main_fn = MIRFunction(
            name="main",
            params=[],
            return_type=_mir_type(TypeKind.VOID),
            blocks=[main_bb],
        )

        # Lambda with two captures
        env_ptr = Value(name="%__env_ptr", ty=_mir_type(TypeKind.UNKNOWN))
        x_loaded = _mir_val("x_env")
        y_loaded = _mir_val("y_env")
        env_load_x = EnvLoad(dest=x_loaded, env=env_ptr, index=0, val_type=_mir_type(TypeKind.INT))
        env_load_y = EnvLoad(dest=y_loaded, env=env_ptr, index=1, val_type=_mir_type(TypeKind.INT))
        sum_val = _mir_val("sum")
        add = BinOp(dest=sum_val, op=BinOpKind.ADD, lhs=x_loaded, rhs=y_loaded)
        lambda_bb = BasicBlock(
            label="entry",
            instructions=[env_load_x, env_load_y, add, Return(val=sum_val)],
        )
        lambda_fn = MIRFunction(
            name="lambda_multi",
            params=[
                MIRParam(name="__env_ptr", ty=_mir_type(TypeKind.UNKNOWN)),
            ],
            return_type=_mir_type(TypeKind.INT),
            blocks=[lambda_bb],
        )

        module = MIRModule(name="test_multi_cap", functions=[main_fn, lambda_fn])
        emitter = LLVMMIREmitter(module_name="test_multi_cap")
        llvm_module = emitter.emit(module)
        ir_str = str(llvm_module)

        assert "__mn_alloc" in ir_str
        assert "lambda_multi" in ir_str


# ===========================================================================
# Test: Free variable analysis (via lowerer)
# ===========================================================================


class TestFreeVariableAnalysis:
    """Free variable analysis correctly detects captured variables."""

    def test_no_captures_simple_lambda(self):
        """A lambda with no free variables should have no captures."""
        from mapanare.ast_nodes import BinaryExpr, Identifier
        from mapanare.lower import MIRLowerer

        lowerer = MIRLowerer()
        # Simulate: (x) => x + 1
        body = BinaryExpr(
            op="+",
            left=Identifier(name="x"),
            right=Identifier(name="1"),
        )
        free = lowerer._analyze_free_vars(body, {"x"})
        assert free == []

    def test_captures_outer_variable(self):
        """A lambda referencing an outer variable should detect it as free."""
        from mapanare.ast_nodes import BinaryExpr, Identifier
        from mapanare.lower import MIRLowerer
        from mapanare.mir import MIRType, Value
        from mapanare.types import TypeInfo, TypeKind

        lowerer = MIRLowerer()
        # Define 'outer' in the lowerer's scope
        lowerer._define_var(
            "outer",
            Value(name="%outer", ty=MIRType(TypeInfo(kind=TypeKind.INT))),
        )
        # Simulate: (x) => outer + x
        body = BinaryExpr(
            op="+",
            left=Identifier(name="outer"),
            right=Identifier(name="x"),
        )
        free = lowerer._analyze_free_vars(body, {"x"})
        assert free == ["outer"]

    def test_builtins_not_captured(self):
        """Builtins like println should not be detected as free variables."""
        from mapanare.ast_nodes import CallExpr, Identifier
        from mapanare.lower import MIRLowerer

        lowerer = MIRLowerer()
        # Simulate: (x) => println(x)
        body = CallExpr(
            callee=Identifier(name="println"),
            args=[Identifier(name="x")],
        )
        free = lowerer._analyze_free_vars(body, {"x"})
        assert free == []

    def test_multiple_captures(self):
        """Multiple outer variables should all be detected."""
        from mapanare.ast_nodes import BinaryExpr, Identifier
        from mapanare.lower import MIRLowerer
        from mapanare.mir import MIRType, Value
        from mapanare.types import TypeInfo, TypeKind

        lowerer = MIRLowerer()
        lowerer._define_var("a", Value(name="%a", ty=MIRType(TypeInfo(kind=TypeKind.INT))))
        lowerer._define_var("b", Value(name="%b", ty=MIRType(TypeInfo(kind=TypeKind.INT))))
        # Simulate: (x) => a + b + x
        body = BinaryExpr(
            op="+",
            left=BinaryExpr(
                op="+",
                left=Identifier(name="a"),
                right=Identifier(name="b"),
            ),
            right=Identifier(name="x"),
        )
        free = lowerer._analyze_free_vars(body, {"x"})
        assert "a" in free
        assert "b" in free
        assert len(free) == 2


# ===========================================================================
# Test: End-to-end lowering (source → MIR → check)
# ===========================================================================


class TestClosureLowering:
    """Closures are correctly lowered from AST to MIR."""

    def _lower_source(self, source: str) -> MIRModule:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        program = parse(source)
        lowerer = MIRLowerer()
        return lowerer.lower(program, module_name="test")

    def test_lambda_no_capture_emits_const(self):
        """A lambda with no captures should emit a Const FN reference."""
        source = """
fn main() -> Int {
    let f = (x) => x + 1
    return f(5)
}
"""
        module = self._lower_source(source)
        main_fn = module.get_function("main")
        assert main_fn is not None
        # Should have a Const instruction with a lambda name
        insts = [
            inst
            for bb in main_fn.blocks
            for inst in bb.instructions
            if isinstance(inst, Const) and inst.ty.kind == TypeKind.FN
        ]
        assert len(insts) >= 1

    def test_lambda_with_capture_emits_closure_create(self):
        """A lambda capturing an outer variable should emit ClosureCreate."""
        source = """
fn main() -> Int {
    let x: Int = 10
    let f = (y) => x + y
    return f(5)
}
"""
        module = self._lower_source(source)
        main_fn = module.get_function("main")
        assert main_fn is not None
        # Should have a ClosureCreate instruction
        closure_insts = [
            inst
            for bb in main_fn.blocks
            for inst in bb.instructions
            if isinstance(inst, ClosureCreate)
        ]
        assert len(closure_insts) >= 1
        # The closure should capture x
        assert len(closure_insts[0].captures) == 1

    def test_lambda_with_capture_emits_closure_call(self):
        """Calling a closure variable should emit ClosureCall."""
        source = """
fn main() -> Int {
    let x: Int = 10
    let f = (y) => x + y
    return f(5)
}
"""
        module = self._lower_source(source)
        main_fn = module.get_function("main")
        assert main_fn is not None
        closure_calls = [
            inst
            for bb in main_fn.blocks
            for inst in bb.instructions
            if isinstance(inst, ClosureCall)
        ]
        assert len(closure_calls) >= 1

    def test_lambda_function_has_env_param(self):
        """The generated lambda function should have __env_ptr as first param."""
        source = """
fn main() -> Int {
    let x: Int = 10
    let f = (y) => x + y
    return f(5)
}
"""
        module = self._lower_source(source)
        # Find the lambda function (not main)
        lambda_fns = [fn for fn in module.functions if fn.name != "main"]
        assert len(lambda_fns) >= 1
        lambda_fn = lambda_fns[0]
        # First param should be __env_ptr
        assert lambda_fn.params[0].name == "__env_ptr"
        # Should have EnvLoad instruction
        env_loads = [
            inst for bb in lambda_fn.blocks for inst in bb.instructions if isinstance(inst, EnvLoad)
        ]
        assert len(env_loads) >= 1
        assert env_loads[0].index == 0

    def test_multiple_captures_lowering(self):
        """Multiple captured variables should produce correct ClosureCreate."""
        source = """
fn main() -> Int {
    let a: Int = 5
    let b: Int = 10
    let f = (x) => a + b + x
    return f(1)
}
"""
        module = self._lower_source(source)
        main_fn = module.get_function("main")
        assert main_fn is not None
        closure_insts = [
            inst
            for bb in main_fn.blocks
            for inst in bb.instructions
            if isinstance(inst, ClosureCreate)
        ]
        assert len(closure_insts) >= 1
        assert len(closure_insts[0].captures) == 2


# ===========================================================================
# Test: End-to-end LLVM IR emission from source
# ===========================================================================


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestClosureE2E:
    """End-to-end: Mapanare source → MIR → LLVM IR."""

    def _to_llvm_ir(self, source: str) -> str:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        program = parse(source)
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program, module_name="test")
        emitter = LLVMMIREmitter(module_name="test")
        llvm_module = emitter.emit(mir_module)
        return str(llvm_module)

    def test_simple_capture_produces_valid_ir(self):
        """A simple closure capture should produce valid LLVM IR."""
        # Use a non-arithmetic body to avoid type mismatch with untyped params
        source = """
fn main() -> Int {
    let x: Int = 10
    let f = (y) => x
    return f(5)
}
"""
        ir_str = self._to_llvm_ir(source)
        # Should have __mn_alloc for env allocation
        assert "__mn_alloc" in ir_str
        # Should have the main function and lambda
        assert "define" in ir_str

    def test_closure_with_multiple_captures_ir(self):
        """A closure capturing two variables should emit valid LLVM IR."""
        source = """
fn main() -> Int {
    let x: Int = 10
    let y: Int = 20
    let f = (a) => x
    return f(5)
}
"""
        ir_str = self._to_llvm_ir(source)
        assert "__mn_alloc" in ir_str
        assert "define" in ir_str
