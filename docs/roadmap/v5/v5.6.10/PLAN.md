# Mapanare v5.6.10 — "Self-host hardening — Ve.2 residuals + struct_byte_size + culebra baseline"

> **Post-Ve.3 cleanup release.** With v5.6.9's fixed-point restored,
> close the residual hardening items the v5.6.5–v5.6.9 arc left
> in place: the 18 × 384-byte list-floor fallback sites (Ve.2
> residuals), the v5.6.8 struct_byte_size patch (re-evaluated now
> that Ve.3 is closed), and establish a clean culebra baseline so
> v5.7.0+ work has a known-good comparison anchor.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.9 shipped (Ve.3 closed; non-empty stage3.ll;
strict-or-near fixed-point holds).
**Estimated work:** 1 session (~2–3 hours).
**Owner dockets:** Ve.2 residuals (opened v5.6.7) + ABI sizing
hardening (deferred from v5.6.8).

---

## Why this release exists

### Three hardening items left in place

1. **Ve.2 residuals — 18 × 384-byte list-floor sites.**
   `__mn_list_new(i64 384)` hardcoded fallback drops from 387 →
   18 sites in v5.6.7's `lower_let_list_hint` work. The 18
   residuals come from empty-list literals in contexts that don't
   route through `lower_let`:
   - Struct field defaults (`new Foo { items: [] }`)
   - Call arguments (`f([])`)
   - Return expressions (`return []`)
   - Map values (`{ k: [] }`)

   These are SAFE (the floor over-allocates, never under) but
   wasteful — 384 bytes per list × repeated emission across
   hundreds of sites bloats the runtime memory footprint.

2. **struct_byte_size patch from v5.6.8.**
   v5.6.8's investigation surfaced that `struct_byte_size`
   undercounts named structs at 8 bytes (true 80 for Value)
   because:
   - `register_internal_struct` pushes stub entries with
     `llvm_type="%struct.X"` that the forward search finds first.
   - `llvm_aggregate_size` counts ALL commas including those
     inside nested aggregates.

   The patch (delegate to `llvm_sizeof_st` which uses the
   v5.6.5 stub-skip in `lookup_struct_field_types`) was
   empirically tested and DID NOT close Ve.3. v5.6.8 reverted it
   to keep the v5.6.9+ debugging surface clean.

   **Now that Ve.3 is closed**, the patch becomes a hardening
   candidate: it gives correct sret/byref classification for
   downstream releases and aligns with Python's emitter behavior.
   The 7% stage2.ll growth is acceptable IF goldens / sanitizers
   stay green and the IR remains llvm-as clean.

   **Decision in v5.6.10**: re-apply the patch and verify it's
   benign in the post-Ve.3 world. If it surfaces a new bug, defer
   again with documented evidence. If it's clean, ship.

3. **Culebra baseline for v5.7.0+.**
   v5.6.9 establishes the first culebra baseline with a working
   fixed-point. v5.6.10 freezes that baseline as the v5.7.0 entry
   point — every v5.7.x release compares against it.

### Why bundle these three

All three are SAFE-by-default work (no Ve.3-class blast radius)
that builds on the v5.6.9 fixed-point foundation. Splitting into
three releases would burn version slots without per-release user
value. Bundling here lets v5.7.0 start from a clean
hardened-but-functional state.

---

## Scope

### What ships

#### 9.10a — Ve.2 residuals: thread elem_ty hint through non-`let` lowerer paths

The 18 sites are reached via four lowerer entry points that don't
currently propagate the type annotation. Identify and patch each:

```bash
# Find call sites still emitting __mn_list_new(i64 384):
grep -n "__mn_list_new(i64 384)" /tmp/stage2.ll | wc -l    # expect 18
grep -B 5 "__mn_list_new(i64 384)" /tmp/stage2.ll \
    | head -50
```

Group by upstream context. Suspected lowerer functions:

| Path | Mapanare construct | File:line |
|---|---|---|
| `lower_struct_init` | struct field default | `lower.mn:???` |
| `lower_call_args` | empty-list call arg | `lower.mn:???` |
| `lower_return` | `return []` | `lower.mn:???` |
| `lower_map_init` | map value | `lower.mn:???` |

For each: thread the EXPECTED elem_ty from the caller's type
context (struct field types from registered structs, function
param types from `find_function`, return type from
`current_fn.return_type`). Same pattern as v5.6.7's
`lower_let_list_hint` + `extract_list_elem_ty`.

After fix, the list floor at `emit_list_init`'s hybrid path can
be REMOVED entirely:

```mn
fn emit_list_init(...) {
    if elem_ty.kind != TK_UNKNOWN() {
        // GEP-trick path
    }
    // OLD: 384-byte floor
    // NEW: error — no elem_ty hint propagated
}
```

#### 9.10b — Re-apply v5.6.8 struct_byte_size patch

Patch (one-liner):

```mn
fn struct_byte_size(st: EmitState, ty: String) -> Int {
    // v5.6.10 — delegate to llvm_sizeof_st for correct recursive sizing.
    return llvm_sizeof_st(st, ty)
}
```

Validate:
1. Goldens 64/66 preserved.
2. `verify_fixed_point.sh` continues to hold STRICT/NEAR.
3. Full sanitizer sweep clean (no NEW findings vs v5.6.9).
4. stage2.ll growth ≤ 8% vs v5.6.9 (the 7% from v5.6.8's test
   plus a small variance budget for Ve.2 residual closures).
5. `llvm-as` clean.

If any check fails, REVERT the patch and document why. Don't
bundle a partial sret/byref change.

#### 9.10c — Establish v5.6.10 culebra baseline

```bash
mkdir -p docs/roadmap/v5/v5.6.10/culebra
culebra summary /tmp/stage2.ll \
    > docs/roadmap/v5/v5.6.10/culebra/summary.md
culebra triage /tmp/stage2.ll \
    > docs/roadmap/v5/v5.6.10/culebra/triage.md
culebra baseline save /tmp/stage2.ll \
    -o docs/roadmap/v5/v5.6.10/culebra/baseline-end.json
culebra baseline diff /tmp/stage2.ll \
    -b docs/roadmap/v5/v5.6.9/culebra/baseline-end.json \
    > docs/roadmap/v5/v5.6.10/culebra/baseline-delta-from-v5.6.9.md
```

The delta should show:
- `__mn_list_new(i64 384)` count: 18 → 0 (Ve.2 closed)
- Sret/byref counts: per-function changes from struct_byte_size
- No new critical findings.

#### 9.10d — Update PARITY_GAPS.md

Move:
- Ve.2 residuals → Historical (closed v5.6.10)
- Self-hosting fixed-point restored → Historical (closed v5.6.9
  carry-forward)
- ABI sizing hardening → Historical (closed v5.6.10)

### What does NOT ship

- **Multi-level walk for Rt.04**. v6.0 borrow-checker scope.
- **Sh.7 / B closure work**. v5.7.0.
- **noalias-on-byref** (if v5.6.9 didn't ship it). Tracked
  separately — adding noalias to byref params is a hint that
  may surface latent aliasing bugs; ship only when
  empirically tested.
- **New features.** v5.6.x is closeout; v5.7.x is feature work.

---

## Exit criteria

1. `__mn_list_new(i64 384)` count in stage2.ll: **0** (was 18 at
   v5.6.9).
2. `verify_fixed_point.sh --keep` STRICT or NEAR.
3. `culebra fixedpoint` confirms cycle.
4. `struct_byte_size` returns correct sizes for all internal
   structs (Value→80, MIRType→64, EmitState→752, etc.).
5. Harness 64/66 preserved.
6. stage2.ll growth ≤ 8% vs v5.6.9.
7. Valgrind sweep 0 new ERRORS.
8. ASan UAF sweep 0 new findings.
9. LSan baseline unchanged (62_list_output remains baseline-gated).
10. Non-bootstrap pytest 0 failures.
11. `make lint` clean.
12. `check_struct_registry.py` 23/23/91 clean.
13. `culebra triage --brief` reports no NEW critical findings
    vs the v5.6.9 baseline.
14. `docs/roadmap/v5/v5.6.10/culebra-journal.jsonl` populated.
15. `docs/roadmap/v5/PARITY_GAPS.md` Ve.2 residuals + sizing
    hardening flipped to Historical.

---

## Design decisions

### D1 — One bundled release for closeout hardening

Three items, all SAFE-class, all build on v5.6.9. Bundling avoids
version-slot churn and gives v5.7.0 a single hardened entry point.

### D2 — struct_byte_size patch is gated on green sanitizers

Re-applying the patch is contingent on full sanitizer + golden +
fixed-point gates passing. v5.6.8 documented that the patch's
7% IR growth surfaced no new ASan / valgrind findings BUT didn't
close Ve.3. With Ve.3 closed in v5.6.9, the same green gates
still apply — if they hold, the patch ships; if not, defer.

### D3 — Floor removal is the goal, not just lowering count

After 9.10a, `emit_list_init`'s 384-byte floor branch should be
DEAD code. Remove it explicitly to prevent regression. The
hybrid path becomes: GEP-trick for known elem_ty, ERROR for
TK_UNKNOWN (with a clear diagnostic).

### D4 — Baseline freeze is the v5.7.0 anchor

v5.7.0 will introduce closure-typed + or-pattern work. Some of
that work touches `lower.mn` (closure capture resolution) and
`semantic.mn` (or-pattern check). Having a v5.6.10 culebra
baseline lets v5.7.0 detect any regression in IR shape immediately.

### D5 — Culebra-driven validation throughout

Every step has a culebra check at the end:
- `culebra triage` after each patch
- `culebra baseline diff` against v5.6.9
- `culebra fixedpoint` for the round-trip
- `culebra journal add` for every milestone

---

## Risks

- **R1 — Ve.2 residual sites are deeper than expected.** Some
  empty-list literals may need MIR-level type inference (not
  just AST-level threading). Mitigation: scope each of the 4
  paths individually; ship what closes cleanly, document the
  rest as v5.6.11 if they need infra.
- **R2 — struct_byte_size patch surfaces a NEW bug post-Ve.3.**
  v5.6.8 saw the 7% IR growth not close Ve.3, but didn't test
  what the larger IR did to the OTHER ~500 functions. Mitigation:
  full sanitizer gate; revert if any new finding.
- **R3 — Floor removal breaks a corner case.** Some lowerer path
  may genuinely lack a type hint. Mitigation: phase the change —
  first lower the count to 0, THEN remove the floor branch in a
  separate patch within v5.6.10.
- **R4 — Culebra finds a HIGH/CRITICAL on the v5.6.10 baseline
  that v5.6.9 missed.** Possible if the v5.6.10 patches surface
  a new template match. Mitigation: triage first; if finding is
  not Ve.3-equivalent, document as v5.7.x scope.

---

## What NOT to do

- Do not bundle Sh.7 / B closure work. That's v5.7.0.
- Do not ship the struct_byte_size patch if any sanitizer regresses.
  v5.6.8 already showed that a patch with 7% IR growth without
  observable benefit is a regression risk.
- Do not skip the fixed-point validation after each patch. v5.6.10
  builds on v5.6.9's fixed-point foundation; verify it still holds
  after each step.
- Do not remove the 384-byte floor in the same patch that lowers
  the count to 0. Phase: count→0 first, then dead-code removal.
- Do not commit `/tmp/*` artifacts. Diagnostic outputs go in
  `docs/roadmap/v5/v5.6.10/culebra/`.
