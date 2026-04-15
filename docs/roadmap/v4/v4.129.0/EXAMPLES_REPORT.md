# v4.129.0 Examples Verification Report

**Date:** 2026-04-15
**Total examples:** 29 `.mn` files under `examples/`
**Method:** `python3 -m mapanare check <file>` for every example. For
WASM examples, also `python3 -m mapanare emit-wasm` to catch
backend-specific errors.

## Summary

| Status | Count | Percentage |
|---|---|---|
| PASS | 16 | 55% |
| FAIL | 13 | 45% |

Per-category breakdown of the 13 failures:

| Cause | Count | Files |
|---|---|---|
| Multi-line list/tensor literal (grammar limitation) | 5 | ai/basic_chat, ai/basic_stream, ai/chat_agent, ai/rag_agent, tensor/matrix_ops |
| `stdlib/gpu/tensor.mn` + `kernel.mn` qualified-type-ref bug | 3 | experimental/gpu/{benchmark,matmul,neural_net} |
| Stale `@Counter()` spawn syntax | 2 | experimental/mobile/{android,ios}/app |
| `extern "Python" fn` removed v4.29.0 | 2 | packages/mn_http/main, packages/mn_json/main |
| Module-level `let mut` invisible to functions | 1 | wasm/dom_app |

Per PROMPT.md Decision 2: "document the failure. Add a comment at
the top of the example noting the known issue and docket ID. Do not
teach workarounds for bugs." This release adds header comments to
each failing example citing the cause below. **No bug fixes or
workarounds in this release.**

---

## PASS list (16)

```
examples/async_file_io.mn
examples/async_http_demo.mn
examples/bind/math_lib.mn
examples/cli/todo.mn
examples/cli/word_count.mn
examples/gpu/matmul_bench.mn
examples/gpu/vector_add.mn
examples/network/http_fetch.mn
examples/packages/mn_collections/main.mn
examples/transpile/collatz.mn
examples/transpile/fibonacci.mn
examples/transpile/fibonacci_bench.mn
examples/transpile/primes.mn
examples/wasm/cloudflare-worker/worker.mn
examples/wasm/hello.mn
examples/wasm/wasi_app.mn
```

---

## FAIL details

### Category A — Multi-line list/tensor literal (5 files)

**Error shape:** `error: Unexpected newline — expected '#{', '(',
'[', ']', 'if', ...`

**Root cause:** The LALR grammar at `mapanare/mapanare.lark:...`
does not permit list or tensor literals to span multiple lines. A
list like

```mn
let xs = [
    1,
    2,
]
```

is rejected at the newline after `[`. Single-line literals work
fine.

**Not a release regression.** Reproduces on `/tmp` scratch files
containing the minimal multi-line list form. This is a pre-existing
grammar limitation, not something v4.117.0–v4.128.0 broke.

**Affected examples:**
- `examples/ai/basic_chat.mn` — line 16:38 inside `llm.chat` args
- `examples/ai/basic_stream.mn` — line 16:43 same pattern
- `examples/ai/chat_agent.mn` — line 27:36
- `examples/ai/rag_agent.mn` — line 29:13
- `examples/tensor/matrix_ops.mn` — line 12:31 inside `Tensor<Float>[...]`

**Docket:** open a new `Gr.1` (grammar) entry for multi-line
collection literals. Out of scope for v4.129.0. Fix in a future
parser release.

### Category B — stdlib qualified-type-ref bug (3 files)

**Error shape:** `error: Unexpected dot ('.') — expected '#{',
'(', ')', ',', '=', ...` in `stdlib/gpu/tensor.mn:90:19` or
`stdlib/gpu/kernel.mn:63:20`.

**Root cause:** stdlib source uses `device.DeviceKind` as a
qualified type reference (field type / parameter type). The grammar
accepts qualified names only in expression positions, not in type
positions.

**Not an example bug.** The three examples (`experimental/gpu/*.mn`)
are blocked by a broken stdlib module upstream. Opening a new
`Gr.2` docket for qualified-type-refs in type position. Fix belongs
in grammar + `types.py`, not in the examples or this release.

**Affected examples:**
- `examples/experimental/gpu/benchmark.mn`
- `examples/experimental/gpu/matmul.mn`
- `examples/experimental/gpu/neural_net.mn`

All three transitively import `stdlib/gpu/tensor.mn`. Fixing the
stdlib file (bare `DeviceKind` instead of `device.DeviceKind`) plus
adjusting the imports would close these three — but that's a
stdlib edit, not a docs edit.

### Category C — Stale spawn syntax (2 files)

**Error shape:** `error: Unexpected at ('@') — expected '#{',
'(', '[', 'if', 'none', ...` at `@Counter()`.

**Root cause:** The mobile example uses `@Counter()` as agent spawn
syntax. Per SPEC §9.3, spawning is `spawn Name` — `@` is decorator
syntax only. The examples were written against an earlier draft
(pre-v2.0.0?) and never updated.

**Affected examples:**
- `examples/experimental/mobile/android/app.mn`
- `examples/experimental/mobile/ios/app.mn`

These are in `experimental/` — signaling they're aspirational
rather than maintained. A header comment is enough; rewriting to
current syntax is out of scope.

### Category D — `extern "Python" fn` removed v4.29.0 (2 files)

**Error shape:** `extern "Python" fn was removed in v4.29.0. For
Python interop, compile your Mapanare module normally and generate
a Python binding with 'mapanare bind --lang python <module.mn>'.`

**Root cause:** The removal message is literally the compiler's
error text — it tells users exactly what to do. The examples were
written before v4.29.0 (≈150 versions ago) and never updated.

**Affected examples:**
- `examples/packages/mn_http/main.mn`
- `examples/packages/mn_json/main.mn`

Add a header comment pointing at `mapanare bind`; a proper rewrite
is out of scope.

### Category E — Module-level `let mut` invisible to functions (1 file)

**Error shape:** `error: Undefined variable 'count'` inside
function bodies that read a module-level `pon mut count`.

**Root cause:** SPEC §2.1 documents module-level immutable `let`;
module-level `let mut` is not defined. The parser silently accepts
it, but the semantic checker does not expose the resulting symbol
inside function bodies. Minimally reproduced on a 6-line scratch:

```mn
let mut counter: Int = 0
fn bump() { counter = counter + 1 }
bump(); print(str(counter))
```

Fails with `Undefined variable 'counter'` on line 2 and line 4.

**Not a v4.117.0–v4.128.0 regression.** The example has been broken
since it was written. Either the SPEC should document
`let mut` at module scope (and the semantic checker should be
fixed) OR the example should not rely on it.

**Affected example:**
- `examples/wasm/dom_app.mn`

Opens new docket `Sem.1` for module-level `let mut` scoping. Out of
scope for v4.129.0.

---

## Header comments added

One comment block at the top of each of the 13 failing examples,
pointing at this report. Format:

```mn
// ====================================================================
// Known issue (v4.129.0): this example does not currently compile.
// Cause: <category>. See docs/roadmap/v4/v4.129.0/EXAMPLES_REPORT.md
// for root cause and docket reference.
// ====================================================================
```

The header replaces nothing — it is inserted above any existing
comments.

---

## New dockets opened

| ID | Title | Category | Priority |
|---|---|---|---|
| Gr.1 | Multi-line list/tensor literal grammar support | Grammar | low |
| Gr.2 | Qualified type refs in type position | Grammar | medium (blocks 2 stdlib modules) |
| Sem.1 | Module-level `let mut` scoping | Semantics | low |

All three carry forward to v4.130.0 (pre-panel prep) or later.
Documented here and in v4.130.0 MEASUREMENTS.md when it's written.
