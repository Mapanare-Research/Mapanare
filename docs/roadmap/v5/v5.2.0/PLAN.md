# Mapanare v5.2.0 — "Package Registry MVP"

> **The last open item on `V5_READINESS.md`.** `mapanare install pkg`
> works against a real registry: search, publish, install a versioned
> `.mn` package. Was explicitly scoped as "v5.x ecosystem" at the
> v4.136.0 panel; this is that slot.

**Status:** PLANNED (skeleton)
**Breaking:** No (net-new feature)
**Prerequisite:** v5.1.2 shipped
**Estimated work:** 4-6 sessions (this is a minor bump, not a patch)

---

## Why this release exists

Mapanare has had `mapanare install`, `mapanare publish`,
`mapanare search`, and `mapanare login` as CLI commands since v4.1.0.
They currently point at stub endpoints. The V5_READINESS.md audit at
v4.135.0 identified package-registry infrastructure as the last open
feature-track item that would be embarrassing to lack at v5.0.

v5.0.0 shipped without it ("ecosystem scope, not v5.0 gate"). v5.2.0
delivers it.

## Scope

**In scope:**
- A registry service (host-TBD — candidate: Cloudflare Workers +
  R2, as it's free at MVP scale and matches
  `docs/project_website_architecture.md`)
- Package metadata schema: name, version, description, dependencies
  (with version constraints), license, repository URL, checksum,
  entry point
- CLI wiring in `mapanare/cli.py::cmd_publish` and `cmd_install`:
  - `mapanare publish` tars the current project, uploads to registry,
    updates `packages/index.json`
  - `mapanare install foo@1.2.3` downloads, verifies checksum,
    extracts to a per-project `mn_modules/` directory
  - `mapanare install` (no arg) reads `mapanare.toml` and installs
    all declared deps
- Lockfile: `mapanare.lock` records resolved versions
- Dependency resolution: semver with `^` `~` `>=` operators (MVP
  picks the latest satisfying; no SAT solver)
- A handful of seed packages published by the Mapanare team:
  - `http-server` (stdlib extraction)
  - `json-parser` (exists in stdlib; re-publish as pkg)
  - `dato` (the DataFrame library — already at
    `github.com/Mapanare-Research/dato`)

**Out of scope:**
- Per-package build scripts (native FFI stubs; v5.3+)
- Private packages / access control (v5.3+)
- Yanking and delisting semantics
- Vendoring for offline builds (v5.4+)
- Cargo-parity (features, dev-deps, target-specific deps)

## Exit criteria

- `mapanare publish dato@0.1.0` succeeds from an untrusted machine
  (registry auth works)
- `mapanare install dato@0.1.0` in a fresh project downloads the
  package and `import dato` resolves
- The registry serves at least 10 packages on launch day (seed with
  small utilities)
- Web UI at `packages.mapanare.dev` shows package list + details
  (can be static-generated from the R2 bucket)

## Risks

**Risk 1 — hosting cost explodes.**
Package registries can become expensive as they grow (npm's S3 bill
is legendary).
*Mitigation:* R2 is free for egress to Cloudflare's CDN; packages
stored there with a reasonable cache TTL should cost under $5/mo
until at least 10k packages.

**Risk 2 — version-resolution edge cases become panic-class bugs.**
A badly-resolved install is hard to roll back.
*Mitigation:* MVP uses strictly latest-satisfying; no transitive
peer-dep resolution. Users who hit the edge case can pin exact
versions.

**Risk 3 — supply-chain attack risk day one.**
*Mitigation:* require SHA256 checksum verification on install. Pin
initial set of publishers to team-controlled accounts. Document a
yanking procedure even if we don't implement it yet.
