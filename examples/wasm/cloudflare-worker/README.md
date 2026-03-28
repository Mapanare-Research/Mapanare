# Mapanare Cloudflare Worker Example

HTTP handler compiled from Mapanare to WASM, deployed to Cloudflare Workers edge network.

## Prerequisites

- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/) (`npm install -g wrangler`)
- Mapanare compiler with WASM backend

## Build

```bash
mapanare emit-wasm --binary worker.mn -o worker.wasm
```

## Local Development

```bash
wrangler dev
```

## Deploy

```bash
wrangler deploy
```

## Endpoints

| Path | Response |
|------|----------|
| `/` | Welcome message |
| `/health` | Health check |
| `/fib` | Fibonacci(30) computation |
| `/*` | 404 Not Found |

## Architecture

The Mapanare compiler emits WebAssembly from MIR (mid-level IR). The WASM module
exports `handle_request` which the JS glue code calls for each incoming HTTP
request. The worker runs on Cloudflare's edge network with sub-millisecond cold
start times.
