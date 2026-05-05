"""Tests for the v5.44.0 Ps.1 ModuleResolver search-order contract.

Locks the four-step order:

1. Source-local files (``<source_dir>/<path>.mn`` or ``mod.mn``).
2. Explicit user-provided paths (``--stdlib-path`` / ``--extra-path``).
3. Installed package roots.
4. Bundled stdlib.

Each test pits one layer against another to confirm precedence.
Falsifiability: removing the search-order branch in
``ModuleResolver.resolve_path`` for any layer fails the corresponding
"X wins over Y" test.
"""

from __future__ import annotations

import os
from pathlib import Path

from mapanare.modules import ModuleResolver
from mapanare.pkg_discovery import PackageRoot


def _write(p: Path, content: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _make_pkg_root(
    tmp_path: Path,
    *,
    package_name: str = "shared",
    import_name: str | None = None,
    version: str = "0.1.0",
    entry_content: str = "pub fn hello() -> Int { return 1 }",
    extra_files: dict[str, str] | None = None,
) -> PackageRoot:
    """Construct a fake mn_modules-style installed package root."""
    pkg_dir = tmp_path / "mn_modules" / f"{package_name}-{version}"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "mapanare.toml").write_text(
        f'[package]\nname = "{package_name}"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    entry = pkg_dir / "main.mn"
    entry.write_text(entry_content, encoding="utf-8")
    for relpath, content in (extra_files or {}).items():
        _write(pkg_dir / relpath, content)
    return PackageRoot(
        package_name=package_name,
        import_name=import_name or package_name.replace("-", "_"),
        version=version,
        root_dir=pkg_dir,
        entry_module=entry,
        source="mn_modules",
        integrity=None,
    )


# ---------------------------------------------------------------------------
# Source-local wins
# ---------------------------------------------------------------------------


def test_source_local_wins_over_package(tmp_path: Path) -> None:
    """A `shared.mn` next to the importing source must beat any
    package whose import_name is `shared`."""
    src = tmp_path / "src"
    src.mkdir()
    _write(src / "shared.mn", 'pub fn hello() -> Int { return 99 }')
    pkg = _make_pkg_root(tmp_path)

    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["shared"], str(src))
    assert found is not None
    assert os.path.normpath(found) == os.path.normpath(str(src / "shared.mn"))
    # The package import log must NOT record this resolution — source-local
    # bypassed the package layer entirely.
    assert resolver.import_log() == []


def test_source_local_wins_over_explicit(tmp_path: Path) -> None:
    """Explicit --stdlib-path is layer 2; source-local is layer 1."""
    src = tmp_path / "src"
    src.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()
    _write(src / "shared.mn", 'pub fn local() -> Int { return 1 }')
    _write(extra / "shared.mn", 'pub fn explicit() -> Int { return 2 }')

    resolver = ModuleResolver(search_paths=[str(extra)])
    found = resolver.resolve_path(["shared"], str(src))
    assert found is not None
    assert os.path.normpath(found) == os.path.normpath(str(src / "shared.mn"))


# ---------------------------------------------------------------------------
# Explicit wins over packages
# ---------------------------------------------------------------------------


def test_explicit_path_wins_over_package(tmp_path: Path) -> None:
    """--extra-path / --stdlib-path is checked before installed packages."""
    src = tmp_path / "src"
    src.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()
    _write(extra / "shared.mn", 'pub fn explicit() -> Int { return 1 }')
    pkg = _make_pkg_root(tmp_path)

    resolver = ModuleResolver(
        search_paths=[str(extra)],
        package_roots=[pkg],
    )
    found = resolver.resolve_path(["shared"], str(src))
    assert found is not None
    assert os.path.normpath(found) == os.path.normpath(str(extra / "shared.mn"))
    # Package layer must not have fired.
    assert resolver.import_log() == []


# ---------------------------------------------------------------------------
# Packages win over bundled stdlib
# ---------------------------------------------------------------------------


def test_package_wins_over_bundled_stdlib(tmp_path: Path) -> None:
    """A package with import_name `math` shadows the bundled stdlib `math`.

    This is the contract: installed packages are layered between
    explicit paths and bundled stdlib so users can override stdlib
    modules with their own packaged versions.
    """
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(
        tmp_path,
        package_name="math",
        version="9.9.9",
        entry_content='pub fn pi() -> Int { return 314 }',
    )
    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["math"], str(src))
    assert found is not None
    # Must resolve to the package, not the bundled stdlib/math.mn.
    assert os.path.normpath(found) == os.path.normpath(str(pkg.entry_module))
    # The import was logged.
    log = resolver.import_log()
    assert len(log) == 1
    assert log[0].package_name == "math"
    assert log[0].version == "9.9.9"
    assert log[0].source == "mn_modules"


def test_bundled_stdlib_still_resolves_when_no_package(tmp_path: Path) -> None:
    """Without a shadowing package, bundled stdlib still resolves."""
    src = tmp_path / "src"
    src.mkdir()
    resolver = ModuleResolver()
    # `math` is in the bundled stdlib
    found = resolver.resolve_path(["math"], str(src))
    assert found is not None
    assert "stdlib" in found
    assert found.endswith("math.mn") or found.endswith(os.path.join("math", "mod.mn"))


# ---------------------------------------------------------------------------
# Hyphen → underscore mapping (Ps.2)
# ---------------------------------------------------------------------------


def test_hyphen_to_underscore_import_name(tmp_path: Path) -> None:
    """Package `mn-foo-bar` is importable as `mn_foo_bar`."""
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(
        tmp_path,
        package_name="mn-foo-bar",
        # import_name auto-derived: hyphens → underscores
    )
    assert pkg.import_name == "mn_foo_bar"
    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["mn_foo_bar"], str(src))
    assert found is not None
    log = resolver.import_log()
    assert len(log) == 1
    assert log[0].package_name == "mn-foo-bar"
    assert log[0].import_name == "mn_foo_bar"


def test_underscore_package_no_hyphen_alternative(tmp_path: Path) -> None:
    """A package whose name is `mn_foo` (no hyphen) is the canonical
    form; there is no hyphenated alternative checked."""
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(tmp_path, package_name="mn_foo")
    assert pkg.import_name == "mn_foo"
    resolver = ModuleResolver(package_roots=[pkg])
    assert resolver.resolve_path(["mn_foo"], str(src)) is not None


# ---------------------------------------------------------------------------
# Submodule resolution within a package (Ps.2 entry-module rule)
# ---------------------------------------------------------------------------


def test_submodule_resolves_under_package_root(tmp_path: Path) -> None:
    """`import mn_collections::utils` resolves to
    `mn_modules/mn_collections-0.1.0/utils.mn`."""
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(
        tmp_path,
        package_name="mn_collections",
        extra_files={"utils.mn": "pub fn util() -> Int { return 42 }"},
    )
    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["mn_collections", "utils"], str(src))
    assert found is not None
    assert os.path.normpath(found) == os.path.normpath(str(pkg.root_dir / "utils.mn"))
    log = resolver.import_log()
    assert len(log) == 1
    assert log[0].import_path == ("mn_collections", "utils")


def test_submodule_dir_mod_mn(tmp_path: Path) -> None:
    """`import mn_collections::sub` falls through to `sub/mod.mn`."""
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(
        tmp_path,
        package_name="mn_collections",
        extra_files={"sub/mod.mn": "pub fn nested() -> Int { return 7 }"},
    )
    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["mn_collections", "sub"], str(src))
    assert found is not None
    assert found.endswith(os.path.join("sub", "mod.mn"))


def test_bare_package_import_resolves_to_entry(tmp_path: Path) -> None:
    """`import mn_collections` resolves to the package's entry module."""
    src = tmp_path / "src"
    src.mkdir()
    pkg = _make_pkg_root(tmp_path, package_name="mn_collections")
    resolver = ModuleResolver(package_roots=[pkg])
    found = resolver.resolve_path(["mn_collections"], str(src))
    assert found is not None
    assert os.path.normpath(found) == os.path.normpath(str(pkg.entry_module))


# ---------------------------------------------------------------------------
# Backward compatibility: legacy bare construction
# ---------------------------------------------------------------------------


def test_bare_constructor_unchanged_behavior(tmp_path: Path) -> None:
    """Pre-v5.44.0 callers using bare `ModuleResolver()` see no change."""
    src = tmp_path / "src"
    src.mkdir()
    _write(src / "local.mn", 'pub fn x() -> Int { return 1 }')
    resolver = ModuleResolver()
    # Source-local resolution still works.
    assert resolver.resolve_path(["local"], str(src)) is not None
    # Bundled stdlib still works.
    assert resolver.resolve_path(["math"], str(src)) is not None
    # Package roots is empty, log is empty.
    assert resolver.package_roots() == []
    assert resolver.import_log() == []


def test_search_paths_kw_unchanged_behavior(tmp_path: Path) -> None:
    """Pre-v5.44.0 callers using `search_paths=...` see no change."""
    src = tmp_path / "src"
    src.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()
    _write(extra / "ext.mn", 'pub fn x() -> Int { return 1 }')
    resolver = ModuleResolver(search_paths=[str(extra)])
    assert resolver.resolve_path(["ext"], str(src)) is not None
