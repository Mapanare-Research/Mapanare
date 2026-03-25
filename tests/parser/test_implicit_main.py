"""Tests for the implicit main feature.

If a .mn file has no ``fn main()`` definition, top-level statements are
wrapped in a synthetic ``FnDef(name="main")``.  If both top-level statements
and an explicit ``fn main()`` exist, parsing raises ``ParseError``.
"""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import (
    Block,
    CallExpr,
    ExprStmt,
    FnDef,
    LetBinding,
    Program,
)
from mapanare.emit_python import PythonEmitter
from mapanare.parser import ParseError, parse

# ===================================================================
# Implicit main wrapping
# ===================================================================


class TestImplicitMain:
    # ------------------------------------------------------------------
    # 1. Simple top-level expression → synthetic main
    # ------------------------------------------------------------------
    def test_implicit_main_simple(self) -> None:
        p = parse('print("hello")')
        assert isinstance(p, Program)
        assert len(p.definitions) == 1
        fn = p.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.name == "main"
        assert isinstance(fn.body, Block)
        assert len(fn.body.stmts) == 1
        stmt = fn.body.stmts[0]
        assert isinstance(stmt, ExprStmt)
        assert isinstance(stmt.expr, CallExpr)

    # ------------------------------------------------------------------
    # 2. Multiple top-level statements → synthetic main with all stmts
    # ------------------------------------------------------------------
    def test_implicit_main_with_let(self) -> None:
        src = "let x: Int = 42\nlet y: Int = x + 8\nprint(y)"
        p = parse(src)
        assert len(p.definitions) == 1
        fn = p.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.name == "main"
        assert len(fn.body.stmts) == 3
        assert isinstance(fn.body.stmts[0], LetBinding)
        assert isinstance(fn.body.stmts[1], LetBinding)
        assert isinstance(fn.body.stmts[2], ExprStmt)

    # ------------------------------------------------------------------
    # 3. Helper fn + top-level stmt → helper first, synthetic main second
    # ------------------------------------------------------------------
    def test_implicit_main_with_helper_fn(self) -> None:
        src = (
            "fn greet(name: String) -> String {\n"
            '    return "Hello, " + name\n'
            "}\n"
            "\n"
            'print(greet("World"))'
        )
        p = parse(src)
        assert len(p.definitions) == 2
        assert isinstance(p.definitions[0], FnDef)
        assert p.definitions[0].name == "greet"
        assert isinstance(p.definitions[1], FnDef)
        assert p.definitions[1].name == "main"
        assert len(p.definitions[1].body.stmts) == 1

    # ------------------------------------------------------------------
    # 4. Explicit main left unchanged
    # ------------------------------------------------------------------
    def test_explicit_main_unchanged(self) -> None:
        src = 'fn main() {\n    print("still works")\n}'
        p = parse(src)
        assert len(p.definitions) == 1
        fn = p.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.name == "main"
        assert len(fn.body.stmts) == 1

    # ------------------------------------------------------------------
    # 5. Explicit main + top-level stmt → ParseError
    # ------------------------------------------------------------------
    def test_implicit_main_error_mixing(self) -> None:
        src = 'fn main() {\n    print("explicit")\n}\nprint("implicit")'
        with pytest.raises(ParseError, match="cannot mix"):
            parse(src)

    # ------------------------------------------------------------------
    # 6. Empty file → 0 definitions
    # ------------------------------------------------------------------
    def test_empty_file_no_main(self) -> None:
        p = parse("")
        assert isinstance(p, Program)
        assert len(p.definitions) == 0

    # ------------------------------------------------------------------
    # 7. Definitions only, no top-level stmts → no synthetic main
    # ------------------------------------------------------------------
    def test_definitions_only_no_main(self) -> None:
        src = "fn helper() -> Int {\n    return 42\n}"
        p = parse(src)
        assert len(p.definitions) == 1
        assert isinstance(p.definitions[0], FnDef)
        assert p.definitions[0].name == "helper"

    # ------------------------------------------------------------------
    # 8. Synthetic main is not public
    # ------------------------------------------------------------------
    def test_implicit_main_synthetic_not_public(self) -> None:
        p = parse('print("hello")')
        fn = p.definitions[0]
        assert isinstance(fn, FnDef)
        assert fn.name == "main"
        assert fn.public is False

    # ------------------------------------------------------------------
    # 9. Definitions + top-level stmts (no explicit main) → order preserved
    # ------------------------------------------------------------------
    def test_implicit_main_preserves_definition_order(self) -> None:
        src = 'fn helper() { }\nprint("x")'
        p = parse(src)
        assert len(p.definitions) == 2
        assert isinstance(p.definitions[0], FnDef)
        assert p.definitions[0].name == "helper"
        assert isinstance(p.definitions[1], FnDef)
        assert p.definitions[1].name == "main"

    # ------------------------------------------------------------------
    # 10. PythonEmitter: implicit main → sync def main (no async needed)
    # ------------------------------------------------------------------
    def test_emit_python_implicit_main(self) -> None:
        p = parse('print("hello")')
        emitter = PythonEmitter()
        output = emitter.emit(p)
        assert "def main()" in output
        assert "main()" in output
        # No async needed for a simple print
        assert "async def main()" not in output
        assert "asyncio.run" not in output

    # ------------------------------------------------------------------
    # 11. PythonEmitter: library (no main) → no asyncio.run
    # ------------------------------------------------------------------
    def test_emit_python_no_main_guard_for_library(self) -> None:
        src = "fn helper() -> Int {\n    return 42\n}"
        p = parse(src)
        emitter = PythonEmitter()
        output = emitter.emit(p)
        assert "asyncio.run(main())" not in output
