# Pre-Panel Audit — v4.71.0 (Arc 8: Coroutine Foundation)

> Arc 8 scope is **foundation only**: design doc, grammar, semantic analysis,
> prelude lowering. Runnable async (suspension, scheduler, end-to-end) arrives
> in Arc 9 (v4.72.0-v4.76.0). `await` deliberately errors at compile time.

## SESSION_REPORT fact-check

| Release | Claim | Verification |
|---------|-------|-------------|
| v4.67.0 | DESIGN.md has 8 sections + 3 appendices | `grep '^## ' docs/roadmap/v4/v4.67.0/DESIGN.md` — confirmed 8 + 3 |
| v4.67.0 | 4 reviewers signed off (Rattler APPROVED) | Recorded in SESSION_REPORT.md §Informal Review Feedback |
| v4.68.0 | 14 parser + 5 interim tests | `tests/parser/test_async_await.py` (14), `tests/semantic/test_async_interim_error.py` (5) — confirmed |
| v4.68.0 | `await` at unary precedence | `test_await_binds_tighter_than_addition` + `test_await_binds_looser_than_field_access` — confirmed |
| v4.68.0 | Delta review PASS from 3 reviewers | `.reviews/deltas/v4.68.0-async-grammar.md` — confirmed |
| v4.69.0 | TypeKind.FUTURE in enum + registries | `mapanare/types.py:43,83,255,267,280` — confirmed |
| v4.69.0 | Async fn return type wrapped in Future<T> | `test_async_fn_returns_future` in test_async_semantics.py — confirmed |
| v4.69.0 | 3 new semantic errors | await-outside-async, await-on-non-Future, forgot-to-await — confirmed in tests |
| v4.70.0 | `presplitcoroutine` attribute on async fn | `test_async_fn_has_presplitcoroutine` — confirmed |
| v4.70.0 | 12 coro intrinsic declarations | `test_coro_intrinsic_declarations` — confirmed |
| v4.70.0 | `await` errors at v4.72.0 target | `test_await_expr_errors_at_v4_72` — confirmed |

## Test summary

| Test file | Tests | Status |
|-----------|-------|--------|
| `tests/parser/test_async_await.py` | 14 | PASS |
| `tests/semantic/test_async_interim_error.py` | 5 | PASS |
| `tests/semantic/test_async_semantics.py` | 11 | PASS |
| `tests/llvm/test_coroutine_prelude.py` | 11 | PASS |
| **Total async tests** | **41** | **PASS** |

## Demo: async fn compile + IR

```mapanare
async fn compute() -> Int {
    return 42
}
fn main() -> Int { return 0 }
```

Produces IR with: `define ptr @compute(...) presplitcoroutine`, `@llvm.coro.id`,
`@llvm.coro.begin`, `@llvm.coro.suspend` (initial + final), `coro.cleanup:` +
`@llvm.coro.free`, `coro.ret:` + `@llvm.coro.end`, `ret ptr %future`.

## v4.66.0 action items status

| # | Item | Status |
|---|------|--------|
| 1 | cmd_build -g to clang | OPEN (deferred, not async-related) |
| 2 | Integration test with llvm-dwarfdump | OPEN |
| 3 | gdb debugging tutorial | OPEN |
| 4 | check_dwarf.sh in CI | OPEN |
| 5 | A2 dual-closure for self-hosted emitter | OPEN |
| 6 | 6 v4.61.0 items | OPEN (tracked) |
| 7 | vacuous test_ret_instruction_has_dbg | OPEN |
| 8 | Local variable debug info tests | OPEN |

**Note:** These are Arc 7 items. Arc 8 focused entirely on coroutine foundation
per the 5-minor arc cadence. These items carry forward to Arc 9.
