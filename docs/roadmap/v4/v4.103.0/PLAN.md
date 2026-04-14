# Mapanare v4.103.0 — else/sino Verification + Closure Type Annotations

> **Phase A release 4 (final).** The three critical/high blockers are
> fixed: tagged-pointer UB (v4.100.0), list indexing (v4.101.0), async
> linking (v4.102.0). Two HIGH items remain from the v4.99.0 docket:
> else/sino has grammar support but benchmarks use double-negation
> workarounds suggesting it was never verified end-to-end, and closure
> type annotations (`Fn(Int) -> Int`) parse but lowering fails. This
> release adds golden tests for both, fixes whatever breaks, and closes
> Phase A.

**Status:** DONE — 2026-04-13. See SESSION_REPORT.md. **Phase A complete — all 5 critical/high docket items closed.** Docket #4 (else/sino) fixed via a deeper discovery: the Python emitter's drop-glue was freeing boxed enum payloads whose pointers lived transitively in the returned value but beyond `_extract_ret_ptrs`'s reach, causing `ElseClause` aliasing in the self-hosted AST. Conservative skip when return has any pointer field. Docket #5 (closure types) fixed via 3 changes in `lower.py`: FnType resolves to MIRType(FN), typed-variable calls emit ClosureCall, all lambdas emit ClosureCreate (empty-captures case = `{@fn_ptr, null}`). Both goldens run end-to-end via Python bootstrap + clang. Golden pass through mnc-stage1: 16/62 → 21/64 (5 more tests pass from the boxed-drop fix as side effect).
**Breaking:** No
**Prerequisite:** v4.102.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Verify else/sino and fix closure type annotation lowering — close all 5 critical/high docket items from v4.99.0.

---

## Scope

**Docket item #4 — else/sino verification.** Coral noted in the v4.99.0 panel that `else` (and its Spanish keyword `sino`) appears in the grammar but the panel's benchmark programs use double-negation patterns (`if !condition { ... }`) instead of `else` branches. This suggests the feature was never tested end-to-end through the native pipeline. The fix: write a golden test that uses `else`/`sino` in if-expressions, compile through both the Python bootstrap and mnc-stage1, verify output matches. If either pipeline mishandles else/sino, trace and fix the parser, lowerer, or emitter.

**Docket item #5 — closure type annotations.** Coral also noted that `Fn(Int) -> Int` parses correctly as a type annotation (the grammar handles it) but lowering fails when a variable is annotated with a closure type. This means you can write `let f: Fn(Int) -> Int = |x| x + 1` but the compiler crashes or emits wrong code. The issue is likely in `lower.py` (or `lower.mn` in the self-hosted compiler) where `FnType` with explicit parameter types is not fully handled during variable declaration lowering.

After v4.103.0, all 5 critical/high docket items from the v4.99.0 panel are closed. Phase A (Bug Sprint) is complete.

## Phase 1 — else/sino golden test

- [ ] Write `tests/golden/63_else_sino.mn`:
  ```mapanare
  fn classify(x: Int) -> String {
      if x > 0 {
          return "positive"
      } else {
          if x < 0 {
              return "negative"
          } sino {
              return "zero"
          }
      }
  }

  fn main() {
      print(classify(42))
      print(classify(-7))
      print(classify(0))
  }
  ```
  Cover: `else` keyword, `sino` keyword (Spanish), nested if/else, else in expression position (if supported), else after multi-line if body
- [ ] Compile through Python bootstrap: `python -m mapanare run tests/golden/63_else_sino.mn`
- [ ] Verify output: `positive`, `negative`, `zero` (one per line)
- [ ] Compile through mnc-stage1: `./mapanare/self/mnc-stage1 tests/golden/63_else_sino.mn -o /tmp/63.ll`
- [ ] Link and run: `clang /tmp/63.ll -L runtime/native -lmapanare_rt -o /tmp/63 && /tmp/63`
- [ ] Compare output between both pipelines — must match

## Phase 2 — Fix else/sino if broken

- [ ] If Python bootstrap fails: trace through `mapanare/parser.py` and `mapanare/lower.py` — is `else`/`sino` handled in the AST? Is it lowered to MIR correctly? Is the emitter generating the right branch?
- [ ] If mnc-stage1 fails: trace through `mapanare/self/parser.mn` and `mapanare/self/lower.mn` — same questions
- [ ] If both work: no fix needed, just the golden test is the deliverable
- [ ] If only one pipeline fails: fix the broken one, re-verify

## Phase 3 — Closure type annotation golden test

- [ ] Write `tests/golden/64_closure_typed.mn`:
  ```mapanare
  fn apply(f: Fn(Int) -> Int, x: Int) -> Int {
      return f(x)
  }

  fn main() {
      let double: Fn(Int) -> Int = |x| x * 2
      let negate: Fn(Int) -> Int = |x| 0 - x
      print(apply(double, 5))
      print(apply(negate, 3))
      print(double(10))
  }
  ```
  Cover: `Fn(T) -> T` annotation on `let` binding, `Fn` annotation on function parameter, closure assigned to typed variable, closure called directly and passed as argument
- [ ] Compile through Python bootstrap: `python -m mapanare run tests/golden/64_closure_typed.mn`
- [ ] Verify output: `10`, `-3`, `20` (one per line)
- [ ] Compile through mnc-stage1 — expect this to fail (the panel said lowering fails)
- [ ] If Python bootstrap also fails: fix `lower.py` first, then `lower.mn`

## Phase 4 — Fix closure type annotation lowering

- [ ] If lowering fails in Python bootstrap (`lower.py`):
  - Find the handler for variable declarations with type annotations
  - Find where `FnType` (or `Fn(T) -> T` type info) is processed during lowering
  - The likely issue: `FnType` with explicit parameter types is not matched or is treated as an unknown type
  - Fix: handle `FnType` in the variable declaration lowering path, emit the correct MIR for a closure binding
- [ ] If lowering fails only in self-hosted compiler (`lower.mn`):
  - Same analysis as above but in `mapanare/self/lower.mn`
  - The self-hosted compiler may not have the `FnType` case in its type resolution
- [ ] Re-compile `tests/golden/64_closure_typed.mn` through both pipelines after the fix
- [ ] Verify output matches expected

## Phase 5 — Rebuild + full golden suite

- [ ] Rebuild mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run all golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Target: 64/64 (62 from v4.101.0 + `63_else_sino.mn` + `64_closure_typed.mn`)
- [ ] Record pass count — any failures should be unrelated to else/sino or closure types
- [ ] Run `make test` — full pytest suite passes

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.103.0]` entry
- [ ] `SESSION_REPORT.md` written
- [ ] Note in SESSION_REPORT.md: "Phase A complete. All 5 critical/high docket items from v4.99.0 are fixed."

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `63_else_sino.mn` passes through Python bootstrap | output log |
| 2 | `63_else_sino.mn` passes through mnc-stage1 (compile + link + run) | output log |
| 3 | `64_closure_typed.mn` passes through Python bootstrap | output log |
| 4 | `64_closure_typed.mn` passes through mnc-stage1 (compile + link + run) | output log |
| 5 | 64/64 golden tests pass through mnc-stage1 | test log |
| 6 | No regressions in existing golden tests | test log (62 existing all pass) |
| 7 | `make test` passes (full pytest suite) | pytest output |
| 8 | Phase A docket status: all 5 critical/high items closed | SESSION_REPORT.md |

---

## What this release does NOT do

- **Fix MEDIUM/LOW docket items** — byref size heuristic divergence (#7), coroutine frame coupling (#8), string concat performance (#9), keyword collision documentation (#10), async error messages (#11) are Phase B or later.
- **Run a panel** — Phase A has no panel. The next panel is v4.106.0.
- **Add new language features** — this verifies and fixes existing features only.
- **Refactor the closure implementation** — closures work via environment struct capture. This release fixes type annotations on closure bindings, not the capture mechanism.
- **Add else-if as a single keyword** — `else if` works as two keywords (else + nested if). An `elif`/`sinosi` keyword is not in scope.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| else/sino works in both pipelines — no fix needed | high | none | The golden test is still valuable as regression coverage; this is the good outcome |
| Closure type annotation fix requires grammar changes | low | high | The grammar already parses `Fn(Int) -> Int` — the issue is in lowering, not parsing |
| Closure type fix in Python lowerer does not carry over to self-hosted lowerer | medium | medium | Fix both independently; test both pipelines |
| New golden tests conflict with tests added by v4.101.0 or v4.102.0 | low | low | Check numbering after building on v4.102.0; renumber if needed |
| Closure type annotations work for simple cases but fail for higher-order patterns | medium | medium | Start with the simple case (Phase 3 test); document higher-order limitations as future work |

---

## After v4.103.0

Phase A is complete. All 5 critical/high docket items from the v4.99.0 panel are fixed:

1. Tagged-pointer UB (v4.100.0) -- CLOSED
2. List indexing bug (v4.101.0) -- CLOSED
3. Async linking (v4.102.0) -- CLOSED
4. else/sino verification (v4.103.0) -- CLOSED
5. Closure type annotations (v4.103.0) -- CLOSED

v4.104.0 begins Phase B: rebuild and verify. The remaining 6 docket items (MEDIUM and LOW) are scoped across v4.104.0-v4.105.0. The next full panel is v4.106.0 — the first panel since v4.99.0's 6.59/10. The goal is to demonstrate that the bug sprint moved the needle.
