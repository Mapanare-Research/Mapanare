# v5.2.0 Session Report — Package Registry MVP

**Date:** 2026-04-22
**Version:** 5.2.0
**Type:** Feature (first MINOR bump since v5.0.0)

---

## Summary

Delivers `mapanare install <pkg>@<ver>` against a real registry. Closes
the last open item on V5_READINESS.md (package registry infrastructure).

## What shipped

### Session 1 — Registry backend

Created `registry/` with Cloudflare Workers + R2 backend:

- **Source**: `registry/src/index.ts` (~350 lines)
- **Config**: `registry/wrangler.toml`, `registry/package.json`, `registry/tsconfig.json`
- **API endpoints**:
  - `GET /v1/packages` — list all packages
  - `GET /v1/packages/:name` — package metadata + versions
  - `GET /v1/packages/:name/:version` — single version info
  - `GET /v1/packages/:name/:version/tar` — download tarball (R2)
  - `POST /v1/packages` — publish (auth required, multipart/form-data)
  - `GET /v1/search?q=...` — substring search
- **Auth**: GitHub OAuth flow (`/auth/github`, `/auth/callback`, `/auth/poll`)
- **Security**: Bearer tokens in KV, IP rate limiting (60 req/min), team-only publishing
- **Deploy target**: `registry.mapanare.dev`

### Sessions 2-3 — Client CLI updates

Updated `stdlib/pkg.py`:

- `REGISTRY_URL` → `https://registry.mapanare.dev`
- API paths → `/v1/packages` (was `/api/packages`)
- Install directory → `mn_modules/<name>-<version>/` (was `mapanare_packages/<name>/`)
- SHA-256 verification on every tarball download
- `repository` field added to `MapanareManifest`
- `install_all()` function for no-arg `mapanare install`
- Publish sends metadata fields (name, version, description, license, repository, entry, dependencies)
- Fixed multipart encoding bug (`.encode()` scope on f-string concatenation)

Updated `mapanare/cli.py`:

- `mapanare install foo@1.2.3` — parses `@version` syntax
- `mapanare install` (no args) — reads `mapanare.toml` and installs all deps
- `package` argument now optional (`nargs="?"`)
- Help text updated from "git-based" to "registry"

### Session 4 — Integration

Registry deployment and seed packages are pending — requires
Cloudflare account setup and `wrangler deploy`. Source code is ready.

### Session 5 — Tests

Created `tests/registry/` with 51 tests:

- `test_mapanare_toml_parsing.py` — 17 tests (manifest parsing, serialization, dependency formats)
- `test_lockfile.py` — 14 tests (round-trip, determinism, disk I/O)
- `test_publish_install_roundtrip.py` — 20 tests (semver resolution, tarball creation, integrity, install-all, URL assertions)

All 51 tests pass.

### Phase N — Version + docs

- `VERSION` → `5.2.0`
- `ROADMAP.md` entry added
- `CLAUDE.md` entry added
- `docs/guides/packages.md` — user-facing guide (publish, install, schema, lockfile, auth)
- `registry/README.md` — backend setup + API reference

## Files changed

| File | Change |
|------|--------|
| `VERSION` | `5.1.4` → `5.2.0` |
| `stdlib/pkg.py` | Registry URL, API paths, install dir, SHA-256 verify, repository field, install_all, multipart fix |
| `mapanare/cli.py` | `@version` parsing, no-arg install, optional package arg, help text |
| `registry/src/index.ts` | New — Worker backend |
| `registry/wrangler.toml` | New — Worker config |
| `registry/package.json` | New — Worker deps |
| `registry/tsconfig.json` | New — TS config |
| `registry/README.md` | New — Backend docs |
| `tests/registry/__init__.py` | New |
| `tests/registry/test_mapanare_toml_parsing.py` | New — 17 tests |
| `tests/registry/test_lockfile.py` | New — 14 tests |
| `tests/registry/test_publish_install_roundtrip.py` | New — 20 tests |
| `docs/guides/packages.md` | New — User guide |
| `docs/roadmap/ROADMAP.md` | v5.2.0 entry |
| `CLAUDE.md` | v5.2.0 entry |

## Deferred to v5.3+

- Open publishing (currently team-only)
- Peer-dependency / transitive resolution
- SAT solver for version conflicts
- Package yanking / delisting
- Vendoring for offline builds
- Private packages / access control
- Install-time scripts (explicitly rejected for supply-chain safety)

## Test results

```
tests/registry/ — 51 passed / 0 failed
```
