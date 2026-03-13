"""Module resolution for the Mapanare compiler.

Resolves import paths to files, parses and caches modules, and detects
circular imports.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field

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


class ModuleResolutionError(Exception):
    """Raised when a module cannot be resolved."""


class ModuleResolver:
    """Resolves import paths to files and caches parsed modules.

    Maintains a module cache keyed by absolute path and a resolution stack
    for circular import detection.
    """

    def __init__(self, search_paths: list[str] | None = None) -> None:
        self._cache: dict[str, ResolvedModule] = {}
        self._resolution_stack: list[str] = []
        self._search_paths = search_paths or []
        # Auto-add the stdlib directory if it exists
        stdlib_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stdlib"
        )
        if os.path.isdir(stdlib_dir) and stdlib_dir not in self._search_paths:
            self._search_paths.append(stdlib_dir)

    def resolve_path(self, import_path: list[str], source_dir: str) -> str | None:
        """Resolve an import path to a file on disk.

        Search order:
        0. Handle ``self::`` prefix: resolve relative to source_dir directly
        1. <source_dir>/<path>.mn
        2. <source_dir>/<path>/mod.mn
        3. Each search path (stdlib, etc.)

        Returns absolute path or None if not found.
        """
        # Handle `import self::module` — resolve relative to source_dir,
        # stripping the "self" prefix so `self::ast` resolves to `<dir>/ast.mn`
        # rather than `<dir>/self/ast.mn`.
        if import_path and import_path[0] == "self":
            remaining = import_path[1:]
            if remaining:
                rel_self = os.path.join(*remaining) + ".mn"
                candidate_self = os.path.normpath(os.path.join(source_dir, rel_self))
                if os.path.isfile(candidate_self):
                    return os.path.abspath(candidate_self)
                # Try directory module
                rel_self_dir = os.path.join(*remaining, "mod.mn")
                candidate_self_dir = os.path.normpath(os.path.join(source_dir, rel_self_dir))
                if os.path.isfile(candidate_self_dir):
                    return os.path.abspath(candidate_self_dir)

        rel = os.path.join(*import_path) + ".mn"
        candidate = os.path.normpath(os.path.join(source_dir, rel))
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

        # Try directory module
        rel_dir = os.path.join(*import_path, "mod.mn")
        candidate_dir = os.path.normpath(os.path.join(source_dir, rel_dir))
        if os.path.isfile(candidate_dir):
            return os.path.abspath(candidate_dir)

        # Search additional paths
        for search_dir in self._search_paths:
            candidate = os.path.normpath(os.path.join(search_dir, rel))
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            candidate_dir = os.path.normpath(os.path.join(search_dir, rel_dir))
            if os.path.isfile(candidate_dir):
                return os.path.abspath(candidate_dir)

        return None

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
