# Mapanare v4.71.0 — Arc 8 Panel Release (Coroutine Foundation Close)

> **Eighth 5-minor cadence panel.** Arc 8 closes. Panel grades the
> coroutine foundation work from v4.67.0–v4.70.0. Async/await isn't
> runnable yet — that's arc 9 — but it's halfway there and each step
> is structurally correct.

**Status:** DONE (2026-04-13)
**Session log:** Panel executed. PASS WITH NOTES (8.29/10). Zero NEEDS WORK. Arc 8 closes. 9 action items tracked for Arc 9.
**Decisions taken:** Arc 8 closes despite below-9.0 aggregate — foundation is sound per all 7 reviewers. Arc 9 opens at v4.72.0.
**Breaking:** No
**Prerequisite:** v4.70.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** The hardest design work in the project is half-shipped. Panel grades whether the foundation is sound enough to finish.

---

## Arc scope

- v4.67.0: Coroutine design document (design-only)
- v4.68.0: `async`/`await` grammar + AST + parser (delta review)
- v4.69.0: Semantic analysis + `Future<T>` type constructor
- v4.70.0: MIR suspension points (stubs) + coroutine lowering pt 1 (prelude emission)

Panel-specific questions:
- Is the DESIGN.md sound? Did v4.68.0-v4.70.0 follow it without deviation? Any deviations documented?
- Does `async fn foo() -> Int { return 42 }` compile to valid IR, pass `llvm-as`, and survive `coro-split` into `ramp` + `resume` + `destroy` + `cleanup` functions?
- Does `await` still fail at lower time, with an updated "arrives in v4.72.0" message? (Intended interim state.)
- Are the semantic checks sufficient to catch "forgot to await" and "await outside async"?
- Does Rattler (LLVM lens) sign off on the coroutine prelude shape?

---

## Phase 1 — Pre-panel sweep

- [ ] Compile 10 tiny async programs (one-function, no awaits — just `async fn foo() -> Int { 42 }`) and verify:
  - IR emission successful
  - `llvm-as` clean on emitted IR
  - `opt -passes=coro-split,coro-cleanup` produces split functions
  - `clang` links the result into a `.o` file (no runtime driver yet)
- [ ] The v4.68.0-v4.69.0 semantic tests all pass
- [ ] No regressions in existing (non-async) tests

## Phase 2 — Documentation polish

- [ ] `docs/SPEC.md` §Futures subsection — draft version updated to reflect the v4.68.0-v4.70.0 state
- [ ] `docs/roadmap/v4/POST_RECOVERY_ROADMAP.md` §Arc 8 — reflect actual progress, note any deviations
- [ ] `CHANGELOG.md` — honest arc-8 status section

## Phase 3 — Measurement refresh

- [ ] Coroutine-specific metrics:
  - Compile time for a 10-line async fn (expected: ~2x the non-async cost due to `coro-split`)
  - Post-split IR size (one function becomes four)
  - Binary size for a simple async program (no runtime driver yet — just the `.o`)
- [ ] `MEASUREMENTS.md` written

## Phase 4 — LOW sweep + pre-panel audit

- [ ] Any v4.66.0 LOW items still open
- [ ] Fact-check v4.67.0-v4.70.0 SESSION_REPORT claims against file:line
- [ ] `PRE_PANEL_AUDIT.md`

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.71.0. Arc: Arc 8 (coroutine foundation).
- [ ] `mkdir -p .reviews/v4.71.0/` + pre-populate. Include DESIGN.md in the pre-populated files — this is the key context for the panel.
- [ ] Spawn 7 reviewers. Special focus:
  - **Rattler (LLVM)** — primary. He reviewed DESIGN.md at v4.67.0; now he grades the execution. Specifically verifies: `presplitcoroutine` shape, `coro-split` pipeline integration, frame size computation correctness
  - **Cobra (C++/ABI)** — C++20 coroutines grew from exactly this LLVM infrastructure; he knows the space. Grades the coroutine frame layout vs C++ expectations
  - **Mamba (C runtime)** — the scheduler integration is his v4.73.0, but he can preview the runtime-integration questions now
  - **Coral (language design)** — does the `async fn` / `await` user experience match the DESIGN.md §3 goals?
  - **Viper (memory safety)** — the coroutine frame is heap-allocated; grade the drop-glue interaction (arc 9 work, but preview)

## Phase 6 — Closeout

- [ ] `.reviews/v4.71.0/README.md` written
- [ ] If PASS: arc 8 closes. v4.72.0 opens arc 9 (coroutine completion).
- [ ] If NEEDS WORK: recovery protocol; arc 9 slides. Given the complexity of this work, a NEEDS WORK verdict is more likely here than in other arcs — the panel may surface real design gaps. That's the point.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 10-program smoke test passes (compile + llvm-as + coro-split + clang) | pre-panel log |
| 2 | Documentation updated to match actual progress | `check_docs_drift.py` clean |
| 3 | Metrics recorded | `MEASUREMENTS.md` |
| 4 | `LEDGER_AUDIT.md` / `PRE_PANEL_AUDIT.md` | files |
| 5 | Panel prompt retargeted + pre-populated with DESIGN.md | diff + ls |
| 6 | 7 reviewer files | listed |
| 7 | `.reviews/v4.71.0/README.md` written | file |
| 8 | Panel verdict ≥ 9.0 with zero NEEDS WORK (target) | README.md |
| 9 | Rattler signs off on coroutine prelude shape | `06-rattler.md` |
| 10 | DESIGN.md adjustments (if any) merged back | DESIGN.md diff |
| 11 | SESSION_REPORT written | file |

---

## What v4.71.0 does NOT do

- **New features**
- **Suspension** — v4.72.0
- **Runtime scheduler** — v4.73.0
- **End-to-end async** — v4.75.0

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md)
- [`POST_RECOVERY_ROADMAP.md`](../POST_RECOVERY_ROADMAP.md) §Arc 8

---

## After v4.71.0

v4.72.0 opens **Arc 9 (coroutine completion)**. First release: lowering pt 2 (`llvm.coro.suspend`, `llvm.coro.save`, `llvm.coro.free`, `llvm.coro.resume`, `llvm.coro.destroy`). `await expr` stops erroring. Not yet runnable (no scheduler).
