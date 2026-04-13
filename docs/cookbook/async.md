# Async/Await Cookbook

Progressive tutorial for asynchronous programming in Mapanare. Each example is a complete, runnable program.

See [SPEC.md](../SPEC.md) section 29 for the formal semantics. See the [Coroutine Design Document](../roadmap/v4/v4.67.0/DESIGN.md) for LLVM lowering details.

> **Note:** Async/await uses LLVM coroutine intrinsics implemented in Arc 8-9
> (v4.67.0-v4.76.0). The examples below match the golden tests
> (`tests/golden/55-57_async_*.mn`). The Python bootstrap's `emit-llvm`
> backend does not yet support async; these examples compile through the
> native compiler path (`mnc run`).

---

## 1. Your First Async Function

An `async fn` is a function that can suspend and resume. Calling it returns a `Future<T>` rather than executing the body immediately. Use `block_on` to drive the future from synchronous code.

```mn
async fn compute() -> Int {
    return 42
}

fn main() {
    let result: Int = block_on(compute())
    print(str(result))
}
```

```
42
```

`block_on` runs the event loop until the future completes, then returns the result. It is the bridge between synchronous `main` and the async world.

---

## 2. Await Chains

Inside an `async fn`, use `await` to suspend until another async function completes. The result is unwrapped automatically.

```mn
async fn inner() -> Int {
    return 42
}

async fn outer() -> Int {
    let x: Int = await inner()
    return x + 1
}

fn main() {
    let result: Int = block_on(outer())
    print(str(result))
}
```

```
43
```

`outer` calls `inner` and awaits its result. The coroutine suspends at the `await` point and resumes when `inner` produces a value.

---

## 3. Fan-Out: Multiple Awaits

Await multiple async functions sequentially. Each `await` suspends until its operand is ready, then continues to the next.

```mn
async fn fetch_a() -> Int {
    return 20
}

async fn fetch_b() -> Int {
    return 40
}

async fn fetch_c() -> Int {
    return 50
}

async fn fanout() -> Int {
    let a: Int = await fetch_a()
    let b: Int = await fetch_b()
    let c: Int = await fetch_c()
    return a + b + c
}

fn main() {
    let total: Int = block_on(fanout())
    print(str(total))
}
```

```
110
```

The three fetches run sequentially (each completes before the next starts). Concurrent fan-out with structured concurrency is planned for v5.x.

---

## 4. Async with Computations

Async functions can perform arbitrary computation between await points. Values computed before a suspension are preserved across the suspend/resume boundary.

```mn
async fn double(x: Int) -> Int {
    return x * 2
}

async fn pipeline(n: Int) -> Int {
    let step1: Int = await double(n)
    let step2: Int = await double(step1)
    let step3: Int = await double(step2)
    return step3
}

fn main() {
    // 5 -> 10 -> 20 -> 40
    let result: Int = block_on(pipeline(5))
    print(str(result))
}
```

```
40
```

---

## 5. Async Function Returning Strings

Async works with any return type, not just integers.

```mn
async fn greet(name: String) -> String {
    return "Hello, " + name + "!"
}

fn main() {
    let msg: String = block_on(greet("Mapanare"))
    print(msg)
}
```

```
Hello, Mapanare!
```

---

## 6. `block_on` From Sync Code

`block_on` is the only way to execute async code from a synchronous context. It runs the scheduler's event loop until the given future resolves.

```mn
async fn compute_sum(a: Int, b: Int) -> Int {
    return a + b
}

fn main() {
    let r1: Int = block_on(compute_sum(10, 20))
    let r2: Int = block_on(compute_sum(r1, 30))
    print(str(r2))
}
```

```
60
```

Each `block_on` call drives one future to completion. You can call `block_on` multiple times from `main`, but you cannot nest `block_on` calls (calling `block_on` from inside an async function will deadlock).

---

## 7. Common Pitfalls

### Do not call `block_on` from async code

```mn
// BAD: deadlock
async fn broken() -> Int {
    let x: Int = block_on(some_async_fn())  // deadlocks!
    return x
}
```

Use `await` instead of `block_on` inside async functions. `block_on` blocks the current thread's event loop, which is already running when you're inside an async context.

### Do not forget `await`

```mn
// BAD: result is a Future<Int>, not an Int
async fn fetch() -> Int { return 42 }

async fn caller() -> Int {
    let f = fetch()  // this is a Future<Int>, not 42
    return await f   // you must await to get the value
}
```

If you forget `await`, you get a `Future<T>` value instead of `T`. The semantic checker will catch type mismatches, but the error message may be confusing if you are not familiar with futures.

### Async functions with no `await` are valid

An `async fn` that never uses `await` is a single-step coroutine: it completes immediately on first resume. This is useful for testing or for functions that are async for interface consistency.

```mn
async fn immediate() -> Int {
    return 42  // no await, completes immediately
}
```

---

## See Also

- [SPEC.md](../SPEC.md) section 29 for the formal specification of `Future<T>`, `await`, and `block_on`
- [Coroutine Design Document](../roadmap/v4/v4.67.0/DESIGN.md) for LLVM lowering details
- Golden tests: `tests/golden/55_async_basic.mn`, `56_async_await.mn`, `57_real_await.mn`
