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
| Own.1 | (neither) | (neither) — no move semantics in the language at all | Viper all panels (28 releases) | **v5.1.3** Phase 1 (register_struct / register_enum); v6.0 full borrow checker |

### Optimizer (MIR passes)

The v4.152.0 E8 audit re-evaluated four passes that were disabled at
v4.111.0. Results:

| Pass | Python | Self-hosted | Status | Target |
|---|:---:|:---:|---|---|
| `strength_reduce` | ON | OFF | Zero-ROI both sides; LLVM instcombine covers — parity deferred | — |
| `inline_small_functions` | ON | OFF | **In.1**: rename_instructions collides on caller's `%dst` after inlining | v5.1.2 |
| `licm` | OFF | OFF | **Li.1**: hoist_instruction leaves original in source block — parity, both disabled | v5.1.2 |
| `escape_analysis` | ON | OFF | **Ea.1**: self-hosted version is a stub (`return f` unchanged) | v5.1.2 |

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
| **Ge.1r** | 4 valgrind ERRORS on goldens 26/29/30/31 — "Invalid read of size 16|8" in generics monomorphization | Same root-cause class as Own.1; was asymptomatic at v4.142.0-v4.144.0; resurfaced due to binary-layout shift | v5.1.1 opportunistic |
| Own.1 | `register_struct` / `register_enum` latent UAFs; no move semantics | Language-level ceiling | v5.x feature track |

### Benchmark reporting (Mamba v4.154.0)

Not compiler parity but listed for completeness — all three are
one-line to small fixes Mamba has now flagged 2-3 times:

| ID | Symptom | Target |
|---|---|---|
| **Bn.2** | Geomean arithmetic wrong in FINAL_REPORT (says 1.17×, actual 1.21×); baseline 7.31× mislabeled as 5.83× | v5.1.2 |
| ~~Bn.3~~ | ~~JSON `"version": "4.125.0"` hardcoded~~ `benchmarks/cross_language/run_benchmarks.py` reads VERSION file; per-run JSON now carries the live version. | ~~**v5.0.6 CLOSED**~~ |
| **Bn.4** | C `struct_alloc.c` uses malloc+free; Rust/Mapanare return by value — benchmarks measure different things | v5.1.2 |

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

- **Sh.4** — tensor reshape — v5.x feature track
- **Sh.5** — mutable views — v5.x feature track
- **Sh.6** — stepped slices — v5.x feature track
- **Sh.7** — closure-typed captures — v5.x feature track
- **Sh.9a** — async test harness — v5.x feature track
- **Perf.2** — lazy thread creation in coro scheduler; eliminates the
  `MAPANARE_ASYNC_THREADS=2` workaround that the 0.85× Go headline
  requires — **v5.1.4**

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
