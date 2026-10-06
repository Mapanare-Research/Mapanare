"""Package-root discovery for the Mapanare compiler (v5.44.0+, Ps.1).

Bridges ``stdlib/pkg.py`` (manifest / lockfile / ``mn_modules`` install
layout) and ``mapanare/modules.py`` (import resolution). The compiler
does not scan ``mn_modules/`` directly; it consumes ``PackageRoot``
records produced here.

This boundary is deliberate. It keeps storage assumptions in one
place so a future global content-addressed package cache can back
``PackageRoot`` records without touching resolver call sites or the
CLI entry points.

Search-order policy (locked by ``ModuleResolver`` and tested):

1. Source-local files (``<source_dir>/<path>.mn`` or ``mod.mn``).
2. Explicit user-provided paths (``--stdlib-path`` / ``--extra-path``).
3. Installed package roots (this module's records).
4. Bundled stdlib shipped with the compiler.

Lockfile policy:

* If ``mapanare.lock`` exists in ``project_dir``, it is authoritative.
  The discovery scan is keyed off the lock; a missing install dir
  raises ``PackageDiscoveryError`` with "run mnc install" rather than
  silently falling back to a different version.
* If no lockfile exists, ``mn_modules/`` is scanned alphabetically.
  Multiple installed versions of the same package raise
  ``PackageDiscoveryError`` (ambiguous). One version per package is
  the v5.44.0 contract.

The compiler MUST NOT scan a global cache opportunistically. Roots
sourced from a global cache (when one exists) MUST come through this
helper after manifest / lockfile selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from collections.abc import Callable

    from mapanare.modules import ModuleResolver


@dataclass(frozen=True)
class PackageRoot:
    """A single installed package root visible to the compiler.

    Attributes:
        package_name: Canonical package name (may contain hyphens),
            as declared in the package's ``mapanare.toml``.
        import_name: Name used in ``import`` statements. Hyphens in
            ``package_name`` are mapped to underscores per the v0
            rule (Ps.2).
        version: Resolved version string from the lockfile, or the
            version declared in the installed package's
            ``mapanare.toml`` when there is no lockfile.
        root_dir: Directory containing the package's source tree
            (e.g. ``<project>/mn_modules/<name>-<version>/``).
        entry_module: Entry-point ``.mn`` file. ``mod.mn`` if present,
            otherwise ``main.mn``.
        source: Backing storage for this root. v5.44.0 ships only
            ``"mn_modules"``. Reserved literals for forward
            compatibility: ``"path"``, ``"git"``, ``"global-cache"``.
        integrity: SHA-256 integrity hash from the lockfile when
            available; ``None`` when discovered via directory scan.
    """

    package_name: str
    import_name: str
    version: str
    root_dir: Path
    entry_module: Path
    source: str
    integrity: Optional[str] = None


class PackageDiscoveryError(Exception):
    """Raised when package discovery cannot complete."""


def package_name_to_import_name(name: str) -> str:
    """Map a package name to an import name (Ps.2).

    Hyphens in package names are mapped to underscores. ``mn-foo``
    becomes ``mn_foo``; ``mn_foo`` is unchanged. This is the only
    canonicalization applied.
    """
    return name.replace("-", "_")


def find_project_dir(source_path: Path | str) -> Optional[Path]:
    """Walk up from ``source_path`` looking for ``mapanare.toml``.

    Returns the directory containing ``mapanare.toml`` (the project
    root), or ``None`` if no project root is found before reaching
    the filesystem root. Used to bound package discovery to the
    enclosing project.
    """
    cur = Path(source_path).resolve()
    if cur.is_file():
        cur = cur.parent
    while True:
        if (cur / "mapanare.toml").is_file():
            return cur
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def _entry_module(pkg_dir: Path) -> Optional[Path]:
    """Pick the package entry module: ``mod.mn`` if present, else
    ``main.mn``. Returns ``None`` if neither exists."""
    for candidate in ("mod.mn", "main.mn"):
        p = pkg_dir / candidate
        if p.is_file():
            return p
    return None


def _candidate_install_dirs(packages_dir: Path, name: str, version: str) -> list[Path]:
    """All plausible install-dir layouts for ``name@version``.

    The installer writes:

    * ``<packages_dir>/<name>-<version>/`` for explicit-version installs;
    * ``<packages_dir>/<name>-latest/`` for git installs with no version;
    * ``<packages_dir>/<name>/`` is also accepted defensively (no
      installer currently writes this shape, but path/git overrides may).
    """
    return [
        packages_dir / f"{name}-{version}",
        packages_dir / f"{name}-latest",
        packages_dir / name,
    ]


def discover_package_roots(
    project_dir: Optional[Path | str],
    *,
    use_lockfile: bool = True,
) -> list[PackageRoot]:
    """Discover installed package roots for a project.

    Args:
        project_dir: Project root containing ``mapanare.toml``. Pass
            ``None`` (e.g. when compiling a standalone ``.mn`` outside
            a project) to get an empty list.
        use_lockfile: When ``True`` and ``mapanare.lock`` exists,
            build the package list from the lock entries (lockfile is
            authoritative). When ``False`` or no lockfile is present,
            scan ``mn_modules/`` alphabetically.

    Returns:
        List of ``PackageRoot`` records. Empty when the project has
        no installed packages.

    Raises:
        PackageDiscoveryError: When the lockfile names a package whose
            install directory is missing, when an installed package
            has no entry module, or when ``mn_modules/`` (no lockfile
            mode) contains multiple versions of the same package.
    """
    if project_dir is None:
        return []
    project_dir = Path(project_dir)
    if not project_dir.is_dir():
        return []

    # Late import: stdlib/pkg.py is heavy and not needed at
    # ModuleResolver import time.
    from stdlib.pkg import (
        MAPANARE_PACKAGES_DIR,
        ManifestError,
        load_lockfile,
        load_manifest,
    )

    packages_dir = project_dir / MAPANARE_PACKAGES_DIR
    if not packages_dir.is_dir():
        return []

    lockfile_path = project_dir / "mapanare.lock"
    if use_lockfile and lockfile_path.is_file():
        return _roots_from_lockfile(
            project_dir,
            packages_dir,
            load_lockfile,
        )

    return _roots_from_scan(packages_dir, load_manifest, ManifestError)


def _roots_from_lockfile(
    project_dir: Path,
    packages_dir: Path,
    load_lockfile_fn: "Callable[..., Any]",
) -> list[PackageRoot]:
    """Build PackageRoot list from ``mapanare.lock`` (authoritative)."""
    lockfile = load_lockfile_fn(str(project_dir))
    roots: list[PackageRoot] = []
    for locked in lockfile.packages:
        candidates = _candidate_install_dirs(packages_dir, locked.name, locked.version)
        installed_dir = next((d for d in candidates if d.is_dir()), None)
        if installed_dir is None:
            tried = ", ".join(str(c.relative_to(project_dir)) for c in candidates)
            raise PackageDiscoveryError(
                f"package '{locked.name}@{locked.version}' is locked but "
                f"not installed (tried: {tried}). Run: mnc install"
            )
        entry = _entry_module(installed_dir)
        if entry is None:
            raise PackageDiscoveryError(
                f"package '{locked.name}@{locked.version}' has no "
                f"entry module (expected mod.mn or main.mn under "
                f"{installed_dir})"
            )
        roots.append(
            PackageRoot(
                package_name=locked.name,
                import_name=package_name_to_import_name(locked.name),
                version=locked.version,
                root_dir=installed_dir,
                entry_module=entry,
                source="mn_modules",
                integrity=locked.integrity or None,
            )
        )
    return roots


def _roots_from_scan(
    packages_dir: Path,
    load_manifest_fn: "Callable[..., Any]",
    manifest_error_cls: type[Exception],
) -> list[PackageRoot]:
    """Scan ``mn_modules/`` alphabetically (no-lockfile mode).

    Each candidate directory's own ``mapanare.toml`` is the source
    of truth for ``(name, version)``. Falls back to dir-name parsing
    only when the manifest is missing or malformed.

    Multiple installed versions of the same package raise
    ``PackageDiscoveryError``.
    """
    by_name: dict[str, list[tuple[str, Path]]] = {}
    for entry in sorted(packages_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            manifest = load_manifest_fn(str(entry))
            pkg_name = manifest.name
            version = manifest.version
        except (manifest_error_cls, FileNotFoundError, OSError):
            # Fall back to dirname parsing on the LAST hyphen.
            name_version = entry.name
            if "-" in name_version:
                last = name_version.rfind("-")
                pkg_name = name_version[:last]
                version = name_version[last + 1 :]
            else:
                pkg_name = name_version
                version = "0.0.0"
        by_name.setdefault(pkg_name, []).append((version, entry))

    roots: list[PackageRoot] = []
    for pkg_name, candidates in sorted(by_name.items()):
        if len(candidates) > 1:
            versions = ", ".join(sorted(v for v, _ in candidates))
            raise PackageDiscoveryError(
                f"multiple installed versions of package '{pkg_name}' "
                f"({versions}); add a mapanare.lock or remove duplicates"
            )
        version, installed_dir = candidates[0]
        entry_mod = _entry_module(installed_dir)
        if entry_mod is None:
            # Skip silently in scan mode — a junk dir without
            # mod.mn / main.mn is not a valid package import.
            continue
        roots.append(
            PackageRoot(
                package_name=pkg_name,
                import_name=package_name_to_import_name(pkg_name),
                version=version,
                root_dir=installed_dir,
                entry_module=entry_mod,
                source="mn_modules",
                integrity=None,
            )
        )
    return roots


def build_resolver_for_source(
    source_path: Optional[str | Path],
    *,
    explicit_paths: Optional[list[str]] = None,
) -> "ModuleResolver":
    """Construct a package-aware ``ModuleResolver`` from a source path.

    Lower-level primitive used by both the CLI (``_build_resolver_from_args``)
    and the LSP backend. Walks up from ``source_path`` to find an enclosing
    project, discovers installed package roots, and constructs the resolver.

    Caller handles ``PackageDiscoveryError``: the CLI surfaces the error
    and exits; the LSP swallows it and falls back to bare resolution.
    """
    # Local import to avoid a hard pkg_discovery → modules cycle.
    from mapanare.modules import ModuleResolver

    explicit = list(explicit_paths or [])
    project_dir = find_project_dir(source_path) if source_path else None
    package_roots: list[PackageRoot] = []
    if project_dir is not None:
        package_roots = discover_package_roots(project_dir)
    return ModuleResolver(
        search_paths=explicit or None,
        package_roots=package_roots or None,
    )
