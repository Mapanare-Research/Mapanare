# Mapanare v4.122.0 — Fix Qs.1: List<Int> Indexing in Argument Position

> **Post-panel closeout release 2.** The highest-impact correctness bug
> remaining. `arr[0]` on a `List<Int>` returns wrong values on the
> native pipeline: `"<?>"` when passed as an argument to `str()`,
> a raw pointer value when bound via `let v = arr[0]`. The Python
> bootstrap produces the correct result (42). V5_READINESS called this
> "would embarrass a v5 label." This release finds the root cause,
> fixes it, and adds a regression test.

**Status:** DONE (2026-04-14)
**Breaking:** No
**Prerequisite:** v4.121.0
**Delta review:** No
**Full panel:** No (v4.130.0)
**Estimated work:** 1 sprint
**Theme:** Fix the flagship List<Int> indexing bug. Native pipeline must match Python bootstrap.
**Outcome:** Shipped. Single-line behavioural fix in `mapanare/lower.py::_lower_let` — after patching `ListInit.elem_type` for empty lists with annotations, also rebind `val` to carry the declared type so downstream `IndexGet` / `ListPush` / `len` see correct element type args. Native pipeline now matches Python bootstrap for all five test patterns. Self-hosted compiler verified not to need a mirror fix. New golden `65_list_int_indexing.mn` + 5 IR-level regression tests pin the invariant. See `SESSION_REPORT.md` for details.

---

## Scope

The bug manifests in two ways:

```mapanare
let arr: List<Int> = []
arr.push(42)
print(str(arr[0]))     // native prints "<?>"   -- expected: "42"
let v: Int = arr[0]
print(str(v))           // native prints "94535861117616" -- expected: "42"
```

The Python bootstrap handles both correctly. The native pipeline (LLVM emitter) does not. The root cause is in how `List<Int>` element access is lowered to LLVM IR — either the GEP indices are wrong for the list's data array, or the load instruction returns a pointer-to-Int instead of an Int value.

Two code paths need investigation:
1. `mapanare/emit_llvm_text.py` — Python bootstrap LLVM emitter
2. `mapanare/self/emit_llvm.mn` — self-hosted emitter (same pattern may exist)

The fix must produce correct values for `arr[0]` in all positions: direct argument, let binding, loop index, comparison, arithmetic.

## Phase 1 — Reproduce with minimal .mn file

- [ ] Create `tests/golden/65_list_int_indexing.mn`:
  ```mapanare
  fn main() {
      let arr: List<Int> = []
      arr.push(42)
      arr.push(99)
      arr.push(7)

      // Direct argument
      print(str(arr[0]))    // expect: 42

      // Let binding
      let v: Int = arr[0]
      print(str(v))          // expect: 42

      // Second element
      print(str(arr[1]))    // expect: 99

      // After mutation
      arr.push(100)
      print(str(arr[3]))    // expect: 100

      // In arithmetic
      let sum: Int = arr[0] + arr[1]
      print(str(sum))        // expect: 141
  }
  ```
- [ ] Compile through Python bootstrap — verify all outputs are correct
- [ ] Compile through mnc-stage1 — verify the bug reproduces (wrong values)
- [ ] Save both IR outputs for comparison: `bootstrap_65.ll` and `stage1_65.ll`

## Phase 2 — Compare IR to identify the GEP/load divergence

- [ ] Extract the IR for `arr[0]` in argument position from both outputs
- [ ] Extract the IR for `let v = arr[0]` from both outputs
- [ ] Compare GEP instructions: are the indices different?
- [ ] Compare load instructions: is one loading a pointer where it should load a value?
- [ ] Identify the specific emit function in `emit_llvm_text.py` that generates the wrong IR
- [ ] Document the root cause: which line(s) in the emitter produce the wrong GEP/load

## Phase 3 — Fix in emit_llvm_text.py

- [ ] Fix the list element access emission for `List<Int>` (and `List<Float>`, `List<Bool>` — any primitive list)
- [ ] The fix must handle:
  - `arr[i]` as a direct argument to a function call
  - `arr[i]` in a let binding
  - `arr[i]` in an arithmetic expression
  - `arr[i]` in a comparison
  - `arr[i]` in a return statement
- [ ] Verify the fix does not break `List<String>` or `List<MyStruct>` indexing (reference types)
- [ ] Re-compile the golden test through the Python bootstrap — verify correct output

## Phase 4 — Fix in self-hosted emitter

- [ ] Read `mapanare/self/emit_llvm.mn` — find the list element access emission
- [ ] Determine if the same bug exists in the self-hosted emitter
- [ ] If yes, apply the equivalent fix
- [ ] If no (the self-hosted emitter has a different code path), document why

## Phase 5 — Regression test

- [ ] Finalize `tests/golden/65_list_int_indexing.mn` with all patterns from Phase 1
- [ ] Add the reference IR: `tests/golden/65_list_int_indexing.ref.ll`
- [ ] Add a pytest regression test in `tests/llvm/` that specifically verifies:
  - `List<Int>` element access produces an `i64` (not a pointer)
  - The GEP indices are correct for the list data array
- [ ] Run the test through both pipelines

## Phase 6 — Rebuild + golden sweep

- [ ] Rebuild mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run all golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record the pass count — the new golden should pass, no existing goldens should regress
- [ ] `make test` — green
- [ ] `make lint` — clean

## Phase 7 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.122.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Bug reproduced with minimal .mn file | IR diff between bootstrap and stage1 |
| 2 | Root cause documented (specific line in emitter) | SESSION_REPORT |
| 3 | Fix in `emit_llvm_text.py` | diff |
| 4 | Fix in `emit_llvm.mn` (if applicable) | diff or documented as not-applicable |
| 5 | Regression test: `65_list_int_indexing.mn` passes through both pipelines | golden test output |
| 6 | `List<String>` and `List<MyStruct>` indexing still works (no regression) | golden tests 03, 04, etc. |
| 7 | Golden pass count maintained or improved | test log |
| 8 | `make test` green | test log |
| 9 | V5_READINESS item Qs.1 resolved | V5_READINESS.md update or SESSION_REPORT note |

---

## What this release does NOT do

- **Fix enum boxing (Rt.1)** — that is v4.124.0.
- **Delete optimizer.py** — that is v4.123.0.
- **Fix List<T> for all T** — focuses on `List<Int>` and primitive types. Complex generic list interactions are v5.x.
- **Touch the parser or semantic checker** — this is an emitter bug, not a type system bug.
- **Run a panel** — the next panel is v4.130.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Fix for `List<Int>` breaks `List<String>` indexing | medium | high | Phase 3 explicitly tests reference types after the fix |
| Root cause is in `lower.py` not `emit_llvm_text.py` | medium | medium | Phase 2 comparison will reveal where the divergence occurs; fix follows the root cause |
| Self-hosted emitter has a different (harder) variant of the bug | low | medium | Phase 4 investigates independently; if the fix is complex, defer to v4.125.0+ |
| The raw pointer value (94535861117616) indicates a deeper ABI issue | low | high | If the GEP fix doesn't resolve it, escalate to a struct-layout investigation |
| New golden test (65) fails through integration pipeline | low | low | Expected; integration pipeline may need the same fix |

---

## After v4.122.0

v4.123.0 is the dead-code sweep: delete `optimizer.py` (1,203 lines, 9% test coverage) and remove the TBAA metadata declaration that v4.109.0 forensics confirmed is 100% dead. Pure cleanup — no behavior change, net negative lines.
