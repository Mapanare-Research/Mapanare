# Cobra v4.106.0 Review — ABI / fixed-point

## Score: 7.5/10
## Verdict: PASS WITH NOTES

## Context: v4.99.0 → v4.106.0

At v4.99.0 I gave 6.5/10 PASS WITH SIGNIFICANT NOTES, partially dissenting
on the tagged-pointer UB framing — the bit-0 tagging was *intentional*
(that's what `mn_tag_heap` was for), even if the LLVM provenance model made
it fragile. Phase A has now addressed that framing concern head-on by
moving the flag into a bitfield: the `data` pointer is always a valid
pointer, and the UB class is structurally gone. That is exactly the shape
of fix I asked for. The ABI lens for v4.106.0 therefore shifts from "is
the UB gone?" (yes) to "are the two emitters' ABIs converged enough to
allow fixed-point self-compilation?" (not yet — and Phase A never claimed
they would be).

## MnString ABI (Item #1, Phase A)

**CLOSED.** `runtime/native/mapanare_core.h:57-61` defines:

```c
typedef struct {
    const char *data;
    uint64_t    len     : 63;
    uint64_t    is_heap : 1;
} MnString;
```

Size: `8 (ptr) + 8 (uint64_t bitfield word) = 16 bytes`. Matches the
LLVM-IR form `{ ptr, i64 }` that both emitters produce. Bit 63 of the
second eightbyte is `is_heap`; bits 0–62 are `len`. The exported masks
`MN_STR_LEN_MASK = 0x7FFF...` and `MN_STR_HEAP_BIT = 0x8000...` at lines
67–68 are the ABI contract for any IR-level consumer. SysV AMD64 / Win64
register-return path is preserved — no `byval` / `sret` churn was forced
on callers, which is the reason the 16-byte ceiling was worth defending
(SESSION_REPORT.md lines 58–73 document the 24-byte alternative that
would have crossed the two-eightbyte register boundary and segfaulted).
Python ctypes binding, self-hosted emitter's inline mask, and
`__mn_str_len` helper are all consistent on which half of the word is
length vs flag. Clean.

## Bootstrap vs stage1 ABI divergences (v4.104.0 Div.3, Div.5)

**Div.3 — Option payload ABI divergence. HIGH in my lens, MEDIUM on the
docket.** Bootstrap emits `Option<Int>` as `{ i1, i64 }` (payload
inlined); stage1 emits `{ i1, ptr }` (payload boxed). Both produce `42
... 7` on `17_option` because the value `7` fits in a pointer slot — but
this is observational luck, not agreement. Any scenario where the two
emitters' outputs are linked together (bootstrap-compiled caller invoking
stage1-compiled callee returning `Option<Int>`, or the reverse) would
mismatch at the calling convention and corrupt the flag or payload. More
importantly: **fixed-point self-compilation requires ABI agreement.** If
the bootstrap compiles `self/` to one Option layout and `mnc-stage1`
recompiles the same sources to a different Option layout, stage2 IR will
differ structurally from stage1 IR on every function that touches
`Option`. That is exactly what the 21/64 golden ceiling hides: the stage1
compiler is consistent *with itself*; it is not interchangeable with the
bootstrap.

**Div.5 — main return type (`i64` bootstrap vs `i32` stage1). LOW.**
Linux x86_64 / System V expects `i32`; stage1 is ABI-correct, bootstrap
works only because the high 32 bits happen to be zero. Noted, not
blocking.

## byref size heuristic (v4.99.0 item #7)

**Status: OPEN.** MEASUREMENTS.md line 118 correctly lists this as not in
Phase A scope. I do not downgrade for this — Phase A's claimed scope was
the 5 critical/high items, and #7 was MEDIUM. But it is a related ABI
concern and should be a Phase C entry.

## Fixed-point implications

Fixed-point self-compilation (the v5.0.0 gate) requires the two emitters
to converge on a single ABI. Today:

- `MnString`: converged (both emit `{ ptr, i64 }` with bit-63 semantics).
- `Option<T>`: **not converged** (Div.3). Blocking for fixed-point.
- `main` return: cosmetic divergence (Div.5).
- byref size heuristic: OPEN (docket #7).
- `internal` linkage + declare preamble: cosmetic; `build_stage1.py`
  normalizes via post-processing.

Phase A delivered its scope; it did not promise ABI unification. Grading
should reflect that the Phase A docket is closed honestly, not that ABI
convergence shipped.

## Findings

1. `MnString` bitfield: structurally sound, ABI-preserving, cleaner than
   tagging. Full credit.
2. Option payload (Div.3) is a latent ABI incompatibility that blocks
   v5's fixed-point claim. Not a Phase A regression, but the panel should
   not let it drift into "fixed-point works" rhetoric.
3. `main` return (Div.5) is cosmetic but should be unified on `i32` per
   SysV — stage1 is already correct; fix the bootstrap, not stage1.
4. 17/18 stage1 runnable tests byte-identical to bootstrap (MEASUREMENTS
   line 49) is strong evidence that stage1-internal ABI is self-consistent.

## Docket items you would open

- **Cb.1 MEDIUM** — Unify `Option<T>` representation between
  `mapanare/emit_llvm_text.py` and `mapanare/self/emit_llvm.mn`. Pick the
  stage1 `{i1, ptr}` form (pointer-uniform, generics-friendly) OR the
  bootstrap `{i1, i64}` form (no heap pressure for small payloads);
  document the choice in an ABI spec. Required for fixed-point.
- **Cb.2 LOW** — Align `main` return type to `i32` in the bootstrap.
- **Cb.3 MEDIUM (carry-over)** — Byref size heuristic divergence (v4.99.0
  item #7) still OPEN. Assign to Phase C.
- **Cb.4 LOW (new)** — Publish an MnString ABI contract doc that records
  the bit-63 `is_heap` convention and the `MN_STR_LEN_MASK` expectation
  for third-party FFI. Currently only in the header comment.

## Grade justification

The tagged-pointer characterization concern from v4.99.0 is structurally
addressed — the `data` pointer is a real pointer again. That is worth +1
over my prior 6.5. The Option ABI divergence (Div.3) and the open byref
heuristic prevent a full PASS; both are real fixed-point blockers.
Phase A's scope was the 5 critical/high items, all CLOSED with evidence;
I do not penalize for work that was not promised. Net: **7.5/10 PASS
WITH NOTES.**

## One-line summary

MnString ABI landed clean at 16 bytes with a proper bitfield; Option
payload still diverges between emitters (`{i1,i64}` vs `{i1,ptr}`) —
Phase A shipped what it promised, but fixed-point self-compilation is
still gated on unifying that one layout.
