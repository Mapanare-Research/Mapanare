# Mapanare v4.1.0 — Ecosystem Infrastructure

> The compiler is done. Now make the ecosystem work like a real language toolchain.

**Status:** IN PROGRESS
**Breaking:** No
**Prerequisite:** v4.0.0

---

## What v4.1.0 Delivers

The v4.0.0 compiler is production-quality. But a language is more than a compiler.
v4.1.0 builds the infrastructure that real users need: persistent package registry,
web login, download page, version manager, and native binary distribution.

---

## Phase 1: Package Registry + Web Login (Week 1-2)

> Fix the #1 user-facing bug (packages disappear) and add web authentication.

### 1A. PostgreSQL Connection Reliability

- [x] Replace bare `psycopg2.connect()` with `ThreadedConnectionPool(1, 5)`
- [x] Add retry logic: 3 attempts, 1s backoff, pool reinit on failure
- [x] Move DDL initialization to one-time `init_db()` at startup
- [x] Add `GET /api/health` endpoint (SELECT 1 against pool)
- [x] Add `users` table to DDL (PostgreSQL + SQLite)

**Files:** `registry.py`, `server.py`

### 1B. Web Login via GitHub OAuth

- [x] `GET /auth/web-login` — initiates OAuth with `web:` state prefix
- [x] Modified `/auth/callback` — detects web flow, sets signed `mn_session` cookie (HMAC-SHA256, 30-day expiry)
- [x] `GET /auth/me` — reads cookie, returns `{username, avatar_url, is_authenticated}`
- [x] `POST /auth/logout` — clears cookie
- [x] `_upsert_user()` — insert/update user record on login
- [x] `SESSION_SECRET` env var in `render.yaml`

**Files:** `auth.py`, `render.yaml`

### 1C. Frontend Auth + Navbar

- [x] `useAuth()` hook — fetches `/auth/me`, exposes user/logout
- [x] Navbar: Login button (logged out) / avatar + dropdown (logged in)
- [x] Navbar: "Download" link added to navigation

**Files:** `src/hooks/useAuth.ts` (new), `src/components/Navbar.tsx`

### 1D. Account Dashboard

- [x] `/dashboard` route — My Packages table, token management info
- [x] Fetches `GET /api/packages?author=<username>`
- [x] Protected: redirects to login if not authenticated

**Files:** `src/pages/Dashboard.tsx` (new), `src/App.tsx`

### 1E. Package Download Button + Download Page

- [x] Download button on PackageDetail page (links to `/api/packages/{name}/{version}/download`)
- [x] `/download` page — platform auto-detection, copy-to-clipboard install commands, version pinning, pip, build-from-source

**Files:** `src/pages/PackageDetail.tsx`, `src/pages/Download.tsx` (new), `src/App.tsx`

---

## Phase 2: Cross-Platform Installers (Week 3-4)

> Install scripts that pin versions, and native compiler binaries in CI.

### 2A. Install Script Version Pinning

- [ ] `packaging/install.sh` — add `--version` and `--install-dir` argument parsing
- [ ] `packaging/install.ps1` — add `-Version` parameter
- [ ] Enable: `curl ... | bash -s -- --version 4.0.0`

### 2B. Native Compiler Distribution in CI

- [ ] New `build-native` job in `publish.yml`: build `mnc` binary (not PyInstaller) on 3 platforms
- [ ] Uses `build_stage1.py` → stage2 self-compile → clang link → ~3MB binary
- [ ] Upload `mnc-linux-x64`, `mnc-darwin-arm64`, `mnc-win-x64.exe` to GitHub Release
- [ ] New `checksums` job: SHA256SUMS.txt for all release artifacts

### 2C. Cross-Platform Seed Binaries

- [ ] Build seed binaries for darwin-arm64 and windows-x64 in CI
- [ ] Update `build_from_seed.sh` case statement for new platforms
- [ ] Store seeds in `bootstrap/seed/{platform}/`

---

## Phase 3: Version Manager — `mapanare-up` (Week 5-6)

> pyenv-style version management with `.mapanare-version` per-project pinning.

### 3A. Shell Scripts

- [ ] `packaging/mapanare-up.sh` (~300 lines) — `install`, `list`, `default`, `use`, `update`, `uninstall`
- [ ] `packaging/mapanare-shim.sh` (~30 lines) — walks up dirs for `.mapanare-version`, falls back to `~/.mapanare/default`
- [ ] `packaging/mapanare-up.ps1` — Windows equivalent

### 3B. Directory Layout

```
~/.mapanare/
  bin/mapanare        ← shim (resolves version, dispatches)
  bin/mapanare-up     ← version manager
  bin/mnc             ← shim for native compiler
  versions/4.0.0/     ← actual binaries
  versions/4.1.0/
  default             ← file containing default version
```

### 3C. Integration

- [ ] `install.sh` installs `mapanare-up` + shim alongside compiler
- [ ] Adds `~/.mapanare/bin` to PATH in `.bashrc`/`.zshrc`
- [ ] Download page updated with version manager instructions

---

## Phase 4: CI Release Pipeline (Week 6-7)

> Staged releases, checksums, and proper release automation.

- [ ] Staged releases: `v4.1.0-beta.1` (pre-release) vs `v4.1.0` (stable)
- [ ] `--channel beta` flag in install scripts
- [ ] SHA256 checksums for all artifacts
- [ ] macOS code signing (deferred — requires Apple Developer account)

---

## Phase 5: Blog + Docs (Week 7)

> Tutorial content and documentation for the new infrastructure.

- [ ] Blog: "Transpile Python to Native: 68x Faster" tutorial
- [ ] Blog: "Getting Started with GPU Compute" tutorial
- [ ] New doc page: `/docs/package-manager`
- [ ] New doc page: `/docs/version-manager`
- [ ] Audit all existing doc pages for v4.0.0 accuracy

---

## Exit Criteria

1. Published packages persist across Render redeploys
2. Web login works: GitHub OAuth → avatar in navbar → dashboard
3. Download page live with platform detection
4. `mapanare-up install latest` works on Linux/macOS/Windows
5. `.mapanare-version` file auto-selects correct compiler version
6. Native `mnc` binaries in GitHub Releases alongside PyInstaller bundles
7. SHA256 checksums for all release artifacts
