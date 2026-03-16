# Mapanare Language Specification

**Version:** 1.0.0
**Status:** 1.0 Final

Mapanare is an AI-native compiled programming language where agents, signals, streams, and tensors are first-class primitives -- not libraries. The production backend targets LLVM for native machine code. A legacy Python transpiler backend exists for reference and bootstrapping only.

---

## 1. Language Goals and Non-Goals

### Goals

- **AI-native primitives.** Agents, signals, streams, and tensors are built into the language, not imported from libraries. AI workflows are expressible without external frameworks.
- **Compiled.** Mapanare is always compiled. The production backend targets LLVM for native machine code. A legacy Python transpiler backend exists for bootstrapping.
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
- **Not backwards-compatible with Python syntax.** Although the legacy backend transpiles to Python, Mapanare's syntax is its own. Valid Python is not valid Mapanare and vice versa.

---

## 2. Lexical Structure

### 2.1 Keywords

The following identifiers are reserved as keywords and cannot be used as variable or function names.

#### Bindings and Mutability

| Keyword | Description |
|---|---|
| `let` | Declare an immutable variable binding. |
| `mut` | Declare a mutable variable binding: `let mut x = 0`. |

#### Functions and Definitions

| Keyword | Description |
|---|---|
| `fn` | Define a function. |
| `return` | Return a value from a function. If omitted, the last expression is the return value. |
| `pub` | Mark a definition as publicly visible outside its module. |
| `self` | Reference to the current agent or struct instance within `impl` blocks. |
| `extern` | Declare a foreign function interface (FFI) binding. |

#### Agents and Concurrency

| Keyword | Description |
|---|---|
| `agent` | Define an agent (concurrent actor with typed input/output channels). |
| `spawn` | Create and start a new agent instance. Returns a handle to the running agent. |
| `sync` | Await and retrieve an asynchronous result from an agent output or stream. |

#### Reactive and Streaming

| Keyword | Description |
|---|---|
| `signal` | Declare a reactive signal binding. |
| `stream` | Declare a stream binding. |
| `pipe` | Define a named pipeline composing agents or functions via `|>`. |

#### Control Flow

| Keyword | Description |
|---|---|
| `if` | Conditional branch. |
| `else` | Alternative branch for `if`. |
| `match` | Pattern matching expression. Exhaustiveness is checked at compile time. |
| `for` | Loop over an iterable: `for x in items { }`. |
| `while` | Loop while a condition is true: `while cond { }`. |
| `in` | Used with `for` to specify the iterable. |
| `break` | Exit the innermost `for` or `while` loop immediately. |
| `assert` | Assert a boolean condition; abort with an error if false. |

#### Types and Data

| Keyword | Description |
|---|---|
| `type` | Define a type alias: `type Name = String`. |
| `struct` | Define a data structure with named fields. |
| `enum` | Define an algebraic data type (tagged union / sum type). |
| `impl` | Implement methods on a struct, enum, or agent. |
| `trait` | Define a trait (interface): a set of method signatures that types can implement. |
| `new` | Construct a struct instance: `new Point { x: 1.0, y: 2.0 }`. |

#### Modules

| Keyword | Description |
|---|---|
| `import` | Import definitions from another module. |
| `export` | Re-export definitions from the current module. |

#### Literals

| Keyword | Description |
|---|---|
| `true` | Boolean literal for true. |
| `false` | Boolean literal for false. |
| `none` | The `None` variant of `Option<T>`, representing absence of a value. |

#### Contextual Keywords

These identifiers are keywords only in specific grammar positions:

| Keyword | Context |
|---|---|
| `input` | Inside `agent` blocks — declares an input channel. |
| `output` | Inside `agent` blocks — declares an output channel. |
| `Tensor` | Type expressions — the tensor type constructor. |
| `_` | Pattern matching — wildcard pattern. |

### 2.2 Operators

#### Pipe Operator

| Operator | Name | Description |
|---|---|---|
| `\|>` | Pipe | Pass the result of the left-hand expression as the first argument to the right-hand function or agent. Enables left-to-right data flow. |

```mn
let result = data |> tokenize |> classify |> format
// Equivalent to: format(classify(tokenize(data)))
```

#### Type and Function Operators

| Operator | Name | Description |
|---|---|---|
| `->` | Return type | Annotates the return type of a function: `fn foo() -> Int`. |
| `=>` | Arrow | Used in lambda expressions and match arms: `(x) => x + 1` or `Some(v) => v`. |
| `::` | Namespace | Access a namespaced item: `Math::sqrt`, `Option::Some`. Also used for turbofish generic calls: `foo::<Int>(x)`. |
| `@` | Decorator | Apply a compile-time annotation or decorator to a definition. Also used for matrix multiplication on tensors: `a @ b`. |

#### Arithmetic Operators

| Operator | Name | Description |
|---|---|---|
| `+` | Add | Addition for numeric types, concatenation for strings. |
| `-` | Subtract | Subtraction. Also unary negation: `-x`. |
| `*` | Multiply | Multiplication. |
| `/` | Divide | Division. Integer division for `Int`, floating-point division for `Float`. |
| `%` | Modulo | Remainder after integer division. |

#### Comparison Operators

| Operator | Name | Description |
|---|---|---|
| `==` | Equal | Structural equality. |
| `!=` | Not equal | Structural inequality. |
| `<` | Less than | Ordering comparison. |
| `>` | Greater than | Ordering comparison. |
| `<=` | Less or equal | Ordering comparison. |
| `>=` | Greater or equal | Ordering comparison. |

#### Logical Operators

| Operator | Name | Description |
|---|---|---|
| `&&` | Logical AND | Short-circuiting conjunction. |
| `\|\|` | Logical OR | Short-circuiting disjunction. |
| `!` | Logical NOT | Boolean negation. |

#### Assignment Operators

| Operator | Name | Description |
|---|---|---|
| `=` | Assign | Assign a value to a mutable binding. |
| `+=` | Add-assign | `x += 1` is equivalent to `x = x + 1`. |
| `-=` | Subtract-assign | Compound subtraction assignment. |
| `*=` | Multiply-assign | Compound multiplication assignment. |
| `/=` | Divide-assign | Compound division assignment. |

#### Other Operators

| Operator | Name | Description |
|---|---|---|
| `..` | Range | Create an exclusive range: `0..10`. |
| `..=` | Range inclusive | Create an inclusive range: `0..=10`. |
| `?` | Error propagation | Unwrap a `Result` or `Option`. If `Err` or `None`, return early from the enclosing function. Modeled after Rust's `?` operator. |
| `<-` | Send | Send a value into an agent's input channel: `agent.input <- value`. |

#### Operator Precedence (Highest to Lowest)

| Precedence | Operators |
|---|---|
| 1 (highest) | `::` `@` `.` |
| 2 | `!` `-` (unary) |
| 3 | `*` `/` `%` `@` (matmul) |
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

### 2.3 Literals

#### Numeric Literals

```mn
let a: Int = 42
let b: Int = 1_000_000       // underscores for readability
let c: Float = 3.14
let d: Float = 1.0e-10       // scientific notation
let e: Int = 0xFF             // hexadecimal
let f: Int = 0b1010           // binary
let g: Int = 0o77             // octal
```

#### String Literals

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

#### Character Literals

```mn
let c: Char = 'a'
let newline: Char = '\n'
let backslash: Char = '\\'
```

A `Char` literal is a single Unicode scalar value enclosed in single quotes. Escape sequences are supported: `\n`, `\t`, `\r`, `\\`, `\'`.

#### Boolean and None Literals

```mn
let t = true
let f = false
let absent: Option<Int> = none
```

### 2.4 Comments

```mn
// Single-line comment

/* Multi-line
   block comment */

/// Doc comment — attached to the following definition
/// and available to tooling and documentation generators
```

Doc comments (`///`) are captured by the parser and associated with the following function, agent, struct, enum, trait, or type alias definition.

### 2.5 Identifiers

Identifiers start with a letter or underscore, followed by letters, digits, or underscores: `[a-zA-Z_][a-zA-Z0-9_]*`. Identifiers are case-sensitive.

---

## 3. Type System

### 3.1 Primitive Types

| Type | TypeKind | Description |
|---|---|---|
| `Int` | `INT` | 64-bit signed integer. |
| `Float` | `FLOAT` | 64-bit IEEE 754 floating-point number. |
| `Bool` | `BOOL` | Boolean value: `true` or `false`. |
| `String` | `STRING` | Immutable UTF-8 encoded string. |
| `Char` | `CHAR` | Single Unicode scalar value (code point). |
| `Void` | `VOID` | Unit type representing the absence of a value. Functions with no meaningful return value return `Void`. |

### 3.2 Generic Container Types

| Type | TypeKind | Description |
|---|---|---|
| `List<T>` | `LIST` | Dynamically-sized ordered collection of elements of type `T`. Arena-backed. |
| `Map<K, V>` | `MAP` | Hash map from keys of type `K` to values of type `V`. Keys must be hashable. Robin Hood hash table in native mode. |
| `Option<T>` | `OPTION` | A value that is either `Some(value)` or `None`. Represents the possible absence of a value without null pointers. |
| `Result<T, E>` | `RESULT` | A value that is either `Ok(value)` or `Err(error)`. Used for recoverable error handling. |
| `Signal<T>` | `SIGNAL` | Reactive container holding a value of type `T`. When the value changes, all dependents are notified and recomputed. |
| `Stream<T>` | `STREAM` | Asynchronous iterable producing values of type `T` over time. Supports backpressure. |
| `Channel<T>` | `CHANNEL` | Typed, bounded message channel for inter-agent communication. Carries values of type `T`. |
| `Tensor<T>[shape]` | `TENSOR` | N-dimensional array with element type `T` and compile-time verified shape. Example: `Tensor<Float>[3, 3]` is a 3x3 matrix of floats. |

### 3.3 Compound / User-Defined Types

| Type | TypeKind | Description |
|---|---|---|
| `fn(A, B) -> C` | `FN` | Function type with parameter types and return type. Used for closures and function references. |
| `struct Name { ... }` | `STRUCT` | Named product type with typed fields. |
| `enum Name { ... }` | `ENUM` | Named sum type (tagged union) with variants. |
| `agent Name { ... }` | `AGENT` | Concurrent actor type with typed input/output channels. |
| `pipe Name { ... }` | `PIPE` | Named agent pipeline composition. |
| `type Name = ...` | `TYPE_ALIAS` | Type alias. |
| `trait Name { ... }` | `TRAIT` | Trait (interface) definition. |

### 3.4 Special Types

| Type | TypeKind | Description |
|---|---|---|
| `Range` | `RANGE` | Integer range created by `..` and `..=` operators. Used in `for` loops. |
| (type variable) | `TYPE_VAR` | Compiler-internal type variable for generic instantiation. |
| (unknown) | `UNKNOWN` | Compiler-internal placeholder for unresolved types. Compatible with all types during inference. |
| (builtin fn) | `BUILTIN_FN` | Compiler-internal type for builtin function references. |

### 3.5 Type Inference Rules

Mapanare uses local type inference. The compiler infers types from the immediate context of each expression.

#### What is Inferred

- **Let bindings:** The type of a `let` binding is inferred from its initializer expression. An explicit annotation is optional.

  ```mn
  let x = 42              // inferred as Int
  let y = 3.14            // inferred as Float
  let z: String = "hello" // explicitly annotated
  let flag = true         // inferred as Bool
  ```

- **List element types:** Inferred from the first element. `[1, 2, 3]` is `List<Int>`.

- **Map key/value types:** Inferred from the first entry. `#{"a": 1}` is `Map<String, Int>`.

- **Lambda return types:** Inferred from the body expression. `(x) => x + 1` where `x: Int` returns `Int`.

- **Generic instantiation:** Generic type parameters are inferred at call sites from argument types. `identity(42)` infers `T = Int`.

#### What Must Be Annotated

- **Function parameters:** All function parameters require type annotations.

  ```mn
  fn add(a: Int, b: Int) -> Int {
      return a + b
  }
  ```

- **Function return types:** Required when the function signature needs to be clear. Can be omitted if the return type is `Void`.

- **Ambiguous generics:** When the compiler cannot determine the type parameter from context, use the turbofish syntax:

  ```mn
  let result = decode::<MyStruct>(json_string)
  ```

#### Type Checking Rules

- If a `let` binding has both an annotation and an initializer, their types must be compatible. A mismatch is a compile-time error.
- Arithmetic operators require both operands to be the same numeric type (`Int` or `Float`). No implicit numeric coercion.
- Comparison operators (`==`, `!=`, `<`, `>`, `<=`, `>=`) require both operands to be the same type.
- The condition in `if`, `while`, and `assert` must be `Bool`.
- The `?` operator requires the enclosing function to return `Result` or `Option`.

### 3.6 Struct Types

Structs are product types -- named collections of fields.

```mn
struct Point {
    x: Float,
    y: Float,
}
```

#### Struct Construction

Structs are constructed using the `new` keyword followed by the struct name and field initializers:

```mn
let p = new Point { x: 1.0, y: 2.0 }
```

The `new` keyword is required for LALR grammar disambiguation (it distinguishes struct literals from blocks after `if`/`for`/`while`).

#### Methods via `impl`

```mn
impl Point {
    fn distance(self, other: Point) -> Float {
        let dx = self.x - other.x
        let dy = self.y - other.y
        return Math::sqrt(dx * dx + dy * dy)
    }
}
```

#### Generic Structs

```mn
struct Pair<A, B> {
    first: A,
    second: B,
}
```

### 3.7 Enum Types (Algebraic Data Types)

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

#### Variants

Each variant can carry zero or more values:

```mn
enum Token {
    Eof,                           // no data
    Number(Int),                   // one value
    Pair(String, Int),             // two values
}
```

#### Exhaustiveness

Match expressions on enums must be exhaustive -- every variant must be handled, or a wildcard `_` arm must be present. The compiler reports an error if a variant is missing and no wildcard is present.

#### Generic Enums

```mn
enum Either<A, B> {
    Left(A),
    Right(B),
}
```

### 3.8 Option and Result Types

#### Option<T>

`Option<T>` represents a value that may or may not be present. It replaces null pointers.

```mn
let x: Option<Int> = Some(42)
let y: Option<Int> = none

match x {
    Some(v) => println("Got: ${v}"),
    None    => println("Nothing"),
}
```

`Option` values must be explicitly unwrapped before use. There is no implicit null.

**Construction:**
- `Some(value)` — wraps a value.
- `none` — the absent variant.

**Pattern matching:** See section 5 (Pattern Matching).

**Error propagation:** The `?` operator on an `Option<T>` unwraps `Some(v)` or returns `none` from the enclosing function (which must also return `Option`).

#### Result<T, E>

`Result<T, E>` represents an operation that can succeed with `Ok(value)` or fail with `Err(error)`. It is the primary error-handling mechanism.

```mn
fn parse_int(s: String) -> Result<Int, String> {
    // ...
}

let result = parse_int("42")
match result {
    Ok(n)  => println("Parsed: ${n}"),
    Err(e) => println("Error: ${e}"),
}
```

**Construction:**
- `Ok(value)` — success variant.
- `Err(error)` — error variant.

**Error propagation:** The `?` operator provides concise error propagation:

```mn
fn process(s: String) -> Result<Int, String> {
    let n = parse_int(s)?    // returns Err early if parse fails
    return Ok(n * 2)
}
```

When `?` is applied to a `Result`, it unwraps `Ok(v)` for the expression's value or returns `Err(e)` from the enclosing function. The enclosing function must return a compatible `Result` type.

### 3.9 Agent Types

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

When you `spawn` an agent, the returned handle exposes the input and output channels with their declared types. See section 9 (Agent Model) for full semantics.

### 3.10 Tensor Types

Tensors have their element type and shape verified at compile time.

```mn
let v: Tensor<Float>[3] = [1.0, 2.0, 3.0]         // 1D vector, 3 elements
let m: Tensor<Float>[2, 3] = [[1.0, 2.0, 3.0],     // 2D matrix, 2x3
                               [4.0, 5.0, 6.0]]
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

### 3.11 Type Aliases

```mn
type Name = String
type Matrix = Tensor<Float>[3, 3]
type Callback = fn(Int) -> Bool
```

Type aliases are transparent -- the alias name and the underlying type are interchangeable.

### 3.12 Function Types

Function types describe the signature of a callable value (function pointer or closure):

```mn
type Predicate = fn(Int) -> Bool
type Mapper = fn(String) -> String

fn apply(f: fn(Int) -> Int, x: Int) -> Int {
    return f(x)
}
```

---

## 4. Control Flow

### 4.1 If / Else

`if` is an expression — it evaluates to a value when both branches are present.

```mn
if condition {
    // then branch
} else {
    // else branch
}
```

Chained conditions use `else if`:

```mn
if x > 10 {
    println("big")
} else if x > 0 {
    println("small")
} else {
    println("non-positive")
}
```

The condition must be of type `Bool`.

### 4.2 For Loop

Iterates over a range or iterable:

```mn
for i in 0..10 {
    println("${i}")
}

for item in items {
    process(item)
}
```

The loop variable is immutable within the body. The iterable can be a `Range`, `List<T>`, `Stream<T>`, or `Map<K, V>` (iterates over entries).

### 4.3 While Loop

Loops while a condition is true:

```mn
let mut count = 0
while count < 10 {
    println("${count}")
    count += 1
}
```

The condition must be of type `Bool`. Evaluated before each iteration.

### 4.4 Break

`break` exits the innermost `for` or `while` loop immediately:

```mn
for i in 0..100 {
    if i > 10 {
        break
    }
}
```

### 4.5 Return

`return` exits the current function with a value:

```mn
fn double(x: Int) -> Int {
    return x * 2
}
```

`return` without a value returns `Void`. If omitted, the last expression in the function body is the implicit return value.

### 4.6 Match Expression

Pattern matching dispatches on the structure of a value. See section 5 (Pattern Matching) for full details.

```mn
match value {
    Some(x) => println("got ${x}"),
    None    => println("nothing"),
}
```

### 4.7 Assert Statement

`assert` is a built-in statement that evaluates a boolean expression and aborts with an error if the result is `false`.

```mn
assert x > 0
assert len(items) == expected_count
assert result == 42, "Expected 42"
```

The optional second argument is an error message expression (typically a string). The compiler emits `assert` as an `Assert` MIR instruction, handled natively by both backends.

---

## 5. Pattern Matching

### 5.1 Syntax

```mn
match expr {
    pattern1 => expr_or_block,
    pattern2 => expr_or_block,
    ...
}
```

Match arms are separated by commas. Each arm consists of a pattern, `=>`, and either an expression or a block.

### 5.2 Pattern Kinds

| Pattern | Syntax | Matches |
|---|---|---|
| **Constructor** | `Name(p1, p2, ...)` | Enum variant with the given name, binding inner values to sub-patterns. |
| **Literal** | `42`, `3.14`, `"hello"`, `true`, `false` | Exact value match for integers, floats, strings, and booleans. |
| **Identifier** | `x` | Matches anything, binding the value to the name `x`. |
| **Wildcard** | `_` | Matches anything, discarding the value. |

### 5.3 Destructuring

Enum variants are destructured by their constructor pattern:

```mn
enum Expr {
    Num(Int),
    Add(Int, Int),
}

match expr {
    Num(n)    => println("number: ${n}"),
    Add(a, b) => println("sum: ${a + b}"),
}
```

Nested destructuring is supported:

```mn
match result {
    Ok(Some(v)) => println("got ${v}"),
    Ok(None)    => println("ok but empty"),
    Err(e)      => println("error: ${e}"),
}
```

### 5.4 Exhaustiveness

The compiler checks that match expressions are exhaustive:

- For enum types, every variant must have a matching arm, OR a wildcard `_` arm must be present.
- For `Option<T>`, both `Some(...)` and `None` must be handled.
- For `Result<T, E>`, both `Ok(...)` and `Err(...)` must be handled.
- For `Bool`, both `true` and `false` must be handled, or a wildcard must be present.

A missing arm is a compile-time error.

### 5.5 Match as Expression

When all arms produce a value, `match` is an expression:

```mn
let name = match status {
    Ok(v) => v.name,
    Err(_) => "unknown",
}
```

---

## 6. Functions

### 6.1 Function Definition

```mn
fn name(param1: Type1, param2: Type2) -> ReturnType {
    // body
}
```

Functions can be marked `pub` for visibility outside the module:

```mn
pub fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

### 6.2 Generic Functions

```mn
fn identity<T>(x: T) -> T {
    return x
}

let a = identity(42)       // T = Int
let b = identity("hello")  // T = String
```

### 6.3 Closures and Lambdas

Lambda expressions create anonymous functions:

```mn
let double = (x) => x * 2
let add = (a, b) => a + b
```

Multi-parameter lambdas use tuple syntax on the left of `=>`:

```mn
let sum = (a, b) => a + b
```

Note: Lambda parameter types are inferred from context. Type annotations on lambda parameters are not supported in the grammar — use a named function if explicit types are needed.

#### Capture Semantics

Closures capture variables from the enclosing scope:

```mn
let offset = 10
let add_offset = (x: Int) => x + offset
println(add_offset(5))  // prints 15
```

**Implementation:** Closures with free variables are compiled as a pair: `{function_pointer, environment_struct_pointer}`. The environment struct contains the captured variables. Variables are captured by value (copy).

Closures without free variables are compiled as plain function pointers with no environment overhead.

### 6.4 Decorators

Decorators are compile-time annotations applied to definitions:

```mn
@test
fn test_addition() {
    assert 1 + 1 == 2
}

@supervised("one_for_one")
agent Worker {
    // ...
}
```

Built-in decorators:
- `@test` — marks a function as a test case.
- `@supervised(strategy)` — configures agent restart policy.
- `@restart(policy, max, window)` — detailed restart configuration.
- `@allow(permission)` — security permission annotation.

---

## 7. Trait System

### 7.1 Trait Declaration

A trait defines a set of method signatures that types can implement:

```mn
trait Display {
    fn to_string(self) -> String
}

trait Eq {
    fn eq(self, other: Self) -> Bool
}
```

Trait methods declare their signatures without bodies. The `self` parameter indicates the method receiver.

### 7.2 Trait Implementation

Types implement traits via `impl Trait for Type` blocks:

```mn
impl Display for Point {
    fn to_string(self) -> String {
        return "(${self.x}, ${self.y})"
    }
}

impl Eq for Point {
    fn eq(self, other: Point) -> Bool {
        return self.x == other.x && self.y == other.y
    }
}
```

The compiler verifies that all trait methods are implemented. Missing or extra methods are compile-time errors.

### 7.3 Builtin Traits

| Trait | Method | Signature | Description |
|---|---|---|---|
| `Display` | `to_string` | `(self) -> String` | Convert to human-readable string. |
| `Eq` | `eq` | `(self, other: Self) -> Bool` | Structural equality. |
| `Ord` | `cmp` | `(self, other: Self) -> Int` | Ordering comparison. Returns -1, 0, or 1. |
| `Hash` | `hash` | `(self) -> Int` | Hash value for use in maps/sets. |

### 7.4 Trait Bounds on Generics

Generic type parameters can be constrained with trait bounds:

```mn
fn print_value<T: Display>(x: T) {
    println(x.to_string())
}
```

The bound `T: Display` means `T` must implement the `Display` trait.

---

## 8. Module System

### 8.1 File-Based Modules

Each `.mn` file is a module. The module name is derived from the file path relative to the project root.

### 8.2 Imports

```mn
import encoding::json
import net::http {get, post}
import crypto
```

Import syntax:
- `import path::to::module` — imports the module, access via `module::item`.
- `import path::to::module {item1, item2}` — imports specific items into the local scope.
- Module paths use `::` as the separator.

### 8.3 Visibility

Definitions are private by default. The `pub` keyword makes a definition visible to other modules:

```mn
pub fn public_function() -> Int { return 42 }
fn private_function() -> Int { return 0 }

pub struct PublicStruct { field: Int }
```

### 8.4 Exports

The `export` keyword re-exports definitions:

```mn
export fn helper() -> Int { return 1 }
export name1, name2
```

### 8.5 Self-References

Within a multi-module compilation, `self::` refers to the current module:

```mn
import self::lexer
import self::parser
```

### 8.6 Circular Dependencies

The compiler detects circular imports and reports an error. Circular dependencies between modules are not allowed.

---

## 9. Agent Model

### 9.1 Overview

Agents are the fundamental concurrency primitive in Mapanare. They are concurrent actors that encapsulate state, communicate exclusively through typed message channels, and run independently of each other. There is no shared mutable state between agents.

### 9.2 Definition

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

Agent members:
- `input name: Type` — declares a typed input channel.
- `output name: Type` — declares a typed output channel.
- `let [mut] name = expr` — declares internal state.
- `fn name(...) { ... }` — defines methods. The `handle` method processes incoming messages.

### 9.3 Spawning and Communication

```mn
let a = spawn MyAgent()           // create and start agent
a.request <- some_value            // send input (non-blocking)
let result = sync a.response       // receive output (blocking)
```

- `spawn Name()` creates a new agent instance and starts it running.
- `<-` sends a message to an agent's input channel. The send is non-blocking; the message is queued in the agent's ring buffer.
- `sync expr` blocks the current execution until the agent produces an output.

### 9.4 Lifecycle

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

### 9.5 Typed Channels

Agent channels are typed and bounded. The type is declared in the agent definition. In the native runtime, channels are implemented as lock-free SPSC (single-producer, single-consumer) ring buffers.

### 9.6 Backpressure

When an agent's input buffer reaches capacity, the sending side is notified. The sender can:

- Block until space is available (default behavior with `sync`).
- Drop the message (configurable policy).
- Apply a timeout and fail with a `Result`.

Backpressure propagates through pipelines automatically.

### 9.7 Supervision

Agents can be configured with restart policies for failure recovery:

```mn
let worker = spawn MyAgent() @restart("always", 3, 60)
```

| Policy | Behavior |
|---|---|
| `always` | Restart the agent on any failure, up to `max` times within `window` seconds. |
| `never` | Let the agent stay stopped on failure. |
| `transient` | Restart only on unexpected failures (not on normal exit). |

Supervision trees can be built by having agents spawn and monitor child agents.

---

## 10. Signal Model

### 10.1 Overview

Signals are reactive primitives that hold a value and automatically propagate changes to dependents. They enable declarative, reactive dataflow without manual event wiring.

### 10.2 Declaration

```mn
// Mutable signal: can be set directly
let mut count = signal(0)

// Computed signal: derived from other signals, read-only
let doubled = signal { count.value * 2 }

// Updating a signal
count.value = 5
println(doubled.value)   // prints 10
```

`signal(expr)` creates a mutable signal with an initial value. `signal { expr }` creates a computed signal that re-evaluates when its dependencies change.

### 10.3 Dependency Tracking

The compiler tracks which signals are read during the evaluation of a computed signal. When any dependency changes, the computed signal is marked dirty and recomputed on next access (lazy) or immediately (eager, configurable).

```mn
let mut a = signal(1)
let mut b = signal(2)
let sum = signal { a.value + b.value }

a.value = 10
println(sum.value)   // prints 12
```

### 10.4 Subscribers

Signals support subscriptions for side effects on change:

```mn
let mut temperature = signal(20.0)

// Subscribe to changes
temperature.subscribe((t) => {
    println("Temperature changed to ${t}")
})
```

### 10.5 Batched Updates

Multiple signal updates within a `batch` block are coalesced into a single recomputation pass, avoiding intermediate recalculations:

```mn
batch {
    x.value = 10
    y.value = 20
    z.value = 30
}
// Dependents recompute once, not three times
```

### 10.6 Propagation Order

Signal updates propagate in topological order of the dependency graph. If signal A depends on signals B and C, A is recomputed only after both B and C have been updated.

---

## 11. Stream Model

### 11.1 Overview

Streams are asynchronous iterables that produce values over time. They are the primary abstraction for handling sequences of events, data chunks, and real-time feeds.

### 11.2 Declaration and Usage

```mn
// Create a stream from values
let s = Stream::from([1, 2, 3, 4, 5])

// Consume a stream
for value in s {
    println("${value}")
}
```

### 11.3 Stream Operators

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
| `collect()` | Collect all elements into a `List`. |

```mn
let result = numbers
    |> Stream::filter((n) => n % 2 == 0)
    |> Stream::map((n) => n * n)
    |> Stream::take(10)
    |> Stream::fold(0, (acc, n) => acc + n)
```

### 11.4 Backpressure

Streams have built-in backpressure. When a consumer processes values slower than the producer emits them, the producer is throttled automatically.

Backpressure strategies:

| Strategy | Behavior |
|---|---|
| `buffer(n)` | Buffer up to `n` elements, then apply backpressure. |
| `drop_oldest` | Drop the oldest buffered element when full. |
| `drop_newest` | Drop the newest (incoming) element when full. |
| `error` | Raise an error when the buffer overflows. |

### 11.5 Stream Fusion

The compiler optimizes adjacent stream operators by fusing them into a single pass. This eliminates intermediate allocations and reduces overhead. Fusion does not change observable behavior.

### 11.6 Lazy vs Eager

Stream operators are lazy by default — they are not evaluated until the stream is consumed (via `for`, `fold`, `collect`, or `for_each`). This enables efficient composition of long operator chains.

---

## 12. Pipe Definitions

Named pipelines compose agents into data-processing graphs:

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
        if len(tokens) > 10 {
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
println(label)
```

The pipe chain connects the output of one agent to the input of the next. The pipeline itself is spawned and used like a single agent — input goes to the first agent; output comes from the last.

---

## 13. Generics

### 13.1 Declaration

Functions, structs, enums, and agents can be parameterized over types using angle-bracket syntax:

```mn
fn identity<T>(x: T) -> T {
    return x
}

struct Pair<A, B> {
    first: A,
    second: B,
}

enum Either<A, B> {
    Left(A),
    Right(B),
}
```

### 13.2 Type Parameter Constraints

Type parameters can have trait bounds:

```mn
fn max<T: Ord>(a: T, b: T) -> T {
    if a.cmp(b) > 0 {
        return a
    }
    return b
}
```

### 13.3 Instantiation

Generic types are instantiated either by inference or explicitly:

```mn
// Inferred: T = Int from argument type
let x = identity(42)

// Explicit via turbofish syntax
let y = identity::<String>("hello")
let data = decode::<MyStruct>(json_string)
```

The turbofish syntax `name::<Type>(args)` explicitly provides type arguments at a call site. It is required when the compiler cannot infer the type parameter from the arguments alone.

### 13.4 Monomorphization

In the LLVM backend, generics are monomorphized at compile time. Each unique instantiation of a generic function or type generates a specialized version. There is no runtime polymorphism for generics.

---

## 14. Builtin Functions

The following functions are available without import:

| Function | Signature | Description |
|---|---|---|
| `print(value)` | `(Any) -> Void` | Print a value to stdout without newline. |
| `println(value)` | `(Any) -> Void` | Print a value to stdout with a trailing newline. |
| `len(collection)` | `(List<T> \| String \| Map<K,V>) -> Int` | Return the number of elements or characters. |
| `str(value)` | `(Any) -> String` | Convert a value to its string representation. |
| `toString(value)` | `(Any) -> String` | Alias for `str()`. |
| `int(value)` | `(Float \| String) -> Int` | Convert to integer. |
| `float(value)` | `(Int \| String) -> Float` | Convert to float. |
| `Some(value)` | `(T) -> Option<T>` | Wrap a value in `Some`. |
| `Ok(value)` | `(T) -> Result<T, E>` | Wrap a value in `Ok`. |
| `Err(error)` | `(E) -> Result<T, E>` | Wrap an error in `Err`. |
| `signal(value)` | `(T) -> Signal<T>` | Create a mutable signal with an initial value. |
| `stream(value)` | `(T) -> Stream<T>` | Create a stream from a value. |

---

## 15. String Methods

Strings support the following methods, all callable via dot syntax:

| Method | Signature | Description |
|---|---|---|
| `len()` | `() -> Int` | Return the byte length of the string. |
| `char_at(index)` | `(Int) -> Char` | Return the character at the given index. |
| `byte_at(index)` | `(Int) -> Int` | Return the byte value at the given index. |
| `substr(start, length)` | `(Int, Int) -> String` | Extract a substring starting at `start` with the given `length`. |
| `find(needle)` | `(String) -> Int` | Return the index of the first occurrence of `needle`, or -1 if not found. |
| `contains(needle)` | `(String) -> Bool` | Return `true` if the string contains `needle`. |
| `starts_with(prefix)` | `(String) -> Bool` | Return `true` if the string starts with `prefix`. |
| `ends_with(suffix)` | `(String) -> Bool` | Return `true` if the string ends with `suffix`. |
| `split(delimiter)` | `(String) -> List<String>` | Split the string by `delimiter` and return a list of parts. |
| `trim()` | `() -> String` | Remove leading and trailing whitespace. |
| `trim_start()` | `() -> String` | Remove leading whitespace. |
| `trim_end()` | `() -> String` | Remove trailing whitespace. |
| `to_upper()` | `() -> String` | Convert to uppercase. |
| `to_lower()` | `() -> String` | Convert to lowercase. |
| `replace(old, new)` | `(String, String) -> String` | Replace all occurrences of `old` with `new`. |

Example:

```mn
let s = "  Hello, World!  "
let trimmed = s.trim()              // "Hello, World!"
let upper = trimmed.to_upper()      // "HELLO, WORLD!"
let parts = trimmed.split(", ")     // ["Hello", "World!"]
let found = trimmed.contains("World") // true
let sub = trimmed.substr(0, 5)      // "Hello"
```

---

## 16. List Operations

### 16.1 List Literals

```mn
let nums: List<Int> = [1, 2, 3, 4, 5]
let empty: List<String> = []
```

The element type is inferred from the first element, or from the type annotation if the list is empty.

### 16.2 Indexing

```mn
let first = nums[0]      // get element at index (0-based)
```

Out-of-bounds access is a runtime error.

### 16.3 Operations

| Operation | Syntax | Description |
|---|---|---|
| Get element | `list[index]` | Access element by index (0-based). |
| Push | `list.push(value)` | Append an element to the end. Requires `let mut`. |
| Length | `len(list)` | Return number of elements. |
| Iteration | `for item in list { }` | Iterate over elements. |

### 16.4 List in LLVM Backend

Lists are implemented as arena-backed dynamic arrays. In native mode, `__mn_list_new(elem_size)` allocates, `__mn_list_push(list, elem)` appends, and `__mn_list_get(list, index)` retrieves.

---

## 17. Map Operations

### 17.1 Map Literals

Map literals use the `#{ }` syntax:

```mn
let ages = #{"Alice": 30, "Bob": 25}
let empty: Map<String, Int> = #{}
```

Key and value types are inferred from the first entry.

### 17.2 Indexing

```mn
let age = ages["Alice"]       // get value by key
```

### 17.3 Operations

| Operation | Syntax | Description |
|---|---|---|
| Get value | `map[key]` | Access value by key. |
| Set value | `map[key] = value` | Insert or update a key-value pair. Requires `let mut`. |
| Length | `len(map)` | Return number of entries. |
| Contains | `map.contains(key)` | Check if key exists. |
| Delete | `map.delete(key)` | Remove a key-value pair. |
| Iteration | `for entry in map { }` | Iterate over key-value pairs. |

### 17.4 Map in LLVM Backend

Maps are implemented as a Robin Hood hash table in the C runtime, type-erased via `i8*`. Key types must be hashable (primitives and strings). The map supports iteration via `__mn_map_iter_new()`, `__mn_map_iter_next()`, `__mn_map_iter_free()`.

---

## 18. FFI (Foreign Function Interface)

### 18.1 C FFI

Declare external C functions using `extern "C"`:

```mn
extern "C" fn sqrt(x: Float) -> Float
extern "C" fn puts(s: String) -> Int
```

External functions can then be called directly:

```mn
let root = sqrt(2.0)
```

Link external libraries with the `--link-lib` flag:

```bash
mapanare build program.mn --link-lib m -o program
```

### 18.2 Python Interop (Legacy)

The legacy Python backend supports calling Python functions:

```mn
extern "Python" fn json::loads(s: String) -> String
```

Python interop uses `extern "Python" fn module::name(params) -> RetType` to import and call Python functions with type-safe wrappers. Return type `Result<T, String>` wraps Python exceptions in `Err`. Use `--python-path` to add custom module search paths.

### 18.3 Calling Conventions

All FFI functions use the C calling convention. Types are mapped as:

| Mapanare Type | C Type |
|---|---|
| `Int` | `int64_t` |
| `Float` | `double` |
| `Bool` | `int32_t` (0 or 1) |
| `String` | `const char*` |
| `Void` | `void` |

---

## 19. Error Model

### 19.1 Structured Diagnostics

All compiler and runtime errors use structured codes in the format `MN-X0000`:

| Prefix | Category | Example |
|---|---|---|
| `MN-P` | Parse errors | `MN-P0001` unexpected token |
| `MN-S` | Semantic errors | `MN-S0001` undefined variable |
| `MN-L` | MIR lowering errors | `MN-L0001` unsupported node |
| `MN-C` | Code generation errors | `MN-C0001` LLVM emit failure |
| `MN-R` | Runtime errors | `MN-R0001` agent mailbox full |
| `MN-T` | Tooling errors | `MN-T0001` test discovery failure |

### 19.2 Error Reporting

Compiler errors include:
- **Error code** (e.g., `MN-S0001`).
- **Source location** (file, line, column).
- **Span** highlighting the offending code.
- **Message** describing the error.
- **Notes** with additional context (e.g., "did you mean X?").

Errors are formatted in Rust-style with color-coded output:

```
error[MN-S0001]: undefined variable `foo`
  --> src/main.mn:5:12
   |
5  |     let x = foo + 1
   |             ^^^ not found in this scope
```

### 19.3 Recoverable vs Panic Errors

- **Recoverable errors** use `Result<T, E>` and the `?` operator. These are the standard error-handling mechanism for operations that can fail (I/O, parsing, network).
- **Panics** (`assert` failures, out-of-bounds access, division by zero) terminate the program immediately with an error message and stack trace. Panics are not catchable.

---

## 20. Testing

### 20.1 Built-in Test Runner

Mapanare includes a built-in test runner invoked via `mapanare test`. Test functions are marked with the `@test` decorator and use `assert` statements for verification.

### 20.2 Test Syntax

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
- The optional second argument to `assert` is a message: `assert x > 0, "x must be positive"`.
- Test functions are discovered automatically in `.mn` files.

### 20.3 Test Discovery and Execution

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

## 21. Observability

### 21.1 Tracing

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

### 21.2 Metrics

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

### 21.3 Debug Info (DWARF)

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

## 22. Deployment

### 22.1 Supervision Trees

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

### 22.2 Health Checks

Agent applications expose health and readiness endpoints:

- `/health` — liveness check (is the process running?)
- `/ready` — readiness check (are all agents initialized and running?)
- `/status` — detailed agent status (names, states, uptime)

### 22.3 Graceful Shutdown

On `SIGTERM`, the runtime:

1. Stops accepting new messages.
2. Drains in-flight messages from all agent mailboxes.
3. Calls `on_stop()` on each agent.
4. Exits cleanly within a configurable timeout (default: 30 seconds).

### 22.4 Deploy Scaffolding

```bash
mapanare deploy init                   # generate Dockerfile + config
```

Generates a multi-stage Dockerfile optimized for Mapanare agent applications.

---

## 23. Example Programs

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
        if len(tokens) > 10 {
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

## 24. Stability

### 24.1 What Is Frozen

Starting with v1.0.0, the following are frozen and will not change without an RFC and deprecation cycle:

- **Syntax:** All grammar rules defined in this specification.
- **Semantics:** Type checking rules, operator behavior, control flow semantics.
- **Type system:** All 25 TypeKind variants and their behavior.
- **Builtin functions:** Names, signatures, and behavior of all builtin functions.
- **String methods:** All 15 methods and their signatures.
- **Agent model:** Spawn, send, sync semantics, lifecycle states.
- **Signal model:** Creation, computed, subscription, batched update semantics.
- **Stream operators:** All documented operators and their behavior.
- **Error codes:** Format (`MN-X0000`) and assigned codes.

### 24.2 What Can Still Change

The following areas may evolve without a breaking change:

- **Standard library additions:** New modules and functions can be added.
- **Optimizer improvements:** Better optimization passes and strategies.
- **New compilation targets:** Additional CPU architectures and platforms.
- **Tooling:** New CLI commands, LSP features, formatter improvements.
- **Performance:** Implementation changes that do not affect observable behavior.

### 24.3 Breaking Change Process

Any change to a frozen area requires:

1. **RFC:** A written proposal in `docs/rfcs/` following the RFC template.
2. **Deprecation warning:** The old behavior must emit a compiler warning for at least one minor version.
3. **Migration guide:** Instructions for updating affected code.
4. **Major version bump:** Breaking changes require a new major version.

---

## 25. Standard Library (v0.9.0)

Seven native stdlib modules written in `.mn`, compiled via LLVM:

| Module | Path | Description |
|---|---|---|
| JSON | `encoding/json.mn` | Recursive descent JSON parser/serializer |
| CSV | `encoding/csv.mn` | RFC 4180 CSV parser/writer |
| HTTP Client | `net/http.mn` | HTTP/1.1 client on C runtime TCP/TLS |
| HTTP Server | `net/http/server.mn` | HTTP server with routing and middleware |
| WebSocket | `net/websocket.mn` | RFC 6455 WebSocket client and server |
| Crypto | `crypto.mn` | SHA-1, SHA-256, HMAC, Base64, random bytes, JWT |
| Regex | `text/regex.mn` | PCRE2-based regular expressions |

### JSON Module (`encoding/json`)

Types: `JsonValue` (enum: Null, Bool, Int, Float, Str, Array, Object), `JsonError`.

Functions:
- `decode(String) -> Result<JsonValue, JsonError>` — parse JSON string.
- `encode(JsonValue) -> String` — serialize to compact JSON.
- `encode_pretty(JsonValue, Int) -> String` — serialize with indentation.
- `stream_parse(String) -> Stream<JsonEvent>` — streaming parser.
- `validate(JsonValue, JsonSchema) -> Result<Bool, List<JsonError>>` — schema validation.

### CSV Module (`encoding/csv`)

Types: `CsvTable` (headers + rows), `CsvError`, `CsvConfig`.

Functions:
- `parse(String) -> Result<CsvTable, CsvError>` — parse CSV string.
- `parse_with(String, CsvConfig) -> Result<CsvTable, CsvError>` — parse with custom config.
- `to_string(CsvTable, String, String) -> String` — serialize to CSV string.
- `write(CsvTable, String) -> Result<Bool, CsvError>` — write to file.

### HTTP Client (`net/http`)

Types: `HttpMethod` (enum), `HttpRequest`, `HttpResponse`, `HttpError`, `HttpConfig`.

Functions:
- `get(String) -> Result<HttpResponse, HttpError>` — HTTP GET.
- `post(String, String) -> Result<HttpResponse, HttpError>` — HTTP POST.
- `put`, `delete`, `patch`, `head`, `options` — other methods.

### HTTP Server (`net/http/server`)

Types: `Route`, `Router`, `MatchResult`, `ServerConfig`.

Functions:
- `new_router() -> Router` — create router.
- `router_add_route(Router, String, String, String) -> Router` — add route.
- `match_route(String, String, String, String) -> MatchResult` — match request.
- `build_response(Int, Map<String, String>, String) -> String` — build HTTP response.

### WebSocket (`net/websocket`)

Types: `WsMessage` (enum: Text, Binary, Ping, Pong, Close), `WsConnection`, `WsError`, `WsFrame`.

Functions:
- `ws_connect(String) -> Result<WsConnection, WsError>` — connect to server.
- `ws_send(WsConnection, WsMessage)` — send message.
- `ws_recv(WsConnection) -> Result<WsMessage, WsError>` — receive message.
- `ws_close(WsConnection)` — close connection.

### Crypto (`crypto`)

Functions: SHA-1, SHA-256, HMAC, Base64 encode/decode, random bytes, JWT helpers. FFI to OpenSSL via `dlopen`.

### Regex (`text/regex`)

Functions: `regex_match`, `regex_search`, `regex_replace`, `regex_split`. Character classes, quantifiers, capture groups via PCRE2 FFI.

---

## Appendix A: Grammar Summary (EBNF Sketch)

This is a simplified sketch of the grammar. The authoritative grammar is in `mapanare/mapanare.lark`.

```ebnf
program        = { import_decl | definition | statement } ;
definition     = fn_def | agent_def | struct_def | enum_def
               | type_alias | pipe_def | impl_def | trait_def
               | impl_trait_def | export_def | extern_fn_def
               | decorated_def | doc_commented_def ;

fn_def         = ["pub"] "fn" IDENT ["<" type_params ">"]
                 "(" [params] ")" ["->" type] block ;
extern_fn_def  = "extern" STRING "fn" IDENT ["::" IDENT]
                 "(" [params] ")" ["->" type] ;
agent_def      = ["pub"] "agent" IDENT "{" { agent_member } "}" ;
struct_def     = ["pub"] "struct" IDENT ["<" type_params ">"]
                 "{" { field_def } "}" ;
enum_def       = ["pub"] "enum" IDENT ["<" type_params ">"]
                 "{" { variant } "}" ;
pipe_def       = ["pub"] "pipe" IDENT "{" pipe_chain "}" ;
impl_def       = "impl" IDENT "{" { fn_def } "}" ;
trait_def      = ["pub"] "trait" IDENT "{" { trait_method } "}" ;
impl_trait_def = "impl" IDENT "for" IDENT "{" { fn_def } "}" ;
import_decl    = "import" path [ "{" names "}" ] ;
export_def     = "export" ( definition | "{" names "}" ) ;
decorated_def  = { decorator } definition ;
decorator      = "@" IDENT [ "(" args ")" ] ;
doc_commented_def = { "///" text } definition ;

agent_member   = "input" IDENT ":" type
               | "output" IDENT ":" type
               | let_binding
               | fn_def ;

pipe_chain     = IDENT { "|>" IDENT } ;

type_expr      = fn_type | tensor_type | generic_type | named_type ;
generic_type   = IDENT "<" type_expr { "," type_expr } ">" ;
tensor_type    = "Tensor" "<" type_expr ">" "[" expr { "," expr } "]" ;
fn_type        = "fn" "(" [ type_expr { "," type_expr } ] ")" "->" type_expr ;

statement      = let_binding | assignment | expr | for_loop
               | while_loop | if_expr | match_expr | return_stmt
               | break_stmt | assert_stmt ;
let_binding    = "let" ["mut"] IDENT [":" type] "=" expr ;
for_loop       = "for" IDENT "in" expr block ;
while_loop     = "while" expr block ;
return_stmt    = "return" [expr] ;
break_stmt     = "break" ;
assert_stmt    = "assert" expr ["," expr] ;

expr           = assign_expr "=>" expr                    (* lambda *)
               | assign_expr ;
assign_expr    = or_expr [ ("=" | "+=" | "-=" | "*=" | "/=") assign_expr ]
               | or_expr "<-" assign_expr ;
or_expr        = and_expr { "||" and_expr } ;
and_expr       = eq_expr { "&&" eq_expr } ;
eq_expr        = cmp_expr { ("==" | "!=") cmp_expr } ;
cmp_expr       = pipe_expr { ("<" | ">" | "<=" | ">=") pipe_expr } ;
pipe_expr      = range_expr { "|>" range_expr } ;
range_expr     = add_expr [ (".." | "..=") add_expr ] ;
add_expr       = mul_expr { ("+" | "-") mul_expr } ;
mul_expr       = unary_expr { ("*" | "/" | "%" | "@") unary_expr } ;
unary_expr     = ("-" | "!") unary_expr | postfix_expr ;
postfix_expr   = atom_expr { call | method_call | field_access | index | "?" } ;

atom_expr      = INT | FLOAT | STRING | CHAR | "true" | "false" | "none"
               | "spawn" IDENT "(" [args] ")"
               | "sync" postfix_expr
               | "signal" "(" expr ")" | "signal" block
               | "stream" "(" expr ")"
               | if_expr | match_expr
               | "new" IDENT "{" { field_init } "}"
               | IDENT "::" "<" type_args ">" "(" [args] ")"  (* turbofish *)
               | IDENT "::" IDENT                              (* namespace *)
               | "self"
               | IDENT
               | "[" [expr { "," expr }] "]"                   (* list *)
               | "#{" [expr ":" expr { "," expr ":" expr }] "}" (* map *)
               | "(" expr ")"
               | "(" expr "," expr { "," expr } ")"           (* tuple *)
               ;
```

---

## Appendix B: Compilation Pipeline

### Overview

The Mapanare compiler uses a multi-stage pipeline with an intermediate representation (MIR) between the AST and final code emission:

```
.mn source --> Lexer --> Parser --> AST --> Semantic Analysis --> MIR Lowering --> MIR Optimizer --> Emitter
                                                                                                    |--> Python (legacy)
                                                                                                    +--> LLVM IR --> Native Binary
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

### Python Transpiler (Legacy)

The Python emitter translates MIR to Python source code. This backend is legacy — kept for reference and bootstrapping only. It is not the target for new features.

### LLVM Native Backend

The LLVM emitter translates MIR to LLVM IR, producing native machine code. This is the production backend.

- Agent spawn/send/sync codegen backed by the C runtime thread pool and ring buffers.
- Compile-time tensor shape verification (element-wise ops and matmul via runtime calls).
- Arena-based memory management with tag-bit string freeing (no garbage collector).
- Ahead-of-time compilation for deployment.
- Cross-compilation to Linux x64, macOS ARM64, Windows x64.

---

## Appendix C: Reserved Keywords

The following identifiers are reserved for future use and cannot be used as variable or function names, even though they have no current semantics:

| Reserved | Potential Future Use |
|---|---|
| `async` | Asynchronous function declaration |
| `await` | Asynchronous expression |
| `yield` | Generator / coroutine yield |
| `macro` | Compile-time macro system |
| `where` | Generic constraint clauses |
| `use` | Path shortening |
| `as` | Type casting / import renaming |
| `const` | Compile-time constants |
| `static` | Module-level mutable state |
| `unsafe` | Escape hatch for memory safety |
| `move` | Explicit ownership transfer |
| `ref` | Reference binding in patterns |
| `loop` | Infinite loop construct |
| `continue` | Skip to next loop iteration |
| `super` | Parent module reference |
| `crate` | Root module reference |
| `mod` | Module declaration |
| `dyn` | Dynamic dispatch |
| `box` | Heap allocation |

Note: These keywords are not currently enforced by the parser. They are reserved by convention to prevent user code from using names that may become keywords in future versions.

---

## Appendix D: Error Code Registry

See section 19.1 for the error code format. The complete registry of assigned error codes:

### Parse Errors (MN-P)

| Code | Description |
|---|---|
| `MN-P0001` | Unexpected token |
| `MN-P0002` | Unterminated string literal |
| `MN-P0003` | Invalid numeric literal |
| `MN-P0004` | Unexpected end of input |

### Semantic Errors (MN-S)

| Code | Description |
|---|---|
| `MN-S0001` | Undefined variable |
| `MN-S0002` | Type mismatch |
| `MN-S0003` | Undefined function |
| `MN-S0004` | Wrong number of arguments |
| `MN-S0005` | Assignment to immutable variable |
| `MN-S0006` | Undefined type |
| `MN-S0007` | Duplicate definition |
| `MN-S0008` | Missing trait method implementation |
| `MN-S0009` | Non-exhaustive match |
| `MN-S0010` | Invalid `?` operator context |

### Lowering Errors (MN-L)

| Code | Description |
|---|---|
| `MN-L0001` | Unsupported AST node in lowering |

### Code Generation Errors (MN-C)

| Code | Description |
|---|---|
| `MN-C0001` | LLVM IR emission failure |
| `MN-C0002` | Linking failure |

### Runtime Errors (MN-R)

| Code | Description |
|---|---|
| `MN-R0001` | Agent mailbox full |
| `MN-R0002` | Index out of bounds |
| `MN-R0003` | Division by zero |
| `MN-R0004` | Assert failure |
| `MN-R0005` | Stack overflow |

### Tooling Errors (MN-T)

| Code | Description |
|---|---|
| `MN-T0001` | Test discovery failure |
| `MN-T0002` | Benchmark failure |
