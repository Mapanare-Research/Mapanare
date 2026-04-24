# Mapanare v5.6.4 — "Own.1 Phase 3: Rt.06 Tensor Drop-Glue"

> **Close Rt.06 by porting the Python bootstrap's `_tensor_vars` /
> `_emit_drop_glue_tensors` pair to the self-hosted emitter.** Adds
> a fourth ownership list (`tensor_owned`) parallel to
> `str_owned` / `list_owned` / `boxed_owned`, a matching
> `emit_track_tensor` helper, and per-site tracking at every
> tensor-allocating emit point. Closes LSan leaks on all 5 tensor
> goldens (49/50/51/52/53).

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.6.3 shipped (Sh.6 closed — all 5 tensor
goldens run byte-identical; Rt.06 now formally covers 49/50/51/52/53)
**Estimated work:** 1 session (~2–3 hours). Purely additive; mirrors
the v5.4.1 shadow-slot pattern exactly, just swaps `{ptr, i64}` /
`__mn_list_free` / `free` for `ptr` / `__mn_tensor_free`.
**Owner docket:** Own.1 Phase 3 (Rt.06 opened v5.6.2; scope expanded
v5.6.3 to include slice + reductions goldens)

---

## Why this release exists

### The baseline-gated leaks

After v5.6.3, `check_leak_summary.py` tolerates 5 tensor-shaped
LEAK entries — inherited from each golden's prior `COMPILE_FAIL`
class as phases of Sh.6 closed:

| Golden | Leak source | Objs / bytes |
|---|---|---:|
| `49_tensor_literal` | `__mn_tensor_alloc` from `emit_tensor_init` | 9 / 248 B |
| `50_tensor_indexing` | multi-dim alloc + indexing intermediates | 12 / 392 B |
| `51_tensor_broadcast` | `__mn_tensor_{add,mul,…}_broadcast/scalar/rscalar` fresh-tensor returns | 24 / 672 B |
| `52_tensor_slicing` | `__mn_tensor_slice` fresh tensor; tensor literals in `let c = ...` / `let d = ...` | ~30 / ~800 B (new in v5.6.3) |
| `53_linear_regression` | per-epoch `X * w + b`, `pred - y`, `error * X` broadcast intermediates | ~1000 / ~28 KB (new in v5.6.3; the `for epoch in 0..10` loop allocates fresh tensors per iteration) |

All are process-exit-only — the OS reclaims on termination, so no
user-facing correctness issue. But the LSan gate remains baseline-
gated which means any *new* tensor-allocation pattern silently gets
a free pass. Closing Rt.06 tightens the gate from "these goldens
may leak" to "no tensor may leak at function exit."

### Python reference

- `mapanare/emit_llvm_text.py:541` — `self._tensor_vars: list[str]`
- `mapanare/emit_llvm_text.py:2039-2078` —
  `_emit_drop_glue_tensors(ret_val, ret_ty)` — per-tracked-var
  `load ptr + icmp eq null + br + call void @__mn_tensor_free`,
  with ret-value alias short-circuit when ret_ty is PTR.
- `mapanare/emit_llvm_text.py:1672-1674` — decl emission gated on
  `self._tensor_vars` non-empty (mirrors the v5.4.1 pattern).
- `mapanare/emit_llvm_text.py:3715/3753/3767/3782/4481` — 5 per-
  site `self._tensor_vars.append(i.dest.name)` calls (slice,
  broadcast, scalar, rscalar, alloc).

### Self-hosted current state

Zero tensor tracking. Every site that emits a call returning a
fresh tensor `ptr` leaves the value un-freed at function exit:

```bash
grep -n "__mn_tensor_alloc\|__mn_tensor_slice\|_broadcast_\|_scalar_\|_rsub_scalar_\|_rdiv_scalar_" \
  mapanare/self/emit_llvm.mn | grep "call noalias ptr" | wc -l
# 22 emit sites (1 alloc + 1 slice + 8 broadcast + 8 scalar + 4 rscalar)
```

All 22 need `emit_track_tensor(s, dn)` after the emit line.

---

## Scope

### What ships

#### 9.4a — `EmitState.tensor_owned` + `tensor_owned_source`

Two new fields on `EmitState`. Registry bump 23 → 24 structs
(`check_struct_registry.py` will reject if the field lists
disagree between the declaration, constructor, and
`make_entry` / `register_internal_struct` rows — four sites).

```mn
struct EmitState {
    ...
    str_owned: List<String>,
    list_owned: List<String>,
    boxed_owned: List<String>,
    tensor_owned: List<String>,        // v5.6.4 — tensor slot bases
    ...
    str_owned_source: List<String>,
    list_owned_source: List<String>,
    boxed_owned_source: List<String>,
    tensor_owned_source: List<String>  // v5.6.4 — tensor source SSA names
}
```

Both lists are string-typed; `tensor_owned` holds slot bases
(without the leading `%`), `tensor_owned_source` holds the SSA
source name the slot was allocated for (parallel to the existing
`*_owned_source` pattern from v5.4.4).

#### 9.4b — `emit_track_tensor` helper

Mirrors `emit_track_boxed` in structure (tensor values are
single `ptr`, identical to boxed):

```mn
fn emit_track_tensor(st: EmitState, ptr_val: String) -> EmitState {
    let mut s: EmitState = st
    let idx: Int = s.counter
    s.counter = s.counter + 1
    let slot_base: String = "tens_track." + toString(idx)
    let slot: String = "%" + slot_base
    s.entry_prelude_lines.push("  " + slot + " = alloca ptr, align 8")
    s.entry_prelude_lines.push("  store ptr null, ptr " + slot)
    // v5.4.3 free-before-store parity: in loop bodies, __mn_tensor_free
    // the prior snapshot before overwriting. Null-tolerant — the zero-
    // init ensures first-iter is a no-op.
    if s.loop_depth > 0 {
        let prev_tmp: String = "%prev.tens." + toString(s.counter)
        s.counter = s.counter + 1
        s = emit_line(s, "  " + prev_tmp + " = load ptr, ptr " + slot)
        s = emit_line(s, "  call void @__mn_tensor_free(ptr " + prev_tmp + ")")
    }
    s = emit_line(s, "  store ptr " + ptr_val + ", ptr " + slot)
    s.tensor_owned.push(slot_base)
    s.tensor_owned_source.push(ret_val_base(ptr_val))
    return s
}
```

The loop-depth branch is load-bearing for golden 53 —
`53_linear_regression` loops 10 epochs and each iteration
allocates ~4 fresh tensors via `pred = X * w + b`,
`error = pred - y`, `error * X`. Without loop-depth free-before-
store, 40 tensors leak (even with drop-glue at return). With it,
all 40 collapse to 4 live slots per iteration that get freed on
overwrite.

#### 9.4c — Per-site tracking injection

22 emit sites need a post-emit call to `emit_track_tensor(s, dn)`:

| Site | Current line | Injection |
|---|---|---|
| `emit_tensor_init` (~line 1482) | `s = emit_line(s, "  " + dn + " = call noalias ptr @__mn_tensor_alloc(...)")` | append `s = emit_track_tensor(s, dn)` |
| `__mn_tensor_slice` special case (v5.6.3) | final `s_sl = emit_line(s_sl, "  " + dn + " = call noalias ptr @__mn_tensor_slice(...)")` | append `s_sl = emit_track_tensor(s_sl, dn)` |
| 8 broadcast fns in `emit_mir_call` | current generic `emit_call_ir` fallback | add dedicated per-fn branch that emits the call and tracks |
| 8 scalar fns | same | same |
| 4 rscalar fns | same | same |

Wait — the self-hosted emitter currently has **no** dedicated
branches for the 20 tensor binop fns; they route through the
generic `emit_mir_call` path (which uses the `find_function` +
`emit_call_ir` helpers). So the injection strategy differs from
Python:

**Option A** — replicate Python's per-fn pattern (add 20 `if fn_name ==`
branches in `emit_mir_call`, each doing its own emit + track).
Byte-identical to Python but +160 LOC.

**Option B** — track at the end of the generic call path, guarded
on fn_name membership in a 22-element set. +30 LOC.

**Decision: B.** The generic call path already emits the right IR
(v5.6.2 shipped this). Adding 20 branches duplicates the emit
logic just to attach a tracking call. Use a predicate
`is_tensor_allocating_fn(fn_name)` + a single post-emit injection
in the generic path's success branches (the `Some(fe)` branch at
`emit_llvm.mn:3696` and the `_` branch at `:3717`). `emit_tensor_init`
and `__mn_tensor_slice` still get direct injections (they have
special-case branches already).

```mn
fn is_tensor_allocating_fn(fn_name: String) -> Bool {
    if fn_name == "__mn_tensor_alloc" { return true }
    if fn_name == "__mn_tensor_slice" { return true }
    if fn_name == "__mn_tensor_add_broadcast_f64" { return true }
    if fn_name == "__mn_tensor_sub_broadcast_f64" { return true }
    if fn_name == "__mn_tensor_mul_broadcast_f64" { return true }
    if fn_name == "__mn_tensor_div_broadcast_f64" { return true }
    if fn_name == "__mn_tensor_add_broadcast_i64" { return true }
    if fn_name == "__mn_tensor_sub_broadcast_i64" { return true }
    if fn_name == "__mn_tensor_mul_broadcast_i64" { return true }
    if fn_name == "__mn_tensor_div_broadcast_i64" { return true }
    if fn_name == "__mn_tensor_add_scalar_f64" { return true }
    if fn_name == "__mn_tensor_sub_scalar_f64" { return true }
    if fn_name == "__mn_tensor_mul_scalar_f64" { return true }
    if fn_name == "__mn_tensor_div_scalar_f64" { return true }
    if fn_name == "__mn_tensor_add_scalar_i64" { return true }
    if fn_name == "__mn_tensor_sub_scalar_i64" { return true }
    if fn_name == "__mn_tensor_mul_scalar_i64" { return true }
    if fn_name == "__mn_tensor_div_scalar_i64" { return true }
    if fn_name == "__mn_tensor_rsub_scalar_f64" { return true }
    if fn_name == "__mn_tensor_rdiv_scalar_f64" { return true }
    if fn_name == "__mn_tensor_rsub_scalar_i64" { return true }
    if fn_name == "__mn_tensor_rdiv_scalar_i64" { return true }
    return false
}
```

Post-emit injection point: after `emit_line` returns in each
success branch, if `is_tensor_allocating_fn(fn_name)`, call
`emit_track_tensor(s, dn)` before returning the state.

#### 9.4d — `emit_drop_glue_tensors` helper

Mirrors `emit_drop_glue_boxed` structurally — `ptr` slot type,
`__mn_tensor_free` instead of `@free`, ret-ptr alias short-
circuit:

```mn
fn emit_drop_glue_tensors(st: EmitState, ret_tensor_ptrs: List<String>) -> EmitState {
    let mut s: EmitState = st
    let n: Int = len(s.tensor_owned)
    let ns: Int = len(s.tensor_owned_source)
    let nret: Int = len(ret_tensor_ptrs)
    let mut i: Int = 0
    for _ in 0..1024 {
        if i >= n { return s }
        let name: String = s.tensor_owned[i]
        let mut source: String = ""
        if i < ns { source = s.tensor_owned_source[i] }
        let is_moved: Bool = (len(source) > 0) && list_has_string(s.moved_locals, source)
        if !is_moved {
            let cnt: Int = s.counter
            s.counter = s.counter + 1
            let tvtmp: String = "%drop.tv" + toString(cnt)
            s = emit_line(s, "  " + tvtmp + " = load ptr, ptr %" + name)
            if nret > 0 {
                let free_lbl: String = "drop.tfree." + toString(cnt)
                let skip_lbl: String = "drop.tskip." + toString(cnt)
                s = emit_or_reduce_ret_match(s, tvtmp, ret_tensor_ptrs, cnt, "t", skip_lbl, free_lbl)
                s = emit_line(s, free_lbl + ":")
                s = emit_line(s, "  call void @__mn_tensor_free(ptr " + tvtmp + ")")
                s = emit_line(s, "  br label %" + skip_lbl)
                s = emit_line(s, skip_lbl + ":")
            } else {
                s = emit_line(s, "  call void @__mn_tensor_free(ptr " + tvtmp + ")")
            }
        }
        i = i + 1
    }
    return s
}
```

Null-tolerance: `__mn_tensor_free` already handles null (runtime
C guards `if (!t) return;` at `runtime/native/mapanare_gpu_builtins.c`).
No null-check needed before the free.

`emit_drop_glue_destroy` (v5.5.7 async cleanup helper) also grows
a tensor branch — same structure, unconditional free (no
moved_locals consult, consistent with the existing destroy helper).

#### 9.4e — `emit_drop_glue` dispatch

Add a fourth `ret_tensor_ptrs` list + pre-drop extraction + call
to the new helper. The scalar-ptr return path currently pushes to
`ret_box_ptrs`; we need to disambiguate — `ptr` return type could
be either a tensor *or* a boxed enum payload. Decision: push the
same SSA to **both** `ret_box_ptrs` and `ret_tensor_ptrs`. Each
per-resource drop-glue helper has its own alias check, so a
tensor ret-val legitimately appearing in both lists will short-
circuit both drops — the one that wouldn't apply (boxed when the
local is a tracked tensor, and vice versa) is a no-op because the
slot won't match the unrelated owner list.

Same logic for the `%struct.*` field walk: any `ptr` field lands
in both `ret_box_ptrs` and `ret_tensor_ptrs`. Over-approximation
is safe; we lose no frees but may skip some that could legitimately
fire (tensor-in-struct-return pattern — not present in the corpus,
so no observable effect).

#### 9.4f — Move-emission for tensors (optional)

v5.4.4 emitted `Instruction::Move(val)` after `list.push`,
`IndexSet`, StructInit fields, EnumInit payloads, Some / Ok / Err
wrappers, MapInit entries. None of these currently target tensors
in the golden corpus, but for completeness:

- `list.push(a_tensor)` should emit Move(tensor_val) so drop-glue
  skips it (list owns the slot now).

Check whether the lowerer already emits Move unconditionally
(`lower_push_method` at `lower.mn:2630` does `emit_instr(…,
Move(arg_r.value))` regardless of type). If so, the existing
Move path already covers tensors — the Move visits `moved_locals`
via the MIR kind string `"move"`, which is type-agnostic. No
additional lowerer changes needed — just verify.

### What does NOT ship

- **Multi-function tensor lifetime tracking.** A tensor passed as
  a fn arg and returned keeps its escape semantics from scalar-ptr
  return — no inter-procedural analysis. Fine; Python has the
  same scope.
- **Tensor move-on-assign.** `let b = a; … use(a) …` (double-
  drop) is not a pattern in the corpus. v6.0 borrow-checker scope.
- **Close Ve.1.** Pre-existing from v5.4.4 — still out of scope.
- **Change Python emitter.** Python already tracks; the gap is
  self-hosted only.
- **Close goldens 51 / 64.** v5.7.0's job.

---

## Exit criteria

1. `check_struct_registry.py` reports 24 make_entry / 24
   register_internal_struct cross-checked against 92 source
   structs (+1 vs v5.6.3's 91 — no new structs, but `EmitState`
   field count grows by 2).

   Wait — adding fields to an existing struct doesn't add a new
   struct. The field-list parity check is the relevant gate.
   Expected: 23/23/91 still, with the field-list for `EmitState`
   updated at all 4 sites.

2. `mnc-stage1` compiles all 5 tensor goldens byte-identical to
   v5.6.3 output:

   - 49: `1 3 1 3 2 6 1 6 2 3 3 8 1 8 3 20 -1 -2.5`
   - 50: `1 3 4 6 10 30 1 8 42 99 200`
   - 51: `11 44 9 36 10 10 101 104 2 8 11 33`
   - 52: `15 3 5 1 4 0 60 30 1 2 20 30 2 6`
   - 53: `w = 1.96879 / b = 0.560177 / converging`

3. LSan sweep: 0 tensor leaks across 49/50/51/52/53. Previously
   baseline-gated LEAK entries now either move to CLEAN or stay
   in a residual (non-tensor) leak class.

4. `scripts/check_leak_summary.py` baseline TSV refreshed — all
   5 tensor goldens now gate at 0 objs / 0 B. Any future tensor-
   allocation pattern that doesn't track must now fail CI.

5. Harness: 64/66 preserved (no regressions).

6. stage2.ll `llvm-as` clean. Expected +1-2% line growth from the
   ~50 tracking+drop-glue lines added to the ~140 functions that
   do tensor work (but self-compilation barely touches tensors —
   only `emit_tensor_init` uses the alloc path, so stage2.ll
   growth should be under 0.5%).

7. Valgrind sweep: 0 new ERRORS.

8. Non-bootstrap pytest 0 failures.

9. `make lint` clean.

10. `docs/known_issues.md` Rt.06 row flipped to **CLOSED v5.6.4**.

---

## Design decisions

### D1 — Separate `tensor_owned` list vs reuse `boxed_owned`

Python has separate `_tensor_vars` from `_boxed_vars`, and uses
different free fns (`__mn_tensor_free` vs `@free`). Mirroring the
split is structurally cleaner (each resource kind has its own
tracking list + drop-glue helper + runtime free).

The alternative — lumping tensors into `boxed_owned` and branching
inside `emit_drop_glue_boxed` on the source fn name — couples two
distinct resource kinds into one slot list, forcing the drop-glue
helper to remember which free fn to call per slot. Rejected.

### D2 — Post-emit injection in generic call path vs 20 dedicated branches

**Chose: post-emit injection.** The 20 tensor binop fns currently
route through the generic `find_function → emit_call_ir` path with
correct types. Adding 20 dedicated branches to match Python's
structure costs ~160 LOC and duplicates correctness logic already
exercised during v5.6.2 broadcast tests. A single
`is_tensor_allocating_fn(fn_name)` predicate + one post-emit call
gives parity.

### D3 — Loop-depth free-before-store

Golden 53 is the case study. 10-epoch loop × ~4 fresh tensors per
iter = 40 leaked tensors without intra-loop free. The existing
`loop_depth > 0 → load + free before store` pattern from v5.4.3
(`emit_track_string` / `_boxed`) ports directly. Reuse verbatim.

### D4 — Return-escape `ptr` dual-push (box + tensor)

For any scalar `ptr` return, the same SSA gets pushed to both
`ret_box_ptrs` and `ret_tensor_ptrs`. Each helper independently
short-circuits its slot drops on alias match. Over-approximation
is safe: if a fn returns a tensor, the boxed drop-glue won't free
it (no boxed slot matches the ptr anyway), and the tensor drop-
glue correctly skips the matching tensor slot. Symmetric.

### D5 — No recursive struct-field walk for tensor ptrs

The v5.4.4 `%struct.*` one-level walk already treats all `ptr`
fields uniformly (pushes into `ret_box_ptrs`). Adding a parallel
push into `ret_tensor_ptrs` at the same site gives tensor drop-
glue the same escape visibility without adding a separate walk.
Same over-approximation reasoning as D4.

### D6 — Python-parity over theoretical purity

A fn might have `__mn_tensor_free` called on a ptr that's
actually a boxed enum payload (or vice versa). In practice neither
runtime fn cares about "wrong" pointers beyond the null check —
both call into `free()` on the data, which is defined behavior
for any heap ptr. The real correctness gate is: every
`__mn_tensor_alloc` result has exactly one `__mn_tensor_free`
call on the normal-return path. The dual-push can cause a tensor
ptr to appear in `ret_box_ptrs` and be skipped by the boxed drop-
glue because of an alias that doesn't actually alias (false
skip). But false skips only mean we leave a drop that Python would
have emitted — equal or fewer frees, never double-free. Safe.

### D7 — Design context: how other languages handle resource drop

- **Rust:** compiler-known `Drop` trait; drop glue inserted at
  every scope exit via MIR → codegen. Tensor-typed values would
  just implement Drop. Complete but requires borrow checker.
- **Swift:** ARC + `deinit`. Each strong reference has a retain/
  release pair; ref-count-zero triggers deinit. Tensor = class,
  gets deinit for free.
- **C++:** RAII — `~Tensor()` called at scope exit. Move/copy
  semantics prevent double-free.
- **Go:** GC. No drop glue needed; collector frees unreferenced
  tensors.
- **Mapanare today:** compiler tracks + inserts `__mn_*_free`
  calls at return edges. Explicit, no GC, no borrow checker. This
  release adds tensor to the set of resources the compiler
  tracks.

---

## Risks

- **R1 — Double-free from dual-push collision.** If a local is
  tracked in `tensor_owned` AND a struct-return field happens to
  alias it, the over-approximation means the boxed drop-glue
  won't fire (correct) but the tensor drop-glue also skips
  (correct). No double-free. *Not observed.*
- **R2 — Move-on-insert for tensors.** `list.push(tensor)` moves
  ownership; drop-glue must skip the source slot. v5.4.4's Move
  pattern is type-agnostic (matches on SSA name via
  `moved_locals`); verify it fires on tensor args by grepping
  `lower_push_method`. If it doesn't, add a targeted Move
  emission there.
- **R3 — stage2.ll growth.** Every fn that emits a tensor op now
  carries tracking slots + drop-glue. Self-compilation barely
  uses the tensor path (only `emit_tensor_init`), so stage2.ll
  growth should be <0.5%. Verify in Phase 8.
- **R4 — Baseline TSV refresh hiding a real regression.** If we
  naively flip 49/50/51/52/53 to CLEAN in the baseline without
  running the actual sweep, we mask a failure. Mitigation: flip
  only after the sweep confirms 0 tensor leaks, and log the
  before/after summaries.
- **R5 — Ve.1 interaction.** Adding per-fn tracking slots inflates
  each fn's entry-block prelude. If the inflation crosses some
  threshold in `parse_fn_body`'s 256-byte List<X> allocation
  (the Ve.1 root cause), stage2 may newly segfault on
  `mnc_all.mn` compilation. Run stage2-build as a gate; if it
  fails, size-gate tracking injection behind an env var and
  revisit Ve.1 properly.
- **R6 — Tensor as struct field.** A struct with a tensor `ptr`
  field returned from a fn will get the field walked as `ret_box_ptrs`
  currently. The v5.6.4 patch pushes the same field into
  `ret_tensor_ptrs` too. Works. But if the struct is returned
  via sret, the alias comparison hits different SSA — verify the
  existing v5.4.4 walk covers sret returns correctly.

---

## What NOT to do

- **Do not add a tensor move-on-assign pattern.** `let b = a;
  use(a)` would double-free; out of scope. If the corpus has no
  such pattern, we skip it.
- **Do not add a `Drop` trait to Mapanare's type system.** v6.0
  scope.
- **Do not change Python's emitter.** Python already has this.
- **Do not refactor the existing drop-glue shape.** Just extend
  with the fourth resource kind.
- **Do not ship without baseline TSV refresh.** Baseline-gated
  entries that should now be CLEAN remaining as "LEAK allowed"
  is a silent regression waiting to bite.
- **Do not decouple `emit_track_tensor` from
  `is_tensor_allocating_fn`.** Every fn in the predicate list
  must track; every call to `emit_track_tensor` must be for a
  fn in the list. Keep them in sync.
- **Do not add a null-check before `__mn_tensor_free`.** Runtime
  handles null (`if (!t) return`). Adding one would duplicate the
  guard and inflate IR.
