# Mapanare Stability Policy

**Effective from:** v1.0.0
**Status:** Active

This document defines what is guaranteed stable in Mapanare, what is not, and how
breaking changes are managed.

---

## What Is Guaranteed Stable

Starting at v1.0.0, the following are frozen and subject to the backwards compatibility
guarantees described in this document:

- **Syntax.** All grammar productions in the language specification (`docs/SPEC.md`) are
  stable. Valid Mapanare v1.0 programs will remain valid in all v1.x releases.
- **Semantics.** Type checking rules, scoping rules, pattern matching exhaustiveness,
  operator precedence, and evaluation order are fixed.
- **Builtin functions.** The signatures and behavior of builtins (`print`, `println`,
  `len`, `str`, `int`, `float`, `Some`, `Ok`, `Err`, `signal`, `stream`) are stable.
- **Stdlib public API.** The public function and type signatures of shipped stdlib modules
  (`encoding/json`, `encoding/csv`, `net/http`, `net/websocket`, `crypto`, `text/regex`)
  are stable. Return types, parameter types, and error variants will not change.
- **Error codes.** Structured error codes in `MN-X0000` format are stable. Existing codes
  will not be reassigned to different error conditions.
- **CLI interface.** The commands `run`, `build`, `test`, `check`, `fmt`, `lint`, `doc`,
  `emit-llvm`, `emit-mir` and their documented flags are stable.

## What Is NOT Frozen

The following may change in any minor or patch release without an RFC:

- **New stdlib modules.** Adding new modules (e.g., `db/sql`, `encoding/yaml`) does not
  break existing code.
- **New stdlib functions.** Adding functions or types to existing stdlib modules, provided
  existing signatures are unchanged.
- **New builtins.** Adding new builtin functions, provided existing ones are unchanged.
- **Optimizer behavior.** MIR optimizer passes may be added, removed, or reordered. Output
  code performance characteristics may change.
- **Compiler diagnostics text.** Error and warning message wording may change. Error codes
  remain stable; human-readable text does not.
- **C runtime internals.** The native C runtime (`runtime/native/`) is an implementation
  detail. Function names, memory layout, and internal APIs may change.
- **LLVM IR output.** The specific LLVM IR generated is not stable. Only the observable
  behavior of compiled programs is guaranteed.
- **New compilation targets.** Adding targets (e.g., WASM, ARM64) does not require an RFC.
- **New CLI commands.** Adding new subcommands or flags does not break existing usage.
- **MIR representation.** The MIR data structures and text format are internal and may change.
- **Self-hosted compiler internals.** The modules in `mapanare/self/` are implementation
  details, not public API.
- **Debug info format.** DWARF output structure may change.

---

## Semantic Versioning Contract

Mapanare follows [Semantic Versioning 2.0.0](https://semver.org/).

### Major (e.g., v2.0.0)

A major version bump means at least one of:

- Removal of syntax that was valid in the prior major version.
- Change to the semantics of existing language constructs.
- Removal of a stdlib public API (function, type, or error variant).
- Change to a builtin function signature or behavior.
- Removal of a CLI command or flag.

### Minor (e.g., v1.1.0)

A minor version bump means new functionality that is backwards-compatible:

- New stdlib modules.
- New functions or types added to existing stdlib modules.
- New language features that do not alter existing syntax or semantics (requires RFC).
- New CLI commands or flags.
- New builtin functions.
- New compilation targets.

### Patch (e.g., v1.0.1)

A patch version bump means backwards-compatible fixes:

- Bug fixes (compiler, runtime, stdlib).
- Performance improvements.
- Documentation corrections.
- Diagnostic message improvements.
- Security patches.

---

## Deprecation Cycle

When a stable API or language feature must be removed or changed:

1. **Warn.** The feature is marked with the `@deprecated` attribute and the compiler emits
   a deprecation warning. The warning message must include the replacement (if any) and
   the version in which removal is planned.

2. **One minor version minimum.** The deprecation warning must be present for at least one
   full minor release before removal. For example, if deprecated in v1.2.0, it may be
   removed no earlier than v1.3.0 (or v2.0.0 for syntax/semantic changes).

3. **Remove.** The feature is removed. If removal changes syntax or semantics, it requires
   a major version bump. If it only removes a stdlib function, it may happen in a minor
   release provided the deprecation cycle was followed.

4. **Migration guide.** Every removal must be accompanied by a migration guide following
   the template in `docs/MIGRATION_TEMPLATE.md`.

### Deprecation warning format

```
warning[MN-D0001]: `old_function` is deprecated since v1.2.0
  --> src/main.mn:15:5
   |
15 |     old_function(x)
   |     ^^^^^^^^^^^^ use `new_function` instead
   |
   = note: will be removed in v2.0.0
```

---

## Communicating Breaking Changes

Breaking changes are communicated through multiple channels:

1. **RFC.** All breaking changes require a published RFC in `docs/rfcs/` before
   implementation. See `docs/rfcs/RFC_PROCESS.md`.

2. **CHANGELOG.** Every release with deprecations or removals has a `### Breaking Changes`
   section at the top of its changelog entry.

3. **Compiler warnings.** Deprecation warnings are emitted during compilation for at least
   one minor version before removal.

4. **Migration guide.** A migration guide is published in `docs/migrations/` for every
   breaking change, following the template in `docs/MIGRATION_TEMPLATE.md`.

5. **Release notes.** GitHub release notes highlight breaking changes prominently.

---

## Exceptions

The following situations are not considered breaking changes and do not require an RFC or
deprecation cycle:

- **Fixing a bug where the compiler accepted invalid code.** If the spec says code is
  invalid but the compiler accepted it, fixing the compiler is a bug fix.
- **Fixing undefined behavior in the C runtime.** Behavior not specified in the language
  spec or stdlib documentation is undefined and may change.
- **Security fixes.** Critical security vulnerabilities may be patched without a
  deprecation cycle, though a migration guide is still provided.

---

*This policy is itself versioned. Changes to this document require an RFC.*
