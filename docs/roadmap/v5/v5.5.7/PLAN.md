# Mapanare v5.5.7 — "Sanitizer + fixed-point hardening"

> **Stabilization release. No new features. Sweeps the full
> sanitizer matrix on the 5 Sh.4 goldens (valgrind / ASan /
> TSan / LSan), hardens the destroy-path drop-glue, and
> investigates whether async emission contributed to or can
> clear the long-open Ve.1 stage3 regression.**

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.5.6 shipped (scheduler-driven, real
concurrency)
**Estimated work:** 1–2 sessions (~3–5 hours)

---

## Why this release exists

### v5.5.4–v5.5.6 left two classes of risk behind

**R1 — Drop-glue × coroutine cleanup (HIGH in DESIGN.md §6).**
v5.5.4 emits drop-glue BEFORE `ret` rewrites, covering the
normal ready-path. But the coroutine's `coro.cleanup` block
(entered when the scheduler destroys the coroutine at a
suspend point) runs NO drop-glue. Locals alive at the suspend
would leak.

Concretely: imagine an async fn that allocates a String
before its first `await`, then the `await`'s inner never
completes and the scheduler destroys the outer before the
String is consumed. That String is in the coroutine frame,
frame is freed by `coro.free`, but the String's backing
memory is separately heap-allocated and nobody calls
`__mn_str_free` on it.

For the 5 Sh.4 goldens, this doesn't materialize — all awaits
complete trivially. But it's a correctness time-bomb for any
real async program.

**R2 — Sanitizer silence is not proof.** v5.5.4–v5.5.6
valgrind-checked only 55_async_basic. Full matrix required:
- valgrind on all 5 Sh.4 goldens
- ASan on all 5
- TSan on 56/57/58/59 (the multi-await ones)
- LSan on all 5

### Ve.1 investigation

Open since v5.4.4. Stage3.ll is 0 lines because mnc-stage2
segfaults during lex of mnc_all.mn. v5.5.4 Q3 Phase 0
confirmed async work doesn't CAUSE Ve.1, but may or may not
have changed its character.

v5.5.7 re-runs `scripts/verify_fixed_point.sh` and investigates
the segfault with `valgrind_map` — is it the same drop-glue
bug v5.4.4 described, or has the surface shifted? Output: a
diagnosis report, possibly a fix, possibly a deeper deferral.

---

## Scope

### What ships

#### 7.1 — Full sanitizer matrix

`scripts/run_asan_goldens.sh`, `scripts/valgrind_all_goldens.sh`,
`scripts/run_asan_leak_goldens.sh` — all run against the 5
Sh.4 goldens (in addition to the existing corpus).

**Deliverables per sanitizer:**

| Sanitizer | Gate | Current baseline | v5.5.7 target |
|---|---|---|---|
| valgrind | 0 new ERRORS on 5 Sh.4 | 0 on 55 (v5.5.4/5.6) | 0 on all 5 |
| ASan | 0 findings on 5 Sh.4 | not measured on async yet | 0 on all 5 |
| LSan | 0 leaks on 5 Sh.4 | not measured on async | baseline or fix |
| TSan | 0 races on async goldens | v5.1.4 verified C runtime alone | 0 on goldens under v5.5.6 emitter |

Any new findings either get **fixed** (preferred) or
**baseline-gated** (documented in `docs/known_issues.md` with
Rt.XX ID).

#### 7.2 — Destroy-path drop-glue (R1 fix)

`emit_llvm.mn::emit_mir_function` — extend the coroutine
epilogue. Before `coro.free` in `coro.cleanup:`, emit drop-
glue calls for all currently-owned locals.

```
coro.cleanup:
  ; v5.5.7 — destroy-path drop-glue: free String/List/boxed
  ; locals alive at any suspend point before the frame is
  ; freed. CoroSplit's spill analysis will have hoisted these
  ; into frame slots; we run drop_glue at the MIR level so
  ; CoroSplit sees normal load+free sequences.
  <emit_drop_glue on str_owned / list_owned / boxed_owned>
  %coro.mem.free = call ptr @llvm.coro.free(token %coro.id, ptr %coro.hdl)
  call void @free(ptr %coro.mem.free)
  br label %coro.ret
```

**Challenge:** drop-glue currently uses `ret_val` tracking
from the normal-exit path. Destroy-path doesn't have a
"returned value" — it's cleanup only. Need a drop-glue
variant that skips no owners (`moved_locals` is irrelevant
since cancellation happens before move).

`emit_drop_glue_destroy(st: EmitState) -> EmitState` — new
helper that iterates `str_owned`/`list_owned`/`boxed_owned`
unconditionally and emits free calls.

**LOC:** ~40 (new helper + 5-line integration in epilogue).

**Risk:** CoroSplit spill analysis may not hoist all owned
locals into the frame if they're local to pre-suspend code.
In that case, the destroy-path would reference SSA values
that don't exist at the destroy point. v4.67.0 DESIGN.md §4.9
notes this:

> "For values that are conditionally initialized (only
> allocated on some paths), use a boolean flag in the frame
> to track whether cleanup is needed."

v5.5.7 ships the simple version (assume all tracked owners
are live at all suspend points). The 5 Sh.4 goldens have NO
heap-allocated locals inside async fns (just Int), so no
spill is exercised. Real I/O async programs would stress
this; deferred to v5.5.7 follow-up or v5.5.8.

#### 7.3 — Ve.1 investigation

Not a code change — an investigation + report. Write
`docs/roadmap/v5/v5.5.7/VE1_INVESTIGATION.md`:

1. Re-run `bash scripts/verify_fixed_point.sh --keep` at v5.5.7
   HEAD. Document current state.
2. Run `valgrind_map` on mnc-stage2 during lex of mnc_all.mn.
   Map the crash offset to a Mapanare source location.
3. Compare against v5.4.4's original Ve.1 notes.
4. Classify: (a) same bug still open, (b) bug has shifted,
   (c) bug is fixable, (d) bug is fixable BY async work, (e)
   bug is unrelated and should be a separate arc.
5. Recommend next action.

**If the investigation finds a small fix, ship it in v5.5.7.**
If it's a larger surgery, spec out v5.5.7.1 as its own micro-
release.

#### 7.4 — Fixed-point at best effort

`scripts/verify_fixed_point.sh --keep` run and results
documented. stage3.ll may still be 0 lines if Ve.1 isn't
fixed here. That's acceptable; note it.

### What does NOT ship

- New features (spawn/join/etc.). v5.5.8.
- Emitter structural changes beyond the destroy-path fix.
- Runtime changes.
- PARITY_GAPS.md update. v5.5.9.

---

## Exit criteria

1. valgrind: 0 new ERRORS across all 66 goldens (baseline
   unchanged or improved).
2. ASan: 0 findings on 5 Sh.4 goldens; full 66-golden sweep
   reported.
3. LSan: 0 new leaks on 5 Sh.4; existing baseline preserved.
4. TSan: 0 races on async goldens under v5.5.6 emission.
5. Destroy-path drop-glue helper present and wired, even if
   not exercised by goldens.
6. VE1_INVESTIGATION.md report complete.
7. Goldens harness 59/66 preserved.
8. stage2.ll llvm-as clean, self-hosting preserved.

---

## Design decisions

### D1 — Ship destroy-path drop-glue even if goldens don't exercise

Correctness debt. The 5 Sh.4 goldens don't cover the path, but
the path EXISTS in the IR. Future real-I/O goldens will hit
it. Shipping now means future work has the right foundation.

### D2 — Baseline-gate rather than fix if needed

If the sanitizer sweep finds a minor leak that's non-trivial
to fix (e.g., scheduler thread TLS residue), document as an
Rt.XX in `docs/known_issues.md` and baseline-gate in
`scripts/check_leak_summary.py`. Don't block the release.

### D3 — Ve.1 investigation is primary deliverable even if no fix

The goal is clarity. Even if Ve.1 remains open, a written
diagnosis that classifies it by type/scope lets future
releases plan properly.

### D4 — TSan requires a rebuild

`scripts/build_tsan.sh` presumably rebuilds mnc-stage1 with
`-fsanitize=thread` (or equivalent). Golden binaries also
need TSan link. Check whether the existing goldens harness
supports this or if it needs extension.

---

## Risks

### R1 — Sanitizer finds a real leak or race (MEDIUM)

Likely outcome: minor leaks (future struct + box double-free,
TLS residue, etc.). Most should be small fixes. If a TSan
race appears in the scheduler integration, that's v5.5.6's
bug and we fix in v5.5.7.

### R2 — Destroy-path drop-glue false positive (MEDIUM)

If we emit drop-glue for a local that was moved/consumed
before the suspend, we'd double-free. Need `moved_locals`
tracking to continue through suspend points. Python bootstrap
handles this via CoroSplit's liveness analysis — values not
live at suspend are spilled to dead-slots.

For v5.5.7, keep conservative: only emit drop-glue for
UNMOVED owners. The moved_locals set already lives in
EmitState; read it in `emit_drop_glue_destroy`.

### R3 — Ve.1 turns out to be blocked by v5.4.4 drop-glue (MEDIUM)

If the investigation reveals Ve.1 is specifically a drop-glue
infrastructure bug in the Own.1 Phase 2 code, the fix may be
large (rewriting the shadow-slot architecture). In that case,
spec v5.4.5 as a separate release to handle it.

### R4 — Fixed-point still broken after v5.5.7 (acceptable)

If Ve.1 isn't fixable in v5.5.7 scope, we document and move
on. stage2.ll llvm-as is the available gate; stage3 verification
is a nice-to-have blocked on a separate issue.

---

## What NOT to do

- Do not ship a half-done destroy-path fix. If edge cases are
  unresolved, document and defer — don't land code that's
  partially correct.
- Do not baseline-gate a real bug just to hit the release
  deadline. If a genuine leak / race appears, fix it.
- Do not try to fix Ve.1 if the investigation shows it's a
  deep drop-glue rewrite. That belongs in a separate arc.
- Do not add spawn/join. v5.5.8.
