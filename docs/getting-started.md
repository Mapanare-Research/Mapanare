# Getting Started with Mapanare

**15 minutes to your first agent pipeline.**

Mapanare (pronounced *mah-pah-NAH-reh*) is an AI-native compiled language where agents, signals, streams, and pipes are first-class primitives — not libraries.

This tutorial takes you from zero to a working multi-agent pipeline. Every code sample here compiles and runs.

---

## Install

### From source (recommended for now)

```bash
git clone https://github.com/Mapanare-Research/Mapanare.git
cd Mapanare
pip install -e ".[dev]"
```

Requires Python 3.11+.

### Verify

```bash
mapanare --version
```

---

## 1. Hello, World

Create a file called `hello.mn`:

```mn
fn main() {
    print("Hello, Mapanare!")
}
```

Run it:

```bash
mapanare run hello.mn
```

Output:

```
Hello, Mapanare!
```

`print` prints with a trailing newline. `println` is deprecated — use `print` instead.

---

## 2. Variables and Types

Mapanare is statically typed with type inference. Variables are immutable by default.

```mn
fn main() {
    let name = "World"
    let x: Int = 42
    let pi: Float = 3.14159
    let active: Bool = true

    print("Hello, " + name + "!")
    print("x = " + str(x))
    print("pi = " + str(pi))

    // Mutable variables use 'let mut'
    let mut count: Int = 0
    count += 1
    print("count = " + str(count))
}
```

Key points:
- `let` declares an immutable binding
- `let mut` declares a mutable binding
- Types can be inferred or annotated explicitly
- `str()` converts values to strings

---

## 3. Functions

Functions use `fn`, with type annotations on parameters and return values.

```mn
fn add(a: Int, b: Int) -> Int {
    return a + b
}

fn greet(name: String) -> String {
    return "Hello, " + name + "!"
}

fn main() {
    print(str(add(3, 4)))
    print(greet("Mapanare"))
}
```

Output:

```
7
Hello, Mapanare!
```

---

## 4. Control Flow

### If/else

```mn
fn classify(n: Int) -> String {
    if n < 0 {
        return "negative"
    } else if n == 0 {
        return "zero"
    } else {
        return "positive"
    }
}

fn main() {
    print(classify(-5))
    print(classify(0))
    print(classify(42))
}
```

### While loops

```mn
fn main() {
    let mut i: Int = 0
    while i < 5 {
        print(str(i))
        i += 1
    }
}
```

### For loops

```mn
fn main() {
    // Exclusive range: 0, 1, 2, 3, 4
    for i in 0..5 {
        print(str(i))
    }

    // Inclusive range: 1, 2, 3, 4, 5
    let mut sum: Int = 0
    for i in 1..=5 {
        sum += i
    }
    print("sum = " + str(sum))

    // Iterate over a list
    let items = [10, 20, 30]
    for item in items {
        print(str(item))
    }
}
```

---

## 5. Structs

No classes, no inheritance. Structs hold data.

```mn
struct Point {
    x: Float,
    y: Float
}

fn distance(p: Point) -> Float {
    return (p.x * p.x + p.y * p.y)
}

fn main() {
    let p = Point(3.0, 4.0)
    print("x = " + str(p.x))
    print("y = " + str(p.y))
    print("distance squared = " + str(distance(p)))
}
```

---

## 6. Enums and Pattern Matching

Enums can carry data. Pattern matching destructures them.

```mn
enum Shape {
    Circle(Float),
    Rect(Float, Float)
}

fn area(s: Shape) -> Float {
    match s {
        Shape_Circle(r) => { return 3.14159 * r * r },
        Shape_Rect(w, h) => { return w * h },
        _ => { return 0.0 }
    }
    return 0.0
}

fn main() {
    let c = Shape_Circle(5.0)
    let r = Shape_Rect(3.0, 4.0)
    print("circle area = " + str(area(c)))
    print("rect area = " + str(area(r)))
}
```

> **Note:** Enum variants use the `EnumName_VariantName(...)` syntax for both construction and pattern matching.

Match also works on plain values:

```mn
fn describe(n: Int) -> String {
    match n {
        1 => { return "one" },
        2 => { return "two" },
        3 => { return "three" },
        _ => { return "other" }
    }
    return "unreachable"
}

fn main() {
    print(describe(1))
    print(describe(99))
}
```

---

## 7. Lists

```mn
fn main() {
    let mut items: List<Int> = []
    items.push(10)
    items.push(20)
    items.push(30)

    print("length = " + str(items.length()))
    print("first = " + str(items[0]))

    let mut total: Int = 0
    for item in items {
        total += item
    }
    print("total = " + str(total))
}
```

---

## 8. Error Handling: Result and Option

No exceptions. Mapanare uses `Result<T, E>` and `Option<T>` for error handling.

### Result

```mn
fn divide(a: Int, b: Int) -> Result<Int, String> {
    if b == 0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}

fn main() {
    let r1 = divide(10, 2)
    match r1 {
        Ok(v) => { print("result = " + str(v)) },
        Err(e) => { print("error: " + e) }
    }

    let r2 = divide(10, 0)
    match r2 {
        Ok(v) => { print("result = " + str(v)) },
        Err(e) => { print("error: " + e) }
    }
}
```

Output:

```
result = 5
error: division by zero
```

### The `?` operator

The `?` operator propagates errors automatically:

```mn
fn might_fail(ok: Bool) -> Result<Int, String> {
    if ok {
        return Ok(42)
    }
    return Err("failed")
}

fn do_work() -> Result<Int, String> {
    let v = might_fail(true)?
    return Ok(v + 8)
}

fn main() {
    let r = do_work()
    print(str(r))
}
```

### Option

```mn
fn find_item(items: List<Int>, target: Int) -> Option<Int> {
    for i in 0..len(items) {
        if items[i] == target {
            return Some(items[i])
        }
    }
    return none
}

fn main() {
    let result = find_item([10, 20, 30], 20)
    match result {
        Some(v) => { print("found: " + str(v)) },
        _ => { print("not found") }
    }
}
```

---

## 9. Agents — Concurrent Actors

This is Mapanare's headline feature. Agents are concurrent actors with typed input/output channels.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

fn main() {
    let g = spawn Greeter()
    g.name <- "World"
    let msg = sync g.greeting
    print(msg)
    sync g.stop()
}
```

Output:

```
Hello, World!
```

Key concepts:
- `agent` defines a concurrent actor with `input` and `output` channels
- `spawn` creates and starts an agent instance
- `<-` sends a message to an agent's input channel
- `sync` blocks until a result is available on the output channel
- `sync agent.stop()` gracefully shuts down the agent

### Sending multiple messages

```mn
agent Doubler {
    input val: Int
    output result: Int

    fn handle(val: Int) -> Int {
        return val * 2
    }
}

fn main() {
    let d = spawn Doubler()
    d.val <- 21
    print(str(sync d.result))
    d.val <- 50
    print(str(sync d.result))
    sync d.stop()
}
```

Output:

```
42
100
```

---

## 10. Multi-Agent Pipelines

Chain agents together to build data processing pipelines.

```mn
agent Add10 {
    input val: Int
    output result: Int

    fn handle(val: Int) -> Int {
        return val + 10
    }
}

agent Double {
    input val: Int
    output result: Int

    fn handle(val: Int) -> Int {
        return val * 2
    }
}

fn main() {
    let a = spawn Add10()
    let d = spawn Double()

    // Pipeline: 5 -> Add10 -> Double
    a.val <- 5
    let mid = sync a.result
    d.val <- mid
    let final_val = sync d.result
    print(str(final_val))

    sync a.stop()
    sync d.stop()
}
```

Output:

```
30
```

(5 + 10) * 2 = 30.

### Named Pipes

Mapanare also has a `pipe` construct to declaratively compose agents:

```mn
agent Increment {
    input n: Int
    output n: Int

    fn handle(n: Int) -> Int {
        return n + 1
    }
}

agent Triple {
    input n: Int
    output n: Int

    fn handle(n: Int) -> Int {
        return n * 3
    }
}

pipe Transform {
    Increment |> Triple
}

fn main() {
    let result = sync Transform(10)
    print(str(result))
}
```

Output:

```
33
```

(10 + 1) * 3 = 33.

---

## 11. Signals — Reactive State

Signals are reactive containers. When a signal's value changes, computed signals that depend on it automatically recompute.

```mn
fn main() {
    let count = signal(0)
    let doubled = signal { count.value * 2 }

    print("doubled = " + str(doubled.value))

    count.value = 10
    print("doubled = " + str(doubled.value))
}
```

Output:

```
doubled = 0
doubled = 20
```

---

## 12. Streams — Async Pipelines

Streams are lazy async sequences with chainable operators.

```mn
fn main() {
    let s = stream([1, 2, 3, 4, 5])
    let result = s.map((x) => x * 2).filter((x) => x > 4)
    let collected = sync result.collect()
    print(str(collected))
}
```

Output:

```
[6, 8, 10]
```

Available stream operators: `.map()`, `.filter()`, `.fold()`, `.take()`, `.collect()`.

---

## Using the Standard Library

Mapanare ships with native stdlib modules written in `.mn`. Import them and compile to native binaries.

### HTTP Client

```mn
import net/http

fn main() {
    let response: HttpResponse = http::get("https://httpbin.org/get")
    if response.status == 200 {
        print(response.body)
    } else {
        print("Request failed: " + str(response.status))
    }
}
```

### JSON Parsing

```mn
import encoding/json

fn main() {
    let text: String = "{\"name\": \"Mapanare\", \"version\": 1}"
    let value: JsonValue = json::parse(text)

    match value {
        JsonValue::Object(obj) => {
            let name: JsonValue = json::get(obj, "name")
            print("Name: " + json::to_string(name))
        },
        _ => print("Expected object")
    }
}
```

### CSV Processing

```mn
import encoding/csv

fn main() {
    let data: String = "name,age\nAlice,30\nBob,25"
    let rows: List<List<String>> = csv::parse(data)
    for row in rows {
        print(row[0] + " is " + row[1])
    }
}
```

Compile any of these with `mapanare build <file>.mn` to produce a native binary.

---

## What's Next

- Read the [Language Specification](SPEC.md) for full syntax details
- Explore the [benchmarks](../benchmarks/cross_language/) to see Mapanare vs Python, Go, and Rust
- Check out the [compiler architecture](../README.md#compiler-architecture)
- Browse [RFCs](rfcs/) for upcoming language changes
- Join the [Discord](https://discord.gg/5hpGBm3WXf) community

---

*Built with care by the Mapanare team.*
