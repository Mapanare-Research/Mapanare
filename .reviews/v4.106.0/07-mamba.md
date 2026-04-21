# Mamba v4.106.0 Review — C runtime

## Score: 8.0/10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

Last panel I gave 6.1 CONDITIONAL PASS and estimated the tagged-pointer
rewrite at 3–4 hours, with the explicit claim that the 16-byte ABI
could be preserved with a C bitfield. v4.100.0 landed exactly that,
at exactly that scope. I'm graded on whether the claimed C-runtime
fixes actually work — not on every C bug the new sanitizer gates
subsequently surfaced.

## Item #1 — Tagged-pointer UB → `is_heap` bitfield

CLEAN. `grep -n "mn_tag_heap\|mn_untag_heap\|mn_is_heap" runtime/native/`
returns 3 hits, all comment text describing the removed scheme
(`mapanare_core.c:166-168`, `mapanare_core.h:36`). No live references.
`mapanare_core.h:57-61` is the new struct: `{ const char *data; uint64_t
len:63, is_heap:1; }` — 16 bytes, same `{ptr, i64}` at LLVM-ABI level.
The `mn_untag(ptr)` macro is retained as a no-op for mechanical
diff — defensible. My v4.99.0 3–4h estimate proved accurate.

## Item #3 — `libmapanare_rt.a` scheduler exports

CLEAN. `nm libmapanare_rt.a | grep -c "T __mn_coro_"` → **6**, all
required: `__mn_coro_register_wait`, `__mn_coro_scheduler_{init,
register,run,destroy}`, `__mn_coro_spawn`. The three async goldens
(55/56/57) run natively → 42, 43, 110. TSan run is race-free. Docket
items #3 and #6 close cleanly.

## New C-runtime bug: `__mn_list_free` heap-UAF (Vg.2 / As.1 / As.3)

Phase A did not claim to fix this. Phase B's ASan run exposed it.
**The bug is real** and the diagnosis in `ASAN_REPORT.md:49-77` is correct:

`mapanare_core.c:1190-1204` decrements the refcount correctly but the
guard `list->data && list->managed` (line 1191) only checks the **local**
`MnList`. A sibling `MnList` created via a plain bitwise struct copy
(no refcount inc) still carries the same `data`/`managed` fields after
the first `__mn_list_free`. Second free reads `header[0]` at
`mn_list_rc:975-976` — that's the freed memory. 12 goldens hit this.

The `mn_list_grow` path (line 1053) already cites this exact aliasing
concern — "Struct copies may share the same data pointer (bitwise copy
without refcount)" — but the fix was only applied there, not on
`__mn_list_free`. The UAF lives in the gap.

**Fix sketch.** Two correct options:

1. **Always refcount on copy.** Route all `MnList` struct copies through
   `__mn_list_retain(MnList)` that bumps rc. Requires emitter support.
   ~1 day, cross-cutting.
2. **Generation counter in the header.** `[magic | rc | gen]`
   (24 B header instead of 16). On alloc, `header[2]++`. Store `gen`
   in the `MnList` at hand-off. `mn_list_rc` verifies `list->gen ==
   header[2]` before trusting `header`. Simple, local, no emitter changes.
   **Estimate: 3–4h, ~40 LOC.** Same energy as the tagged-pointer fix.

Option 2 is what I'd ship in v4.107.0. Closes Vg.2 + As.1 + As.3 together.

## Agent inbox / arena lifetime (item 50 lineage)

Still correct. `mapanare_runtime.c:692-710` drains inbox + outbox with
`message_dtor` before `ring_destroy`. Default dtor is `free` (line 614,
v4.78.0 CARRY_FORWARD #50). Producer lock destroyed after drain.
`mn_agent_arena_destroy` lives at `mapanare_core.c:2428` — separate
lifecycle, no accidental coupling. Good.

## AS-safe crash handler (`mapanare_runtime.c:1810-1928`)

CLEAN. Only `write(2)`, hand-rolled `mn_as_write_{uint,int,cstr,sig_name}`,
`backtrace_symbols_fd` (signal-safety(7) lists as AS-safe). No malloc,
no stdio, no locks. `SA_RESETHAND` prevents recursive handler invocation.
The backtrace-lazy-ld.so-load caveat is honest in the comment. Breadcrumb
uses `__thread` (not pthread TSD — good, TSD mutates lock state).
Replaces the unsafe `fprintf`+`backtrace()` handler from pre-v4.105.0.
Exactly the right shape.

## Findings

- Tagged-pointer removal clean. Scheduler exports clean. Crash handler clean.
- `__mn_list_free` UAF is a pre-existing bug newly **surfaced** by ASan,
  not a regression. Correctly documented in new docket (Vg.2 / As.1).
- 4-byte `managed`/padding footprint in `MnList` unchanged — no new
  ABI surface.

## Docket items I'd open

- **M-Ca.1** (HIGH): Ship the generation counter in `mn_list_alloc_buf`
  header; fold Vg.2 + As.1 + As.3 into a single v4.107.0 fix (~3-4h).
- **M-Ca.2** (MEDIUM): Audit every `MnList` bitwise-copy site in the
  Python/self-hosted emitters and document explicit ownership semantics
  (retain vs. move).
- **M-Ca.3** (LOW): `mn_untag()` no-op macro can be deleted next release
  once IR emitters confirm they never reference it.

## Grade justification

From 6.1 CONDITIONAL PASS to **8.0 PASS WITH NOTES**. The two C-runtime
items I flagged in v4.99.0 (tagged-pointer UB, scheduler exports) are
both cleanly fixed with the scope and timeline I estimated. Bitfield
preserves ABI, zero remnants. The list-free heap-UAF is a separate,
newly-visible bug that Phase A never claimed to address — it belongs
to v4.107.0, and the docket now correctly tracks it. Not -2 for a bug
Phase A didn't promise to fix; -2 because a shared-buffer aliasing
hazard was already known in `mn_list_grow` and should have been
generalized at that time.

## One-line summary

Tagged-pointer bitfield landed clean at my 3–4h estimate; scheduler
exports verified; inbox drain and AS-safe crash handler are correct;
the newly-visible `__mn_list_free` shared-buffer UAF is a real C-runtime
bug, properly docketed, ~3-4h fix with a generation counter.
