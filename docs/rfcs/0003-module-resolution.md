# RFC 0003: Module Resolution

- **Status:** Accepted
- **Phase:** v0.3.0 / Phase 2.2
- **Author:** Mapanare team
- **Date:** 2026-03-10

## Summary

Implement file-based module resolution so that `import` statements actually
locate, parse, and type-check external `.mn` files. Add `pub` visibility
enforcement so only public symbols are accessible to importers. Detect
circular imports with a clear error message.

## Motivation

Imports currently parse syntactically but do not resolve. The semantic checker
registers imported names as `UNKNOWN_TYPE` without loading any external file.
The LLVM backend silently ignores imports. Without working module resolution,
multi-file programs are impossible and no ecosystem can form.

This was cited as a critical issue by 5 of 7 reviewers of v0.2.0.

## Design

### 1. Module Path Resolution

A module path maps to a file on disk relative to the importing file's directory:

```
import math          → math.mn       (sibling file)
import utils::helpers → utils/helpers.mn  (nested directory)
```

The `::` separator maps to `/` in the filesystem.

Search order for `import foo::bar`:
1. `<source_dir>/foo/bar.mn` — relative to the importing file
2. `<source_dir>/foo/bar/mod.mn` — directory module (like Rust)
3. `<project_root>/stdlib/foo/bar.mn` — standard library (future)

If none found, emit a semantic error: `module 'foo::bar' not found`.

### 2. Visibility: `pub` Modifier

The `pub` keyword already exists in the grammar for `fn`, `agent`, `struct`,
`enum`, and `pipe` definitions. The AST nodes already have a `public: bool`
field.

**Rule:** When importing from another module, only definitions marked `pub`
are visible. Attempting to use a non-public symbol from an imported module
produces a semantic error.

Within the same file, all definitions are visible regardless of `pub`.

### 3. Module Loading and Caching

The compiler driver (new `mapanare/modules.py`) maintains:
- A **module cache** keyed by absolute file path, so each module is parsed
  and checked at most once.
- A **resolution stack** tracking which modules are currently being resolved,
  to detect circular imports.

Flow:
1. Parse the root source file
2. For each `ImportDef`, resolve the file path
3. If already cached, reuse the cached module
4. If currently on the resolution stack, emit circular import error
5. Otherwise, parse + check the imported module (recursively)
6. Merge the imported module's public symbols into the importer's scope

### 4. Semantic Integration

The `SemanticChecker` accepts an optional `ModuleResolver` that handles
file-based resolution. When checking an `ImportDef`:

1. Call `resolver.resolve(import_path, current_file)` to get the module
2. For selective imports (`import foo { bar, baz }`):
   - Check that each name exists in the module's exports
   - Check that each name is `pub`
   - Register each name in the current scope with its resolved type
3. For full imports (`import foo`):
   - Register a module symbol so `foo::item` namespace access works
   - Only `pub` items from `foo` are accessible

### 5. Transitive Imports

If module A imports module B, and B imports module C, then:
- A sees B's public symbols
- A does NOT see C's symbols (no transitive re-export)
- B can re-export C's symbols via `export { name1, name2 }` (existing syntax)

### 6. Circular Import Detection

The resolver tracks a stack of modules being resolved. If a module appears
on the stack while being resolved, the compiler emits:

```
error: circular import detected: a.mn -> b.mn -> a.mn
```

### 7. Python Backend

The Python emitter translates imports to Python imports. For resolved modules:
- `import foo` → `import foo` (Python will find the transpiled `.py` file)
- `import foo { bar }` → `from foo import bar`

The compiler driver emits all modules to a common output directory so Python
can resolve them.

### 8. LLVM Backend

For the LLVM backend, each module compiles to a separate LLVM module.
The emitter declares external functions/globals for imported symbols.
The linker combines all object files.

For this initial implementation, the LLVM backend will:
- Declare imported functions as `declare` (external) in the current module
- Require the user to compile and link all source files together

### 9. Error Messages

| Scenario | Error |
|----------|-------|
| Module not found | `module 'foo::bar' not found (searched: ./foo/bar.mn, ./foo/bar/mod.mn)` |
| Circular import | `circular import detected: a.mn -> b.mn -> a.mn` |
| Private symbol | `'helper' is not public in module 'utils'` |
| Unknown symbol | `'xyz' not found in module 'utils'` |

## Future Extensions

- Re-export syntax: `pub import foo { bar }` (re-exports bar publicly)
- Glob imports: `import foo::*` (import all public symbols)
- Package resolution via `mapanare.toml` dependencies
- Separate compilation with `.mni` interface files
