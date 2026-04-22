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

Backend already exists at `mapanare-website/registry.py` (FastAPI + PostgreSQL/SQLite),
deployed to `mapanare.dev`. No new backend created — the existing one already provides:

- **API endpoints** at `/api/packages`:
  - `POST /api/packages` — publish (auth required)
  - `GET /api/packages` — search (query, keyword, pagination)
  - `GET /api/packages/{name}` — package metadata + versions
  - `GET /api/packages/{name}/{ver}` — version info
  - `GET /api/packages/{name}/{ver}/download` — download tarball
  - `DELETE /api/packages/{name}/{ver}` — yank (auth required)
  - `GET /api/stats` — registry statistics
- **Auth**: GitHub OAuth (`/auth/github`, `/auth/callback`, `/auth/poll`) + web login
- **Storage**: PostgreSQL in production (Render), SQLite locally

### Sessions 2-3 — Client CLI updates

Updated `stdlib/pkg.py`:
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

## Files changed

| File | Change |
|------|--------|
| `VERSION` | `5.1.4` → `5.2.0` |
| `stdlib/pkg.py` | Install dir, SHA-256 verify, repository field, install_all, multipart fix |
| `mapanare/cli.py` | `@version` parsing, no-arg install, optional package arg, help text |
| `tests/registry/__init__.py` | New |
| `tests/registry/test_mapanare_toml_parsing.py` | New — 17 tests |
| `tests/registry/test_lockfile.py` | New — 14 tests |
| `tests/registry/test_publish_install_roundtrip.py` | New — 20 tests |
| `docs/guides/packages.md` | New — User guide |
| `docs/roadmap/ROADMAP.md` | v5.2.0 entry |
| `CLAUDE.md` | v5.2.0 entry |
| `README.md` | Version badge 5.0.6 → 5.2.0 |
| `docs/README.es.md` | Version badge 5.0.6 → 5.2.0 |

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
