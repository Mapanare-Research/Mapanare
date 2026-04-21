# v4.112.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase D release 2 complete.** Docket #7 closed: the
self-hosted emitter's `is_byref_type()` no longer misclassifies
small named struct types as byref. A new `struct_byte_size(st, ty)`
helper resolves `%struct.Foo` through the registered struct table
and computes real sizes from the inline `{...}` form, matching the
Python bootstrap's `_tsz` algorithm at `mapanare/emit_llvm_text.py:141`.

Fixed-point convergence itself (stage2 == stage3 byte-for-byte) was
not measured. The self-hosted `mnc-stage1` still cannot compile its
own sources at Stage 1 of `verify_fixed_point.sh`: `mnc_all.mn`
contains `let mut guard: Option<Expr> = None` literals, and
self-hosted `semantic.mn` doesn't register `None` as a constructor.
Python bootstrap bypasses this gap with `skip_check=True`; the
self-hosted compiler has no bypass. This is a pre-existing
semantic gap surfaced by v4.111.0's stage2 validation — not caused
by any v4.112.0 change, not in scope for docket #7.

Given that blocker, the byref fix was verified through:

1. Unit test `/tmp/byref_test.mn` with explicit 16-byte and 80-byte
   structs, byval/byref classification inspected pre/post-fix
2. IR validation (`llvm-as` accepts), full pipeline compiles, binary
   runs with correct output
3. Golden suite: 26/64 passing (identical to v4.111.0 result, zero
   regressions)
4. Spot inspection of `27_impl` and other small-struct goldens —
   methods now emit byval receivers where appropriate

## Self-graded aggregate

**7.8 / 10**

- **Targeted fix landed**: Docket #7 closed with a minimal,
  justified change — 48 added lines, 7 call-site updates. The
  algorithm matches the Python bootstrap's `_tsz` where it matters
  (byref threshold comparison). +strong
- **Scope honesty**: Did not try to fix the `None` semantic gap
  that blocks fixed-point verification — that's a separate,
  larger work item that deserves its own docket (Sh.8) and its
  own release. Wrote the analysis clearly stating that
  fixed-point measurement is blocked, documented why, did not
  pretend the verification was complete. +solid
- **No regressions**: Verified 26/64 golden pass rate is
  preserved byte-for-byte; IR validation still passes; self-hosted
  stage1 still builds cleanly. The fix is strictly additive. +solid
- **Forward dockets clear**: Sh.3 closed, Sh.8 opened,
  Sh.1/Sh.2 carried. The next release (v4.113.0) has a clean
  work surface. +solid
- **What's missing**: Fixed-point script exit criteria 1, 6 marked
  ⚠ because of the Stage 1 blocker. Pragmatic mitigation per
  PLAN.md risk register ("Use --keep to capture partial output.
  Debug the compilation failure as a separate issue.") — but 4 of
  10 exit criteria are blocked. In a future release, fixing
  `None`/`Some` should come **before** more fixed-point work. −soft
- **Culebra scan not completed**: same 854K-line main.ll that
  blocked v4.111.0's scan also blocked this release's. Deferred.
  −soft

## What shipped

### Code changes (production)

- `mapanare/self/emit_llvm.mn` — single-file diff:
  - NEW `struct_byte_size(st: EmitState, ty: String) -> Int`
    (14 lines): resolves `%struct.Foo` through `st.structs`,
    returns `llvm_aggregate_size(entry.llvm_type)`; falls back to
    256 for unregistered names.
  - NEW `is_byref_type_st(st: EmitState, ty: String) -> Bool`
    (10 lines): state-aware byref classifier. Named struct →
    `struct_byte_size`; inline `{...}` → `llvm_type_size` as
    before.
  - RETAINED `is_byref_type(ty)` as back-compat wrapper (no
    current call site uses it; kept for safety in case future
    code lacks EmitState access).
  - UPDATED 7 call sites of the old `is_byref_type` to
    `is_byref_type_st(st|s, ...)`. Every site had EmitState in
    scope; no plumbing required.
- `mapanare/self/mnc_all.mn` — regenerated via `concat_self.py`.

### Documents

- `docs/roadmap/v4/v4.112.0/DIVERGENCE_ANALYSIS.md` — the release's
  primary document, 170 lines. Phase-by-phase analysis:
  baseline (blocked), divergence classification, fix summary,
  post-fix verification, exit criteria scorecard.
- `CHANGELOG.md` — [4.112.0] entry with the full story.
- `docs/roadmap/v4/v4.112.0/SESSION_REPORT.md` — this file.

## Key numbers

### Byref classification change

| Struct size | Pre-fix                  | Post-fix                  | Correct? |
| ----------- | ------------------------ | ------------------------- | -------- |
| 8-byte `Counter`   | `ptr %self.byref` | `%struct.Counter %self`   | ✅ post  |
| 16-byte `Small`    | `ptr %s.byref`    | `%struct.Small %s`        | ✅ post  |
| 16-byte `Point`    | `ptr %p.byref`    | `%struct.Point %p`        | ✅ post  |
| 80-byte `Large`    | `ptr %l.byref`    | `ptr %l.byref`            | ✅ both  |

### Golden pass rate

| Release        | Pass / Total | Delta |
| -------------- | -----------: | ----: |
| v4.111.0       | 26 / 64      | —     |
| **v4.112.0**   | **26 / 64**  | **0** |

No regressions from the byref change; no new passes (fixing byref
classification for small structs doesn't unblock any pre-existing
failure category).

## Exit criteria (PLAN.md, 10 items)

| # | Check | Status |
|---|-------|--------|
| 1 | Fixed-point script runs | ⚠ Stage 1 blocked by pre-existing `None` gap |
| 2 | Baseline divergences documented | ✅ `DIVERGENCE_ANALYSIS.md` §Phase 1-2 |
| 3 | Divergences classified | ✅ Table: byref / structural / cosmetic / semantic-gap |
| 4 | Docket #7 fixed: real struct sizes | ✅ `struct_byte_size` + `is_byref_type_st` |
| 5 | Real struct sizes verified on golden | ✅ `byref_test.mn` + 27_impl inspection |
| 6 | Fixed-point re-run after fix, delta recorded | ⚠ Same blocker; byref verified via other means |
| 7 | Culebra fixedpoint result recorded | ⚠ Deferred (long-running on 854K-line IR) |
| 8 | Golden tests: no regression from v4.111.0 | ✅ 26/64 preserved |
| 9 | `DIVERGENCE_ANALYSIS.md` with before/after | ✅ 170 lines |
| 10 | No new divergences from the fix | ✅ Golden diff + IR validation both clean |

6 of 10 green; 4 of 10 blocked on pre-existing `None` gap or
infrastructure (culebra bounded-time scan).

## Dockets

| Docket | Status     | Description |
| ------ | ---------- | ----------- |
| #7 / Sh.3 | **CLOSED** | Byref size heuristic (this release) |
| Sh.8   | OPEN (new) | Self-hosted `None` / `Some` / `Ok` constructor registration → unblocks fixed-point |
| Sh.1   | OPEN       | `inline_small_functions` MIR corruption (from v4.111.0) |
| Sh.2   | OPEN       | `emit_mir_call` NULL `starts_with` crash (from v4.111.0) |
| #8     | OPEN       | Coroutine frame layout coupling → v4.113.0 |
| #10    | OPEN       | Keyword collision SPEC doc → v4.113.0 |
| #11    | OPEN       | Async error messages → v4.113.0 |

## What v4.112.0 proved

Docket #7's fix is straightforward when the machinery is in place:
struct info was already registered in `st.structs` with the inline
LLVM form, just not being queried for byref decisions. The
divergence analysis also makes explicit that full fixed-point
convergence will require closing the `None` semantic gap in
self-hosted first — a task that belongs in its own release
(tentatively Phase D later, docket **Sh.8**).

v4.113.0 pivots to the remaining v4.99.0 panel dockets (#8, #10,
#11) and may also address Sh.8 if scope permits. After v4.113.0 all
v4.99.0 panel items are closed. v4.114.0 is the Phase D panel.
