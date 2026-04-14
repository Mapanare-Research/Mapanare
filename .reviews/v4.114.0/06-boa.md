# Boa v4.114.0 Review — Python / Developer Experience

## Score: 8.5 / 10
## Verdict: PASS

## Context

v4.106.0 I was the highest at 8.5 PASS — developer experience had
matured through Phase A / Phase B. The v4.99.0 docket item #11
(async error messages) was the only DX-relevant item I owned; I
flagged: "tell the user WHAT failed in the async pipeline, not just
that something failed."

v4.113.0 landed that fix. I am one of the primary reviewers for it.

## Primary lens — Docket #11: async error messages

### Sites improved

`runtime/native/mapanare_runtime.c`:

1. `__mn_coro_scheduler_init`: worker `pthread_create` failure
2. `__mn_coro_scheduler_register`: scheduler-not-initialised guard
3. `__mn_coro_scheduler_register`: deque+overflow both full
4. `__mn_coro_register_wait`: overflow full (suspended await
   loses resumer)
5. `__mn_file_read_async`: `calloc` Future alloc failure
6. `__mn_file_read_async`: `malloc` ctx alloc failure
7. `__mn_file_read_async`: `pthread_create` failure

5 call paths, 7 messages. My docket asked for "at least 3
improved"; v4.113.0 delivered 5.

### Are they genuinely improved?

I read each message against my own "would a user understand what
went wrong" bar:

**Site 1** (pthread_create in scheduler):
> mapanare: async runtime: failed to spawn worker thread K of N:
> <strerror> (errno E). Likely causes: RLIMIT_NPROC exhausted, or
> ENOMEM at pthread stack allocation. Try lowering
> MAPANARE_ASYNC_THREADS or raising `ulimit -u`.

**YES.** Names the failed worker index, the errno with strerror
text, two likely causes, and two actionable fixes. This is the
reference for what async errors should look like.

**Site 2** (scheduler not initialised):
> mapanare: async runtime: cannot spawn task — scheduler not
> initialised. The main() emitted by the compiler should call
> __mn_coro_scheduler_init() before any async function runs; if
> this message appeared, the emitter (mapanare/emit_llvm_text.py)
> dropped that call for the current entry point.

**YES.** Names the missing init call. The user hitting this
error is either a compiler contributor (in which case the
reference to `emit_llvm_text.py` is the exact file to look at) or
a user whose code did something unusual (in which case the
message tells them what the runtime expected).

I **manually triggered this in v4.113.0 Phase 4**:
```
$ /tmp/test_scheduler_uninit
mapanare: async runtime: cannot spawn task — scheduler not ...
$ echo $?
1
```
Exit code 1, named message. Reproducible.

**Site 3** (deque + overflow full):
> mapanare: async runtime: failed to spawn task — both worker-0
> deque (cap=1024) and global overflow queue (cap=4096) are full.
> Too many concurrent spawn() calls without await points; the
> scheduler cannot drain. Rewrite to spawn in batches or add an
> await.

**YES.** Names both capacities, diagnoses the usage pattern, and
suggests the fix.

**Site 4** (register_wait overflow full):
> mapanare: async runtime: cannot register await — global overflow
> queue (cap=4096) is full. Coroutine at 0x<addr> is awaiting
> Future at 0x<addr>; without a resumer slot it will never wake.
> Rewrite to limit concurrent awaits.

**YES.** This is the single most damaging async failure mode —
a parked coroutine with no resumer. Naming the handle + Future
addresses is gold for debugging.

**Site 5, 6, 7** (file_read_async allocation paths):

All three name the specific failed allocation. Acceptable.

### Reachability

v4.113.0 PRE_PANEL_AUDIT is honest: "1 of 5 sites reachable without
env stress; the other 4 are wired guards requiring RLIMIT_NPROC
exhaustion, queue overflow, or OOM."

I would have liked regression tests for each path. That's a stretch
— writing a test that reliably exhausts `RLIMIT_NPROC` inside CI is
fragile. I'll accept "correctly wired, message is named" with one
caveat for Phase E: **add a pytest fixture that mocks the failure
at the guard** (e.g., a debug-only env var
`MAPANARE_ASYNC_FAIL_AT_WORKER=2`) so site 1 can be exercised.

**Sub-score for #11: 9.0 / 10.** Messages are the right shape.
Reachability proof for 1 of 5 is adequate; 5 of 5 would be 10.

## Primary lens — SPEC keywords (docket #10, DX angle)

A user running `let sino = 42` and seeing a parse error used to
hit the wall: no SPEC text to help, no error-message hint. §2.1.1
now lists every bilingual keyword. The DX improvement is real.

Bonus: the error message `MN-P-006: unexpected token` is referenced
in §2.1 intro, so a user can search the SPEC by error code and land
on §2.1.1.

## Primary lens — Python dev workflow

`make test` / `make lint` / `dev.ps1 validate` all work.
`scripts/test_native.py` harness is stable. `pytest -n auto` runs
clean (modulo the pre-existing 67 unrelated failures in CI-tool
checks / lint / binding tests). None of the Phase D releases broke
the dev loop.

`python -m mapanare emit-llvm file.mn -o out.ll` still emits valid
IR. `python -m mapanare run file.mn` still works as a fast dev
path. Phase D respected the "don't break the user's daily
workflow" principle.

## What I'd flag

1. **Add reachability tests for async error sites.** Phase E task.
   Env-var based mocking of the guard makes testing feasible.
2. **SPEC §2.1.1 could link to error-code Appendix D.** Minor doc
   polish; not blocking.
3. **`mapanare test` self-hosted path is limited.** The full test
   runner works via Python; the self-hosted `mnc test` supports
   fewer assertions. Carry-forward; not a Phase D regression.

## Verdict

**PASS @ 8.5.**

v4.113.0 delivered what I asked for. The messages are specific,
actionable, and in the project's voice. Site 2 triggered and
verified. The one thing missing — reachability tests for the other
four — is the kind of instrumentation that belongs in Phase E.

Phase D closes if the aggregate holds.
