"""Module resolution for the Mapanare compiler.

Resolves import paths to files, parses and caches modules, and detects
circular imports.

Search-order policy (v5.44.0+, locked by tests in tests/packages/):

1. ``self::`` prefix — relative to the source file's directory.
2. Source-local file or directory (``<source_dir>/<path>.mn`` or
   ``<source_dir>/<path>/mod.mn``).
3. Explicit user-provided search paths (``--stdlib-path`` /
   ``--extra-path`` / ``MAPANARE_PATH``).
4. Installed package roots (``PackageRoot`` records from
   ``mapanare.pkg_discovery``; v5.44.0 backed by ``mn_modules/``).
5. Bundled stdlib shipped with the compiler.

Source-local always wins; explicit overrides outrank packages;
packages outrank bundled stdlib. Order is deterministic and never
varies based on which source happens to "answer first" — each step
is checked in sequence.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from mapanare.ast_nodes import (
    AgentDef,
    Definition,
    EnumDef,
    ExportDef,
    FnDef,
    ImportDef,
    PipeDef,
    Program,
    StructDef,
    TypeAlias,
)

if TYPE_CHECKING:
    from mapanare.pkg_discovery import PackageRoot


@dataclass
class ModuleExport:
    """A single exported symbol from a module."""

    name: str
    definition: Definition
    public: bool


@dataclass
class ResolvedModule:
    """A parsed and checked module with its exports."""

    filepath: str
    program: Program
    exports: dict[str, ModuleExport] = field(default_factory=dict)
    source_hash: str = ""  # SHA-256 hex digest for change detection


@dataclass(frozen=True)
class ImportRecord:
    """Single record of a package-resolved import (Ps.4 diagnostics).

    Attributes:
        package_name: Canonical package name from the manifest.
        import_name: Name actually used in the ``import`` statement
            (post hyphen→underscore mapping).
        version: Resolved version string.
        source: Backing storage (``"mn_modules"`` in v5.44.0; reserved
            ``"path"`` / ``"git"`` / ``"global-cache"`` for the future).
        integrity: SHA-256 from the lockfile, or ``None``.
        import_path: Original dotted import path components, e.g.
            ``["mn_collections", "sorted_list"]``.
        resolved_filepath: Absolute path the import resolved to.
    """

    package_name: str
    import_name: str
    version: str
    source: str
    integrity: str | None
    import_path: tuple[str, ...]
    resolved_filepath: str


class ModuleResolutionError(Exception):
    """Raised when a module cannot be resolved."""


class ModuleResolver:
    """Resolves import paths to files and caches parsed modules.

    Maintains a module cache keyed by absolute path and a resolution stack
    for circular import detection.

    Construction is backward-compatible: every legacy call site that
    passes nothing (or only ``search_paths=...``) keeps its prior
    behavior. ``package_roots`` and the ``_import_log`` only fire when
    callers opt in via :func:`mapanare.cli._build_resolver_from_args`
    (Ps.3).
    """

    def __init__(
        self,
        search_paths: list[str] | None = None,
        *,
        package_roots: "list[PackageRoot] | None" = None,
    ) -> None:
        self._cache: dict[str, ResolvedModule] = {}
        self._resolution_stack: list[str] = []
        # Explicit user paths (--stdlib-path / --extra-path / MAPANARE_PATH).
        self._explicit_paths: list[str] = list(search_paths or [])
        # Installed package roots (v5.44.0+, Ps.1). Empty list keeps
        # legacy behavior unchanged.
        self._package_roots: list[PackageRoot] = list(package_roots or [])
        # Resolved package-import log (v5.44.0+, Ps.4).
        self._import_log: list[ImportRecord] = []
        # Auto-detect bundled stdlib (last in the search order).
        stdlib_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stdlib"
        )
        self._bundled_stdlib_dir: str | None = (
            stdlib_dir if os.path.isdir(stdlib_dir) else None
        )
        # Backward-compat view: combined explicit + bundled stdlib list.
        # No external code grep-uses this in v5.44.0 HEAD; preserved for
        # any unindexed/playground consumer.
        self._search_paths: list[str] = list(self._explicit_paths)
        if (
            self._bundled_stdlib_dir is not None
            and self._bundled_stdlib_dir not in self._search_paths
        ):
            self._search_paths.append(self._bundled_stdlib_dir)

    def resolve_path(self, import_path: list[str], source_dir: str) -> str | None:
        """Resolve an import path to a file on disk.

        Search order (locked):

        0. ``self::`` prefix: resolve relative to ``source_dir``,
           stripping the prefix.
        1. Source-local: ``<source_dir>/<path>.mn`` then
           ``<source_dir>/<path>/mod.mn``.
        2. Explicit user paths (``--stdlib-path`` / ``--extra-path``).
        3. Installed package roots (Ps.1).
        4. Bundled stdlib.

        Returns absolute path or ``None`` if not found.
        """
        # Step 0: `import self::module` — resolve relative to source_dir,
        # stripping the "self" prefix so `self::ast` resolves to
        # `<dir>/ast.mn` rather than `<dir>/self/ast.mn`.
        if import_path and import_path[0] == "self":
            remaining = import_path[1:]
            if remaining:
                rel_self = os.path.join(*remaining) + ".mn"
                candidate_self = os.path.normpath(os.path.join(source_dir, rel_self))
                if os.path.isfile(candidate_self):
                    return os.path.abspath(candidate_self)
                rel_self_dir = os.path.join(*remaining, "mod.mn")
                candidate_self_dir = os.path.normpath(os.path.join(source_dir, rel_self_dir))
                if os.path.isfile(candidate_self_dir):
                    return os.path.abspath(candidate_self_dir)

        rel = os.path.join(*import_path) + ".mn"
        rel_dir = os.path.join(*import_path, "mod.mn")

        # Step 1: source-local file, then source-local mod.mn.
        candidate = os.path.normpath(os.path.join(source_dir, rel))
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
        candidate_dir = os.path.normpath(os.path.join(source_dir, rel_dir))
        if os.path.isfile(candidate_dir):
            return os.path.abspath(candidate_dir)

        # Step 2: explicit user-provided search paths.
        for search_dir in self._explicit_paths:
            candidate = os.path.normpath(os.path.join(search_dir, rel))
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            candidate_dir = os.path.normpath(os.path.join(search_dir, rel_dir))
            if os.path.isfile(candidate_dir):
                return os.path.abspath(candidate_dir)

        # Step 3: installed package roots (Ps.1). The first path component
        # is matched against each PackageRoot's import_name; the remainder
        # resolves relative to the package's root_dir.
        if import_path and self._package_roots:
            head = import_path[0]
            for pkg in self._package_roots:
                if pkg.import_name != head:
                    continue
                resolved = self._resolve_in_package(pkg, import_path)
                if resolved is not None:
                    return resolved
                # Same import_name on multiple packages would be ambiguous;
                # discovery already errors on duplicates, so the first
                # match is the only match.

        # Step 4: bundled stdlib (last).
        if self._bundled_stdlib_dir is not None:
            candidate = os.path.normpath(os.path.join(self._bundled_stdlib_dir, rel))
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            candidate_dir = os.path.normpath(os.path.join(self._bundled_stdlib_dir, rel_dir))
            if os.path.isfile(candidate_dir):
                return os.path.abspath(candidate_dir)

        return None

    def _resolve_in_package(
        self, pkg: "PackageRoot", import_path: list[str]
    ) -> str | None:
        """Resolve an ``import_path`` whose head matches ``pkg.import_name``.

        Records the resolution in ``_import_log`` (Ps.4) on success.
        """
        remaining = import_path[1:]
        resolved: str | None = None
        if not remaining:
            # Bare `import <pkg>` resolves to the package entry module.
            resolved = os.path.abspath(str(pkg.entry_module))
        else:
            rel = os.path.join(*remaining) + ".mn"
            candidate = os.path.normpath(os.path.join(str(pkg.root_dir), rel))
            if os.path.isfile(candidate):
                resolved = os.path.abspath(candidate)
            else:
                rel_dir = os.path.join(*remaining, "mod.mn")
                candidate_dir = os.path.normpath(os.path.join(str(pkg.root_dir), rel_dir))
                if os.path.isfile(candidate_dir):
                    resolved = os.path.abspath(candidate_dir)

        if resolved is not None:
            self._import_log.append(
                ImportRecord(
                    package_name=pkg.package_name,
                    import_name=pkg.import_name,
                    version=pkg.version,
                    source=pkg.source,
                    integrity=pkg.integrity,
                    import_path=tuple(import_path),
                    resolved_filepath=resolved,
                )
            )
        return resolved

    def import_log(self) -> list[ImportRecord]:
        """Return the package-import log (Ps.4 diagnostics surface)."""
        return list(self._import_log)

    def package_roots(self) -> "list[PackageRoot]":
        """Return the installed package roots this resolver was built with."""
        return list(self._package_roots)

    def resolve_module(
        self,
        import_path: list[str],
        source_file: str,
    ) -> ResolvedModule:
        """Resolve, parse, and cache a module.

        Args:
            import_path: Module path components (e.g. ["utils", "helpers"]).
            source_file: Absolute path of the file containing the import.

        Returns:
            The resolved module with its public exports.

        Raises:
            ModuleResolutionError: If module not found or circular import.
        """
        source_dir = os.path.dirname(os.path.abspath(source_file))
        filepath = self.resolve_path(import_path, source_dir)

        if filepath is None:
            mod_name = "::".join(import_path)
            search1 = os.path.join(source_dir, os.path.join(*import_path) + ".mn")
            search2 = os.path.join(source_dir, os.path.join(*import_path, "mod.mn"))
            raise ModuleResolutionError(
                f"module '{mod_name}' not found (searched: {search1}, {search2})"
            )

        # Check cache
        if filepath in self._cache:
            return self._cache[filepath]

        # Check for circular imports
        if filepath in self._resolution_stack:
            cycle = self._resolution_stack[self._resolution_stack.index(filepath) :]
            cycle.append(filepath)
            chain = " -> ".join(os.path.basename(f) for f in cycle)
            raise ModuleResolutionError(f"circular import detected: {chain}")

        # Parse and check the module
        self._resolution_stack.append(filepath)
        try:
            module = self._load_module(filepath)
            self._cache[filepath] = module
            return module
        finally:
            self._resolution_stack.pop()

    def _load_module(self, filepath: str) -> ResolvedModule:
        """Parse a module file, resolve its imports, and extract its exports."""
        from mapanare.parser import parse

        with open(filepath, encoding="utf-8") as f:
            source = f.read()

        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()

        program = parse(source, filename=filepath)

        # Recursively resolve any imports in this module
        for defn in program.definitions:
            if isinstance(defn, ImportDef):
                self.resolve_module(defn.path, filepath)

        # Extract exports
        exports: dict[str, ModuleExport] = {}
        for defn in program.definitions:
            self._collect_exports(defn, exports)

        return ResolvedModule(
            filepath=filepath, program=program, exports=exports, source_hash=source_hash
        )

    def _collect_exports(self, defn: Definition, exports: dict[str, ModuleExport]) -> None:
        """Collect exported symbols from a definition."""
        if isinstance(defn, FnDef):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, AgentDef):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, StructDef):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, EnumDef):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, PipeDef):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, TypeAlias):
            exports[defn.name] = ModuleExport(name=defn.name, definition=defn, public=defn.public)
        elif isinstance(defn, ExportDef):
            # `export fn foo() ...` — the inner definition is public
            if defn.definition:
                # Mark the inner def as public
                if hasattr(defn.definition, "public"):
                    object.__setattr__(defn.definition, "public", True)
                self._collect_exports(defn.definition, exports)
            # `export { name1, name2 }` — re-export by name
            for name in defn.names:
                if name in exports:
                    exports[name] = ModuleExport(
                        name=name, definition=exports[name].definition, public=True
                    )
        elif isinstance(defn, ImportDef):
            pass  # imports are not re-exported

    def get_cached(self, filepath: str) -> ResolvedModule | None:
        """Get a cached module by absolute filepath."""
        return self._cache.get(filepath)

    def is_cached(self, filepath: str) -> bool:
        """Check if a module is already cached."""
        return filepath in self._cache

    def has_changed(self, filepath: str) -> bool:
        """Check if a cached module's source file has changed on disk.

        Returns True if the file's content hash differs from the cached hash,
        or if the file is not cached. Used for incremental compilation.
        """
        abs_path = os.path.abspath(filepath)
        cached = self._cache.get(abs_path)
        if cached is None:
            return True
        if not os.path.isfile(abs_path):
            return True
        with open(abs_path, encoding="utf-8") as f:
            current_hash = hashlib.sha256(f.read().encode("utf-8")).hexdigest()
        return current_hash != cached.source_hash

    def all_modules(self) -> list[tuple[str, ResolvedModule]]:
        """Return all cached modules as (filepath, module) pairs."""
        return list(self._cache.items())
