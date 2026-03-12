# Mapanare for Rust Developers

You know Rust. Here's what's familiar and what's different in Mapanare.

---

## Familiar Concepts

| Rust | Mapanare | Notes |
|------|----------|-------|
| `enum` + `match` | `enum` + `match` | Nearly identical semantics |
| `Result<T, E>` | `Result<T, E>` | Same concept, same `?` operator |
| `Option<T>` | `Option<T>` | `Some(v)` / `none` |
| `struct` | `struct` | Product types with named fields |
| `impl` blocks | `impl` blocks | Methods on types |
| `trait` | `trait` | Shared behavior interfaces |
| `let` / `let mut` | `let` / `let mut` | Immutable by default |
| Pattern matching | Pattern matching | Exhaustive on enums |

## Key Differences

| Rust | Mapanare |
|------|----------|
| Ownership + borrowing | No ownership model (arena memory in LLVM, GC in Python backend) |
| `fn main()` required | Top-level statements auto-wrapped in main |
| `String` vs `&str` | Single `String` type |
| `Vec<T>` | `List<T>` |
| `HashMap<K, V>` | `Map<K, V>` with `#{ k: v }` literals |
| `tokio::spawn` | `spawn Agent()` — built-in actors |
| `async/await` | `sync` + agents — no colored functions |
| Lifetimes | Not needed |
| Macros | Decorators (`@name`) |
| Cargo | `mapanare init/install/publish` |

## Side-by-Side

### Enums and Pattern Matching

```rust
// Rust
enum Shape {
    Circle(f64),
    Rect(f64, f64),
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r) => std::f64::consts::PI * r * r,
        Shape::Rect(w, h) => w * h,
    }
}
```

```mn
// Mapanare
enum Shape {
    Circle(Float),
    Rect(Float, Float),
}

fn area(s: Shape) -> Float {
    match s {
        Circle(r) => 3.14159 * r * r,
        Rect(w, h) => w * h,
    }
}
```

### Error Handling

```rust
// Rust
fn parse(s: &str) -> Result<i64, String> {
    s.parse().map_err(|e| e.to_string())
}

fn process() -> Result<i64, String> {
    let n = parse("42")?;
    Ok(n * 2)
}
```

```mn
// Mapanare — same pattern
fn process() -> Result<Int, String> {
    let n = parse("42")?
    return Ok(n * 2)
}
```

### Concurrency

```rust
// Rust (tokio)
let handle = tokio::spawn(async { worker(data).await });
let result = handle.await?;
```

```mn
// Mapanare — agents, not async/await
agent Worker {
    input data: String
    output result: String
    fn handle(data: String) -> String { return data }
}

let w = spawn Worker()
w.data <- "hello"
let result = sync w.result
```

## What You Gain

- **No borrow checker** — simpler mental model for concurrent code
- **Built-in actors** — agents replace manual async + channels
- **Reactive signals** — automatic dependency tracking
- **Faster iteration** — Python backend for development, LLVM for production
- **String interpolation** — `"${expr}"` instead of `format!("{}", expr)`

## What You Give Up

- No ownership/borrowing guarantees (memory safety via arena allocation instead)
- No zero-cost abstractions at the Rust level
- Smaller ecosystem (but Python interop bridges the gap)
