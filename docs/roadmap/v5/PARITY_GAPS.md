# Python ↔ Self-Hosted Parity Gaps

> **What's in the Python bootstrap emitter (`mapanare/emit_llvm_text.py`
> + `mapanare/*.py`) that the self-hosted compiler
> (`mapanare/self/*.mn`) does not yet have.** One-stop inventory
> distilled from the v4.154.0 panel — Cobra, Viper, Mamba.
>
> Every item here means: when the Python bootstrap compiles a file,
> it gets optimization X. When `mnc-stage1` (or `mnc-win-x64.exe`)
> compiles the same file, it does not. The self-hosted compiler
> compiling *itself* doesn't benefit from its own optimizations
> unless those optimizations also live in `.mn` form.

**Opened:** 2026-04-21 (v5.0.1 prep)
**Source panels:** v4.154.0 (primary), v4.144.0 (baseline)
**Cadence:** update after every v5.x panel

---

## The headline gap — CLOSED (v5.0.4)

**Cb.15 — ABI.1 sret classifier is Python-only.** → **CLOSED v5.0.4.**

`mapanare/self/abi.mn` (75 LOC) ports the per-target ABI classifier.
`emit_llvm.mn::use_sret_return` replaces the 64B `is_byref_type_st`
threshold for return types. stage2.ll sret count: 2,263 → 4,112.
All 17-64B aggregates on SysV now correctly use sret. Cobra's
verification grep returns 26 matches (was 0 at v5.0.3).

**Rt.4 — Enum size hardcode.** → **CLOSED v5.0.6.**

`llvm_type_size` in `mapanare/self/emit_llvm.mn` returned a hardcoded
`16` for any `%enum.*` plus a comment claiming "enums are always
{i64, ptr}". Rt.1 (v4.124.0) made 2-slot inline enums `{i64,i64,i64}`
= 24B; the comment became actively false and the 16 became a latent
heap overflow waiting to activate once the self-hosted emitter began
constructing inline enums (Cb.15 at v5.0.4). v5.0.6 returns 24 as
the safe upper bound across all three layouts and rewrites the
comment to match reality.

---

## Inventory by domain

### ABI / Codegen

| ID | Python has | Self-hosted has | Panel | Target |
|---|---|---|---|---|
| ~~Cb.15~~ | ~~`abi.py` + `_use_sret` per-target classifier~~ | ~~`abi.mn` + `use_sret_return`~~ | ~~Cobra v4.154.0~~ | ~~**v5.0.4 CLOSED**~~ |
| ~~Cb.9a~~ | ~~`module_path` field on TypeExpr~~ | ~~`bare_type_name()` + resolve_type_expr classification~~ | ~~Cobra v4.144.0+v4.154.0~~ | ~~**v5.0.5 CLOSED**~~ |
| ~~Gr.2~~ | ~~`named_type (DOT NAME)*` in grammar~~ | ~~Bootstrap grammar synced~~ | ~~Coral v4.136.0~~ | ~~**v5.0.5 CLOSED**~~ |
| ~~Rt.4~~ | ~~Correct enum size~~ | ~~`llvm_type_size` returns safe upper bound 24 for all `%enum.*`; comment documents the three layouts~~ | ~~Rattler v4.154.0~~ | ~~**v5.0.6 CLOSED**~~ |
| ~~Own.1~~ | ~~`_do_call` blanket-move + `_move_resource` + `_emit_drop_glue`~~ | ~~Self-hosted `Move` MIR variant, ownership slots in `EmitState` (str/list/boxed_owned + moved_locals), drop-glue helpers + `emit_mir_return` wiring. Owner-list population + lowerer Move emission + runtime free declarations deferred to v5.4.1.~~ | ~~Viper all panels (28 releases)~~ | ~~**v5.1.3** Phase 1 CLOSED (Cb.7 workaround); **v5.4.0** Phase 2 CLOSED (infrastructure landed — see v5.4.0/RESCOPE.md); full borrow checker v6.0~~ |

### Optimizer (MIR passes)

The v4.152.0 E8 audit re-evaluated four passes that were disabled at
v4.111.0. Results:

| Pass | Python | Self-hosted | Status | Target |
|---|:---:|:---:|---|---|
| `strength_reduce` | ON | OFF | Zero-ROI both sides; LLVM instcombine covers — parity deferred | — |
| ~~`inline_small_functions`~~ | ~~ON~~ | ~~ON~~ | ~~**In.1** CLOSED v5.1.2: `replace_uses_in_instr` renames caller's dest to fresh prefixed name~~ | ~~v5.1.2~~ |
| `licm` | OFF | OFF | **Li.1** OPEN: unit tests pass but live goldens regress (05_for_loop, 21_list_ops, 33_break_continue). Needs fixpoint + preheader insertion. | v5.2 |
| ~~`escape_analysis`~~ | ~~ON~~ | ~~ON~~ | ~~**Ea.1** CLOSED v5.1.2: analysis ported to self-hosted (codegen annotation deferred — no alloc_kind on Instruction enum)~~ | ~~v5.1.2~~ |

> Cobra v4.154.0 line 41: *"This is a Python-emitter-only fix. The
> self-hosted emitter has no classifier, no `_use_sret`, and still
> returns everything by value up to the old `_BYREF_BYTES = 64`
> threshold."*

### Emitter — enum layout (historical reference)

Prior parity gap, already closed — documented here so we remember
the shape:

| ID | Gap | Closed |
|---|---|---|
| Cb.5 / Rt.1 | `_enum_inline` Python-only; self-hosted emitted `{i64, ptr}` + heap | **v4.140.0** — ported `_enum_inline` to `emit_llvm.mn` with `EmitState.enum_inline_slots` registry |

### Memory-safety residuals

Not strictly parity gaps (both emitters produce the same buggy code),
but Viper v4.154.0 resurfaced these:

| ID | Symptom | Scope | Target |
|---|---|---|---|
| ~~**Ge.1r**~~ | ~~4 valgrind ERRORS on goldens 26/29/30/31 — "Invalid read of size 16|8" in generics monomorphization~~ Zero-init fix in `try_monomorphize_enum` / `try_monomorphize_struct` at v5.1.1. Valgrind sweep at v5.3.0 confirms 0 ERRORS on all 4 goldens. | ~~Same root-cause class as Own.1~~ | ~~**v5.1.1 CLOSED**~~ |
| ~~Own.1~~ | ~~`register_struct` / `register_enum` latent UAFs~~ Phase 1 closed: Cb.7 zero-after-push workaround applied at both sites. Phase 2 (Move instruction + drop-glue in self-hosted emitter) deferred to v5.1.4+. General borrow checker: v6.0. | ~~Specific UAF class: CLOSED. General ceiling: OPEN~~ | ~~**v5.1.3** Phase 1~~ |
| Ve.3 | **CLOSED v5.6.9** — drop-glue UAF on `List<Enum>` returns. `clone_instr_for_inline`'s List<Instruction> return path freed every tracked heap-boxed payload, leaving dangling ptrs in the returned list. Caller dereferenced via `instr_dest(inst)` and read garbage Value names → `__mn_str_concat` OOM. Same multi-level aliasing class as Rt.04 (List<String> in returned struct). 25-LOC RESCOPE fix in `emit_llvm.mn:4763`: skip drops conservatively when `ret_ty == llvm_list_rt() && len(boxed_owned) > 0`. Cost: intermediate boxes leak (accepted per v5.6.6 precedent — UAF prevention > leak prevention). Multi-level alias analysis is v6.0 borrow-checker scope. `mnc-stage2 /tmp/p1.mn` was 0-line OOM since v5.6.4 → 215 lines `llvm-as` clean RC=0. | n/a — fix shipped | **v5.6.9 CLOSED** |
| Ve.4 | **CLOSED v5.6.11** — match-arm lowering produced empty BasicBlocks in self-hosted compiled lowerer. Root cause: `emit_index_get` / `emit_index_set` inline fast paths (i64/double/ptr) used a constant 8-byte stride GEP, while `__mn_list_push` writes used the runtime `elem_size` field from the list struct (= 384 for the 7 Ve.2 residual `List<Int> = []` floor sites including `build_match_arms`). The second `indices.push` in `build_match_arms` wrote at byte offset 384; the inline GEP-i64 read at byte offset 8; mismatch returned heap-pointer-shaped intra-buffer spillage from the first push. `set_block(s, garbage_int)` then made `emit_instr`'s bounds check silently no-op the second arm's instructions. Fix: 14 LOC across the two emit sites — load `list.elem_size` (struct field 3) at runtime, compute `offset = idx * elem_size`, then `getelementptr inbounds i8, ptr %data, i64 %offset`. SROA elides the runtime load when elem_size is a known constant. Hero metric: `verify_fixed_point.sh` reaches NEAR (0.002% diff) for the first time since v5.6.4 (7 releases). Goldens 64/66 preserved; full sanitizer gate clean. Lk.1 stays open (v6.0) — the fix does not surface or close Lk.1 because allocations remain at elem_size=384 for the residual sites. See `docs/roadmap/v5/v5.6.11/SESSION_REPORT.md`. | n/a — fix shipped | **v5.6.11 CLOSED** |
| Lk.1 | **CLOSED v5.6.12** — closed at the structural root cause, not as multi-level alias analysis (which would have been v6.0). The fix is destination-passing semantics in `lower.mn::lower_let`: when value is a list literal with an annotated element type, pre-compute the var's alloca name and lower the `ListInit` directly into it via the new `lower_list_typed_into(st, elements, hint, dest_name)` helper. Skip the post-emit `Alloca` + `Store` pair (those would create the duplicate `%t<N>.addr` alloca + the copy that was the alloca-aliasing leak). The emitter's `dn + ".addr"` convention then derives the same alloca name as the let var — one alloca, one tracking entry, no copy, no leak. Mirrors rustc's `PlaceRef`-based codegen (result-location semantics). With Lk.1 closed at the source, the v5.6.10 scalar gate was applied in the same release: `if elem_ty.kind == TK_UNKNOWN() { if elem_sz_n < 384 { elem_sz_n = 384 } }` replaces the unconditional floor. Closes all 7 Ve.2 residual `__mn_list_new(i64 384)` sites. **Hero metric**: 65_list_int_indexing LSan **CLEAN** (was: would leak 80 bytes if scalar gate applied without Lk.1 fix); floor sites **7 → 0**; stage2.ll **−431 lines** (eliminated duplicate allocas + stores). Adjacent finding: 62_list_output's pre-existing Rt.04 leak unmasked by the stack-layout shift (LSan's "still reachable" heuristic was relying on a stale pointer in the duplicate alloca); baseline TSV refreshed (9 obj/141 B → 13 obj/346 B). The leak source is unchanged; closing it remains v6.0 work. See `docs/roadmap/v5/v5.6.12/SESSION_REPORT.md`. | n/a — fix shipped | **v5.6.12 CLOSED** |

### Benchmark reporting (Mamba v4.154.0)

Not compiler parity but listed for completeness — all three are
one-line to small fixes Mamba has now flagged 2-3 times:

| ID | Symptom | Target |
|---|---|---|
| ~~Bn.2~~ | ~~Geomean arithmetic wrong~~ `run_benchmarks.py` now computes `geomean()` from raw per-benchmark ratios and embeds it in JSON `"geomean_ratios"` field. Summary table appends Mn/Lang ratios. | ~~**v5.1.2 CLOSED**~~ |
| ~~Bn.3~~ | ~~JSON `"version": "4.125.0"` hardcoded~~ `benchmarks/cross_language/run_benchmarks.py` reads VERSION file; per-run JSON now carries the live version. | ~~**v5.0.6 CLOSED**~~ |
| ~~Bn.4~~ | ~~C `struct_alloc.c` uses malloc+free~~ Rewritten to return struct by value (stack return) matching Rust/Mapanare. No `malloc`/`free` in hot loop. | ~~**v5.1.2 CLOSED**~~ |

### Documentation drift (Boa v4.144.0+v4.154.0)

| ID | Symptom | Severity | Target |
|---|---|---|---|
| ~~Bo.12-table~~ | ~~README benchmark table~~ README.md table now shows v4.153.0 numbers (168× Py, 0.85× Go, 1.17× Rust, 0.96× C); retracted "1.12×" / "4.86×" gone. | ~~**v5.0.6 CLOSED**~~ |
| ~~Bo.12-i18n~~ | ~~Localized READMEs~~ `docs/README.{es,pt,zh-CN}.md` version badges bumped 5.0.0 → 5.0.6; test-count badges 5534+ → 5720+; benchmark prose already consistent. | ~~**v5.0.6 CLOSED**~~ |

### Test-coverage gaps (Rattler + Anaconda v4.154.0)

| ID | Gap | Target |
|---|---|---|
| ~~Cb.6-test~~ | ~~Regression gate missing~~ `tests/llvm/test_enum_inline_parity.py::test_self_hosted_rejects_typed_pointer_slot` structurally gates the `ends_with("*")` rejection. | ~~**v5.0.6 CLOSED**~~ |
| ~~An.9~~ | ~~E1 unified-return no IR-shape test~~ `tests/llvm/test_unified_return_shape.py` asserts single switch in `@area` pre-opt; single switch in `@main` post-O2 when `opt` is available. | ~~**v5.0.6 CLOSED**~~ |
| ~~An.10~~ | ~~Test-count drift~~ `scripts/count_tests.py` + `make count-tests` give a deterministic `def test_*` count. | ~~**v5.0.6 CLOSED**~~ |

### Build-script hygiene

| ID | Issue | Target |
|---|---|---|
| ~~Dr.1-mutation~~ | ~~build_stage1.py mutates SELF_DIR~~ Substitution happens into `tempfile.TemporaryDirectory`; compile reads from tempdir; source tree stays pristine. | ~~**v5.0.6 CLOSED**~~ |

### Process / tracking (Cobra v4.154.0)

Not technical debt, but a tracking failure Cobra called out:

- **Ledger undercount** — v4.153.0 DOCKET_LEDGER claimed 8 open
  dockets; Cobra verified the honest count was 11+ (Cb.15, Cb.9a,
  Own.1 all absent from tracking). 27% undercount.
- **Fix:** this `PARITY_GAPS.md` document exists specifically to
  catch this failure mode. Every panel release going forward audits
  whether items marked closed in SESSION_REPORTs are actually
  verifiable via grep against HEAD.

### Feature gaps (both emitters lack)

Not parity gaps (both missing), but panel-visible:

- **Sh.4 (tensor reshape)** — tensor reshape — v5.x feature track
- **Sh.5** — mutable views — v5.x feature track

> Note: the Sh.4 ID appears in two namespaces. The bullet above
> refers to the *tensor reshape* feature gap (both emitters lack
> it). The Sh.4 in `docs/known_issues.md` historically referred
> to *async self-hosted lowering*, which **CLOSED v5.5.4–v5.5.7**
> across the coroutine arc — `presplitcoroutine` + the
> `@llvm.coro.id/begin/save/suspend/end` pipeline (v5.5.4),
> scheduler-driven `AwaitSuspend` (v5.5.5), scheduler-driven
> `BlockOn` + main lifecycle (v5.5.6), drop-glue + fixed-point
> hardening (v5.5.7). All 5 Sh.4 goldens
> (55/56/57/58/59_async_*) compile through `mnc-stage1` and
> are valgrind / ASan / LSan / TSan clean.
- ~~**Sh.6**~~ — ~~tensor literals / indexing / broadcast / slicing /
  reductions in self-hosted~~ — **CLOSED v5.6.3** (phases 1-4 closed
  across v5.6.0 / v5.6.1 / v5.6.2 / v5.6.3). All 5 tensor goldens
  (49/50/51/52/53) run byte-identical to expected output through
  `mnc-stage1 → llc → clang`. Grep verification:
  `grep -l "lower_tensor_slice\|tensor_reduction" mapanare/self/lower.mn`
  returns `mapanare/self/lower.mn`. Stepped slicing (`a[::2]`) and
  tensor reshape / mutable views remain out of scope — tracked
  separately as v5.x / v6.0 feature work.
- ~~**Sh.7**~~ — ~~closure-typed parameters — v5.x feature track~~ —
  **CLOSED v5.7.0**. Self-hosted `parser.mn` now extracts multi-param
  lambdas from `(a, b) => ...` (was: only single Ident); `lower.mn`
  routes calls through fn-typed locals via indirect-call SSA name;
  `emit_llvm_ir.mn::emit_call_ir` recognises `%`-prefixed callees;
  `mir_opt.mn` renames Call's fn_name during inlining. Goldens
  **65/66 → 66/66 — first time in project history**.
- **Sh.9a** — async test harness — v5.x feature track
- ~~**Perf.2**~~ — lazy thread creation in coro scheduler — **CLOSED
  v5.1.4** (default-settings async geomean 2.3 → 1.19 ms, 0.91× Go
  without env var; `MAPANARE_ASYNC_THREADS` preserved as optional
  override)

---

## Why this doc exists (process)

Cobra v4.154.0 noted a 27% undercount in the v4.153.0 `DOCKET_LEDGER`:
three carry-forward items (Cb.15, Cb.9a, Own.1) were opened in
earlier SESSION_REPORTs and quietly dropped before the panel. The
ledger tracked 8 open; the honest count was 11.

The fix: a human-readable parity inventory that lives in the roadmap,
not buried in one release's docket ledger. When an item closes, it
moves from the "Inventory" table into the "Historical" section.

The ledger still exists (in per-release `DOCKET_LEDGER.md`) for
severity/status detail. This doc is the *tracking* layer above it
that Cobra's review said we need.

---

## Close policy

An item closes when:

1. The self-hosted `.mn` implementation exists and is invoked from
   the active optimizer/emitter pipeline
2. A test under `tests/llvm/` or `tests/mir_opt/` asserts the Python
   output and the self-hosted output are byte-identical on a
   representative corpus
3. The item moves to the "Historical" section with closure release
   cited

An item does **not** close just because a SESSION_REPORT says it's
done. Cobra's v4.154.0 finding — three items "closed" in
SESSION_REPORTs but absent from the ledger — is the failure mode
this policy exists to prevent.

---

## Historical (closed items)

| ID | What | Closed | Verification |
|---|---|---|---|
| **Rt.4** | `llvm_type_size` for `%enum.*` returns 24 (safe upper bound across {i64,ptr}, {i64,i64}, {i64,i64,i64} layouts). Stale "always {i64, ptr}" comment replaced with the three-layout breakdown. | **v5.0.6** | `grep -n 'always {i64, ptr}' mapanare/self/emit_llvm.mn` → 0. Rt.1 heap-overflow latent path neutralised. |
| **Bn.3** | `benchmarks/cross_language/run_benchmarks.py` reads `VERSION` at import time; JSON `"version"` field + arg-parser description both use the live value. | **v5.0.6** | `grep -n '"4.125.0"' benchmarks/cross_language/run_benchmarks.py` → 0 (outside docstring). |
| **Bo.12-table** | README benchmark table shows 168× Py / 0.85× Go / 1.17× Rust / 0.96× C (v4.153.0 official numbers). | **v5.0.6** | `grep -rn "1.12x\|1.12×\|4.86×" README.md docs/README.*.md` → 0. |
| **Bo.12-i18n** | Localized READMEs (`docs/README.{es,pt,zh-CN}.md`) version badges 5.0.0 → 5.0.6; test badges 5534+ → 5720+. | **v5.0.6** | `grep -n '5.0.0-blue\|5534' docs/README.*.md` → 0. |
| **Cb.6-test** | Regression gate structurally asserts self-hosted `type_fits_inline_slot` rejects `*`-suffixed types. | **v5.0.6** | `pytest tests/llvm/test_enum_inline_parity.py -v` → 2 passed. |
| **An.9** | `tests/llvm/test_unified_return_shape.py` gates E1 structure (single switch in `@area` pre-opt; sret on `@make_shape`; post-O2 single-switch when `opt` available). | **v5.0.6** | `pytest tests/llvm/test_unified_return_shape.py -v` → 2 passed / 1 skipped (opt on Windows). |
| **An.10** | `scripts/count_tests.py` + `make count-tests` emit deterministic `def test_*` count. | **v5.0.6** | `python scripts/count_tests.py` → 4209 (expands to ~5720 pytest-collected). |
| **Dr.1-mutation** | `scripts/build_stage1.py` uses `tempfile.TemporaryDirectory` for version-placeholder substitution; source tree never mutated. | **v5.0.6** | `grep -n "mn_file.write_text\|SELF_DIR.*write_text" scripts/build_stage1.py` → 0 for .mn files. |
| **Cb.15** | ABI.1 sret classifier ported to self-hosted (`abi.mn` + `emit_llvm.mn::use_sret_return`). stage2.ll sret count 2,263 → 4,112. SysV 16B threshold replaces 64B for returns. | **v5.0.4** | `grep -c 'sret\|classify_return\|_use_sret' mapanare/self/emit_llvm.mn` → 12; `grep -c 'abi_classify' mapanare/self/abi.mn` → 2. Fixed-point NEAR (4 diff, Dr.1 only). Sanitizers: 0 new. |
| **Cb.9a** | Qualified type refs: `bare_type_name()` helper in `semantic.mn` extracts last component from dotted names for primitive/builtin classification. `resolve_type_expr` uses bare name for `is_primitive_type` / `is_builtin_generic`, preserves full dotted name in TypeInfo for emitter. | **v5.0.5** | `grep -c 'bare_type_name' mapanare/self/semantic.mn` → 4. 12 parser tests in `tests/parser/test_qualified_types.py`. |
| **Gr.2** | Bootstrap grammar synced: `bootstrap/mapanare.lark` `named_type` / `generic_type` accept `NAME (DOT NAME)*`, matching main grammar (done v4.139.0). | **v5.0.5** | `grep 'DOT NAME' bootstrap/mapanare.lark` → 2 rules. 12 parser tests. |
| Cb.5 / Rt.1 | `_enum_inline` ported to self-hosted `emit_llvm.mn` | **v4.140.0** | — |
| **In.1** | `inline_small_functions` SSA rename: `replace_uses_in_instr` renames caller's dest to `%_inlN_M_dst` and updates all downstream uses. Pass enabled in both Python and self-hosted. | **v5.1.2** | `pytest tests/mir_opt/test_inline_rename.py -v` → 4 passed. |
| **Li.1** | LICM: unit tests pass (`test_licm_no_duplicate.py` → 3 passed), but live golden tests regress. Pass remains disabled in both pipelines. Li.1 OPEN for v5.2. | **v5.1.2** (partial — tests added, pass NOT enabled) | `pytest tests/mir_opt/test_licm_no_duplicate.py -v` → 3 passed. Live goldens: 05_for_loop, 21_list_ops, 33_break_continue regress when enabled. |
| **Ea.1** | Escape analysis: self-hosted stub replaced with full `check_escape` analysis. Python `escape_analysis_promotion` sets `alloc_kind=STACK`. Self-hosted Instruction enum lacks alloc_kind field (codegen annotation deferred to v5.2+). | **v5.1.2** | `pytest tests/mir_opt/test_escape_analysis.py -v` → 7 passed. |
| **Bn.2** | `geomean()` function in `run_benchmarks.py`; JSON `"geomean_ratios"` field; summary table appends Mn/Lang ratios. | **v5.1.2** | `python3 -c "from benchmarks.cross_language.run_benchmarks import geomean; print(geomean([1.0, 4.0]))"` → 2.0. |
| **Bn.4** | `struct_alloc.c` returns struct by value (no malloc). Matches Rust/Mapanare methodology. | **v5.1.2** | `grep malloc benchmarks/cross_language/c/struct_alloc.c` → 0. |
| **Own.1** (Phase 1) | Cb.7 zero-after-push workaround applied to `register_struct` (lower.mn:330-336) and `register_enum` (lower.mn:364-369). Mirrors existing pattern at monomorphize sites (lines 1795-1798, 1997-1998). Python emitter already safe via `_do_call` blanket-move (line 3882). Phase 2 (Move instruction, `moved_locals` in EmitState, drop-glue in self-hosted emitter) deferred to v5.1.4+. Full borrow checker: v6.0. | **v5.1.3** | `grep -n 'Own.1' mapanare/self/lower.mn` → 2 matches (register_struct, register_enum). Valgrind: 0 ERRORS across 66 goldens. |
| **Own.1** (Phase 2) | `Move(Value)` MIR variant in both emitters; four ownership-tracking slots (`str_owned` / `list_owned` / `boxed_owned` / `moved_locals`) added to self-hosted `EmitState` with 23/23 Reg.1 gate clean; three drop-glue helpers (`emit_drop_glue_strings` / `_lists` / `_boxed`) plus the `emit_drop_glue` dispatcher in self-hosted `emit_llvm.mn`; `emit_mir_return` calls `emit_drop_glue` ahead of every `ret`. Python emitter's `_do_move` routes `Move` → `_move_resource`. Self-hosted emitter's `"move"` kind handler pushes the stripped local name onto `moved_locals`. Phase 0 baseline verified all 11 Sh.2 tests already pass (closed silently pre-release by v5.1.3 Cb.7 + v5.3.2 inliner); v5.4.0 ships the infrastructure that prevents Sh.2-shape regressions. Owner-list population + lowerer Move emission + runtime free declarations deferred to v5.4.1. Full borrow checker: v6.0. | **v5.4.0** | `git grep -n 'str_owned\|list_owned\|boxed_owned\|moved_locals\|emit_drop_glue\|Move(' mapanare/self/ mapanare/mir.py mapanare/emit_llvm_text.py`. Goldens 54/66 preserved. Valgrind: 0 new ERRORS. ASan: 55 CLEAN / 11 CRASH_NO_ASAN unchanged. 13_fib IR byte-identical pre/post except VERSION placeholder. Registry gate clean. See docs/roadmap/v5/v5.4.0/RESCOPE.md + SESSION_REPORT.md. |
| **Own.1** (Phase 2 — functional) | Shadow-slot architecture ported from Python (`_track_string`, `_track_boxed`, `_track_closure`). Owner lists populated at all heap-allocating emit sites: `emit_mir_call` dispatch covers runtime + user String-returning calls; `emit_binop +` covers String concat; `emit_interp_concat` tracks intermediates; `emit_list_init` registers list allocas (hoisted to entry-block prelude with zero-init so they dominate all drop-glue loads). Three new `EmitState` fields (`entry_prelude_lines`, `entry_block_body`, `in_entry_block`) with 24/24 Reg.1 gate clean. Drop-glue revised with per-slot `icmp eq ptr` + multi-block branch: `emit_drop_glue` extracts the returned data pointer once (via `extractvalue`) for scalar String / List / ptr returns, helpers skip the free when a slot aliases the ret ptr. Aggregate returns (struct / enum / Option / Result) conservatively skip all drops (trades leaks for UAF safety — v5.4.2 may add the recursive struct-field walk). Runtime free declarations for `__mn_str_free` / `__mn_list_free` / `free` added to `declare_all_runtime`. Lowerer Move emission skipped — escape detection makes it optional at this slice and `__mn_list_free` is non-deep so list-push doesn't risk String double-free. String literals intentionally NOT tracked (Python's `_mkstr` omits tracking too): they live in rodata, `__mn_str_free` is_heap=0 no-ops on them, and tracking each blew `get_fn_attrs`-sized functions quadratically. Full borrow checker: v6.0. | **v5.4.1** | Goldens 54/66 preserved. Valgrind 66 WARNINGS_ONLY / 0 ERRORS (baseline). ASan 55 CLEAN / 11 CRASH_NO_ASAN (baseline). 22_string_builder under ASan: prints `*****\n---\n`, exits 0. Narrow leak test (`greet() -> String`) under `detect_leaks=1`: 0 leaks. stage2.ll 165k lines, +33% vs baseline (within plan's R3 30-50% expectation). stage2 `llvm-as` OK; stage3 empty (Ve.1 baseline preserved). Non-bootstrap pytest 5488 passed / 0 failed. `make lint` clean. Registry 23/23 clean. See docs/roadmap/v5/v5.4.1/SESSION_REPORT.md. |
| **Own.1** (Phase 2 — functional + leak-clean + CI-gated) | `scripts/run_asan_leak_goldens.sh` compile+link+executes every golden under LSan (`detect_leaks=1:leak_check_at_exit=1`). Two targeted fixes: (1) `is_string_returning_builtin(fn_name)` helper + extended Phase 3.2 hook in `emit_mir_by_kind` "call" branch covers 13 builtins whose MIR dest defaults to `mir_unknown()` in `lower_call_by_name`'s generic path (read_file, sha256, regex_replace, http_get, base64_*, hmac_sha256, hex_encode, random_bytes, gpu_device_name, read_line, join, typeof) — closes 4 goldens × 9 leak objs / 202 B. (2) `emit_track_boxed(ep)` at `emit_enum_init`'s boxed-payload path closes 50_match_or_patterns's enum-payload box leak. Residual 4 leak goldens (22_string_builder loop-reassignment, 62_list_output struct-return intermediates, 39/40 GPU Mesa/Vulkan) documented as Rt.03 / Rt.04 / Rt.02 in `docs/known_issues.md` and grandfathered via baseline-comparison gate in `scripts/check_leak_summary.py`. `leak:mapanare_gpu_init` suppression trims 520 B of libcuda cuInit per run. `make leak-check` + `.github/workflows/sanitizers.yml` leak-check job ratify the sweep as a merge requirement. Full borrow checker: v6.0. | **v5.4.2** | Leak sweep 44 CLEAN / 4 LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0 RUN_FAIL / 0 regressions. UAF sweep 55 CLEAN / 11 CRASH_NO_ASAN preserved. Valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved. Goldens 54/66 preserved. stage2.ll 168952 lines (+1.8% vs v5.4.1), `llvm-as` OK. stage3 empty (Ve.1 preserved). Non-bootstrap pytest 5488 passed / 0 failed. `make lint` clean. See docs/roadmap/v5/v5.4.2/SESSION_REPORT.md. |
| **Own.1** (Phase 2 — infrastructure for Move-aware drop glue) | Three new `EmitState` fields (`str_owned_source`, `list_owned_source`, `boxed_owned_source`) — parallel arrays aligned index-for-index with the existing owner lists, carrying the bare SSA source name the slot was allocated for. Registry bump 22/22 clean. `emit_track_string` / `_boxed` populate the source entries; `emit_list_init` records the list-var's bare name. Python mirror: `_local_strings_source`, `_local_boxed_source`, `_list_vars_source` lists plus a new `_moved_locals: set[str]` attribute that `_move_resource` updates alongside the existing slot-zero logic. Lowerer Move emission in both `lower.mn` and `lower.py`: `Move(val)` is emitted after every resource-consuming operation — `list.push`, `map[k] = v` / `list[i] = v`, `StructInit` (per field), `EnumInit` (per payload arg), `Some(val)` / `Ok(val)` / `Err(val)`, `MapInit` literal (per k/v). Drop-glue helpers `emit_drop_glue_strings` / `_lists` / `_boxed` rewritten to accept `List<String>` of ret-ptrs; `is_moved` check consults the parallel source array. Also fixes a latent `emit_fn` entry-block-body flush cap of 65536 that silently truncated the drop-glue tail of large functions (raised to 1M). Guard-lift for `%struct.*` returns was implemented with a one-level field walk and reverted: the ~40 extractvalue lines per `%struct.EmitState`-returning call site inflated stage2.ll by 5× and triggered an mnc-stage2 runtime segfault (Ve.1 regression). v5.4.5+ re-lifts with a size gate. 62_list_output stays LEAK in this release; infrastructure is in place for the next release to close. Full borrow checker: v6.0. | **v5.4.4** | Leak sweep 45 CLEAN / 3 LEAK (Rt.02 × 2 + Rt.04 × 1, baseline unchanged from v5.4.3) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0 RUN_FAIL / 0 regressions. UAF sweep 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR preserved. Valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved. Goldens 54/66 preserved. stage2.ll 191k lines (+54% vs v5.4.3 from Phase 1 plumbing). stage2 `llvm-as` OK; **stage3.ll REGRESSED from non-empty-teardown-crash to 0-lines-segfault — Ve.1 regressed, not remediated this release**. Non-bootstrap pytest 5495 passed / 0 failed. `make lint` clean. Registry 23/23 clean. See docs/roadmap/v5/v5.4.4/SESSION_REPORT.md. |
| **Own.1** (Phase 2 — functional + leak-clean + CI-gated + loop-reassignment-clean) | New `EmitState.loop_depth: Int` (19th field, Reg.1 gate 24 → 25 clean) tracks nested-loop depth across MIR block emission; `emit_mir_basic_block` pushes on `for_body` / `while_body` / `mapfor_body` labels, pops at block end. Python `LLVMTextEmitter._loop_depth` + `_emit_fn` reset + push/pop around the `for bb in fn.blocks` loop provide parity. `emit_track_string` / `_boxed` / `_closure` (self-hosted) + `_track_string` / `_track_boxed` / `_track_closure` (Python) prepend a `load {slot_ty}, slot` + `@__mn_str_free` / `@free` when `loop_depth > 0`; outside loops the emission is byte-identical to v5.4.2. Zero-init in the entry-block prelude + null-tolerant runtime free fns make the first-iteration free a no-op without a runtime branch. Closes Rt.03: 22_string_builder 6 objs / 19 B → CLEAN; baseline TSV refreshed. D3 UAF risk (aliased copies + reassignment) did not materialize on the current corpus — UAF sweep byte-identical. Full borrow checker: v6.0. | **v5.4.3** | Leak sweep 45 CLEAN / 3 LEAK (Rt.02 × 2 + Rt.04, baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0 RUN_FAIL / 0 regressions. UAF sweep 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR preserved. Valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved. Goldens 54/66 preserved. stage2.ll 169280 lines (+0.19% vs v5.4.2), `llvm-as` OK. stage3 empty (Ve.1 preserved). Non-bootstrap pytest 5494 passed / 0 failed. `make lint` clean. See docs/roadmap/v5/v5.4.3/SESSION_REPORT.md. |
| **Own.1** (Phase 3 — Rt.06 tensor drop-glue CLOSED) | Self-hosted emitter ports Python's `_tensor_vars` / `_emit_drop_glue_tensors` pair. Two new `EmitState` fields (`tensor_owned` + `tensor_owned_source`) parallel to the existing str/list/boxed triples. New `emit_track_tensor` helper mirrors `emit_track_boxed`: zero-init slot in entry-block prelude, store of the tensor ptr after the alloc emit line, ownership-list push; loop-depth branch prepends `load ptr, slot` + `call void @__mn_tensor_free(ptr %prev.tens.N)` before the store so v5.4.3's loop-reassignment pattern works for tensors too (load-bearing for 53_linear_regression's 10-epoch loop × 4 fresh tensors). `is_tensor_allocating_fn(fn_name)` predicate enumerates 22 runtime fns (1 alloc + 1 slice + 8 broadcast + 8 scalar + 4 rscalar); post-emit injection in the generic `emit_mir_call` `Some(fe)` + `_` success branches covers all 20 binop fns without duplicating v5.6.2's emit logic. Direct injection at `emit_tensor_init` + `__mn_tensor_slice` special case. `emit_drop_glue_tensors` helper structurally parallel to `_boxed` — SSA prefix `t` (`%drop.tv.N` / `drop.tfree.N` / `drop.tskip.N`), `__mn_tensor_free` call. `emit_drop_glue_destroy` (v5.5.7 async cleanup) grows a fourth unconditional tensor loop. `emit_drop_glue` dispatcher: fourth `ret_tensor_ptrs` list; scalar ptr return + `%struct.*` ptr field walk dual-push same SSA into both `ret_box_ptrs` + `ret_tensor_ptrs` — each helper alias-checks its own slot list so the over-approximation is safe (no double-free possible, no missed-free on the correct helper). Baseline TSV flipped 49/50/51/52/53 from COMPILE_FAIL/LEAK-allowed to CLEAN-required. Full borrow checker: v6.0. | **v5.6.4** | Leak sweep 50 CLEAN / 3 LEAK (Rt.02 × 2 external driver + Rt.04 × 1, baseline-gated) / 1 COMPILE_FAIL / 12 LINK_FAIL / 0 RUN_FAIL / 0 regressions. All 5 tensor goldens 49/50/51/52/53: 0 objs / 0 B under LSan. UAF sweep 60 CLEAN / 6 CRASH_NO_ASAN / 0 ASAN_ERROR preserved. Valgrind 66 WARNINGS_ONLY / 0 ERRORS preserved. Goldens 64/66 preserved (byte-identical tensor output: 49 `1 3 1 3 2 6 1 6 2 3 3 8 1 8 3 20 -1 -2.5`; 50 `1 3 4 6 10 30 1 8 42 99 200`; 51 `11 44 9 36 10 10 101 104 2 8 11 33`; 52 `15 3 5 1 4 0 60 30 1 2 20 30 2 6`; 53 `w = 1.96879 / b = 0.560177 / converging`). stage2.ll 205446 lines (+0.56% vs v5.6.3), 934 defines (+3: `emit_track_tensor`, `is_tensor_allocating_fn`, `emit_drop_glue_tensors`). llvm-as OK. stage3 empty (Ve.1 preserved). `make lint` clean. Registry 23/23/91 clean. See docs/roadmap/v5/v5.6.4/SESSION_REPORT.md. |
| **Perf.2** | Lazy thread creation in coro scheduler. `__mn_coro_scheduler_init` pre-creates 2 workers eagerly, grows pool lazily when `active_tasks > workers * 8`. Idle workers self-exit after 100 ms (floor: 2 workers). Default async geomean: 2.3 → 1.19 ms (0.91× Go without env var). `MAPANARE_ASYNC_THREADS` preserved as optional override. | **v5.1.4** | TSan 0 races; valgrind 0 leaks; 54/66 goldens unchanged. Default-settings geomean matches tuned case within noise. |
| **Ge.1r** | 4 valgrind ERRORS on generics goldens 26/29/30/31 ("Invalid read of size 16|8") eliminated by zero-init fix in `try_monomorphize_enum` / `try_monomorphize_struct`. Extends v4.142.0 partial Ge.1 closure with explicit aggregate field initialization after monomorphic allocation. | **v5.1.1** | Valgrind sweep at v5.3.0: 0 ERRORS on goldens 26/29/30/31. 62 WARNINGS_ONLY, 2 ERRORS (GPU feature-gap tests only). |
| **Sh.4 (async)** | Self-hosted emitter ships full LLVM-coroutine lowering for async fns: `presplitcoroutine` attribute + the `@llvm.coro.id/begin/save/suspend/end` pipeline (v5.5.4 — Phase 1: real LLVM coroutines), scheduler-driven `AwaitSuspend` (v5.5.5 — Phase 2), scheduler-driven `BlockOn` + main lifecycle (v5.5.6 — Phase 3), drop-glue + sanitizer hardening (v5.5.7 — closes Rt.05 inner-coroutine handle leak). All 5 Sh.4 goldens (55_async_basic / 56_async_await / 57_real_await / 58_async_file_io / 59_async_fanout) compile through `mnc-stage1` and execute correctly through the real LLVM coroutine ABI. | **v5.5.4–v5.5.7** | Goldens 59/66 → preserved through arc; valgrind 0 errors / 0 leaks on 55–59 (e.g., 59_async_fanout = 36 allocs / 36 frees / 0 in use at exit); ASan 0 errors; LSan 0 leaks; TSan 0 races on 56/57/58/59 under `MAPANARE_ASYNC_THREADS=4`. See `docs/roadmap/v5/v5.5.4/`–`v5.5.7/SESSION_REPORT.md`. |
| **Sh.6** | Tensor surface ported to self-hosted emitter across 4 phases. v5.6.0: tensor literals + parser walker + 6 `__mn_tensor_*` runtime decls + golden 49 byte-identical. v5.6.1: multi-dim indexing (`a[i, j]` / `d[i, j] = val`) + 4 variadic `__mn_tensor_{get,set}_{f64,i64}_nd` decls + golden 50 closes end-to-end. v5.6.2: broadcast + scalar binops (`+/-/*//`) + 20 `__mn_tensor_*_{broadcast,scalar,r*}_{f64,i64}` decls + golden 51. v5.6.3: tensor slicing + reductions (sum / mean / max / min / argmax / argmin) + `_` wildcard token + `Expr::TensorSlice` AST + 11 reduction decls + golden 52 (parse-error → byte-identical) + golden 53 (function-match → runtime-correct). | **v5.6.0–v5.6.3** | All 5 tensor goldens (49/50/51/52/53) byte-identical to expected output through `mnc-stage1 → llc → clang`. `grep -l "lower_tensor_slice\|tensor_reduction" mapanare/self/lower.mn` returns `mapanare/self/lower.mn`. See `docs/roadmap/v5/v5.6.{0,1,2,3}/SESSION_REPORT.md`. |
| **Sh.7** | Self-hosted closure-typed parameter resolution. Four self-hosted changes: `parser.mn`'s `FAT_ARROW` handler now extracts multi-param lambdas from `(a, b) => ...` (was: only single `Ident` LHS); `lower.mn::lower_call_by_name` routes calls through fn-typed locals via indirect-call SSA name (`lookup_var(fn_name)` → if `addr.ty.kind == TK_FN()` then emit `Load` + `Call(dest, "%loaded_val", args)`); `emit_llvm_ir.mn::emit_call_ir` / `emit_call_void` recognise `%`-prefixed callees and emit `call <ret> %fn(<args>)` without the `@` prefix; `mir_opt.mn`'s `clone_instr_for_inline` and `replace_uses_in_instr` rename Call's `fn_name` when it's an SSA value (closes the inliner's dangling-reference issue). | **v5.7.0** | Goldens **65/66 → 66/66 — first time in project history**. `tests/golden/64_closure_typed.mn` byte-identical pre/post except VERSION. New tests: 3 in `test_closure_typed_params.py`. See `docs/roadmap/v5/v5.7.0/SESSION_REPORT.md`. |
| **B (or-pattern + None)** | `_is_enum_variant_name` short-circuits to True for built-in `None`/`Some`/`Ok`/`Err` (was: only walked user-defined enums, treating `None` as a fresh binding name); `Identifier("None")` resolves to `Option` in both `_infer_expr` (semantic) and `_lower_identifier` (lower) — mirrors self-hosted v4.134.0 Sh.12 fix. Self-hosted `bind_pattern` doesn't have the over-strict check (just binds from the first alt) — no mirror needed. | **v5.7.0** | `tests/golden/51_match_guards_and_or.ref.ll` re-blessed (2 fns, 298 lines). New tests: 5 in `test_or_pattern_guards.py`. Bootstrap pytest **225 passed / 0 failed** (was 13 baseline including 51). See `docs/roadmap/v5/v5.7.0/SESSION_REPORT.md`. |
| **DX.1** | `mnc --help` / `-h` / `help` print a 30-line usage block instead of `error: cannot read file '--help'`. Per-subcommand help via both `mnc help <sub>` and `mnc <sub> --help` — early dispatch branches in `mn_main` route to `print_help_text()` / `print_subcommand_help()` helpers in `main.mn`. Edge case `mnc help` without arg-2 falls through to the same `print_help_text`. | **v5.9.0** | `tests/test_cli_help.py` — 20 passed: covers `--help`, `-h`, `help`, `help <sub>` for all 5 subcommands, `<sub> --help` for all 5, `version` no-placeholder. |
| **DX.2** | `mnc version` prints `mapanare 5.9.0` instead of the literal `mapanare __MN_VERSION__`. Structural fix: new `__mn_version_string()` C-runtime export returning a build-time-baked constant (`-DMAPANARE_VERSION="..."` from the VERSION file). Eliminates the v4.28.0 source-tree placeholder + `scripts/build_stage1.py:_substitute_version()` tempdir-copy dance. Self-hosted `version()` and `emit_metadata_node`'s `!"<ver>"` literal both call the export at runtime — same shape as v5.8.6 We.1's `__mn_host_is_windows()`. Bb.3 seed refresh shipped (mandatory; new builtin call site predates the v5.8.8 seed). Same fix also incidentally restores the strict 3-stage fixed-point that has been NEAR (4 VERSION-only diff lines) since v4.140.0 — both stages now embed identical version strings because the C-runtime constant is the single source of truth. | **v5.9.0** | `mnc version` and `mnc --version` on a fresh build print `mapanare 5.9.0`. `tests/self_hosted/test_main_mn.py::test_version_calls_runtime_export` + `test_version_string_is_not_hardcoded` gate the structure. `grep "__MN_VERSION__" mapanare/self/*.mn scripts/build_stage1.py` returns 0 non-comment hits. `-DMAPANARE_VERSION` flag wired to 5 publish.yml clang/gcc sites. |
| **DX.3** | Missing-clang failures print platform-specific install instructions (`winget install LLVM.LLVM` on Windows / `brew install llvm` on macOS / `apt install clang` on Linux) instead of the bare `error: clang failed`. clang's stderr is no longer swallowed via `2>/dev/null` — captured to `__mn_clang_err_path()` (a platform-portable temp file) and reprinted on non-zero exit via `report_clang_failure()`. `check_clang_available()` probe at the start of every `run` / `build` / `test` / `compile` entry point. Probe cost <10 ms; runs once per process invocation. | **v5.9.0** | Manual sweep on Linux (`PATH=/nonexistent ./mnc-stage1 run hello.mn`) prints "error: clang not found" + Linux install hint, exits 1. With clang present, identical behavior to v5.8.8. |
| **DX.4** | `mnc cache stats` and `mnc cache clean` work on Windows. Replaced the POSIX-only `__mn_system("if [ -d ... ]; find ... | wc -l; du -sh; rm -rf")` shell-out with three new C-runtime exports — `__mn_dir_count_files`, `__mn_dir_total_size`, `__mn_dir_remove_recursive` — each implemented with platform-conditional walkers (FindFirstFile / FindNextFile on Windows, opendir / readdir on POSIX). Pre-v5.9.0 Windows users hit `-d was unexpected at this time` (cmd.exe's reaction to bash's `[ -d ... ]` test). Also adds `__mn_dev_null_redirect()` shim returning ` 2>/dev/null` on POSIX and ` 2>NUL` on Windows; sweep replaces every literal `2>/dev/null` in `main.mn` (gcc link, strip, mapanare transpile, etc.) — 4 sites converted. | **v5.9.0** | Manual sweep on Linux: empty cache → "No cache (run mnc build <dir> first)"; populated cache (3 files, 30B, 3 modules in manifest.txt) → byte-by-byte expected output; `cache clean` → recursive removal works. Windows sweep deferred to next release (no Windows VM in the v5.9.0 session); the platform-specific code paths are correct by inspection (mirrors `__mn_dir_list_strings`'s shape from v3.x). |
| **DX.6** | `install.ps1` and `install.sh` install the `mnc.exe` / `mnc` name alongside `mapanare` (PyInstaller doesn't read argv[0] — the alias is transparent). Pre-v5.9.0 install.ps1 references `mapanare.exe` everywhere; user reports + the v5.8.7 Windows probe showed they were typing `mnc` (matching `mnc-stage1`, README, and the standalone native binary `mnc-win-x64.exe`). Fix: `install.ps1` adds `Copy-Item mapanare.exe mnc.exe`; `install.sh` adds `ln -sf mapanare mnc`. Getting-started message uses `mnc init` / `mnc run` / `mnc build` / `mnc --help` consistently. `mapanare` continues to work as an alias for backward compatibility. | **v5.9.0** | `grep -n "mnc.exe\|mapanare.exe" packaging/install.ps1` shows the alias path; `grep "mnc " packaging/install.sh` shows the `ln -sf` line. Manual install on Windows VM deferred to next release; the PowerShell + Bash logic is correct by inspection. |
| **DX.7** | `install.ps1` getting-started message dropped the `(requires LLVM)` parenthetical now that DX.3 surfaces a clean install path on a missing clang. The `mapanare check` line gone (the native CLI doesn't have a separate check command — `mnc <file>` does the type check + IR emit). | **v5.9.0** | `grep "requires LLVM\|mapanare check" packaging/install.ps1` returns 0 lines. |
