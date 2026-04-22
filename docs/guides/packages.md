# Package Management

Mapanare has a built-in package manager backed by the
[Mapanare Package Registry](https://registry.mapanare.dev).

## Quick start

```bash
# Install a package
mapanare install json@1.0.0

# Install latest version
mapanare install json

# Install all dependencies from mapanare.toml
mapanare install
```

## `mapanare.toml`

Every Mapanare project has a `mapanare.toml` manifest:

```toml
[package]
name = "myapp"
version = "0.1.0"
description = "My application"
license = "MIT"
repository = "https://github.com/user/myapp"
entry = "main.mn"

[dependencies]
json = "^1.0.0"
http-server = "~2.0.0"
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Package name (lowercase, alphanumeric + hyphens) |
| `version` | Yes | Semver version (e.g. `1.2.3`) |
| `description` | No | Short description |
| `license` | No | SPDX license identifier |
| `repository` | No | Source repository URL |
| `entry` | No | Entry point (default: `main.mn`) |
| `authors` | No | List of author names |
| `mapanare_version` | No | Required Mapanare version |

## Version constraints

Dependencies use semver constraints:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `^1.2.3` | `>=1.2.3, <2.0.0` | Compatible updates |
| `~1.2.3` | `>=1.2.3, <1.3.0` | Patch updates only |
| `>=1.0.0` | At least 1.0.0 | Minimum version |
| `>=1.0.0,<2.0.0` | Range | Between two versions |
| `1.2.3` | Exactly 1.2.3 | Pinned |
| `*` | Any version | Latest |

## Installing packages

```bash
# Specific version
mapanare install dato@0.1.0

# Latest compatible version
mapanare install dato

# From a git repository (fallback)
mapanare install mylib --git https://github.com/user/mylib.git

# All dependencies from mapanare.toml
mapanare install
```

Packages are downloaded to `mn_modules/<name>-<version>/` in your
project directory. The resolved versions are recorded in `mapanare.lock`.

### SHA-256 verification

Every download is verified against the registry's SHA-256 checksum.
If the checksum doesn't match, the install fails. This prevents
supply-chain tampering.

## `mapanare.lock`

The lockfile records exactly which versions were installed:

```json
{
  "lockfile_version": 1,
  "packages": [
    {
      "name": "json",
      "version": "1.0.0",
      "git": "https://registry.mapanare.dev/v1/packages/json/1.0.0/tar",
      "commit": "sha256:abc123...",
      "integrity": "sha256:def456..."
    }
  ]
}
```

Commit the lockfile to version control. When `mapanare install` finds
a lockfile, it uses the pinned versions for reproducible builds.

## Publishing packages

### Authentication

```bash
# Authenticate via GitHub OAuth
mapanare login
```

This opens a browser for GitHub authentication. Your token is saved
to `~/.mapanare/token`.

### Publish

```bash
# Publish with auto-patch bump (0.1.0 -> 0.1.1)
mapanare publish

# Publish with minor bump
mapanare publish --minor

# Publish without version bump
mapanare publish --no-bump

# Provide token inline
mapanare publish --token <your-token>
```

The publish command:
1. Reads `mapanare.toml` for package metadata
2. Builds a `.tar.gz` archive of your project
3. Computes SHA-256 checksum
4. Uploads to `registry.mapanare.dev`

### What gets published

- `mapanare.toml`
- All `.mn` source files
- `README.md`, `LICENSE`

Excluded: `mn_modules/`, hidden directories, `__pycache__/`,
`node_modules/`.

## Searching

```bash
mapanare search json
mapanare search --keyword data
```

## Creating a new project

```bash
mapanare init myproject
cd myproject
mapanare install http-server
```

This creates a `mapanare.toml` and `main.mn` scaffold.

## Registry API

The registry is at `https://registry.mapanare.dev` with these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/packages` | List all packages |
| `GET` | `/v1/packages/:name` | Package info + versions |
| `GET` | `/v1/packages/:name/:version` | Version details |
| `GET` | `/v1/packages/:name/:version/tar` | Download tarball |
| `POST` | `/v1/packages` | Publish (auth required) |
| `GET` | `/v1/search?q=...` | Search packages |

## Environment variables

| Variable | Description |
|----------|-------------|
| `MAPANARE_REGISTRY_URL` | Override registry URL (default: `https://registry.mapanare.dev`) |
| `MAPANARE_TOKEN` | API token (alternative to `~/.mapanare/token`) |
