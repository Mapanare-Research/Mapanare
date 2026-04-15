# Mapanare v4.131.0 — Sh.2 investigation + fix (single focus)

> **Single-focus release.** v4.131.0 was originally scoped as THE PANEL
> (v5 gate attempt 3). Pre-panel evidence showed the recovery arc hit a
> quality ceiling at 8.21/10 with Sh.2 unfixed — and Sh.2 is the single
> dominant open finding (36 of ~47 sanitizer findings trace to it per
> v4.130.0 VALGRIND_REPORT + ASAN_REPORT). Panelling now ≠ passing. This
> release lands the Sh.2 fix instead. Panel pushes to v4.135.0 after
> Sh.2, An.1, and Sh.11 close.
>
> The original panel PLAN.md is preserved at PLAN-panel.md for reuse.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.130.0
**Full panel:** No (deferred to v4.135.0)
**Estimated work:** 1 sprint (investigation-heavy)
**Theme:** Close the one bug class that's been deferred four times.

---

## Why the earlier "mirror 6 call sites into self-hosted emit_llvm.mn" framing was wrong

v4.127.0 PLAN said: "mirror v4.101.0's Python-emitter `_move_resource`
adoption into self-hosted `emit_llvm.mn` at six analogous call sites."
v4.128.0, v4.129.0, v4.130.0 all carried this framing forward. It is
not actionable as written:

- `mapanare/self/emit_llvm.mn::EmitState` has **no** `str_slots` or `boxed_slots` fields
- There is **no** `_move_resource` function or equivalent in the self-hosted emitter
- There is **no** per-variable move tracking infrastructure to "mirror" into

The self-hosted emitter emits LLVM IR directly without the Python
emitter's drop-glue + move-tracking architecture. Adding that
infrastructure would be a separate, much larger project.

## Where the Sh.2 fix actually belongs

The crash is in the **Python-compiled `mnc-stage1` binary**, specifically
inside that binary's `emit_mir_call` function. Python `emit_llvm_text.py`
is what compiles `mapanare/self/emit_llvm.mn` into `mnc-stage1`. So the
drop-glue bug is in the **Python emitter's** lowering of the match-arm
pattern present in self-hosted code:

```
let fn_opt: Option<FnEntry> = find_function(s, fn_name)
match fn_opt {
    Some(fe) => {
        if fe.ret_type == "void" { ... }         // OK
        if is_byref_type_st(s, fe.ret_type) {    // CRASH: fe.ret_type.ptr = NULL
            ...
        }
    }
}
```

Per v4.126.0's diagnostic narrowing, the crash is reliable and
triggered by "two calls to the same fn in sequence" (e.g.,
`rec(n-1) + rec(n-2)`) — the first call's drop glue apparently frees
heap that was aliased between `fe.ret_type` and `st.functions[i].ret_type`,
and the second call dereferences stale memory.

## Investigation already completed (during PLAN authoring)

- `_track_string` / `_local_strings` / `_emit_drop_glue_strings` audited
- `_extract_ret_ptrs` recurses into nested structs to collect return-escaping ptrs
- Drop glue compares tracked string ptrs against return-escaping ptrs and skips matching ones
- `_do_enum_payload` extracts struct aggregates via `load` — does **not** call `_track_string` (correct: loaded aliases shouldn't be tracked)
- `_do_idx_get` for LIST loads struct aggregate via `load` — same, no tracking (correct)
- `_do_field_get` extracts String fields via `load {ptr, i64}` — no tracking (correct, it's an alias)

**So what IS freeing `fe.ret_type`'s heap?** That's what the fix phase
needs to pin down via IR inspection on a minimal repro.

## Phase 1 — Minimal repro + IR capture

- [ ] Write `tests/sh2_minimal_repro.mn` — the smallest program that triggers Sh.2 (candidate: `fn f() -> Int { return 1 } fn main() { let a = f(); let b = f(); print(a + b) }`, compiled self-hosted first)
- [ ] Build and run under valgrind: `python3 scripts/build_stage1.py && valgrind ./mapanare/self/mnc-stage1 tests/sh2_minimal_repro.mn`
- [ ] Capture crash frame + confirm it reproduces the v4.126.0 pattern
- [ ] Dump the IR for `find_function` from `mapanare/self/main.ll` post-build (the file compiled from `mnc_all.mn` by Python bootstrap)
- [ ] Identify what drop-glue call at find_function's return is freeing the aliased String heap

## Phase 2 — Fix hypothesis and implementation

Based on Phase 1 findings, the fix is likely one of:

- **(a) Alias-walk from return value**: `_extract_ret_ptrs` already recurses, but may miss `{ptr, i64}` MnString sub-structs treating them as struct aggregates rather than extracting the inner ptr. Fix: teach `_extract_ret_ptrs` to treat `{ptr, i64}` specially and extract the ptr.
- **(b) Suppress drop glue for list-indexed struct variables**: when `f = list[i]` loads a struct aggregate, its String fields alias. Track this and skip drop glue for aliases.
- **(c) Something else**: Phase 1 IR inspection will tell.

Implementation will be one of:

- **Option (a)**: ~10 lines in `_extract_ret_ptrs` to handle `{ptr, i64}` specially
- **Option (b)**: new tracking state + skip logic, ~30-50 lines
- **Option (c)**: TBD — scope will be re-evaluated at Phase 2 start

- [ ] Write the fix in `mapanare/emit_llvm_text.py`
- [ ] Rebuild `mnc-stage1`: `python3 scripts/build_stage1.py`
- [ ] Re-run minimal repro under valgrind: no errors

## Phase 3 — Verification sweep

- [ ] Golden test count: `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1` — target ≥ 47/65 (up from 39/65)
- [ ] Valgrind sweep: `bash scripts/valgrind_all_goldens.sh` — target ≤ 15 ERRORS (down from 31)
- [ ] ASan sweep: `bash scripts/run_asan_goldens.sh` (fresh `mnc-stage1-asan` build) — target ≤ 5 ASAN_ERROR (down from 23)
- [ ] Zero regressions in previously-passing goldens
- [ ] Core pytest subset (excluding bootstrap): 5057+ pass, no new failures
- [ ] Bootstrap pytest: no new failures vs v4.130.0 baseline

## Phase 4 — Closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped to 4.132.0
- [ ] `CHANGELOG.md [4.131.0]` entry
- [ ] `SESSION_REPORT.md` written — honest delta numbers, documented fix mechanism
- [ ] Roadmap status updated (PLAN.md Status→DONE, v4/README.md row, ROADMAP.md row, CLAUDE.md current version)

---

## Exit criteria

| # | Check | Target | Stretch | Downside case |
|---|---|---|---|---|
| 1 | Minimal repro reproduces Sh.2 under valgrind | reproduces | — | no repro → Sh.2 may be environment-dependent, document and continue |
| 2 | Fix identified and implemented | yes | — | bug is structural → ship findings + continue in v4.132.0 |
| 3 | `make test` green | no new failures vs v4.130.0 | — | new failures → fix regressed; do not ship |
| 4 | Native golden count | ≥ 47/65 | ≥ 50/65 | < 45/65 → fix incomplete, scope v4.132.0 accordingly |
| 5 | Valgrind ERRORS | ≤ 15 | ≤ 5 | > 20 → fix touched wrong bug class |
| 6 | ASan findings | ≤ 5 | 0 | > 10 → fix touched wrong bug class |
| 7 | Zero regressions in previously-passing goldens | mandatory | — | any regression → revert + redo |
| 8 | `libmapanare_rt.a` byte-identical to v4.130.0 | yes | — | only IF no C runtime change; document if changed |

Target numbers are goals, not commitments. The fix may land a smaller
win than predicted. If so: ship the real delta, plan v4.132.0 accordingly.
If the investigation reveals the bug is structural and can't be closed
in one release, ship the findings + partial fix + scope v4.132.0+.

---

## What this release does NOT do

- **Panel.** Deferred to v4.135.0 after Sh.2 + An.1 + Sh.11 land.
- **An.1.** 39 deterministic test failures are on the v4.132.0 track.
- **Sh.11.** The `lower_expr` SIGSEGV fixed-point blocker is on the v4.133.0 track.
- **Pack manager, self-hosted async/tensor/closure, DWARF.** All v5.x feature gaps, not blocking a v5 panel pass.
- **Touch the self-hosted `.mn` source.** The fix is purely in Python `emit_llvm_text.py`. No `mapanare/self/*.mn` edits.
- **Touch the C runtime.** Unless Phase 1 reveals a C-side bug, which would change scope significantly.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Phase 1 repro doesn't fire under valgrind | low | high | Fall back to ASan; fall back to the v4.126.0 documented patterns; widen repro set |
| Bug is structural (cross-cutting drop-glue re-design) | medium | high | Ship findings + partial fix; honest scope for v4.132.0+ |
| Fix closes Sh.2 but opens a new bug class | medium | high | Full golden sweep + sanitizer sweep before commit; revert if regression |
| Wrong fix hypothesis, multiple rounds of trial | medium | medium | Budget 2-3 rounds of repro/fix/verify before descoping |
| `libmapanare_rt.a` changes unexpectedly | low | low | No C runtime edits planned; byte-compare at end |
| Fix regresses goldens that currently pass | low | high | Exit criterion 7 is mandatory; revert rather than patch forward |

---

## After v4.131.0

- v4.132.0 — An.1 reduction (39 → ≤ 15 test failures)
- v4.133.0 — Sh.11 investigation + fix (fixed-point blocker)
- v4.134.0 — Pre-panel refresh + MEASUREMENTS.md finalize
- v4.135.0 — THE PANEL, v5 gate attempt 3

If v4.131.0 Phase 1 reveals the bug is broader than one fix can cover,
v4.132.0 continues Sh.2 and the sequence shifts right by one release.
The process is the process. The numbers are the numbers.
