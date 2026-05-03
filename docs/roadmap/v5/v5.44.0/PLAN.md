# v5.44.0 — Ps.* — package-aware imports + stdlib extraction runway

**Status:** PLANNING
**Type:** Package-system / compiler integration release. Small,
load-bearing CLI + module-resolution edits; no language syntax
changes. This is the ecosystem bridge before the v5 closeout
panel.
**Breaking:** No. Existing bundled `stdlib/` remains the default.
Installed packages become an additional import source.
**Prerequisite:** v5.43.0 shipped (distributed agents). Package
manager docs and `stdlib/pkg.py` already exist; this release makes
installed packages compile like real dependencies.
**Estimated effort:** 1-2 sessions. Mostly resolver/CLI wiring,
tests, docs, and one clean pure-.mn package example.

---

## Why this exists

Mapanare already has the shape of a Cargo/npm/pip-style package
system:

- `mapanare.toml`
- `[dependencies]`
- semver-ish constraints
- `mn_modules/<name>-<version>/`
- `mapanare.lock`
- registry-first install with git fallback
- publish tarballs

But the compiler side is not complete enough to make an external
repo behave like a normal user dependency. `mnc install` can place
packages under `mn_modules/`, yet the import resolver mainly searches
the source file directory and the built-in `stdlib/`. That means an
isolated `mapanare-research/stdlib` repo can be tested with manual
path tricks, but not yet with the normal workflow:

```bash
mnc install collections
mnc run main.mn
```

This release closes that gap. It does **not** move the whole stdlib
out of the main repo. It creates the runway for doing that safely:
package-aware imports, version/install tracking in the compiler
workflow, CI proof from an isolated repo, and clear policy for which
stdlib modules can be external packages.

The important rule: packages that require native runtime ABI support
(`net/http`, future `time`, sqlite, TLS, etc.) stay bundled until the
runtime requirement is explicit in package metadata and CI. Pure `.mn`
packages move first.

---

## Goals

1. **Ps.1** — Package-aware import resolution: installed packages in
   `mn_modules/` are importable without manual `--stdlib-path` hacks.
2. **Ps.2** — Lockfile-backed install tracking: compiler/CLI can
   identify the exact installed version used for a build.
3. **Ps.3** — Stable package layout contract: package root, entry
   module, exported module names, and examples are documented and
   tested.
4. **Ps.4** — External stdlib policy: classify stdlib modules as
   bundled-core, runtime-bound package candidates, or pure package
   candidates.
5. **Ps.5** — Isolated-repo test path: prove an external package repo
   can be checked out, installed, imported, tested, and packaged.
6. **Ps.6** — CI sketch for `mapanare-research/stdlib`: matrix against
   latest released `mnc` and current `main`/nightly `mnc`.
7. **Ps.7** — Keep the v5 closeout panel honest: v5.45.0 audits this
   ecosystem bridge before v6.0 begins.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ps.1** | HIGH | **Package import roots.** Extend `ModuleResolver` construction so project builds include installed package roots from `mn_modules/`, derived from `mapanare.lock` when present and directory scan fallback otherwise. Keep search order deterministic: source-local, explicit `--stdlib-path`/extra paths, installed packages, bundled stdlib. | 3h |
| **Ps.2** | HIGH | **Package name to import root mapping.** Define how `mn_collections-0.1.0/` maps to imports. Preferred v0: package root exports `mod.mn` or `main.mn`; package name import aliases hyphen to underscore (`mn-foo` importable as `mn_foo`). Document the rule and add tests for exact-version dirs. | 2h |
| **Ps.3** | HIGH | **CLI integration.** Ensure `mnc run`, `mnc build`, `mnc emit-llvm`, `mnc emit-mir`, and test runner paths all construct resolvers with the same package roots. Today `build` has `--stdlib-path`; `emit-llvm` still uses a plain resolver. Remove that inconsistency. | 3h |
| **Ps.4** | HIGH | **Lockfile/install tracking in build diagnostics.** When a package import resolves through `mn_modules`, record package name/version/source in the module cache or diagnostics surface. This gives reproducible-build breadcrumbs and lets future `mnc package graph` report actual deps. | 2h |
| **Ps.5** | MEDIUM | **Pure package exemplar.** Promote `examples/packages/mn_collections` into the blessed example, because it is pure `.mn` and does not depend on removed Python interop. Add a consumer example with `[dependencies] mn_collections = "0.1.0"` and an import that compiles through `mn_modules`. | 2h |
| **Ps.6** | MEDIUM | **HTTP/time policy note.** Document why `examples/packages/mn_http` is not the model: it uses removed `extern "Python"` and the real `stdlib/net/http.mn` is runtime-bound. `net/http` remains bundled until packages can declare native runtime ABI requirements. Same policy applies to v5.34.0 time shims. | 1h |
| **Ps.7** | MEDIUM | **External stdlib classification doc.** Add `docs/guides/stdlib-packaging.md` or extend package docs with a table: bundled-core, pure package candidate, runtime-bound candidate, downstream-only. Initial candidates: `text`, `encoding/csv`, collection helpers = pure; `net/http`, `time`, sqlite/crypto = runtime-bound; calendars beyond Gregorian = downstream-only. | 2h |
| **Ps.8** | MEDIUM | **Isolated repo workflow.** Write the theoretical-but-actionable flow for `mapanare-research/stdlib`: checkout repo, install local path/git dependency, run package tests, pack tarball, publish. Include local dev loop before registry exists. | 1h |
| **Ps.9** | MEDIUM | **CI contract.** Draft `.github/workflows/stdlib.yml` shape for the future external repo: test against latest released `mnc`, current Mapanare `main` artifact, Windows/macOS/Linux, and a package tarball smoke test. Keep as docs unless the repo exists in this tree. | 1h |
| **Ps.10** | HIGH (gate) | **Tests.** Add focused tests for manifest parsing, `mn_modules` root discovery, import resolution from installed package dirs, lockfile preference, CLI parity across `build`/`emit-llvm`, and tarball exclusion of `mn_modules`. | 4h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.43.0 HEAD clean. Confirm package
  manager tests and module-resolution tests baseline.
- **Phase 1** — Ps.1 + Ps.2 resolver design and package-root
  discovery. Keep it deterministic and tiny.
- **Phase 2** — Ps.3 CLI parity: all compile/test entry points use
  the same resolver construction.
- **Phase 3** — Ps.4 build diagnostics / install tracking surface.
- **Phase 4** — Ps.5 pure package exemplar + consumer example.
- **Phase 5** — Ps.6-Ps.9 docs: stdlib packaging policy,
  isolated-repo workflow, CI contract.
- **Phase 6** — Ps.10 tests + regression gates.
- **Phase 7** — Bump + tag.

---

## Out of scope

- **Moving bundled stdlib out of this repo.** v5.44.0 only makes that
  safe later. Bundled stdlib remains the default user experience.
- **Registry server changes.** Use existing registry-first + git
  fallback behavior. Server-side metadata improvements can follow.
- **Native ABI dependency metadata.** This release documents the
  requirement but does not design the full ABI declaration format.
- **Making `net/http` external.** It is runtime-bound and should stay
  bundled for now.
- **Making v5.34.0 `time` external.** It needs runtime shims; same
  policy as HTTP.
- **v6.0 borrow-checker work.** The panel moved to v5.45.0; v6.0
  still waits for that panel.

---

## Risk

1. **Import search order ambiguity.** Local files, installed packages,
   and bundled stdlib can collide. Mitigation: deterministic order,
   diagnostic that reports the chosen path, and tests for collisions.
2. **Package names vs import names.** Hyphens are normal package names
   but awkward module names. Mitigation: v0 rule is simple and
   documented: package names may contain hyphens; import aliases use
   underscores.
3. **Lockfile lies if `mn_modules` is manually edited.** The lockfile
   can point at a version not actually installed. Mitigation: if the
   locked package directory is missing or integrity mismatches, fail
   with `run mnc install`, not silent fallback.
4. **Runtime-bound packages look installable but fail at link time.**
   HTTP/time are the concrete examples. Mitigation: do not bless them
   as external package examples yet; document native ABI metadata as
   a future requirement.
5. **Panel scope drift.** Adding v5.44.0 before the closeout means the
   panel has one more release to audit. Mitigation: v5.45.0 panel plan
   explicitly includes Ps.* in its audit list.

---

## Success criteria

- ✅ A project with `mapanare.toml` + `mapanare.lock` can import a
  package installed under `mn_modules/<name>-<version>/`.
- ✅ `mnc build`, `mnc emit-llvm`, `mnc emit-mir`, and test runner use
  the same package-aware resolver behavior.
- ✅ Lockfile-installed version is visible in build diagnostics or
  module metadata.
- ✅ `mn_collections` package example compiles from a consumer project.
- ✅ `mn_http` package example is either marked legacy/broken or
  clearly redirected to bundled `stdlib/net/http.mn`.
- ✅ Docs explain bundled-core vs pure-package vs runtime-bound package
  policy.
- ✅ Isolated `mapanare-research/stdlib` workflow is documented enough
  to test a package before a registry publish.
- ✅ Focused package/import tests pass.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "installed packages are not real compiler import roots" gap.
- The immediate blocker to testing package candidates from an isolated
  repo.
- The roadmap ambiguity around whether `http`/`time` should move out
  now: not yet, because they are runtime-bound.

**Inherits to v5.45.0:**
- End-of-v5 closeout panel. It now audits v5.31.0 through v5.44.0,
  including Ps.*.

**Inherits to v6.0 or later:**
- Native ABI dependency metadata for packages.
- First-class `mnc package graph` / dependency tree UI.
- Actual `mapanare-research/stdlib` repo split once package imports
  have soaked.
- Registry-side package provenance/signing hardening.

**Aggregate state entering v5.45.0 (closeout panel):**
foundation arc complete; stdlib gap-close complete; manifesto arc
complete; package-system runway complete. v5.45.0 is the panel that
green-lights v6.0.
