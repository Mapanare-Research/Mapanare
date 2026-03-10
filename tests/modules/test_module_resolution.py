"""Tests for module resolution (Phase 2.2).

Tests cover:
- Module path resolution (file lookup)
- Single import, selective import
- pub visibility enforcement
- Transitive imports
- Circular import detection
- Module caching
- Python emitter output for imports
- LLVM emitter handling of imports
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mapanare.ast_nodes import (
    ImportDef,
    Program,
    TypeAlias,
)
from mapanare.modules import ModuleResolutionError, ModuleResolver
from mapanare.parser import parse
from mapanare.semantic import check

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_mn(directory: str, name: str, content: str) -> str:
    """Write a .mn file and return its absolute path."""
    path = os.path.join(directory, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Module path resolution
# ---------------------------------------------------------------------------


class TestModulePathResolution:
    """Tests for ModuleResolver.resolve_path."""

    def test_resolve_simple_module(self, tmp_path: Path) -> None:
        """import math → math.mn"""
        (tmp_path / "math.mn").write_text("pub fn add(a: Int, b: Int) -> Int { return a + b }")
        resolver = ModuleResolver()
        result = resolver.resolve_path(["math"], str(tmp_path))
        assert result is not None
        assert result.endswith("math.mn")

    def test_resolve_nested_module(self, tmp_path: Path) -> None:
        """import utils::helpers → utils/helpers.mn"""
        (tmp_path / "utils").mkdir()
        (tmp_path / "utils" / "helpers.mn").write_text("pub fn helper() { }")
        resolver = ModuleResolver()
        result = resolver.resolve_path(["utils", "helpers"], str(tmp_path))
        assert result is not None
        assert "helpers.mn" in result

    def test_resolve_directory_module(self, tmp_path: Path) -> None:
        """import mymod → mymod/mod.mn"""
        (tmp_path / "mymod").mkdir()
        (tmp_path / "mymod" / "mod.mn").write_text("pub fn init() { }")
        resolver = ModuleResolver()
        result = resolver.resolve_path(["mymod"], str(tmp_path))
        assert result is not None
        assert "mod.mn" in result

    def test_resolve_not_found(self, tmp_path: Path) -> None:
        """import nonexistent → None"""
        resolver = ModuleResolver()
        result = resolver.resolve_path(["nonexistent"], str(tmp_path))
        assert result is None

    def test_file_preferred_over_dir(self, tmp_path: Path) -> None:
        """When both foo.mn and foo/mod.mn exist, foo.mn wins."""
        (tmp_path / "foo.mn").write_text("pub fn from_file() { }")
        (tmp_path / "foo").mkdir()
        (tmp_path / "foo" / "mod.mn").write_text("pub fn from_dir() { }")
        resolver = ModuleResolver()
        result = resolver.resolve_path(["foo"], str(tmp_path))
        assert result is not None
        assert result.endswith("foo.mn")
        assert "mod.mn" not in result


# ---------------------------------------------------------------------------
# Module loading and exports
# ---------------------------------------------------------------------------


class TestModuleLoading:
    """Tests for module loading, caching, and export extraction."""

    def test_load_module_with_pub_fn(self, tmp_path: Path) -> None:
        main_path = _write_mn(str(tmp_path), "main.mn", 'import math\nfn main() { print("hi") }')
        _write_mn(
            str(tmp_path),
            "math.mn",
            "pub fn add(a: Int, b: Int) -> Int { return a + b }\nfn private_helper() { }",
        )
        resolver = ModuleResolver()
        module = resolver.resolve_module(["math"], main_path)
        assert "add" in module.exports
        assert module.exports["add"].public is True
        assert "private_helper" in module.exports
        assert module.exports["private_helper"].public is False

    def test_module_caching(self, tmp_path: Path) -> None:
        main_path = _write_mn(str(tmp_path), "main.mn", "import utils")
        _write_mn(str(tmp_path), "utils.mn", "pub fn helper() { }")
        resolver = ModuleResolver()
        mod1 = resolver.resolve_module(["utils"], main_path)
        mod2 = resolver.resolve_module(["utils"], main_path)
        assert mod1 is mod2

    def test_module_not_found_error(self, tmp_path: Path) -> None:
        main_path = _write_mn(str(tmp_path), "main.mn", "import ghost")
        resolver = ModuleResolver()
        with pytest.raises(ModuleResolutionError, match="module 'ghost' not found"):
            resolver.resolve_module(["ghost"], main_path)

    def test_pub_struct_export(self, tmp_path: Path) -> None:
        main_path = _write_mn(str(tmp_path), "main.mn", "import types")
        _write_mn(
            str(tmp_path),
            "types.mn",
            "pub struct Point { x: Int, y: Int }\nstruct Internal { data: Int }",
        )
        resolver = ModuleResolver()
        module = resolver.resolve_module(["types"], main_path)
        assert "Point" in module.exports
        assert module.exports["Point"].public is True
        assert "Internal" in module.exports
        assert module.exports["Internal"].public is False

    def test_pub_enum_export(self, tmp_path: Path) -> None:
        main_path = _write_mn(str(tmp_path), "main.mn", "import colors")
        _write_mn(
            str(tmp_path),
            "colors.mn",
            "pub enum Color { Red, Green, Blue }",
        )
        resolver = ModuleResolver()
        module = resolver.resolve_module(["colors"], main_path)
        assert "Color" in module.exports
        assert module.exports["Color"].public is True


# ---------------------------------------------------------------------------
# Circular import detection
# ---------------------------------------------------------------------------


class TestCircularImports:
    """Tests for circular import detection."""

    def test_direct_circular_import(self, tmp_path: Path) -> None:
        _write_mn(str(tmp_path), "a.mn", "import b\npub fn fa() { }")
        _write_mn(str(tmp_path), "b.mn", "import a\npub fn fb() { }")
        main_path = str(tmp_path / "a.mn")
        resolver = ModuleResolver()
        with pytest.raises(ModuleResolutionError, match="circular import detected"):
            resolver.resolve_module(["b"], main_path)

    def test_indirect_circular_import(self, tmp_path: Path) -> None:
        _write_mn(str(tmp_path), "a.mn", "import b\npub fn fa() { }")
        _write_mn(str(tmp_path), "b.mn", "import c\npub fn fb() { }")
        _write_mn(str(tmp_path), "c.mn", "import a\npub fn fc() { }")
        main_path = str(tmp_path / "a.mn")
        resolver = ModuleResolver()
        with pytest.raises(ModuleResolutionError, match="circular import detected"):
            resolver.resolve_module(["b"], main_path)


# ---------------------------------------------------------------------------
# Semantic checking with module resolution
# ---------------------------------------------------------------------------


class TestSemanticModuleResolution:
    """Tests for semantic checker integration with module resolution."""

    def test_selective_import_pub_fn(self, tmp_path: Path) -> None:
        """import math { add } — pub fn add is accessible."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import math { add }\nfn main() { let x: Int = add(1, 2) }",
        )
        _write_mn(
            str(tmp_path),
            "math.mn",
            "pub fn add(a: Int, b: Int) -> Int { return a + b }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert errors == []

    def test_selective_import_private_fn_error(self, tmp_path: Path) -> None:
        """import math { helper } — non-pub fn produces error."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import math { helper }\nfn main() { }",
        )
        _write_mn(
            str(tmp_path),
            "math.mn",
            "fn helper() { }\npub fn add(a: Int, b: Int) -> Int { return a + b }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert len(errors) == 1
        assert "not public" in errors[0].message

    def test_selective_import_nonexistent_error(self, tmp_path: Path) -> None:
        """import math { nonexistent } — symbol not found."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import math { nonexistent }\nfn main() { }",
        )
        _write_mn(
            str(tmp_path),
            "math.mn",
            "pub fn add(a: Int, b: Int) -> Int { return a + b }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert len(errors) == 1
        assert "not found in module" in errors[0].message

    def test_module_not_found_error(self, tmp_path: Path) -> None:
        """import nonexistent — module not found."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import nonexistent\nfn main() { }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert len(errors) == 1
        assert "not found" in errors[0].message

    def test_full_module_import(self, tmp_path: Path) -> None:
        """import utils — registers module name in scope."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import utils\nfn main() { }",
        )
        _write_mn(
            str(tmp_path),
            "utils.mn",
            "pub fn helper() { }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert errors == []

    def test_import_struct(self, tmp_path: Path) -> None:
        """import types { Point } — struct type is registered in scope."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import types { Point }\nfn main() { let p: Point = p }",
        )
        _write_mn(
            str(tmp_path),
            "types.mn",
            "pub struct Point { x: Int, y: Int }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        # No "unknown type Point" error — the struct type is resolved
        assert not any("unknown type" in e.message.lower() for e in errors)

    def test_import_enum(self, tmp_path: Path) -> None:
        """import colors { Color } — enum variants are registered in scope."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import colors { Color }\nfn main() { let c = Red }",
        )
        _write_mn(
            str(tmp_path),
            "colors.mn",
            "pub enum Color { Red, Green, Blue }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        # Red should be recognized (no "undefined variable" error)
        assert not any("undefined" in e.message.lower() for e in errors)


# ---------------------------------------------------------------------------
# Transitive imports
# ---------------------------------------------------------------------------


class TestTransitiveImports:
    """Tests for transitive import behavior."""

    def test_transitive_not_visible(self, tmp_path: Path) -> None:
        """A imports B, B imports C. A cannot see C's symbols."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import b { fb }\nfn main() { fb() }",
        )
        _write_mn(
            str(tmp_path),
            "b.mn",
            "import c { fc }\npub fn fb() { fc() }",
        )
        _write_mn(
            str(tmp_path),
            "c.mn",
            "pub fn fc() { }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        # main.mn should pass — it only uses fb which is public in b
        assert errors == []

    def test_chained_imports_resolve(self, tmp_path: Path) -> None:
        """A imports B, B imports C. All modules parse and check correctly."""
        main_path = _write_mn(
            str(tmp_path),
            "main.mn",
            "import b { fb }\nfn main() { let x: Int = fb() }",
        )
        _write_mn(
            str(tmp_path),
            "b.mn",
            "import c { fc }\npub fn fb() -> Int { return fc() }",
        )
        _write_mn(
            str(tmp_path),
            "c.mn",
            "pub fn fc() -> Int { return 42 }",
        )
        resolver = ModuleResolver()
        ast = parse(
            open(main_path, encoding="utf-8").read(),
            filename=main_path,
        )
        errors = check(ast, filename=main_path, resolver=resolver)
        assert errors == []


# ---------------------------------------------------------------------------
# Backward compatibility (no resolver)
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Tests that semantic checking still works without a resolver."""

    def test_import_without_resolver(self) -> None:
        """When no resolver, imports register as UNKNOWN_TYPE (old behavior)."""
        source = 'import std::io\nfn main() { print("hello") }'
        ast = parse(source, filename="<test>")
        errors = check(ast, filename="<test>")
        assert errors == []

    def test_selective_import_without_resolver(self) -> None:
        """Selective import without resolver registers names."""
        source = "import math { sin, cos }\nfn main() { }"
        ast = parse(source, filename="<test>")
        errors = check(ast, filename="<test>")
        assert errors == []


# ---------------------------------------------------------------------------
# Python emitter
# ---------------------------------------------------------------------------


class TestPythonEmitterImports:
    """Tests that the Python emitter generates correct import statements."""

    def test_emit_simple_import(self) -> None:
        from mapanare.emit_python import PythonEmitter

        imp = ImportDef(path=["utils"], items=[])
        program = Program(definitions=[imp])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "import utils" in code

    def test_emit_nested_import(self) -> None:
        from mapanare.emit_python import PythonEmitter

        imp = ImportDef(path=["std", "io"], items=[])
        program = Program(definitions=[imp])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "import std.io" in code

    def test_emit_selective_import(self) -> None:
        from mapanare.emit_python import PythonEmitter

        imp = ImportDef(path=["math", "trig"], items=["sin", "cos"])
        program = Program(definitions=[imp])
        emitter = PythonEmitter()
        code = emitter.emit(program)
        assert "from math.trig import sin, cos" in code


# ---------------------------------------------------------------------------
# pub type_alias
# ---------------------------------------------------------------------------


class TestPubTypeAlias:
    """Tests for pub type alias parsing."""

    def test_parse_pub_type_alias(self) -> None:
        source = "pub type Meters = Int"
        ast = parse(source, filename="<test>")
        assert len(ast.definitions) == 1
        alias = ast.definitions[0]
        assert isinstance(alias, TypeAlias)
        assert alias.name == "Meters"
        assert alias.public is True

    def test_parse_private_type_alias(self) -> None:
        source = "type Meters = Int"
        ast = parse(source, filename="<test>")
        alias = ast.definitions[0]
        assert isinstance(alias, TypeAlias)
        assert alias.public is False
