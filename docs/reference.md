# Mapanare Language Reference

**Version:** 0.5.0

This is the complete language reference for Mapanare. For a tutorial introduction, see [Getting Started](getting-started.md). For the formal specification, see [SPEC.md](SPEC.md).

---

## Table of Contents

- [Primitive Types](#primitive-types)
- [Keywords](#keywords)
- [Operators](#operators)
- [Variables and Bindings](#variables-and-bindings)
- [Functions](#functions)
- [Control Flow](#control-flow)
- [Pattern Matching](#pattern-matching)
- [Structs](#structs)
- [Enums](#enums)
- [Traits](#traits)
- [Generics](#generics)
- [Type Aliases](#type-aliases)
- [Lists](#lists)
- [Maps](#maps)
- [Strings](#strings)
- [Option and Result](#option-and-result)
- [Agents](#agents)
- [Signals](#signals)
- [Streams](#streams)
- [Pipes](#pipes)
- [Tensors](#tensors)
- [Modules and Imports](#modules-and-imports)
- [FFI — Foreign Function Interface](#ffi--foreign-function-interface)
- [Decorators](#decorators)
- [Lambdas](#lambdas)
- [Builtin Functions](#builtin-functions)
- [Comments](#comments)
- [CLI Commands](#cli-commands)
- [Optimization Levels](#optimization-levels)

---

## Primitive Types

| Type | Description | Example |
|------|-------------|---------|
| `Int` | 64-bit signed integer | `42`, `1_000_000`, `0xFF`, `0b1010`, `0o77` |
| `Float` | 64-bit IEEE 754 float | `3.14`, `1.0e-10` |
| `Bool` | Boolean | `true`, `false` |
| `String` | Immutable UTF-8 string | `"hello"`, `"value: ${x}"` |
| `Char` | Single Unicode scalar | `'a'`, `'\n'` |
| `Void` | Unit type (no value) | — |

### Container Types

| Type | Description | Example |
|------|-------------|---------|
| `List<T>` | Ordered, dynamic-size collection | `[1, 2, 3]` |
| `Map<K, V>` | Hash map | `#{ "key": "value" }` |
| `Option<T>` | `Some(value)` or `none` | `Some(42)`, `none` |
| `Result<T, E>` | `Ok(value)` or `Err(error)` | `Ok(42)`, `Err("fail")` |

### Concurrency and Reactive Types

| Type | Description |
|------|-------------|
| `Signal<T>` | Reactive container with automatic change propagation |
| `Stream<T>` | Asynchronous iterable producing values over time |
| `Channel<T>` | Typed message channel for inter-agent communication |
| `Tensor<T>[shape]` | N-dimensional array with compile-time shape verification |

---

## Keywords

### Bindings

| Keyword | Usage |
|---------|-------|
| `let` | Declare an immutable binding: `let x = 42` |
| `mut` | Make a binding mutable: `let mut x = 0` |

### Functions

| Keyword | Usage |
|---------|-------|
| `fn` | Define a function: `fn add(a: Int, b: Int) -> Int { ... }` |
| `return` | Return a value from a function |
| `pub` | Mark a definition as publicly visible |
| `self` | Reference to current instance in `impl` blocks |

### Agents and Concurrency

| Keyword | Usage |
|---------|-------|
| `agent` | Define a concurrent actor |
| `spawn` | Create and start an agent: `let a = spawn MyAgent()` |
| `sync` | Await an agent output: `let r = sync a.output` |

### Reactive and Streaming

| Keyword | Usage |
|---------|-------|
| `signal` | Declare a reactive signal |
| `stream` | Declare a stream |
| `pipe` | Define a named agent pipeline |

### Control Flow

| Keyword | Usage |
|---------|-------|
| `if` / `else` | Conditional branching |
| `match` | Pattern matching expression |
| `for` / `in` | Loop over an iterable: `for x in items { ... }` |
| `while` | Loop with condition: `while cond { ... }` |

### Types and Data

| Keyword | Usage |
|---------|-------|
| `struct` | Define a data structure: `struct Point { x: Float, y: Float }` |
| `enum` | Define a tagged union: `enum Color { Red, Blue }` |
| `type` | Type alias: `type Name = String` |
| `impl` | Implement methods: `impl Point { ... }` |
| `trait` | Define a trait: `trait Display { ... }` |

### Modules

| Keyword | Usage |
|---------|-------|
| `import` | Import from a module: `import math` or `import utils::{foo, bar}` |
| `export` | Re-export: `export fn public_fn() { ... }` |

### FFI

| Keyword | Usage |
|---------|-------|
| `extern` | Foreign function declaration: `extern "C" fn malloc(size: Int) -> Int` |

### Literals

| Keyword | Value |
|---------|-------|
| `true` | Boolean true |
| `false` | Boolean false |
| `none` | The `None` variant of `Option<T>` |

---

## Operators

### Precedence Table (Highest to Lowest)

| Prec | Operators | Description |
|------|-----------|-------------|
| 1 | `::` `@` `.` | Namespace access, decorator, field access |
| 2 | `!` `-` (unary) | Logical NOT, negation |
| 3 | `*` `/` `%` `@` | Multiply, divide, modulo, matrix multiply |
| 4 | `+` `-` | Add, subtract |
| 5 | `..` `..=` | Exclusive and inclusive range |
| 6 | `\|>` | Pipe |
| 7 | `<` `>` `<=` `>=` | Comparison |
| 8 | `==` `!=` | Equality |
| 9 | `&&` | Logical AND (short-circuit) |
| 10 | `\|\|` | Logical OR (short-circuit) |
| 11 | `?` | Error propagation |
| 12 | `=` `+=` `-=` `*=` `/=` `<-` | Assignment, compound assignment, send |
| 13 | `=>` | Lambda arrow, match arm |

### Arithmetic

```mn
let sum = a + b       // addition (also string concatenation)
let diff = a - b      // subtraction
let prod = a * b      // multiplication
let quot = a / b      // division
let rem = a % b       // modulo
let neg = -x          // unary negation
```

### Comparison and Logical

```mn
a == b    a != b          // equality
a < b     a > b           // ordering
a <= b    a >= b          // ordering
a && b    a || b    !a    // logical (short-circuit)
```

### Assignment

```mn
x = 10        // assign
x += 1        // add-assign
x -= 1        // subtract-assign
x *= 2        // multiply-assign
x /= 2        // divide-assign
```

### Special Operators

```mn
data |> transform |> format    // pipe: left-to-right data flow
agent.input <- value           // send: message to agent channel
let val = result?              // error propagation (early return on Err/None)
0..10                          // exclusive range
0..=10                         // inclusive range
Math::sqrt                     // namespace access
a @ b                          // matrix multiplication (tensors)
```

---

## Variables and Bindings

Variables are declared with `let`. They are immutable by default.

```mn
let x = 42                    // immutable, type inferred as Int
let name: String = "Alice"    // immutable, explicitly typed
let mut count = 0             // mutable
count += 1                    // OK — count is mutable
```

Type annotations are optional when the type can be inferred.

---

## Functions

```mn
fn add(a: Int, b: Int) -> Int {
    return a + b
}

// Public function (visible to importers)
pub fn greet(name: String) -> String {
    return "Hello, ${name}!"
}

// No return type means Void
fn log_message(msg: String) {
    print(msg)
}
```

### Generic Functions

```mn
fn identity<T>(x: T) -> T {
    return x
}

fn first<T>(items: List<T>) -> T {
    return items[0]
}
```

### Trait Bounds

```mn
fn print_item<T: Display>(item: T) {
    print(item.to_string())
}
```

---

## Control Flow

### If / Else

```mn
if x > 0 {
    print("positive")
} else if x == 0 {
    print("zero")
} else {
    print("negative")
}
```

### For Loops

```mn
// Range (exclusive)
for i in 0..5 {
    print(str(i))    // 0, 1, 2, 3, 4
}

// Range (inclusive)
for i in 1..=3 {
    print(str(i))    // 1, 2, 3
}

// Over a list
for item in items {
    print(str(item))
}
```

### While Loops

```mn
let mut i = 0
while i < 10 {
    print(str(i))
    i += 1
}
```

---

## Pattern Matching

`match` destructures values. All arms must be exhaustive for enums.

```mn
match value {
    1 => print("one"),
    2 => print("two"),
    _ => print("other"),
}
```

### Enum Matching

```mn
enum Shape {
    Circle(Float),
    Rect(Float, Float),
}

fn describe(s: Shape) -> String {
    match s {
        Circle(r) => return "circle with radius ${str(r)}",
        Rect(w, h) => return "rect ${str(w)}x${str(h)}",
    }
}
```

### Option and Result Matching

```mn
match maybe_value {
    Some(v) => print("got ${str(v)}"),
    None => print("nothing"),
}

match result {
    Ok(v) => print("success: ${str(v)}"),
    Err(e) => print("error: ${e}"),
}
```

---

## Structs

Structs are product types — named collections of fields.

```mn
struct Point {
    x: Float,
    y: Float,
}

// Construction uses positional arguments
let p = Point(1.0, 2.0)

// Field access
print(str(p.x))    // 1.0
```

### Methods via `impl`

```mn
impl Point {
    fn magnitude(self) -> Float {
        return (self.x * self.x + self.y * self.y)
    }
}
```

### Generic Structs

```mn
struct Pair<A, B> {
    first: A,
    second: B,
}
```

---

## Enums

Enums are sum types (tagged unions). Each variant can carry data.

```mn
enum Color {
    Red,
    Green,
    Blue,
    Custom(Int, Int, Int),
}

// Construction
let c = Color_Red
let custom = Color_Custom(255, 128, 0)
```

> **Note:** Enum variants are constructed with `EnumName_VariantName(args)` syntax.

---

## Traits

Traits define shared behavior.

```mn
trait Display {
    fn to_string(self) -> String
}

impl Display for Point {
    fn to_string(self) -> String {
        return "(${str(self.x)}, ${str(self.y)})"
    }
}
```

### Builtin Traits

| Trait | Methods |
|-------|---------|
| `Display` | `to_string(self) -> String` |
| `Eq` | `eq(self, other: Self) -> Bool` |
| `Ord` | `cmp(self, other: Self) -> Int` |
| `Hash` | `hash(self) -> Int` |

---

## Generics

Functions, structs, enums, and agents can be parameterized with type variables.

```mn
fn max<T: Ord>(a: T, b: T) -> T {
    if a.cmp(b) > 0 {
        return a
    }
    return b
}

struct Stack<T> {
    items: List<T>,
}
```

---

## Type Aliases

```mn
type Name = String
type Matrix = Tensor<Float>[3, 3]
type Callback = fn(Int) -> Bool
type StringResult = Result<String, String>
```

---

## Lists

```mn
let items: List<Int> = [1, 2, 3]
let empty: List<String> = []

// Access
let first = items[0]

// Methods
let mut list: List<Int> = []
list.push(10)
list.push(20)
let len = list.length()
let popped = list.pop()

// Iteration
for item in items {
    print(str(item))
}
```

---

## Maps

Maps use `#{ key: value }` syntax.

```mn
let config = #{ "host": "localhost", "port": "8080" }

// Access
let host = config["host"]
```

---

## Strings

### String Literals

```mn
let simple = "hello, world"
let escaped = "line one\nline two"
```

### String Interpolation

```mn
let name = "World"
let greeting = "Hello, ${name}!"
let computed = "sum = ${a + b}"
let nested = "len = ${str(len(items))}"
```

Any valid expression can appear inside `${...}`.

### Multi-line Strings

```mn
let text = """
    This is a multi-line
    string literal.
"""
```

### String Methods

| Method | Description |
|--------|-------------|
| `.length()` | String length |
| `.find(sub)` | Index of first occurrence (-1 if not found) |
| `.substring(start, end)` | Extract substring |
| `.split(sep)` | Split into list of strings |
| `.contains(sub)` | Check if substring exists |
| `.starts_with(prefix)` | Check prefix |
| `.ends_with(suffix)` | Check suffix |
| `.to_upper()` | Convert to uppercase |
| `.to_lower()` | Convert to lowercase |
| `.trim()` | Remove leading/trailing whitespace |
| `.replace(old, new)` | Replace occurrences |

---

## Option and Result

### Option<T>

Represents a value that may or may not be present. Replaces null.

```mn
let x: Option<Int> = Some(42)
let y: Option<Int> = none

// Pattern match to extract
match x {
    Some(v) => print(str(v)),
    None => print("nothing"),
}
```

### Result<T, E>

Represents success or failure. Primary error-handling mechanism.

```mn
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division by zero")
    }
    return Ok(a / b)
}
```

### The `?` Operator

Propagates errors automatically — unwraps `Ok`/`Some`, returns early on `Err`/`None`.

```mn
fn process() -> Result<Int, String> {
    let a = parse_int("42")?     // returns Err early if parse fails
    let b = parse_int("10")?
    return Ok(a + b)
}
```

---

## Agents

Agents are concurrent actors with typed input/output channels.

### Definition

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

### Spawning and Communication

```mn
let counter = spawn Counter()       // create and start
counter.increment <- 5              // send (non-blocking)
let result = sync counter.count     // receive (blocking)
```

### Lifecycle

| State | Description |
|-------|-------------|
| `init` | Created, `on_init()` called |
| `running` | Processing messages |
| `paused` | Suspended, messages buffered |
| `stopped` | Terminated, `on_stop()` called |

### Lifecycle Hooks

```mn
agent MyAgent {
    input data: String
    output result: String

    fn on_init() {
        // called when agent starts
    }

    fn handle(data: String) -> String {
        return data
    }

    fn on_stop() {
        // called when agent stops
    }
}
```

---

## Signals

Signals are reactive containers. Dependents recompute automatically when values change.

```mn
// Mutable signal
let mut count = signal(0)

// Computed signal (read-only, auto-updates)
let doubled = signal { count.value * 2 }

// Update
count.value = 5
print(str(doubled.value))    // 10
```

### Batched Updates

```mn
batch {
    x.value = 10
    y.value = 20
}
// Dependents recompute once, not twice
```

---

## Streams

Streams are async iterables with composable operators.

```mn
let s = stream([1, 2, 3, 4, 5])

// Chain operators
let result = s
    |> filter((x) => x > 2)
    |> map((x) => x * 10)
```

### Stream Operators

| Operator | Description |
|----------|-------------|
| `map(fn)` | Transform each element |
| `filter(fn)` | Keep elements matching predicate |
| `flat_map(fn)` | Map then flatten |
| `take(n)` | First n elements |
| `skip(n)` | Skip first n elements |
| `chunk(n)` | Group into chunks of size n |
| `zip(other)` | Pair elements from two streams |
| `merge(other)` | Interleave two streams |
| `fold(init, fn)` | Reduce to single value |
| `scan(init, fn)` | Emit intermediate accumulator values |
| `distinct()` | Remove consecutive duplicates |
| `throttle(ms)` | At most one element per time window |
| `debounce(ms)` | Emit after quiet period |
| `collect()` | Collect all elements into a list |

---

## Pipes

Pipes compose agents into declarative data-processing pipelines.

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
        if len(tokens) > 5 {
            return "long"
        }
        return "short"
    }
}

pipe ClassifyText {
    Tokenizer |> Classifier
}
```

---

## Tensors

Tensors have compile-time shape verification.

```mn
let v: Tensor<Float>[3] = [1.0, 2.0, 3.0]
let m: Tensor<Float>[2, 3] = [[1.0, 2.0, 3.0],
                               [4.0, 5.0, 6.0]]

// Matrix multiply — inner dimensions must match
let a: Tensor<Float>[2, 3] = ...
let b: Tensor<Float>[3, 4] = ...
let c = a @ b    // Result: Tensor<Float>[2, 4]

// Shape mismatch is a compile error
let x: Tensor<Float>[3] = [1.0, 2.0, 3.0]
let y: Tensor<Float>[4] = [1.0, 2.0, 3.0, 4.0]
let z = x + y    // COMPILE ERROR: shape mismatch [3] vs [4]
```

### Tensor Creation

```mn
let z = Tensor.zeros<Float>(3, 3)      // 3x3 zero tensor
let o = Tensor.ones<Float>(4)          // length-4 ones vector
let t = Tensor.from_list([1.0, 2.0])   // from list literal
```

### Tensor Operations

| Category | Operations | Syntax |
|----------|-----------|--------|
| Arithmetic | add, sub, mul, div | `a + b`, `a - b`, `a * b`, `a / b` |
| Matrix | matmul, dot, transpose | `a @ b`, `a.dot(b)`, `a.transpose()` |
| Reductions | sum, mean, max, min | `t.sum()`, `t.mean()`, `t.max()`, `t.min()` |

### Tensor Metadata

| Property | Type | Description |
|----------|------|-------------|
| `shape` | `List<Int>` | Dimension sizes |
| `ndim` | `Int` | Number of dimensions |
| `size` | `Int` | Total element count |
| `device` | `String` | Current device (`"cpu"`, `"cuda"`, `"vulkan"`) |

### GPU Device Transfer

```mn
let cpu_tensor: Tensor<Float>[1024] = Tensor.ones<Float>(1024)
let gpu_tensor = cpu_tensor.to_device("cuda")   // CPU -> GPU
let back = gpu_tensor.to_device("cpu")           // GPU -> CPU

// Operations on GPU tensors execute on the GPU
@gpu
fn process(t: Tensor<Float>[1024]) -> Tensor<Float>[1024] {
    return t * 2.0 + Tensor.ones<Float>(1024)
}
```

All tensor operations fall back to CPU transparently when no GPU is available.

---

## Modules and Imports

### File-based Modules

Each `.mn` file is a module. Use `pub` to make definitions visible to importers.

```mn
// math_utils.mn
pub fn square(x: Int) -> Int {
    return x * x
}
```

### Importing

```mn
// Import entire module
import math_utils

// Import specific items
import utils::{foo, bar}
```

### Exporting

```mn
// Re-export a definition
export fn public_api() -> Int {
    return 42
}

// Re-export by name
export { foo, bar }
```

---

## FFI — Foreign Function Interface

### C Interop

```mn
extern "C" fn abs(x: Int) -> Int
extern "C" fn malloc(size: Int) -> Int
```

Use `--link-lib` to link against C libraries:

```bash
mapanare build program.mn --link-lib m    # links libm
```

### Python Interop

```mn
extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn json::loads(s: String) -> Result<String, String>
```

Use `--python-path` to add module search paths:

```bash
mapanare run program.mn --python-path ./mymodules
```

Python exceptions are wrapped in `Result<T, String>` when the return type is `Result`.

---

## Decorators

Decorators annotate definitions with metadata.

```mn
@allow(W001)
fn unused_var_ok() {
    let x = 42
}

@restart(policy: "always", max: 3, window: 60)
agent ReliableWorker {
    // ...
}
```

### GPU Decorators

| Decorator | Description |
|-----------|-------------|
| `@gpu` | Auto-dispatch to CUDA or Vulkan based on runtime detection; falls back to CPU |
| `@cuda` | Force CUDA backend (runtime error if unavailable) |
| `@vulkan` | Force Vulkan backend (runtime error if unavailable) |
| `@metal` | Reserved for future macOS/iOS Metal support |

```mn
@gpu
fn add_tensors(a: Tensor<Float>[1024], b: Tensor<Float>[1024]) -> Tensor<Float>[1024] {
    return a + b
}

@cuda
fn train_step(weights: Tensor<Float>[256, 128], grads: Tensor<Float>[256, 128]) -> Tensor<Float>[256, 128] {
    return weights - grads * 0.01
}

@vulkan
fn compute_shader(data: Tensor<Float>[4096]) -> Tensor<Float>[4096] {
    return data * 2.0
}
```

GPU backends are loaded at runtime via `dlopen` -- no compile-time SDK installation required. When `@gpu` is used, the runtime probes for CUDA first, then Vulkan, then falls back to CPU.

---

## Lambdas

Lambda expressions use `=>` syntax.

```mn
// Single parameter
let double = (x) => x * 2

// Multiple parameters
let add = (a, b) => a + b

// With blocks
let process = (x) => {
    let y = x * 2
    return y + 1
}

// In stream operators
data |> filter((x) => x > 0) |> map((x) => x * 10)
```

---

## Builtin Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `print(value)` | `(Any) -> Void` | Print with newline |
| `println(value)` | `(Any) -> Void` | **Deprecated.** Alias for `print`. Use `print` instead |
| `len(collection)` | `(List<T> \| String) -> Int` | Length of collection or string |
| `str(value)` | `(Any) -> String` | Convert to string |
| `toString(value)` | `(Any) -> String` | Convert to string (alias) |
| `int(value)` | `(Any) -> Int` | Convert to integer |
| `float(value)` | `(Any) -> Float` | Convert to float |
| `Some(value)` | `(T) -> Option<T>` | Wrap in Some |
| `Ok(value)` | `(T) -> Result<T, E>` | Wrap in Ok |
| `Err(error)` | `(E) -> Result<T, E>` | Wrap in Err |
| `signal(value)` | `(T) -> Signal<T>` | Create a signal |
| `stream(iterable)` | `(List<T>) -> Stream<T>` | Create a stream |

---

## Comments

```mn
// Single-line comment

/* Multi-line
   comment */
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `mapanare run <file>` | Compile and execute |
| `mapanare build <file>` | Compile to native binary via LLVM |
| `mapanare jit <file>` | JIT-compile and run natively |
| `mapanare check <file>` | Type-check only (with error recovery) |
| `mapanare compile <file>` | Transpile to Python |
| `mapanare emit-llvm <file>` | Emit LLVM IR |
| `mapanare repl` | Interactive REPL |
| `mapanare fmt <file>` | Format source code |
| `mapanare lint <file>` | Lint for code quality issues |
| `mapanare lint --fix <file>` | Auto-fix lint warnings |
| `mapanare init [path]` | Initialize new project |
| `mapanare install <pkg>` | Install a package |
| `mapanare publish [path]` | Publish to registry |
| `mapanare search <query>` | Search package registry |
| `mapanare login` | Authenticate with registry |
| `mapanare version [type]` | Show or bump version |
| `mapanare targets` | List compilation targets |
| `mapanare doc <file>` | Generate documentation from doc comments |
| `mapanare emit-wasm <file>` | Emit WebAssembly (WAT text format) |

### Common Options

| Option | Description |
|--------|-------------|
| `-O0` to `-O3` | Optimization level |
| `-o <path>` | Output file path |
| `--target <triple>` | Cross-compilation target (e.g., `wasm32-wasi`, `aarch64-apple-ios17.0`) |
| `--lib` | Produce library output (`.a` for iOS, `.so` for Android) instead of executable |
| `--link-lib <lib>` | Link against a C library |
| `--python-path <dir>` | Python module search path |
| `--fix` | Auto-fix lint warnings |
| `--bench` | Output benchmark metrics (JIT mode) |
| `--binary` | Emit `.wasm` binary instead of WAT text (emit-wasm only, requires `wat2wasm`) |

### WebAssembly Targets

```bash
# Browser target (no WASI, JS host provides imports)
mapanare emit-wasm source.mn

# Binary output
mapanare emit-wasm --binary source.mn

# Server-side WASI target
mapanare emit-wasm --wasi source.mn
```

### Mobile Cross-Compilation

```bash
# iOS static library
mapanare build --target aarch64-apple-ios17.0 --lib app.mn

# Android shared library
mapanare build --target aarch64-linux-android34 --lib app.mn

# Android emulator
mapanare build --target x86_64-linux-android34 --lib app.mn
```

---

## Optimization Levels

| Level | Name | Passes |
|-------|------|--------|
| `-O0` | None | No optimization |
| `-O1` | Basic | Constant folding |
| `-O2` | Standard | Constant folding + dead code elimination (default) |
| `-O3` | Aggressive | All of O2 + agent inlining + stream fusion |

---

## Lint Rules

The linter (`mapanare lint`) checks for common issues:

| Rule | Description | Auto-fix |
|------|-------------|----------|
| `W001` | Unused variable | No (use `_` prefix to suppress) |
| `W002` | Unused import | Yes (removes import line) |
| `W003` | Variable shadowing | No |
| `W004` | Unreachable code after `return` | No |
| `W005` | Mutable variable never mutated | Yes (removes `mut`) |
| `W006` | Empty `match` arm body | No |
| `W007` | Agent `handle` without send response | No |
| `W008` | `Result` not checked / `?` not used | No |

Suppress individual warnings with `@allow(rule)`:

```mn
@allow(W001)
fn example() {
    let unused = 42
}
```

---

*For the full language specification, see [SPEC.md](SPEC.md).*
*For stdlib module documentation, see [stdlib.md](stdlib.md).*
