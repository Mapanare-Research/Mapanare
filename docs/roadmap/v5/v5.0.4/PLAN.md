# Mapanare v5.0.4 — "Cb.15: ABI Classifier to Self-Hosted"

> **Port the v4.149.0 ABI.1 sret classifier from Python to self-hosted.**
> The single biggest perf win of the v4 arc (`struct_alloc` 70× → 1.06×
> Rust) lives only in `mapanare/abi.py` + `mapanare/emit_llvm_text.py`.
> `mapanare/self/emit_llvm.mn` has no classifier; self-compiled programs
> (and the self-hosted compiler compiling itself) do not benefit.
>
> This is the "speed boost we only did for one."

**Status:** SHIPPED
**Breaking:** No (ABI-level — matches clang's convention on 17-64B
aggregates; existing code using these ABIs only via Python bootstrap
gains the optimization)
**Prerequisite:** v5.0.3 shipped
**Estimated work:** 2-3 sessions

---

## Why this release exists

Cobra v4.154.0 line 91-107:

> Cb.15-abi-self-hosted: opened, then lost. The v4.149.0
> SESSION_REPORT at line 125 explicitly says: "New LOW docket opened:
> **Cb.15-abi-self-hosted** — the self-hosted emitter
> (`mapanare/self/emit_llvm.mn`) doesn't have the classifier. This is
> a parity item for v4.152.0 or v4.153.0 scope." The v4.153.0
> DOCKET_LEDGER has 8 open dockets. Cb.15-abi-self-hosted is not
> among them…
>
> I verified by grepping `emit_llvm.mn` for `sret`, `classify_return`,
> `_use_sret`, `abi.py`, and `Cb.15`. Zero matches. The self-hosted
> emitter still uses the permissive by-value return path. This is not
> a correctness bug (LLVM's backend inserts sret silently), but it IS
> an ABI-parity gap between the Python and self-hosted emitters —
> exactly the class of divergence that Cb.5 (the inline-enum ABI saga)
> proved can be load-bearing.

Mamba v4.154.0 line 31-38 on the same fix from the Python side:

> struct_alloc: 1.198 ms → 0.018 ms. 70.47× Rust → 1.06× Rust. This
> is the single experiment that moved the needle the most. … 100K
> malloc+free per benchmark run → zero. This is the correct fix. I
> named this gap at v4.144.0. It is closed.

Closed on the Python side. Still open on the self-hosted side.

## What already works

| Component | File | Lines | Status |
|---|---|---|---|
| SysV AMD64 §3.2.3 classifier (≤ 16B → register) | `mapanare/abi.py::classify_sysv` | ~40 | Complete |
| Win64 x64 classifier (1/2/4/8B → register) | `mapanare/abi.py::classify_win64` | ~20 | Complete |
| AArch64 AAPCS64 classifier (≤ 16B → register) | `mapanare/abi.py::classify_aapcs64` | ~25 | Complete |
| Python emitter `_use_sret` | `mapanare/emit_llvm_text.py` | — | Complete |
| Test matrix (9 SysV + 6 Win64 + 3 AAPCS64 + 7 integration) | `tests/llvm/test_abi_struct_return.py` | — | 25 tests |

What's missing: all of that, in `.mn` form, callable from `emit_llvm.mn`.

## Scope

**In scope:**
- **New file** `mapanare/self/abi.mn` — classifier in Mapanare, mirroring
  `abi.py` shape: one `fn classify_return(ty: MIRType, target: TargetTriple)
  -> ReturnConvention` with the three target-specific branches
- **Edit** `mapanare/self/emit_llvm.mn` — add `fn emit_state_use_sret(st:
  EmitState, ty: MIRType) -> Bool` that calls into `abi.mn::classify_return`
  and returns `true` iff `ReturnConvention::Sret`
- **Replace** every emission site that currently uses the 64B
  threshold with a call to the new classifier
- **Parity test** — new `tests/llvm/test_abi_parity_self_hosted.py`:
  for each enum/struct in the golden corpus, assert Python
  `_use_sret(ty)` and self-hosted `emit_state_use_sret(ty)` agree
- Self-hosted goldens rerun to confirm stage2.ll picks up the new
  sret calls (`sret` count should go from ~0 to ~57 like the Python
  side's v4.149.0 measurement)

**Out of scope:**
- Changes to the Python classifier (`abi.py`) — that's the reference
  implementation
- Argument-passing classifier (`_use_byref` for params) — v4.149.0
  only changed the return path; params are a separate v5.x item
- Benchmark re-run with the new self-hosted binary — happens naturally
  at the v5.3.0 panel

## Exit criteria

1. `grep -c 'sret\|classify_return\|_use_sret' mapanare/self/emit_llvm.mn`
   → non-zero (Cobra's v4.154.0 verification grep now returns matches)
2. `tests/llvm/test_abi_parity_self_hosted.py` passes with 25+ tests
3. Self-compiled `stage2.ll` on Linux contains `sret` on the
   17-64B aggregate return signatures (match Python emitter's
   0 → 57 jump from v4.149.0)
4. Strict 3-stage fixed point holds (stage2 and stage3 byte-identical)
5. `benchmarks/cross_language/struct_alloc.mn` compiled via
   `mnc-stage1` (not just Python bootstrap) shows the ~70× improvement
   — the "speed boost we only did for one" now applies when the
   self-hosted compiler is the one compiling
6. Cb.15 entry in `docs/roadmap/v5/PARITY_GAPS.md` moves from
   "Inventory" to "Historical"

## Risks

**Risk 1 — fixed-point breaks.**
Any emitter change risks this. The `sret` emission changes function
signatures in the IR, which propagates through the self-compilation
output, potentially desynchronizing the stage2 ↔ stage3 byte-identical
invariant.
*Mitigation:* run `scripts/verify_fixed_point.sh` after every commit.
If it breaks, the Python and self-hosted classifiers are computing
different conventions somewhere — which is the bug we're fixing, so
the divergence surfaces correctness.

**Risk 2 — stack frames grow without `sret`.**
Functions that currently return 24-64B aggregates by value allocate
that aggregate on the caller's frame and copy. With `sret`, the caller
passes a pointer to the return slot. If the self-hosted compiler's
stack frames were tight under the old convention, the new convention
may shift stack layout and expose latent bugs.
*Mitigation:* v4.149.0 hit none of these on the Python side and had
identical measurements (55/66 goldens, same sanitizer state). If it
worked for Python, it'll work for self-hosted.

**Risk 3 — the self-hosted classifier subtly disagrees with Python.**
`abi.py` is ~99 LOC. A hand-port to `.mn` could diverge on edge
cases (e.g., zero-width fields, single-field structs, nested
aggregates). A one-off divergence breaks Exit Criterion 2 before it
breaks anything real.
*Mitigation:* the parity test runs *first* — port the classifier,
stand up the test, and iterate on the port until the test passes
*before* wiring the call into `emit_llvm.mn`.

## Rollback

If the port produces incorrect IR (fixed-point fails, goldens
regress): revert `emit_llvm.mn` to not call the new classifier. Keep
`abi.mn` in the tree as dormant code; close Cb.15 as deferred to
v5.1.x. The Python side is unaffected.
