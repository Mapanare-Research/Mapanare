# Mapanare for Python Developers

You know Python. Here's how Mapanare maps to concepts you already understand.

---

## Key Differences at a Glance

| Python | Mapanare |
|--------|----------|
| Dynamic typing | Static typing with inference |
| `def` | `fn` |
| `class` | `struct` + `impl` (no inheritance) |
| `None` | `Option<T>` — explicit, checked |
| Exceptions | `Result<T, E>` + `?` operator |
| `asyncio.Task` | `agent` (built-in actors) |
| `list`, `dict` | `List<T>`, `Map<K, V>` |
| f-strings `f"{x}"` | `"${x}"` interpolation |
| Indentation-based | Brace-based `{ }` |
| Mutable by default | Immutable by default (`let mut` for mutable) |

## Variables

```python
# Python
x = 42
name: str = "Alice"
x = 100  # reassign freely
```

```mn
// Mapanare
let x = 42              // immutable
let name: String = "Alice"
let mut x = 42           // mutable
x = 100                  // OK
```

## Functions

```python
# Python
def add(a: int, b: int) -> int:
    return a + b
```

```mn
// Mapanare
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

## Structs Instead of Classes

```python
# Python
@dataclass
class Point:
    x: float
    y: float

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5
```

```mn
// Mapanare
struct Point { x: Float, y: Float }

impl Point {
    fn magnitude(self) -> Float {
        return (self.x * self.x + self.y * self.y)
    }
}
```

## Error Handling

```python
# Python
try:
    result = int("bad")
except ValueError as e:
    print(f"Error: {e}")
```

```mn
// Mapanare — no exceptions, use Result
fn parse(s: String) -> Result<Int, String> {
    // ...
}

match parse("bad") {
    Ok(v) => print(str(v)),
    Err(e) => print("Error: ${e}"),
}

// Or propagate with ?
let v = parse("42")?
```

## Concurrency

```python
# Python
async def worker(data):
    return data.upper()

async def main():
    task = asyncio.create_task(worker("hello"))
    result = await task
```

```mn
// Mapanare — agents are built-in actors
agent Worker {
    input data: String
    output result: String
    fn handle(data: String) -> String {
        return data.to_upper()
    }
}

let w = spawn Worker()
w.data <- "hello"
let result = sync w.result
```

## Collections

```python
# Python
items = [1, 2, 3]
config = {"host": "localhost", "port": "8080"}
```

```mn
// Mapanare
let items: List<Int> = [1, 2, 3]
let config = #{ "host": "localhost", "port": "8080" }
```

## Pattern Matching

```python
# Python 3.10+
match command:
    case "quit":
        exit()
    case "hello":
        print("Hi!")
    case _:
        print("Unknown")
```

```mn
// Mapanare
match command {
    "quit" => exit(),
    "hello" => print("Hi!"),
    _ => print("Unknown"),
}
```

## What You Gain

- **Compile-time type safety** — catch bugs before running
- **No `None` surprises** — `Option<T>` forces explicit handling
- **Native performance** — LLVM backend is 20-60x faster than Python
- **Built-in concurrency** — agents, signals, streams as language primitives
- **String interpolation** — `"${expr}"` just like f-strings but cleaner

## What's Different

- No inheritance — use traits for polymorphism
- No exceptions — use `Result<T, E>` and `?`
- Immutable by default — use `let mut` when you need mutation
- Types required on function signatures (inferred elsewhere)
