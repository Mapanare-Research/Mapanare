# v5.6.6 — Rt.04 attempt + RESCOPE — single-level walk insufficient

**Status:** SHIPPED (Rt.04 stays open; documents why)
**Breaking:** No
**Date:** 2026-04-24

> **Note on git ordering:** v5.6.6 was originally planned to ship
> between v5.6.5 and v5.6.7. The v5.6.5 → v5.6.7 jump skipped it
> when the user prioritised the Ve.2 lowerer fix; v5.6.6 lands
> here, after v5.6.7 in git history but holds its planned slot in
> the version sequence.

## Headline

**Rt.04 cannot be closed by a one-level struct-field walk.** The
walk's struct-of-list-of-string blind spot causes a confirmed
heap-use-after-free in 62_list_output: drop glue extracts the
returned struct's `List<String>` field as an alias, but the
individual Strings *inside* that list are tracked separately and
freed prematurely. Symmetric for any nested resource. Closing
Rt.04 requires either a multi-level walk (PLAN explicitly
deferred to v5.7.x / v6.0) or a borrow checker that tracks
ownership through container types.

**What this release contributes:** the `ret_ty_is_aggregate`
signature is extended to take `st: EmitState`, plumbing the
state-aware gate path so future re-lift attempts can size-gate
without another invasive refactor. The actual gate is reverted to
the v5.4.4 conservative-skip behaviour after empirical UAF
verification.

## Why a one-level walk is unsafe — the empirical proof

`62_list_output.mn` defines:

```mn
struct St { lines: List<String>, n: Int }

fn emit_line(st: St, line: String) -> St {
    let mut s: St = st
    s.lines.push(line)
    return s
}
```

The function returns `St` by value. Tracked String slots inside
`emit_line` (e.g., from internal `__mn_str_concat` intermediates)
have data pointers that point to the **String headers inside the
list buffer** — the same underlying `char *` data the caller
will read after return.

The v5.6.6 single-level walk extracts `St`'s direct fields:

| Field | Type | Walk action |
|---|---|---|
| `lines` | `{ptr, i64, i64, i64, i64}` (List) | Extract list ptr → `ret_list_ptrs` |
| `n` | `i64` | Skip (not a resource) |

The walk does **NOT** descend into `lines`'s element list and
extract the individual Strings. So `ret_str_ptrs` stays empty.

Then `emit_drop_glue_strings` runs: each tracked String slot's
data pointer is alias-checked against `ret_str_ptrs` (empty) →
no match → `__mn_str_free` fires → strings underlying the
returned list are freed.

After return, `main`'s `__mn_str_join` reads freed memory.
Confirmed by ASan with `-fsanitize=address`:

```
==59144==ERROR: AddressSanitizer: heap-use-after-free
READ of size 18 at 0x503000000070 thread T0
    #0 memcpy
    #1 __mn_str_join
    #2 main

freed by thread T0 here:
    #0 free
    #1 __mn_str_free          ← the premature free
    #2 emit_drop_glue_strings  ← walk decided "no alias" wrongly
```

The fix isn't tightening the gate (already tried N=8 → 4, M=50 →
10; same failure). The fix is multi-level alias extraction:
walking `lines`'s elements and pushing each String's data ptr
into `ret_str_ptrs`. That's outside this release's scope per the
PLAN's stated boundary.

## What was attempted and reverted

### Attempt 1 — N=8 fields, M=50 slots

Per PLAN.md §9.6b. Result: stage2.ll grew **+10.3%** (207,616 →
229,022). Far over PLAN exit criterion #4's **3% budget**. The
gate fired for too many small structs in too many call sites,
each emitting a chain of `extractvalue` lines.

### Attempt 2 — N=4 fields, M=20 slots

Per PLAN.md §9.6b's tighten-on-overshoot guidance. Result:
stage2.ll grew +3.67% — still over budget.

### Attempt 3 — N=4 fields, M=10 slots

stage2.ll grew +2.39% (under budget). ASan reproduced the
heap-use-after-free in 62_list_output:

```
__mn_str_free(<freed>) called from emit_drop_glue_strings
… caller's __mn_str_join reads freed buffer
```

The leak fix (closing 9 objs / 141 B) and the UAF (reading freed
String data) are mutually exclusive at this walk depth. The PLAN
expected the leak to close cleanly because `St` has 2 fields ≤
gate threshold. It missed that the leak's resource lives at depth
2 (struct → list → string), not depth 1.

## What ships

### Signature change preserved

```mn
fn ret_ty_is_aggregate(st: EmitState, ret_ty: String) -> Bool
```

The call site at `emit_drop_glue:4716` passes `st`. Body returns
the same conservative-skip values as v5.4.4 / v5.6.5 for now,
but the future borrow-checker / multi-level walk implementation
can replace the body without re-threading state through callers.

### Documentation

`mapanare/self/emit_llvm.mn:4689-4720` — the new comment block
documents the empirical UAF, lists what was tried, and explains
why a single-level walk is insufficient for struct-of-list-of-X
shapes. Future contributors won't re-attempt this fix without
hitting the same wall.

`docs/roadmap/v5/v5.6.6/SESSION_REPORT.md` — this report.
`docs/known_issues.md` — Rt.04 row updated to clarify the
multi-level scope.

## What does NOT ship

- **62_list_output leak fix.** Stays at 9 objs / 141 B.
  Baseline-gated; not a regression.
- **Multi-level struct walk.** Required for Rt.04 closure but
  scoped to v6.0 borrow checker era per PLAN §"What does NOT
  ship".
- **stage2.ll growth.** Effectively 0% (+3 lines from comments
  reformatted alongside the signature change).

## Metrics

| Gate | v5.6.7 | v5.6.6 | Δ |
|---|---:|---:|---:|
| stage2.ll lines | 207,616 | 207,619 | +0.00% |
| stage2.ll `llvm-as` | OK | OK | — |
| `ret_ty_is_aggregate` signature | `(ret_ty)` | `(st, ret_ty)` | + plumbing |
| 62_list_output LSan | 9 obj / 141 B (LEAK, baseline) | 9 obj / 141 B | unchanged |
| goldens harness | 64/66 | 64/66 | — |
| `make lint` | clean | clean | — |
| `check_struct_registry.py` | 23/23/91 | 23/23/91 | — |
| ASan on `mnc_all.mn`: heap-buffer-overflow | 0 | 0 | — |

## Risks — none materialized

- **R1 — Walk re-introduces UAF.** Empirically verified at all
  three attempted thresholds; reverted before commit.
- **R2 — Signature change breaks callers.** Only one caller
  exists (`emit_drop_glue`); updated atomically. Goldens preserve.
- **R3 — Doc-only release loses momentum.** Honest scoping is
  more valuable than optimistic patches per "no cheap shit"
  directive — a UAF would be much worse than a documented leak.

## What's next

- **v5.6.8** — **Ve.3 close — stage2 runtime OOM.** Continues
  the v5.6.5/v5.6.7 thread to reach non-empty stage3.ll.
  Independent of Rt.04.
- **v5.6.9+** — **Ve.2 residual closure.** Threads list-elem-ty
  hints from struct-field defaults, call-arg positions, return
  expressions. Reduces 18 × 384-byte floor sites toward 0.
- **v6.0** — **Borrow checker.** Replaces the current explicit
  drop-glue tracking with proper ownership analysis. Closes
  Rt.04 alongside any other multi-level alias scenarios in one
  pass. The current Mapanare-side leak (62_list_output) survives
  until then.

## Lesson

The v5.4.4 → v5.6.6 history shows the cost of single-level alias
analysis on a language with non-refcounted leaf strings. Two
sessions of attempted closures, two confirmed unsafe outcomes
(v5.4.4: stage2 explosion; v5.6.6: UAF). The structural answer is
**ownership at the type level, not the slot level** — which is
exactly what borrow checking provides. The interim release notes
this clearly so the next attempt doesn't repeat the cycle.
