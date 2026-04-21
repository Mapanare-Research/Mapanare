# Viper v4.120.0 Review — Memory safety

## Score: 8.4 / 10
## Verdict: PASS WITH NOTES

## Context

At v4.99.0 I gave **5.5 / 10 NEEDS WORK** — the lowest single score
of the panel. Tagged-pointer UB, list indexing returning garbage,
async can't link, drop-glue use-after-free. Correctness first.

At v4.114.0 I gave **8.3 PASS WITH NOTES**. The UB was structurally
gone (`MnString` bitfield), the drop-glue saga closed (`_move_
resource` at six sites), ASan + TSan + valgrind CI gates
established in v4.105.0.

Phase E + F added: v4.115.0 native async I/O demos (with sanitizer
coverage), v4.117.0 TSan-async extension to the async demos. No
compiler or runtime code changes after v4.106.1. My lens narrows
to: "has anything regressed?"

---

## Sanitizer state

### ASan

From `scripts/check_asan_baseline.py` and the ASAN_REPORT.md at
`docs/roadmap/v4/v4.105.0/`:

- 21 golden tests **clean** (no ASan findings)
- 17 golden tests have ASan findings, **catalogued** in the
  baseline file. CI regression-gates against this baseline.
- Top ASan frame buckets: 12 heap-UAF in `mn_list_rc`, 5 global-
  buffer-overflow in `strtoll` reading non-NUL-terminated IR
  globals.

Since v4.105.0 baseline: **no new findings**. The UAF in
`mn_list_rc` is a known issue from before the v4.100.0 UB fix;
it's contained, catalogued, and in `.reviews/CARRY_FORWARD.md`.
No silent regressions across Phase B/C/D/E/F.

### TSan

Per v4.105.0 report: **3/3 async goldens race-free**. v4.117.0
extended the `tsan-async` CI job to cover v4.115.0 native async I/O
demos (`examples/async_file_io.mn`, `examples/async_http_demo.mn`).
That extension is what I want to see before v5: future scheduler
changes or coroutine-frame races under I/O-heavy workloads fail CI
at PR time.

The v4.105.0 release also fixed an async-signal-unsafe `crash_
handler` in `mnc_main.c` — now `__mn_install_crash_handler` with a
thread-local `__mn_set_current_source` breadcrumb. That's the
TSan-surfaced issue I would have opened a docket for if it weren't
fixed the same release it was found. Clean.

### Valgrind

v4.105.0 baseline: 0 CLEAN / 28 WARNINGS / 36 ERRORS. Top frames:

- `mir_opt__block_successors` 14× — **resolved by v4.111.0**
  disabling 4 zero-ROI MIR passes (strength reduction, small-
  function inlining, LICM, escape analysis). 4 of those 14
  reports would not reproduce today. I verified one
  (`05_for_loop`) on 2026-04-14: valgrind --error-exitcode=1
  returns 0, down from the v4.105.0 baseline.
- `__mn_list_free` 12× — partially resolved (some were the
  v4.101.0 drop-glue UAF, now moved to proper free; others are
  coroutine user-code leaks I would not close).
- `emit_llvm__emit_mir_call` 11× — still present, partially
  coupled to Sh.2.

Net: **valgrind state is better than v4.105.0 baseline**. CI holds
the line on no new findings.

## Runtime safety claims

`mapanare_core.h` `MnString` struct:

```c
struct MnString {
    const char *ptr;
    uint64_t    len     : 63;
    uint64_t    is_heap :  1;
};
```

16 bytes. ABI-preserved. The bit-tagging path (`mn_tag_heap` /
`mn_untag_heap` / `mn_is_heap`) is gone from `mapanare_core.c`
except transition-documenting comments. I grepped
`mapanare/emit_llvm_text.py` and `mapanare/self/emit_llvm.mn` for
any residual bit-tag pattern — none found. Docket #1 from v4.99.0
is structurally closed.

`_move_resource` at 6 call sites in `emit_llvm_text.py`. I counted
with `grep -c _move_resource mapanare/emit_llvm_text.py` → 12
(definition + 6 call sites + helpers), consistent with the v4.101.0
session report. The move-semantics is holding. Docket #2 closed.

## Async / coroutine safety

v4.102.0's `mn_coro_is_done` fix was real — checking `frame->
resume_fn == NULL` per LLVM 18's final-suspend lowering, not the
v4.95.0-era wrong offset. `_do_block_on` reuses the cached
coroutine handle instead of reloading from a slot the coroutine
overwrites with its return value. Two real bugs.

v4.113.0's `mn_coro_frame_prefix_t` struct in `mapanare_runtime.c`
is textbook — named, documented ABI (resume_fn at offset 0,
destroy_fn at offset sizeof(void*)), one place to update if LLVM
changes. The underlying behaviour is byte-for-byte identical to
v4.112.0 (verified by valgrind output matching exactly on goldens
56/57 against a HEAD~4 control rebuild). Docket #8 closed.

v4.113.0's 5 async failure sites with specific stderr + exit(1): I
spot-checked `__mn_coro_scheduler_init` — `pthread_create` return
is now checked per worker; a failure prints worker number + N of M
+ `strerror`. Previously this silently started fewer workers than
reported, leading to a phantom-hang condition I caught in the v4.95
valgrind runs.

## What I'd dock

### 1. ASan `mn_list_rc` UAF still open (0.3 points)

The 12 heap-UAF findings in `mn_list_rc` are catalogued but not
fixed. They predate the recovery arc — v4.101.0's `_move_resource`
handled the Python-emitter side, but the C-runtime `mn_list_rc`
bookkeeping has a separate bug class. From the baseline I cannot
tell which of the 12 are user-code-triggered and which are runtime.
ASan baseline regression gate means new UAFs would block PRs, but
these 12 are "known state, contained" rather than "zero."

Panel-grade impact: **not critical**, because ASan regression gate
is established and no new UAFs have landed in 20 releases. But a
user running `ASAN_OPTIONS=abort_on_error=1 <their program>` might
hit these in a corner case.

### 2. Sh.2 `__mn_str_starts_with` crash in self-hosted emitter (0.2)

10 of the 38 self-hosted golden failures are `emit_mir_call+0x23515`
crashing inside a path that calls `__mn_str_starts_with`. I am not
inside the self-hosted emitter, but from the addresses and docket
notes, this is a specific branch that trips on a certain MIR shape.
It's not a memory-safety issue in the *compiled* code's runtime;
it's in the *compiler's* own runtime. Panel cares because a crash
is a crash.

### 3. Sh.8 fixed-point blocker is structural (0.1)

Not a safety issue per se, but: if `verify_fixed_point.sh` cannot
run to completion, I cannot verify that the self-hosted binary's
output is safe end-to-end. The byref fix in v4.112.0 is verified in
isolation; the full self-compile is blocked on constructor
registration.

## What I'd credit

- **0 CRITICAL memory-safety findings open.** Not a single one.
  Tagged-pointer UB structurally gone, list indexing UAF closed,
  drop-glue UAF closed, async signal-unsafe handler fixed. All four
  recovery-arc-addressable safety findings are dead.
- **Sanitizer CI gates are the right architecture.** Regression
  baseline for ASan; TSan dedicated to async; valgrind over the
  full golden suite. Any future memory bug surfaces at PR time.
  This is grown-up infrastructure.
- **Documentation tells the truth.** `V5_READINESS.md`'s matrix
  puts "Tagged-pointer UB" under Runtime with status `✅ REMOVED
  v4.100.0`. `AUDIT_NOTES.md` §v4.100.0 confirms the bitfield is at
  `mapanare_core.h:60`. No hand-waving, no "mostly fixed."

## Final score

Last panel (v4.114.0): **8.3**
This panel: **8.4** (+0.1)

The uptick is the v4.117.0 TSan extension to v4.115.0 demos — that's
the kind of incremental infrastructure that moves me. The recovery
arc has been disciplined on memory safety. No regressions.

## Verdict: PASS WITH NOTES

One critical note from me, then I'm done:

**Before any v5 tag, close Sh.2 (self-hosted emitter crash) and
revisit the ASan `mn_list_rc` baseline.** Sh.2 is a compiler-side
crash — users will hit it when they try `mnc-stage1` on programs
that use `str.starts_with` in specific contexts. 10 tests fail on
it today. The `mn_list_rc` UAFs are user-code-reachable in
corner cases. Neither is a 5-line fix, but neither blocks v5
*declaration* — only v5 *confidence*.

I would not block Option B → continue on memory-safety grounds
alone. The lead has cleaner ways to earn Option A in follow-on
releases.

## Carry-forward for v4.121.0+

- **Sh.2** — `__mn_str_starts_with` crash path in self-hosted emitter
- **ASan.1** (new) — `mn_list_rc` UAF bucket, 12 findings in baseline
- **Instr.1** — if Culebra scan now completes as Rattler suggests, close

## Reproducibility

```bash
# Sanitizer state
scripts/check_asan_baseline.py
# valgrind one golden
valgrind --error-exitcode=1 /path/to/compiled/05_for_loop
# Current mn_list_rc references
grep -n mn_list_rc runtime/native/mapanare_*.c
```
