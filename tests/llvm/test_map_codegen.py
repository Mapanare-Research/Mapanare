"""Tests for Phase 1 — LLVM Map/Dict Codegen.

Tests verify:
  - C runtime map functions are declared correctly in LLVM IR
  - MapInit emits __mn_map_new + __mn_map_set calls
  - IndexGet on maps emits __mn_map_get
  - IndexSet on maps emits __mn_map_set
  - len() on maps emits __mn_map_len
  - AST emitter: MapLiteral, map indexing, map assignment
"""

from __future__ import annotations

from llvmlite import ir

from mapanare.ast_nodes import (
    Block,
    ExprStmt,
    FnDef,
    Identifier,
    IndexExpr,
    IntLiteral,
    LetBinding,
    MapEntry,
    MapLiteral,
    NamedType,
    Param,
    StringLiteral,
)
from mapanare.emit_llvm import LLVMEmitter
from mapanare.emit_llvm_mir import LLVMMIREmitter
from mapanare.mir import (
    BasicBlock,
    Call,
    Const,
    IndexGet,
    IndexSet,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Return,
    Value,
)
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fn(
    name: str = "test_fn",
    params: list[Param] | None = None,
    ret: NamedType | None = None,
    body: list[object] | None = None,
) -> FnDef:
    return FnDef(
        name=name,
        params=params or [],
        return_type=ret,
        body=Block(stmts=body or []),
    )


def _emit_single_fn(fn: FnDef) -> tuple[LLVMEmitter, ir.Function]:
    emitter = LLVMEmitter()
    func = emitter.emit_fn(fn)
    return emitter, func


def _ir_str(emitter: LLVMEmitter) -> str:
    return str(emitter.module)


def _mir_type(kind: TypeKind, name: str = "") -> MIRType:
    return MIRType(type_info=TypeInfo(kind=kind, name=name))


def _mir_val(name: str, kind: TypeKind = TypeKind.INT) -> Value:
    return Value(name=name, ty=_mir_type(kind))


def _mir_map_val(name: str) -> Value:
    return Value(name=name, ty=_mir_type(TypeKind.MAP))


def _build_mir_module(fn_name: str, instructions: list, ret_val: Value | None = None) -> MIRModule:
    """Build a minimal MIR module with one function and one basic block."""
    instrs = list(instructions)
    if ret_val:
        instrs.append(Return(val=ret_val))
    else:
        instrs.append(Return(val=None))

    bb = BasicBlock(label="entry", instructions=instrs)
    fn = MIRFunction(
        name=fn_name,
        params=[],
        return_type=_mir_type(TypeKind.VOID) if not ret_val else ret_val.ty,
        blocks=[bb],
    )
    return MIRModule(name="test", functions=[fn])


# ===========================================================================
# Task 12-13: AST Emitter — MapLiteral
# ===========================================================================


class TestASTEmitterMapLiteral:
    """Verify emit_llvm.py handles MapLiteral nodes."""

    def test_empty_map_literal(self):
        """Empty map #{} emits __mn_map_new call."""
        fn = _make_fn(
            body=[
                LetBinding(
                    name="m",
                    mutable=False,
                    value=MapLiteral(entries=[]),
                ),
            ]
        )
        emitter, func = _emit_single_fn(fn)
        ir_text = _ir_str(emitter)
        assert "__mn_map_new" in ir_text

    def test_int_int_map_literal(self):
        """Map #{1: 10, 2: 20} emits __mn_map_new + 2x __mn_map_set."""
        fn = _make_fn(
            body=[
                LetBinding(
                    name="m",
                    mutable=False,
                    value=MapLiteral(
                        entries=[
                            MapEntry(key=IntLiteral(value=1), value=IntLiteral(value=10)),
                            MapEntry(key=IntLiteral(value=2), value=IntLiteral(value=20)),
                        ]
                    ),
                ),
            ]
        )
        emitter, func = _emit_single_fn(fn)
        ir_text = _ir_str(emitter)
        assert "__mn_map_new" in ir_text
        assert "__mn_map_set" in ir_text

    def test_string_int_map_literal(self):
        """Map #{"a": 1, "b": 2} emits map with string key type tag."""
        fn = _make_fn(
            body=[
                LetBinding(
                    name="m",
                    mutable=False,
                    value=MapLiteral(
                        entries=[
                            MapEntry(key=StringLiteral(value="a"), value=IntLiteral(value=1)),
                            MapEntry(key=StringLiteral(value="b"), value=IntLiteral(value=2)),
                        ]
                    ),
                ),
            ]
        )
        emitter, func = _emit_single_fn(fn)
        ir_text = _ir_str(emitter)
        assert "__mn_map_new" in ir_text
        assert "__mn_map_set" in ir_text

    def test_map_literal_returns_pointer(self):
        """MapLiteral produces an i8* (opaque pointer) value."""
        fn = _make_fn(
            body=[
                LetBinding(
                    name="m",
                    mutable=False,
                    value=MapLiteral(
                        entries=[
                            MapEntry(key=IntLiteral(value=1), value=IntLiteral(value=10)),
                        ]
                    ),
                ),
            ]
        )
        emitter, func = _emit_single_fn(fn)
        ir_text = _ir_str(emitter)
        # The map_new call returns i8*
        assert "i8*" in ir_text


# ===========================================================================
# Task 14-15: AST Emitter — Map indexing and assignment
# ===========================================================================


class TestASTEmitterMapIndex:
    """Verify emit_llvm.py handles map[key] reads and writes."""

    def test_map_index_emits_map_get(self):
        """map[key] calls __mn_map_get."""
        fn = _make_fn(
            body=[
                LetBinding(
                    name="m",
                    mutable=False,
                    value=MapLiteral(
                        entries=[
                            MapEntry(key=IntLiteral(value=1), value=IntLiteral(value=42)),
                        ]
                    ),
                ),
                ExprStmt(
                    expr=IndexExpr(
                        object=Identifier(name="m"),
                        index=IntLiteral(value=1),
                    )
                ),
            ]
        )
        emitter, func = _emit_single_fn(fn)
        ir_text = _ir_str(emitter)
        assert "__mn_map_get" in ir_text


# ===========================================================================
# Task 16: MIR Emitter — MapInit
# ===========================================================================


class TestMIREmitterMapInit:
    """Verify emit_llvm_mir.py handles MapInit instruction."""

    def test_empty_map_init(self):
        """MapInit with no pairs → __mn_map_new only."""
        dest = _mir_map_val("m")
        inst = MapInit(
            dest=dest,
            key_type=_mir_type(TypeKind.INT),
            val_type=_mir_type(TypeKind.INT),
            pairs=[],
        )
        mod = _build_mir_module("test_empty_map", [inst])
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_new" in ir_text

    def test_map_init_with_pairs(self):
        """MapInit with pairs → __mn_map_new + __mn_map_set calls."""
        k1 = _mir_val("k1")
        v1 = _mir_val("v1")
        k2 = _mir_val("k2")
        v2 = _mir_val("v2")
        dest = _mir_map_val("m")

        instrs = [
            Const(dest=k1, value=1),
            Const(dest=v1, value=10),
            Const(dest=k2, value=2),
            Const(dest=v2, value=20),
            MapInit(
                dest=dest,
                key_type=_mir_type(TypeKind.INT),
                val_type=_mir_type(TypeKind.INT),
                pairs=[(k1, v1), (k2, v2)],
            ),
        ]
        mod = _build_mir_module("test_map_pairs", instrs)
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_new" in ir_text
        assert "__mn_map_set" in ir_text

    def test_string_key_map_init(self):
        """MapInit with String key type → key_type tag = 1."""
        k = _mir_val("k", TypeKind.STRING)
        v = _mir_val("v", TypeKind.INT)
        dest = _mir_map_val("m")

        instrs = [
            Const(dest=k, value="hello"),
            Const(dest=v, value=42),
            MapInit(
                dest=dest,
                key_type=_mir_type(TypeKind.STRING),
                val_type=_mir_type(TypeKind.INT),
                pairs=[(k, v)],
            ),
        ]
        mod = _build_mir_module("test_str_map", instrs)
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_new" in ir_text
        # Key type tag 1 (string)
        assert "i64 1" in ir_text or "i64 16" in ir_text  # 1 = tag or 16 = string key_size


# ===========================================================================
# Task 17: MIR Emitter — Map IndexGet/IndexSet
# ===========================================================================


class TestMIREmitterMapIndexOps:
    """Verify emit_llvm_mir.py handles IndexGet/IndexSet on maps."""

    def test_map_index_get(self):
        """IndexGet on MAP type → __mn_map_get call."""
        map_val = _mir_map_val("m")
        key_val = _mir_val("k")
        dest = _mir_val("result")

        instrs = [
            Const(dest=map_val, value=0),  # placeholder
            Const(dest=key_val, value=1),
            IndexGet(dest=dest, obj=map_val, index=key_val),
        ]
        mod = _build_mir_module("test_map_get", instrs)
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_get" in ir_text

    def test_map_index_set(self):
        """IndexSet on MAP type → __mn_map_set call."""
        map_val = _mir_map_val("m")
        key_val = _mir_val("k")
        val = _mir_val("v")

        instrs = [
            Const(dest=map_val, value=0),  # placeholder
            Const(dest=key_val, value=1),
            Const(dest=val, value=42),
            IndexSet(obj=map_val, index=key_val, val=val),
        ]
        mod = _build_mir_module("test_map_set", instrs)
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_set" in ir_text


# ===========================================================================
# Task 19: Map len() via MIR Call
# ===========================================================================


class TestMIREmitterMapLen:
    """Verify len() on maps emits __mn_map_len."""

    def test_map_len(self):
        """Call(len, [map]) → __mn_map_len."""
        map_val = _mir_map_val("m")
        result = _mir_val("n")

        instrs = [
            Const(dest=map_val, value=0),
            Call(dest=result, fn_name="len", args=[map_val]),
        ]
        mod = _build_mir_module("test_map_len", instrs, ret_val=result)
        emitter = LLVMMIREmitter()
        llvm_mod = emitter.emit(mod)
        ir_text = str(llvm_mod)
        assert "__mn_map_len" in ir_text


# ===========================================================================
# Runtime function declarations
# ===========================================================================


class TestMapRuntimeDeclarations:
    """Verify map runtime functions are declared with correct signatures."""

    def test_map_new_declared(self):
        """__mn_map_new(i64, i64, i64) -> i8*."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_new()
        assert fn.name == "__mn_map_new"
        assert len(fn.args) == 3

    def test_map_set_declared(self):
        """__mn_map_set(i8*, i8*, i8*) -> void."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_set()
        assert fn.name == "__mn_map_set"
        assert len(fn.args) == 3

    def test_map_get_declared(self):
        """__mn_map_get(i8*, i8*) -> i8*."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_get()
        assert fn.name == "__mn_map_get"
        assert len(fn.args) == 2

    def test_map_del_declared(self):
        """__mn_map_del(i8*, i8*) -> i64."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_del()
        assert fn.name == "__mn_map_del"
        assert len(fn.args) == 2

    def test_map_len_declared(self):
        """__mn_map_len(i8*) -> i64."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_len()
        assert fn.name == "__mn_map_len"
        assert len(fn.args) == 1

    def test_map_contains_declared(self):
        """__mn_map_contains(i8*, i8*) -> i64."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_contains()
        assert fn.name == "__mn_map_contains"
        assert len(fn.args) == 2

    def test_map_iter_new_declared(self):
        """__mn_map_iter_new(i8*) -> i8*."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_iter_new()
        assert fn.name == "__mn_map_iter_new"
        assert len(fn.args) == 1

    def test_map_iter_next_declared(self):
        """__mn_map_iter_next(i8*, i8**, i8**) -> i64."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_iter_next()
        assert fn.name == "__mn_map_iter_next"
        assert len(fn.args) == 3

    def test_map_free_declared(self):
        """__mn_map_free(i8*) -> void."""
        emitter = LLVMEmitter()
        fn = emitter._rt_map_free()
        assert fn.name == "__mn_map_free"
        assert len(fn.args) == 1


# ===========================================================================
# MIR Emitter — Map runtime function declarations
# ===========================================================================


class TestMIREmitterMapRuntimeDecls:
    """Verify MIR emitter declares map runtime functions correctly."""

    def test_mir_map_new(self):
        emitter = LLVMMIREmitter()
        emitter.emit(MIRModule(name="test", functions=[]))
        fn = emitter._rt_map_new()
        assert fn.name == "__mn_map_new"

    def test_mir_map_set(self):
        emitter = LLVMMIREmitter()
        emitter.emit(MIRModule(name="test", functions=[]))
        fn = emitter._rt_map_set()
        assert fn.name == "__mn_map_set"

    def test_mir_map_get(self):
        emitter = LLVMMIREmitter()
        emitter.emit(MIRModule(name="test", functions=[]))
        fn = emitter._rt_map_get()
        assert fn.name == "__mn_map_get"

    def test_mir_map_len(self):
        emitter = LLVMMIREmitter()
        emitter.emit(MIRModule(name="test", functions=[]))
        fn = emitter._rt_map_len()
        assert fn.name == "__mn_map_len"
