# External Package Workflow

**Status:** v5.44.0 Ps.8. Documents the dev loop for working on a
package in an isolated repo (e.g., a future `mapanare-research/stdlib`
split) before publishing it through the registry.

The v5.44.0 release ships package-aware imports
(`docs/guides/stdlib-packaging.md`) but does not split any stdlib
modules out yet. This guide is the actionable recipe for when you
*do* want to develop or test a package against a consumer project.

---

## Three modes for using a package

| Mode | When | How |
|---|---|---|
| Path dependency | Local development; iterating on a package + consumer simultaneously | `[dependencies] my-pkg = { path = "../my-pkg" }` |
| Git dependency | CI; pinning a non-registry source | `[dependencies] my-pkg = { git = "...", branch = "main" }` |
| Registry dependency | Production; published package | `[dependencies] my-pkg = "0.1.0"` |

v5.44.0 supports all three at the install layer (`stdlib/pkg.py`); the
resolver reads `mn_modules/` regardless of which install path produced
the directory.

---

## Path-dependency dev loop

The fast iteration loop. The package source lives in a sibling
directory; changes to the package are picked up by the consumer on
the next build.

### Layout

```
work/
├── my-pkg/                       # package repo (isolated)
│   ├── mapanare.toml             # name = "my-pkg", version = "0.1.0"
│   ├── main.mn                   # or mod.mn — entry module
│   └── tests/                    # package's own tests
└── consumer/                     # consumer project
    ├── mapanare.toml             # depends on my-pkg via path
    ├── main.mn                   # imports my_pkg
    └── (mn_modules/ is populated by `mnc install`)
```

### Consumer's `mapanare.toml`

```toml
[package]
name = "consumer"
version = "0.1.0"

[dependencies]
my-pkg = { path = "../my-pkg" }
```

Note: `mnc install` for path dependencies is currently a copy
operation (a literal copy of the path-dep directory into
`mn_modules/<name>-latest/`). For pure iteration, you can also
manually symlink:

```bash
ln -s "$(realpath ../my-pkg)" consumer/mn_modules/my-pkg-latest
```

The compiler doesn't care whether the entry under `mn_modules/` is a
real directory, a symlink, or an installer-populated copy. The
resolver consumes `PackageRoot` records produced by
`mapanare.pkg_discovery.discover_package_roots`; storage shape is
the discovery layer's concern, not the resolver's.

### Daily loop

```bash
cd consumer
mnc run main.mn                         # reads via mn_modules/
# Edit ../my-pkg/main.mn ...
mnc run main.mn                         # picks up changes
mnc build main.mn --verbose             # see [package] line:
                                        #   [package] my-pkg@latest from mn_modules
```

### Importing a hyphenated package

Hyphens in package names map to underscores in import names:

```mn
import my_pkg               // for package my-pkg
```

This is the only canonicalization. A package whose name is already
`my_pkg` (no hyphen) imports as `my_pkg` directly.

---

## Git-dependency loop

For CI or when you want to pin a specific commit of a package without
publishing it:

```toml
[dependencies]
my-pkg = { git = "https://github.com/me/my-pkg.git", branch = "main" }
```

`mnc install`:

1. Resolves `git` URL.
2. `git clone --depth 1 --branch <branch>` into
   `mn_modules/my-pkg-latest/`.
3. Records the resolved commit hash + integrity SHA-256 in
   `mapanare.lock`.

After a successful install, the lockfile is the source of truth.
Subsequent `mnc build` runs verify the install dir matches the
locked commit; mismatches fail with `run mnc install`.

---

## Registry-dependency loop

For published packages:

```toml
[dependencies]
my-pkg = "0.1.0"          # exact
my-pkg = "^0.1.0"         # caret: 0.1.x but not 0.2
my-pkg = ">=0.1.0,<0.3"   # range
```

`mnc install`:

1. Queries the registry (`MAPANARE_REGISTRY_URL`,
   default `https://mapanare.dev`).
2. Resolves the highest version satisfying the constraint.
3. Downloads the tarball; verifies SHA-256 against the registry's
   declared checksum (supply-chain baseline).
4. Extracts to `mn_modules/<name>-<version>/`.
5. Records the resolved version + integrity in `mapanare.lock`.

If the registry is unreachable, `mnc install` falls back to the
convention git URL (`github.com/Mapanare-Research/<name>.git`) for
official packages.

---

## Publishing

Once the package is ready:

```bash
cd my-pkg
mnc bump patch                         # bump version
mnc package                            # build .tar.gz locally (smoke test)
# inspect: tar tzf my-pkg-0.1.1.tar.gz
mnc publish --token $MAPANARE_TOKEN    # upload to registry
```

The tarball excludes `mn_modules/`, `__pycache__`, hidden dirs
(`.git/`, `.mn-cache/`), and `node_modules/`. This is locked by
`stdlib/pkg.py:_build_tarball` and tested by
`tests/packages/test_package_tarball_excludes_mn_modules.py`.

---

## Testing your package

Inside the package repo:

```bash
mnc test ./tests/                      # run @test functions
mnc check --all                        # type-check every .mn file
```

Both go through the same package-aware resolver as `mnc build`, so a
package that depends on another package (transitive deps) resolves
correctly during its own tests.

---

## Diagnosing resolution

When an import doesn't resolve where you expect:

```bash
mnc build main.mn --verbose
```

Stderr lists every package that was resolved through `mn_modules/`:

```
[package] my-pkg@0.1.0 from mn_modules
[package] another-pkg@2.3.1 from mn_modules
```

For machine-readable form:

```bash
mnc build main.mn --diag-json /tmp/d.json
cat /tmp/d.json
```

If the package you expect isn't listed, check:

1. Is `mapanare.toml` present in the consumer's directory? (`find .
   -name mapanare.toml`)
2. Is the package installed? (`ls mn_modules/`)
3. Does the lockfile pin the right version? (`cat mapanare.lock`)
4. Does the package's directory have a `main.mn` or `mod.mn`?

Search-order policy is documented in
`mapanare/modules.py::ModuleResolver` and locked by
`tests/packages/test_resolver_search_order.py`:

1. Source-local file (highest priority — overrides everything else).
2. Explicit `--stdlib-path` / `--extra-path` / `MAPANARE_PATH`.
3. Installed packages (this layer).
4. Bundled stdlib (lowest priority).

Source-local always wins; explicit overrides outrank packages;
packages outrank bundled stdlib.

---

## Why this matters now

v5.44.0 makes the workflow above real. Before this release, even a
consumer with a fully populated `mn_modules/` couldn't import from
those packages without manual `--stdlib-path` hacks against each
package directory.

After v5.44.0, the workflow is symmetric to npm/Cargo/pip:
declare-install-import.

The **migration** of stdlib modules out of the main repo into
external packages is a separate, deliberately-deferred decision (see
`docs/guides/stdlib-packaging.md`). v5.44.0 ships the runway; v6.0+
decides what to drive on it.
