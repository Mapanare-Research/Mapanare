"""v5.21.0 Te.6 — chained comparison tests."""

from __future__ import annotations

from mapanare.ast_nodes import (
    BinaryExpr,
    ChainedCompare,
    LetBinding,
)
from mapanare.parser import parse


def _stmts(src: str) -> list:
    prog = parse(src)
    for d in prog.definitions:
        body = getattr(d, "body", None)
        if body is not None:
            return body.stmts
    return []


def _let_value(stmt):
    assert isinstance(stmt, LetBinding)
    return stmt.value


# ---------------------------------------------------------------------------
# AST shape: 1-cmp shapes preserve legacy BinaryExpr (D6)
# ---------------------------------------------------------------------------


class TestSingleComparisonPreserved:
    def test_lt_single_is_binary(self) -> None:
        v = _let_value(_stmts("fn main() { let r = a < b }")[0])
        assert isinstance(v, BinaryExpr)
        assert v.op == "<"

    def test_eq_single_is_binary(self) -> None:
        v = _let_value(_stmts("fn main() { let r = a == b }")[0])
        assert isinstance(v, BinaryExpr)
        assert v.op == "=="

    def test_ne_single_is_binary(self) -> None:
        v = _let_value(_stmts("fn main() { let r = a != b }")[0])
        assert isinstance(v, BinaryExpr)
        assert v.op == "!="


# ---------------------------------------------------------------------------
# AST shape: 3+ element chains build ChainedCompare
# ---------------------------------------------------------------------------


class TestChainedShape:
    def test_three_element(self) -> None:
        v = _let_value(_stmts("fn main() { let r = 0 < x < 10 }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["<", "<"]
        assert len(v.operands) == 3

    def test_four_element(self) -> None:
        v = _let_value(_stmts("fn main() { let r = a < b < c < d }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["<", "<", "<"]
        assert len(v.operands) == 4

    def test_mixed_ops(self) -> None:
        v = _let_value(_stmts("fn main() { let r = 0 <= x < 10 }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["<=", "<"]

    def test_chained_equality(self) -> None:
        v = _let_value(_stmts("fn main() { let r = a == b == c }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["==", "=="]

    def test_mixed_eq_and_cmp(self) -> None:
        # D1 — `==`/`!=` merged into the same precedence as ordering
        v = _let_value(_stmts("fn main() { let r = a == b < c }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["==", "<"]

    def test_mixed_direction(self) -> None:
        # D2 — `a < b > c` is legal
        v = _let_value(_stmts("fn main() { let r = a < b > c }")[0])
        assert isinstance(v, ChainedCompare)
        assert v.ops == ["<", ">"]


# ---------------------------------------------------------------------------
# Type checking + Bool result
# ---------------------------------------------------------------------------


class TestSemanticBool:
    def test_chain_in_if(self) -> None:
        # Chain is a Bool — usable in if condition; no type error
        from mapanare.semantic import SemanticChecker

        prog = parse('fn main() { let x = 5; if 0 < x < 10 { print("ok") } }')
        checker = SemanticChecker()
        checker.check(prog)
        assert checker.errors == []

    def test_chain_in_assert(self) -> None:
        from mapanare.semantic import SemanticChecker

        prog = parse("fn main() { let x = 5; assert 0 < x < 10 }")
        checker = SemanticChecker()
        checker.check(prog)
        assert checker.errors == []


# ---------------------------------------------------------------------------
# Lowering — verify once-evaluation by inspecting LLVM IR
# ---------------------------------------------------------------------------


class TestLoweringOnce:
    def test_non_trivial_middle_binds_to_chain_temp(self) -> None:
        from mapanare.cli import _compile_to_llvm_ir
        from mapanare.mir_opt import MIROptLevel as OptLevel

        src = """\
fn middle(c: Int) -> Int {
    return 5
}

fn check(c: Int) -> Bool {
    return 0 < middle(c) < 10
}

fn main() {
    print(str(check(0)))
}
"""
        ir = _compile_to_llvm_ir(src, "test_once.mn", opt_level=OptLevel.O0)
        # Locate the @check function and verify @middle is called exactly once
        idx = ir.find("define internal noundef i1 @check")
        if idx < 0:
            idx = ir.find("@check(")
        assert idx >= 0, "expected @check function in IR"
        end = ir.find("\n}\n", idx)
        check_region = ir[idx:end] if end > idx else ir[idx:]
        call_count = check_region.count("@middle(")
        assert call_count == 1, (
            f"expected exactly 1 call to @middle in @check (D3 once-eval), got {call_count}\n"
            f"region:\n{check_region[:1500]}"
        )
        # And the synthesized chain temp must appear
        assert "__mn_chain_" in check_region, "non-trivial middle must bind to a __mn_chain_N temp"

    def test_trivial_middle_no_chain_temp(self) -> None:
        from mapanare.cli import _compile_to_llvm_ir
        from mapanare.mir_opt import MIROptLevel as OptLevel

        src = """\
fn check(x: Int) -> Bool {
    return 0 < x < 10
}

fn main() {
    print(str(check(5)))
}
"""
        ir = _compile_to_llvm_ir(src, "test_trivial.mn", opt_level=OptLevel.O0)
        idx = ir.find("define internal noundef i1 @check")
        if idx < 0:
            idx = ir.find("@check(")
        assert idx >= 0, "expected @check function in IR"
        end = ir.find("\n}\n", idx)
        check_region = ir[idx:end] if end > idx else ir[idx:]
        # Trivial middle — no `__mn_chain_` synthesized name in @check
        assert "__mn_chain_" not in check_region, (
            "trivial Identifier middle should not allocate a chain temp\n"
            f"region:\n{check_region[:1500]}"
        )
