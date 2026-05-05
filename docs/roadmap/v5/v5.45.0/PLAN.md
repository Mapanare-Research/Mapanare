# v5.45.0 — Ts.2 + Ts.3 — tensor mutable views + stepped slices; tensor closeout arc CLOSED

**Status:** PLANNING
**Type:** Compiler / codegen / runtime closeout. Closes the
v5.41.0 option-B contract (Ts.2 + Ts.3) that has been carried
4 releases past its commitment slot. Adds grammar for stepped
slices, refcount on `mapanare_tensor_t`, and view aliasing
under a refcount-aware drop-glue model. After v5.45.0 the
"Not yet on LLVM" line in CLAUDE.md drops `mutable views,
stepped slices` — the tensor closeout arc is fully done.
**Breaking:** No, in the surface sense. **Yes, ABI** — the
`mapanare_tensor_t` struct grows by ~16 bytes (refcount + view
flag + parent pointer). All consumers go through the regular
recompile cycle (stage1 must be rebuilt between bump and
verify per the v5.31.0 lesson). No tagged binary outside the
project is expected to consume `mapanare_tensor_t` directly.
**Prerequisite:** v5.44.0 shipped (package-aware imports +
stdlib extraction runway). Tensor closeout was promised at
v5.41.1 / v5.42.0 / v5.43.0 / v5.44.0 — escalates to HIGH at
this slot if not landed.
**Estimated effort:** 3–5 working days (per v5.41.0
PRE_PHASE_AUDIT corrected budget). Roughly equal in size to
v5.43.0 Da.\* but with a smaller blast radius (one struct,
one C runtime file, four codegen branches).

---

## Why this exists

v5.41.0 PRE_PHASE_AUDIT laid out a three-option scope: full
closeout (option A), Ts.1-only at v5.41.0 + Ts.2+Ts.3 at
v5.41.1 (option B), or strike the parity-gap claim (option C).
Lead picked option B. v5.41.0 shipped Ts.1 (reshape with copy
semantics). Ts.2 + Ts.3 were committed for v5.41.1.

v5.41.1 → v5.44.0 shipped without the closeout. The reasons
were each defensible in isolation — Ai.\* manifesto kickoff at
v5.40.0 was load-bearing for the user-visible thesis; v5.42.0
As.\* and v5.43.0 Da.\* finished the manifesto arc; v5.44.0
Ps.\* was the ecosystem bridge before the panel — but
collectively they push a v5.41.0 commitment 4 releases past
its slot. **The audit's escalation rule fires now: MEDIUM at
v5.41.1, HIGH if not landed by v5.42.0; we're now at v5.45.0,
firmly past the threshold.**

The structural argument for closing now, before the v5.47.0
panel:

1. **The CLAUDE.md "Not yet on LLVM: tensor reshape, mutable
   views, stepped slices" line is partially closed.** Reading
   the line at panel time as half-closed is worse than closing
   it before the panel reads it.
2. **Ts.2 mutable views require `mapanare_tensor_t` refcount
   surgery.** Doing this surgery before the panel green-lights
   v6.0 means the borrow checker has stable ground; doing it
   after means borrow-check has to track an in-flight ABI
   change.
3. **Ts.3 stepped slices require grammar + AST + parser
   changes.** Those are a category of edit ("language surface
   that the borrow checker will see") that should be settled
   before v6.0 starts auditing language surface.
4. **Tensor reshape's copy-semantics stopgap from v5.41.0
   becomes refcount-aliased here.** v5.41.0 documented this
   as a v5.41.1 swap — the `noalias` attribute on
   `__mn_tensor_reshape` drops at this release.

The v5.41.0 PRE_PHASE_AUDIT laid out the structural moves
already. v5.45.0 executes that audit's recommendation
mostly verbatim, with one PLAN-level deviation: the audit
treated `mapanare_tensor_t` as having "no refcount, no
strides, no offset" and budgeted refcount only. **v5.45.0
adds refcount and a view flag, but does NOT add strides or
offset.** Strided / non-contiguous tensors are a v6.0+
candidate; v5.45.0 ships **shape-only views** (a view shares
the parent's data buffer with possibly different shape, but
remains contiguous-row-major). This is the smallest closure
that satisfies the parity-gap claim without opening the
strided-tensor ABI. Stepped slices return **independent
copies** (not views) for the same reason — stepped data is
inherently non-contiguous and would force strides.

This split is honest about scope:
- **Ts.2 view-aliasing:** ships at v5.45.0; only for shape-
  preserving or shape-changing views over the same contiguous
  buffer (`view()`, the alias-flavor of `reshape()`).
- **Ts.3 stepped slices:** ships at v5.45.0 as **stepped
  copies** — same surface as Ts.2's slice-with-step but copy
  semantics underneath, like v5.41.0's `__mn_tensor_slice`.
- **Strided views / non-contiguous tensors:** v6.0+. Listed
  on the v6.0 carry, not a v5.45.0 obligation.

---

## Goals

1. **Ts.2.A** — Refcount on `mapanare_tensor_t`. Append-only
   struct extension; existing consumers see zero behavior
   change. `__mn_tensor_free` becomes refcount-aware.
2. **Ts.2.B** — Mutable view via `t.view(shape)` and the
   alias-flavor of reshape. Both share data buffer with
   parent; both bump parent's refcount; both drop the
   `noalias` attribute that v5.41.0 placed on
   `__mn_tensor_reshape`.
3. **Ts.3.A** — Grammar + AST + parser for `[start..end:step]`
   range syntax. Single new lexer token; `RangeExpr.step`
   field; `IndexItem.step` field; parser construction.
4. **Ts.3.B** — Lower + emit + runtime for stepped slices on
   `Tensor`. Copy semantics. Returns a fresh tensor — no
   refcount sharing.
5. **Ts.4** — Test corpus: 3 new goldens (one for views, one
   for stepped slice, one for reshape-as-view), aliasing
   regression tests, drop-glue ASan / valgrind sweep, golden
   boundary cases.
6. **Ts.5** — `docs/stdlib/tensor.md` cookbook (deferred from
   v5.41.0 because surface was incomplete; ships at v5.45.0
   when surface is fully closed).
7. **Ts.6** — CLAUDE.md "Not yet on LLVM" line fully
   closed; SPEC sync; CHANGELOG.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Ts.2.A** | HIGH | **Refcount on `mapanare_tensor_t`.** Append `int64_t refcount` + `uint8_t is_view` + `mapanare_tensor_t *parent` (NULL if not a view). `mapanare_tensor_alloc` initializes refcount=1, is_view=0, parent=NULL. `__mn_tensor_free` decrements refcount; only frees data + metadata when refcount hits zero. Views: increment parent's refcount on creation; decrement parent's refcount when view itself drops to zero (then check parent for free). **Append-only:** new fields go at end of struct; pre-v5.45.0 stage1 binaries linked against post-v5.45.0 runtime fail loudly at link (struct size mismatch in any caller using `sizeof(mapanare_tensor_t)`). Document this in SESSION_REPORT — same pattern as v5.42.0 As.6 binary-compat regression. | 4h |
| **Ts.2.B** | HIGH | **Mutable view surface.** New runtime export `__mn_tensor_view(parent, shape: const MnList *)` allocates view metadata sharing parent's data buffer; bumps parent's refcount. Lower path: `t.view(shape)` on builtin `Tensor`. Reshape's alias-flavor (the v5.41.0 stopgap was copy semantics): `__mn_tensor_reshape` drops the `noalias` attribute and routes through `__mn_tensor_view` internally — the surface API doesn't change but the semantics do (writes to reshaped tensor are now visible in source). Document in CHANGELOG `### Changed` — **potentially breaking** for any user code that depended on v5.41.0's accidental-copy semantics. | 5h |
| **Ts.3.A** | HIGH | **Grammar + AST + parser for `:step`.** New lexer token (e.g., `RANGE_STEP_SEP` for the `:`); extend `range_op` rule to optionally accept `:step_expr`; add `step: Expr | None` field to `RangeExpr` and `IndexItem` AST nodes; parser constructs step-bearing nodes. Negative step is OUT OF SCOPE — reserved syntax for v6.0. Step must be an integer literal or constant expression evaluating to a positive integer; emitter checks at lower time and raises a clear error otherwise. Bootstrap copy of grammar in `bootstrap/` updated in lockstep. | 4h |
| **Ts.3.B** | HIGH | **Stepped slice on Tensor.** New runtime export `__mn_tensor_step_slice(src, axis, start, end, step) -> tensor` returning a fresh tensor with copy semantics. Lower: `t[start..end:step]` on Tensor. Step semantics: `(end - start + step - 1) / step` elements per axis; bounds-checked at runtime. **Copy not view** — stepped data is non-contiguous; supporting it as a view would require strides which is a v6.0 ABI item. | 4h |
| **Ts.4** | HIGH (gate) | **Tests.** New goldens: `97_tensor_view_aliasing.mn` (write to view visible in parent; refcount on multi-view; parent outlives all views), `98_tensor_stepped_slice.mn` (3 axes × {1, 2, 3} step combos; out-of-bounds step caught), `99_tensor_reshape_aliased.mn` (v5.41.0 copy stopgap → v5.45.0 alias swap regression test; the v5.41.0 source-unmodified-after-reshape test in golden 96 EXPECTED to flip — that's the aliasing swap; document explicitly). New pytest: `tests/llvm/test_tensor_views.py` (5 cases including drop-glue ordering: parent freed before view, view freed before parent, both held, mid-loop view drop), `tests/llvm/test_tensor_stepped_slice.py` (4 cases). ASan + valgrind sweeps on every new test. | 6h |
| **Ts.5** | MEDIUM | **Cookbook.** `docs/stdlib/tensor.md` (deferred from v5.41.0 with explicit forward link). Quick reference, type/API table, 6 cookbook recipes (reshape; view-then-mutate; stepped slice; sliding window via stepped slice; copy-vs-view discipline; refcount mental model). Aliasing semantics explicitly documented — what mutates, what doesn't, when to copy explicitly. | 3h |
| **Ts.6** | MEDIUM | **Closeout artifacts.** CLAUDE.md "Not yet on LLVM" line fully closed (drop the entire mention); SPEC.md header re-sync to v5.45.0 cut + new sync block documenting refcount addition + the v5.41.0 reshape-semantics swap; CHANGELOG `### Added` for Ts.2 + Ts.3, `### Changed` for the reshape-semantics swap (potentially breaking — flag explicitly per check_changelog_honesty); release-notes entry; Ts.2 v6.0-stopgap line removed from carry. | 1h |
| **Ts.7** | HIGH (gate) | **Strict 3-stage fixed point preservation.** Self-host mirror needed: lower.mn + emit_llvm.mn for the new ops + grammar parsing in self-host. v5.41.0 Ts.1 mirrored cleanly because the only change was a Call branch on a method dispatch; Ts.2 + Ts.3 add a new method (view), modify reshape semantics, add a new index-item form (stepped). Self-host source touches expected: ~150 LOC across `mapanare/self/lower.mn`, `mapanare/self/emit_llvm.mn`, `mapanare/self/parser.mn`, `mapanare/self/ast.mn`. **STRICT preservation is load-bearing** — if the bump-and-verify shows divergence, halt and investigate before tagging. | 6h |
| **Ts.8** | MEDIUM | **Binary-compat regression.** New `tests/runtime/test_tensor_struct_compat.py` mirroring v5.41.0 / v5.42.0 pattern: locks `sizeof(mapanare_tensor_t)` between expected pre-v5.45.0 size and v5.45.0 size + ~16 bytes; field-placement order assertions; refcount-init-to-1 invariant; `__mn_tensor_free` no-op-on-still-aliased semantics. ~120 LOC. | 2h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.44.0 HEAD clean. Confirm goldens
  96/96 + STRICT. Re-read v5.41.0 PRE_PHASE_AUDIT.md — it
  remains the structural source of truth for this release;
  v5.45.0 PLAN inherits its scope corrections. **Audit `mapanare/self/`
  for tensor-method usage** — Ts.7 self-host mirror has to know
  whether the bootstrap stage1 itself ever calls `.view()`,
  `.reshape()`, or stepped slices. Phase 0 confirms it does not
  (same precaution as v5.41.0 Ts.1 took for `.reshape()`); if it
  does, STRICT preservation requires careful mirror-edit
  ordering.
- **Phase 1** — Ts.2.A C runtime: refcount field + view flag
  + parent pointer; refcount-aware `__mn_tensor_free`. Ship
  the C side first; the existing `__mn_tensor_alloc` + reshape
  paths must keep working unchanged before any new emit
  branches land. C smoke (`/tmp/ts2a_smoke.c`) before any
  Mapanare-side edits.
- **Phase 2** — Ts.2.B view surface: `__mn_tensor_view` runtime
  helper; lower + emit branches in Python bootstrap; reshape
  aliasing swap (drop `noalias`, route through
  `__mn_tensor_view`).
- **Phase 3** — Ts.3.A grammar + AST + parser for `:step`.
  Bootstrap grammar copy synced. Add unit tests for the parser
  (range-with-step, range-without-step still works,
  range-with-non-int-step rejects cleanly).
- **Phase 4** — Ts.3.B stepped-slice runtime + lower + emit.
  Copy semantics; bounds checked.
- **Phase 5** — Ts.7 self-host mirror. lower.mn + emit_llvm.mn
  + parser.mn + ast.mn edits. Mirror-edit ordering: parser
  first (so AST nodes exist), then lower, then emit. Stage1
  rebuild after each milestone.
- **Phase 6** — Ts.4 tests. Goldens, pytest, ASan + valgrind
  sweeps.
- **Phase 7** — Ts.8 binary-compat regression. Ts.5 cookbook.
- **Phase 8** — Ts.6 closeout artifacts; bump + verify;
  fixed-point STRICT check (mandatory rebuild stage1 between
  bump and verify per v5.31.0 lesson).

---

## Out of scope

- **Strided / non-contiguous tensors.** v6.0+. Adding strides
  to `mapanare_tensor_t` is a separate ABI change with deep
  implications for every existing tensor op (broadcast, scalar,
  reduce). v5.45.0 ships shape-only views.
- **Negative step.** Reserved syntax; v6.0 candidate. Parser
  rejects negative literal step at lower time with a clear
  error.
- **Non-integer step.** Parser/lower rejects.
- **`.transpose()` / `.permute()`.** These need strides;
  v6.0+.
- **GPU `Tensor.view()`.** The stdlib `GpuTensor` (separate
  type from builtin `Tensor`) ships its own `reshape` already;
  unifying the two surfaces is a v6.0+ design conversation.
- **Borrow-check on view aliasing.** v6.0 borrow checker. The
  refcount runtime is the foundation; the static aliasing
  rules are a v6.0 PLAN input.
- **Closeout panel.** Moved to v5.47.0.

---

## Risk

1. **STRICT preservation.** Adding a new MIR shape (the
   stepped-slice indexing) and modifying an existing reshape's
   semantics both have non-trivial self-host mirror surface.
   v5.41.0 Ts.1 was clean because the new branch fired only on
   user code; Ts.2 reshape-semantics swap fires on every
   reshape including any in `stdlib/`. Mitigation: Phase 0
   audits `stdlib/` for `.reshape()` usage; if any, the
   semantic change is documented in CHANGELOG `### Changed`
   per the changelog-honesty rule.
2. **Refcount cycles.** A view can't hold a refcount on its
   own data buffer (the parent does); but parent → child view
   could in principle be made cyclic by a future `view_of(view)`
   chain. v5.45.0 design: views always hold a refcount on the
   *root* parent (single hop), not on intermediate views.
   Document and lock with a test (view-of-view → both refcount
   the original parent).
3. **ABI break for downstream.** `mapanare_tensor_t` size grows.
   No external consumer exists that we know of, but the
   project memory entry on v5.31.0's stage1-rebuild lesson
   applies: must rebuild stage1 between bump and verify.
   Mitigation: explicit checklist item; binary-compat
   regression test.
4. **v5.41.0 reshape-copy users.** If any user code relies on
   v5.41.0's copy semantics (writes to reshaped tensor not
   visible in source), v5.45.0's aliasing swap silently breaks
   them. Mitigation: CHANGELOG `### Changed` flag
   ("potentially breaking — semantic change"); cookbook
   explicitly documents copy-vs-view discipline; Phase 0
   audit grep `stdlib/` + `examples/` for reshape usage and
   note any reliance on the stopgap.
5. **PRE_PHASE_AUDIT may catch more deviations.** v5.41.0
   PRE_PHASE_AUDIT caught 4 PLAN/PROMPT premise errors at
   once. Same pattern applies here: assume Phase 0 will
   surface something. Mitigation: Phase 0 timeboxed to ~2h
   with explicit deviation-surfacing protocol; if Phase 0
   catches a structural blocker, surface to lead before
   proceeding.
6. **Goldens 96/96 disturbance.** Adding 3 goldens →
   99/99 expected. v5.41.0 reshape golden (96) flips on the
   reshape-semantics swap; the Ts.4 plan explicitly accounts
   for this.
7. **Self-host mirror parser change.** v5.41.0 / v5.42.0 /
   v5.43.0 / v5.44.0 all preserved STRICT with zero
   `mapanare/self/*.mn` source touches; v5.45.0 *requires*
   self-host mirror. STRICT preservation here is the
   structural risk. Mitigation: stage1 rebuild after each
   self-host edit; full fixed-point check at Phase 8 closeout.

---

## Success criteria

- ✅ `t.view(shape)` compiles end-to-end through Python
  bootstrap and stage1; writes to view visible in parent.
- ✅ `t.reshape(shape)` returns aliasing view (semantic swap
  from v5.41.0 stopgap); `noalias` attribute removed.
- ✅ `t[start..end:step]` parses, lowers, emits, links, runs.
  Stepped slice returns a fresh contiguous tensor (copy
  semantics).
- ✅ `mapanare_tensor_t` refcount works correctly under
  multi-view, multi-drop scenarios.
- ✅ `__mn_tensor_free` is refcount-aware; no double-free, no
  use-after-free under ASan / valgrind.
- ✅ Self-host mirror lands; STRICT 3-stage fixed point
  preserved.
- ✅ Goldens 99/99 (96 existing + 3 new).
- ✅ `docs/stdlib/tensor.md` cookbook shipped.
- ✅ CLAUDE.md "Not yet on LLVM" line removed entirely (was
  partially closed at v5.41.0).
- ✅ CHANGELOG `### Added` (Ts.2 + Ts.3) + `### Changed`
  (reshape-semantics swap) per check_changelog_honesty rule.
- ✅ SPEC.md header sync.
- ✅ Binary-compat regression test pinning struct size +
  field placement.
- ✅ `make ci-gates` GREEN; `make lint` clean.

---

## Carry-forward delta

**Closes:**
- Ts.2 + Ts.3 (option-B contract from v5.41.0 — 4-release
  carry).
- The "Not yet on LLVM: tensor reshape, mutable views,
  stepped slices" line in CLAUDE.md (Ts.1 closed half at
  v5.41.0; v5.45.0 closes the rest).
- v5.41.0's reshape-copy stopgap (the `noalias` attribute on
  `__mn_tensor_reshape` drops here).
- Tensor cookbook deferral from v5.41.0.

**Inherits to v5.46.0:**
- Three v5.43.0 lowerer bugs (`Result<T, complex Err>`
  destructure + variant rewrap + nested 15-arm match) —
  unchanged from v5.43.0 carry; v5.46.0's whole release.

**Inherits to v5.47.0:**
- End-of-v5 closeout panel (moved from v5.45.0 → v5.47.0
  to make room for Ts.2/Ts.3 + the lowerer-bug closeout).

**Inherits to v6.0 or later:**
- Strided / non-contiguous tensors (negative step, transpose,
  permute).
- Borrow-check on view aliasing (the static rules layered on
  top of the v5.45.0 refcount runtime).
- Unifying builtin `Tensor` with stdlib `GpuTensor` surface.
- Hard removal of `{}` (carry from v5.19.0).

**Aggregate state entering v5.46.0:**
- Tensor closeout arc CLOSED at v5.45.0.
- Manifesto arc CLOSED (since v5.43.0).
- Package-system runway CLOSED (since v5.44.0).
- Three v5.43.0 lowerer bugs remain MEDIUM — load-bearing for
  v5.46.0; escalates to HIGH if not landed.
- macOS notarization MEDIUM carry (from v5.33.0 Nu.2).
- Strict 3-stage fixed point preserved at v5.45.0's expected
  ~242k+ lines.
