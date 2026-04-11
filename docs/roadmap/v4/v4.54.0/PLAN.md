# Mapanare v4.54.0 — `emit_c.mn` Decision (A9)

> **Arc 5 release 3.** Closes `CARRY_FORWARD.md` A9. The self-hosted
> C emitter `mapanare/self/emit_c.mn` (770 lines) references MIR types
> that no longer exist — it has been stale since v4.2.0's emitter
> consolidation. v4.54.0 executes Path A (rewrite) or Path B (delete).

**Status:** PLANNED
**Breaking:** No (depending on path choice — Path B deletes a self-hosted module that's already broken; Path A restores it)
**Prerequisite:** v4.53.0
**Delta review:** No
**Full panel:** No (v4.56.0)
**Estimated work:** 1 sprint (Path B) or 3 sprints (Path A)
**Theme:** Decide whether Mapanare needs a self-hosted C backend, or whether the Python `mapanare/emit_c.py` is the canonical fallback.

---

## The decision

**Option A — Rewrite `emit_c.mn` to target the current MIR.** ~3 sprints of work. Brings the self-hosted pipeline to full parity with the Python side: a `.mn` program can be compiled to C via `mnc emit-c`, without going through Python.

**Option B — Delete `emit_c.mn`.** ~1 sprint (mostly documentation). The Python-side `mapanare/emit_c.py` remains the only C emitter. The self-hosted pipeline drops the C backend; users who want C output go through Python.

### Which path is correct

**The case for Path B (delete):**
- v4.2.0 consolidated to one LLVM emitter on the Python side. The C emitter was kept as a fallback for platforms without LLVM but has barely been touched since.
- 770 lines of stale self-hosted code is debt. Deleting it is strictly less code.
- The Python emitter at `mapanare/emit_c.py` (2,408 lines) is maintained and tested. If the user wants C output, they can go through Python.
- v4.58.0 deletes the Python emitter anyway (A3 — `mapanare/emit_python_mir.py`), but that's the **Python transpile backend**, not the C emitter. The C emitter survives.
- **Wait — do we need it for bootstrap on systems without LLVM?** The self-hosted compiler uses LLVM IR. The bootstrap chain (`scripts/build_from_seed.sh`) also uses LLVM. There's no bootstrap path that requires C-as-LLVM-substitute today.

**The case for Path A (rewrite):**
- Parity with the Python side. The self-hosted claim "fully bootstraps without Python" is cleaner if every Python emitter has a self-hosted equivalent.
- A C backend unlocks platforms where LLVM is unavailable or undesirable (embedded, legacy).
- Some users may want to read generated C for debugging.

**Decision for v4.54.0:** Path B. Reasons:
- Nobody is asking for `mnc emit-c` today.
- Debt cost of stale code > debt cost of missing feature.
- If demand emerges, v5.x can rebuild the self-hosted C emitter against a fresh MIR with no legacy baggage.
- The v4.27.0 Path B precedent: "strike claims that aren't backed by working code."

If the lead changes their mind during Phase 0 (audit), the path choice is recorded in DECISIONS.md and the rest of the phases reroute.

---

## Phase 0 — Decision document

- [ ] `docs/roadmap/v4/v4.54.0/DECISIONS.md` — one page:
  - The decision: Path B (delete), with dates
  - The alternatives considered and rejected
  - The open question: "what if a future release needs a C backend?" — answered: "rebuild fresh"
  - The migration path for users: none required (nobody uses `mnc emit-c` through the self-hosted pipeline)

---

## Phase 1 — Path B execution (delete)

### Phase 1.1: Delete the file

- [ ] `rm mapanare/self/emit_c.mn`
- [ ] Any references to `emit_c.mn` in `scripts/build_stage1.py` — remove
- [ ] Any references in `mapanare/self/main.mn` that dispatched to a C backend — remove (expected: none, since the file hasn't been wired)
- [ ] Grep the tree for `emit_c` symbols that might have been imported from the self-hosted side: `grep -rn "emit_c" mapanare/self/`

### Phase 1.2: Strike claims

- [ ] `docs/SPEC.md` — if any section claims the self-hosted compiler emits C, rewrite or strike
- [ ] `CHANGELOG.md` — historical entries that claimed the C emitter was self-hosted: add inline strike notes pointing at v4.54.0
- [ ] `docs/roadmap/v4/README.md` — remove any row claiming self-hosted C emitter

### Phase 1.3: Update claims about Python independence

- [ ] `docs/roadmap/v0/` to `docs/roadmap/v2/` READMEs (if they exist) may claim "self-hosted without Python." Audit and correct: the claim is true for LLVM codegen; it was never true for C codegen (not really).
- [ ] `README.md` — if it mentions C as a "compile target", verify it says "via the Python backend" to be honest.

### Phase 1.4: Tests

- [ ] If any tests exist that compile `mapanare/self/emit_c.mn` (unlikely — it was stale), delete them.
- [ ] `tests/self_hosted/test_c_emitter_deleted.py` — a grep-based regression test: assert `mapanare/self/emit_c.mn` does not exist on disk. Catches a future accidental resurrection.

## Phase 2 — Fixed-point

- [ ] Rebuild stage1, stage2, stage3. Fixed-point diff stays at 0. Nothing in the live pipeline should have depended on `emit_c.mn`.

## Phase 3 — LOW sweep

2 items.

## Phase 4 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.54.0
- [ ] `CHANGELOG.md [4.54.0]` — A9 closed, Path B executed, 770 lines deleted
- [ ] `.reviews/CARRY_FORWARD.md` — A9 CLOSED
- [ ] DECISIONS.md committed
- [ ] SESSION_REPORT written — includes the decision rationale and the rationale for not choosing Path A

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | DECISIONS.md written | file exists |
| 2 | `mapanare/self/emit_c.mn` deleted | `ls` returns not-found |
| 3 | No references to emit_c in the self-hosted tree | grep clean |
| 4 | `scripts/build_stage1.py` still builds | rebuild clean |
| 5 | Stage1 + stage2 + stage3 all clean | fixed-point 0 |
| 6 | Documentation claims about self-hosted C emitter struck or corrected | `check_changelog_honesty.py` + `check_docs_drift.py` clean |
| 7 | `tests/self_hosted/test_c_emitter_deleted.py` regression gate | file exists + passes |
| 8 | A9 CLOSED in `CARRY_FORWARD.md` | ledger diff |
| 9 | All existing golden tests pass | test_native.py |
| 10 | Standard closeout clean | CI |

---

## What v4.54.0 does NOT do

- **Delete the Python-side `mapanare/emit_c.py`** — that's different. The Python C emitter is alive and healthy and stays.
- **Remove the `mnc emit-c` CLI command** — that command goes through the Python emitter; it still works.
- **Build a new C backend from scratch** — Path B. Explicitly.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Some hidden script or test depends on `emit_c.mn` | low | medium | Phase 1 grep + rebuild catches it |
| Users complain that "the self-hosted compiler doesn't emit C" | low | low | Documentation is honest; `mnc emit-c` via Python still works |
| Future v5.x wants a C backend and has to rebuild it | medium | low | Acceptable; fresh rebuild on current MIR is cleaner than resurrecting 770 stale lines |

---

## Reference

- [`.reviews/CARRY_FORWARD.md`](../../../../.reviews/CARRY_FORWARD.md) A9
- v4.2.0 `SESSION_REPORT.md` — the emitter consolidation that made `emit_c.mn` stale
- v4.27.0 — the Path B precedent (strike claims that aren't backed by working code)

---

## After v4.54.0

v4.55.0 is the real `const` — v4.26.0's original CRITICAL finding finally gets the Path A fix, 29 releases later.
