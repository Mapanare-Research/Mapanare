"""Tests for trait definitions, implementations, and trait bounds."""

from __future__ import annotations

import pytest

from mapanare.ast_nodes import FnDef, ImplDef, TraitDef
from mapanare.emit_python import PythonEmitter
from mapanare.parser import parse
from mapanare.semantic import SemanticChecker

try:
    from mapanare.emit_llvm import LLVMEmitter

    HAS_LLVM = True
except ImportError:
    HAS_LLVM = False


# ---------------------------------------------------------------------------
# Parsing tests
# ---------------------------------------------------------------------------


class TestTraitParsing:
    """Test that trait syntax parses correctly."""

    def test_basic_trait_def(self) -> None:
        src = "trait Display {\n    fn to_string(self) -> String\n}\n"
        p = parse(src)
        assert len(p.definitions) == 1
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        assert t.name == "Display"
        assert len(t.methods) == 1
        assert t.methods[0].name == "to_string"
        assert t.methods[0].has_self is True

    def test_trait_with_multiple_methods(self) -> None:
        src = (
            "trait Ord {\n"
            "    fn cmp(self, other: Int) -> Int\n"
            "    fn lt(self, other: Int) -> Bool\n"
            "}\n"
        )
        p = parse(src)
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        assert len(t.methods) == 2
        assert t.methods[0].name == "cmp"
        assert t.methods[1].name == "lt"

    def test_pub_trait(self) -> None:
        src = "pub trait Hash {\n    fn hash(self) -> Int\n}\n"
        p = parse(src)
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        assert t.public is True

    def test_trait_method_no_return_type(self) -> None:
        src = "trait Runnable {\n    fn run(self)\n}\n"
        p = parse(src)
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        assert t.methods[0].return_type is None

    def test_trait_method_with_params(self) -> None:
        src = "trait Eq {\n    fn eq(self, other: Int) -> Bool\n}\n"
        p = parse(src)
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        m = t.methods[0]
        assert m.name == "eq"
        assert m.has_self is True
        assert len(m.params) == 1
        assert m.params[0].name == "other"

    def test_impl_trait_for_type(self) -> None:
        src = (
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        d = p.definitions[0]
        assert isinstance(d, ImplDef)
        assert d.trait_name == "Display"
        assert d.target == "Point"
        assert len(d.methods) == 1

    def test_inherent_impl_no_trait(self) -> None:
        src = (
            "impl Point {\n" "    fn dist(self) -> Float {\n" "        return 0.0\n" "    }\n" "}\n"
        )
        p = parse(src)
        d = p.definitions[0]
        assert isinstance(d, ImplDef)
        assert d.trait_name is None
        assert d.target == "Point"

    def test_trait_bounds_on_generics(self) -> None:
        src = "fn max<T: Ord>(a: T, b: T) -> T {\n" "    return a\n" "}\n"
        p = parse(src)
        f = p.definitions[0]
        assert isinstance(f, FnDef)
        assert f.type_params == ["T"]
        assert f.trait_bounds == {"T": "Ord"}

    def test_multiple_type_params_with_bounds(self) -> None:
        src = "fn foo<A: Display, B>(a: A, b: B) -> String {\n" '    return "ok"\n' "}\n"
        p = parse(src)
        f = p.definitions[0]
        assert isinstance(f, FnDef)
        assert f.type_params == ["A", "B"]
        assert f.trait_bounds == {"A": "Display"}

    def test_type_param_no_bound(self) -> None:
        src = "fn id<T>(x: T) -> T {\n    return x\n}\n"
        p = parse(src)
        f = p.definitions[0]
        assert isinstance(f, FnDef)
        assert f.type_params == ["T"]
        assert f.trait_bounds == {}

    def test_self_typed_param_in_impl(self) -> None:
        """Backward compat: self: Type still works."""
        src = (
            "impl Point {\n"
            "    fn dist(self: Point) -> Float {\n"
            "        return 0.0\n"
            "    }\n"
            "}\n"
        )
        p = parse(src)
        d = p.definitions[0]
        assert isinstance(d, ImplDef)
        assert d.methods[0].params[0].name == "self"


# ---------------------------------------------------------------------------
# Semantic checking tests
# ---------------------------------------------------------------------------


class TestTraitSemantic:
    """Test semantic analysis of traits."""

    def test_trait_def_registers_in_scope(self) -> None:
        src = "trait Display {\n    fn to_string(self) -> String\n}\n"
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0
        sym = checker.global_scope.lookup("Display")
        assert sym is not None
        assert sym.kind == "trait"

    def test_impl_trait_missing_method_error(self) -> None:
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "    fn format(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert any("Missing implementation of 'format'" in e.message for e in errors)

    def test_impl_trait_extra_method_error(self) -> None:
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "    fn extra(self) -> String {\n"
            '        return "extra"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert any("'extra' is not defined in trait" in e.message for e in errors)

    def test_impl_trait_all_methods_ok(self) -> None:
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0

    def test_impl_undefined_trait_error(self) -> None:
        src = (
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl FakeTrait for Point {\n"
            "    fn foo(self) -> Int {\n"
            "        return 0\n"
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert any("Undefined trait 'FakeTrait'" in e.message for e in errors)

    def test_impl_undefined_type_error(self) -> None:
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "impl Display for FakeType {\n"
            "    fn to_string(self) -> String {\n"
            '        return "fake"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert any("Undefined type 'FakeType'" in e.message for e in errors)

    def test_inherent_impl_still_works(self) -> None:
        """Existing impl without trait should continue to work."""
        src = (
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Point {\n"
            "    fn origin(self) -> Bool {\n"
            "        return true\n"
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0

    def test_trait_bounds_parse_correctly(self) -> None:
        """Trait bounds on generics are stored in FnDef."""
        src = (
            "trait Ord {\n"
            "    fn cmp(self, other: Int) -> Int\n"
            "}\n"
            "fn max<T: Ord>(a: T, b: T) -> T {\n"
            "    return a\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0

    def test_empty_trait(self) -> None:
        src = "trait Marker {\n}\n"
        p = parse(src)
        assert len(p.definitions) == 1
        t = p.definitions[0]
        assert isinstance(t, TraitDef)
        assert len(t.methods) == 0

    def test_empty_trait_impl(self) -> None:
        src = "trait Marker {\n}\n" "struct Foo {\n    x: Int\n}\n" "impl Marker for Foo {\n}\n"
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0

    def test_trait_impl_tracked(self) -> None:
        """Successful trait impls are tracked for bound checking."""
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0
        assert checker._type_implements_trait("Point", "Display")
        assert not checker._type_implements_trait("Point", "Eq")

    def test_trait_with_multiple_params(self) -> None:
        """Trait with method that has multiple typed params."""
        src = "trait Comparable {\n" "    fn compare(self, other: Int, flag: Bool) -> Int\n" "}\n"
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0

    def test_failed_trait_impl_not_tracked(self) -> None:
        """Incomplete trait impls are NOT tracked."""
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "    fn format(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        checker.check(p)
        assert not checker._type_implements_trait("Point", "Display")


# ---------------------------------------------------------------------------
# Python emission tests
# ---------------------------------------------------------------------------


class TestTraitPythonEmission:
    """Test Python backend emission of traits."""

    def test_trait_emits_protocol(self) -> None:
        src = "trait Display {\n    fn to_string(self) -> String\n}\n"
        p = parse(src)
        emitter = PythonEmitter()
        code = emitter.emit(p)
        assert "from typing import Protocol" in code
        assert "class Display(Protocol):" in code
        assert "def to_string(self) -> str: ..." in code

    def test_trait_with_params_emits_protocol(self) -> None:
        src = "trait Eq {\n    fn eq(self, other: Int) -> Bool\n}\n"
        p = parse(src)
        emitter = PythonEmitter()
        code = emitter.emit(p)
        assert "class Eq(Protocol):" in code
        assert "def eq(self, other: int) -> bool: ..." in code

    def test_empty_trait_emits_pass(self) -> None:
        src = "trait Marker {\n}\n"
        p = parse(src)
        emitter = PythonEmitter()
        code = emitter.emit(p)
        assert "class Marker(Protocol):" in code
        assert "pass" in code

    def test_trait_impl_methods_merged_into_struct(self) -> None:
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        emitter = PythonEmitter()
        code = emitter.emit(p)
        assert "class Point:" in code
        assert "def to_string(self)" in code


# ---------------------------------------------------------------------------
# LLVM emission tests
# ---------------------------------------------------------------------------


class TestBuiltinTraits:
    """Test builtin traits are pre-registered."""

    def test_display_registered(self) -> None:
        checker = SemanticChecker()
        checker.check(parse("fn main() {}"))
        sym = checker.global_scope.lookup("Display")
        assert sym is not None
        assert sym.kind == "trait"

    def test_eq_registered(self) -> None:
        checker = SemanticChecker()
        checker.check(parse("fn main() {}"))
        assert checker.global_scope.lookup("Eq") is not None

    def test_ord_registered(self) -> None:
        checker = SemanticChecker()
        checker.check(parse("fn main() {}"))
        assert checker.global_scope.lookup("Ord") is not None

    def test_hash_registered(self) -> None:
        checker = SemanticChecker()
        checker.check(parse("fn main() {}"))
        assert checker.global_scope.lookup("Hash") is not None

    def test_impl_builtin_trait(self) -> None:
        src = (
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0
        assert checker._type_implements_trait("Point", "Display")

    def test_impl_builtin_trait_missing_method(self) -> None:
        src = (
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Eq for Point {\n"
            "}\n"
        )
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert any("Missing implementation of 'eq'" in e.message for e in errors)

    def test_bounded_generic_with_builtin_trait(self) -> None:
        src = "fn max<T: Ord>(a: Int, b: Int) -> Int {\n" "    return a\n" "}\n"
        p = parse(src)
        checker = SemanticChecker()
        errors = checker.check(p)
        assert len(errors) == 0


@pytest.mark.skipif(not HAS_LLVM, reason="llvmlite not installed")
class TestTraitLLVMEmission:
    """Test LLVM backend emission of traits."""

    def test_trait_def_no_codegen(self) -> None:
        """Trait definitions produce no LLVM code (type-level only)."""
        src = "trait Display {\n    fn to_string(self) -> String\n}\n"
        p = parse(src)
        emitter = LLVMEmitter()
        mod = emitter.emit_program(p)
        llvm_ir = str(mod)
        # No function should be generated for the trait itself
        assert "Display" not in llvm_ir or "define" not in llvm_ir

    def test_impl_methods_emitted_as_functions(self) -> None:
        """Trait impl methods are emitted as mangled standalone functions."""
        src = (
            "trait Display {\n"
            "    fn to_string(self) -> String\n"
            "}\n"
            "struct Point {\n"
            "    x: Float,\n"
            "    y: Float\n"
            "}\n"
            "impl Display for Point {\n"
            "    fn to_string(self) -> String {\n"
            '        return "point"\n'
            "    }\n"
            "}\n"
        )
        p = parse(src)
        emitter = LLVMEmitter()
        mod = emitter.emit_program(p)
        llvm_ir = str(mod)
        # Should have a function named Point_to_string
        assert "Point_to_string" in llvm_ir

    def test_trait_with_bounded_generic_fn(self) -> None:
        """Generic fn with trait bounds compiles."""
        src = (
            "trait Ord {\n"
            "    fn cmp(self, other: Int) -> Int\n"
            "}\n"
            "fn max<T: Ord>(a: Int, b: Int) -> Int {\n"
            "    return a\n"
            "}\n"
        )
        p = parse(src)
        emitter = LLVMEmitter()
        mod = emitter.emit_program(p)
        llvm_ir = str(mod)
        assert "define" in llvm_ir
        assert "max" in llvm_ir
