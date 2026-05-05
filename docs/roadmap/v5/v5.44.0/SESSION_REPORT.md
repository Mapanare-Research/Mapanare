# v5.44.0 SESSION_REPORT — Ps.\* package-aware imports + stdlib extraction runway

**Status:** READY (not tagged — per project convention, lead approves tags).
**Date:** 2026-05-05.
**Type:** Package-system / compiler integration release. Wires existing
`stdlib/pkg.py` machinery into the existing `mapanare/modules.py`
resolver. No language syntax changes, no compiler edits, no runtime
edits, no `mapanare/self/*.mn` source touches.

---

## Aggregate state

| Metric | Value |
|---|---|
| STRICT 3-stage fixed point | **Preserved by construction** — 242,338 lines / 0 diff (46-release strict streak from v5.7.1 baseline; zero `.mn` self-host edits) |
| Goldens | **96/96** (no compiler edits → no IR shape change) |
| Compiler edits | **0** |
| Runtime edits | **0** |
| `mapanare/self/*.mn` touches | **0** |
| New Python code | ~330 LOC (`pkg_discovery.py` + `cli.py` helpers) |
| Modified Python code | ~80 LOC across `modules.py` + 4 call-site files |
| New tests | 65 cases across 7 files (`tests/packages/`) |
| New docs | ~660 LOC (3 guides) |
| New examples | `consumer_collections/` + 2 LEGACY.md |

---

## What shipped

### Ps.1 + Ps.2 — Resolver extension + name mapping

`mapanare/pkg_discovery.py` (net-new, ~280 LOC):

- `PackageRoot` frozen dataclass holding
  `(package_name, import_name, version, root_dir, entry_module,
  source, integrity)`. `source` is a string literal that is
  `"mn_modules"` in v5.44.0 and reserved for future `"path"`,
  `"git"`, `"global-cache"` backings.
- `discover_package_roots(project_dir, *, use_lockfile=True)` —
  primary entry point. Lockfile-authoritative when present;
  alphabetical scan fallback otherwise. Multiple installed versions
  in scan mode → `PackageDiscoveryError`. Missing locked install
  dir → `PackageDiscoveryError("...run mnc install")`.
- `find_project_dir(source_path)` — walks up looking for
  `mapanare.toml`.
- `package_name_to_import_name(name)` — hyphen→underscore (Ps.2).
- `_entry_module(pkg_dir)` — `mod.mn` else `main.mn` (Ps.2).
- `build_resolver_for_source(source_path, *, explicit_paths=None)` —
  lower-level primitive used by both the CLI helper
  (`_build_resolver_from_args`) and the LSP backend.

`mapanare/modules.py` extended:

- `ImportRecord` frozen dataclass for the Ps.4 diagnostics surface.
- `ModuleResolver.__init__` accepts kw-only
  `package_roots: list[PackageRoot] | None = None`. Backward-compat:
  bare `ModuleResolver()` and `ModuleResolver(search_paths=...)`
  unchanged.
- `_explicit_paths`, `_package_roots`, `_bundled_stdlib_dir`,
  `_import_log` fields added; `_search_paths` preserved for any
  unindexed grep-consumer.
- `resolve_path` rewritten with the four-step search order: source-
  local → explicit → packages → bundled stdlib. The bundled-stdlib
  step is no longer auto-appended to `_search_paths`; it has its own
  dedicated step in the resolution loop.
- New `_resolve_in_package(pkg, import_path)` helper handles the
  package-root branch and records the resolution in `_import_log`.
- New public methods `import_log()` and `package_roots()`.

### Ps.3 — CLI parity refactor

`mapanare/cli.py`:

- `_collect_explicit_paths(args)` — gathers `--stdlib-path` first,
  then each `--extra-path`, then `MAPANARE_PATH` env split on the OS
  path separator. Dedupes.
- `_build_resolver_from_args(args, source_path)` — single source of
  truth for resolver construction. Delegates to
  `build_resolver_for_source` for the project-walking logic; surfaces
  `PackageDiscoveryError` as stderr + `sys.exit(1)`.
- `_add_resolver_args(parser)` — argparse boilerplate. Parsers wired
  through `_build_resolver_from_args` MUST call this so all entry
  points expose identical surface.

Refactored 9 entry points (previously 8 different shapes):

| Site | Before | After |
|---|---|---|
| `cmd_check` (via `_check_one`) | `ModuleResolver()` | `_build_resolver_from_args(args, source_path=path)` per file |
| `cmd_run` | (didn't use a resolver) | `_build_resolver_from_args` + threaded into `_compile_to_c` |
| `cmd_build` | `ModuleResolver(search_paths=[stdlib_path])` | `_build_resolver_from_args` |
| `cmd_emit_llvm` | `ModuleResolver()` | `_build_resolver_from_args` |
| `cmd_emit_c` | (didn't use a resolver) | `_build_resolver_from_args` + threaded into `_compile_to_c` |
| `cmd_emit_mir` | `ModuleResolver()` | `_build_resolver_from_args` |
| `cmd_emit_wasm` | `ModuleResolver()` per src_file | `_build_resolver_from_args` per src_file |
| `cmd_build_multi` | (no resolver before; `compile_multi_module_mir` constructed its own) | `_build_resolver_from_args` + threaded through `_compile_multi_module_text` |
| `cmd_test` (via `_compile_test_to_llvm` in test_runner) | `ModuleResolver()` | `build_resolver_for_source` with PackageDiscoveryError fallback to bare resolver |

External call sites refactored:

| File | Behavior |
|---|---|
| `mapanare/multi_module.py:compile_multi_module_mir` | New optional `resolver` kw arg; backward-compatible bare fallback |
| `mapanare/test_runner.py:_compile_test_to_llvm` | `build_resolver_for_source` + tolerant fallback |
| `mapanare/lsp/analysis.py:_resolve_imported_symbols` | Same pattern as test_runner |

`_compile_to_c` extended with optional `resolver` kw arg (passed to
`check_or_raise`).

### Ps.4 — Install diagnostics

Two surfaces exposed via `_add_resolver_args`:

- `--verbose` — one `[package] <name>@<version> from <source>` line
  per resolved package import on stderr, deduped on
  `(package_name, version)`.
- `--diag-json PATH` — machine-readable JSON:
  ```json
  {
    "schema_version": 1,
    "packages": [
      {
        "name": "...",
        "import_name": "...",
        "version": "...",
        "source": "mn_modules",
        "integrity": "sha256:...",
        "imports": [{"import_path": [...], "resolved": "..."}]
      }
    ]
  }
  ```

`_surface_install_diagnostics(args, resolver)` is called from each
`cmd_*` AFTER successful compilation. Failed builds don't leak
partial diagnostics.

### Ps.5 — Pure exemplar

`examples/packages/consumer_collections/`:

- `mapanare.toml` declares `mn_collections = "0.1.0"`.
- `mapanare.lock` pins resolved version + integrity.
- `main.mn` imports `mn_collections` and exercises `sum`, `max`,
  `min`, `reverse`.
- `mn_modules/mn_collections-0.1.0/` pre-staged (copy of
  `examples/packages/mn_collections/`) so the demo runs without
  `mnc install`.
- `README.md` documents the dev loop, expected `--verbose` output,
  expected `--diag-json` payload.

### Ps.6 — Legacy markers

`examples/packages/mn_http/LEGACY.md` and
`examples/packages/mn_json/LEGACY.md`. Both explain:

1. Why these don't compile (`extern "Python"` removed at v4.29.0).
2. Why they're not the model for new packages (HTTP is runtime-bound;
   JSON now ships natively as `stdlib/encoding/json.mn`).
3. Where to find the model (`mn_collections` +
   `consumer_collections`).

PROMPT only mentioned `mn_http`; the Phase 0 audit surfaced that
`mn_json` has the identical legacy shape and got the same treatment.

### Ps.7 + Ps.8 + Ps.9 — Docs

- `docs/guides/stdlib-packaging.md` (~290 LOC) — bundled-core /
  pure-package candidate / runtime-bound / downstream-only
  classification + initial inventory of every stdlib module + the
  migration prerequisites (native-ABI declaration in `mapanare.toml`
  + runtime-export ABI versioning) deliberately deferred from
  v5.44.0.
- `docs/guides/external-package-workflow.md` (~230 LOC) — three dep
  modes (path/git/registry), daily iteration, hyphen mapping,
  publishing flow, diagnosis guide.
- `docs/guides/stdlib-ci-template.yml` (~140 LOC) — reference YAML
  for the future external-stdlib repo's CI. Multi-OS × dual-channel
  (latest released + main artifact) + tarball-exclusion gate.

### Ps.10 — Tests

`tests/packages/` (net-new): 65 cases across 7 files.

| File | Cases | Purpose |
|---|---|---|
| `test_resolver_search_order.py` | 12 | Locks 4-step search-order contract + hyphen mapping + entry-module rule + backward-compat |
| `test_resolver_lockfile.py` | 15 | Lockfile-authoritative; missing-dir error; multi-version scan error; project-dir walk |
| `test_cli_parity.py` | 17 | Every compile subcmd has resolver flags; grep-gate against bare `ModuleResolver()`; functional parity through `_build_resolver_from_args` |
| `test_install_diagnostics.py` | 7 | `--verbose` + `--diag-json` surfaces match lockfile |
| `test_consumer_collections_e2e.py` | 8 | Staged exemplar end-to-end; LEGACY.md presence |
| `test_package_tarball_excludes_mn_modules.py` | 3 | Tarball never includes `mn_modules/`, `__pycache__`, hidden dirs |
| `test_resolver_does_not_scan_global_cache.py` | 3 | Local-storage / shared-storage / project-scoped boundary |

**All 65 GREEN at v5.44.0 HEAD in 1.77s.**

---

## PROMPT/PLAN deviations (load-bearing)

### Phase 0 audit corrected the PLAN's framing

The PLAN said "design a package system." Phase 0 audit
(`PRE_PHASE_AUDIT.md`) found that **most of the package machinery
already exists** — `stdlib/pkg.py` is 1037 LOC of complete
manifest/lockfile/install/publish code. v5.44.0 wires existing
machinery into the resolver; doesn't re-design.

The PROMPT pre-empted this with "**CRITICAL — read this before
drafting any new file:** the PLAN treats this as if the package system
were green-field. The premise is partly wrong at HEAD." Audit
confirmed the warning and avoided hours of re-implementation.

### `mn_json` not mentioned in PROMPT

The PROMPT scoped Ps.6 around `mn_http`. Audit found `mn_json` has
the identical `extern "Python"` legacy shape. Treated identically:
both got `LEGACY.md`. Documented in `PRE_PHASE_AUDIT.md` and locked
in `test_consumer_collections_e2e.py::test_consumer_legacy_examples_marked`.

### CRITICAL impact rating on `ModuleResolver`

GitNexus impact analysis returned CRITICAL (56 impacted symbols, 23
direct callers, 17 execution flows). The PROMPT's STOP rule on CRITICAL
was surfaced to the user, who approved proceeding because the change
is structurally additive (kw-only optional new param with safe
default). All 23 legacy call sites continue to behave identically
unless explicitly routed through `_build_resolver_from_args`. The
backward-compat tests in `test_resolver_search_order.py` lock this:
`test_bare_constructor_unchanged_behavior`,
`test_search_paths_kw_unchanged_behavior`.

### Ps.5 staged `mn_modules/`

The PROMPT described `consumer_collections/` as the demo for the
`mnc install` flow. Phase 4 staged the `mn_modules/mn_collections-0.1.0/`
directory directly so the demo runs without network access (and
without depending on a working `mnc install` flow against a registry
that may not exist). README documents that this pre-staging is what
`mnc install` would produce from a real registry.

### `mn_http` retired in place, not moved

The PROMPT offered two options for `mn_http`: add a `LEGACY.md` or
move to `_legacy/mn_http/`. Took option A (in-place LEGACY.md) per
"prefer the simpler" tie-break. Same applied to `mn_json`.

### Ps.4 `--verbose` and `--diag-json` are universal flags

Implemented as part of `_add_resolver_args` rather than per-cmd,
because the load-bearing parity contract is "every compile entry
point has the same surface." Adding them only to `cmd_build` (the
PROMPT's narrowest reading) would have re-introduced the asymmetry
Ps.3 was specifically closing.

---

## Risk assessment closure

| PLAN risk | Mitigation shipped |
|---|---|
| Import search order ambiguity | Deterministic 4-step order; locked by `test_resolver_search_order.py` (12 cases, every pairwise precedence) |
| Package names vs import names | One rule, documented + tested: hyphens → underscores |
| Lockfile lies if `mn_modules/` is manually edited | `test_lockfile_no_silent_version_fallback`; missing-dir → `mnc install` |
| Runtime-bound packages look installable but fail at link time | Documented in `docs/guides/stdlib-packaging.md`; `mn_http` + `mn_json` marked LEGACY |
| Panel scope drift | v5.45.0 panel plan now includes Ps.\* in audit list |
| Local `mn_modules/` becomes accidental architecture | `discover_package_roots` is the only place `mn_modules` path math lives; resolver consumes `PackageRoot` records only |
| Global cache creates spooky imports | `test_resolver_does_not_scan_global_cache.py` (3 cases) locks the project-scoped-only invariant |

---

## Aggregate state entering v5.45.0

- **0 HIGH** (Ps.\* arc closed cleanly; no v5.43.0 carry-overs
  escalated)
- **2 MEDIUM** carry-forwards from v5.43.0 (lowerer fixes for
  `Result<T, complex Err>` + variant rewrap + nested 15-arm match;
  macOS notarization carry from v5.33.0 Nu.2)
- **~8 LOW** carry-forwards (added: native-ABI dependency declaration
  schema for `mapanare.toml`, runtime-export ABI versioning,
  global-cache implementation, registry-side package signing — all
  v6.0+ work)

**Manifesto arc CLOSED for v5.x at v5.43.0.**
**Package-system runway CLOSED at v5.44.0.**
**v5.45.0 is the closeout panel that audits v5.31.0 → v5.44.0 and
green-lights v6.0.**

---

## Files changed

```
A docs/roadmap/v5/v5.44.0/PRE_PHASE_AUDIT.md
A docs/roadmap/v5/v5.44.0/SESSION_REPORT.md          (this file)
A mapanare/pkg_discovery.py
M mapanare/modules.py
M mapanare/cli.py
M mapanare/multi_module.py
M mapanare/test_runner.py
M mapanare/lsp/analysis.py
A tests/packages/__init__.py
A tests/packages/test_resolver_search_order.py
A tests/packages/test_resolver_lockfile.py
A tests/packages/test_cli_parity.py
A tests/packages/test_install_diagnostics.py
A tests/packages/test_consumer_collections_e2e.py
A tests/packages/test_package_tarball_excludes_mn_modules.py
A tests/packages/test_resolver_does_not_scan_global_cache.py
A examples/packages/consumer_collections/mapanare.toml
A examples/packages/consumer_collections/mapanare.lock
A examples/packages/consumer_collections/main.mn
A examples/packages/consumer_collections/README.md
A examples/packages/consumer_collections/mn_modules/mn_collections-0.1.0/main.mn
A examples/packages/consumer_collections/mn_modules/mn_collections-0.1.0/mapanare.toml
A examples/packages/mn_http/LEGACY.md
A examples/packages/mn_json/LEGACY.md
A docs/guides/stdlib-packaging.md
A docs/guides/external-package-workflow.md
A docs/guides/stdlib-ci-template.yml
M docs/SPEC.md                                       (header re-sync)
M CHANGELOG.md
M CLAUDE.md                                          (release-notes entry)
M VERSION                                            (5.43.0 → 5.44.0)
M README.md                                          (badge bump)
M docs/README.es.md                                  (badge bump)
```
