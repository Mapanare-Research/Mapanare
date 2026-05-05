"""Tests for the v5.44.0 Ps.1 local-storage / shared-storage boundary.

Locks a load-bearing architectural invariant:

    The compiler MUST NOT scan a global / user-wide cache directory
    opportunistically. Any future global cache must produce
    `PackageRoot` records selected by the project's manifest/lock,
    not by "happens to exist on disk."

Today there is no global cache; this test prevents accidentally
introducing one in the resolver. If a future release adds global-cache
support, the implementation must:

  1. Add a new `source` literal to PackageRoot (e.g., "global-cache").
  2. Add the lookup logic to `discover_package_roots` keyed by lockfile
     entries, not by a directory scan.
  3. Update this test to reflect the project-scoped selection.

Falsifiability: introducing a `for d in
~/.mapanare/cache/`` style scan in `ModuleResolver` or
`discover_package_roots` will fail this test, because a fake user-wide
cache populated with a matching package will then produce an import
that should have been a not-found.
"""

from __future__ import annotations

from pathlib import Path

from mapanare.modules import ModuleResolver
from mapanare.pkg_discovery import discover_package_roots


def test_resolver_does_not_scan_user_cache(tmp_path: Path, monkeypatch) -> None:
    """A user-wide cache directory containing a matching package must
    NOT be searched without explicit project-level selection."""
    # Set up a fake user-wide cache that LOOKS like it could be a
    # global package store. A future global-cache implementation might
    # default to ~/.mapanare/cache/. We populate it with a `secret_pkg`
    # the project never declared.
    fake_user_cache = tmp_path / "fake_user_cache"
    fake_pkg = fake_user_cache / "secret_pkg-1.0.0"
    fake_pkg.mkdir(parents=True)
    (fake_pkg / "mapanare.toml").write_text(
        '[package]\nname = "secret_pkg"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    (fake_pkg / "main.mn").write_text(
        'pub fn leak() -> Int { return 999 }\n', encoding="utf-8"
    )

    # Set every plausible env var the future cache might honor.
    monkeypatch.setenv("HOME", str(tmp_path / "fake_home"))
    monkeypatch.setenv("MAPANARE_CACHE_DIR", str(fake_user_cache))
    monkeypatch.setenv("XDG_CACHE_HOME", str(fake_user_cache))

    # A project that has NO mn_modules/ and no manifest pointing at
    # secret_pkg.
    project = tmp_path / "project"
    project.mkdir()
    (project / "mapanare.toml").write_text(
        '[package]\nname = "honest"\nversion = "0.1.0"\n', encoding="utf-8"
    )

    # Discovery must NOT pick up secret_pkg from anywhere.
    roots = discover_package_roots(project)
    names = [r.package_name for r in roots]
    assert "secret_pkg" not in names, (
        "discover_package_roots leaked a package from a user-wide cache; "
        "global storage must be selected via mapanare.toml/lock, never "
        "scanned opportunistically"
    )


def test_resolver_construction_does_not_inject_packages_from_env(
    tmp_path: Path, monkeypatch
) -> None:
    """ModuleResolver constructed bare must have an empty package_roots
    list regardless of MAPANARE_CACHE_DIR / HOME / XDG env vars."""
    monkeypatch.setenv("MAPANARE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg_cache"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    resolver = ModuleResolver()
    assert resolver.package_roots() == [], (
        "bare ModuleResolver() must NOT populate package_roots from env vars"
    )
    assert resolver.import_log() == []


def test_resolve_path_does_not_consult_unknown_directories(
    tmp_path: Path,
) -> None:
    """A package matching by name in an undeclared directory must not
    resolve."""
    src = tmp_path / "src"
    src.mkdir()
    # Random orphan directory: looks like an installed package but is
    # not declared in any project manifest, lockfile, or PackageRoot
    # passed to the resolver.
    orphan = tmp_path / "orphan_dir" / "orphan_pkg-0.1.0"
    orphan.mkdir(parents=True)
    (orphan / "main.mn").write_text(
        'pub fn x() -> Int { return 1 }\n', encoding="utf-8"
    )

    resolver = ModuleResolver()  # no package_roots passed
    found = resolver.resolve_path(["orphan_pkg"], str(src))
    assert found is None, (
        "resolver found a package in an undeclared directory — packages "
        "must only resolve through explicit PackageRoot records"
    )
