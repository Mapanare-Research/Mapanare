"""v5.15.0 Te.2.D — implicit-return one-liner.

``fn name(args) [-> RetType] = expr`` is sugar for
``fn name(args) [-> RetType] { return expr }``.

Block-form implicit return is *separately* covered by SPEC §4.5 and
already works pre-v5.15.0; these tests cover only the one-liner.
"""

from __future__ import annotations

from mapanare.ast_nodes import Block, FnDef, ReturnStmt
from mapanare.parser import parse


def _fn(program_src: str, name: str) -> FnDef:
    program = parse(program_src)
    for d in program.definitions:
        if isinstance(d, FnDef) and d.name == name:
            return d
    raise AssertionError(f"no fn {name!r}")


def test_one_liner_returns_expr_via_synthetic_return() -> None:
    fn = _fn("fn double(x: Int) -> Int = x * 2", "double")
    assert isinstance(fn.body, Block)
    assert len(fn.body.stmts) == 1
    stmt = fn.body.stmts[0]
    assert isinstance(stmt, ReturnStmt)
    assert stmt.value is not None


def test_one_liner_no_return_type() -> None:
    fn = _fn("fn id(y: Int) = y", "id")
    assert isinstance(fn.body, Block)
    assert len(fn.body.stmts) == 1
    assert isinstance(fn.body.stmts[0], ReturnStmt)


def test_one_liner_with_pub() -> None:
    fn = _fn("pub fn pi() -> Float = 3.14159", "pi")
    assert fn.public is True
    assert isinstance(fn.body, Block)
    assert isinstance(fn.body.stmts[0], ReturnStmt)


def test_block_form_unchanged() -> None:
    """Sanity: block-form fn still parses to a Block with the same
    statements. This is the v5.13.0-prep audit's already-shipped path
    — we must not regress it."""
    fn = _fn("fn add(a: Int, b: Int) -> Int { return a + b }", "add")
    assert isinstance(fn.body, Block)
    assert isinstance(fn.body.stmts[0], ReturnStmt)


def test_block_form_implicit_last_expr_unchanged() -> None:
    """The block-form last-expression-as-result was already shipped at
    v5.14.0; v5.15.0 must not touch this path."""
    fn = _fn("fn add(a: Int, b: Int) -> Int { a + b }", "add")
    assert isinstance(fn.body, Block)
    assert len(fn.body.stmts) == 1
