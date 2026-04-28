# v5.4.0 Session Report — Own.1 Phase 2: Self-Hosted Drop-Glue Infrastructure

**Date:** 2026-04-23
**Status:** READY TO TAG
**Scope:** Rescoped at Phase 0 from "close 11 Sh.2 goldens (54/66 → 65/66)"
to **"memory-correctness infrastructure, 0 new goldens"** — see
`RESCOPE.md` for details. Sh.2 was discovered to be already closed at
v5.3.3 baseline; v5.4.0 ships the infrastructure that prevents its
recurrence and closes Viper's 28-panel Own.1 Phase 2 carry-forward.

## Starting state

- Version: 5.3.3
- Native goldens: **54/66 PASS** (12 fail: 5 Sh.4 async + 5 Sh.6 tensor
  + 1 Sh.7 closure-typed + 1 B bootstrap-also-fails)
- Valgrind: 66 WARNINGS_ONLY, 0 ERRORS
- ASan: 55 CLEAN, 11 CRASH_NO_ASAN (the 11 currently-failing tests;
  **not** the 11 Sh.2 tests — those are all CLEAN)
- Fixed-point: stage2.ll `llvm-as` OK, stage3.ll empty (Ve.1 LOW)
- Own.1: Phase 1 CLOSED (v5.1.3 Cb.7), Phase 2 open

## What landed

### Phase 0 — baseline capture + rescope

Discovered via direct ASan + exit-code check that all 11 Sh.2 tests
from `docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md` (`13_fib`,
`19_nested_match`, `20_recursion`, `22_string_builder`,
`29_generic_impl`, `31_generic_multi`, `47_try_operator`,
`48_match_nested_exhaustive`, `49_match_guards`, `62_list_output`,
`63_else_sino`) already pass on every axis at v5.3.3 baseline.

Rescope documented in `RESCOPE.md`. Target: land the infrastructure
Viper has flagged for 28 panels while keeping goldens at 54/66 and
sanitizer numbers at baseline.

### Phase 1 — `Move` MIR instruction (both emitters)

- `mapanare/mir.py`: `Move(value: Value)` dataclass after `Phi`.
- `mapanare/emit_llvm_text.py`: `Move` in import list, `_disp[Move] =
  self._do_move`, `_do_move(i)` routes to the existing
  `_move_resource(i.value.name)`.
- `mapanare/self/mir.mn`: `Move(Value)` enum variant, `instr_move_val`
  accessor, `"move"` in `instr_kind` dispatch.
- `mapanare/self/emit_llvm.mn`: `"move"` kind routed to no-op stub
  (upgraded in Phase 4).

Goldens post: 54/66. Registry gate: 23/23 clean.

### Phase 2 — `EmitState` ownership slots

Four `List<String>` fields added to `EmitState`: `str_owned`,
`list_owned`, `boxed_owned`, `moved_locals`. Updates three registry
sites (struct decl, `build_internal_struct_list::make_entry`,
`register_all_internal_structs::register_internal_struct`). Reset at
the start of `emit_mir_function` alongside `current_ret_type`. Reg.1
gate (v4.143.0) caught one mismatch during development — fixed, clean.

Goldens post: 54/66. Registry gate: 23/23 clean.

### Phase 3 — Drop-glue helpers + `emit_mir_return` wiring

Three per-resource helpers in `mapanare/self/emit_llvm.mn`:

- `emit_drop_glue_strings(st, ret_base)` — loads and calls
  `__mn_str_free` for each owned String not in `moved_locals` or
  matching the returned value
- `emit_drop_glue_lists(st, ret_base)` — passes the alloca ptr to
  `__mn_list_free`
- `emit_drop_glue_boxed(st, ret_base)` — loads ptr and calls `free`

Plus `emit_drop_glue(st, ret_val, ret_ty)` dispatcher with a fast-path
no-op when all three owner lists are empty. `emit_mir_return` calls
`emit_drop_glue` ahead of every `ret` emission path (void, sret,
i32-truncated main, normal return, unreachable zeroinitializer).

**Simplifications vs Python:** no multi-block null-check branching
(runtime free fns tolerate null), no ret-ptr alias detection through
struct field extraction (returned local is identified by name match).

Goldens post: 54/66. IR diff for `13_fib` pre/post Phase 3: **4 lines,
all in the VERSION placeholder line of metadata** (`!0 = !{"5.3.2"}`
→ `!0 = !{"5.4.0"}`). Byte-identical otherwise — confirms the empty
owner lists make the helpers no-ops this release.

### Phase 4 — `"move"` kind handler populates `moved_locals`

Upgraded the Phase 1 no-op stub. The handler now:

1. Extracts the Value via `instr_move_val(inst)`
2. Strips the `%` prefix with `ret_val_base`
3. Returns early if already in `moved_locals` (idempotent)
4. Pushes the stripped name onto `moved_locals`

Lowerer Move emission deferred to v5.4.1 — shipping it here would
populate `moved_locals` while owner lists are still empty, producing
zero behavioral benefit. The three follow-on pieces (owner-list
population, lowerer Move emission, runtime free declarations) must
land together to meaningfully exercise the sanitizer HARD GATE.

Goldens post: 54/66. IR diff for `13_fib`: 0 bytes (Phase 3 vs Phase 4).

### Phase 5 — Sanitizer HARD GATE

| Metric | Baseline (v5.3.3→5.4.0 before edits) | v5.4.0 after edits | Delta |
|---|---|---|---|
| Goldens | 54/66 | 54/66 | 0 |
| Valgrind | 66 WARNINGS_ONLY, 0 ERRORS | 66 WARNINGS_ONLY, 0 ERRORS | 0 |
| ASan | 55 CLEAN / 11 CRASH_NO_ASAN | 55 CLEAN / 11 CRASH_NO_ASAN | 0 |
| 11 Sh.2 tests ASan-CLEAN | 11/11 | 11/11 | 0 |
| Fixed-point (stage2 llvm-as) | OK | OK | 0 |
| Fixed-point (stage3) | empty (Ve.1) | empty (Ve.1) | 0 (preserved) |
| Registry gate | 23/23 clean | 23/23 clean | 0 |

ASan diff between baselines: empty — every test classified identically
pre/post.

### Phase 6 — pytest + lint

- Non-bootstrap pytest: **5483 passed, 116 skipped, 9 xfailed, 0 failed**
  (after `make build-rt` rebuilt `libmapanare_rt.a` with
  `MAPANARE_VERSION=5.4.0` to satisfy `test_user_agent.py`).
- `make lint`: **clean** (ruff + black + mypy all green).

No new `tests/native/test_sh2_close.py` added. The 11 Sh.2 tests
already have golden-harness coverage + ASan coverage in the existing
sweep (all 11 CLEAN). Adding a dedicated pytest file would duplicate
coverage the existing harness already provides. Noted in `RESCOPE.md`.

### Phase 7 — benchmarks

Skipped. IR output is byte-identical except for the VERSION string;
there is nothing for benchmarks to measure. A CPU-isolated run would
report the same numbers as v5.3.3 modulo noise.

### Phase 8 — release artifacts

- `PARITY_GAPS.md`: Own.1 Phase 2 row updated to CLOSED v5.4.0 + moved
  to Historical with detailed verification row.
- `RESCOPE.md`: documents the Phase 0 discovery + rescope.
- `SESSION_REPORT.md` (this file).
- Tag + push deferred pending explicit user approval per saved rule.

## Final state

- Version: 5.4.0
- Native goldens: 54/66 PASS (unchanged)
- Valgrind: 0 new ERRORS (66 WARNINGS_ONLY, byte-identical to baseline)
- ASan: 55 CLEAN / 11 CRASH_NO_ASAN (unchanged)
- Fixed-point: stage2 `llvm-as` OK (unchanged); stage3 still empty (Ve.1)
- Own.1 Phase 2: **CLOSED** — infrastructure landed, v5.4.1 will
  populate owner lists + add lowerer Move emission + runtime free
  declarations for end-to-end drop-glue

## Deferred

Tracked in `RESCOPE.md` §"Deferred to v5.4.1":

1. Owner-list population in emit_alloca / emit_copy / emit_wrap_some /
   emit_list_init / emit_closure_create
2. Lowerer Move emission in `lower.mn::lower_call_by_name`
3. Runtime free declarations in `declare_all_runtime`

These three must land together so the HARD GATE can cover the
end-to-end drop-glue path.

## Commit history

```
787e189 v5.4.0 Phase 4: populate moved_locals from Move kind handler
a5b98ef v5.4.0 Phase 3: drop-glue emission helpers + emit_mir_return wiring
088e838 v5.4.0 Phase 2: EmitState ownership-tracking slots
007e2bf v5.4.0 Phase 1: add Move MIR instruction variant (both emitters)
9cbd36b v5.4.0: version bump + rescope — Own.1 Phase 2 correctness infra
```
