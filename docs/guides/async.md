# Async Programming in Mapanare

> Status as of v4.115.0. Scope: native binaries produced by the
> Python bootstrap emitter + `libmapanare_rt.a`. The self-hosted
> compiler (mnc-stage1) does not yet lower async; that's docket
> Sh.4 for a future release.

Mapanare supports cooperative async through three keywords:
`async fn`, `await`, and `block_on(expr)`. Under the hood the
emitter lowers every `async fn` to an LLVM coroutine using the
switched-resume ABI, and `block_on` drives the scheduler until
the root coroutine reaches its final suspend.

This guide shows how to use the three keywords, what works today,
and what's still to come.

---

## Mental model

**Cooperative.** When an async fn hits an `await`, it may yield
back to the scheduler. When the awaited task completes, the
scheduler resumes the suspended coroutine.

**Not preemptive.** The runtime does not preempt a coroutine mid-
computation. Pure-compute async fns run straight through; they
only yield at `await` points. Full non-blocking suspension at
arbitrary points is a v5.x target.

**Cooperative I/O.** The C runtime's file-I/O and network-I/O
calls are synchronous. An async fn that calls `__mn_file_write`
blocks the current worker for the duration of the write — this
is equivalent to Go before goroutines or early Node.js file ops.
The async structure still provides composition (chain via
`await`) and a place to hang future non-blocking wiring.

---

## Syntax

### `async fn`

Declares a coroutine-lowered function. Its return type is
conceptually `Future<T>` but written as the underlying T; the
emitter wraps it.

```mn
async fn square(x: Int) -> Int {
    return x * x
}
```

### `await`

Inside an async fn, `await` resumes another async fn and yields
back to the scheduler until the awaited future resolves. The
expression has the type of the awaited return.

```mn
async fn sum_of_squares(a: Int, b: Int) -> Int {
    let x: Int = await square(a)
    let y: Int = await square(b)
    return x + y
}
```

### `block_on`

From a non-async function, `block_on(expr)` runs an async fn to
completion and returns its value. This is the only way to invoke
an async fn from `main()`.

```mn
fn main() {
    let total: Int = block_on(sum_of_squares(3, 4))
    print(str(total))   // 25
}
```

---

## End-to-end: file I/O

The complete program at `examples/async_file_io.mn` reads a
seed file, counts lines and words through an async pipeline, and
writes a summary back to disk. The sketch:

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
    return wrote + lines        // fold wrote into return; see Sh.9 below
}

fn main() {
    let content: String = __mn_file_read_or_empty("/tmp/in.txt")
    let encoded: Int = block_on(process(content))
    print("done: " + str(encoded))
}
```

Compile and run:

```
python3 -m mapanare emit-llvm examples/async_file_io.mn -o /tmp/afi.ll
clang /tmp/afi.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl \
      -o /tmp/async_file_io
/tmp/async_file_io
```

The full example also works at `-O2` (clang -O2 against the emitted IR).

---

## End-to-end: HTTP GET

The complete program at `examples/async_http_demo.mn` issues a
real HTTP GET to `http://example.com/`, runs an async pipeline
over the response body, and writes a summary file. The network
request itself is a synchronous call to `http_get(url)` which
lowers to `__mn_http_get` in the C runtime (libcurl-backed where
available, falls back to a socket path).

```
python3 -m mapanare emit-llvm examples/async_http_demo.mn -o /tmp/ahd.ll
clang /tmp/ahd.ll -L runtime/native -lmapanare_rt -lpthread -lm -ldl \
      -o /tmp/async_http_demo
/tmp/async_http_demo
# fetched bytes=540
# pipeline   bytes=540 marker=1
# summary file path: /tmp/async_http_demo_summary.txt
```

If the sandbox blocks outbound TCP, `http_get` returns an empty
String; the program prints "network unreachable" and exits 0.
CI-safe.

---

## What works today

| Feature | Status | Pipeline |
|---|---|---|
| `async fn foo() -> Int` | yes | Python bootstrap |
| `await` on Int-returning async fn | yes | Python bootstrap |
| Chain of N awaits inside one async fn | yes | Python bootstrap |
| `block_on(async_fn(...))` from `main()` | yes | Python bootstrap |
| Real file I/O from inside an async pipeline | yes (v4.115.0) | Python bootstrap |
| Real network I/O from inside an async pipeline | yes (v4.115.0) | Python bootstrap |
| Async goldens at -O2 | yes | Python bootstrap |

## What does not work yet

| Gap | Docket | Notes |
|---|---|---|
| Self-hosted `mnc-stage1` lowers async | Sh.4 | 5 goldens blocked; carry-forward from Phase D |
| `await` on String-returning async fn | Sh.9 | Emitter produces invalid IR — fetch String synchronously before entering the pipeline |
| Unused-await DCE | Sh.9 | Emitter DCE eliminates awaits whose Int return is unused — fold result into the pipeline's return |
| Non-blocking (true suspension) file I/O | Sh.10 (opened v4.115.0) | `__mn_file_read_async` exists in the C runtime but is not reachable from Mapanare source until Sh.9 ships |
| Async iterators / streams | — | v5.x |
| Preemptive multi-threaded scheduler | — | Current scheduler is inline-resume; multi-thread deque exists but block_on drives single-worker |

## Recipe catalog

### Fan-out: run N async tasks concurrently

Today the scheduler is inline-resume; `await a(); await b()` runs
sequentially, not concurrently. Fan-out through `spawn` is wired
in the C runtime (`__mn_coro_spawn`) but has no Mapanare surface
yet. See golden `57_real_await.mn` for the await-chain pattern.

### Read a file, process, write a file

See `examples/async_file_io.mn`.

### Fetch a URL, parse, write a summary

See `examples/async_http_demo.mn`.

### Avoid the Sh.9 DCE trap

Always use the `await` result in a later expression. The simplest
pattern: fold it into the return value.

```mn
async fn pipeline() -> Int {
    let x: Int = await do_something()
    let w: Int = await write_it()          // Int, but only called for side effect
    return w + x                           // ← w used, so not DCE'd
}
```

### Avoid the Sh.9 String-await trap

Fetch String content *before* entering the async pipeline:

```mn
fn main() {
    let content: String = __mn_file_read_or_empty("/tmp/in.txt")
    let r: Int = block_on(process(content))    // async fn takes String param
    print(str(r))
}
```

Do not write:

```mn
async fn read_it() -> String { ... }

async fn process() -> Int {
    let s: String = await read_it()        // ← breaks at emit time
    ...
}
```

---

## Further reading

- `tests/golden/55_async_basic.mn` — minimal async fn + block_on
- `tests/golden/56_async_await.mn` — two-level await chain
- `tests/golden/57_real_await.mn` — four async fns, fanout-style await chain
- `examples/async_file_io.mn` — full file-I/O pipeline (v4.115.0)
- `examples/async_http_demo.mn` — full network pipeline (v4.115.0)
- `runtime/native/mapanare_runtime.c:1670` — the scheduler implementation
- `runtime/native/mapanare_runtime.c:1539` — coroutine frame prefix (v4.113.0)
