# Mapanare for TypeScript Developers

You know TypeScript. Here's how Mapanare compares.

---

## Familiar Concepts

| TypeScript | Mapanare |
|------------|----------|
| Static types with inference | Static types with inference |
| Generics `<T>` | Generics `<T>` |
| `interface` | `trait` |
| Arrow functions `=>` | Lambda `(x) => x + 1` |
| Template literals `` `${x}` `` | String interpolation `"${x}"` |
| `\|>` (TC39 proposal) | `\|>` pipe operator (built-in) |
| Union types | `enum` (tagged unions) |
| `null \| undefined` | `Option<T>` — explicit, no null |

## Key Differences

| TypeScript | Mapanare |
|------------|----------|
| Classes + inheritance | Structs + traits (no classes) |
| `try/catch` | `Result<T, E>` + `?` operator |
| `Promise/async/await` | `agent` + `spawn` + `sync` |
| npm/yarn | `mapanare install/publish` |
| Compiles to JS | Compiles to Python or LLVM native |
| `const`/`let` | `let`/`let mut` |

## Side-by-Side

### Types and Functions

```typescript
// TypeScript
function add(a: number, b: number): number {
    return a + b;
}

const greet = (name: string): string => `Hello, ${name}!`;
```

```mn
// Mapanare
fn add(a: Int, b: Int) -> Int {
    return a + b
}

let greet = (name) => "Hello, ${name}!"
```

### Interfaces → Traits

```typescript
// TypeScript
interface Printable {
    toString(): string;
}

class Point implements Printable {
    constructor(public x: number, public y: number) {}
    toString() { return `(${this.x}, ${this.y})`; }
}
```

```mn
// Mapanare
trait Printable {
    fn to_string(self) -> String
}

struct Point { x: Float, y: Float }

impl Printable for Point {
    fn to_string(self) -> String {
        return "(${str(self.x)}, ${str(self.y)})"
    }
}
```

### Union Types → Enums

```typescript
// TypeScript
type Result<T> = { ok: true; value: T } | { ok: false; error: string };
```

```mn
// Mapanare — built-in
enum Result<T, E> {
    Ok(T),
    Err(E),
}

// Already in the language — just use it:
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 { return Err("division by zero") }
    return Ok(a / b)
}
```

### Async → Agents

```typescript
// TypeScript
async function fetchData(url: string): Promise<string> {
    const res = await fetch(url);
    return res.text();
}
```

```mn
// Mapanare — agents are concurrent actors
agent Fetcher {
    input url: String
    output data: String
    fn handle(url: String) -> String {
        // process and return
        return "data"
    }
}

let f = spawn Fetcher()
f.url <- "https://example.com"
let data = sync f.data
```

### Pipe Operator

```typescript
// TypeScript (proposed)
const result = data |> transform |> validate |> format;
```

```mn
// Mapanare — built-in, works today
let result = data |> transform |> validate |> format
```

## What You Gain

- **No null/undefined** — `Option<T>` catches missing values at compile time
- **Native performance** — LLVM backend, not interpreted
- **Built-in concurrency** — agents instead of Promise chains
- **Reactive signals** — like RxJS observables, but in the language
- **Pattern matching** — exhaustive, on enums and values
- **Pipe operator** — available now, not a TC39 proposal

## What's Different

- No DOM, no browser APIs (Mapanare is a systems/AI language)
- No class inheritance — traits + structs instead
- No exceptions — `Result<T, E>` for all error handling
- Compiled, not transpiled to JS
