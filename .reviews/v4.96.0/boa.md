# Boa — Python/DX Review (Arc 13)

**Grade: 9/10**
**Verdict: PASS**

## Assessment

### async/await developer experience

The async surface is clean and familiar:
```mapanare
async fn fetch() -> Int { return 42 }
fn main() {
    let result = block_on(fetch())
    print(str(result))
}
```

This reads naturally. `async fn` marks a coroutine, `await` suspends, `block_on` drives from synchronous context. The pattern matches Rust (`tokio::block_on`), Python (`asyncio.run`), and Swift (`async let`). A developer coming from any of these languages will be productive immediately.

### spawn() builtin

`spawn(async_call())` returns a Future handle and registers with the scheduler. This is the Go `go func()` equivalent but returns a handle for later `await`. Clean API. The naming is intuitive (Tokio uses `tokio::spawn`, Go uses `go`).

### StringBuilder builtins

`sb_create()`, `sb_append(sb, str)`, `sb_to_string(sb)` — explicit and clear. The naming follows the Java/C# `StringBuilder` convention. The pattern:
```mapanare
let mut sb = sb_create()
sb_append(sb, "hello")
sb_append(sb, " world")
let result = sb_to_string(sb)
```

This is functional but verbose compared to Go's `strings.Builder` or Rust's `String::push_str`. A future version could add method syntax (`sb.append("hello")`) to reduce ceremony. Not blocking.

### Error messages

The existing error infrastructure handles `block_on` and `spawn` as builtins — calling them with wrong arity produces "Undefined function" or arity mismatch errors. These are not async-specific errors. A future version should provide:
- "await used outside async fn" (currently caught by the semantic checker)
- "block_on called with non-Future argument"
- "spawn called with non-async-fn result"

### Test updates for v4.92.0

The 6 async test updates (block_on.py, async_golden.py, coroutine_lowering.py) correctly reflect the new scheduler-driven model. Test names were updated (`test_block_on_emits_scheduler_call` instead of `test_block_on_emits_resume_loop`). Good DX for test maintainers.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| Method syntax for StringBuilder (`sb.append(x)`) | MEDIUM | Reduces ceremony for explicit API |
| Async-specific error messages | LOW | Better DX for common mistakes |

## Score justification

9/10 — the async surface is clean and familiar. StringBuilder API is functional. spawn() is intuitive. Test updates maintain quality. Minor ceremony in StringBuilder usage noted but not blocking.
