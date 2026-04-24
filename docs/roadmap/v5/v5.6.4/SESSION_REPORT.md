# Mapanare v5.6.4 — Own.1 Phase 3: Rt.06 Tensor Drop-Glue

> **Rt.06 CLOSED — zero tensor leaks across all 5 tensor goldens.**

**Status:** SHIPPED
**Scope delivered:**

- `EmitState` gains two fields (`tensor_owned: List<String>` and
  `tensor_owned_source: List<String>`) parallel to the existing
  `str_owned` / `list_owned` / `boxed_owned` pairs.
- `emit_track_tensor` helper mirrors `emit_track_boxed` structurally
  (ptr slot type; `__mn_tensor_free` instead of `@free`). Loop-depth
  free-before-store parity with v5.4.3 — load-bearing for golden 53
  where the 10-epoch loop allocates ~4 fresh tensors per iteration.
- `is_tensor_allocating_fn(fn_name)` predicate enumerates 22 runtime
  fns: `__mn_tensor_alloc`, `__mn_tensor_slice`, 8 broadcast
  (`add/sub/mul/div × f64/i64`), 8 scalar, 4 reverse-scalar.
- Per-site tracking injection at 4 call sites: `emit_tensor_init`
  and the `__mn_tensor_slice` special case get direct injections;
  the two generic-call success branches (`Some(fe)` at ~3790 and
  `_` fallback at ~3822) get `is_tensor_allocating_fn` guards.
- `emit_drop_glue_tensors` helper — structurally parallel to
  `emit_drop_glue_boxed`, with ret-ptr alias short-circuit and
  SSA prefix `t` disambiguated from `s` / `l` / `b`.
- `emit_drop_glue_destroy` (v5.5.7 async cleanup) grows a fourth
  tensor loop with unconditional `__mn_tensor_free` — consistent
  with the existing str / list / boxed loops.
- `emit_drop_glue` dispatcher: fourth `ret_tensor_ptrs: List<String>`
  list. Fast-path guard includes `len(tensor_owned) > 0`. Scalar
  ptr return + `%struct.*` field walk dual-push `ret` into both
  `ret_box_ptrs` and `ret_tensor_ptrs` — each per-resource helper
  alias-checks its own slot list, so the over-approximation is
  safe (PLAN §D4).
- `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`
  refreshed: 49/50/51/52/53 flip from `COMPILE_FAIL` / LEAK-allowed
  to `CLEAN`. Future tensor-allocation patterns that skip
  `emit_track_tensor` now fail `make leak-check`.

**Scope deferred:** Tensor move-on-assign (v6.0 borrow-checker).
Tensor-inside-struct field pattern (no corpus occurrences).
Inter-procedural tensor-lifetime analysis (Python has the same
scope — fine).

---

## Changes by phase

### Phase 0 — Baseline + version bump

- Bumped `VERSION` 5.6.3 → 5.6.4.
- Captured pre-fix leak numbers per-golden at
  `docs/roadmap/v5/v5.6.4/asan-leak-baseline-pre-fix.tsv`:
  49 → 9 objs / 248 B, 50 → 12/392, 51 → 24/672, 52 → 15/416,
  53 → 123/3608 (the dominant leak; tensor binop + slice
  intermediates across 10 epochs).

### Phase 1 — `EmitState.tensor_owned` + `tensor_owned_source`

Two new `List<String>` fields parallel to the three existing
ownership lists. Four sites had to stay in sync:

- `struct EmitState { ... }` declaration at `emit_llvm.mn:81,111`
- `new_emit_state(...)` constructor at `:129,136,137` — both new
  lists initialized to `[]`, appended to `new EmitState { ... }`
  keyword-arg list.
- `emit_internal_structs_registry(...)` `make_entry` row at `:148`
- `register_internal_struct(...)` call at `:193`

`check_struct_registry.py` clean (23 `make_entry` / 23
`register_internal_struct` / 91 source structs — no new struct,
`EmitState` just grows two fields).

### Phase 2 — `emit_track_tensor` + `is_tensor_allocating_fn`

Helper inserted right after `emit_track_boxed` at
`emit_llvm.mn:4141`. Structure verbatim from `emit_track_boxed`
modulo:

- slot prefix: `tens_track.` instead of `box_track.`
- free fn: `@__mn_tensor_free` instead of `@free`
- ownership lists: `s.tensor_owned.push(slot_base)` +
  `s.tensor_owned_source.push(ret_val_base(ptr_val))`

Loop-depth branch loads the prior snapshot at
`%prev.tens.N` and calls `__mn_tensor_free` before storing the new
value. Null-tolerant runtime (`if (!t) return` at
`runtime/native/mapanare_gpu_builtins.c`) means first-iter is a
no-op on the zero-initialised slot.

`is_tensor_allocating_fn(fn_name)` at `emit_llvm.mn:4168` — 22-branch
if-ladder (1 alloc + 1 slice + 8 broadcast + 8 scalar + 4 rscalar).
Keeping a predicate instead of 20 dedicated `emit_mir_call`
branches is the key v5.6.4 design call (PLAN §D2) — v5.6.2 already
shipped correct IR for these 20 fns via the generic
`find_function` → `emit_call_ir` path. Duplicating 160 LOC of
emit logic just to attach a tracking call would have been dead
weight.

### Phase 3 — Per-site tracking injection

- `emit_tensor_init` at `:1495` — append `s = emit_track_tensor(s,
  dn)` after the `__mn_tensor_alloc` emit line.
- `__mn_tensor_slice` special case at `:3514` —
  `s_sl = emit_track_tensor(s_sl, dn)` before the final `return s_sl`.
- `emit_mir_call` `Some(fe)` success branch at `:3797` — post-emit
  injection gated on `is_tensor_allocating_fn(fn_name)`.
- `emit_mir_call` `_` fallback success branch at `:3822` — same
  gate pattern, covers fns not registered in `st.functions`.

Verified shape on golden 52: 18 `tens_track.` slot allocas, 0
`__mn_tensor_free` calls (dispatcher wiring landed in Phase 5).
Verified on golden 53: 22 tens_track slots, 8 `prev.tens.*` loads
inside the 10-epoch loop — confirms the v5.4.3 free-before-store
pattern fires.

### Phase 4 — `emit_drop_glue_tensors` helper + destroy-path wiring

Helper at `emit_llvm.mn:4362`. Structurally identical to
`emit_drop_glue_boxed`:

- `ptr` slot type (same as boxed)
- SSA prefix `t` (`%drop.tv.N` / `drop.tfree.N` / `drop.tskip.N`)
- `call void @__mn_tensor_free(ptr %drop.tvN)`
- `emit_or_reduce_ret_match` shared with the three existing helpers,
  passing `"t"` as the prefix arg — `%drop.tmacc.N` / `%drop.tsame.N.K`
  SSA names distinct from str / list / boxed.

`emit_drop_glue_destroy` (v5.5.7 async cleanup) extended with a
parallel unconditional tensor loop at `:4475` — SSA prefix
`%drop.d.t.N` distinct from normal-exit `%drop.tv.N` and sibling
destroy-path `%drop.d.{s,l,b}.N`.

### Phase 5 — `emit_drop_glue` dispatcher

Fast-path guard at `:4445` extended to include `len(st.tensor_owned)`.
Fourth list declared at `:4462`. Dual-push logic at the two ptr
escape sites:

- Scalar ptr return (`:4479-4483`) — push `ret_val` to both
  `ret_box_ptrs` and `ret_tensor_ptrs`.
- `%struct.*` field walk, `ft == "ptr"` branch (`:4515-4523`) —
  push `fp` to both lists.

Per PLAN §D4, over-approximation is safe: if the scalar ptr is
actually a tensor, boxed drop-glue won't match any tracked boxed
slot (no-op); tensor drop-glue alias-matches and short-circuits
the tracked tensor slot. Symmetric for the boxed case.

Tail of `emit_drop_glue` now calls
`s = emit_drop_glue_tensors(s, ret_tensor_ptrs)` after
`emit_drop_glue_boxed`.

### Phase 6 — Verify goldens + byte-identical output

All 5 tensor goldens compile + run byte-identical to v5.6.3:

| Golden | Output | Match |
|---|---|---|
| 49_tensor_literal | `1 3 1 3 2 6 1 6 2 3 3 8 1 8 3 20 -1 -2.5` | ✓ |
| 50_tensor_indexing | `1 3 4 6 10 30 1 8 42 99 200` | ✓ |
| 51_tensor_broadcast | `11 44 9 36 10 10 101 104 2 8 11 33` | ✓ |
| 52_tensor_slicing | `15 3 5 1 4 0 60 30 1 2 20 30 2 6` | ✓ |
| 53_linear_regression | `w = 1.96879 / b = 0.560177 / converging` | ✓ |

Golden harness: 64/66 preserved — `51_match_guards_and_or` (B —
bootstrap also fails or-pattern) and `64_closure_typed` (Sh.7)
remain the only failures, same as v5.6.3. Shape counts per golden:

| Golden | tens_track slots | `__mn_tensor_free` calls |
|---|---:|---:|
| 49 | 20 | 5 |
| 50 | 20 | 5 |
| 51 | 44 | 11 |
| 52 | 24 | 6 |
| 53 | 28 | 10 |

Track/free ratio is ~1:4 because most slots are consumed inline
(tensor literals stored into list elements; intermediate binop
results immediately fed to the next binop or assigned to a
tracked name that aliases them). The slots still carry non-null
values at fn exit and drop-glue frees them.

### Phase 7 — LSan sweep + baseline refresh

Full 66-golden LSan sweep under `ASAN_OPTIONS=detect_leaks=1:
leak_check_at_exit=1` with `LSAN_OPTIONS=suppressions=asan_leak_suppressions.txt`:

| Class | Count |
|---|---:|
| CLEAN | 50 |
| LEAK | 3 |
| COMPILE_FAIL | 1 |
| LINK_FAIL | 12 |
| RUN_FAIL | 0 |

All 5 tensor goldens report **0 objs / 0 B** — Rt.06 closed. The
3 residual LEAK entries:

- `62_list_output` — 9 objs / 141 B, `__mn_alloc`. Pre-existing
  Rt.03 residual from v5.4.3; baseline unchanged (this is the
  aggregate-return loop-reassignment case v5.4.4's guard-lift
  attempt reverted).
- `39_gpu_detect` — 5 objs / 50212 B. All frames in
  `libcuda.so.1` (`cuInit`, unnamed) and `libvulkan.so.1` (Mesa
  llvmpipe initialization). Environmental — no Mapanare code in
  any stack trace. Baseline bumped from 3/49655 (v5.4.2 driver
  version) to 5/50212 (current WSL libvulkan).
- `40_gpu_tensor` — same 5/50212, same root cause
  (`gpu_available()` → `mapanare_gpu_init` → libcuda + libvulkan).

Baseline at `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`
refreshed; `scripts/check_leak_summary.py` PASSES:

```
Run TSV:      /tmp/asan-v5.6.4-after/asan-leak-summary.tsv
Baseline TSV: docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv

=== PASS: no leak regressions vs baseline ===
```

Post-fix snapshot at
`docs/roadmap/v5/v5.6.4/asan-leak-summary-post-fix.tsv`.

### Phase 8 — Fixed-point + stage2 + sanitizers

**stage2 self-compile:**

- stage1 → stage2.ll: 205,446 lines / 934 defines (+1,148 lines /
  +3 defines vs v5.6.3's 204,298 / 931). Growth: +0.56% —
  well under the 2% PLAN §R3 budget. 3 new defines are
  `emit_track_tensor`, `is_tensor_allocating_fn`, and
  `emit_drop_glue_tensors`. `llvm-as` clean.
- mnc-stage2 builds (4,467,392 bytes — consistent with v5.6.3 size
  modulo line-count drift).
- mnc-stage2 → stage3.ll: **Ve.1 persists** — stage2 segfaults
  during compilation of `mnc_all.mn`, same signature as v5.6.3
  and v5.4.4+. Not a v5.6.4 regression; pre-existing. Tracked in
  `docs/known_issues.md` Ve.1.

**Valgrind sweep:** 66 WARNINGS_ONLY / 0 ERRORS — byte-identical
to v5.6.3 baseline.

**ASan UAF sweep:** 60 CLEAN / 6 CRASH_NO_ASAN / 0 ASAN_ERROR —
byte-identical to v5.6.3 baseline. The 6 CRASH_NO_ASAN goldens are
the same Python-bootstrap C-backend compile failures on tensor
builtins (orthogonal to LLVM path).

### Phase 9 — Pytest + lint + struct registry

- Non-bootstrap pytest: **5565 passed / 116 skipped / 9 xfailed /
  0 failed** in 418s (+1 vs v5.6.3's 5564 — collateral from the
  VERSION macro bump in a parametrised test).
- `make lint`: all checks passed (ruff + black + mypy clean).
- `check_struct_registry.py`: clean (23 / 23 / 91).

### Phase 10 — Docs + SESSION_REPORT

- `docs/known_issues.md` — Rt.06 row flipped to **CLOSED v5.6.4**.
- `docs/roadmap/v5/PARITY_GAPS.md` — no row update (Rt.06 was
  tracked under memory-safety residuals; the PLAN.md carry-forward
  entry now points to closed).
- `CLAUDE.md` — v5.6.4 entry prepended.
- `docs/roadmap/ROADMAP.md` — v5.6.4 entry prepended.

---

## Exit criteria

| # | Criterion | Status |
|---|---|---|
| 1 | `check_struct_registry.py` reports 23/23/91 (field-list parity; `EmitState` field count +2) | ✓ clean |
| 2 | `mnc-stage1` produces byte-identical v5.6.3 output on 49/50/51/52/53 | ✓ all 5 match |
| 3 | LSan sweep: 0 tensor leaks across 49/50/51/52/53 | ✓ 0 objs / 0 B |
| 4 | `scripts/check_leak_summary.py` baseline TSV refreshed; no "LEAK allowed" entries for tensor goldens | ✓ flipped to CLEAN |
| 5 | Harness 64/66 preserved | ✓ same 2 fails |
| 6 | stage2.ll `llvm-as` clean; growth under 2% | ✓ +0.56% |
| 7 | Valgrind sweep: 0 new ERRORS | ✓ 0 ERRORS |
| 8 | Non-bootstrap pytest 0 failures | ✓ 5565 passed |
| 9 | `make lint` clean | ✓ |
| 10 | `docs/known_issues.md` Rt.06 → CLOSED v5.6.4 | ✓ |

---

## Risks vs reality

| Risk | PLAN severity | Outcome |
|---|---|---|
| R1 — double-free from dual-push collision | LOW | not observed; `emit_or_reduce_ret_match` per-helper alias check works as designed |
| R2 — move-on-insert for tensors | MED | no corpus occurrences; lowerer's existing Move path is type-agnostic and would cover if they appeared |
| R3 — stage2.ll growth | MED | +0.56% — well under 2% budget |
| R4 — baseline refresh hides real regression | HIGH | mitigated — sweep run before flip; pre-fix counts recorded at `asan-leak-baseline-pre-fix.tsv`; 39/40 delta documented as external WSL driver drift |
| R5 — Ve.1 interaction | HIGH | no new regression; stage2.ll growth (+0.56%) is modest; Ve.1 signature unchanged |
| R6 — tensor as struct field | LOW | dual-push covers one-level walk; no sret-specific breakage observed |

---

## What's next

- **v5.6.5+** — Close Rt.04 (list-in-struct escape), re-lift the
  `%struct.*` guard with size gate, diagnose Ve.1 properly.
- **v5.7.0** — Close Sh.7 closure-typed captures + B or-pattern →
  66/66.
- **v5.7.1** — SPEC + docs polish (pre-panel).
- **v5.8.0** — RE-PANEL (target 9.7+).

See `docs/roadmap/v5/CLOSEOUT_ARC.md`.
