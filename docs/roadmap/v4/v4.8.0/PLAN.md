# Mapanare v4.8.0 — Language Evolution (Post-Refactor)

> The foundation is solid. Now build the future.

**Status:** TODO
**Breaking:** Yes (new language features)
**Prerequisite:** v4.7.0 (entire refactor sequence complete)

---

## What Changed

The v4.2.0-v4.7.0 refactor delivered:

- **v4.2.0** — Deleted ~8,500 lines of dead emitter code, single pipeline
- **v4.3.0** — Drop glue works for all types, return-value escape analysis
- **v4.4.0** — Thread-safe signals, atomic counters, COW audit, agent lifecycle
- **v4.5.0** — UNKNOWN split, self-hosted semantic + verifier wired
- **v4.6.0** — Hardcoded tables removed, MIRType enum, workarounds fixed
- **v4.7.0** — Unified fixpoint optimizer, self-hosted constant propagation

The compiler is now correct, clean, and fast. New features can be added with
confidence that the foundation won't break under them.

---

## Candidate Features (prioritize at v4.8.0 planning time)

### Compile-Time Tensor Shapes

- `Tensor<Float>[M, K] @ Tensor<Float>[K, N]` — shape mismatch is a compile error
- Requires `const` keyword for static dimension expressions
- Connects semantic analyzer to `gpu_tensor_*` builtins
- Prevents GPU crashes from shape mismatches

### `const` Keyword

- Compile-time constants in grammar and semantic checker
- `const N: Int = 100` — value known at compile time
- Enables static tensor dimensions, compile-time array sizes
- Foundation for const generics in the future

### `@gpu` Auto-Kernel Extraction

- Decorator on a function → automatic kernel extraction
- Detect parallelizable loops → generate PTX/SPIR-V
- Wire through MIR GpuKernel metadata → LLVM codegen
- Graceful CPU fallback when no GPU available

### Reactive Async

- Tie async/await natively into Mapanare Streams
- Cooperative scheduling on the event loop
- `async fn fetch(url: String) -> Result<String, Error>`
- Streams as async iterators: `for await item in stream:`

### Auto-Generated FFI Bindings

- `mapanare build mylib.mn --lib --bindings`
- Generates `.pyi` (Python), `.d.ts` (TypeScript), Go wrappers
- From exported function signatures in the compiled `.so`/`.dylib`
- Zero-friction adoption: accelerate hot paths without rewriting

### Distributed Agent Routing

- Actor-model routing for `@Agent` across processes/machines
- Location-transparent `send` — agents can be local or remote
- Supervision trees span multiple nodes
- Foundation for distributed Mapanare applications

---

## Planning Process

At v4.8.0 planning time:

1. Review the candidate list above
2. Evaluate: which feature has the highest user impact?
3. Consider dependencies: `const` must come before tensor shapes
4. Scope to 1-2 features per version
5. Write a full PLAN.md with phases and exit criteria

**Do not plan v4.8.0 in detail until v4.7.0 is complete.** The refactor may
surface new priorities.
