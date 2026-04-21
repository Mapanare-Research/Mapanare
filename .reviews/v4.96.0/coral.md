# Coral — Language Design Review (Arc 13)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### Async model comparison

| Feature | Mapanare | Go | Rust | Swift |
|---------|----------|-----|------|-------|
| Async function | `async fn` | N/A (goroutines) | `async fn` | `async` |
| Await | `await expr` | `<-chan` | `.await` | `await expr` |
| Spawn | `spawn(f())` | `go f()` | `tokio::spawn(f())` | `Task { f() }` |
| Block from sync | `block_on(f())` | implicit | `tokio::block_on(f())` | N/A |
| Scheduler | Work-stealing | GMP runtime | Tokio work-stealing | GCD/cooperative |

Mapanare's model is closest to Rust/Tokio with the key simplification that `block_on` is a builtin (not a library function) and the scheduler is built into the runtime (not pluggable). For a language targeting AI/agent workloads, this is the right level of abstraction — users shouldn't need to choose a runtime.

### Multi-threaded model intuitiveness

The model is implicit multi-threading: `spawn()` enqueues a task, the scheduler distributes across N threads, `await` suspends and yields. The user doesn't see threads directly. This is the Go model (goroutines hide threads) adapted for coroutines.

**Potential confusion:** In Go, goroutines are always concurrent. In Mapanare, `async fn` without `spawn` runs sequentially (driven by the caller's `await`). Only `spawn` creates true concurrency. This distinction is subtle but correct — it matches Rust's model where `async fn` is lazy until driven.

### StringBuilder as a language feature

`sb_create()`, `sb_append()`, `sb_to_string()` are free functions (builtins), not methods on a type. This is functional but doesn't feel native to Mapanare's object-oriented surface. In a future version, `StringBuilder` should be a first-class struct with method syntax:
```mapanare
let sb = StringBuilder()
sb.append("hello")
sb.append(" world")
let s = sb.to_string()
```

The current free-function API works and is correct, but the future method syntax would be more idiomatic.

### String concat in loops

The automatic `string_concat_optimization` MIR pass is a nice touch — it detects the pathological pattern and rewrites it without user intervention. Even if the detection is conservative (only fires inside natural loops), it eliminates the most common case. Users who need more control have the explicit `sb_*` API.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| StringBuilder as a first-class struct type | MEDIUM | Methods instead of free functions |
| Document spawn vs await concurrency semantics | LOW | Subtle distinction worth explaining |

## Score justification

9/10 — the async model is clean, intuitive, and competitive with Go/Rust. StringBuilder is functional if not yet idiomatic. The implicit multi-threading model is the right abstraction for the target audience.
