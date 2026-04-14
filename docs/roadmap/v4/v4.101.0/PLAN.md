# Mapanare v4.101.0 — Self-Hosted Emitter Output Corruption

> **Phase A release 2.** v4.100.0 removed the tagged-pointer UB but the
> observable output corruption persists — confirmed pre-existing in the
> pristine v4.99.0 binary. The v4.100.0 session identified a clear
> forensic fingerprint: every declaration line from `mnc-stage1` is
> prefixed with 16 bytes of garbage matching an `MnString` struct
> (`{ data, len }`) being written where the string's data bytes should
> be. This release diagnoses and fixes the actual root cause, which
> likely also explains the list indexing bug (docket #2) since both
> involve incorrect element access in `List<String>`.

**Status:** DONE — 2026-04-13. See SESSION_REPORT.md. Root cause was move-semantics gap in `mapanare/emit_llvm_text.py` (`_do_list_push`, `_do_struct_init`, `_do_field_set`, and related paths). Six sites fixed. Golden tests: 0/61 → 16/62. Regression test `tests/golden/62_list_output.mn` added.
**Breaking:** No
**Prerequisite:** v4.100.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Diagnose and fix the self-hosted emitter output corruption — the 16-byte MnString struct leak in the IR output stream.

---

## Scope

The v4.99.0 panel attributed garbled `mnc-stage1` output to tagged-pointer
UB. v4.100.0 proved this wrong: the corruption exists in the pristine
v4.99.0 binary with zero v4.100.0 changes applied. The real bug is in the
self-hosted emitter's string output path.

**The forensic fingerprint** (from v4.100.0 session):
- Every declaration line has a 16-byte prefix of garbage.
- The first 8 bytes look like user-space pointers (`0x00007f...`).
- The second 8 bytes repeat across blocks.
- This is exactly what you'd see if the 16-byte `MnString` struct
  (`{ const char *data; uint64_t len:63; uint64_t is_heap:1; }`) was
  being memcpy'd into the output buffer instead of dereferencing
  `s.data` and writing the pointed-to bytes.

**Three plausible culprits** (from v4.100.0 session):
1. `List<String>` element access in the self-hosted emitter: elements
   are stored by value (16 bytes each). If the emitter reads the element
   pointer (`&s`) instead of the element's data pointer (`s.data`), the
   struct bytes appear in the output.
2. The `join("\n", st.lines)` call that produces final IR text — the
   `join` implementation may be reading list element storage addresses
   instead of dereferencing string data.
3. `__mn_str_concat` chain in the emission path — the runtime function
   is unit-tested and known-good, so the bug is more likely in the
   emitted IR that calls it.

**This likely subsumes docket #2** (list indexing). The panel reported
`data[j]` returning garbage — which is exactly what happens if list
element access returns the element's stack/heap address (16 bytes)
instead of dereferencing the stored value. Fixing the emitter's string
list access should fix both issues.

## Phase 1 — Instrument and compare

- [ ] Compile a trivial program (`fn main() { print("hello") }`) through BOTH the Python bootstrap and mnc-stage1. Save both IR outputs.
- [ ] Diff the outputs byte-by-byte. Identify exactly where the corruption begins — which function, which line, which string.
- [ ] Instrument `__mn_str_print` with debug output: print the `MnString` struct fields (`data` pointer, `len`, `is_heap`) to stderr before writing. Rebuild mnc-stage1. Run the trivial program. Verify whether the struct fields are sane (valid pointer, reasonable length) or corrupted on arrival.
- [ ] If the struct fields are sane but the output is still garbled, the bug is in `__mn_str_print` itself (unlikely — unit-tested). If the struct fields are garbage, the bug is upstream: the caller is passing the wrong value.

## Phase 2 — Trace the List<String> element access path

- [ ] In the self-hosted emitter (`mapanare/self/emit_llvm.mn`), find where `st.lines` (a `List<String>`) is built up via push/append.
- [ ] Find where `st.lines` elements are accessed — likely in a `join` call or a loop that concatenates lines.
- [ ] Emit the LLVM IR that the self-hosted emitter generates for this path. Look for:
  - GEP into list data array: does it index by `16 * i` (correct for 16-byte MnString elements)?
  - Load from list element: does it load `{ ptr, i64 }` (the MnString struct) or just `ptr` (wrong — that's just the data pointer)?
  - After loading the MnString, does it extract `s.data` via `extractvalue` before passing to `__mn_str_print` / `__mn_str_concat`?
- [ ] Compare this IR against what the Python bootstrap emitter generates for the same `join` / list iteration pattern. The Python IR is known-good — any divergence is the bug.

## Phase 3 — Fix the root cause

- [ ] Based on Phase 2 findings, fix the emitter. Most likely fix:
  - If list element access returns `ptr` (address of element in list storage) instead of loading the `{ ptr, i64 }` struct at that address: add a load instruction after the GEP.
  - If the MnString struct is loaded but `s.data` is not extracted: add `extractvalue { ptr, i64 }, 0` to get the data pointer before passing to print/concat.
  - If `join` implementation in the self-hosted stdlib is wrong: fix the `join` function's IR emission.
- [ ] Fix in `mapanare/self/emit_llvm.mn` (self-hosted emitter)
- [ ] If the same pattern exists in `mapanare/emit_llvm_text.py` (Python emitter), fix there too — though the Python path produces correct output, so it may already be correct
- [ ] If the bug is in `mapanare/self/lower.mn` (MIR lowering for list element access), fix at the MIR level

## Phase 4 — Verify the fix

- [ ] Rebuild mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run `./mapanare/self/mnc-stage1 tests/golden/01_hello.mn` — output should be clean IR, no 16-byte garbage prefix
- [ ] Run `./mapanare/self/mnc-stage1 tests/golden/01_hello.mn | llvm-as -o /dev/null` — the output should be valid LLVM IR
- [ ] Compare mnc-stage1 output vs Python bootstrap output for the same file — diff should show only cosmetic differences (label names, metadata), not structural corruption

## Phase 5 — Golden test sweep

- [ ] Run ALL golden tests through mnc-stage1: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Record pass count. Target: significant improvement from 0/61 (pre-fix).
- [ ] For any remaining failures, document whether they are caused by the same list-access pattern or a different issue.
- [ ] If the list indexing bug (docket #2) is confirmed fixed as a side effect, document that in SESSION_REPORT.md.
- [ ] Add regression test: `tests/golden/62_list_output.mn` — a program that builds a list of strings, joins them, and prints. Must produce correct output through both pipelines.

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.101.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Root cause identified and documented | SESSION_REPORT.md root cause section |
| 2 | 16-byte garbage prefix eliminated from mnc-stage1 output | `mnc-stage1 01_hello.mn` produces clean IR |
| 3 | mnc-stage1 output passes `llvm-as` validation | `llvm-as -o /dev/null` succeeds |
| 4 | Fix applied in self-hosted emitter | diff of `emit_llvm.mn` and/or `lower.mn` |
| 5 | mnc-stage1 vs Python bootstrap output diff is cosmetic only | diff output |
| 6 | Golden test pass count significantly improved from 0/61 | test log with pass count |
| 7 | Regression test `62_list_output.mn` passes both pipelines | test log |
| 8 | Docket #2 (list indexing) status assessed | SESSION_REPORT.md documents whether it's the same bug |
| 9 | No regressions in Python bootstrap tests | `make test` output |
| 10 | Valgrind clean on mnc-stage1 compiling 01_hello.mn | valgrind output |

---

## What this release does NOT do

- **Fix async linking** — that is v4.102.0.
- **Fix else/sino or closure types** — that is v4.103.0.
- **Optimize output** — this fixes correctness. The IR may be verbose but it must be valid.
- **Achieve 61/61 golden** — the target is "significant improvement from 0/61" with root cause identified. Some failures may have unrelated causes.
- **Run a panel** — next panel is v4.106.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Root cause is not in List<String> access but somewhere else entirely | medium | medium | The 16-byte fingerprint strongly suggests MnString struct leak; Phase 1 instrumentation will confirm or rule out |
| Fix breaks the Python bootstrap emitter path | low | high | Python path is known-good; changes to shared code must preserve Python output |
| Multiple independent bugs compound to produce the corruption | medium | medium | Fix one at a time; verify each fix narrows the corruption |
| Self-hosted emitter has architectural issues beyond a point fix | medium | high | If the bug is systemic (wrong calling convention for all struct-returning functions), document the scope and plan a follow-up |
| Valgrind reveals additional memory issues unrelated to this bug | medium | low | Document, don't block. Valgrind issues become v4.105.0 scope (debugging infrastructure). |

---

## After v4.101.0

If the output corruption is fixed, v4.102.0 proceeds with async linking (docket #3). If the corruption persists but is better understood, v4.102.0 may need to continue the investigation before moving to async. The session report will recommend the path based on findings.
