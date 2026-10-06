# v5.44.0 — PRE_PHASE_AUDIT

Audit of v5.43.0 HEAD before drafting any new package-system code.
The PROMPT explicitly warns the PLAN's "design a package system"
framing is partly wrong: most of the package machinery already
exists. This document confirms exactly what's shipped, what's
missing, and what each Ps.\* item actually has to add.

---

## Existing at v5.43.0 HEAD

### Manifest / lockfile / install machinery

`stdlib/pkg.py` (1037 LOC) ships a near-complete Cargo/npm-style
package manager:

| Surface | Where | Status |
|---|---|---|
| `mapanare.toml` parser | `parse_manifest`, `MapanareManifest` | shipped, with mini TOML parser |
| Manifest writer | `MapanareManifest.to_toml`, `save_manifest` | shipped |
| `[dependencies]` `[dev-dependencies]` | `Dependency.from_dict`, both sections | shipped (semver-ish: `*`, `^`, `~`, `>=`, `<=`, `=`, exact) |
| `mapanare.lock` JSON format | `LockFile`, `LockedDependency` | shipped (lockfile_version: 1; integrity SHA-256) |
| Install layout | constant `MAPANARE_PACKAGES_DIR = "mn_modules"` | shipped |
| Registry-first install | `_install_from_registry` (with SHA-256 verification) | shipped |
| Git fallback install | `_install_from_git` (depth-1 clone, branch override) | shipped |
| Convention git URL | `_default_git_url` → `github.com/Mapanare-Research/<name>.git` | shipped |
| Integrity hash | `_compute_integrity` SHA-256 over `.mn` + `mapanare.toml` | shipped |
| Publish tarball | `_build_tarball`, `publish_package` (multipart upload) | shipped |
| **Tarball exclusion of `mn_modules`** | `_build_tarball` line 605 | **shipped — Ps.10 just locks** |
| Search registry | `search_packages` | shipped |
| `init_project` from template | `init_project` + templates dir | shipped |
| `bump_version` (major/minor/patch) | `bump_version` | shipped |
| `uninstall_package` | full mn_modules cleanup + manifest/lock update | shipped |

**Implication:** every Ps.\* item that touches manifest/lockfile/install
behavior is **wiring**, not authoring. Do not re-implement TOML parse,
lockfile JSON, integrity hash, or registry calls.

### Module resolver

`mapanare/modules.py:50` defines `ModuleResolver`:

```python
def __init__(self, search_paths: list[str] | None = None) -> None:
    self._cache: dict[str, ResolvedModule] = {}
    self._resolution_stack: list[str] = []
    self._search_paths = search_paths or []
    # Auto-adds bundled stdlib directory:
    stdlib_dir = os.path.join(..., "stdlib")
    if os.path.isdir(stdlib_dir) and stdlib_dir not in self._search_paths:
        self._search_paths.append(stdlib_dir)
```

`resolve_path` order at HEAD:

1. `self::` prefix (relative to source_dir, strip prefix)
2. `<source_dir>/<path>.mn`
3. `<source_dir>/<path>/mod.mn`
4. For each search path: `<dir>/<path>.mn` then `<dir>/<path>/mod.mn`

Bundled stdlib is appended to `self._search_paths` last, so source-local
already wins over bundled stdlib. Caching, circular-import detection,
SHA-256 source hashing, and `ResolvedModule` exports collection are
shipped.

**Implication:** Ps.1 is a small, surgical extension — accept
`package_roots: list[PackageRoot] | None = None` in `__init__`, slot it
into the search order BEFORE the bundled stdlib (so packages override
bundled but source-local still wins), and add hyphen→underscore
canonicalization. Estimated ~30 LOC core change.

### CLI ModuleResolver construction sites

| File:line | Caller | search_paths? |
|---|---|---|
| `mapanare/cli.py:289` | `cmd_check` (likely) | bare |
| `mapanare/cli.py:835` | `cmd_build` | **YES** (only site) |
| `mapanare/cli.py:1175` | `cmd_emit_llvm` | bare |
| `mapanare/cli.py:1348` | `cmd_emit_mir` | bare |
| `mapanare/cli.py:1388` | `cmd_emit_wasm` | bare |
| `mapanare/multi_module.py:641` | `cmd_build_multi` | bare |
| `mapanare/test_runner.py:112` | `cmd_test` | bare |
| `mapanare/lsp/analysis.py:1094` | LSP backend | bare |

**Only `--stdlib-path`** is plumbed in argparse — at `cli.py:2152` under
`p_build`. The PROMPT's "today `mnc emit-llvm` and `mnc emit-mir` may
not take `--stdlib-path` or build a different resolver" is **confirmed**:
they use bare `ModuleResolver()`. This is exactly the inconsistency
Ps.3 closes.

### Example packages

| Path | Status | Pure? |
|---|---|---|
| `examples/packages/mn_collections/` | exemplar candidate (Ps.5) | **YES** — `grep -rln 'extern' main.mn` returns nothing; pure `.mn` collection helpers |
| `examples/packages/mn_http/` | legacy | **NO** — `extern` blocks in `main.mn` (Python interop) |
| `examples/packages/mn_json/` | legacy | **NO** — `extern` blocks in `main.mn`; mapanare.toml description says "via Python interop" |

Note: `mn_json` was not mentioned in the PROMPT but exists and has the
same legacy shape as `mn_http`. Both should be retired/relabeled in
Ps.6 — not just `mn_http`.

### `mn_modules/` directories

`find . -type d -name "mn_modules" 2>/dev/null` returns nothing. The
install layout is **documented and writeable but never realized in the
repo**. All Ps.10 tests must construct fake `mn_modules/` trees in
`tmp_path` fixtures.

### Existing tests

`tests/modules/test_module_resolution.py` — closest relative; 80+ lines
of resolver tests (`TestModulePathResolution`, etc.) using `tmp_path`.
Pattern to mirror in `tests/packages/`.

`tests/packages/` does not exist; net-new directory.

---

## Ps.\* deltas vs. existing

| ID | Delta vs. HEAD | Effort estimate |
|---|---|---|
| **Ps.1** | NEW: `discover_package_roots()` helper + `PackageRoot` dataclass + `ModuleResolver(package_roots=...)` parameter + hyphen→underscore canonicalization. Resolver search-order extension. ~80 LOC core; ~150 LOC including tests. | 3h |
| **Ps.2** | NEW (small): doc the hyphen→underscore rule + entry-module rule (`mod.mn` else `main.mn`). Both already in spirit; lock with tests. | 1h |
| **Ps.3** | REFACTOR: extract `_build_resolver_from_args(args, source_path)` helper. Update 7 bare-construction sites + the existing `cmd_build` site. Add `--stdlib-path` argparse arg to `p_run`, `p_check`, `p_emit_llvm`, `p_emit_mir`, `p_emit_wasm`, `p_build_multi`, `p_test`. Lock with parametrized parity test. ~80 LOC code change + ~50 LOC tests. | 3h |
| **Ps.4** | NEW: `_import_log: list[ImportRecord]` on `ModuleResolver` recording (name, version, source) when an import resolves through a package root. Surface via `--diag-json` and `--verbose` stderr. ~60 LOC + tests. | 2h |
| **Ps.5** | PARTIAL: `mn_collections` confirmed pure — keep as-is. NEW: `examples/packages/consumer_collections/` (mapanare.toml + main.mn + mapanare.lock + README) demonstrating the consumer flow. ~80 LOC across files. | 2h |
| **Ps.6** | NEW: mark `mn_http/LEGACY.md` AND `mn_json/LEGACY.md` (both have extern blocks; PROMPT only mentioned mn_http but mn_json has the same shape). ~30 LOC docs. | 1h |
| **Ps.7** | NEW: `docs/guides/stdlib-packaging.md` (~300 LOC classification table + policy). | 2h |
| **Ps.8** | NEW: `docs/guides/external-package-workflow.md` (~150 LOC dev loop). | 1h |
| **Ps.9** | NEW: `docs/guides/stdlib-ci-template.yml` (~100 LOC reference YAML, NOT active CI). | 1h |
| **Ps.10** | NEW: `tests/packages/` directory + 8 test files. ~500 LOC tests. | 4h |

**Compiler edits:** **NONE.** Resolver lives in `mapanare/modules.py`
(Python infra), not the LLVM emitter or self-host source.
**Runtime edits:** **NONE.**
**Self-host source touches** (`mapanare/self/*.mn`): **NONE.**

**Strict 3-stage fixed-point trivially preserved by construction.**
**Goldens 96/96 trivially preserved** (no compiler/runtime changes).

---

## Surprises during audit

1. **`mn_json` exists** and was not mentioned in the PROMPT. Same legacy
   shape as `mn_http` (extern blocks; "Python interop" in description).
   Treated identically to `mn_http` in Ps.6.

2. **Tarball already excludes `mn_modules`** — `_build_tarball` line 605
   explicitly skips `mn_modules`, `mapanare_packages`, `__pycache__`,
   `node_modules`. Ps.10's tarball-exclusion test locks already-correct
   behavior (still valuable as regression gate).

3. **Bundled stdlib is auto-appended** to `search_paths` in
   `ModuleResolver.__init__`. This means the load-bearing decision for
   Ps.1 is *where* package roots slot relative to that auto-append —
   they must come BEFORE bundled stdlib for the documented order
   (source-local → explicit → packages → bundled) to hold. Concretely:
   `_search_paths = [explicit..., *package_root_dirs, stdlib_dir]`.

4. **`MAPANARE_PACKAGES_DIR` constant** lives in `stdlib/pkg.py`. The
   discovery helper should import it from there, not duplicate.

5. **`_install_from_registry` writes to `mn_modules/<name>-<version>/`**
   where `<version>` is the resolved version (best match), not the
   constraint string. `_install_from_git` uses `<version>` if not `*`,
   else `latest`. So directory names can be `mn_collections-0.1.0/` or
   `mn_collections-latest/`. Discovery must handle both.

6. **There is an `archive/stdlib/pkg.py`** — older copy. Ignore; the
   live one is `stdlib/pkg.py`.

---

## Ps.4 storage-source field naming

Per PROMPT, the `PackageRoot.source` field uses these literals:
- `"mn_modules"` — discovered under project's `mn_modules/<name>-<version>/`
- `"path"` — future path-dependency support
- `"git"` — future direct git-checkout support
- `"global-cache"` — future global cache backing

v5.44.0 ships `"mn_modules"` only; the field is reserved for forward
compatibility per the local-storage / shared-storage / project-scoped
boundary the PROMPT articulates.

---

## Risk assessment

GitNexus impact pre-flight (queued for Phase 1 entry):

- `ModuleResolver` is consumed by 8 call sites; impact MEDIUM but
  contained — adding an optional kw-only param is backward-compatible.
- `cli.py` resolver construction is the load-bearing risk surface; the
  parametrized parity test in Ps.3 is the structural mitigation.
- No symbols on the agent / network / runtime hot path are touched.

No HIGH or CRITICAL impact expected. Will re-verify in Phase 1 entry.

---

## Phase order confirmation

Phase plan unchanged from PROMPT:

- **Phase 0** (this doc + audit) — DONE.
- **Phase 1** — Ps.1 + Ps.2: `PackageRoot` + `discover_package_roots` +
  resolver extension + unit tests.
- **Phase 2** — Ps.3: extract `_build_resolver_from_args` + refactor
  8 sites + parametrized parity test.
- **Phase 3** — Ps.4: install diagnostics surface.
- **Phase 4** — Ps.5 + Ps.6: consumer_collections example + LEGACY.md
  for mn_http and mn_json.
- **Phase 5** — Ps.7 + Ps.8 + Ps.9 docs.
- **Phase 6** — Ps.10 tests.
- **Phase 7** — bump + closeout.

**Total estimated:** 18–20 hours of focused work; well within
1–2 sessions.
