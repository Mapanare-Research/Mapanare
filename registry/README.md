# Mapanare Package Registry

Cloudflare Workers + R2 backend for `mapanare install` / `mapanare publish`.

## Setup

```bash
cd registry
npm install

# Create KV namespaces
wrangler kv:namespace create TOKENS
wrangler kv:namespace create PACKAGE_INDEX

# Update wrangler.toml with the returned namespace IDs

# Set secrets
wrangler secret put GITHUB_CLIENT_ID
wrangler secret put GITHUB_CLIENT_SECRET

# Create R2 bucket
wrangler r2 bucket create mapanare-packages
```

## Deploy

```bash
npm run deploy
```

## Local development

```bash
npm run dev
```

## API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/v1/packages` | No | List all packages |
| `GET` | `/v1/packages/:name` | No | Package metadata + versions |
| `GET` | `/v1/packages/:name/:version` | No | Single version metadata |
| `GET` | `/v1/packages/:name/:version/tar` | No | Download tarball |
| `POST` | `/v1/packages` | Bearer | Publish a package |
| `GET` | `/v1/search?q=...` | No | Substring search |
| `GET` | `/auth/github?session=...` | No | Start GitHub OAuth |
| `GET` | `/auth/callback` | No | GitHub OAuth callback |
| `GET` | `/auth/poll?session=...` | No | Poll for auth completion |

## Publishing (MVP)

Publishing is restricted to members of the `Mapanare-Research` GitHub org.
Open publishing is planned for v5.3+.
