# v4.32.0 Session Report — 2026-04-11

## Verdict
- Self-graded aggregate: ~9.3 (maintains recovery-arc level; zero new features, zero regressions)
- CARRY_FORWARD.md rows closed: #33, #34, #35 (self-hosted side), #32 (verified)
- CARRY_FORWARD.md rows opened: #49 (Viper V1, tracked v4.33.0), #50 (Viper M5, tracked v4.33.0)
- Panel items closed: 9 of 9 HIGH/MEDIUM from v4.31.0 docket

## Completed
- **Phase 1.1** — `runtime/native/mapanare_core.c:1011-1042`: `__mn_list_get`/`__mn_list_set` abort on OOB with diagnostic. `tests/runtime/test_list_bounds.py` (9 tests). `docs/cookbook.md` bounds note.
- **Phase 1.2** — `mapanare/self/emit_llvm.mn`: `get_fn_attrs` 25 → ~90 entries + new `get_fn_ret_prefix` (13 allocators). `mapanare/self/emit_llvm_ir.mn`: `emit_add`/`sub`/`mul` emit `nsw`. `__mn_map_new` 3-arg → 4-arg. `mnc_all.mn` + `main.ll` regenerated. Stage2.ll: noalias 0→22, nsw 0→1007, willreturn 0→188.
- **Phase 1.3** — `.reviews/CARRY_FORWARD.md`: dual-closure schema (PY/SH columns), rows #30-#35 updated, rows #49+#50 added.
- **Phase 2.1** — `git rm runtime/native/libmapanare_rt.a` + `mapanare/self/stage2.ll`. `.gitignore` updated. New `make check-no-tracked-binaries` CI gate.
- **Phase 2.2** — `mapanare/emit_llvm_text.py`: `_emit_drop_glue` 300→48 lines (dispatcher) + 8 helpers. Byte-identity verified.
- **Phase 2.3** — `runtime/native/mapanare_io.c`, `mapanare_db.c`, `mapanare_html.c`: `mnstr_to_cstr` consolidated to `mapanare_internal.h`. `len<0` crash window closed.
- **Phase 2.4** — `mapanare/bind.py`: struct String fields auto-unwrap via `@property`. `_py_annotation_for` raises `BindError` on unknown types.
- **Phase 2.5** — `runtime/native/mapanare_core.c`: `mn_signal_recompute` under lock. Recursive POSIX mutex. `tests/runtime/tsan/signal_recompute_stress.c` TSan-clean.
- **Phase 2.6** — `.github/workflows/ci.yml`: 5 gates get `if: always()`. `scripts/check_changelog_honesty.py` + `check_no_hollow_features.py`: `.git`-absent fallback to `grep -rl`.

## Carry-forward closed
- Row #32 (list `bitcast`): PY v4.30.0 / SH v4.32.0 verified (only ptr→ptr no-op remains)
- Row #33 (nsw): PY v4.30.0 / SH v4.32.0 — `grep -c ' nsw ' /tmp/stage2.ll` = 1007
- Row #34 (__mn_map_new arity): PY v4.30.0 / SH v4.32.0 — 4-arg declare+call
- Row #35 (noalias/willreturn): PY v4.30.0 / SH v4.32.0 — 22 noalias, 188 willreturn

## Carry-forward still open
- Row #30 (`i64*` opaque pointer): SH OPEN — one live `i64*` at `emit_llvm.mn:528`. Tracked to v4.33.0.
- Row #31 (`void ()*` opaque pointer): SH OPEN — one live `void ()*` at `emit_llvm.mn:949`. Tracked to v4.33.0.
- Row #49 (drop-glue skip-struct-ret, Viper V1): OPEN — Phase 2.2 was a pure refactor, could not remove the early return without changing IR. Tracked to v4.33.0.
- Row #50 (agent destroy message leak, Viper M5): OPEN — ~20-line runtime change. Tracked to v4.33.0.
- Rows A1-A9: unchanged from v4.31.0 (DEFERRED to v5.x).

## Measurements

| Metric | Before (v4.31.0) | After (v4.32.0) | Delta |
|--------|------------------:|------------------:|------:|
| main.ll lines | 186,681 | 186,681 | 0 |
| stage2.ll lines | 111,429 | 113,211 | +1,782 |
| Fixed-point diff | 69 | 69 | 0 |
| Golden tests | 44/44 | 44/44 | 0 |
| Stage2 modules | 11/11 | 11/11 | 0 |
| noalias in stage2.ll | 0 | 22 | +22 |
| nsw in stage2.ll | 0 | 1,007 | +1,007 |
| willreturn in stage2.ll | 0 | 188 | +188 |
| mnc-stage1 size | 3,302,024 | 3,322,664 | +20,640 |
| _emit_drop_glue lines | ~300 | 48 (dispatch) | -252 |

## Decisions Made
- **Decision 1 (drop-glue extraction scope)**: strict refactor, no behavior changes. Verified with `diff main.ll.before main.ll.after` = 0 lines.
- **Decision 2 (Viper V1 closure path)**: Path B — kept the early return, added CARRY_FORWARD.md row #49 tracking to v4.33.0. Phase 2.2 was a pure refactor; removing the early return would change emitted IR.
- **Decision 3 (self-hosted semantic mirror)**: ported every Python `_RUNTIME_FN_ATTRS` entry with a direct mapping (~90 entries). For runtime symbols without a self-hosted counterpart, used conservative defaults (nounwind only).
- **Signal mutex made recursive** (Phase 2.5): `PTHREAD_MUTEX_RECURSIVE` on POSIX to allow `compute_fn` to call `__mn_signal_get` (which re-acquires the lock) without deadlock. Windows `CRITICAL_SECTION` was already recursive.

## Verification Results
- `scripts/test_native.py --stage1 mapanare/self/mnc-stage1`: 44/44 pass
- `scripts/ir_doctor.py stage2`: 11/11 modules valid
- `scripts/verify_fixed_point.sh`: 69 diff lines / 113,211 (0.061%), within threshold=100
- `scripts/check_no_hollow_features.py`: clean (3 steps)
- `scripts/check_changelog_honesty.py`: clean
- `scripts/check_docs_drift.py`: clean (133 blocks)
- `scripts/check_silent_skips.py tests/`: clean
- `make check-runtime-sources`: clean
- `make check-no-tracked-binaries`: clean
- TSan signal_recompute_stress: 4 threads x 5000 iterations, zero races
- `tests/runtime/test_list_bounds.py`: 9/9 pass
- `tests/bind/test_python_binding.py::test_unknown_type_raises_bind_error`: pass
- `tests/llvm/test_drop_glue.py`: 6/6 pass

## Tool discipline retrospective
- Culebra: baseline save at session start (`.culebra/v4.32.0-start.json`), metrics snapshots after Phase 1.2. No triage or scan commands run — the Phase 1.2 changes were attribute-level, not IR-structural.
- Raw commands: `gcc -c`, `grep -c`, `diff`, `wc -l` used for proof collection. All proofs are reproducible from the commit chain.

## Next Session Should Start With
- Read `docs/roadmap/v4/v4.33.0/PLAN.md` (first new language feature in 7 releases: `?` operator)
- Read `docs/roadmap/v4/v4.33.0/PROMPT.md`
- Delta review mandatory (Coral primary) per `REVIEW_CADENCE.md`
- Sweep 2-3 LOW items from v4.31.0 panel (rows #30, #31 are quick 1-liners)
