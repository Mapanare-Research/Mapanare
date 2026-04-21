"""v4.149.0 E5 / ABI.1: per-target return convention tests.

Tests that the emitter uses register-return vs sret correctly for each
target triple, matching System V AMD64 §3.2.3, Win64, and AArch64 AAPCS64.
"""

from __future__ import annotations

import re

from mapanare.abi import ReturnABI, classify_return

# ── Unit tests for the classifier ─────────────────────────────────────


class TestSysVClassification:
    """System V AMD64: ≤ 16 bytes → register, > 16 bytes → sret."""

    TRIPLE = "x86_64-pc-linux-gnu"

    def test_single_i64_in_register(self) -> None:
        assert classify_return("{i64}", 8, self.TRIPLE) == ReturnABI("register")

    def test_two_i64_in_registers(self) -> None:
        assert classify_return("{i64, i64}", 16, self.TRIPLE) == ReturnABI("register")

    def test_i1_i64_in_registers(self) -> None:
        assert classify_return("{i1, i64}", 16, self.TRIPLE) == ReturnABI("register")

    def test_three_i64_uses_sret(self) -> None:
        assert classify_return("{i64, i64, i64}", 24, self.TRIPLE) == ReturnABI("sret")

    def test_ptr_i64_in_registers(self) -> None:
        assert classify_return("{ptr, i64}", 16, self.TRIPLE) == ReturnABI("register")

    def test_result_type_uses_sret(self) -> None:
        assert classify_return("{i1, {i64, {ptr, i64}}}", 32, self.TRIPLE) == ReturnABI("sret")

    def test_four_i64_uses_sret(self) -> None:
        assert classify_return("{i64, i64, i64, i64}", 32, self.TRIPLE) == ReturnABI("sret")

    def test_empty_struct_in_register(self) -> None:
        assert classify_return("{}", 0, self.TRIPLE) == ReturnABI("register")

    def test_scalar_i64_in_register(self) -> None:
        assert classify_return("i64", 8, self.TRIPLE) == ReturnABI("register")


class TestWin64Classification:
    """Win64 x64: exactly 1/2/4/8 bytes → register, everything else → sret."""

    TRIPLE = "x86_64-pc-windows-msvc"

    def test_single_i64_in_register(self) -> None:
        assert classify_return("{i64}", 8, self.TRIPLE) == ReturnABI("register")

    def test_two_i64_uses_sret(self) -> None:
        assert classify_return("{i64, i64}", 16, self.TRIPLE) == ReturnABI("sret")

    def test_ptr_i64_uses_sret(self) -> None:
        assert classify_return("{ptr, i64}", 16, self.TRIPLE) == ReturnABI("sret")

    def test_three_i64_uses_sret(self) -> None:
        assert classify_return("{i64, i64, i64}", 24, self.TRIPLE) == ReturnABI("sret")

    def test_i1_uses_register(self) -> None:
        assert classify_return("{i1}", 1, self.TRIPLE) == ReturnABI("register")

    def test_i32_uses_register(self) -> None:
        assert classify_return("{i32}", 4, self.TRIPLE) == ReturnABI("register")


class TestAArch64Classification:
    """AArch64 AAPCS64: ≤ 16 bytes → register, > 16 bytes → sret."""

    TRIPLE = "aarch64-unknown-linux-gnu"

    def test_two_i64_in_registers(self) -> None:
        assert classify_return("{i64, i64}", 16, self.TRIPLE) == ReturnABI("register")

    def test_three_i64_uses_sret(self) -> None:
        assert classify_return("{i64, i64, i64}", 24, self.TRIPLE) == ReturnABI("sret")

    def test_option_int_in_registers(self) -> None:
        assert classify_return("{i1, i64}", 16, self.TRIPLE) == ReturnABI("register")


# ── Integration tests: emitted IR matches classifier ──────────────────


def _emit_ir(source: str, target: str = "x86_64-linux-gnu") -> str:
    """Compile Mapanare source to LLVM IR text on the given target."""
    from mapanare.cli import _compile_to_llvm_ir

    return _compile_to_llvm_ir(source, "test.mn", target_name=target)


class TestEmitterConsistency:
    """Header and call site must both use the same ABI decision."""

    SHAPE_SOURCE = """\
enum Shape {
    Circle(Int),
    Square(Int),
    Triangle(Int, Int),
}

fn make_shape(i: Int) -> Shape {
    if i == 0 { return Shape::Circle(i) }
    if i == 1 { return Shape::Square(i) }
    return Shape::Triangle(i, i)
}

fn use_shape(s: Shape) -> Int {
    match s {
        Circle(r) => { return r },
        Square(side) => { return side },
        Triangle(a, b) => { return a + b }
    }
}

fn main() {
    let s: Shape = make_shape(1)
    print(str(use_shape(s)))
}
"""

    def test_sysv_24byte_enum_uses_sret(self) -> None:
        ir = _emit_ir(self.SHAPE_SOURCE, "x86_64-linux-gnu")
        assert "sret({i64, i64, i64})" in ir
        m = re.search(r"define\s+\w*\s*void\s+@make_shape\(", ir)
        assert m is not None, "make_shape should return void with sret on SysV"

    def test_sysv_call_site_uses_sret(self) -> None:
        ir = _emit_ir(self.SHAPE_SOURCE, "x86_64-linux-gnu")
        assert re.search(r"call void @make_shape\(ptr sret", ir) is not None

    def test_win64_24byte_enum_uses_sret(self) -> None:
        ir = _emit_ir(self.SHAPE_SOURCE, "x86_64-windows-msvc")
        assert "sret({i64, i64, i64})" in ir

    def test_aarch64_24byte_enum_uses_sret(self) -> None:
        ir = _emit_ir(self.SHAPE_SOURCE, "aarch64-apple-macos")
        assert "sret({i64, i64, i64})" in ir

    OPTION_SOURCE = """\
fn maybe(x: Int) -> Option<Int> {
    if x > 0 { return Some(x) }
    return none
}

fn main() {
    let r: Option<Int> = maybe(5)
    match r {
        Some(v) => { print(str(v)) },
        _ => { print("none") }
    }
}
"""

    def test_sysv_option_int_stays_register(self) -> None:
        ir = _emit_ir(self.OPTION_SOURCE, "x86_64-linux-gnu")
        m = re.search(r"define\s+\w*\s*\{i1, i64\}\s+@maybe\(", ir)
        assert m is not None, "maybe() should return {i1, i64} by value on SysV"

    def test_win64_option_int_uses_sret(self) -> None:
        ir = _emit_ir(self.OPTION_SOURCE, "x86_64-windows-msvc")
        assert "sret({i1, i64})" in ir

    def test_header_and_call_agree(self) -> None:
        """The critical invariant: definition and call site must use the same convention."""
        ir = _emit_ir(self.SHAPE_SOURCE, "x86_64-linux-gnu")
        # If make_shape uses sret in definition, call site must too
        has_sret_def = "define internal void @make_shape(ptr" in ir
        has_sret_call = "call void @make_shape(ptr sret" in ir
        assert (
            has_sret_def == has_sret_call
        ), "Definition and call site must agree on sret convention"
