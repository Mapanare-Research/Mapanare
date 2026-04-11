# Mapanare v4.66.0 — Arc 7 Panel Release (DWARF Close)

> **Seventh 5-minor cadence panel.** Arc 7 closes. Panel grades the
> DWARF work from v4.62.0–v4.65.0 and specifically checks whether
> gdb can debug a Mapanare program end-to-end.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.65.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** A2 is closed. Real debug info. Real gdb.

---

## Arc scope

- v4.62.0: DWARF design + infrastructure
- v4.63.0: `DICompileUnit` + `DISubprogram`
- v4.64.0: Line metadata on every instruction
- v4.65.0: `DILocalVariable` + `llvm.dbg.declare`/`value` + gdb smoke test

Panel questions:
- Compile a Mapanare program with `-g`, open it in gdb, set a breakpoint, step through, inspect variables. Does the experience match what a C developer expects?
- Does `llvm-dwarfdump --verify` pass on 10 representative goldens without errors?
- Is the self-hosted emitter byte-identical to the Python emitter when both emit `-g`?
- Any regressions in non-debug build quality?

---

## Phase 1 — Pre-panel sweep

- [ ] Run gdb scripted sessions on 10 golden programs. Each session:
  - Break at `main`
  - Run
  - Inspect the first 2-3 local variables
  - Step through a few instructions
  - Verify source lines shown match the `.mn` file
- [ ] If any gdb session surfaces an issue, fix it in v4.66.0 before the panel.

## Phase 2 — Documentation polish

- [ ] `docs/cookbook.md` — new §"Debugging with gdb" chapter walking through the full gdb experience
- [ ] `docs/SPEC.md` §Compilation — document the `-g` flag and DWARF output
- [ ] `docs/reference.md` — CLI reference for `-g`

## Phase 3 — Measurement refresh

- [ ] `culebra summary` — record
- [ ] Debug-info metrics:
  - `-g` build size overhead for `01_hello.mn` (expected: binary ~30% larger with DWARF)
  - `-g` compile-time overhead (expected: ~10% slower)
  - DWARF section line count (`llvm-dwarfdump --all` → wc -l)
- [ ] `MEASUREMENTS.md`

## Phase 4 — LOW sweep + pre-panel audit

- [ ] LOW items from v4.61.0 ledger
- [ ] Fact-check v4.62.0-v4.65.0 SESSION_REPORT claims
- [ ] `PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.66.0. Arc: Arc 7 (DWARF).
- [ ] `mkdir -p .reviews/v4.66.0/` + pre-populate
- [ ] Spawn 7 reviewers. Special focus:
  - **Rattler (LLVM)** — primary. DWARF is in his lens. Grade `!DI*` metadata quality, pass-pipeline interaction.
  - **Anaconda (toolchain)** — grades the `-g` flag UX and `scripts/check_dwarf.sh` CI integration
  - **Cobra (C++/ABI)** — grades against C++ debug experience
  - **Mamba (C runtime)** — no runtime changes, but the C DWARF expectations are his lens
  - **Boa (Python/DX)** — is the gdb experience good enough to recommend?

## Phase 6 — Closeout

- [ ] `.reviews/v4.66.0/README.md`
- [ ] If PASS: arc 7 closes. v4.67.0 opens arc 8 (coroutine foundation).
- [ ] If NEEDS WORK: recovery protocol; arc 8 slides.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 10 goldens pass gdb scripted sessions | pre-panel log |
| 2 | Cookbook §Debugging with gdb chapter written | `check_docs_drift.py` clean |
| 3 | Metrics recorded | `MEASUREMENTS.md` |
| 4 | `LEDGER_AUDIT.md` / `PRE_PANEL_AUDIT.md` | files |
| 5 | Panel prompt retargeted + pre-populated | diff + ls |
| 6 | 7 reviewer files | listed |
| 7 | `README.md` written | file |
| 8 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README |
| 9 | A2 formally CLOSED in ledger (was closed in v4.65.0; panel confirms) | ledger diff |
| 10 | gdb experience matches C developer expectations (subjective, panel judgment) | Boa / Cobra reviews |
| 11 | SESSION_REPORT written | file |

---

## What v4.66.0 does NOT do

- **New features**
- **Coroutine work** — v4.67.0+

---

## Reference

- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 7

---

## After v4.66.0

v4.67.0 opens **Arc 8 (coroutine foundation)** — the first of two arcs shipping real async/await. Starts with a design doc. Four releases of v4.67.0-v4.71.0 set up the grammar, AST, semantic, and half the lowering. Arc 9 (v4.72.0-v4.76.0) finishes lowering + scheduler + end-to-end tests.
