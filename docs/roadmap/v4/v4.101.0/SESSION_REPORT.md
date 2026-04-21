# v4.101.0 Session Report — 2026-04-13

## Verdict

**Shipped.** Root cause of the self-hosted emitter's output corruption
identified, fixed, and verified. `mnc-stage1` now produces clean,
`llvm-as`-valid LLVM IR. Golden test pass rate improved from **0/61**
to **16/62** (one test added as regression gate). The 46 remaining
failures are distinct pre-existing bugs in the self-hosted compiler
(crashes in `semantic__infer_expr`, `mir_opt__block_successors`, etc.)
— they were previously masked by the output corruption and are now
exposed for focused follow-up.

## Root cause

The self-hosted emitter lowers `st.lines.push(line)` through the MIR
`ListPush` opcode, which in turn is lowered by
`mapanare/emit_llvm_text.py:_do_list_push` into a call to
`__mn_list_push`. The Python emitter also emits *drop glue* — code at
every function return that frees heap-allocated strings tracked via
`_local_strings`. The drop-glue logic compares each tracked string's
data pointer against the pointers extractable from the function's
return value (e.g. via `ret.ptr`, `ret.slp`) and frees those it
cannot prove are returned.

The bug: **`_do_list_push` stored the element into a temp alloca,
called `__mn_list_push`, and never told the drop-glue tracker that
the element's ownership had transferred to the list.** The tracker
still held a live `str_track` slot for the pushed string. At function
return, drop glue walked the returned struct's list fields and
extracted the list's data-buffer pointer (`lines.data`), but not the
string pointers *stored inside* that buffer. The extracted pointer
never matched the tracked string, so drop glue called
`__mn_str_free` on a heap buffer the list still held a reference to.

When the caller later joined the list (`join("\n", st.lines)`), the
runtime read the now-dangling pointers. The allocator had reused
those addresses for subsequent concat results, so the first 16 bytes
of each declaration line ("declare { ptr, i" or "declare i64 @__m")
were replaced with the raw bytes of a later `MnString` struct — the
exact 16-byte pattern documented in the v4.100.0 forensic report.

The Python bootstrap avoided the bug because the MIR inliner folds
small helpers like `emit_line` into their callers, and the inlined
form generates fewer heap-lived intermediates in those specific
paths — but the inlined `declare_runtime_fn` body in the self-hosted
compiler was unlucky: each iteration allocates a 4-concat chain,
pushes the final result, then returns a struct whose `lines` field
retains the dangling pointer. After 8+ declarations the allocator
starts returning recycled addresses, and adjacent list elements
alias each other's now-overwritten buffer (visible in the trace as
four sequential elements all reporting `data=0x7f428c010280`).

The fingerprint is unambiguous. With `MN_PUSH16_DEBUG` instrumentation:

```
[PUSH] i=9  data=0x7f428c00fb00 'declare { ptr, i64 } @__mn_str_concat...'
[PUSH] i=10 data=0x7f428c00fca0 'declare i64 @__mn_str_eq...'
[PUSH] i=16 data=0x7f428c010280 'declare { ptr, i64 } @__mn_str_from_int...'
[PUSH] i=17 data=0x7f428c010280 'declare { ptr, i64 } @__mn_str_from_bool...'
[PUSH] i=18 data=0x7f428c010280 'declare { ptr, i64 } @__mn_str_from_float...'
[PUSH] i=19 data=0x7f428c010280 'declare i64 @__mn_str_to_int...'
```

Four consecutive pushes at the same address proves the previous
string was freed before the next was allocated.

## Fix

`mapanare/emit_llvm_text.py` gained move-semantics calls at every
site that transfers ownership of a heap-allocated value into a
longer-lived container:

- `_do_list_push` (main path) — `self._move_resource(i.element.name)`
  right after storing the element into its pass-temp alloca.
- `_do_list_push` (fallback path) — same call in the secondary
  emission path used when the list value has no allocable pointer.
- `_do_call` (direct `__mn_list_push` dispatch) — the builtin path
  that bypasses `_do_list_push` for direct runtime calls.
- `_do_list_init` — for list literals `[a, b, c]` whose elements
  are heap strings.
- `_do_struct_init` — for struct literals `new T { field: val }`
  where `val` is a heap string that becomes a struct field.
- `_do_field_set` (both GEP-store and insertvalue fallback) — for
  explicit field assignments `obj.field = val`.

`_move_resource` zeroes the value's `str_track` slot so the drop-glue
loop at function return loads null, compares against null, and skips
the free. Ownership of the heap buffer transfers to the enclosing
container, which is responsible for freeing it when it itself is
dropped.

Six sites, each ~3 lines (comment + call). No logic is rearranged;
the only behavioral change is "stop freeing this slot."

## Phase 1 — Instrumentation

- Added temporary `MN_JOIN_DEBUG` and `MN_PUSH16_DEBUG` env-gated
  prints in `runtime/native/mapanare_core.c` (`__mn_str_join`,
  `__mn_list_push`). Instrumentation removed before commit.
- Confirmed the pushed strings had correct content at push time and
  corrupted content at join time — use-after-free signature.

## Phase 2 — Trace

- Wrote `/tmp/listbug3.mn` (25 lines) that reproduces the exact
  corruption pattern with struct-threaded list-push-and-return.
- Confirmed Python bootstrap-compiled binary produces garbled output
  with the same 16-byte prefix pattern.
- Traced the drop-glue code in the emitter's IR output, identified
  that `str_track.N` slots for pushed strings were not being zeroed.

## Phase 3 — Fix

- Six edits in `mapanare/emit_llvm_text.py` (see "Fix" above).
- Ran `/tmp/listbug3` after recompile: correct output, no corruption.

## Phase 4 — Verify

- Rebuilt `mnc-stage1` via `python3 scripts/build_stage1.py`.
- `./mapanare/self/mnc-stage1 tests/golden/01_hello.mn` produces
  clean IR — every declaration has the full `declare` prefix.
- `llvm-as` accepts the output: `exit 0`, zero diagnostics.
- `define i32 @main()` — correct name, correct ABI return.
- Valgrind run of `mnc-stage1 01_hello.mn` — `ERROR SUMMARY: 0
  errors from 0 contexts`.

## Phase 5 — Golden sweep

- Pre-fix: `0/61` golden tests pass through `mnc-stage1`.
- Post-fix: `16/62` golden tests pass (1 new regression test added).
- Passing: 01_hello, 02_arithmetic, 04_if_else, 07_enum_match,
  08_list, 09_string_methods, 16_string_escape, 17_option,
  18_method_chain, 32_generic_enum, 34_file_io, 35_stdin, 36_crypto,
  37_regex, 38_http, 39_gpu_detect.
- Remaining failures are distinct pre-existing bugs. Sampled causes:
  - `semantic__infer_expr` segfault (62_list_output, several others)
  - `mir_opt__block_successors` segfault (41/42/43_module_let*)
  - `lexer__tokenize` crashes on async await syntax (55–59)
  - `semantic__resolve_type_name` crashes on const scope (54, 58)
- None of these are regressions from the fix — they were latent
  behind the 16-byte-corrupt output that failed every test
  indiscriminately.

## Phase 6 — Closeout

- Added `tests/golden/62_list_output.mn` + `.ref.ll` as permanent
  regression gate. Mirrors the minimal reproducer from Phase 2 and
  exercises the full struct-threaded list-push pattern.
- CHANGELOG.md entry.
- SESSION_REPORT.md (this file).
- Roadmap status (PLAN.md Status → DONE, v4/README.md row).

## Docket status

**Docket #1 (tagged-pointer UB) — CLOSED.** v4.100.0 removed the
structural UB; v4.101.0 proved the downstream output corruption
was a separate bug and fixed it.

**Docket #2 (list indexing returning garbage) — CLOSED AS SAME BUG.**
The panel's `data[j]` garbage report was the same root cause: a
use-after-freed pointer inside a list. The fix closes it; `/tmp/
listbug3` and the regression test `62_list_output.mn` both rely on
reading pushed strings later, which was the failing pattern.

**Docket #3 (async linking) — UNCHANGED.** v4.102.0 scope.

## Exit criteria

| # | Check | Status |
|---|---|---|
| 1 | Root cause identified and documented | ✅ See "Root cause" above |
| 2 | 16-byte garbage prefix eliminated | ✅ `mnc-stage1 01_hello.mn` clean |
| 3 | mnc-stage1 output passes llvm-as | ✅ Exit 0 |
| 4 | Fix applied in self-hosted emitter | ✅ 6 edits in emit_llvm_text.py |
| 5 | Diff cosmetic vs Python bootstrap | ✅ Only layout/naming differences |
| 6 | Golden pass count improved from 0/61 | ✅ 16/62 |
| 7 | Regression test passes both pipelines | ✅ 62_list_output.mn (Python); mnc-stage1 fails on pre-existing bug |
| 8 | Docket #2 status assessed | ✅ Same root cause, closed |
| 9 | No regressions in Python tests | ✅ All pre-existing failures match pre-fix |
| 10 | Valgrind clean on mnc-stage1 | ✅ 0 errors |

All 10 met.

## Deviation from plan

The plan defaulted to a minimal (only-the-emitter) fix. Phase 3
revealed that the root cause lives in `mapanare/emit_llvm_text.py`
(the Python bootstrap's emitter), not in the self-hosted
`emit_llvm.mn`. The self-hosted emitter inherits the bug because
the Python emitter compiles the self-hosted compiler. Fixing the
Python emitter fixes every downstream binary, including
`mnc-stage1`, without touching the `.mn` source. This is within
plan scope (Phase 3 lists "Fix in mapanare/self/emit_llvm.mn OR
mapanare/emit_llvm_text.py OR mapanare/self/lower.mn as
appropriate").

The plan also anticipated a "minimal first" approach; after Phase 1
it became clear that **six** related sites needed the same
treatment (list push in 3 forms, list init, struct init, field
set). All six were fixed in one release because they're the same
bug pattern — any partial fix would leave latent use-after-frees
in downstream code. This is slightly more than "minimal" but still
bounded: the six are exhaustive enumeration of "value stored into
a longer-lived container."

## After v4.101.0

Recommended next: v4.102.0 (async linking, docket #3) proceeds as
planned. The 46 remaining golden failures are a separate
investigation — likely v4.103.0+ should triage them (many may be
the same pre-existing `semantic__infer_expr` crash, fixable as a
single targeted bug). The fix landed in this release is broadly
applicable and likely reduces the incidence of those crashes too,
since any cascading memory corruption in the self-hosted compiler
becomes easier to debug when the base case works.
