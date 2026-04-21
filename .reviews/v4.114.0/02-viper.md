# Viper v4.114.0 Review — Memory safety

## Score: 8.5 / 10
## Verdict: PASS

## Context

At v4.106.0 I gave **7.5 / 10 PASS WITH NOTES**. The tagged-pointer
UB was closed (Phase A), but I flagged the coroutine frame's
hardcoded `*(void **)handle == NULL` read in `mn_coro_is_done` —
"fragile; any layout change silently corrupts the status check." I
wanted that structurally decoupled, the same way the `is_heap`
bitfield replaced `mn_tag_heap`.

v4.113.0 landed that fix. I am the primary reviewer for it.

## Primary lens — Docket #8: coroutine frame decoupling

### The fix

```c
typedef struct mn_coro_frame_prefix {
    void (*resume_fn)(void *handle);   /* NULL ⇒ coroutine completed */
    void (*destroy_fn)(void *handle);  /* frees the coroutine frame  */
} mn_coro_frame_prefix_t;

static inline int mn_coro_is_done(void *handle) {
    const mn_coro_frame_prefix_t *frame = (const mn_coro_frame_prefix_t *)handle;
    return frame->resume_fn == NULL;
}
```

Both functions (`mn_coro_is_done` and `mn_coro_resume`) now use
typed field access. 15 lines of comment inside the typedef document
the LLVM switched-resume ABI contract.

### Was this fix needed?

Yes, but not for a reason I gave in v4.106.0. I called it "fragile"
— that framing was slightly wrong. The cast was never *unsafe*;
`*(void **)handle` and `frame->resume_fn` compile to the same load
on x86_64 with the LLVM switched-resume lowering. The fix I asked
for was really a **review-surface** fix: a reader scanning the
scheduler shouldn't have to reverse-engineer the LLVM coroutine ABI
from a raw cast.

That is what v4.113.0 delivered. The named struct provides:
- One definition to update if LLVM ever changes the ABI
- Grep-able field names that name what's being read
- A 15-line comment documenting the ABI invariants

It doesn't find any bugs. It prevents a class of future bugs where
a contributor adds a third coroutine-related field and offset
arithmetic starts to matter.

**Sub-score for #8: 9.0 / 10.** Execution is clean. The only reason
it's not 10 is that a reviewer might reasonably ask "why didn't you
use `llvm.coro.done` intrinsic directly in C?" — the answer is "the
intrinsic is only callable from IR, and the C scheduler isn't
generated IR." Fair answer; worth stating inline.

### Hardcoded-offset audit

My ask: zero raw coroutine-frame offset reads anywhere in
executable code. v4.113.0's grep audit is documented in
`v4.113.0/SESSION_REPORT.md` and re-run in v4.114.0 Phase 1. Two
matches, both in comments:

- `runtime/native/mapanare_runtime.c:1536` — comment describing
  the old pattern
- `mapanare/emit_llvm_text.py:4941` — comment about LLVM's
  `destroy_fn` slot

**Zero executable code reads the coroutine frame by raw offset.**
The audit is tight.

## Primary lens — Valgrind on async goldens

Re-ran on 2026-04-14:

| Test | `definitely lost` | `indirectly lost` | ERROR SUMMARY |
|---|---:|---:|---|
| 55_async_basic | 0 | 0 | **0 errors from 0 contexts** |
| 56_async_await | 32 B (1 block) | 24 B (2 blocks) | **0 errors from 0 contexts** |
| 57_real_await | 96 B (3 blocks) | 72 B (6 blocks) | **0 errors from 0 contexts** |

Zero memory-safety errors on all three. The leaks are in user code
(`inner`, `fetch_a/b/c` boxing return values via `malloc`), not in
the coroutine infrastructure.

What I care about most: v4.113.0's `async-valgrind.md` artifact
records a byte-for-byte comparison between post-change and
pre-change valgrind output. Same leak sites, same byte counts,
same addresses (modulo ASLR). This is the right shape of proof
for an ABI-adjacent change — it is not enough to say "still passes";
you have to prove nothing is leaking *differently*.

v4.113.0 did that proof. I re-ran the control. Numbers match.

## Secondary — ASan on the same tests

| Test | Output | ASan errors | Leak bytes |
|---|---|---:|---:|
| 55_async_basic | 42 | 0 | 0 |
| 56_async_await | 43 | 0 | 56 (user code) |
| 57_real_await | 110 | 0 | 216 (user code) |
| 06_struct | 3 | 0 | 0 |

Zero functional ASan errors. Leak sites match valgrind. Defense in
depth held.

## Secondary — Async error messages (docket #11, shared with Boa)

Not my lane, but overlap: the new `mapanare: async runtime:` bail
paths (`__mn_coro_scheduler_init` on `pthread_create` failure,
`__mn_coro_scheduler_register` pre-init guard, queue-full bail) all
`exit(1)` deterministically. This closes a small class of
"spawn() silently drops tasks" memory-safety concerns — a dropped
coroutine is a leaked coroutine frame. +0.2 for indirect memory
safety improvement.

## What I'd flag for the panel

1. **Coroutine frame fix is a documentation / review-surface win,
   not a bug fix.** Sessions reports are honest about this but the
   docket list could look like a bug-fix claim. Reviewers should
   score it as what it is: an ergonomic / future-proofing fix.

2. **Pre-existing async leaks persist.** The 56/57 leaks come from
   `__mn_Int_box` sites in user coroutine bodies. Phase D didn't
   touch them. A future release should close them — tracking as
   `Coro.1` (opened here).

3. **Valgrind baseline automation holds.** `check_valgrind_baseline.py`
   in CI would catch any regression; the control experiment in
   v4.113.0 proves the tooling works. Good infra.

## Verdict

**PASS @ 8.5.**

The coroutine frame fix does what I asked, with the framing
refinement that it's ergonomic rather than unsafe-to-safe. Valgrind
and ASan both clean of errors. Byte-for-byte memory-neutral control
experiment is the right kind of proof.

Phase D closes if the aggregate holds.
