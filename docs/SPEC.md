# Mapanare Language Specification

**Version:** 0.8.0
**Status:** Skeleton / Working Draft

Mapanare is an AI-native compiled programming language where agents, signals, streams, and tensors are first-class primitives -- not libraries. It compiles via Python transpilation first, then LLVM native.

---

## 1. Language Goals and Non-Goals

### Goals

- **AI-native primitives.** Agents, signals, streams, and tensors are built into the language, not imported from libraries. AI workflows are expressible without external frameworks.
- **Compiled.** Mapanare is always compiled. The initial backend transpiles to Python for rapid iteration; the production backend targets LLVM for native machine code.
- **Simple, familiar syntax.** The syntax draws from Rust (enums, pattern matching), TypeScript (type annotations, generics), and Python (readability, minimal ceremony).
- **Type-safe with inference.** Static types catch errors at compile time. Type inference reduces annotation burden -- you write types where they clarify, the compiler infers the rest.
- **Concurrency via agents and message passing.** No raw threads, no shared mutable state. Agents are concurrent actors that communicate through typed channels.
- **Reactive via signals.** Signals propagate changes automatically. Computed values recompute when their dependencies change, enabling declarative reactive dataflow.
- **Pipeline-oriented.** The `|>` pipe operator chains transformations naturally. Named pipelines compose agents into data-processing graphs.
- **ML-ready.** First-class `Tensor<T>[shape]` types with compile-time shape verification. Tensor operations are built in, not bolted on.

### Non-Goals

- **Not a general-purpose systems language.** Mapanare does not aim to replace C or Rust for kernel development, device drivers, or bare-metal programming.
- **Not interpreted.** All Mapanare code is compiled before execution. An interactive REPL exists (`mapanare repl`) but it compiles each input before evaluating.
- **No garbage collector in native mode.** The LLVM backend uses arena-based memory management with scope-level cleanup and tag-bit freeing for heap-allocated strings. The Python transpiler backend inherits Python's GC, but that is a transitional implementation detail.
- **No OOP class hierarchies.** There are no classes, no inheritance, no `extends`. Use agents for concurrent behavior and structs for data.
- **Not backwards-compatible with Python syntax.** Although Mapanare transpiles to Python, its syntax is its own. Valid Python is not valid Mapanare and vice versa.

---

## 2. Primitive Types

| Type | Description |
|---|---|
| `Int` | 64-bit signed integer. |
| `Float` | 64-bit IEEE 754 floating-point number. |
| `Bool` | Boolean value: `true` or `false`. |
| `String` | Immutable UTF-8 encoded string. |
| `Char` | Single Unicode scalar value (code point). |
| `Void` | Unit type representing the absence of a value. Functions with no meaningful return value return `Void`. |
| `Option<T>` | A value that is either `Some(value)` or `None`. Represents the possible absence of a value without null pointers. |
| `Result<T, E>` | A value that is either `Ok(value)` or `Err(error)`. Used for recoverable error handling. |
| `Tensor<T>[shape]` | N-dimensional array with element type `T` and compile-time verified shape. Example: `Tensor<Float>[3, 3]` is a 3x3 matrix of floats. |
| `List<T>` | Dynamically-sized ordered collection of elements of type `T`. |
| `Map<K, V>` | Hash map from keys of type `K` to values of type `V`. Keys must be hashable. |
| `Signal<T>` | Reactive container holding a value of type `T`. When the value changes, all dependents are notified and recomputed. |
| `Stream<T>` | Asynchronous iterable producing values of type `T` over time. Supports backpressure. |
| `Channel<T>` | Typed, bounded message channel for inter-agent communication. Carries values of type `T`. |

### Numeric Literals

```mn
let a: Int = 42
let b: Int = 1_000_000       // underscores for readability
let c: Float = 3.14
let d: Float = 1.0e-10       // scientific notation
let e: Int = 0xFF             // hexadecimal
let f: Int = 0b1010           // binary
let g: Int = 0o77             // octal
```

### String Literals

```mn
let s = "hello, world"
let multi = "line one\nline two"
let interpolated = "value is ${x}"   // string interpolation
let multiline = """
    This is a multi-line
    string literal
"""
```

String interpolation with `${expr}` is supported in both regular and triple-quoted strings.
Any valid expression can appear inside `${...}`, including function calls and binary operations:

```mn
let name = "world"
println("Hello, ${name}!")
println("sum: ${a + b}")
println("length: ${len(items)}")
```

---

## 3. Keywords

The following identifiers are reserved as keywords and cannot be used as variable or function names.

### Bindings and Mutability

| Keyword | Description |
|---|---|
| `let` | Declare an immutable variable binding. |
| `mut` | Declare a mutable variable binding: `let mut x = 0`. |

### Functions and Definitions

| Keyword | Description |
|---|---|
| `fn` | Define a function. |
| `return` | Return a value from a function. If omitted, the last expression is the return value. |
| `pub` | Mark a definition as publicly visible outside its module. |
| `self` | Reference to the current agent or struct instance within `impl` blocks. |

### Agents and Concurrency

| Keyword | Description |
|---|---|
| `agent` | Define an agent (concurrent actor with typed input/output channels). |
| `spawn` | Create and start a new agent instance. Returns a handle to the running agent. |
| `sync` | Await and retrieve an asynchronous result from an agent output or stream. |

### Reactive and Streaming

| Keyword | Description |
|---|---|
| `signal` | Declare a reactive signal binding. |
| `stream` | Declare a stream binding. |
| `pipe` | Define a named pipeline composing agents or functions via `\|>`. |

### Control Flow

| Keyword | Description |
|---|---|
| `if` | Conditional branch. |
| `else` | Alternative branch for `if`. |
| `match` | Pattern matching expression. Exhaustiveness is checked at compile time. |
| `for` | Loop over an iterable. |
| `in` | Used with `for` to specify the iterable: `for x in items { }`. |

### Types and Data

| Keyword | Description |
|---|---|
| `type` | Define a type alias: `type Name = String`. |
| `struct` | Define a data structure with named fields. |
| `enum` | Define an algebraic data type (tagged union / sum type). |
| `impl` | Implement methods on a struct, enum, or agent. |

### Modules

| Keyword | Description |
|---|---|
| `import` | Import definitions from another module. |
| `export` | Re-export definitions from the current module. |

### Literals

| Keyword | Description |
|---|---|
| `true` | Boolean literal for true. |
| `false` | Boolean literal for false. |
| `none` | The `None` variant of `Option<T>`, representing absence of a value. |

---

## 4. Operators

### Pipe Operator

| Operator | Name | Description |
|---|---|---|
| `\|>` | Pipe | Pass the result of the left-hand expression as the first argument to the right-hand function or agent. Enables left-to-right data flow. |

```mn
let result = data |> tokenize |> classify |> format
// Equivalent to: format(classify(tokenize(data)))
```

### Type and Function Operators

| Operator | Name | Description |
|---|---|---|
| `->` | Return type | Annotates the return type of a function: `fn foo() -> Int`. |
| `=>` | Arrow | Used in lambda expressions and match arms: `(x) => x + 1` or `Some(v) => v`. |
| `::` | Namespace | Access a namespaced item: `Math::sqrt`, `Option::Some`. |
| `@` | Decorator | Apply a compile-time annotation or decorator to a definition. |

### Arithmetic Operators

| Operator | Name | Description |
|---|---|---|
| `+` | Add | Addition for numeric types, concatenation for strings. |
| `-` | Subtract | Subtraction. Also unary negation: `-x`. |
| `*` | Multiply | Multiplication. |
| `/` | Divide | Division. Integer division for `Int`, floating-point division for `Float`. |
| `%` | Modulo | Remainder after integer division. |

### Comparison Operators

| Operator | Name | Description |
|---|---|---|
| `==` | Equal | Structural equality. |
| `!=` | Not equal | Structural inequality. |
| `<` | Less than | Ordering comparison. |
| `>` | Greater than | Ordering comparison. |
| `<=` | Less or equal | Ordering comparison. |
| `>=` | Greater or equal | Ordering comparison. |

### Logical Operators

| Operator | Name | Description |
|---|---|---|
| `&&` | Logical AND | Short-circuiting conjunction. |
| `\|\|` | Logical OR | Short-circuiting disjunction. |
| `!` | Logical NOT | Boolean negation. |

### Assignment Operators

| Operator | Name | Description |
|---|---|---|
| `=` | Assign | Assign a value to a mutable binding. |
| `+=` | Add-assign | `x += 1` is equivalent to `x = x + 1`. |
| `-=` | Subtract-assign | Compound subtraction assignment. |
| `*=` | Multiply-assign | Compound multiplication assignment. |
| `/=` | Divide-assign | Compound division assignment. |

### Other Operators

| Operator | Name | Description |
|---|---|---|
| `..` | Range | Create a range: `0..10` (exclusive end), `0..=10` (inclusive end). |
| `?` | Error propagation | Unwrap a `Result` or `Option`. If `Err` or `None`, return early from the enclosing function. Modeled after Rust's `?` operator. |
| `<-` | Send | Send a value into an agent's input channel: `agent.input <- value`. |

### Operator Precedence (Highest to Lowest)

| Precedence | Operators |
|---|---|
| 1 (highest) | `::` `@` `.` |
| 2 | `!` `-` (unary) |
| 3 | `*` `/` `%` |
| 4 | `+` `-` |
| 5 | `..` `..=` |
| 6 | `\|>` |
| 7 | `<` `>` `<=` `>=` |
| 8 | `==` `!=` |
| 9 | `&&` |
| 10 | `\|\|` |
| 11 | `?` |
| 12 | `=` `+=` `-=` `*=` `/=` `<-` |
| 13 (lowest) | `=>` |

---

## 5. Example Programs

### Example 1: Hello World

The minimal Mapanare program. Top-level statements are automatically wrapped in `main`.

```mn
print("Hello, Mapanare!")
```

**Behavior:** Prints `Hello, Mapanare!` to standard output and exits.

### Example 2: Agent Definition

Demonstrates defining an agent with typed input and output channels, spawning it, sending a message, and synchronously receiving a result.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

let greeter = spawn Greeter()
greeter.name <- "World"
let result = sync greeter.greeting
print(result)
```

**Behavior:** Spawns a `Greeter` agent, sends `"World"` to its `name` input channel, waits for the `greeting` output, and prints `Hello, World!`.

**Key concepts illustrated:**
- `agent` keyword defines a concurrent actor.
- `input` and `output` declare typed channels.
- `spawn` creates a running agent instance.
- `<-` sends a value into a channel.
- `sync` blocks until the output is available.
- Top-level statements are automatically wrapped in `fn main()` by the compiler.

### Example 3: Multi-Agent Pipeline

Demonstrates composing multiple agents into a named pipeline using the `pipe` keyword and `|>` operator.

```mn
agent Tokenizer {
    input text: String
    output tokens: List<String>

    fn handle(text: String) -> List<String> {
        return text.split(" ")
    }
}

agent Classifier {
    input tokens: List<String>
    output label: String

    fn handle(tokens: List<String>) -> String {
        if tokens.len() > 10 {
            return "long"
        }
        return "short"
    }
}

pipe ClassifyText {
    Tokenizer |> Classifier
}

let pipeline = spawn ClassifyText()
pipeline.text <- "Mapanare is an AI-native programming language"
let label = sync pipeline.label
print(label)
```

**Behavior:** Defines two agents (`Tokenizer` and `Classifier`), composes them into a pipeline called `ClassifyText`, feeds in a sentence, and prints the classification label `short`.

**Key concepts illustrated:**
- `pipe` defines a named agent pipeline.
- `|>` connects the output of one agent to the input of the next.
- The pipeline itself is spawned and used like a single agent.
- Input goes to the first agent in the chain; output comes from the last.

---

## 6. Type System

### Static Typing with Inference

Mapanare is statically typed. Every expression has a known type at compile time. The compiler uses local type inference to reduce annotation burden.

```mn
let x = 42              // inferred as Int
let y = 3.14            // inferred as Float
let z: String = "hello" // explicitly annotated
let flag = true         // inferred as Bool
```

Type annotations are required on function signatures (parameters and return types). They are optional on local bindings when the type can be inferred.

```mn
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

### Generic Types

Functions, structs, enums, and agents can be parameterized over types using angle-bracket syntax.

```mn
fn identity<T>(x: T) -> T {
    return x
}

let a = identity(42)       // T = Int
let b = identity("hello")  // T = String
```

```mn
struct Pair<A, B> {
    first: A,
    second: B,
}
```

### Option Type

`Option<T>` represents a value that may or may not be present. It replaces null pointers.

```mn
let x: Option<Int> = Some(42)
let y: Option<Int> = none

match x {
    Some(v) => print("Got: ${v}"),
    None    => print("Nothing"),
}
```

`Option` values must be explicitly unwrapped before use. There is no implicit null.

### Result Type

`Result<T, E>` represents an operation that can succeed with `Ok(value)` or fail with `Err(error)`. It is the primary error-handling mechanism.

```mn
fn parse_int(s: String) -> Result<Int, String> {
    // ...
}

let result = parse_int("42")
match result {
    Ok(n)  => print("Parsed: ${n}"),
    Err(e) => print("Error: ${e}"),
}
```

The `?` operator provides concise error propagation:

```mn
fn process(s: String) -> Result<Int, String> {
    let n = parse_int(s)?    // returns Err early if parse fails
    return Ok(n * 2)
}
```

### Type Aliases

```mn
type Name = String
type Matrix = Tensor<Float>[3, 3]
type Callback = fn(Int) -> Bool
```

### Struct Types

Structs are product types -- named collections of fields.

```mn
struct Point {
    x: Float,
    y: Float,
}

impl Point {
    fn distance(self, other: Point) -> Float {
        let dx = self.x - other.x
        let dy = self.y - other.y
        return Math::sqrt(dx * dx + dy * dy)
    }
}
```

### Enum Types (Algebraic Data Types)

Enums are sum types -- tagged unions where each variant can carry different data.

```mn
enum Shape {
    Circle(Float),
    Rectangle(Float, Float),
    Triangle(Float, Float, Float),
}

fn area(shape: Shape) -> Float {
    match shape {
        Circle(r)          => 3.14159 * r * r,
        Rectangle(w, h)    => w * h,
        Triangle(a, b, c)  => {
            let s = (a + b + c) / 2.0
            return Math::sqrt(s * (s - a) * (s - b) * (s - c))
        },
    }
}
```

Match expressions on enums must be exhaustive -- every variant must be handled, or a wildcard `_` arm must be present.

### Agent Types

Agents have typed input and output channels that form their public interface.

```mn
agent Counter {
    input increment: Int
    output count: Int

    let mut state: Int = 0

    fn handle(increment: Int) -> Int {
        self.state += increment
        return self.state
    }
}
```

When you `spawn` an agent, the returned handle exposes the input and output channels with their declared types.

### Tensor Types

Tensors have their element type and shape verified at compile time.

```mn
let v: Tensor<Float>[3] = [1.0, 2.0, 3.0]         // 1D vector, 3 elements
let m: Tensor<Float>[2, 3] = [[1.0, 2.0, 3.0],     // 2D matrix, 2x3
                               [4.0, 5.0, 6.0]]
let t: Tensor<Int>[2, 2, 2] = [[[1, 2], [3, 4]],   // 3D tensor
                                [[5, 6], [7, 8]]]
```

Shape mismatches are compile-time errors:

```mn
let a: Tensor<Float>[3] = [1.0, 2.0, 3.0]
let b: Tensor<Float>[4] = [1.0, 2.0, 3.0, 4.0]
let c = a + b   // COMPILE ERROR: shape mismatch [3] vs [4]
```

Matrix multiplication verifies dimensional compatibility:

```mn
let a: Tensor<Float>[2, 3] = ...
let b: Tensor<Float>[3, 4] = ...
let c = a @ b   // Result: Tensor<Float>[2, 4] -- inner dimensions must match
```

---

## 7. Agent Model

### Overview

Agents are the fundamental concurrency primitive in Mapanare. They are concurrent actors that encapsulate state, communicate exclusively through typed message channels, and run independently of each other. There is no shared mutable state between agents.

### Definition

```mn
agent MyAgent {
    input request: RequestType
    output response: ResponseType

    // Private state
    let mut counter: Int = 0

    // Handler: called when input is received
    fn handle(request: RequestType) -> ResponseType {
        self.counter += 1
        // process and return
    }

    // Lifecycle hooks (optional)
    fn on_init() { }
    fn on_stop() { }
}
```

### Spawning and Communication

```mn
let a = spawn MyAgent()           // create and start agent
a.request <- some_value            // send input (non-blocking)
let result = sync a.response       // receive output (blocking)
```

- `<-` sends a message to an agent's input channel. The send is non-blocking; the message is queued.
- `sync` blocks the current execution until the agent produces an output.

### Lifecycle

Every agent progresses through defined lifecycle states:

```
init --> running --> paused --> stopped
              |                   ^
              +-------------------+
```

| State | Description |
|---|---|
| `init` | Agent is created. `on_init()` is called. Resources are allocated. |
| `running` | Agent is processing messages from its input channels. |
| `paused` | Agent is temporarily suspended. Messages are buffered but not processed. |
| `stopped` | Agent has terminated. `on_stop()` is called. Resources are released. |

### Backpressure

When an agent's input buffer reaches capacity, the sending side is notified. The sender can:

- Block until space is available (default behavior with `sync`).
- Drop the message (configurable policy).
- Apply a timeout and fail with a `Result`.

Backpressure propagates through pipelines automatically.

### Supervision

Agents can be configured with restart policies for failure recovery:

```mn
let worker = spawn MyAgent() @restart(policy: "always", max: 3, window: 60)
```

| Policy | Behavior |
|---|---|
| `always` | Restart the agent on any failure, up to `max` times within `window` seconds. |
| `never` | Let the agent stay stopped on failure. |
| `transient` | Restart only on unexpected failures (not on normal exit). |

Supervision trees can be built by having agents spawn and monitor child agents.

---

## 8. Signal Model

### Overview

Signals are reactive primitives that hold a value and automatically propagate changes to dependents. They enable declarative, reactive dataflow without manual event wiring.

### Declaration

```mn
// Mutable signal: can be set directly
let mut count = signal(0)

// Computed signal: derived from other signals, read-only
let doubled = signal { count.value * 2 }

// Updating a signal
count.value = 5
print(doubled.value)   // prints 10
```

### Dependency Tracking

The compiler tracks which signals are read during the evaluation of a computed signal. When any dependency changes, the computed signal is marked dirty and recomputed on next access (lazy) or immediately (eager, configurable).

```mn
let mut a = signal(1)
let mut b = signal(2)
let sum = signal { a.value + b.value }

a.value = 10
print(sum.value)   // prints 12
```

### Change Stream

Every signal exposes a stream of its changes, bridging the reactive and streaming models:

```mn
let mut temperature = signal(20.0)

// Get a stream of changes
for change in temperature.changes() {
    print("Temperature changed to ${change}")
}
```

### Batched Updates

Multiple signal updates within a `batch` block are coalesced into a single recomputation pass, avoiding intermediate recalculations:

```mn
batch {
    x.value = 10
    y.value = 20
    z.value = 30
}
// Dependents recompute once, not three times
```

### Signals in Agents

Agents can expose signals as part of their interface, enabling reactive observation of agent state:

```mn
agent Thermometer {
    output temperature: Signal<Float>

    let mut temp = signal(20.0)

    fn handle(reading: Float) -> Signal<Float> {
        self.temp.value = reading
        return self.temp
    }
}
```

---

## 9. Stream Model

### Overview

Streams are asynchronous iterables that produce values over time. They are the primary abstraction for handling sequences of events, data chunks, and real-time feeds.

### Declaration and Usage

```mn
// Create a stream from values
let s = Stream::from([1, 2, 3, 4, 5])

// Consume a stream
for value in s {
    print(value)
}
```

### Stream Operators

Streams support a rich set of composable operators. These can be chained with the pipe operator.

| Operator | Description |
|---|---|
| `map(fn)` | Transform each element. |
| `filter(fn)` | Keep elements matching a predicate. |
| `flat_map(fn)` | Map each element to a stream, then flatten. |
| `take(n)` | Emit only the first `n` elements. |
| `skip(n)` | Skip the first `n` elements. |
| `chunk(n)` | Group elements into chunks of size `n`. |
| `zip(other)` | Pair elements from two streams. |
| `merge(other)` | Interleave elements from two streams. |
| `fold(init, fn)` | Reduce the stream to a single value. |
| `scan(init, fn)` | Like fold, but emits each intermediate accumulator. |
| `distinct()` | Remove consecutive duplicates. |
| `throttle(ms)` | Emit at most one element per time window. |
| `debounce(ms)` | Emit only after a quiet period. |

```mn
let result = numbers
    |> Stream::filter((n) => n % 2 == 0)
    |> Stream::map((n) => n * n)
    |> Stream::take(10)
    |> Stream::fold(0, (acc, n) => acc + n)
```

### Hot vs Cold Streams

| Kind | Behavior |
|---|---|
| **Cold** | Produces values on demand. Each subscriber gets its own independent sequence. Created from data or generators. |
| **Hot** | Produces values continuously regardless of subscribers. Subscribers see values from the point they subscribe. Examples: sensor feeds, user input, network events. |

```mn
// Cold stream: values produced per subscriber
let cold = Stream::from([1, 2, 3])

// Hot stream: shared, always producing
let hot = Stream::interval(1000)   // emits every 1000ms
```

### Backpressure

Streams have built-in backpressure. When a consumer processes values slower than the producer emits them, the producer is throttled automatically. This prevents memory overflow and ensures system stability.

Backpressure strategies:

| Strategy | Behavior |
|---|---|
| `buffer(n)` | Buffer up to `n` elements, then apply backpressure. |
| `drop_oldest` | Drop the oldest buffered element when full. |
| `drop_newest` | Drop the newest (incoming) element when full. |
| `error` | Raise an error when the buffer overflows. |

```mn
let controlled = fast_stream
    |> Stream::buffer(100, strategy: "drop_oldest")
```

### Stream Fusion

The compiler optimizes adjacent stream operators by fusing them into a single pass. This eliminates intermediate allocations and reduces overhead.

```mn
// These three operators are fused into a single iteration:
let result = data
    |> Stream::filter((x) => x > 0)
    |> Stream::map((x) => x * 2)
    |> Stream::take(100)
```

The compiler guarantees that fusion does not change observable behavior.

### Streams and Agents

Agent output channels are streams. This means you can apply all stream operators to agent outputs:

```mn
let sensor = spawn TemperatureSensor()

sensor.readings
    |> Stream::filter((t) => t > 100.0)
    |> Stream::throttle(5000)
    |> Stream::map((t) => "ALERT: ${t} degrees")
    |> Stream::for_each((msg) => notify(msg))
```

---

## 10. Testing

### Built-in Test Runner

Mapanare includes a built-in test runner invoked via `mapanare test`. Test functions are marked with the `@test` decorator and use `assert` statements for verification.

### Test Syntax

```mn
@test
fn test_addition() {
    assert 1 + 1 == 2
}

@test
fn test_string_length() {
    let s = "hello"
    assert len(s) == 5
}
```

**Rules:**

- Test functions must be decorated with `@test`.
- Test functions take no parameters and return `Void`.
- `assert <expr>` evaluates the expression; if it is `false`, the test fails with an `AssertionError` including the source location.
- Test functions are discovered automatically in `.mn` files.

### Assert Statement

`assert` is a built-in statement (not a function call). It evaluates a boolean expression and aborts with an error if the result is `false`.

```mn
assert x > 0
assert len(items) == expected_count
```

The compiler emits `assert` as an `Assert` MIR instruction, which both the Python and LLVM backends handle natively.

### Test Discovery and Execution

```bash
mapanare test                          # run all tests in current directory
mapanare test path/to/tests/           # run tests in a specific directory
mapanare test --filter "test_add"      # run tests matching a substring
```

The test runner:

1. Scans `.mn` files for functions decorated with `@test`.
2. Compiles each test file through the MIR pipeline.
3. Executes each test function in a subprocess.
4. Reports pass/fail results with file:line locations and durations.

---

## 11. Observability

### Tracing

Mapanare supports OpenTelemetry-compatible distributed tracing for agent operations. Tracing is enabled via the `--trace` CLI flag.

```bash
mapanare run --trace program.mn              # console output
mapanare run --trace=otlp program.mn         # OTLP HTTP export
```

Traced operations:

| Operation | Span Name | Attributes |
|-----------|-----------|------------|
| Agent spawn | `agent.spawn` | `agent.name`, `agent.id` |
| Message send | `agent.send` | `agent.name`, `channel` |
| Message handle | `agent.handle` | `agent.name`, `duration_ms` |
| Agent stop | `agent.stop` | `agent.name`, `reason` |
| Agent pause/resume | `agent.pause`, `agent.resume` | `agent.name` |

Spans carry W3C Trace Context (`trace_id`, `span_id`, `parent_span_id`) and are exportable via OTLP HTTP/JSON to any OpenTelemetry-compatible backend (Jaeger, Zipkin, Grafana Tempo, etc.).

### Metrics

Prometheus-format metrics are served via the `--metrics` flag:

```bash
mapanare run --metrics :9090 program.mn
```

Exposed metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `mapanare_agent_spawns_total` | Counter | Total agents spawned |
| `mapanare_agent_messages_total` | Counter | Total messages sent |
| `mapanare_agent_errors_total` | Counter | Total agent errors |
| `mapanare_agent_stops_total` | Counter | Total agents stopped |
| `mapanare_agent_handle_duration_seconds` | Histogram | Message handling latency |

### Structured Error Codes

All compiler and runtime errors use structured codes in the format `MN-X0000`:

| Prefix | Category | Example |
|--------|----------|---------|
| `MN-P` | Parse errors | `MN-P0001` unexpected token |
| `MN-S` | Semantic errors | `MN-S0001` undefined variable |
| `MN-L` | MIR lowering errors | `MN-L0001` unsupported node |
| `MN-C` | Code generation errors | `MN-C0001` LLVM emit failure |
| `MN-R` | Runtime errors | `MN-R0001` agent mailbox full |
| `MN-T` | Tooling errors | `MN-T0001` test discovery failure |

### Debug Info (DWARF)

Native binaries compiled with `-g` / `--debug` include DWARF debug information for source-level debugging with `gdb` or `lldb`:

```bash
mapanare build -g program.mn -o program
lldb ./program
```

Debug info includes:

- Compile unit metadata (source file, producer)
- Function debug info (name, file, line, scope)
- Line number mapping from MIR instructions to source locations
- Variable debug info (names, types, locations)
- Struct type debug info (member layout)

---

## 12. Deployment

### Supervision Trees

Agents can be organized into supervision trees with configurable restart strategies:

```mn
@supervised("one_for_one")
agent Worker {
    input task: String
    output result: String

    fn handle(task: String) -> String {
        return process(task)
    }
}
```

| Strategy | Behavior |
|----------|----------|
| `one_for_one` | Restart only the failed agent |
| `one_for_all` | Restart all agents in the tree when one fails |
| `rest_for_one` | Restart the failed agent and all agents started after it |

### Health Checks

Agent applications expose health and readiness endpoints:

- `/health` — liveness check (is the process running?)
- `/ready` — readiness check (are all agents initialized and running?)
- `/status` — detailed agent status (names, states, uptime)

### Graceful Shutdown

On `SIGTERM`, the runtime:

1. Stops accepting new messages.
2. Drains in-flight messages from all agent mailboxes.
3. Calls `on_stop()` on each agent.
4. Exits cleanly within a configurable timeout (default: 30 seconds).

### Deploy Scaffolding

```bash
mapanare deploy init                   # generate Dockerfile + config
```

Generates a multi-stage Dockerfile optimized for Mapanare agent applications.

---

## Appendix A: Grammar Summary (EBNF Sketch)

This is an informal sketch, not the complete formal grammar.

```ebnf
program        = { import_decl | definition | statement } ;
definition     = fn_def | agent_def | struct_def | enum_def
               | type_alias | pipe_def | impl_def | trait_def
               | impl_trait_def | export_def ;

fn_def         = ["pub"] "fn" IDENT ["<" type_params ">"]
                 "(" [params] ")" ["->" type] block ;
agent_def      = ["pub"] "agent" IDENT "{" { agent_member } "}" ;
struct_def     = ["pub"] "struct" IDENT ["<" type_params ">"]
                 "{" { field_def } "}" ;
enum_def       = ["pub"] "enum" IDENT ["<" type_params ">"]
                 "{" { variant } "}" ;
pipe_def       = ["pub"] "pipe" IDENT "{" pipe_chain "}" ;
impl_def       = "impl" IDENT "{" { fn_def } "}" ;
trait_def      = ["pub"] "trait" IDENT "{" { trait_method } "}" ;
impl_trait_def = "impl" IDENT "for" IDENT "{" { fn_def } "}" ;
import_decl    = "import" path [ "::" "{" names "}" ] ;
export_def     = "export" ( definition | "{" names "}" ) ;

agent_member   = "input" IDENT ":" type
               | "output" IDENT ":" type
               | let_binding
               | fn_def ;

pipe_chain     = IDENT { "|>" IDENT } ;

statement      = let_binding | assignment | expr | for_loop
               | if_expr | match_expr | return_stmt ;
let_binding    = "let" ["mut"] IDENT [":" type] "=" expr ;
```

---

## Appendix B: Compilation Pipeline

### Overview

The Mapanare compiler uses a multi-stage pipeline with an intermediate representation (MIR) between the AST and final code emission:

```
.mn source → Lexer → Parser → AST → Semantic Analysis → MIR Lowering → MIR Optimizer → Emitter
                                                                                          ├→ Python
                                                                                          └→ LLVM IR → Native Binary
```

### MIR (Mid-level Intermediate Representation)

MIR is a typed, SSA-based intermediate representation that sits between the AST and code emission. It was introduced in v0.6.0 to decouple frontend analysis from backend code generation.

**Key properties:**

- **SSA form:** Each temporary is assigned exactly once. Phi nodes merge values at control-flow join points.
- **Typed:** Every instruction carries type information from the semantic checker.
- **Basic blocks:** Code is organized into basic blocks with explicit terminators (branch, switch, return, jump).
- **Three-address form:** Operations use `%temp = op(arg1, arg2)` style instructions.

**Instruction categories:**

| Category | Instructions |
|----------|-------------|
| **Arithmetic** | `Add`, `Sub`, `Mul`, `Div`, `Mod`, `Neg` |
| **Comparison** | `Eq`, `Ne`, `Lt`, `Le`, `Gt`, `Ge` |
| **Logic** | `And`, `Or`, `Not` |
| **Memory** | `Alloca`, `Load`, `Store`, `FieldGet`, `FieldSet` |
| **Control** | `Branch`, `Jump`, `Switch`, `Return`, `Phi` |
| **Calls** | `Call`, `CallBuiltin`, `CallMethod` |
| **Types** | `StructInit`, `EnumInit`, `EnumTag`, `Cast` |
| **Agents** | `AgentSpawn`, `AgentSend`, `AgentSync` |
| **Signals** | `SignalInit`, `SignalGet`, `SignalSet`, `SignalComputed`, `SignalSubscribe` |
| **Streams** | `StreamOp` (map, filter, take, skip, collect, fold) |
| **Closures** | `ClosureCreate`, `ClosureCall`, `EnvLoad` |
| **Strings** | `InterpConcat` |

**MIR optimizer passes (applied at -O1 and above):**

- Constant folding and propagation
- Dead code elimination
- Copy propagation
- Basic block merging
- Unreachable block removal

### Python Transpiler

The Python emitter translates MIR to Python source code. This enables:

- Rapid language prototyping and iteration.
- Leveraging the Python ecosystem (NumPy for tensors, asyncio for agents).
- Immediate access to ML libraries during early development.

Agents map to Python `asyncio` tasks. Signals map to observable patterns.

### LLVM Native Backend

The LLVM emitter translates MIR to LLVM IR, producing native machine code. This enables:

- Agent spawn/send/sync codegen backed by the C runtime thread pool and ring buffers.
- Compile-time tensor shape verification (element-wise ops and matmul via runtime calls).
- Arena-based memory management with tag-bit string freeing (no garbage collector).
- Ahead-of-time compilation for deployment.
- Cross-compilation to Linux x64, macOS ARM64, Windows x64.

As of v0.8.0, all core features (maps, signals with reactivity, streams with operators, closures with capture) are fully supported on the LLVM backend.

---

## Appendix C: Reserved for Future Specification

The following sections are implemented but not yet formally specified here:

- **Module System:** File-based modules with `import`/`export`, `pub` visibility, circular dependency detection. See [RFC 0003](rfcs/0003-module-resolution.md).
- **Memory Model:** Arena allocation with scope-based cleanup, tag-bit string freeing. See [RFC 0002](rfcs/0002-memory-management.md).
- **Trait System:** `trait` definitions, `impl Trait for Type`, trait bounds on generics, monomorphization in LLVM backend. See [RFC 0004](rfcs/0004-traits.md).

The following sections are planned but not yet specified or implemented:

- **Standard Library:** Built-in functions, collections API, I/O primitives (partial implementation in `stdlib/`).
- **Error Model:** Error types, panic vs recoverable errors, stack traces.
- **Concurrency Guarantees:** Ordering, fairness, deadlock prevention.
- **Tensor Operations:** Full operator set, broadcasting rules, autodiff (LLVM backend has partial tensor codegen; Python backend does not yet support tensors).
- **String Interpolation:** `${expr}` syntax is implemented in both Python and LLVM backends. Multi-line strings (`"""..."""`) are also supported.
- **Decorator System:** Custom decorator definitions (built-in decorators `@test`, `@supervised`, `@restart`, `@allow` are specified above).
- **FFI:** Foreign function interface for C and Python interop. C FFI uses `extern "C" fn name(params) -> Type`. Python interop uses `extern "Python" fn module::name(params) -> Type` to import and call Python functions with type-safe wrappers. Return type `Result<T, String>` wraps Python exceptions in `Err`. Use `--python-path` to add custom module search paths.
