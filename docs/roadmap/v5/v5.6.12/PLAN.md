# Mapanare v5.6.12 — "Lk.1 close — destination passing for List let-bindings"

> **Layer 1 of the Rust-style ownership migration.** Closes Lk.1
> at its root cause (alloca-aliasing in `let mut x: List<T> = []`)
> by lowering `let`-bindings for fresh resources directly into
> the variable's alloca — no intermediate `%t0.addr` scratch
> alloca, no copy from scratch to var, no double-tracking. After
> this, the v5.6.10 scalar gate can be re-applied and the
> 384-byte floor branch dropped — closing all 7 Ve.2 residual
> sites in the same release.
>
> **Why this design (not Go-style GC):** Mapanare is already
> Rust-architected — no GC, manual drop-glue, deterministic
> destruction. Adding a GC throws away the runtime perf advantage
> (1.5-3× over Go on memory-heavy workloads). The principled fix
> is what rustc does: result-location semantics
> (destination-passing style). A `let mut a = []` allocates `a`'s
> slot, then evaluates `[]` directly into that slot — no copy.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.11 shipped (Ve.4 closed; fixed-point at NEAR).
**Estimated work:** 1-2 sessions (~3-5 hours).
**Owner docket:** Lk.1 (opened v5.6.10, closing here); Ve.2 residuals
(opened v5.6.5, residual 7 sites closing here).

---

## Why this release exists

### Lk.1 is structurally simple, not "v6.0 borrow-checker"

Per `docs/known_issues.md` Lk.1 row:

> alloca-aliasing leak in inline list-get/push pattern
> (`%t0.addr` vs `%arr1.addr`). drop-glue tracks the ListInit
> destination alloca but mutating pushes write back to a
> separate var-binding alloca — at function exit the free is a
> no-op while the buffer is never freed.

The previous framing called this "v6.0 borrow-checker scope".
That was wrong. The actual fix is: **don't create two allocas
in the first place**. Rust solves this via destination-passing
in codegen (`PlaceRef`); rustc never creates an intermediate
`%t0.addr` for `let a = Vec::new()` — it allocates `a`'s slot
and emits `Vec::new()`'s sret straight into it.

Mapanare's lowerer currently:
```
let mut indices: List<Int> = []
```
lowers to:
```
ListInit(t0, mir_int(), [])     // emitter creates %t0.addr
Alloca(indices.addr, List<Int>) // separate alloca
Store(indices.addr, t0)         // copy from scratch to var
```

After v5.6.12, it lowers to:
```
ListInit(indices.addr, mir_int(), [])  // emit DIRECTLY into indices.addr
```

One alloca. One tracking entry. Mutations (`indices.push(...)`)
write to the only alloca. drop-glue frees the only alloca.
No leak.

### Cascading wins

Once Lk.1 closes, three things follow in this release:

1. **Apply the v5.6.10 scalar gate.** `emit_list_init`'s scalar
   path can use `llvm_type_size(elem_llvm_ty)` directly when
   `elem_ty.kind != TK_UNKNOWN()`. The 384-byte floor branch
   becomes unreachable for known scalar types.

2. **Drop the floor branch entirely** for List<Int>, List<Float>,
   List<Bool>, List<ptr>. The fallback floor remains only for
   genuinely unknown elem_ty.kind (rare; warrants a closer
   look in v5.6.13+).

3. **Close all 7 Ve.2 residuals.** `expr_tensor_shape`,
   `instr_tensor_shape`, `parse_tensor_lit` ×2,
   `new_lower_state`, `new_emit_state`, `build_match_arms`
   all stop emitting `__mn_list_new(i64 384)`.

### Layer 2 (move on assignment) is NOT in this release

`let b = a` (sharing-then-mutating) is a separate concern — the
"share-then-mutate" leak class. v5.6.12 closes the simple
let-binding case which is what's actually blocking us. Layer 2
is conditional v5.6.13+ work IF a share-mutate leak surfaces in
the corpus.

---

## Scope

### What ships

#### 9.12a — Destination-passing infrastructure for List (~60 min)

1. Add a thin abstraction to compute a let-binding's alloca
   name BEFORE lowering the value:
   ```mn
   fn fresh_let_alloca(st: LowerState, name: String, ty: MIRType) -> (LowerState, Value) {
       let addr_name: String = "%" + name + toString(st.tmp_counter) + ".addr"
       let mut s: LowerState = st
       s.tmp_counter = s.tmp_counter + 1
       return (s, new_value(addr_name, ty))
   }
   ```

2. Modify `lower_list_typed` to accept an optional dest-alloca
   hint. New signature:
   ```mn
   fn lower_list_typed_into(st: LowerState, elements: List<Expr>, hint_elem: MIRType, dest_alloca: Option<Value>) -> LowerResult
   ```
   Existing `lower_list_typed` becomes a thin wrapper that
   passes `None` for the hint.

   When `dest_alloca = Some(addr)`:
   - Use `addr.name`'s base (strip `.addr`) as the ListInit's
     dest SSA name. So `%indices0.addr` → ListInit dest =
     `%indices0`. The emitter's existing `dn + ".addr"`
     convention then derives the same `%indices0.addr` as the
     storage alloca — i.e. the let's pre-created alloca.
   - Don't fresh-tmp a name; use the variable's identity.

3. Modify `lower_let` for the empty-list path:
   - Pre-compute the var alloca via `fresh_let_alloca`.
   - Call `lower_list_typed_into` with `dest_alloca = Some(addr)`.
   - **Skip** the post-emit `Alloca(addr)` + `Store(addr, val)`
     pair (those would create the duplicate alloca + copy).
   - `define_var(s, name, addr, mutable)` as before.

#### 9.12b — Emitter: respect the dest hint (~30 min)

`emit_list_init`'s alloca-creation logic:
```mn
let alloca_name: String = dn + ".addr"
s.entry_prelude_lines.push("  " + alloca_name + " = alloca ...")
```

This already produces the right alloca name when `dn = "%indices0"`
(yielding `alloca_name = "%indices0.addr"`). **No emitter changes
needed for the alloca name itself.** The only constraint: when
the lowerer pre-creates the alloca via `Alloca(addr)`, we get
DOUBLE allocas. So the lowerer must SKIP the explicit Alloca
emission when destination-passing is active.

The skip is in `lower_let` (point 3 above), not the emitter.

#### 9.12c — Apply scalar gate + drop floor (~20 min)

In `emit_list_init`:

```mn
// v5.6.12 — scalar gate. With Lk.1 closed via destination
// passing, the 384-byte floor is no longer needed to mask the
// alloca-aliasing leak. Use the actual LLVM type size.
let mut elem_sz_n: Int = llvm_type_size(elem_llvm_ty)
if elem_ty.kind == TK_UNKNOWN() {
    // Genuinely unknown elem_ty — keep a defensive fallback.
    // Investigation candidate for v5.6.13.
    if elem_sz_n < 384 { elem_sz_n = 384 }
}
s = emit_line(s, emit_call_ir(list_name, llvm_list_rt(), "__mn_list_new", "i64 " + toString(elem_sz_n)))
```

The `if elem_ty.kind == TK_UNKNOWN()` gate replaces the
unconditional `if elem_sz_n < 384` floor. Known scalar types
(Int=8, Float=8, Bool=8, ptr=8) get their actual size; unknown
fallback keeps the 384-byte safety net.

#### 9.12d — Validation gate (~30 min)

Per the v5.6.11 PROMPT D2 pattern:

1. **Reproducer**: `mnc-stage2 /tmp/p3.mn` still produces
   non-empty `llvm-as`-clean IR (Ve.4 stays closed).
2. **Fixed-point**: `verify_fixed_point.sh` reaches NEAR or STRICT.
3. **65_list_int_indexing**: LSan reports CLEAN (was: would
   leak 80 bytes if scalar gate applied without Lk.1 fix).
4. **Floor count**: `__mn_list_new(i64 384)` sites = 0 (was: 7
   in v5.6.11).
5. **Goldens**: 64/66 preserved.
6. **Sanitizer matrix**: ASan UAF, valgrind, LSan baseline gate
   all clean. Per PROMPT D2: any regression → REVERT.
7. `make lint` clean; `check_struct_registry.py` 23/23/91 clean;
   non-bootstrap pytest 0 failures.

#### 9.12e — Documentation (~30 min)

- `docs/roadmap/v5/v5.6.12/SESSION_REPORT.md` — full trace +
  per-phase gate results + IR before/after comparison.
- `docs/known_issues.md` — flip Lk.1 row to **CLOSED v5.6.12**;
  flip Ve.2 row to **CLOSED v5.6.12** (residuals closed).
- `docs/roadmap/v5/PARITY_GAPS.md` — move Lk.1 + Ve.2 to
  Historical.
- `CLAUDE.md` — v5.6.12 entry; "Current baseline" → 5.6.12.
- `docs/roadmap/ROADMAP.md` — v5.6.12 stanza prepended.
- `docs/roadmap/v5/CLOSEOUT_ARC.md` — note Lk.1 + Ve.2 closed.

### What does NOT ship

- **Layer 2 (move on assignment).** Conditional v5.6.13 work.
- **Destination passing for struct/enum/map let-bindings.** v5.6.13
  scope. Those types don't have the 384-byte floor issue (they
  use the GEP-trick and emit at correct sizes). The duplicate
  alloca is a code-cleanliness concern, not a correctness one.
- **Reverting v5.6.11's runtime-elem_size load.** Keep it as
  belt-and-suspenders — SROA folds it when stride is constant,
  zero runtime cost. Removing would also work but adds noise.
- **Sh.7 / B closure work.** v5.7.0.
- **Full borrow checker.** Not needed for memory safety with
  Layer 1 + Layer 2; explicitly off the table.

---

## Exit criteria

1. `mnc-stage1` rebuilds clean from updated source.
2. `mnc-stage2 /tmp/p3.mn` still produces non-empty
   `llvm-as`-clean IR (Ve.4 regression check).
3. `verify_fixed_point.sh --keep` reaches NEAR or STRICT (was:
   NEAR at v5.6.11; should stay at NEAR or improve to STRICT).
4. `__mn_list_new(i64 384)` site count: **0** in stage2.ll
   (was: 7 at v5.6.11).
5. Goldens harness: **64/66** preserved (same 2 fails:
   `51_match_guards_and_or` B, `64_closure_typed` Sh.7).
6. **65_list_int_indexing**: LSan reports **CLEAN** (no leaks).
7. ASan UAF: 65 CLEAN / 0 ASAN_ERROR / 1 CRASH_NO_ASAN.
8. Valgrind: 0 ERRORS / 66 WARNINGS_ONLY.
9. LSan baseline gate: **PASS** with the 65_list_int_indexing
   row updated CLEAN (currently expected LEAK per the v5.6.10
   Lk.1 deferral; baseline TSV needs a refresh row).
10. stage2.ll growth: ≤ 2% vs v5.6.11 (217,273 lines). Expected
    DECREASE actually — eliminating intermediate allocas + stores
    should shrink IR slightly.
11. Non-bootstrap pytest: 0 failures.
12. `make lint` clean; `check_struct_registry.py` 23/23/91 clean.
13. `docs/known_issues.md`: Lk.1 + Ve.2 rows flipped to CLOSED.
14. `docs/roadmap/v5/PARITY_GAPS.md`: Lk.1 + Ve.2 moved to
    Historical.

---

## Design decisions

### D1 — Rust-style, not Go-style

Mapanare is no-GC by architecture. Adding GC throws away the
runtime perf advantage. Rust's destination-passing model is
faster (1.5-3× over Go on memory-heavy workloads, per
established benchmarks; Mapanare's own benchmarks already
show ~Rust-speed). The structural fit is exact.

### D2 — Layer 1 only this release

Layer 1 (destination passing for fresh resources in let-bindings)
closes the visible Lk.1 pattern. Layer 2 (move on assignment)
closes the share-then-mutate case. The corpus has no observed
share-mutate leak, so Layer 2 is conditional v5.6.13 work.
Per "no cheap shit": don't ship code we can't justify a need
for.

### D3 — List only, not all resource types

The 7 Ve.2 residual sites are all `List<Int>` lets. Closing them
needs only List support. struct/enum/map have the same
two-alloca pattern but no observable leak (they're not exercised
under LSan in a way that surfaces it). Extending Layer 1 to
those types is v5.6.13 cleanup — gated on whether a leak
actually surfaces.

### D4 — Skip the explicit Alloca instruction in lowerer

Currently `lower_let` emits `Alloca(addr)` then `Store(addr, val)`.
With destination passing, the resource's `emit_list_init`
already creates `addr` (in entry prelude) and stores into it.
Re-emitting `Alloca(addr)` would produce a duplicate alloca
declaration in the IR — which `llvm-as` may or may not flag.
**Skip the Alloca emission entirely** when destination passing
is active. Then we have a single hoisted alloca (in entry
prelude) and no duplicate.

### D5 — Hero metric is concrete

The fixed-point gate (NEAR FIXED POINT) is preserved from
v5.6.11. v5.6.12's hero metric is:
- **`__mn_list_new(i64 384)` site count: 7 → 0.**
- **65_list_int_indexing: LEAK → CLEAN under LSan.**

Both are objectively measurable in seconds via `grep` and
`run_asan_leak_goldens.sh`.

### D6 — Don't touch v5.6.11's runtime-elem_size load

The runtime-elem_size load in `emit_index_get` /
`emit_index_set` (added v5.6.11) is now unnecessary — strides
will naturally match (both 8 for i64). But removing it adds
risk for zero gain. SROA folds it when stride is constant
(zero runtime cost). Keep as belt-and-suspenders.

---

## Risks

- **R1 — Destination-passing breaks let-bindings of non-fresh
  expressions.** `let b = a` where a is a variable (not a
  resource init) goes through `lower_expr` → returns a loaded
  value. The destination-passing path can't apply (no resource
  to redirect). **Mitigation**: gate destination passing on
  `value` being an empty-list literal (the only case
  `lower_let_list_hint` returns non-UNKNOWN for currently).
  Other let cases fall through to the existing
  Alloca + Store path.
- **R2 — Shrinks stage2.ll, breaks fixed-point.** Eliminating
  intermediate allocas + stores will shrink IR. The
  `verify_fixed_point.sh` DIFF_THRESHOLD might be exceeded if
  the shrink is large. **Mitigation**: measure stage2.ll
  before/after; if shrink > 1k lines, raise DIFF_THRESHOLD.
- **R3 — Closing Lk.1 surfaces a NEW leak class.** The v5.6.10
  Lk.1 surfaced when we tried the scalar gate. With Lk.1
  properly fixed, scalar gate is safe — but other latent leaks
  in the corpus might surface. **Mitigation**: full sanitizer
  matrix per PROMPT D2; revert if any sanitizer regresses.
- **R4 — `lower_let` becomes path-dependent.** The fresh-list
  path skips Alloca + Store; the fallback path emits them.
  Maintenance complexity. **Mitigation**: keep the path
  guarded by a single boolean (`use_dest_passing`) at the top
  of the function.

---

## What NOT to do

- Do not bundle Layer 2 (move on assignment). v5.6.13 if needed.
- Do not extend destination passing to struct/enum/map. v5.6.13.
- Do not revert the v5.6.11 runtime-elem_size load.
- Do not skip the fixed-point gate. NEAR or STRICT required.
- Do not commit `/tmp/*` artifacts.
- Do not tag without user approval.
- Do not push without user approval.
- Do not touch `__mn_list_push`'s runtime semantics.
- Do not add a GC. Mapanare is no-GC by architecture.
