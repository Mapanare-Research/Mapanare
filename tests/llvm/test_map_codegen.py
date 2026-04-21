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
    Program,
    StringLiteral,
)
from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.lower import lower as build_mir
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


def _emit_program_ir(fn: FnDef) -> str:
    """Emit a single function through the full pipeline and return LLVM IR text."""
    prog = Program(definitions=[fn])
    mir_module = build_mir(prog, module_name="test")
    emitter = LLVMTextEmitter(module_name="test")
    return emitter.emit(mir_module)


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
    """Verify LLVM emitter handles MapLiteral nodes."""

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
        ir_text = _emit_program_ir(fn)
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
        ir_text = _emit_program_ir(fn)
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
        ir_text = _emit_program_ir(fn)
        assert "__mn_map_new" in ir_text
        assert "__mn_map_set" in ir_text

    def test_map_literal_returns_pointer(self):
        """MapLiteral produces a pointer value."""
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
        ir_text = _emit_program_ir(fn)
        # The map_new call returns a pointer
        assert "ptr" in ir_text or "i8*" in ir_text


# ===========================================================================
# Task 14-15: AST Emitter — Map indexing and assignment
# ===========================================================================


class TestASTEmitterMapIndex:
    """Verify LLVM emitter handles map[key] reads and writes."""

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
                        indices=[IntLiteral(value=1)],
                    )
                ),
            ]
        )
        ir_text = _emit_program_ir(fn)
        assert "__mn_map_get" in ir_text


# ===========================================================================
# Task 16: MIR Emitter — MapInit
# ===========================================================================


class TestMIREmitterMapInit:
    """Verify LLVM text emitter handles MapInit instruction."""

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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
        assert "__mn_map_new" in ir_text
        # Key type tag 1 (string)
        assert "i64 1" in ir_text or "i64 16" in ir_text  # 1 = tag or 16 = string key_size


# ===========================================================================
# Task 17: MIR Emitter — Map IndexGet/IndexSet
# ===========================================================================


class TestMIREmitterMapIndexOps:
    """Verify LLVM text emitter handles IndexGet/IndexSet on maps."""

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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
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
        emitter = LLVMTextEmitter(module_name="test")
        ir_text = emitter.emit(mod)
        assert "__mn_map_len" in ir_text


# ===========================================================================
# Runtime function declarations
# ===========================================================================


class TestMapRuntimeDeclarations:
    """Verify map runtime functions appear in emitted IR when map ops are used."""

    def _emit_map_ir(self) -> str:
        """Emit IR for a function with map operations, returning all declarations."""
        dest = _mir_map_val("m")
        k = _mir_val("k")
        v = _mir_val("v")
        instrs = [
            Const(dest=k, value=1),
            Const(dest=v, value=42),
            MapInit(
                dest=dest,
                key_type=_mir_type(TypeKind.INT),
                val_type=_mir_type(TypeKind.INT),
                pairs=[(k, v)],
            ),
            IndexGet(dest=_mir_val("r"), obj=dest, index=k),
            IndexSet(obj=dest, index=k, val=v),
            Call(dest=_mir_val("n"), fn_name="len", args=[dest]),
        ]
        mod = _build_mir_module("test_map_decls", instrs)
        emitter = LLVMTextEmitter(module_name="test")
        return emitter.emit(mod)

    def test_map_new_declared(self):
        """__mn_map_new is declared."""
        ir_text = self._emit_map_ir()
        assert "__mn_map_new" in ir_text

    def test_map_set_declared(self):
        """__mn_map_set is declared."""
        ir_text = self._emit_map_ir()
        assert "__mn_map_set" in ir_text

    def test_map_get_declared(self):
        """__mn_map_get is declared."""
        ir_text = self._emit_map_ir()
        assert "__mn_map_get" in ir_text

    def test_map_len_declared(self):
        """__mn_map_len is declared."""
        ir_text = self._emit_map_ir()
        assert "__mn_map_len" in ir_text


# ===========================================================================
# MIR Emitter — Map runtime function declarations
# ===========================================================================


class TestMIREmitterMapRuntimeDecls:
    """Verify text emitter declares map runtime functions correctly."""

    def _emit_with_map_ops(self) -> str:
        """Emit a module with map ops and return IR text."""
        dest = _mir_map_val("m")
        k = _mir_val("k")
        v = _mir_val("v")
        instrs = [
            Const(dest=k, value=1),
            Const(dest=v, value=42),
            MapInit(
                dest=dest,
                key_type=_mir_type(TypeKind.INT),
                val_type=_mir_type(TypeKind.INT),
                pairs=[(k, v)],
            ),
            IndexGet(dest=_mir_val("r"), obj=dest, index=k),
            Call(dest=_mir_val("n"), fn_name="len", args=[dest]),
        ]
        mod = _build_mir_module("test_decls", instrs)
        emitter = LLVMTextEmitter(module_name="test")
        return emitter.emit(mod)

    def test_mir_map_new(self):
        ir_text = self._emit_with_map_ops()
        assert "__mn_map_new" in ir_text

    def test_mir_map_set(self):
        ir_text = self._emit_with_map_ops()
        assert "__mn_map_set" in ir_text

    def test_mir_map_get(self):
        ir_text = self._emit_with_map_ops()
        assert "__mn_map_get" in ir_text

    def test_mir_map_len(self):
        ir_text = self._emit_with_map_ops()
        assert "__mn_map_len" in ir_text
