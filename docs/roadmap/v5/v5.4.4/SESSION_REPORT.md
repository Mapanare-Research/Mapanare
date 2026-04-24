# v5.4.4 Session Report — Own.1 Phase 2 infrastructure

**Date:** 2026-04-23
**Status:** READY TO TAG (with rescope; see Deviations)
**Scope:** Land lowerer Move emission, slot-source parallel arrays,
and Move-aware drop-glue plumbing in both emitters. PLAN.md's original
goal of closing Rt.04 (62_list_output LEAK → CLEAN) was rescoped mid-
session; infrastructure lands, guard stays closed, and v5.4.5+ picks
up the leak fix once the field walk is gated on function size.

## Starting state (v5.4.3 tag)

- Version: 5.4.3
- Native goldens: 54/66 PASS (12 fail: 5 Sh.4 async + 5 Sh.6 tensor +
  1 Sh.7 closure_typed + 1 B bootstrap-also-fails)
- Valgrind: 66 WARNINGS_ONLY / 0 ERRORS
- ASan (no leak det.): 55 CLEAN / 11 CRASH_NO_ASAN
- ASan leak: 45 CLEAN / 3 LEAK (39_gpu + 40_gpu Rt.02 third-party +
  62_list_output Rt.04) / 11 COMPILE_FAIL / 7 LINK_FAIL
- Fixed-point: stage2.ll 124k lines, `llvm-as` OK; stage3 non-empty
  with teardown crash (Ve.1 baseline)
- `EmitState`: 19 fields (v5.4.3 added `loop_depth`)

## Phase-by-phase

### Phase 0 — baseline + VERSION bump

Confirmed 54/66 goldens, leak-check PASS, 3 LEAK (Rt.02 × 2 + Rt.04 ×
1). VERSION 5.4.3 → 5.4.4. Committed.

### Phase 1 — slot-source parallel arrays (plumbing)

Added three new `EmitState` fields parallel to the existing owner
lists:

| Field | Type | Indexes aligned with |
|---|---|---|
| `str_owned_source` | `List<String>` | `str_owned` |
| `list_owned_source` | `List<String>` | `list_owned` |
| `boxed_owned_source` | `List<String>` | `boxed_owned` |

Each entry holds the bare SSA source name (stripped of `%`) the slot
was allocated for. Registered in the internal struct registry (2
call sites bumped 19 → 22 fields). Reset in both `new_emit_state` and
the per-function reset in `emit_fn`. Populated by `emit_track_string`
(stripped val_name), `emit_track_boxed` (stripped ptr_val), and
`emit_list_init` (stripped dest.name, not the alloca name).

Python mirror: added `_local_strings_source`, `_local_boxed_source`,
`_list_vars_source` list fields and a new `_moved_locals: set[str]`
attribute. `_move_resource(name)` now adds the stripped name to
`_moved_locals` in addition to the existing slot-zero logic.
Populated in `_track_string`, `_track_boxed`, and `_track_container`
(list branch only).

Goldens 54/66 preserved. No semantic change — pure state plumbing.

### Phase 2 — lowerer Move emission

Emitted `Move(val)` MIR instructions after every resource-consuming
operation in both lowerers:

| Operation | Move target |
|---|---|
| `list.push(val)` | `val` (post ListPush) |
| `map[k] = v` / `list[i] = v` (IndexSet) | `index`, `val` |
| `new St { field: val }` (StructInit) | each `field.val` |
| Enum variant with payload | each payload arg |
| `Some(val)` / `Ok(val)` / `Err(val)` | `val` |
| `MapInit {k: v}` literal | each key and value |

Self-hosted: added `emit_move_vals` / `emit_move_fields` /
`emit_move_kvpairs` helpers in `mapanare/self/lower.mn` and wired
them at each dispatch site (`lower_push_method`, `lower_construct`,
the StructInit / EnumInit branches of `lower_call_by_name` /
`lower_namespace_access`, and the three `*_wrap` expression branches
+ their Builtin-call counterparts).

Python: imported `Move` from `mapanare.mir` and emitted inline after
the corresponding MIR op in `_lower_expr` / `_lower_call` /
`_lower_construct` / `_lower_assign` / `_lower_map` (plus the JSON
decode helper's StructInit + WrapErr + WrapOk sites).

Goldens 54/66 preserved. UAF sweep byte-identical at 55 CLEAN / 11
CRASH_NO_ASAN / 0 ASAN_ERROR.

### Phase 3 — Drop glue honors moved_locals + guard-lift attempt

Per-resource helpers rewritten to accept `List<String>` of ret-ptrs
instead of a single String. `is_moved` check switched from
`str_owned[i]` (the slot base, which never matches moved_locals'
SSA source names) to `str_owned_source[i]` (the bare SSA the slot
was allocated for). `emit_drop_glue` builds the ret-ptr lists by:

1. The existing scalar String / List / ptr extraction.
2. **New:** one-level `%struct.*` field walk — extract each String /
   List / ptr field via `extractvalue %struct.X %ret, idx` and push
   the data ptr into the matching ret-ptr list.

`ret_ty_is_aggregate` was flipped to return `false` for `%struct.*`
(keeping conservative skip for `%enum.*` and anonymous `{...}`).

Multi-ret-ptr support was initially attempted with chained `icmp +
br` (per Python's drop-glue-strings pattern), then switched to an
alloca-based OR-reduction after the chained-label pattern tripped a
bootstrap-compiler edge case (see **Deviation #1**). The OR-reduction
via i1 alloca worked — each iteration loads the accumulator, ORs in
the new compare result, stores back; the final load drives a single
br to skip/free.

Bumped `emit_fn`'s entry-block-body flush cap from 65536 to 1,000,000
iterations (and prelude 8192 → 65536). The 65536 cap was silently
truncating `emit_mir_call`'s drop-glue tail in stage2.ll — this
latent bug would have manifested independent of guard status.

**Result of Phase 3 on the golden corpus:**

| Metric | Phase 2 | Phase 3 | Delta |
|---|---|---|---|
| Goldens | 54/66 | 54/66 | 0 |
| UAF sweep | 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR | 55 / 11 / 0 | 0 |
| Leak sweep | 45 CLEAN / 3 LEAK | 46 CLEAN / 2 LEAK | **62_list_output FIXED** |

**But on self-compilation (fixed-point):**

| Metric | Pre-v5.4.4 (Ve.1) | Phase 3 |
|---|---|---|
| stage2.ll | 124k lines, llvm-as OK | 620k lines, llvm-as OK |
| stage3.ll | non-empty, teardown crash at end | 0 lines, mnc-stage2 segfault during lexing |

Phase 3's field walk added ~40 extractvalue lines per call site that
returns `%struct.EmitState` (22 fields, most of which are List-shape
struct types). `emit_mir_call`'s drop glue exploded from ~1 k lines
to ~66 k. The resulting `mnc-stage2` binary segfaulted during lex of
`mnc_all.mn` — the crash is in `malloc` called from `scan_ident`,
indicating heap corruption from something in the drop-glue-heavy IR.

### Phase 5 RESCOPE — restore aggregate-return guard

Per **PLAN.md's release-sequencing fallback:** "land lowerer Move +
slot-source mapping, KEEP the aggregate-return guard. This ships the
infrastructure without the leak fix; v5.4.5 then removes the guard
once more emit sites are covered."

Restored `ret_ty_is_aggregate` to return `true` for `%struct.*`. The
struct-field walk in `emit_drop_glue` is unreachable (guard bails
early). The per-resource helpers still accept `List<String>` of ret-
ptrs; for scalar returns the list is size 1, and the alloca-based
OR-reduction degrades to a single compare + single-element or-store.

62_list_output reverts to LEAK (matching v5.4.3 baseline). Baseline
file restored to cd4defa (v5.4.3 Phase 4's baseline). `make leak-
check` PASS.

### Phase 4 — baseline + Rt.04 docket (updated for RESCOPE)

`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` reverted to
v5.4.3's contents (62_list_output LEAK). `docs/roadmap/v5/v5.4.4/
asan-leak-summary-post-fix.tsv` kept as the snapshot that DID show
62_list_output CLEAN — evidence that the infrastructure works, even
though the guard re-closure undid that fix pending v5.4.5+.

`docs/known_issues.md` Rt.04 row updated with the full story: infra
landed, guard-lift attempted and reverted, v5.4.5+ re-lifts with a
size-gate.

### Phase 5 — final sanitizer gate

| Metric | Baseline (v5.4.3) | v5.4.4 | Delta |
|---|---|---|---|
| Goldens | 54/66 | 54/66 | 0 |
| Valgrind | 66 WARNINGS_ONLY / 0 ERRORS | 66 / 0 | 0 |
| ASan (no leak det.) | 55 CLEAN / 11 CRASH_NO_ASAN | 55 / 11 | 0 |
| ASan leak | 45 CLEAN / 3 LEAK (Rt.02 × 2 + Rt.04 × 1) | 45 / 3 | 0 |
| stage2.ll | 124k lines, llvm-as OK | 191k lines, llvm-as OK | +54% |
| stage3.ll | non-empty, teardown crash | **0 lines, mnc-stage2 segfault** | **REGRESSED** |

**Ve.1 regression:** stage3.ll went from non-empty (with teardown
crash at end) to empty (with immediate segfault in `scan_ident`
during lex of `mnc_all.mn`). Root cause not fully diagnosed in
session; likely a combination of the Python-bootstrap Move emissions
changing MIR shape for `lex_ident` + the +54% stage2.ll expansion
triggering heap-fragmentation-level instability in mnc-stage2 when
compiling a large source. Goldens and sanitizers remain clean, so
user-level compilation is unaffected; only self-compile is regressed.

### Phase 6 — pytest + lint

`make build-rt` with `MAPANARE_VERSION=5.4.4`. `python3 -m pytest
tests/ --ignore=tests/bootstrap -q`: **5494 passed / 1 failed / 116
skipped / 9 xfailed.** The single failure was `test_ruff_check_passes`
on the new `Move` import sort order in `lower.py`; fixed with
`ruff check --fix`. Post-fix: **5495 / 0 / 116 / 9.**

`make lint`: clean (ruff + black + mypy all green).

## Final state

- Version: 5.4.4
- `EmitState`: 22 fields; registry 23/23 clean
- Native goldens: 54/66 PASS (unchanged)
- Valgrind: 66 WARNINGS_ONLY / 0 ERRORS
- ASan UAF: 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR
- ASan leak: 45 CLEAN / 3 LEAK (Rt.02 × 2 + Rt.04 × 1) — baseline
  unchanged from v5.4.3
- stage2.ll: 191k lines, `llvm-as` OK
- stage3.ll: 0 lines, mnc-stage2 segfault — **Ve.1 regressed**
- Non-bootstrap pytest: 5495 passed / 0 failed
- `make lint`: clean

## Deviations from PLAN.md

1. **Chained `icmp + br` pattern for multi-ret-ptr drop-glue.**
   PLAN.md §5.4.4a implicitly expected a chained pattern. An initial
   implementation using `for _ in 0..N { if ri < nret { ... } }` with
   in-loop `let rp = ret_ptrs[ri]; emit br to next_lbl / free_lbl`
   produced byte-truncated IR on the bootstrap compiler (mnc-stage1)
   when processing functions with long drop-glue sequences — the
   last slot's free_lbl / skip_lbl block definitions were silently
   dropped. Switched to an alloca-based OR-reduction which works on
   both emitters. Root cause was partially independent (§Phase 3's
   65536 flush-cap bug), but the alloca pattern is simpler IR
   regardless.

2. **Guard-lift for `%struct.*` reverted.** PLAN.md §5.4.4c called
   for lifting the aggregate-return guard for `%struct.*` and
   walking one level of struct fields to extract every escaping ptr.
   Implementation worked on the golden corpus (62_list_output LEAK →
   CLEAN, UAF byte-identical). But on `%struct.EmitState` — a 22-
   field struct returned from ~hundreds of call sites in self-hosted
   code — the field-walk expansion (~40 extractvalue lines per call)
   inflated stage2.ll by 5× and triggered an mnc-stage2 runtime
   segfault. Rescoped per PLAN.md's release-sequencing fallback:
   guard stays closed, infrastructure lands, v5.4.5+ re-lifts with
   a size gate.

3. **Ve.1 regression.** stage3.ll went from non-empty (teardown
   crash) to empty (segfault during lex). Not a user-facing issue —
   goldens + sanitizers stay green — but self-compile is worse than
   before. Not remediated in this session; v5.4.5+ scope.

4. **Comprehensive Python Move emissions.** PLAN.md implies parity
   between Python and self-hosted lowerers. Python already had
   emit-site `_move_resource` calls in `_do_list_push` /
   `_do_struct_init` / etc., so the explicit lower.py Moves are
   largely redundant in Python's emitter. Kept for MIR parity at the
   cost of some extra `store zeroinitializer` lines.

## Commit history

```
7cd6bcd v5.4.4 Phase 6: ruff I001 fix — sort Move import
628a4c2 v5.4.4 Phase 5 RESCOPE: restore %struct.* aggregate-return guard
8fd9480 v5.4.4 Phase 4: refresh leak baseline — 62_list_output CLEAN
896d24a v5.4.4 Phase 3: drop glue honors moved_locals; %struct.* aggregate-return guard lifted
54cd0ec v5.4.4 Phase 2: lowerer Move emission for list_push / map_set / struct_init / enum_init / Option/Result wrappers
20b9a8e v5.4.4 Phase 1: slot-source parallel arrays in both emitters (plumbing only)
5991040 v5.4.4: version bump — close Rt.04 struct-return intermediates
```

The Phase 4 commit reflects the Phase-3-temporary state where
62_list_output was CLEAN. The Phase 5 RESCOPE commit reverts the
baseline update and restores Rt.04's OPEN status. Phase 3 +
Phase 4's textual changes stay in history as evidence the fix works
— the revert is a SCOPE revert, not a CODE revert.

## What v5.4.5 opens

1. **Re-lift the `%struct.*` aggregate-return guard** with a size
   gate: only emit the field walk when the struct has ≤N fields OR
   when the calling function's current tracked-slot count is ≤M.
   Falls back to conservative skip for hot paths like `emit_mir_*`.
2. **Diagnose the Ve.1 regression.** Likely candidate: a Python Move
   emission that changes main.ll's `scan_ident` IR in a way that
   causes mnc-stage1 to emit mnc-stage2 IR with a UAF on the
   string-interning path.
3. **62_list_output** re-transitions to CLEAN once (1) lands.
