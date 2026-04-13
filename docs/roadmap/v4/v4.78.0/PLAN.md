# Mapanare v4.78.0 — Close Carry-Forward Items 49, 50, A10b

> **Arc 10 release 2.** Three carry-forward items have survived since
> the recovery arc. Item 49 (drop-glue struct return leak) has been open
> for 8 review cycles. Item 50 (agent destroy in-flight message leak)
> has been open for 2 cycles. A10b (const scope in self-hosted semantic)
> has been open for 3 cycles. All three are LOW severity with known
> fixes. This release closes them.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.77.0
**Delta review:** No
**Full panel:** No (v4.81.0)
**Estimated work:** 1 sprint
**Theme:** Drain the three oldest Mapanare-owned carry-forward items.

---

## Scope

The `CARRY_FORWARD.md` ledger after v4.76.0 has 6 open items. One (A5) is Culebra-external. One (A10) is accepted as a grammar gap, not a bug. The remaining four are Mapanare-owned: items 49, 50, A10b, and three pattern-matching items (P2, P3, P6). This release closes the first three; v4.79.0 closes the pattern-matching group.

**Item 49** — The drop-glue emitter at `emit_llvm_text.py:1097-1099` has an early return that skips drop glue for struct returns. This was a deliberate leak-over-UAF tradeoff from the v4.18.0 era. The fix: proper return-value escape analysis so that struct returns that escape the function (via `sret` pointer or return value) are excluded from drop glue without bailing out of the entire function's cleanup.

**Item 50** — `mapanare_agent_destroy` in `runtime/native/mapanare_runtime.c` frees the agent's inbox ring buffer without draining in-flight messages. Any messages posted but not yet consumed leak their payloads. The fix: drain the ring buffer, freeing each message's payload, before freeing the ring itself. ~20 lines.

**A10b** — The self-hosted `semantic.mn` does not thread const symbols into function body scopes. `const X: Int = 42` at module level is invisible inside `fn foo()`. The Python pipeline handles this correctly. The fix: ensure the scope chain in `semantic.mn` includes the module-level const table when resolving symbols inside function bodies.

## Phase 1 — Item 49: Drop-glue escape analysis

- [ ] Read `mapanare/emit_llvm_text.py` around line 1097 — understand the current early-return logic
- [ ] Identify which struct returns actually escape (returned via sret, stored to caller-visible pointer) vs which are local temporaries
- [ ] Replace the blanket early return with targeted exclusion: only skip drop glue for values that provably escape the function
- [ ] Add test: `tests/llvm/test_drop_glue_struct_return.py` — struct with a heap-allocated field returned from a function; verify drop glue runs on the non-escaping copy, not on the escaping return value
- [ ] Run integration pipeline (from v4.77.0) on affected golden tests to verify no UAF introduced
- [ ] Valgrind on golden tests that return structs (at minimum: `tests/golden/03_struct.mn`, `tests/golden/10_result.mn`, `tests/golden/14_option.mn`)

## Phase 2 — Item 50: Agent destroy inbox drain

- [ ] Read `runtime/native/mapanare_runtime.c` — find `mapanare_agent_destroy` or equivalent
- [ ] Before freeing the inbox ring buffer:
  ```c
  // Drain in-flight messages
  while (ring->read_pos != ring->write_pos) {
      MnMessage *msg = &ring->slots[ring->read_pos % ring->capacity];
      if (msg->payload && msg->payload_size > 0) {
          mn_free(msg->payload);
      }
      ring->read_pos++;
  }
  ```
- [ ] Add test: `tests/runtime/test_agent_destroy_drain.c` — post N messages to an agent, destroy the agent without consuming them, verify no leaks (valgrind)
- [ ] Run existing agent golden tests through integration pipeline

## Phase 3 — Item A10b: Const scope threading in self-hosted semantic

- [ ] Read `mapanare/self/semantic.mn` — find the scope resolution logic for function bodies
- [ ] Compare with `mapanare/semantic.py` — identify how the Python pipeline makes module-level consts visible in function bodies
- [ ] Thread the module-level const symbol table into the function body scope chain in `semantic.mn`
- [ ] Add golden test: `tests/golden/58_const_scope.mn`:
  ```mapanare
  const MAX: Int = 100

  fn check(x: Int) -> Bool {
      return x < MAX
  }

  fn main() {
      print(check(50))   // true
      print(check(150))  // false
  }
  ```
- [ ] Rebuild self-hosted compiler: `bash scripts/rebuild.sh`
- [ ] Run golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`

## Phase 4 — Rebuild + verification

- [ ] Full rebuild: `bash scripts/rebuild.sh full`
- [ ] Golden tests: all 58 pass (57 existing + 1 new const_scope)
- [ ] Stage2 validation: `python scripts/ir_doctor.py stage2`
- [ ] Integration tests (v4.77.0 harness): no regressions
- [ ] Valgrind on struct-return goldens + agent goldens

## Phase 5 — Update CARRY_FORWARD.md

- [ ] Mark item 49 as CLOSED with evidence: "v4.78.0 — escape analysis replaces blanket early return; test `test_drop_glue_struct_return.py`; valgrind clean on struct-return goldens"
- [ ] Mark item 50 as CLOSED with evidence: "v4.78.0 — inbox drain loop in `mapanare_agent_destroy`; test `test_agent_destroy_drain.c`; valgrind clean"
- [ ] Mark A10b as CLOSED with evidence: "v4.78.0 — const scope threaded in `semantic.mn`; golden `58_const_scope.mn` passes through both pipelines"

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.78.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Item 49 escape analysis replaces blanket early return | diff of `emit_llvm_text.py` |
| 2 | Item 49 test: struct return drop glue runs correctly | `test_drop_glue_struct_return.py` passes |
| 3 | Item 49 valgrind clean on struct-return goldens | valgrind output |
| 4 | Item 50 inbox drain loop added | diff of `mapanare_runtime.c` |
| 5 | Item 50 test: no leaks on agent destroy with in-flight messages | `test_agent_destroy_drain.c` + valgrind |
| 6 | A10b const scope threaded in `semantic.mn` | diff + golden test |
| 7 | Golden tests: 58/58 pass (57 + new const_scope) | test log |
| 8 | Stage2 validates | `ir_doctor.py stage2` output |
| 9 | CARRY_FORWARD.md updated: 49, 50, A10b marked CLOSED | diff |
| 10 | No regressions in integration tests | v4.77.0 harness output |

---

## What this release does NOT do

- **Close P2, P3, P6** — those are v4.79.0.
- **Close A5** — that is Culebra-external, not Mapanare's to fix.
- **Close A10** — accepted grammar gap (bounded-for sentinels), not a bug.
- **New features** — this is pure debt drain.
- **Optimizer work** — no changes to `mir_opt.py` or `optimizer.py`.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Item 49 escape analysis is too conservative (still leaks some cases) | medium | medium | Start with the common case (sret returns); track edge cases as future work |
| Item 49 escape analysis is too aggressive (introduces UAF) | low | high | Valgrind on every struct-return golden; integration pipeline catches runtime crashes |
| Item 50 drain loop accesses freed memory if ring was corrupted | low | high | Bounds-check read_pos against capacity; valgrind |
| A10b scope change breaks existing self-hosted semantic behavior | medium | medium | Run full golden suite after the change; compare Python vs self-hosted output |
| New golden test (58_const_scope) fails through integration pipeline | low | low | xfail in integration if needed; the semantic fix is still valuable |

---

## After v4.78.0

v4.79.0 closes the pattern-matching carry-forward group: P2 (zero unit tests for `pattern_matching.py`), P3 (self-hosted guard fall-through divergence), P6 (unreachable-arm warning zero test coverage). After v4.79.0, the carry-forward ledger should show 0 Mapanare-owned open items.
