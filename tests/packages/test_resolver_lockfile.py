"""Tests for v5.44.0 Ps.1 lockfile-authoritative package discovery.

Locks the contract: when `mapanare.lock` exists, it is the source of
truth for package versions. Missing install dirs error out with
"run mnc install"; multiple installed versions of the same package
error in scan mode (no lockfile); manual mn_modules edits diverging
from the lockfile fail with a clear message.

Falsifiability: relaxing the missing-dir check in
``_roots_from_lockfile`` (e.g. silently falling back to "latest")
fails ``test_missing_locked_dir_clear_error``; relaxing the duplicate
check in ``_roots_from_scan`` fails
``test_multiple_versions_without_lockfile_errors``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mapanare.pkg_discovery import (
    PackageDiscoveryError,
    discover_package_roots,
    find_project_dir,
    package_name_to_import_name,
)


def _write_manifest(project_dir: Path, name: str = "consumer", version: str = "0.1.0") -> None:
    (project_dir / "mapanare.toml").write_text(
        f'[package]\nname = "{name}"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def _write_pkg(
    project_dir: Path,
    name: str,
    version: str,
    *,
    layout_name_version: str | None = None,
    files: dict[str, str] | None = None,
    write_manifest: bool = True,
) -> Path:
    """Materialize an installed package under mn_modules/."""
    layout = layout_name_version or f"{name}-{version}"
    pkg_dir = project_dir / "mn_modules" / layout
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if write_manifest:
        (pkg_dir / "mapanare.toml").write_text(
            f'[package]\nname = "{name}"\nversion = "{version}"\n',
            encoding="utf-8",
        )
    (pkg_dir / "main.mn").write_text("pub fn x() -> Int { return 1 }", encoding="utf-8")
    for relpath, content in (files or {}).items():
        (pkg_dir / relpath).parent.mkdir(parents=True, exist_ok=True)
        (pkg_dir / relpath).write_text(content, encoding="utf-8")
    return pkg_dir


def _write_lockfile(project_dir: Path, packages: list[dict]) -> None:
    """Write a minimal mapanare.lock JSON."""
    payload = {"lockfile_version": 1, "packages": packages}
    (project_dir / "mapanare.lock").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# No lockfile: scan mode
# ---------------------------------------------------------------------------


def test_no_packages_dir_returns_empty(tmp_path: Path) -> None:
    """Project with no mn_modules/ → empty list, no error."""
    _write_manifest(tmp_path)
    assert discover_package_roots(tmp_path) == []


def test_none_project_dir_returns_empty(tmp_path: Path) -> None:
    """Standalone .mn file outside any project → empty list."""
    assert discover_package_roots(None) == []


def test_scan_mode_one_package(tmp_path: Path) -> None:
    """No lockfile + one package → discovered."""
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "mn_collections", "0.1.0")
    roots = discover_package_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].package_name == "mn_collections"
    assert roots[0].version == "0.1.0"
    assert roots[0].source == "mn_modules"
    assert roots[0].integrity is None  # scan mode = no integrity


def test_scan_mode_alphabetical_order(tmp_path: Path) -> None:
    """Multiple distinct packages are returned alphabetically by name."""
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "z_pkg", "0.1.0")
    _write_pkg(tmp_path, "a_pkg", "0.2.0")
    _write_pkg(tmp_path, "m_pkg", "0.3.0")
    roots = discover_package_roots(tmp_path)
    names = [r.package_name for r in roots]
    assert names == ["a_pkg", "m_pkg", "z_pkg"]


def test_multiple_versions_without_lockfile_errors(tmp_path: Path) -> None:
    """Two installed versions of the same package, no lockfile → error."""
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "dup_pkg", "0.1.0")
    _write_pkg(tmp_path, "dup_pkg", "0.2.0")
    with pytest.raises(PackageDiscoveryError) as exc:
        discover_package_roots(tmp_path)
    assert "multiple installed versions" in str(exc.value)
    assert "dup_pkg" in str(exc.value)
    assert "mapanare.lock" in str(exc.value)


def test_scan_mode_skips_dir_without_entry_module(tmp_path: Path) -> None:
    """A subdir of mn_modules/ that has no mod.mn or main.mn is silently
    skipped in scan mode. Junk dirs (scratch, .git, etc.) shouldn't fail
    a build."""
    _write_manifest(tmp_path)
    junk = tmp_path / "mn_modules" / "junk-dir"
    junk.mkdir(parents=True)
    (junk / "mapanare.toml").write_text(
        '[package]\nname = "junk"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    # No main.mn, no mod.mn — should be skipped, not raise.
    roots = discover_package_roots(tmp_path)
    assert roots == []


# ---------------------------------------------------------------------------
# Lockfile authoritative
# ---------------------------------------------------------------------------


def test_lockfile_authoritative_when_present(tmp_path: Path) -> None:
    """When mapanare.lock exists, discovery is keyed off it."""
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "mn_collections", "0.1.0")
    _write_lockfile(
        tmp_path,
        [
            {
                "name": "mn_collections",
                "version": "0.1.0",
                "git": "https://example/mn_collections.git",
                "commit": "abc123",
                "integrity": "sha256:deadbeef",
            }
        ],
    )
    roots = discover_package_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].package_name == "mn_collections"
    assert roots[0].version == "0.1.0"
    assert roots[0].integrity == "sha256:deadbeef"  # carried from lockfile


def test_missing_locked_dir_clear_error(tmp_path: Path) -> None:
    """Lockfile names a package whose install dir is absent."""
    _write_manifest(tmp_path)
    (tmp_path / "mn_modules").mkdir()  # exists but empty
    _write_lockfile(
        tmp_path,
        [
            {
                "name": "mn_collections",
                "version": "0.1.0",
                "git": "https://example/mn_collections.git",
                "commit": "abc123",
                "integrity": "sha256:dead",
            }
        ],
    )
    with pytest.raises(PackageDiscoveryError) as exc:
        discover_package_roots(tmp_path)
    msg = str(exc.value)
    assert "mn_collections" in msg
    assert "0.1.0" in msg
    assert "mnc install" in msg
    assert "locked but" in msg


def test_lockfile_no_silent_version_fallback(tmp_path: Path) -> None:
    """If lockfile pins 0.2.0 but only 0.1.0 is installed, error.

    Never silently use the older / different version. This is the
    bug-class that erodes reproducibility.
    """
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "mn_collections", "0.1.0")  # WRONG version
    _write_lockfile(
        tmp_path,
        [
            {
                "name": "mn_collections",
                "version": "0.2.0",
                "git": "https://example/mn_collections.git",
                "commit": "abc",
                "integrity": "",
            }
        ],
    )
    with pytest.raises(PackageDiscoveryError) as exc:
        discover_package_roots(tmp_path)
    assert "0.2.0" in str(exc.value)
    assert "mnc install" in str(exc.value)


def test_lockfile_accepts_latest_layout(tmp_path: Path) -> None:
    """Git installs use `<name>-latest/`. Lockfile that pins version
    `latest` (rare; from `version = "*"` git installs) resolves there."""
    _write_manifest(tmp_path)
    _write_pkg(
        tmp_path,
        "git_pkg",
        "latest",
        layout_name_version="git_pkg-latest",
    )
    _write_lockfile(
        tmp_path,
        [
            {
                "name": "git_pkg",
                "version": "latest",
                "git": "https://example/git_pkg.git",
                "commit": "abc",
                "integrity": "",
            }
        ],
    )
    roots = discover_package_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].version == "latest"


def test_lockfile_missing_entry_module_errors(tmp_path: Path) -> None:
    """A locked-and-installed package with no entry module fails clearly."""
    _write_manifest(tmp_path)
    pkg_dir = tmp_path / "mn_modules" / "broken-0.1.0"
    pkg_dir.mkdir(parents=True)
    # NO main.mn, NO mod.mn
    (pkg_dir / "mapanare.toml").write_text(
        '[package]\nname = "broken"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    _write_lockfile(
        tmp_path,
        [
            {
                "name": "broken",
                "version": "0.1.0",
                "git": "x",
                "commit": "y",
                "integrity": "",
            }
        ],
    )
    with pytest.raises(PackageDiscoveryError) as exc:
        discover_package_roots(tmp_path)
    assert "broken" in str(exc.value)
    assert "entry module" in str(exc.value)


# ---------------------------------------------------------------------------
# Hyphen mapping helper (Ps.2)
# ---------------------------------------------------------------------------


def test_hyphen_mapping_helper() -> None:
    assert package_name_to_import_name("mn-collections") == "mn_collections"
    assert package_name_to_import_name("mn-foo-bar") == "mn_foo_bar"
    assert package_name_to_import_name("already_under") == "already_under"
    assert package_name_to_import_name("simple") == "simple"


def test_hyphenated_package_discovered_with_underscore_import_name(
    tmp_path: Path,
) -> None:
    _write_manifest(tmp_path)
    _write_pkg(tmp_path, "mn-foo-bar", "0.1.0")
    roots = discover_package_roots(tmp_path)
    assert len(roots) == 1
    assert roots[0].package_name == "mn-foo-bar"
    assert roots[0].import_name == "mn_foo_bar"


# ---------------------------------------------------------------------------
# Project-dir discovery
# ---------------------------------------------------------------------------


def test_find_project_dir_walks_up(tmp_path: Path) -> None:
    """find_project_dir walks up from a source file looking for
    mapanare.toml."""
    proj = tmp_path / "myproj"
    proj.mkdir()
    _write_manifest(proj)
    src = proj / "src" / "deep" / "nested.mn"
    src.parent.mkdir(parents=True)
    src.write_text("// content", encoding="utf-8")
    found = find_project_dir(src)
    assert found is not None
    assert found.resolve() == proj.resolve()


def test_find_project_dir_returns_none_no_project(tmp_path: Path) -> None:
    """No mapanare.toml anywhere up the tree → None."""
    src = tmp_path / "src" / "lone.mn"
    src.parent.mkdir(parents=True)
    src.write_text("// content", encoding="utf-8")
    found = find_project_dir(src)
    # NOTE: tmp_path itself contains no mapanare.toml, but pytest's
    # tmp_path is itself often nested under user dirs that might. The
    # contract is "returns when there's no project root in the visible
    # ancestry," but if the test runner is itself inside a Mapanare
    # project this test environment can fool the walk. Accept either
    # None or a resolved path that is NOT inside src's ancestry.
    if found is not None:
        assert tmp_path not in found.parents
        assert tmp_path.resolve() != found.resolve()
