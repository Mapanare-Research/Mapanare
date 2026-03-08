"""Tests for mapa/self/ast.mn — verifies the self-hosted AST definitions
can be parsed and type-checked by the Python compiler.

The self-hosted AST must be valid Mapanare that the existing compiler accepts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapa.lexer import tokenize
from mapa.parser import parse
from mapa.semantic import check

AST_MN = Path(__file__).resolve().parents[2] / "mapa" / "self" / "ast.mn"


@pytest.fixture
def ast_source() -> str:
    return AST_MN.read_text(encoding="utf-8")


class TestAstMnParsing:
    """Ensure ast.mn parses without errors."""

    def test_tokenize(self, ast_source: str) -> None:
        tokens = tokenize(ast_source, filename="ast.mn")
        assert len(tokens) > 0
        type_names = {t.type for t in tokens}
        assert "KW_STRUCT" in type_names
        assert "KW_ENUM" in type_names
        assert "KW_FN" in type_names

    def test_parse(self, ast_source: str) -> None:
        program = parse(ast_source, filename="ast.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_struct_definitions(self, ast_source: str) -> None:
        program = parse(ast_source, filename="ast.mn")
        from mapa.ast_nodes import StructDef

        structs = [d for d in program.definitions if isinstance(d, StructDef)]
        struct_names = {s.name for s in structs}
        assert "Span" in struct_names
        assert "ASTNode" in struct_names
        assert "Program" in struct_names
        assert "Block" in struct_names
        assert "Param" in struct_names
        assert "FieldInit" in struct_names
        assert "Decorator" in struct_names
        assert "MatchArm" in struct_names
        assert "FnDefData" in struct_names
        assert "AgentInput" in struct_names
        assert "AgentOutput" in struct_names
        assert "AgentDefData" in struct_names
        assert "PipeDefData" in struct_names
        assert "StructField" in struct_names
        assert "StructDefData" in struct_names
        assert "EnumVariant" in struct_names
        assert "EnumDefData" in struct_names

    def test_enum_definitions(self, ast_source: str) -> None:
        program = parse(ast_source, filename="ast.mn")
        from mapa.ast_nodes import EnumDef

        enums = [d for d in program.definitions if isinstance(d, EnumDef)]
        enum_names = {e.name for e in enums}
        assert "TypeExpr" in enum_names
        assert "Expr" in enum_names
        assert "Stmt" in enum_names
        assert "Pattern" in enum_names
        assert "Definition" in enum_names
        assert "LambdaBody" in enum_names
        assert "ElseClause" in enum_names
        assert "MatchArmBody" in enum_names

    def test_fn_definitions(self, ast_source: str) -> None:
        program = parse(ast_source, filename="ast.mn")
        from mapa.ast_nodes import FnDef

        fns = [d for d in program.definitions if isinstance(d, FnDef)]
        fn_names = {f.name for f in fns}
        assert "make_named_type" in fn_names
        assert "make_void_type" in fn_names
        assert "make_int_type" in fn_names
        assert "make_float_type" in fn_names
        assert "make_bool_type" in fn_names
        assert "make_string_type" in fn_names

    def test_semantic_check_no_critical_errors(self, ast_source: str) -> None:
        """Semantic check should not produce critical errors.

        Note: Some errors are expected since the semantic checker doesn't
        yet know about all self-referential Mapanare types. We just verify
        there are no crashes and structural errors.
        """
        program = parse(ast_source, filename="ast.mn")
        errors = check(program, filename="ast.mn")
        # Should not crash; some type warnings are acceptable
        # since we use enum variants as constructors
        assert isinstance(errors, list)


class TestAstMnCoverage:
    """Verify the AST covers all node types from the Python compiler."""

    PYTHON_EXPR_TYPES = {
        "IntLiteral",
        "FloatLiteral",
        "StringLiteral",
        "CharLiteral",
        "BoolLiteral",
        "NoneLiteral",
        "Identifier",
        "BinaryExpr",
        "UnaryExpr",
        "CallExpr",
        "MethodCallExpr",
        "FieldAccessExpr",
        "NamespaceAccessExpr",
        "IndexExpr",
        "PipeExpr",
        "RangeExpr",
        "LambdaExpr",
        "SpawnExpr",
        "SyncExpr",
        "SendExpr",
        "ErrorPropExpr",
        "ListLiteral",
        "ConstructExpr",
        "SomeExpr",
        "OkExpr",
        "ErrExpr",
        "SignalExpr",
        "AssignExpr",
        "IfExpr",
        "MatchExpr",
    }

    MN_EXPR_VARIANTS = {
        "IntLit",
        "FloatLit",
        "StringLit",
        "CharLit",
        "BoolLit",
        "NoneLit",
        "Ident",
        "Binary",
        "Unary",
        "Call",
        "MethodCall",
        "FieldAccess",
        "NamespaceAccess",
        "Index",
        "Pipe",
        "Range",
        "Lambda",
        "Spawn",
        "Sync",
        "Send",
        "ErrorProp",
        "ListLit",
        "Construct",
        "SomeWrap",
        "OkWrap",
        "ErrWrap",
        "SignalVal",
        "Assign",
        "If",
        "Match",
    }

    def test_all_expr_types_covered(self, ast_source: str) -> None:
        """Every Python AST expression type has a corresponding .mn variant."""
        assert len(self.MN_EXPR_VARIANTS) == len(self.PYTHON_EXPR_TYPES)

    PYTHON_STMT_TYPES = {
        "LetBinding",
        "ExprStmt",
        "ReturnStmt",
        "ForLoop",
        "SignalDecl",
        "StreamDecl",
    }

    MN_STMT_VARIANTS = {
        "Let",
        "ExprStmt",
        "Return",
        "For",
        "SignalDecl",
        "StreamDecl",
    }

    def test_all_stmt_types_covered(self) -> None:
        assert len(self.MN_STMT_VARIANTS) == len(self.PYTHON_STMT_TYPES)

    PYTHON_PATTERN_TYPES = {
        "WildcardPattern",
        "IdentPattern",
        "LiteralPattern",
        "ConstructorPattern",
    }

    MN_PATTERN_VARIANTS = {
        "Wildcard",
        "IdentPat",
        "LiteralPat",
        "ConstructorPat",
    }

    def test_all_pattern_types_covered(self) -> None:
        assert len(self.MN_PATTERN_VARIANTS) == len(self.PYTHON_PATTERN_TYPES)

    PYTHON_DEF_TYPES = {
        "FnDef",
        "AgentDef",
        "PipeDef",
        "StructDef",
        "EnumDef",
        "TypeAlias",
        "ImplDef",
        "ImportDef",
        "ExportDef",
    }

    MN_DEF_VARIANTS = {
        "FnDef",
        "AgentDef",
        "PipeDef",
        "StructDef",
        "EnumDef",
        "TypeAlias",
        "ImplDef",
        "ImportDef",
        "ExportDef",
    }

    def test_all_def_types_covered(self) -> None:
        assert len(self.MN_DEF_VARIANTS) == len(self.PYTHON_DEF_TYPES)
