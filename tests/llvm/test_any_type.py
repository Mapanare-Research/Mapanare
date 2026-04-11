"""Tests for TypeKind.ANY — emitter mapping, box/unbox, and error rejection."""

from __future__ import annotations

from mapanare.emit_llvm_text import MN_VALUE
from mapanare.mir import MIRType, mir_any
from mapanare.parser import parse
from mapanare.semantic import check
from mapanare.types import TypeInfo, TypeKind


class TestAnyTypeConstants:
    """MN_VALUE constant is 24-byte boxed any: {i32, i32, {ptr, i64}}."""

    def test_mn_value_constant(self) -> None:
        assert MN_VALUE == "{i32, i32, {ptr, i64}}"

    def test_mir_any_factory(self) -> None:
        t = mir_any()
        assert t.kind == TypeKind.ANY


class TestAnyEmitterMapping:
    """TypeKind.ANY resolves to MN_VALUE in the text emitter."""

    def test_text_emitter_rty(self) -> None:
        from mapanare.emit_llvm_text import LLVMTextEmitter

        e = LLVMTextEmitter.__new__(LLVMTextEmitter)
        # _rty needs minimal state — just check it doesn't crash
        mt = MIRType(type_info=TypeInfo(kind=TypeKind.ANY))
        result = e._rty(mt)
        assert result == MN_VALUE


class TestAnyArithmeticRejection:
    """Arithmetic on any + any produces a compile error.

    v4.29.0 test honesty fix: these tests used to wrap the ``let``
    bindings at module scope, but module-level ``let`` expressions do
    not flow through ``_check_binary`` in the semantic checker, so the
    rejection fired exactly zero times and the assertions were
    vacuously (but silently) wrong. The pre-existing failure was
    surfaced by the v4.29.0 verification pass and fixed inline here
    by wrapping the bindings in ``fn main() { ... }`` so the binary
    expression is actually checked. The ``module-level any inference``
    gap is a separate issue tracked for v4.30.0.
    """

    def test_any_plus_any_error(self) -> None:
        source = """
fn main() {
    let x: any = 42
    let y: any = 10
    let z = x + y
}
"""
        program = parse(source, filename="test.mn")
        errors = check(program, filename="test.mn")
        msgs = [e.message for e in errors]
        assert any(
            "Arithmetic on 'any'" in m for m in msgs
        ), f"Expected any arithmetic error, got: {msgs}"

    def test_any_comparison_ok(self) -> None:
        source = """
fn main() {
    let x: any = 42
    let y: any = 10
    let z = x == y
}
"""
        program = parse(source, filename="test.mn")
        errors = check(program, filename="test.mn")
        # Comparisons on any should be allowed
        arithmetic_errors = [e for e in errors if "Arithmetic on 'any'" in e.message]
        assert arithmetic_errors == [], f"Unexpected arithmetic rejection: {arithmetic_errors}"


class TestAnyBoxLowering:
    """Box/unbox calls are emitted for any-typed let bindings."""

    def test_box_fn_mapping(self) -> None:
        from mapanare.lower import MIRLowerer

        box_fns = MIRLowerer._ANY_BOX_FN
        assert TypeKind.INT in box_fns
        assert TypeKind.FLOAT in box_fns
        assert TypeKind.BOOL in box_fns
        assert TypeKind.STRING in box_fns
        assert box_fns[TypeKind.INT] == "__mn_any_box_int"
