"""Phase 8 — Cross-Module LLVM Compilation tests.

Tests verify that multi-module compilation works end-to-end:
  - Two-file compilation with cross-module function calls
  - Three-level import chain
  - Circular dependency detection
  - Cross-module struct sharing
  - Stdlib module imports (encoding::json, crypto)
  - pub visibility enforcement (non-pub symbols hidden)
  - Module prefix computation and name mangling
  - Dependency ordering (topological sort)
  - Incremental compilation (hash-based change detection)
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.modules import ModuleResolutionError, ModuleResolver
from mapanare.multi_module import (
    build_dependency_order,
    compile_multi_module_mir,
    module_prefix,
    module_short_name,
)
from mapanare.parser import parse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_mn(directory: str, name: str, content: str) -> str:
    """Write a .mn file and return its absolute path."""
    path = os.path.join(directory, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content))
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Task 17: Two-file compilation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTwoFileCompilation:
    """a.mn imports b.mn, calls function from b."""

    def test_import_and_call(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "math.mn",
            """\
            pub fn add(a: Int, b: Int) -> Int {
                return a + b
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import math { add }

            fn main() {
                let result = add(2, 3)
                println(str(result))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        # The imported function should be present (mangled)
        assert "math__add" in ir_out

    def test_namespace_access(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "utils.mn",
            """\
            pub fn greet() -> String {
                return "hello"
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import utils

            fn main() {
                let msg = utils.greet()
                println(msg)
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        assert "utils__greet" in ir_out


# ---------------------------------------------------------------------------
# Task 18: Three-level import chain
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestThreeLevelChain:
    """a imports b imports c — three levels of dependency."""

    def test_transitive_import(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "base.mn",
            """\
            pub fn base_value() -> Int {
                return 42
            }
        """,
        )
        _write_mn(
            str(tmp_path),
            "middle.mn",
            """\
            import base { base_value }

            pub fn double_base() -> Int {
                let v = base_value()
                return v + v
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "app.mn",
            """\
            import middle { double_base }

            fn main() {
                let result = double_base()
                println(str(result))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        # Both dependencies should be present
        assert "base__base_value" in ir_out
        assert "middle__double_base" in ir_out


# ---------------------------------------------------------------------------
# Task 19: Circular dependency detection
# ---------------------------------------------------------------------------


class TestCircularDependency:
    """Circular imports should be detected and reported."""

    def test_circular_import_error(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "a.mn",
            """\
            import b
            pub fn fa() -> Int { return 1 }
        """,
        )
        _write_mn(
            str(tmp_path),
            "b.mn",
            """\
            import a
            pub fn fb() -> Int { return 2 }
        """,
        )
        root = os.path.join(str(tmp_path), "a.mn")
        with open(root, encoding="utf-8") as f:
            source = f.read()
        with pytest.raises((ModuleResolutionError, Exception)):
            compile_multi_module_mir(source, root)


# ---------------------------------------------------------------------------
# Task 20: Cross-module struct sharing
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCrossModuleStruct:
    """Struct defined in module A, used in module B."""

    def test_struct_from_import(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "types.mn",
            """\
            pub struct Point {
                x: Int,
                y: Int,
            }

            pub fn make_point(px: Int, py: Int) -> Point {
                return new Point {x: px, y: py}
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import types { make_point }

            fn main() {
                let p = make_point(10, 20)
                println(str(p.x))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        # The imported function should be present with module prefix
        assert "types__make_point" in ir_out

    def test_enum_from_import(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "colors.mn",
            """\
            pub enum Color {
                Red(Int),
                Green(Int),
                Blue(Int)
            }

            pub fn is_red(c: Color) -> Bool {
                match c {
                    Red(v) => { return true },
                    Green(v) => { return false },
                    Blue(v) => { return false }
                }
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import colors { Color, is_red }

            fn main() {
                let c = Red(1)
                let r = is_red(c)
                println(str(r))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        assert "colors__is_red" in ir_out


# ---------------------------------------------------------------------------
# Task 21: Stdlib module import
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestStdlibImport:
    """import encoding::json should resolve to stdlib/encoding/json.mn."""

    def test_stdlib_crypto_import(self) -> None:
        """Test that importing crypto stdlib resolves and compiles."""
        import tempfile

        # crypto.mn has functions; CryptoError is pub but variants need
        # full module import. Test with a simple selective import that
        # verifies stdlib path resolution works.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mn", delete=False, encoding="utf-8"
        ) as f:
            f.write(textwrap.dedent("""\
                import crypto

                fn main() {
                    println("crypto imported")
                }
            """))
            root = f.name
        try:
            with open(root, encoding="utf-8") as f:
                source = f.read()
            ir_out = compile_multi_module_mir(source, root)
            assert "main" in ir_out
            # The crypto module should be compiled into the output
            assert "crypto__" in ir_out or "CryptoError" in ir_out
        finally:
            os.unlink(root)


# ---------------------------------------------------------------------------
# Task 22: pub visibility enforcement
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPubVisibility:
    """Non-pub symbols should not be accessible from outside the module."""

    def test_non_pub_function_inaccessible(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "secret.mn",
            """\
            fn internal_fn() -> Int {
                return 42
            }

            pub fn public_fn() -> Int {
                return internal_fn()
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import secret { internal_fn }

            fn main() {
                let x = internal_fn()
                println(str(x))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        # Should error because internal_fn is not pub
        with pytest.raises(Exception):
            compile_multi_module_mir(source, root)

    def test_non_pub_gets_internal_linkage(self, tmp_path: Path) -> None:
        """Non-pub functions in imported modules get LLVM internal linkage."""
        _write_mn(
            str(tmp_path),
            "helper.mn",
            """\
            fn private_helper() -> Int {
                return 10
            }

            pub fn public_api() -> Int {
                return private_helper()
            }
        """,
        )
        root = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import helper { public_api }

            fn main() {
                let x = public_api()
                println(str(x))
            }
        """,
        )
        with open(root, encoding="utf-8") as f:
            source = f.read()
        ir_out = compile_multi_module_mir(source, root)
        assert "main" in ir_out
        # The public function should be present
        assert "helper__public_api" in ir_out
        # The private function should be internal
        assert "internal" in ir_out
        assert "helper__private_helper" in ir_out


# ---------------------------------------------------------------------------
# Module prefix computation
# ---------------------------------------------------------------------------


class TestModulePrefix:
    """Test module_prefix and module_short_name helpers."""

    def test_stdlib_simple(self) -> None:
        from mapanare.multi_module import _get_stdlib_dir

        stdlib = _get_stdlib_dir()
        fp = os.path.join(stdlib, "crypto.mn")
        assert module_prefix(fp) == "crypto__"

    def test_stdlib_nested(self) -> None:
        from mapanare.multi_module import _get_stdlib_dir

        stdlib = _get_stdlib_dir()
        fp = os.path.join(stdlib, "encoding", "json.mn")
        assert module_prefix(fp) == "encoding_json__"

    def test_stdlib_deep_nested(self) -> None:
        from mapanare.multi_module import _get_stdlib_dir

        stdlib = _get_stdlib_dir()
        fp = os.path.join(stdlib, "net", "http", "server.mn")
        assert module_prefix(fp) == "net_http_server__"

    def test_non_stdlib(self, tmp_path: Path) -> None:
        fp = str(tmp_path / "mylib.mn")
        assert module_prefix(fp) == "mylib__"

    def test_short_name_simple(self) -> None:
        assert module_short_name("/some/path/crypto.mn") == "crypto"

    def test_short_name_mod(self) -> None:
        assert module_short_name("/some/path/mymod/mod.mn") == "mymod"


# ---------------------------------------------------------------------------
# Dependency ordering
# ---------------------------------------------------------------------------


class TestDependencyOrder:
    """Test topological sort of module dependencies."""

    def test_single_dep(self, tmp_path: Path) -> None:
        _write_mn(
            str(tmp_path),
            "dep.mn",
            """\
            pub fn dep_fn() -> Int { return 1 }
        """,
        )
        root_path = _write_mn(
            str(tmp_path),
            "main.mn",
            """\
            import dep { dep_fn }
            fn main() { let x = dep_fn() }
        """,
        )
        with open(root_path, encoding="utf-8") as f:
            source = f.read()
        resolver = ModuleResolver()
        ast = parse(source, filename=root_path)
        from mapanare.semantic import check

        check(ast, filename=root_path, resolver=resolver)
        order = build_dependency_order(resolver, root_path, ast)
        assert len(order) == 1
        assert order[0][1].filepath.endswith("dep.mn")

    def test_chain_order(self, tmp_path: Path) -> None:
        """Dependencies should come before dependents."""
        _write_mn(
            str(tmp_path),
            "c.mn",
            """\
            pub fn fc() -> Int { return 1 }
        """,
        )
        _write_mn(
            str(tmp_path),
            "b.mn",
            """\
            import c { fc }
            pub fn fb() -> Int { return fc() }
        """,
        )
        root_path = _write_mn(
            str(tmp_path),
            "a.mn",
            """\
            import b { fb }
            fn main() { let x = fb() }
        """,
        )
        with open(root_path, encoding="utf-8") as f:
            source = f.read()
        resolver = ModuleResolver()
        ast = parse(source, filename=root_path)
        from mapanare.semantic import check

        check(ast, filename=root_path, resolver=resolver)
        order = build_dependency_order(resolver, root_path, ast)
        filepaths = [os.path.basename(fp) for fp, _ in order]
        assert filepaths.index("c.mn") < filepaths.index("b.mn")


# ---------------------------------------------------------------------------
# Incremental compilation (hash-based change detection)
# ---------------------------------------------------------------------------


class TestIncrementalCompilation:
    """Test hash-based change detection for incremental compilation."""

    def test_unchanged_module(self, tmp_path: Path) -> None:
        path = _write_mn(
            str(tmp_path),
            "stable.mn",
            """\
            pub fn stable_fn() -> Int { return 42 }
        """,
        )
        # resolve_module needs a source_file, not a directory
        dummy_source = str(tmp_path / "dummy.mn")
        resolver = ModuleResolver()
        resolver.resolve_module(["stable"], dummy_source)
        assert not resolver.has_changed(path)

    def test_changed_module(self, tmp_path: Path) -> None:
        path = _write_mn(
            str(tmp_path),
            "changing.mn",
            """\
            pub fn old_fn() -> Int { return 1 }
        """,
        )
        dummy_source = str(tmp_path / "dummy.mn")
        resolver = ModuleResolver()
        resolver.resolve_module(["changing"], dummy_source)
        # Modify the file
        with open(path, "w", encoding="utf-8") as f:
            f.write("pub fn new_fn() -> Int { return 2 }")
        assert resolver.has_changed(path)

    def test_uncached_is_changed(self, tmp_path: Path) -> None:
        path = _write_mn(str(tmp_path), "new.mn", "pub fn f() -> Int { return 1 }")
        resolver = ModuleResolver()
        assert resolver.has_changed(path)
