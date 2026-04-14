# Async/Await Cookbook

Progressive tutorial for asynchronous programming in Mapanare. Each example is a complete, runnable program.

See [SPEC.md](../SPEC.md) section 29 for the formal semantics. See the [Coroutine Design Document](../roadmap/v4/v4.67.0/DESIGN.md) for LLVM lowering details. For the mental model, limitations, and Sh.9 workarounds, see the companion [`docs/guides/async.md`](../guides/async.md).

> **Note (corrected v4.116.0):** the earlier edition of this cookbook
> stated that async programs compile through `mnc run` (the native
> compiler path). That is reversed from current reality. Async examples
> compile through the **Python bootstrap** `emit-llvm` path today and
> link against `libmapanare_rt.a` for a native binary. The self-hosted
> compiler (`mnc-stage1`) does **not** yet lower async (docket Sh.4,
> carry-forward from Phase D). The golden tests
> (`tests/golden/55-57_async_*.mn`) run under the bootstrap pipeline in
> CI. The "async runs natively" claim is still true — it's the generated
> binary that is native, not the compiler driver.

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

---

## 8. Native Compilation Workflow (v4.115.0+)

Every example above compiles to a native binary via the same pipeline.
The Python bootstrap emits LLVM IR; `clang` links it against
`libmapanare_rt.a`. Compiler driver in Python; runtime fully native.

```bash
# Emit LLVM IR from the .mn source
python3 -m mapanare emit-llvm program.mn -o /tmp/program.ll

# Link against the native runtime
clang /tmp/program.ll \
      -L runtime/native -lmapanare_rt \
      -lpthread -lm -ldl \
      -o /tmp/program

# Run
/tmp/program
```

The same pipeline works at `-O2`:

```bash
clang -O2 /tmp/program.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl -o /tmp/program
```

> **Why not `mnc-stage1`?** The self-hosted compiler does not lower
> `async`/`await`/`block_on` yet. Five async golden tests are blocked
> behind docket Sh.4. Until it ships, the Python bootstrap is the
> route for async programs.

## 9. Real File I/O Inside an Async Pipeline (v4.115.0)

From [`examples/async_file_io.mn`](../../examples/async_file_io.mn).
Runs byte-based counters over the content of `/tmp/async_input.txt` and
writes a summary file from inside an `await write_summary(...)` call.

```mn
extern "C" fn __mn_file_read_or_empty(path: String) -> String
extern "C" fn __mn_file_write(path: String, content: String) -> Int

async fn count_lines(content: String) -> Int {
    let mut n: Int = 0
    let mut i: Int = 0
    let limit: Int = len(content)
    while i < limit {
        if content.byte_at(i) == 10 { n = n + 1 }
        i = i + 1
    }
    return n
}

async fn write_summary(path: String, lines: Int) -> Int {
    return __mn_file_write(path, "lines=" + str(lines) + "\n")
}

async fn process(content: String) -> Int {
    let lines: Int = await count_lines(content)
    let wrote: Int = await write_summary("/tmp/out.txt", lines)
    return wrote + lines                       // fold wrote in; see §11 Sh.9b
}

fn main() {
    let content: String = __mn_file_read_or_empty("/tmp/async_input.txt")
    let encoded: Int = block_on(process(content))
    print("done: " + str(encoded))
}
```

Expected output given a three-line input file:

```
done: 3
```

## 10. Real HTTP GET Inside an Async Pipeline (v4.115.0)

From [`examples/async_http_demo.mn`](../../examples/async_http_demo.mn).
Issues a real HTTP GET to `http://example.com/`, runs a three-stage
async pipeline over the body, and writes a summary file.

```bash
python3 -m mapanare emit-llvm examples/async_http_demo.mn -o /tmp/ahd.ll
clang /tmp/ahd.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl \
      -o /tmp/async_http_demo
/tmp/async_http_demo
```

Sample output when the network is reachable:

```
fetched bytes=540
pipeline bytes=540 marker=1
summary file path: /tmp/async_http_demo_summary.txt
```

If the sandbox blocks outbound TCP, the demo exits 0 after printing a
"network unreachable" line — CI-safe by design.

## 11. Two Emitter Bugs to Know About (Sh.9)

Two Python bootstrap emitter bugs were found while writing the v4.115.0
demos. Both have simple workarounds. These are open dockets for a
future release.

### Sh.9a — `await` on a String-returning async fn emits invalid IR

```mn
// BROKEN: llvm-as rejects the generated IR
async fn read_it() -> String { return "hello" }
async fn use_it() -> Int {
    let s: String = await read_it()   // emitter produces a type mismatch
    return len(s)
}
```

**Workaround:** fetch String content *before* entering the async
pipeline and pass it as a parameter:

```mn
fn main() {
    let content: String = __mn_file_read_or_empty("/tmp/in.txt")
    let r: Int = block_on(process(content))   // async fn takes String param
    print(str(r))
}
```

### Sh.9b — DCE drops `await` calls whose Int return is unused

```mn
// BROKEN: write never happens
async fn write_it() -> Int { return __mn_file_write("/tmp/x", "hi") }
async fn run() -> Int {
    let _w: Int = await write_it()   // return unused → DCE drops the whole call
    return 0
}
```

**Workaround:** always fold the `await` result into a later expression —
easiest is the return value:

```mn
async fn run() -> Int {
    let w: Int = await write_it()
    return w                          // w is used, DCE leaves it alone
}
```

Both workarounds appear in the v4.115.0 demos verbatim. Track progress
in the next release's PLAN.md.

---

## See Also

- [SPEC.md](../SPEC.md) section 29 for the formal specification of `Future<T>`, `await`, and `block_on`
- [`docs/guides/async.md`](../guides/async.md) — mental model, limitations table, further reading
- [Coroutine Design Document](../roadmap/v4/v4.67.0/DESIGN.md) for LLVM lowering details
- Golden tests: `tests/golden/55_async_basic.mn`, `56_async_await.mn`, `57_real_await.mn`
- Examples: `examples/async_file_io.mn`, `examples/async_http_demo.mn` (both shipped in v4.115.0)
