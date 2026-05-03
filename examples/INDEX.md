# Examples Index

Mapanare programs organized by feature category. Most examples
compile end-to-end via `python3 -m mapanare emit-llvm <file>` or
the native `mnc emit-llvm <file>`; runnable demos use `mnc run`.

## Terseness arc (Te.\*)

Showcases the v5.13–v5.21 terseness arc — the surface forms that
make Mapanare terser than Python on AI-domain workloads.

| Path | Feature | Source |
|---|---|---|
| `terseness/chained_cmp.mn` | Te.6 chained comparisons (`0 < x < 10`) | v5.21.0 |

## Struct ergonomics (Te.5)

Field shorthand, struct update (`..base`), let destructuring,
refutable-binding forms (if-let, while-let, let-else), and
bounded-generics with traits.

| Path | Feature | Source |
|---|---|---|
| `struct_ergo/generic_trait.mn` | Trait + impl + bounded generic `min<T: Comparable>` | SPEC §7.4 |

## Agents / signals / streams

First-class concurrency primitives.

- `signals/counter.mn` — minimal reactive signal demo.
- `ai/chat_agent.mn`, `ai/rag_agent.mn` — LLM-backed agents.

## Async I/O

Cooperative async file and HTTP demos. Doc references in
`docs/cookbook/async.md` and `docs/guides/async.md` keep these
at the top level.

- `async_file_io.mn` — async file pipeline.
- `async_http_demo.mn` — real HTTP GET via `net/http`.

## AI / LLM

| Path | Notes |
|---|---|
| `ai/basic_chat.mn` | one-shot chat completion |
| `ai/basic_stream.mn` | streamed completions |
| `ai/chat_agent.mn` | agent-shaped chat loop |
| `ai/rag_agent.mn` | retrieval-augmented chat (uses `ai/sample_docs/`) |

## Tensors / GPU

- `tensor/matrix_ops.mn` — basic tensor operations.
- `gpu/vector_add.mn`, `gpu/matmul_bench.mn` — GPU dispatch via `@gpu`.
- `experimental/gpu/` — exploratory GPU examples.

## CLI tooling

- `cli/todo.mn` — minimal todo CLI.
- `cli/word_count.mn` — `wc -l` clone.

## Networking

- `network/http_fetch.mn` — `net/http` GET client.

## WebAssembly

| Path | Target |
|---|---|
| `wasm/hello.mn` | smoke test (`wasm32-unknown-unknown`) |
| `wasm/wasi_app.mn` | WASI host (`wasm32-wasi`) |
| `wasm/dom_app.mn` | browser DOM via JS-interop bridge |
| `wasm/cloudflare-worker/` | Cloudflare Workers deployment |

## Mobile

- `experimental/mobile/android/app.mn` — Android NDK app.
- `experimental/mobile/ios/app.mn` — iOS app.

## FFI / Bindings

- `bind/math_lib.mn` — calling C from Mapanare via `extern`.

## Transpile / Python interop

- `transpile/*.mn` — Mapanare ↔ Python parity benchmarks.
- `python_to_native/*.py` — Python sources translated to Mapanare.

## Packages

- `packages/mn_collections/`, `packages/mn_http/`, `packages/mn_json/` — sample
  package layouts driven by `mapanare.toml`.
