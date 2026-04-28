"""v5.0.5: Parser tests for qualified type references (Gr.2 + Cb.9a).

Grammar accepts NAME (DOT NAME)* in named_type and generic_type rules.
The parser splits the dotted path into module_path (prefix) and name (last).
"""

from __future__ import annotations

from mapanare.ast_nodes import (
    FnDef,
    GenericType,
    LetBinding,
    NamedType,
    Param,
    StructDef,
    StructField,
)
from mapanare.parser import parse


def _parse_fn(src: str) -> FnDef:
    prog = parse(src, filename="test.mn")
    fns = [d for d in prog.definitions if isinstance(d, FnDef)]
    assert len(fns) >= 1
    return fns[0]


class TestQualifiedNamedType:
    """Qualified type in named_type position: NAME (DOT NAME)*."""

    def test_simple_qualified_type_in_let(self):
        src = "fn main() { let x: gpu.Device = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, NamedType)
        assert te.name == "Device"
        assert te.module_path == ["gpu"]

    def test_two_segment_qualified_type(self):
        src = "fn main() { let x: std.io.File = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, NamedType)
        assert te.name == "File"
        assert te.module_path == ["std", "io"]

    def test_qualified_type_as_fn_param(self):
        src = "fn apply(k: gpu.Kernel) { }\n"
        fn = _parse_fn(src)
        param = fn.params[0]
        assert isinstance(param, Param)
        te = param.type_annotation
        assert isinstance(te, NamedType)
        assert te.name == "Kernel"
        assert te.module_path == ["gpu"]

    def test_qualified_type_as_return_type(self):
        src = "fn make() -> gpu.Device { }\n"
        fn = _parse_fn(src)
        te = fn.return_type
        assert isinstance(te, NamedType)
        assert te.name == "Device"
        assert te.module_path == ["gpu"]

    def test_unqualified_type_has_empty_module_path(self):
        src = "fn main() { let x: Int = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, NamedType)
        assert te.name == "Int"
        assert te.module_path == []


class TestQualifiedGenericType:
    """Qualified type in generic_type position: NAME (DOT NAME)* LT ... GT."""

    def test_qualified_generic_in_let(self):
        src = "fn main() { let t: gpu.Tensor<Int> = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, GenericType)
        assert te.name == "Tensor"
        assert te.module_path == ["gpu"]
        assert len(te.args) == 1
        assert isinstance(te.args[0], NamedType)
        assert te.args[0].name == "Int"

    def test_qualified_generic_as_fn_param(self):
        src = "fn consume(data: gpu.Tensor<Float>) { }\n"
        fn = _parse_fn(src)
        param = fn.params[0]
        te = param.type_annotation
        assert isinstance(te, GenericType)
        assert te.name == "Tensor"
        assert te.module_path == ["gpu"]

    def test_qualified_generic_as_return_type(self):
        src = "fn produce() -> gpu.Tensor<Int> { }\n"
        fn = _parse_fn(src)
        te = fn.return_type
        assert isinstance(te, GenericType)
        assert te.name == "Tensor"
        assert te.module_path == ["gpu"]

    def test_qualified_generic_nested_in_builtin(self):
        """Map<gpu.Tensor<Int>, String> -- qualified generic inside a builtin generic."""
        src = "fn main() { let m: Map<gpu.Tensor<Int>, String> = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, GenericType)
        assert te.name == "Map"
        assert te.module_path == []
        assert len(te.args) == 2
        inner = te.args[0]
        assert isinstance(inner, GenericType)
        assert inner.name == "Tensor"
        assert inner.module_path == ["gpu"]

    def test_unqualified_generic_has_empty_module_path(self):
        src = "fn main() { let x: List<Int> = 0 }\n"
        fn = _parse_fn(src)
        let_stmt = fn.body.stmts[0]
        assert isinstance(let_stmt, LetBinding)
        te = let_stmt.type_annotation
        assert isinstance(te, GenericType)
        assert te.name == "List"
        assert te.module_path == []


class TestQualifiedTypeInStructField:
    """Qualified types used as struct field type annotations."""

    def test_struct_field_qualified_type(self):
        src = "struct Foo { dev: gpu.DeviceKind }\nfn main() { }\n"
        prog = parse(src, filename="test.mn")
        structs = [d for d in prog.definitions if isinstance(d, StructDef)]
        assert len(structs) == 1
        field = structs[0].fields[0]
        assert isinstance(field, StructField)
        te = field.type_annotation
        assert isinstance(te, NamedType)
        assert te.name == "DeviceKind"
        assert te.module_path == ["gpu"]

    def test_struct_field_qualified_generic(self):
        src = "struct Foo { items: gpu.Tensor<Int> }\nfn main() { }\n"
        prog = parse(src, filename="test.mn")
        structs = [d for d in prog.definitions if isinstance(d, StructDef)]
        assert len(structs) == 1
        field = structs[0].fields[0]
        assert isinstance(field, StructField)
        te = field.type_annotation
        assert isinstance(te, GenericType)
        assert te.name == "Tensor"
        assert te.module_path == ["gpu"]
