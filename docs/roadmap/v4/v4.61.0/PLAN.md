# Mapanare v4.61.0 — Arc 6 Panel Release (Deprecation + Deletion Close)

> **Sixth 5-minor cadence panel.** Arc 6 closes. Panel grades the
> deletion work from v4.57.0-v4.60.0.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.60.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** The tree is as clean as it's been since the recovery arc.

---

## Arc scope

- v4.57.0: Python emitter deprecation warnings
- v4.58.0: Python emitter deleted (A3)
- v4.59.0: llvmlite JIT deprecation + deletion (A4)
- v4.60.0: Dead code audit + test honesty final pass

Panel questions:
- Does the codebase compile and run cleanly without any deprecated code paths?
- Is the bootstrap chain still intact with no llvmlite / Python-emitter dependencies?
- Is the `CARRY_FORWARD.md` ledger actually honest after v4.60.0's reconciliation?
- Are there any remaining hollow claims in the docs about features that were deleted in this arc?

---

## Phase 1 — Pre-panel sweep

- [ ] Fresh install: `pip install -e ".[dev]"` on a clean environment. Verify no llvmlite pulled in.
- [ ] Fresh bootstrap: `bash scripts/build_from_seed.sh` on a clean tree. Verify `mnc-stage1` builds.
- [ ] Run full test suite: pytest, golden, stage2, fixed-point, CI gates. All green.
- [ ] Grep for any remaining mention of deleted code: `grep -rn "PythonMIREmitter\|emit_python_mir\|llvmlite\|mapanare_jit" mapanare/ docs/ runtime/ tests/ scripts/`. Expected: empty.

## Phase 2 — Documentation polish

- [ ] Final pass on SPEC, cookbook, reference, README
- [ ] Migration docs: v4.57-to-v4.58.md and v4.58-to-v4.59.md — audit readability
- [ ] Architecture diagrams: do they still mention Python backend or llvmlite? Update

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — record
- [ ] Line count: `wc -l mapanare/*.py runtime/native/*.c` — compare to v4.31.0 baseline
- [ ] Python dependency count: `pip list | wc -l` — should be materially smaller without llvmlite
- [ ] Bootstrap chain duration: `time bash scripts/build_from_seed.sh` — should be faster without Python fallback
- [ ] `MEASUREMENTS.md` written

## Phase 4 — LOW sweep + pre-panel audit

- [ ] Any remaining LOW items from v4.56.0 ledger
- [ ] Fact-check v4.57.0-v4.60.0 SESSION_REPORT claims
- [ ] `PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.61.0. Arc: Arc 6 (deprecation + deletion).
- [ ] `mkdir -p .reviews/v4.61.0/` + pre-populate
- [ ] Spawn 7 reviewers. Special focus:
  - **Boa (Python/DX)** — is the developer experience still good without the Python backend path? Does it feel like a loss or a win?
  - **Anaconda (toolchain)** — is the build pipeline cleaner? Does the dependency reduction have a measurable effect?
  - **Mamba (C runtime)** — no C changes in arc 6, but grade the overall runtime health
  - **Rattler (LLVM)** — LLVM backend is now the only backend; any concerns about monoculture?
  - **Viper (memory safety)** — deleted code is safer than live code; grade the deletion

## Phase 6 — Closeout

- [ ] `.reviews/v4.61.0/README.md` written
- [ ] If PASS: arc 6 closes. v4.62.0 opens arc 7 (DWARF).
- [ ] If NEEDS WORK: recovery protocol; arc 7 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Fresh install has no llvmlite | `pip show llvmlite` empty |
| 2 | Fresh bootstrap builds mnc-stage1 | `build_from_seed.sh` clean |
| 3 | Full test suite green | CI logs |
| 4 | Grep for deleted symbols returns empty | grep clean |
| 5 | Documentation polish complete | `check_docs_drift.py` |
| 6 | Metrics recorded | `MEASUREMENTS.md` |
| 7 | `LEDGER_AUDIT.md` / `PRE_PANEL_AUDIT.md` | files exist |
| 8 | Panel prompt retargeted + pre-populated | diff + ls |
| 9 | 7 reviewer files exist | listed |
| 10 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 11 | SESSION_REPORT written | file exists |

---

## What v4.61.0 does NOT do

- **New features**
- **Compiler changes**
- **DWARF work** — that's v4.62.0+

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 6

---

## After v4.61.0

v4.62.0 opens **Arc 7 (DWARF debug info)** — the first of a 5-release arc that closes `CARRY_FORWARD.md` A2. Real debug info. Real gdb backtraces. Real variable inspection.
