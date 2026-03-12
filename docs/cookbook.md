# Mapanare Cookbook

Real-world examples and patterns for common tasks. Each recipe is a complete, runnable program.

---

## Table of Contents

1. [Hello World with Interpolation](#1-hello-world-with-interpolation)
2. [Fibonacci Sequence](#2-fibonacci-sequence)
3. [Reading and Processing a List](#3-reading-and-processing-a-list)
4. [Error Handling Pipeline](#4-error-handling-pipeline)
5. [Struct with Methods](#5-struct-with-methods)
6. [Enum State Machine](#6-enum-state-machine)
7. [Generic Data Structures](#7-generic-data-structures)
8. [Agent: Background Worker](#8-agent-background-worker)
9. [Multi-Agent Data Pipeline](#9-multi-agent-data-pipeline)
10. [Reactive Signals: Temperature Monitor](#10-reactive-signals-temperature-monitor)
11. [Stream Processing](#11-stream-processing)
12. [Calling Python Libraries](#12-calling-python-libraries)
13. [Trait Polymorphism](#13-trait-polymorphism)
14. [Command-Line Calculator](#14-command-line-calculator)

---

## 1. Hello World with Interpolation

The simplest Mapanare program, using string interpolation.

```mn
fn main() {
    let name = "Mapanare"
    let version = "0.5.0"
    println("Hello from ${name} v${version}!")
}
```

```bash
mapanare run hello.mn
# Output: Hello from Mapanare v0.5.0!
```

---

## 2. Fibonacci Sequence

Recursive and iterative approaches.

```mn
// Recursive
fn fib(n: Int) -> Int {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

// Iterative (much faster)
fn fib_iter(n: Int) -> Int {
    let mut a = 0
    let mut b = 1
    for _ in 0..n {
        let temp = b
        b = a + b
        a = temp
    }
    return a
}

fn main() {
    for i in 0..10 {
        println("fib(${str(i)}) = ${str(fib(i))}")
    }

    println("fib(40) = ${str(fib_iter(40))}")
}
```

---

## 3. Reading and Processing a List

Working with lists: create, filter, transform, aggregate.

```mn
fn main() {
    let mut numbers: List<Int> = []
    for i in 1..=20 {
        numbers.push(i)
    }

    // Find even numbers
    let mut evens: List<Int> = []
    for n in numbers {
        if n % 2 == 0 {
            evens.push(n)
        }
    }

    // Sum
    let mut total = 0
    for n in evens {
        total += n
    }

    println("even numbers: ${str(evens.length())}")
    println("sum of evens: ${str(total)}")
}
```

---

## 4. Error Handling Pipeline

Chaining operations that can fail using `Result<T, E>` and `?`.

```mn
fn parse_number(s: String) -> Result<Int, String> {
    // Simulate parsing
    if s == "42" {
        return Ok(42)
    }
    if s == "10" {
        return Ok(10)
    }
    return Err("invalid number: ${s}")
}

fn validate_positive(n: Int) -> Result<Int, String> {
    if n <= 0 {
        return Err("number must be positive, got ${str(n)}")
    }
    return Ok(n)
}

fn process(input: String) -> Result<Int, String> {
    let n = parse_number(input)?
    let valid = validate_positive(n)?
    return Ok(valid * 2)
}

fn main() {
    let result1 = process("42")
    match result1 {
        Ok(v) => println("success: ${str(v)}"),
        Err(e) => println("error: ${e}"),
    }

    let result2 = process("bad")
    match result2 {
        Ok(v) => println("success: ${str(v)}"),
        Err(e) => println("error: ${e}"),
    }
}
```

Output:
```
success: 84
error: invalid number: bad
```

---

## 5. Struct with Methods

Define data types and attach behavior.

```mn
struct Rectangle {
    width: Float,
    height: Float,
}

impl Rectangle {
    fn area(self) -> Float {
        return self.width * self.height
    }

    fn perimeter(self) -> Float {
        return 2.0 * (self.width + self.height)
    }

    fn is_square(self) -> Bool {
        return self.width == self.height
    }

    fn scale(self, factor: Float) -> Rectangle {
        return Rectangle(self.width * factor, self.height * factor)
    }
}

fn main() {
    let rect = Rectangle(5.0, 3.0)
    println("area: ${str(rect.area())}")
    println("perimeter: ${str(rect.perimeter())}")
    println("is square: ${str(rect.is_square())}")

    let big = rect.scale(2.0)
    println("scaled area: ${str(big.area())}")
}
```

---

## 6. Enum State Machine

Model application states with enums and pattern matching.

```mn
enum OrderStatus {
    Pending,
    Confirmed(String),
    Shipped(String),
    Delivered,
    Cancelled(String),
}

fn describe_status(status: OrderStatus) -> String {
    match status {
        Pending => return "Order is pending",
        Confirmed(id) => return "Confirmed with ID: ${id}",
        Shipped(tracking) => return "Shipped — tracking: ${tracking}",
        Delivered => return "Package delivered!",
        Cancelled(reason) => return "Cancelled: ${reason}",
    }
}

fn advance(status: OrderStatus) -> OrderStatus {
    match status {
        Pending => return OrderStatus_Confirmed("ORD-001"),
        Confirmed(_) => return OrderStatus_Shipped("TRACK-42"),
        Shipped(_) => return OrderStatus_Delivered,
        _ => return status,
    }
}

fn main() {
    let mut order = OrderStatus_Pending
    for _ in 0..3 {
        println(describe_status(order))
        order = advance(order)
    }
    println(describe_status(order))
}
```

---

## 7. Generic Data Structures

Build reusable containers with generics.

```mn
struct Stack<T> {
    items: List<T>,
}

fn new_stack<T>() -> Stack<T> {
    let items: List<T> = []
    return Stack(items)
}

fn push<T>(stack: Stack<T>, value: T) -> Stack<T> {
    stack.items.push(value)
    return stack
}

fn peek<T>(stack: Stack<T>) -> Option<T> {
    if stack.items.length() == 0 {
        return none
    }
    return Some(stack.items[stack.items.length() - 1])
}

fn size<T>(stack: Stack<T>) -> Int {
    return stack.items.length()
}

fn main() {
    let mut s = new_stack()
    s = push(s, 10)
    s = push(s, 20)
    s = push(s, 30)

    println("size: ${str(size(s))}")

    match peek(s) {
        Some(v) => println("top: ${str(v)}"),
        None => println("empty"),
    }
}
```

---

## 8. Agent: Background Worker

Use an agent for concurrent processing.

```mn
agent Validator {
    input data: String
    output result: String

    fn handle(data: String) -> String {
        if data.length() == 0 {
            return "INVALID: empty input"
        }
        if data.length() > 100 {
            return "INVALID: too long (${str(data.length())} chars)"
        }
        return "VALID: ${data}"
    }
}

fn main() {
    let v = spawn Validator()

    // Validate multiple inputs
    let inputs = ["hello", "", "Mapanare is great"]
    for input in inputs {
        v.data <- input
        let result = sync v.result
        println(result)
    }

    sync v.stop()
}
```

---

## 9. Multi-Agent Data Pipeline

Chain agents for staged data processing.

```mn
agent Parser {
    input raw: String
    output parsed: Int

    fn handle(raw: String) -> Int {
        // Simple length-based "parsing"
        return raw.length()
    }
}

agent Transformer {
    input value: Int
    output result: Int

    fn handle(value: Int) -> Int {
        return value * value
    }
}

agent Formatter {
    input value: Int
    output text: String

    fn handle(value: Int) -> String {
        return "Result: ${str(value)}"
    }
}

fn main() {
    let p = spawn Parser()
    let t = spawn Transformer()
    let f = spawn Formatter()

    // Pipeline: "hello" -> len(5) -> 25 -> "Result: 25"
    p.raw <- "hello"
    let parsed = sync p.parsed

    t.value <- parsed
    let transformed = sync t.result

    f.value <- transformed
    let output = sync f.text

    println(output)

    sync p.stop()
    sync t.stop()
    sync f.stop()
}
```

Output:
```
Result: 25
```

---

## 10. Reactive Signals: Temperature Monitor

Signals automatically propagate changes through dependent computations.

```mn
fn main() {
    // Raw sensor signal
    let mut temp_celsius = signal(20.0)

    // Derived signals — auto-update when temp changes
    let temp_fahrenheit = signal { temp_celsius.value * 9.0 / 5.0 + 32.0 }
    let is_hot = signal { temp_celsius.value > 30.0 }

    println("${str(temp_celsius.value)}C = ${str(temp_fahrenheit.value)}F")
    println("hot: ${str(is_hot.value)}")

    // Update the source — derived values recompute automatically
    temp_celsius.value = 35.0
    println("${str(temp_celsius.value)}C = ${str(temp_fahrenheit.value)}F")
    println("hot: ${str(is_hot.value)}")
}
```

Output:
```
20.0C = 68.0F
hot: false
35.0C = 95.0F
hot: true
```

---

## 11. Stream Processing

Process sequences of data with composable operators.

```mn
fn main() {
    let numbers = stream([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    // Filter, transform, and collect
    let result = numbers
        |> filter((n) => n % 2 == 0)
        |> map((n) => n * n)

    let collected = sync result.collect()
    println(str(collected))
}
```

Output:
```
[4, 16, 36, 64, 100]
```

### Stream with Fold

```mn
fn main() {
    let data = stream([1, 2, 3, 4, 5])

    // Sum all elements
    let total = data |> fold(0, (acc, x) => acc + x)
    println("sum: ${str(sync total)}")
}
```

---

## 12. Calling Python Libraries

Use `extern "Python"` to call any Python function.

```mn
extern "Python" fn math::sqrt(x: Float) -> Float
extern "Python" fn math::floor(x: Float) -> Float

fn distance(x1: Float, y1: Float, x2: Float, y2: Float) -> Float {
    let dx = x2 - x1
    let dy = y2 - y1
    return math::sqrt(dx * dx + dy * dy)
}

fn main() {
    let d = distance(0.0, 0.0, 3.0, 4.0)
    println("distance: ${str(d)}")
}
```

### With Error Handling

```mn
extern "Python" fn json::loads(s: String) -> Result<String, String>

fn main() {
    let valid = json::loads("{\"name\": \"Mapanare\"}")
    match valid {
        Ok(data) => println("parsed: ${data}"),
        Err(e) => println("error: ${e}"),
    }

    let invalid = json::loads("not json")
    match invalid {
        Ok(data) => println("parsed: ${data}"),
        Err(e) => println("parse error: ${e}"),
    }
}
```

---

## 13. Trait Polymorphism

Define shared interfaces and implement them for different types.

```mn
trait Describable {
    fn describe(self) -> String
}

struct Dog {
    name: String,
    breed: String,
}

struct Cat {
    name: String,
    indoor: Bool,
}

impl Describable for Dog {
    fn describe(self) -> String {
        return "${self.name} is a ${self.breed} dog"
    }
}

impl Describable for Cat {
    fn describe(self) -> String {
        if self.indoor {
            return "${self.name} is an indoor cat"
        }
        return "${self.name} is an outdoor cat"
    }
}

fn print_description<T: Describable>(item: T) {
    println(item.describe())
}

fn main() {
    let dog = Dog("Rex", "Golden Retriever")
    let cat = Cat("Whiskers", true)

    print_description(dog)
    print_description(cat)
}
```

---

## 14. Command-Line Calculator

A small program combining parsing, error handling, and pattern matching.

```mn
enum Op {
    Add,
    Sub,
    Mul,
    Div,
}

fn parse_op(s: String) -> Result<Op, String> {
    match s {
        "+" => return Ok(Op_Add),
        "-" => return Ok(Op_Sub),
        "*" => return Ok(Op_Mul),
        "/" => return Ok(Op_Div),
        _ => return Err("unknown operator: ${s}"),
    }
}

fn calculate(a: Float, op: Op, b: Float) -> Result<Float, String> {
    match op {
        Add => return Ok(a + b),
        Sub => return Ok(a - b),
        Mul => return Ok(a * b),
        Div => {
            if b == 0.0 {
                return Err("division by zero")
            }
            return Ok(a / b)
        },
    }
}

fn main() {
    let result = calculate(10.0, Op_Add, 5.0)
    match result {
        Ok(v) => println("10 + 5 = ${str(v)}"),
        Err(e) => println("error: ${e}"),
    }

    let result2 = calculate(10.0, Op_Div, 0.0)
    match result2 {
        Ok(v) => println("10 / 0 = ${str(v)}"),
        Err(e) => println("error: ${e}"),
    }
}
```

Output:
```
10 + 5 = 15.0
error: division by zero
```

---

## Tips and Patterns

### Prefer `Result` over Panics

Always return `Result<T, E>` from functions that can fail. Use `?` to propagate errors.

### Use Agents for Concurrent Work

If a task can run independently, wrap it in an agent. Agents handle concurrency, backpressure, and lifecycle automatically.

### Use Signals for Reactive State

When multiple values depend on a source, use signals instead of manual update calls.

### Leverage the Pipe Operator

The `|>` operator makes data flow read left-to-right:

```mn
let result = data |> transform |> validate |> format
// instead of: format(validate(transform(data)))
```

### String Interpolation over Concatenation

```mn
// Prefer this:
println("Hello, ${name}! You are ${str(age)} years old.")

// Over this:
println("Hello, " + name + "! You are " + str(age) + " years old.")
```

---

*For the full language reference, see [reference.md](reference.md).*
*For the language specification, see [SPEC.md](SPEC.md).*
