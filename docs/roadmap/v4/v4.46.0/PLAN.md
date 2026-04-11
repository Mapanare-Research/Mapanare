# Mapanare v4.46.0 — Arc 3 Panel Release (Tensor Completeness Close)

> **Third 5-minor cadence panel.** Arc 3 closes. Panel grades the
> tensor work from v4.42.0–v4.45.0.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.45.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Panel validates the tensor completeness arc. Coral's 5-cycle SPEC §3.10 debt is fully paid.

---

## Arc scope the panel grades

- v4.42.0: Tensor literals + runtime primitive wiring
- v4.43.0: Multi-dimensional indexing + bounds checking
- v4.44.0: Broadcasting + SPEC §3.10 status line closure
- v4.45.0: Reductions + slicing/views + linear regression demo

The arc-3 panel specifically checks:
- Does `Tensor<Float>[[1.0, 2.0], [3.0, 4.0]]` parse, type-check, compile, run?
- Does broadcasting compile-time-reject mismatched shapes with good messages?
- Do slicing views correctly share buffers without leaking or dangling?
- Does the linear regression demo actually converge?
- Is the SPEC §3.10 Status line finally truthful?

---

## Phase 1 — Pre-panel sweep

- [ ] Run the linear regression demo (`tests/golden/53_linear_regression.mn`) end-to-end. Verify convergence against a reference NumPy implementation.
- [ ] Run a tensor-heavy valgrind pass across v4.42.0-v4.45.0 goldens. Expect zero leaks or invalid reads.
- [ ] GPU smoke test: if CUDA/Vulkan available, run `examples/gpu/*.mn` through the pipeline. Otherwise skip honestly.
- [ ] Benchmark: compare tensor op performance before v4.42.0 (if measured) and v4.45.0. Any regressions are investigated.

## Phase 2 — Documentation polish

- [ ] `docs/SPEC.md §3.10` — full audit. Is the Status line accurate? Are all tensor literal, indexing, broadcasting, reduction, and slicing forms documented?
- [ ] `docs/cookbook.md` §Tensors — ensure it has sections for each v4.42.0–v4.45.0 feature.
- [ ] `docs/reference.md` — tensor operator table up to date.
- [ ] Cross-check against `check_docs_drift.py`.

## Phase 3 — Measurement refresh

- [ ] `culebra summary mapanare/self/main.ll` — tensor work did not touch `main.ll` substantially (runtime primitives + emitter decls added), but check for regressions.
- [ ] Tensor-specific metrics:
  - Tensor literal allocation time (1k-element)
  - Broadcast add time (1000x1000 + 1000x1000)
  - matmul time (256x256) — GPU vs CPU
  - Slice-view creation time (sub-tensor from a 10k-element parent)
  - Linear regression convergence time (1000 epochs)
- [ ] `MEASUREMENTS.md` written

## Phase 4 — LOW sweep

Any LOW items from v4.41.0 ledger still open. Last chance before the panel.

## Phase 5 — Pre-panel audit

- [ ] Fact-check every v4.42.0–v4.45.0 SESSION_REPORT claim against file:line
- [ ] `PRE_PANEL_AUDIT.md` written

## Phase 6 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.46.0. Arc: Arc 3 (tensor completeness).
- [ ] `mkdir -p .reviews/v4.46.0/` + pre-populate
- [ ] Spawn 7 reviewers. Special focus:
  - **Cobra (C++/ABI)** — primary for tensor ABI. NumPy-parity question: does Mapanare's tensor feel like a real tensor primitive or a thin wrapper?
  - **Rattler (LLVM)** — verifies the lowering paths, especially for slicing views with the atomic refcount
  - **Mamba (C runtime)** — tensor allocator primitives, view ownership, buffer sharing
  - **Viper (memory safety)** — view lifetime, refcount correctness, no dangling-view-after-parent-drop
  - **Coral (language design)** — the §3.10 closure is yours; grade it personally
- [ ] All 7 reviewers.

## Phase 7 — Closeout

- [ ] Write `.reviews/v4.46.0/README.md`
- [ ] If PASS: Arc 3 closes. v4.47.0 opens Arc 4 (stdlib AI/LLM).
- [ ] If NEEDS WORK: recovery protocol; Arc 4 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Linear regression demo converges | runtime output |
| 2 | Valgrind clean on tensor goldens | valgrind log |
| 3 | Documentation polish complete | `check_docs_drift.py` clean |
| 4 | Performance metrics recorded | `MEASUREMENTS.md` |
| 5 | `LEDGER_AUDIT.md` written | file exists |
| 6 | `PRE_PANEL_AUDIT.md` written | file exists |
| 7 | `.reviews/prompt.md` retargeted | diff |
| 8 | `.reviews/v4.46.0/` pre-populated | `ls` |
| 9 | 7 reviewer files exist | listed |
| 10 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 11 | SESSION_REPORT written | file exists |

---

## What v4.46.0 does NOT do

- **New features.** Panel release.
- **Compiler core changes.** Arc 3 was tensor-specific.
- **GPU kernel fusion / auto-diff.** v5.x or v4.47.0+ growth.

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 3
- [`v4.36.0/PLAN.md`](../v4.36.0/PLAN.md), [`v4.41.0/PLAN.md`](../v4.41.0/PLAN.md) — prior panel release patterns

---

## After v4.46.0

v4.47.0 opens **Arc 4 (stdlib AI/LLM growth)**.
