# Mapanare v5.4.3 — "Close Rt.03 — loop-reassignment leaks"

> **Close 22_string_builder's loop-reassignment leak and any others
> in the same class.** v5.4.2 baseline-gated Rt.03 with a deferral
> docket to v5.4.3. This release makes the fix.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.4.2 shipped (leak-check gate + baseline in place)
**Estimated work:** 1 session (~2–3 hours), bounded by sanitizer sweep.

---

## Why this release exists

v5.4.2's leak sweep proved the shadow-slot architecture leaks values
that are reassigned in the same slot at runtime. The structural case:

```mapanare
fn repeat_str(s: String, n: Int) -> String {
    let mut result: String = ""
    for _ in 0..n {
        result = result + s        // str_track.0 slot overwritten per iter
    }
    return result
}
```

At compile time, `emit_track_string` fires once for the concat result
and allocates `str_track.0` in the entry-block prelude. At runtime,
the loop body stores to that slot N times; the prior pointer is lost.
v5.4.1's PLAN.md §D3 premised this was handled automatically by the
shadow-slot architecture — the first corpus-wide sweep (v5.4.2) proved
otherwise. v5.4.2 documented it as **Rt.03** in
`docs/known_issues.md` with a v5.4.3 deferral.

Python's `_track_string` has the identical shape (no free-before-store)
so Python also leaks here. v5.4.3 fixes both emitters.

---

## Scope

### What ships

#### 5.4.3a — Loop-depth tracking in EmitState (self-hosted)

New `EmitState` field:

| Field | Type | Role |
|---|---|---|
| `loop_depth` | `Int` | number of enclosing for/while bodies the current emission is inside |

Incremented at the start of for-body / while-body emission, decremented
at exit. Reset to 0 at `emit_mir_function` entry alongside
`current_ret_type` / owner lists.

Registry bumps: `EmitState` 18 → 19 fields; Reg.1 gate 24 → 25 clean.

#### 5.4.3b — Free-before-store in `emit_track_string` / `_boxed` / `_closure`

When `st.loop_depth > 0`, each tracker prepends a free of the slot's
prior contents before storing the new value. Safe because:

- Slots are zero-initialized in the entry-block prelude; `__mn_str_free`
  / `@free` tolerate null, so the first write in any loop iteration
  no-ops the free.
- Rodata-backed Strings have `is_heap=0`; `__mn_str_free` no-ops them.
  Even if a literal Const somehow ended up in a tracking slot (it
  shouldn't — Phase 3.1 v5.4.1 explicitly doesn't track literals),
  freeing it is a no-op.

Pseudo-IR emitted:

```llvm
; before each loop-iteration tracking store:
%prev.sN = load {ptr, i64}, ptr %str_track.N
call void @__mn_str_free({ptr, i64} %prev.sN)
store {ptr, i64} %val, ptr %str_track.N
```

Outside loops (depth == 0), behavior is unchanged — single store, no
preceding free, matches v5.4.1 / v5.4.2 semantics byte-for-byte.

#### 5.4.3c — Python emitter parity

`mapanare/emit_llvm_text.py::_track_string` / `_track_boxed` /
`_track_closure` gain the same loop-depth guard. Python's existing
loop lowering (for-body / while-body emission paths) needs the
corresponding push/pop of the depth counter.

#### 5.4.3d — Baseline refresh

After fix lands and sweep confirms 22_string_builder CLEAN, update
`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` so the
v5.4.2 check gate's new floor includes the improvement. From that
point forward, a regression back to leaking 22_string_builder fails
CI.

`docs/known_issues.md` Rt.03 row flips from "v5.4.3+" to "**CLOSED
in v5.4.3**" with verification details.

### What does NOT ship

- **Rt.04** (struct-return intermediates, 62_list_output). Separate
  release v5.4.4 — different fix (lowerer Move emission), different
  risk profile.
- **Rt.02** (Mesa/Vulkan loader). Third-party, not Mapanare's to fix.
- **7 LINK_FAIL goldens** (alloca void, br i1 %i64). IR correctness
  bugs, not leaks. Tracked for v5.4.5+.
- **Nested-loop deep analysis.** loop_depth is a flat counter; a
  single layer of free-before-store handles every nesting level
  uniformly. If a specific nested pattern surfaces new UAFs during
  the sanitizer sweep, we widen the fix. Not a design knob we need
  to tune up front.

---

## Exit criteria

1. `bash scripts/run_asan_leak_goldens.sh` → **0 regressions vs
   updated baseline**; 22_string_builder transitions LEAK → CLEAN.
2. Baseline TSV refreshed; `make leak-check` PASS.
3. ASan UAF sweep preserves v5.4.1/v5.4.2 baseline: 55 CLEAN / 11
   CRASH_NO_ASAN. **Any new ASAN_ERROR entry is a HARD FAIL —
   revert.**
4. Valgrind 0 new ERRORS.
5. Goldens 54/66 unchanged.
6. stage2 `llvm-as` OK; stage3 empty (Ve.1 preserved).
7. Non-bootstrap pytest 0 failures.
8. `make lint` clean.
9. Registry gate 25/25 (or whatever the new field count is) clean.
10. `docs/known_issues.md` Rt.03 row CLOSED.

---

## Design decisions

### D1 — Loop-depth, not per-slot tracking

The fix is keyed on WHERE the emit site is, not on which slots are
"hot". Simpler: one `loop_depth` counter vs a per-slot "written
before?" set. Compile-time constant overhead; runtime overhead is
one extra load + call per tracked store inside a loop, no overhead
outside.

### D2 — Free-before-store, not per-iteration slot allocation

Option considered: allocate a ring of N slots, cycle through per
iteration. IR bloat scales with N and requires compile-time loop
bound analysis. Rejected.

Option considered: emit a VLA-like list and push each iteration's
value to it, free all at exit. List manipulation overhead per iter;
also requires a list allocation in the prelude. Rejected.

Free-before-store is O(1) per iteration, no extra allocation, and
leverages the existing zero-init invariant of tracking slots.

### D3 — UAF risk from aliased copies

A Mapanare program that takes a non-tracked copy of a tracked
String and then triggers a reassignment would UAF:

```mapanare
let mut r: String = foo()
let mut t: String = ""       // rodata, not tracked
for _ in 0..n {
    if cond { t = r }         // t aliases r's CURRENT heap memory
    r = r + "x"               // free-before-store frees t's target → UAF on read
}
print(t)                      // UAF if cond fired at least once
```

Mitigation posture: **empirical**. v5.4.3's sanitizer HARD GATE
re-runs the full UAF sweep after every commit. If ANY of the 66
goldens regress into an ASAN_ERROR entry, the fix is reverted and
the release is rescoped. Our baseline is that existing goldens do
NOT exhibit this pattern — if that holds, the fix is safe for the
current corpus.

Acceptable risk because:
- Python has the identical non-fix (Python's `_track_string` also
  lacks free-before-store). Shipping v5.4.3 doesn't *create* this
  UAF pattern — it opens the door to triggering it only if the
  program both reassigns in a loop AND captures an unmanaged alias
  across the reassignment.
- The self-hosted compiler uses Strings as forward-propagating state
  threads, not as captured aliases across mutations. stage2 compiling
  mnc_all.mn is a 38k-line proof that the pattern doesn't appear.

If the sweep reveals a UAF: v5.4.3 ships with Rt.03 STILL open and
documents the pattern. v5.4.4+ can then address with move semantics
or escape analysis.

### D4 — Python parity required

v5.4.3 fixes both emitters because the fix is in the tracking
helper, not IR-specific. Python-emitted code has the same leak
pattern; shipping only the self-hosted fix leaves Python users
regression-exposed and breaks parity.

---

## Risks

### R1 — UAF on aliased reassignment

**Risk: LOW** (per D3 mitigation).

**Mitigation:** Sanitizer HARD GATE after every commit. Rollback
criterion: any regression in UAF sweep count.

### R2 — Loop-depth counter drift

**Risk: MEDIUM.** If the emitter ever forgets to decrement after
increment, all subsequent tracking becomes permanently in-loop.

**Mitigation:** Matched push/pop in exactly two sites
(for-body-entry, for-body-exit; while-body-entry, while-body-exit).
Regression test: emit a program whose function contains tracking
both inside and outside a loop; verify the outside-loop tracking
has no free-before-store line.

### R3 — IR-size increase

**Risk: LOW.** Adds ~3 IR lines per tracked store that happens to
be in a loop. stage2.ll size impact estimated under 5%.

**Mitigation:** Measure at Phase 4. If over 10%, investigate.

---

## Release sequencing

| Outcome of UAF sweep after Phase 2 | Action |
|---|---|
| 0 regressions, 22_string_builder CLEAN | Proceed to baseline refresh + docs |
| 22_string_builder still LEAK (fix didn't work) | Investigate emit site; likely loop_depth isn't being incremented |
| ANY golden transitions CLEAN → ASAN_ERROR | REVERT. Reopen v5.4.3 with a different approach (defer to escape analysis, per-slot write-tracking, etc.) |
| 1+ leak goldens worsen | REVERT. Re-triage. |

---

## What NOT to do

- **Do not suppress or grandfather new ASAN_ERROR findings.** v5.4.3's
  sanitizer gate is HARD — any regression reverts.
- **Do not widen to deep analysis.** Nested-loop cases are handled by
  loop_depth > 0, which covers them uniformly. No per-depth special
  casing needed.
- **Do not touch Rt.04 infrastructure.** v5.4.4 scope. Different
  failure mode, different fix. Bundling increases the chance a UAF
  from one forces a revert of both.
- **Do not skip Python parity.** Test both emitters; ship both fixes
  together.
- **Do not bump v5 tag without explicit user approval.** Saved rule.
