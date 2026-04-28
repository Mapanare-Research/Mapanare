# Mapanare v5.6.6 — "Rt.04 Close — %struct.* guard-lift with size gate"

> **Re-lift the `%struct.*` aggregate-return guard that v5.4.4
> reverted, gated on struct-size and function-slot heuristics so the
> walk fires for small data structs (62_list_output's 2-field `St`)
> but skips the 24-field `EmitState` that returns from 77 fns in
> self-hosted code.** Closes the last known Mapanare-side leak
> (62_list_output: 9 objs / 141 B).

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.5 shipped (Ve.1 closed; `verify_fixed_point.sh`
produces non-empty stage3.ll so we can actually validate that the
walk re-lift doesn't break self-compile).
**Estimated work:** ~1 session (2–3 hours). The infrastructure from
v5.4.4 is already present in `emit_drop_glue`'s struct-field walk
branch (unreachable because the guard bails early); the work is
mostly: add the gate, tune thresholds, validate.
**Owner docket:** Rt.04 (opened v5.4.4; infra landed v5.4.4;
re-lift deferred to v5.4.5+; lands v5.6.6)

---

## Why this release exists

### The last real leak

After v5.6.4's Rt.06 closure, the LSan sweep reports 3 LEAK entries:

| Golden | Leak | Source | Class |
|---|---:|---|---|
| `39_gpu_detect` | 5 / 50212 B | libcuda + libvulkan external | Rt.02 (third-party) |
| `40_gpu_tensor` | 5 / 50212 B | same | Rt.02 |
| `62_list_output` | 9 / 141 B | `__mn_alloc` (intermediate String concat returned via struct) | **Rt.04 (our code)** |

`39` / `40` are in external GPU driver state — no Mapanare code in
the stack traces. Baseline-gated and not actionable.

`62_list_output` is the only remaining leak in **our** code. After
v5.6.6, `make leak-check` will gate on zero Mapanare-side leaks.

### The v5.4.4 history

v5.4.4 Phase 3 implemented the fix: `ret_ty_is_aggregate` flipped to
return `false` for `%struct.*`, and `emit_drop_glue` grew a
one-level struct-field walk that extracts String / List / ptr
fields via `extractvalue` and pushes them into the matching ret-ptr
list. 62_list_output transitioned LEAK → CLEAN on the golden corpus.

**But on self-compilation:**

| Metric | Pre-v5.4.4 | v5.4.4 Phase 3 |
|---|---|---|
| stage2.ll | 124k lines | **620k lines** (5× growth) |
| stage3.ll | non-empty, teardown crash | **0 lines, mnc-stage2 segfault** |

The walk emitted ~40 extractvalue lines per call site that returned
`%struct.EmitState` (22 fields). `emit_mir_call` alone has hundreds
of such sites. The expansion broke `mnc-stage2` runtime.

v5.4.4 Phase 5 RESCOPE reverted the scope (guard stays closed,
infrastructure stays); the next session's plan was to re-lift with
a size gate. That next session is v5.6.6.

### The size gate

Two heuristics, both conservative:

**H1 — struct-size gate:** walk only if the struct has ≤ N fields.
- 62_list_output's `St` = **2 fields** → walk ✓
- EmitState = **24 fields** (post-v5.6.4) → skip ✓
- Most user-defined structs have ≤ 8 fields → walk
- Pick N = 8. Conservative; closes the 62 leak; skips the one known
  problematic shape.

**H2 — function-slot gate:** walk only if the calling fn has ≤ M
tracked ownership slots. (Tracked slots include `str_owned`,
`list_owned`, `boxed_owned`, `tensor_owned`.)
- 62_list_output's `emit_line` + `add_decl` have few slots → walk ✓
- `emit_mir_*` fns in self-hosted have many slots → skip ✓
- Pick M = 50. EmitState-heavy fns typically have hundreds of
  tracked slots (every inner call that returns a String stacks one).

The guard becomes:

```mn
fn ret_ty_is_aggregate(st: EmitState, ret_ty: String) -> Bool {
    if ret_ty.starts_with("%enum.") { return true }
    if ret_ty.starts_with("{") && ret_ty != llvm_string() && ret_ty != llvm_list_rt() {
        return true
    }
    if ret_ty.starts_with("%struct.") {
        // v5.6.6 size gate: walk only for small structs in
        // small-slot functions.
        let sname: String = ret_ty.substr(8, len(ret_ty) - 8)
        let sopt: Option<StructEntry> = find_struct_entry(st, sname)
        match sopt {
            Some(sent) => {
                let nf: Int = len(sent.field_types)
                if nf > 8 { return true }  // too many fields
                let nslots: Int = len(st.str_owned) + len(st.list_owned) + len(st.boxed_owned) + len(st.tensor_owned)
                if nslots > 50 { return true }  // too many tracked slots
                return false  // walk
            },
            _ => { return true }  // unknown struct — conservative
        }
    }
    return false
}
```

Signature change from `(ret_ty: String) -> Bool` to
`(st: EmitState, ret_ty: String) -> Bool`. One caller (the `if
ret_ty_is_aggregate(ret_ty)` at `emit_drop_glue:4519` or near).

---

## Scope

### What ships

#### 9.6a — Signature extension for `ret_ty_is_aggregate`

Thread `st: EmitState` through the call chain. Only one call site
currently uses the helper; the change is surgical.

**Before:**
```mn
fn ret_ty_is_aggregate(ret_ty: String) -> Bool { ... }
...
if ret_ty_is_aggregate(ret_ty) { return st }
```

**After:**
```mn
fn ret_ty_is_aggregate(st: EmitState, ret_ty: String) -> Bool { ... }
...
if ret_ty_is_aggregate(st, ret_ty) { return st }
```

#### 9.6b — Implement the size gate

Replace the simple `starts_with("%struct.")` → `true` arm with:

- struct-lookup via `find_struct_entry(st, sname)` — helper exists
  (used elsewhere in `emit_drop_glue`).
- field-count check: `len(sent.field_types) > 8 → return true`
- slot-count check: `sum(len(st.*_owned)) > 50 → return true`
- Unknown struct (lookup miss): conservative `return true`.
- Otherwise: `return false` — field walk fires.

Constants 8 and 50 chosen empirically from v5.4.4's post-mortem:

- EmitState (24 fields → trips field gate)
- Hot emit functions (100+ tracked String slots → trips slot gate)
- Typical user structs (≤ 8 fields, small functions)

If the stage2.ll growth exceeds 3% at these defaults, **tighten**
the gate (e.g., N = 6, M = 30). If 62_list_output still leaks at
the tight gate, the `St` struct specifically has `lines:
List<String>` + `n: Int` = 2 fields; it should pass any gate above
2.

#### 9.6c — Re-enable field walk

The existing struct-field walk code in `emit_drop_glue` (around
line 4530–4565, inside the `if ret_ty.starts_with("%struct.")`
block) is correct and already wired to push into
`ret_str_ptrs` / `ret_list_ptrs` / `ret_box_ptrs`. Since v5.6.4,
the dual-push to `ret_tensor_ptrs` also applies.

When the gate opens, the walk should fire without further code
changes.

#### 9.6d — Baseline refresh

After the fix:

- 62_list_output should transition to CLEAN.
- Baseline TSV at
  `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` flips
  `62_list_output` row from `9 141 __mn_alloc LEAK` → `0 0 -
  CLEAN`.
- `docs/roadmap/v5/v5.6.6/asan-leak-summary-post-fix.tsv` —
  snapshot of the run.
- `scripts/check_leak_summary.py` gates any future regression.

### What does NOT ship

- **Multi-level struct walks.** A nested struct (struct-of-struct)
  with strings still leaks. v5.7.x scope or v6.0 borrow checker.
- **Adaptive gate tuning.** Constants 8 and 50 stay hardcoded; no
  runtime-learning.
- **Python emitter changes.** Python already has the walk (never
  reverted); self-hosted only.
- **Fix for 39/40 GPU leaks.** External driver state;
  orthogonal.
- **Move-on-assign semantics.** v6.0.
- **Change the existing 4-helper drop-glue dispatch.** Just extend
  the guard.

---

## Exit criteria

1. `62_list_output` under LSan: **0 objs / 0 B**.
2. Baseline TSV `62_list_output` row → CLEAN.
3. `check_leak_summary.py` PASSES.
4. stage2.ll line-count growth vs v5.6.5 < **3%**. (If growth is
   higher, tighten the gate and re-measure.)
5. stage3.ll non-empty (Ve.1 stays closed from v5.6.5).
6. Harness 64/66 preserved.
7. Valgrind sweep 0 new ERRORS.
8. ASan UAF sweep 0 new findings.
9. Non-bootstrap pytest 0 failures.
10. `make lint` clean.
11. `check_struct_registry.py` clean (no new structs; helper
    signature change doesn't affect the registry).
12. `docs/known_issues.md` Rt.04 row flipped to **CLOSED v5.6.6**.

---

## Design decisions

### D1 — Gate by size + slots, not by name

A name-based blocklist (e.g., "skip `%struct.EmitState` specifically")
would be brittle — as `EmitState` grows or shrinks, the gate
stops making sense. Structural gates (field count, slot count)
scale automatically.

### D2 — Hardcoded constants over tunables

Two constants (N = 8, M = 50) are enough. Exposing them as env vars
or flags invites cargo-culting. If they need tuning later, a
one-line edit in `ret_ty_is_aggregate` is cheaper than a config
surface.

### D3 — Conservative on unknown struct

If `find_struct_entry(st, sname)` returns `None`, the walk would
operate on an unknown layout — safer to skip. Over-approximation
leaks (the whole struct skips), but never corrupts.

### D4 — Why 8 and 50 specifically

- `8 fields` — covers every golden struct in the corpus;
  excludes EmitState (24); excludes a handful of large
  self-hosted types (LowerState, MIRModule) that would trigger
  the same explosion.
- `50 slots` — most emit_mir_* functions have 100s of tracked
  slots; most user functions have <50. The threshold is an
  order-of-magnitude cut, not a precise measurement.

### D5 — Why not fix EmitState's shape instead

Refactoring EmitState to be smaller would reduce the per-call-site
walk expansion, but:
- EmitState's 24 fields are semantically meaningful (each tracks
  a real piece of state).
- Shrinking would ripple through every EmitState constructor,
  accessor, and field list.
- The gate fix is local; shape refactor is a day of work with high
  regression risk.

### D6 — How other languages gate their drop glue

- **Rust:** compiler-selected at MIR-lowering time per type. No
  size heuristic — every type's drop is inserted unconditionally.
  Dead drops get DCE'd at codegen.
- **C++:** `~T()` called unconditionally per scope. RAII.
  Compile-time always-on.
- **Swift:** ARC; release calls inserted at MIR level, elided by
  refcount analysis.
- **Go:** GC runtime; no drop glue.
- **Mapanare:** explicit compiler-tracked drops at return edges.
  The size gate is unique to Mapanare's pragmatic balance: zero
  runtime overhead, no borrow checker yet.

---

## Risks

- **R1 — Stage2.ll still explodes with the gate.** If there are
  many small-struct returns that trip the walk in hot emit
  functions, the growth could still be large. *Mitigation:* measure
  first. If >3%, tighten the gate (N = 6, M = 30). If that breaks
  62_list_output, the gate cutoff is too aggressive — rethink.
- **R2 — Stage3 regresses to empty again.** If the walk in a
  small-struct-returning small-slot fn still corrupts, we're back
  to Ve.1-shaped breakage. *Mitigation:* `verify_fixed_point.sh
  --keep` as a gate; if stage3 is empty, revert the re-lift.
- **R3 — 62_list_output still leaks post-gate.** The `St` struct
  has `List<String>` as field 0. If the walk extracts the list
  header but not the elements, the inner String allocations may
  still leak. *Mitigation:* verify the walk covers `{ptr, i64}`
  (String) AND `{ptr, i64, i64, i64}` (List) field types. v5.4.4
  Phase 3 reportedly did; spot-check after re-enable.
- **R4 — New leak from wrong alias match.** The extracted ptr from
  `extractvalue` is the data pointer; if it aliases a tracked
  slot, the alias-short-circuit should skip the free. But if the
  match logic is off, we could either double-free (UAF) or miss a
  free (leak). *Mitigation:* ASan UAF sweep + LSan sweep catch
  both.
- **R5 — New ASAN_ERROR on a previously-CLEAN golden.** UAF from
  the walk freeing a String that's still live. *Mitigation:* full
  ASan sweep as a gate.
- **R6 — Size-gate constants wrong for the corpus.** If a new
  struct at N = 9 fields gets added to a golden, we'd silently
  skip it. *Mitigation:* the walk only matters for leak detection;
  silent skips lead to LEAK detected by LSan. Not UAF-unsafe.

---

## What NOT to do

- **Do not rewrite `emit_drop_glue`.** Just extend the guard
  function. The existing struct-field walk code is correct and
  already present.
- **Do not change the field walk's extraction logic.** It was
  validated at v5.4.4 Phase 3 and the code is unchanged.
- **Do not expose gate constants.** Keep them in
  `ret_ty_is_aggregate`.
- **Do not ship without `verify_fixed_point.sh` producing non-empty
  stage3.** That's the v5.6.5 closure gate; we're downstream of it.
- **Do not refresh the baseline before the sweep confirms CLEAN.**
  Same rule as v5.4.2 / v5.4.3 / v5.6.4: sweep first, baseline
  second.
- **Do not tag v5.6.6 without user approval.** v-tag timing rule.
