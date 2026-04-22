# v5.0.6 Session Report — Multi-Cycle Hygiene Closeout

**Date:** 2026-04-21
**Scope:** Eight multi-cycle carry-forward items closed in one release
**Breaking:** No
**Compiler semantics:** No change (Rt.4 widens an under-allocation;
sanitizer / golden / fixed-point output unchanged)

---

## Items closed

| ID | Severity | Cycles | Fix |
|---|---|---|---|
| **Bo.12-table** | MEDIUM | Boa v4.144+v4.154 (2 cycles) | README table already carried v4.153.0 numbers at entry; verified no `1.12×` / `4.86×` remnants. |
| **Bo.12-i18n** | MEDIUM | Boa v4.144+v4.154 / Coral v4.154 (9 releases behind) | `docs/README.{es,pt,zh-CN}.md` version badges 5.0.0 → 5.0.6; test badges 5534+ → 5720+. |
| **Rt.4** | MEDIUM (latent heap overflow) | Rattler v4.154 (new) | `llvm_type_size` in `mapanare/self/emit_llvm.mn` returns 24 for `%enum.*` (safe upper bound over `{i64,ptr}` / `{i64,i64}` / `{i64,i64,i64}` layouts). Stale "always {i64, ptr}" comment replaced with the three-layout breakdown. |
| **Bn.3** | LOW | Mamba v4.143+v4.144+v4.154 (3 cycles) | `benchmarks/cross_language/run_benchmarks.py` reads `VERSION` at import; JSON `"version"` field + arg-parser description + banner all use live value. |
| **Cb.6-test** | LOW | Rattler v4.144+v4.154 (2 cycles) | `tests/llvm/test_enum_inline_parity.py` — structural gate that `type_fits_inline_slot` contains the `ends_with("*") → return false` clause. |
| **An.9** | LOW | Anaconda v4.154 (new) | `tests/llvm/test_unified_return_shape.py` — asserts single switch in `@area` pre-opt, sret on `@make_shape`, single switch in `@main` post-`opt -O2`. |
| **An.10** | LOW | Anaconda v4.154 (new) | `scripts/count_tests.py` + `make count-tests`. Deterministic `def test_*` count. |
| **Dr.1-mutation** | LOW | Rattler v4.144+v4.154 (2 cycles) | `scripts/build_stage1.py` uses `tempfile.TemporaryDirectory` for version-placeholder substitution; `mapanare/self/` never mutated during build. |

---

## Changes by file

### Source

| File | Change |
|---|---|
| `benchmarks/cross_language/run_benchmarks.py` | `MAPANARE_VERSION = (ROOT / "VERSION").read_text().strip()`; three hardcoded sites (RESULTS_FILE, JSON field, banner, argparse description) use the variable. |
| `mapanare/self/emit_llvm.mn` | `llvm_type_size`: `%enum.*` → 24 (was 16); comment rewritten to document the three layouts. |
| `scripts/build_stage1.py` | Import `tempfile`. Version substitution + compile happen inside `tempfile.TemporaryDirectory`; `SELF_DIR` is read-only during build. The prior try/finally restore pattern is gone. |
| `Makefile` | New `.PHONY` target `count-tests` → `python scripts/count_tests.py`. |
| `VERSION` | `5.0.5` → `5.0.6`. |

### Tests

| File | Purpose |
|---|---|
| `tests/llvm/test_enum_inline_parity.py` | **NEW** — 2 tests. `test_self_hosted_rejects_typed_pointer_slot` structurally asserts the `ends_with("*")` rejection clause in self-hosted `type_fits_inline_slot`. `test_self_hosted_and_python_emitters_agree_on_opaque_ptr` guards against over-broad fix breaking opaque `ptr`. |
| `tests/llvm/test_unified_return_shape.py` | **NEW** — 3 tests. `test_area_has_single_switch_pre_opt` (E1 shape in pre-opt IR), `test_make_shape_uses_sret` (Rt.1/Cb.15 gate), `test_post_opt_single_switch_in_hot_loop` (skipped when `opt` not on PATH). |

### Scripts

| File | Purpose |
|---|---|
| `scripts/count_tests.py` | **NEW** — deterministic `def test_*` regex count across `tests/`. Supports `--by-dir` and `--path`. |

### Docs

| File | Change |
|---|---|
| `README.md` | Version badge 5.0.0 → 5.0.6; test badge 5534+ → 5720+. |
| `docs/README.es.md` | Same badge bumps. |
| `docs/README.pt.md` | Same badge bumps. |
| `docs/README.zh-CN.md` | Same badge bumps. |
| `CLAUDE.md` | v5.0.6 entry added. |
| `docs/roadmap/ROADMAP.md` | v5.0.6 entry added. |
| `docs/roadmap/v5/PARITY_GAPS.md` | 8 items moved to Historical with verification commands. |
| `docs/roadmap/v5/v5.0.6/SESSION_REPORT.md` | This file. |

---

## Verification

| Check | Command | Result |
|---|---|---|
| Retracted benchmark numbers gone | `grep -rn "1.12x\|1.12×\|4.86×\|4.86x" README.md docs/README.*.md` | 0 |
| Bn.3 hardcode removed | `grep -n "\"4.125.0\"" benchmarks/cross_language/run_benchmarks.py` (outside docstring) | 0 |
| Rt.4 stale comment removed | `grep -n "always {i64, ptr}" mapanare/self/emit_llvm.mn` | 0 |
| Cb.6-test gate | `pytest tests/llvm/test_enum_inline_parity.py -v` | 2 passed |
| An.9 gate | `pytest tests/llvm/test_unified_return_shape.py -v` | 2 passed / 1 skipped (opt absent on Windows) |
| An.10 counter works | `python scripts/count_tests.py` | 4209 |
| Makefile target | `make count-tests` | 4209 |
| `build_stage1.py` syntax | `python -c "import ast; ast.parse(open('scripts/build_stage1.py').read())"` | OK |
| `build_stage1.py` no more .mn mutation | `grep -n "mn_file.write_text" scripts/build_stage1.py` | 1 hit, into tempdir only |
| VERSION | `cat VERSION` | 5.0.6 |

The Dr.1-mutation fix was developed on Windows; the end-to-end
`git stash && python scripts/build_stage1.py && git diff mapanare/self/`
verification must run on WSL/Linux where the full toolchain (clang +
linker paths) is available. Logic verified by inspection: substitution
writes exclusively to `tempfile.TemporaryDirectory`; `root_file` passed
to `compile_multi_module_mir` points at the tempdir copy; `source_filename`
in the emitted IR uses `os.path.splitext(os.path.basename(root_file))[0]`
which yields `"main"` independent of tempdir path.

---

## What this release does NOT do

- No compiler semantic changes. Rt.4 widens an allocation by up to 8B;
  no hot-path changes, no ABI change.
- No optimizer / MIR / emitter algorithmic changes.
- No language changes.
- Does not close Own.1, In.1, Li.1, Ea.1, Bn.2, Bn.4, Ge.1r — those are
  architectural, tracked for v5.1.x.

---

## Rationale for bundling

Cobra v4.154.0 flagged a 27% undercount in the v4.153.0 DOCKET_LEDGER.
Multi-cycle carry-forwards are the same failure mode: known, trivial,
unfixed across 2-3 panels. Doing eight one-at-a-time releases would
dwarf the actual work (~3.5 hours) in per-release overhead (version
bump, CI cycle, release notes, panel attention). Bundling into one
hygiene release is the correct unit economics. PARITY_GAPS.md is the
tracking layer Cobra's review said we need; this release populates
its Historical section for the multi-cycle class.
